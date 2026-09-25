#!/usr/bin/env python3
"""Check the Author Spotlight prospect file against the prompt's rules.

Usage:
    python3 check_author_prospects.py [author_spotlight_prospects.csv] [--before backup.csv]

Exits 0 when there are no errors (warnings are allowed), 1 otherwise.
With --before, also reports row / key / email counts before vs after a merge.
"""

import argparse
import csv
import re
import sys
from collections import Counter

REQUIRED_COLUMNS = [
    "author_name", "email", "first_name", "book_title", "book_topic",
    "personalization_detail", "personalization_reason", "personalized_opening",
    "subject_line", "email_body", "research_sources", "research_confidence",
    "personalization_status", "send_status", "date_sent",
]
AUDIT_COLUMNS = [
    "country", "region", "city_searched", "location_evidence", "language",
    "amazon_marketplace", "amazon_author_url", "amazon_author_id", "asins_isbns",
    "pen_names_aliases", "official_website", "social_profiles", "evidence_type",
    "email_attribution_note", "publishing_label", "dedupe_key", "batch_id",
    "date_checked", "notes",
]

CONFIDENCE = {"High", "Medium", "Low"}
PERSONALIZATION = {"Ready", "Needs review", "Generic fallback"}
SEND_STATUS = {"Not sent", "Hold – legal review"}
EVIDENCE = {
    "amazon_author_page", "amazon_snippet_verified", "official_site",
    "social_profile", "amazon_snippet_unverified",
}
PUBLISHING = {"Confirmed KDP", "Likely independent/KDP", "Amazon-listed, KDP unverified"}
LANGUAGES = {"EN", "DE", "FR", "ES", "IT", "NL"}
HOLD_COUNTRIES = {"Germany"}  # always on hold
NON_US_COUNTRIES_HOLD_DEFAULT = True  # UK / EU default to hold unless noted corporate

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"(?:\+?\d[\s().-]?){9,}\d")
STREET_RE = re.compile(
    r"\b\d{1,5}\s+\w+(?:\s\w+)?\s+(?:Street|St\.|Avenue|Ave\.|Road|Rd\.|Lane|Ln\.|Drive|Dr\.|"
    r"Boulevard|Blvd|Court|Ct\.|Straße|Strasse|Weg|Allee)\b",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"\{[^}]*\}|\[paid\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BANNED_OPENING = re.compile(r"truly inspired|I (?:have )?read your book|loved reading", re.IGNORECASE)


def normalize_email(e):
    return e.strip().lower()


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def stats(rows):
    keys = {r.get("dedupe_key", "").strip() for r in rows if r.get("dedupe_key", "").strip()}
    with_email = sum(1 for r in rows if r.get("email", "").strip())
    return len(rows), len(keys), with_email


def check(path):
    errors, warnings = [], []
    header, rows = load(path)

    if header[:len(REQUIRED_COLUMNS)] != REQUIRED_COLUMNS:
        errors.append(f"Columns A–O must be exactly {REQUIRED_COLUMNS}; found {header[:len(REQUIRED_COLUMNS)]}")
    missing_audit = [c for c in AUDIT_COLUMNS if c not in header]
    if missing_audit:
        warnings.append(f"Missing audit columns: {missing_audit}")

    email_owner = {}
    key_owner = {}
    author_url_owner = {}

    for i, r in enumerate(rows, start=2):  # row 1 is the header
        g = lambda c: (r.get(c) or "").strip()
        who = f"row {i} ({g('author_name') or '?'})"

        emails = [e for e in (x.strip() for x in g("email").split(";")) if e]
        if not emails:
            errors.append(f"{who}: no email")
        for e in emails:
            if not EMAIL_RE.match(e):
                errors.append(f"{who}: malformed email '{e}'")
            n = normalize_email(e)
            if n in email_owner:
                errors.append(f"{who}: email {e} duplicates row {email_owner[n]}")
            email_owner.setdefault(n, i)

        key = g("dedupe_key")
        if "dedupe_key" in header:
            if not key:
                errors.append(f"{who}: empty dedupe_key")
            elif key in key_owner:
                errors.append(f"{who}: dedupe_key '{key}' duplicates row {key_owner[key]}")
            key_owner.setdefault(key, i)

        for url in (u.strip() for u in g("amazon_author_url").split("|") if u.strip()):
            m = re.search(r"/(B0[0-9A-Z]{8})", url)
            aid = m.group(1) if m else url.lower()
            if aid in author_url_owner and author_url_owner[aid] != i:
                errors.append(f"{who}: Amazon author {aid} duplicates row {author_url_owner[aid]}")
            author_url_owner.setdefault(aid, i)

        if not g("author_name"):
            errors.append(f"{who}: empty author_name")
        if not g("research_sources").startswith("http"):
            errors.append(f"{who}: research_sources must start with a URL")

        for col in ("email_body", "subject_line", "personalized_opening"):
            if PLACEHOLDER_RE.search(g(col)):
                errors.append(f"{who}: unfilled placeholder in {col}")
        if "[ADD " in g("email_body"):
            warnings.append(f"{who}: email_body still has [ADD …] sender details; fill research/authors/sender_config.json and rebuild")
        if not g("email_body"):
            errors.append(f"{who}: empty email_body")
        if not g("subject_line"):
            errors.append(f"{who}: empty subject_line")
        elif len(g("subject_line")) > 60:
            warnings.append(f"{who}: subject_line over 60 characters")
        if re.match(r"^(re|fwd?)\s*:", g("subject_line"), re.IGNORECASE):
            errors.append(f"{who}: subject_line must not start with Re:/Fwd:")
        if BANNED_OPENING.search(g("personalized_opening")):
            errors.append(f"{who}: personalized_opening claims to have read / been inspired by the book")

        if g("research_confidence") not in CONFIDENCE:
            errors.append(f"{who}: research_confidence '{g('research_confidence')}' not in {sorted(CONFIDENCE)}")
        if g("personalization_status") not in PERSONALIZATION:
            errors.append(f"{who}: personalization_status '{g('personalization_status')}' invalid")
        if g("research_confidence") == "Low" and g("personalization_status") == "Ready":
            errors.append(f"{who}: Low confidence rows must be 'Needs review'")

        status = g("send_status")
        if status not in SEND_STATUS and status not in {"Sent", "Replied", "Bounced", "Unsubscribed", "Do not contact"}:
            errors.append(f"{who}: send_status '{status}' invalid")
        if status == "Not sent" and g("date_sent"):
            warnings.append(f"{who}: date_sent filled but send_status is 'Not sent'")

        country = g("country")
        if country in HOLD_COUNTRIES and status == "Not sent":
            errors.append(f"{who}: {country} rows must be 'Hold – legal review'")
        if NON_US_COUNTRIES_HOLD_DEFAULT and country and country not in {"United States", *HOLD_COUNTRIES} \
                and status == "Not sent" and "corporate" not in g("notes").lower():
            warnings.append(f"{who}: {country} row is 'Not sent' without a corporate-subscriber note")

        if "evidence_type" in header and g("evidence_type") not in EVIDENCE:
            errors.append(f"{who}: evidence_type '{g('evidence_type')}' invalid")
        if g("evidence_type") == "amazon_snippet_unverified" and g("research_confidence") == "High":
            errors.append(f"{who}: unverified snippet evidence cannot be High confidence")
        if "publishing_label" in header and g("publishing_label") not in PUBLISHING:
            errors.append(f"{who}: publishing_label '{g('publishing_label')}' invalid")
        if "language" in header and g("language") and g("language") not in LANGUAGES:
            warnings.append(f"{who}: language '{g('language')}' has no template; should be Needs review")
        if "date_checked" in header and not DATE_RE.match(g("date_checked")):
            errors.append(f"{who}: date_checked must be YYYY-MM-DD")

        for col, val in r.items():
            if not val or col in ("email_body", "research_sources", "amazon_author_url", "asins_isbns",
                                  "amazon_author_id", "batch_id", "dedupe_key", "date_checked", "date_sent"):
                continue
            if PHONE_RE.search(val):
                warnings.append(f"{who}: possible phone number in {col}")
            if STREET_RE.search(val):
                errors.append(f"{who}: possible street address in {col}")

    return header, rows, errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="author_spotlight_prospects.csv")
    ap.add_argument("--before", help="backup taken before the merge, for before/after counts")
    args = ap.parse_args()

    header, rows, errors, warnings = check(args.path)
    n, keys, emails = stats(rows)

    print(f"File: {args.path}")
    if args.before:
        _, before_rows = load(args.before)
        bn, bkeys, bemails = stats(before_rows)
        print(f"Rows:              {bn} -> {n}")
        print(f"Unique dedupe keys: {bkeys} -> {keys}")
        print(f"Email-bearing rows: {bemails} -> {emails}")
        before_keys = {r.get('dedupe_key', '').strip() for r in before_rows}
        new = [r for r in rows if r.get("dedupe_key", "").strip() not in before_keys]
        print(f"New authors: {len(new)}")
        for r in new:
            print(f"  - {r.get('author_name')} | {r.get('country')}/{r.get('region')} | "
                  f"{r.get('evidence_type')} | {r.get('research_confidence')}")
    else:
        print(f"Rows: {n} · unique dedupe keys: {keys} · email-bearing rows: {emails}")

    for col in ("country", "personalization_status", "send_status", "research_confidence", "evidence_type"):
        if col in header:
            c = Counter((r.get(col) or "").strip() or "(blank)" for r in rows)
            print(f"{col}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print("\nStatus: " + ("PASS" if not errors else "FAIL"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

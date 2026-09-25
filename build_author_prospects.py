#!/usr/bin/env python3
"""Merge a researched batch of authors into the canonical Author Spotlight file.

Usage:
    python3 build_author_prospects.py research/authors/us_alabama_batch1.json
    python3 build_author_prospects.py --refresh-bodies   # after filling sender_config.json

- Reads the latest author_spotlight_prospects.csv (creates it if missing).
- Backs it up to backups/ before writing.
- Builds subject/body from the templates in
  prompts/Amazon_Author_Spotlight_Outreach_Prompt.md (single source of truth).
- Idempotent: an author already in the file (same Amazon ID, email, or
  normalized name) is never added twice; only new emails/sources are appended,
  and existing cells (including manual edits) are never overwritten.
- Appends the batch's search log to research/authors/research_log.csv.
- Runs check_author_prospects.py against the result.
"""

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime

from check_author_prospects import AUDIT_COLUMNS, REQUIRED_COLUMNS

ROOT = os.path.dirname(os.path.abspath(__file__))
CANONICAL = os.path.join(ROOT, "author_spotlight_prospects.csv")
BACKUPS = os.path.join(ROOT, "backups")
PROMPT = os.path.join(ROOT, "prompts", "Amazon_Author_Spotlight_Outreach_Prompt.md")
SENDER_CONFIG = os.path.join(ROOT, "research", "authors", "sender_config.json")
LOG = os.path.join(ROOT, "research", "authors", "research_log.csv")
LOG_COLUMNS = ["batch_id", "date", "region", "city", "query", "candidates", "emails",
               "source_urls", "evidence_type", "decision", "reason"]
COLUMNS = REQUIRED_COLUMNS + AUDIT_COLUMNS

HOLD = "Hold – legal review"


def fold(s):
    s = s.replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def normalize_name(name):
    s = fold(name).lower()
    s = re.sub(r"\b[a-z]\.\s*", "", s) if len(s.split()) > 2 else s  # drop middle initials
    return re.sub(r"[^a-z ]", "", s).strip()


def load_templates():
    text = open(PROMPT, encoding="utf-8").read()
    found = re.findall(r"#{3,4} Template (EN|DE|FR|ES|IT|NL)[^\n]*\n\n```\n(.*?)```", text, re.S)
    return {lang: body.rstrip("\n") for lang, body in found}


def load_config():
    cfg = {}
    if os.path.exists(SENDER_CONFIG):
        cfg = json.load(open(SENDER_CONFIG, encoding="utf-8"))
    return cfg


def render(template, fields, cfg, lang):
    body = template
    paid = str(cfg.get("FEATURE_IS_PAID", "")).strip().lower()
    lines = []
    for line in body.split("\n"):
        if line.startswith("[paid] "):
            if paid == "yes":
                lines.append(line[len("[paid] "):])
            continue
        lines.append(line)
    body = "\n".join(lines)
    if lang == "EN" and not fields.get("first_name"):
        body = body.replace("Hi {first_name},", "Hi,", 1)
    values = dict(fields)
    for key in ("SENDER_NAME", "SENDER_TITLE", "WEBSITE", "POSTAL_ADDRESS", "PRIVACY_URL", "IMPRINT_URL"):
        values[key] = cfg.get(key) or f"[ADD {key}]"
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), body)


def default_send_status(a):
    if a.get("country") == "United States":
        return "Not sent"
    if a.get("country") == "United Kingdom" and "corporate" in a.get("notes", "").lower():
        return "Not sent"
    return HOLD


def load_rows():
    if not os.path.exists(CANONICAL):
        return list(COLUMNS), []
    with open(CANONICAL, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        header = list(r.fieldnames or [])
        rows = list(r)
    for c in COLUMNS:  # add any missing columns, keep user's extra ones
        if c not in header:
            header.append(c)
    return header, rows


def write_atomic(path, header, rows):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".csv")
    with os.fdopen(fd, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in header})
    os.replace(tmp, path)


def merge_list(existing, new, sep):
    items = [x.strip() for x in existing.split(sep.strip()) if x.strip()]
    lower = {x.lower() for x in items}
    for x in (y.strip() for y in new.split(sep.strip()) if y.strip()):
        if x.lower() not in lower:
            items.append(x)
            lower.add(x.lower())
    return sep.join(items)


def refresh_bodies(rows, templates, cfg):
    """Re-render email_body for unsent rows whose body still has [ADD …] sender placeholders."""
    n = 0
    for row in rows:
        if row.get("send_status") not in ("Not sent", HOLD) or "[ADD " not in row.get("email_body", ""):
            continue
        lang = row.get("language") or "EN"
        tmpl = templates.get(lang) or templates["EN"]
        m = re.search(r"(?:found your contact email on|Kontaktadresse habe ich auf|adresse de contact sur|"
                      r"dirección de contacto en|indirizzo di contatto su|contactadres op) (.+?)(?:\.| gefunden\.)",
                      row["email_body"])
        fields = {k: row.get(k, "") for k in ("first_name", "author_name", "book_title", "personalized_opening")}
        fields["source_description"] = m.group(1) if m else "your Amazon author page"
        row["email_body"] = render(tmpl, fields, cfg, lang)
        n += 1
    return n


def main():
    if sys.argv[1:] == ["--refresh-bodies"]:
        header, rows = load_rows()
        os.makedirs(BACKUPS, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BACKUPS, f"author_spotlight_prospects_{stamp}.csv")
        shutil.copy2(CANONICAL, backup)
        n = refresh_bodies(rows, load_templates(), load_config())
        write_atomic(CANONICAL, header, rows)
        print(f"Refreshed {n} email bodies")
        sys.exit(subprocess.call([sys.executable, os.path.join(ROOT, "check_author_prospects.py"), CANONICAL,
                                  "--before", backup]))

    batch_path = sys.argv[1]
    batch = json.load(open(batch_path, encoding="utf-8"))
    templates = load_templates()
    cfg = load_config()

    header, rows = load_rows()
    before = len(rows)

    if os.path.exists(CANONICAL):
        os.makedirs(BACKUPS, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BACKUPS, f"author_spotlight_prospects_{stamp}.csv")
        shutil.copy2(CANONICAL, backup)
    else:
        backup = None

    def ids_of(row):
        ids = set(re.findall(r"B0[0-9A-Z]{8}", row.get("amazon_author_url", "") + " " + row.get("amazon_author_id", "")))
        return ids

    added, merged = [], []
    for a in batch["authors"]:
        a_ids = ids_of(a)
        a_emails = {e.strip().lower() for e in a["email"].split(";") if e.strip()}
        a_names = {normalize_name(a["author_name"])} | {
            normalize_name(p) for p in a.get("pen_names_aliases", "").split(";") if p.strip()}

        match = None
        for row in rows:
            r_emails = {e.strip().lower() for e in row.get("email", "").split(";") if e.strip()}
            r_names = {normalize_name(row.get("author_name", ""))} | {
                normalize_name(p) for p in row.get("pen_names_aliases", "").split(";") if p.strip()}
            if (a_ids & ids_of(row)) or (a_emails & r_emails) or (a_names & r_names):
                match = row
                break

        if match:
            match["email"] = merge_list(match.get("email", ""), a["email"], "; ")
            match["research_sources"] = merge_list(match.get("research_sources", ""), a["research_sources"], " | ")
            match["pen_names_aliases"] = merge_list(match.get("pen_names_aliases", ""), a.get("pen_names_aliases", ""), "; ")
            merged.append(a["author_name"])
            continue

        lang = a.get("language", "EN")
        tmpl = templates.get(lang) or templates["EN"]
        fields = {k: a.get(k, "") for k in ("first_name", "author_name", "book_title", "personalized_opening",
                                            "source_description")}
        row = {c: a.get(c, "") for c in COLUMNS}
        row["email_body"] = render(tmpl, fields, cfg, lang)
        low = a.get("evidence_type") == "amazon_snippet_unverified"
        row["research_confidence"] = a.get("research_confidence") or ("Low" if low else "Medium")
        row["personalization_status"] = a.get("personalization_status") or (
            "Needs review" if row["research_confidence"] == "Low" or lang not in templates else "Ready")
        row["send_status"] = default_send_status(a)
        row["date_sent"] = ""
        row["dedupe_key"] = a.get("amazon_author_id") or (
            normalize_name(a["author_name"]) + "|" + re.sub(r"^https?://(www\.)?", "", a.get("official_website", "")).split("/")[0])
        row["batch_id"] = batch["batch_id"]
        row["date_checked"] = batch["date_checked"]
        rows.append(row)
        added.append(a["author_name"])

    write_atomic(CANONICAL, header, rows)

    # research log, deduplicated on (batch_id, query, candidates)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    existing = set()
    if os.path.exists(LOG):
        with open(LOG, newline="", encoding="utf-8-sig") as f:
            existing = {(r["batch_id"], r["query"], r["candidates"]) for r in csv.DictReader(f)}
    new_log = [[batch["batch_id"], batch["date_checked"], *entry] for entry in batch.get("log", [])]
    new_log = [e for e in new_log if (e[0], e[4], e[5]) not in existing]
    write_header = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8-sig" if write_header else "utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(LOG_COLUMNS)
        w.writerows(new_log)

    print(f"Rows {before} -> {len(rows)}; added {len(added)}: {added}; merged into existing: {merged}")
    print(f"Research log entries appended: {len(new_log)}")
    cmd = [sys.executable, os.path.join(ROOT, "check_author_prospects.py"), CANONICAL]
    if backup:
        cmd += ["--before", backup]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()

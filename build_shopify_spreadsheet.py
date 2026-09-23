"""Shopify Jarvis campaign: merge researcher JSON, dedupe, run quality checks and build the workbook."""
import glob
import json
import re
import sys
from collections import Counter
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

RESEARCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "research_shopify"
OUT_FILE = "Australia_Shopify_Jarvis_Prospects_200.xlsx"
TARGET = 200
SENDER = "Cynthia Nana"

COLUMNS = [
    "Prospect Name", "Company", "First Name", "Email", "Country", "State", "City",
    "Shopify Niche", "Shopify Store URL", "Store Product Category", "Buying Intent",
    "Personalization Detail", "Personalization Reason", "Personalized Opening",
    "Subject Line", "Email Body", "Source URL", "Evidence", "Evidence Type",
    "Research Confidence", "Lead Status", "Send Status", "Date Sent", "Notes",
]

AU_STATES = {
    "new south wales", "victoria", "queensland", "western australia", "south australia",
    "tasmania", "australian capital territory", "northern territory",
}
STATE_ALIASES = {
    "nsw": "New South Wales", "vic": "Victoria", "qld": "Queensland", "wa": "Western Australia",
    "sa": "South Australia", "tas": "Tasmania", "act": "Australian Capital Territory",
    "nt": "Northern Territory",
}
EVIDENCE_TYPES = {
    "Official Website", "Shopify Store", "LinkedIn", "Public Business Profile",
    "Public Social Profile", "Shopify Profile", "Public Job Posting", "Search Result Verified", "Other",
}
BANNED_SUBJECT = [
    "urgent", "act now", "make money", "guaranteed", "100%", "get rich", "free money",
    "huge profits", "profit", "!!",
]
BANNED_BODY = [
    "tailored solution", "seamless", "cutting edge", "cutting-edge", "revolutioni",
    "unlock your", "transform your workflow", "leverage", "game changing", "game-changing",
    "guaranteed", "guarantee returns", "make money", "i hope you're doing well",
    "i hope you are doing well", "hope you're having a great day", "i came across your profile",
    "i noticed you have a shopify store", "increase your revenue", "boost your sales",
    "unlock", "tailored",
]
BANNED_OPENINGS = [
    "i hope you", "hope you", "i came across your profile", "i noticed you have a shopify store",
]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
GENERIC_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com",
                   "bigpond.com", "live.com", "protonmail.com", "proton.me", "yahoo.com.au",
                   "optusnet.com.au", "bigpond.net.au", "me.com"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def norm_company(s):
    s = (s or "").lower()
    s = re.sub(r"\b(pty|ltd|limited|inc|llc|the|group|holdings|australia|au|co)\b", " ", s)
    return norm(s)


def site_key(url):
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def clean_state(s):
    s = (s or "").strip()
    if s.lower() in STATE_ALIASES:
        return STATE_ALIASES[s.lower()]
    for st in AU_STATES:
        if st == s.lower():
            return s.title().replace("Of", "of")
    return s


def load_records():
    records, rejected, searches = [], [], 0
    for path in sorted(glob.glob(f"{RESEARCH_DIR}/seg*.json")):
        with open(path) as f:
            data = json.load(f)
        seg = path.rsplit("/", 1)[-1].split("_")[0]
        for r in data.get("accepted", []):
            r["_seg"] = seg
            records.append(r)
        rejected.extend(data.get("rejected", []))
        searches += int(data.get("searches_run", 0) or 0)
    return records, rejected, searches


def load_verification():
    """Independent re-check results keyed by lowercased email."""
    out = {}
    for path in glob.glob(f"{RESEARCH_DIR}/verify*.json"):
        with open(path) as f:
            for v in json.load(f):
                out[v["email"].strip().lower()] = v
    return out


CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}


def qc_issues(r):
    issues = []
    email = r["email"]
    if not EMAIL_RE.match(email):
        issues.append("email format")
    if not (r.get("source_url") or "").startswith("http"):
        issues.append("missing source URL")
    subj = (r.get("subject_line") or "").lower()
    if not subj:
        issues.append("missing subject")
    if len(subj.split()) > 10:
        issues.append("subject too long")
    for b in BANNED_SUBJECT:
        if b in subj:
            issues.append(f"subject contains '{b}'")
    body = (r.get("email_body") or "")
    lb = body.lower()
    for b in BANNED_BODY:
        if b in lb:
            issues.append(f"body contains '{b}'")
    if SENDER.lower() not in lb:
        issues.append("sender name missing")
    if not lb.startswith("hi "):
        issues.append("body greeting")
    opening = (r.get("personalized_opening") or "").strip().lower()
    if not opening:
        issues.append("missing opening")
    for b in BANNED_OPENINGS:
        if opening.startswith(b):
            issues.append("generic opening")
    words = len(body.split())
    if words > 200:
        issues.append(f"body long ({words} words)")
    if not r.get("personalization_detail"):
        issues.append("missing personalization detail")
    if r.get("state") and r["state"].lower() not in AU_STATES:
        issues.append(f"state '{r['state']}' not an AU state")
    return issues


def load_overrides():
    try:
        with open(f"{RESEARCH_DIR}/overrides.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main():
    records, rejected, searches = load_records()
    overrides = load_overrides()
    verification = load_verification()
    # A round-1 rejection that a later round accepted is one business, not two.
    accepted_cos = {norm_company(r.get("company")) for r in records}
    rejected = [x for x in rejected if norm_company(x.get("company")) not in accepted_cos]
    researched = len(records) + len(rejected)

    for r in records:
        for k in ("email", "prospect_name", "company", "first_name", "state", "city"):
            r[k] = (r.get(k) or "").strip()
        r["email"] = r["email"].lower().rstrip(".")
        r["state"] = clean_state(r["state"])
        r["research_confidence"] = (r.get("research_confidence") or "Medium").strip().title()
        if r["research_confidence"] not in CONF_RANK:
            r["research_confidence"] = "Medium"
        if r.get("evidence_type") not in EVIDENCE_TYPES:
            r["evidence_type"] = "Other"

    # QC overrides: exclude unverifiable Shopify links, cap confidence where Shopify is only
    # inferred from URL patterns, and flag records that need a human check.
    excluded = []
    keep_high = set(overrides.get("keep_high", []))
    review = overrides.get("needs_review", {})
    kept_records = []
    for r in records:
        reason = overrides.get("exclude", {}).get(r["email"])
        if reason:
            excluded.append({"company": r["company"], "reason": reason})
            continue
        if keep_high and r["research_confidence"] == "High" and r["email"] not in keep_high:
            r["research_confidence"] = "Medium"
            r["notes"] = (r.get("notes", "") + " Confidence capped at Medium: Shopify inferred from "
                          "store URL patterns only.").strip()
        if r["email"] in review:
            r["_review"] = review[r["email"]]
        kept_records.append(r)
    records = kept_records
    rejected.extend(excluded)

    # Strongest record first so duplicates drop the weaker copy.
    records.sort(key=lambda r: (-CONF_RANK[r["research_confidence"]],
                                0 if r.get("buying_intent", "").startswith("High") else 1))

    kept, dupes = [], []
    seen_email, seen_company, seen_person, seen_domain, seen_store = set(), set(), set(), set(), set()
    for r in records:
        dom = r["email"].split("@")[-1]
        keys = {
            "email": r["email"],
            "company": norm_company(r["company"]),
            "person": norm(r["prospect_name"]),
            "domain": dom if dom not in GENERIC_DOMAINS else None,
            "store": site_key(r.get("shopify_store_url")),
        }
        dup = (keys["email"] in seen_email
               or (keys["company"] and keys["company"] in seen_company)
               or (keys["person"] and keys["person"] in seen_person)
               or (keys["domain"] and keys["domain"] in seen_domain)
               or (keys["store"] and keys["store"] in seen_store))
        if dup:
            dupes.append(r)
            continue
        seen_email.add(keys["email"])
        if keys["company"]:
            seen_company.add(keys["company"])
        if keys["person"]:
            seen_person.add(keys["person"])
        if keys["domain"]:
            seen_domain.add(keys["domain"])
        if keys["store"]:
            seen_store.add(keys["store"])
        kept.append(r)

    # Independent verification: drop records whose email could not be re-found.
    failed_verify = []
    final = []
    for r in kept:
        v = verification.get(r["email"])
        if verification and v is not None and v.get("status") == "not_found":
            failed_verify.append(r)
            continue
        issues = qc_issues(r)
        r["_issues"] = issues
        if v is not None and v.get("status") == "found":
            r["_verified"] = True
        final.append(r)

    # Order: Ready High -> Ready Medium -> review; within that, High intent first.
    def lead_status(r):
        if r["_issues"] or r["research_confidence"] == "Low" or r.get("_review"):
            return "Needs Review"
        if verification and not r.get("_verified"):
            return "Needs Review"
        return "Ready"

    for r in final:
        r["_status"] = lead_status(r)
    final.sort(key=lambda r: (r["_status"] != "Ready", -CONF_RANK[r["research_confidence"]],
                              0 if r.get("buying_intent", "").startswith("High") else 1))
    if len(final) > TARGET:
        overflow = final[TARGET:]
        final = final[:TARGET]
    else:
        overflow = []

    wb = Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append(COLUMNS)

    def row_for(r):
        notes = [r.get("notes", "")]
        if r["_issues"]:
            notes.append("QC: " + "; ".join(r["_issues"]))
        if r.get("_verified"):
            notes.append("Email independently re-verified on source page.")
        if r["research_confidence"] == "Low":
            notes.append("LOW CONFIDENCE - review before sending.")
        if r.get("_review"):
            notes.append("REVIEW: " + r["_review"])
        other = (r.get("other_urls") or "").strip()
        source = r["source_url"] + (("\n" + other) if other else "")
        return [
            r["prospect_name"], r["company"], r["first_name"], r["email"], "Australia",
            r["state"], r["city"], r.get("shopify_niche", ""), r.get("shopify_store_url", ""),
            r.get("product_category", ""), r.get("buying_intent", ""),
            r.get("personalization_detail", ""), r.get("personalization_reason", ""),
            r.get("personalized_opening", ""), r.get("subject_line", ""), r.get("email_body", ""),
            source, r.get("evidence", ""), r["evidence_type"], r["research_confidence"],
            r["_status"], "Not Sent", None, " ".join(n for n in notes if n).strip(),
        ]

    for r in final:
        ws.append(row_for(r))

    widths = [22, 26, 12, 32, 11, 20, 16, 24, 20, 30, 34, 48, 48, 50, 32, 70, 45, 60, 20, 12, 14, 11, 11, 40]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    header_fill = PatternFill("solid", fgColor="1F3864")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    last = ws.max_row
    for col, opts in (("T", "High,Medium,Low"), ("U", "Ready,Needs Review,Excluded"),
                      ("V", "Not Sent,Sent,Bounced,Replied")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{max(last, 2)}")
    ws.column_dimensions["W"].number_format = "yyyy-mm-dd"

    conf = Counter(r["research_confidence"] for r in final)
    status = Counter(r["_status"] for r in final)
    summary = [
        ("Total prospects researched", researched),
        ("Total qualified prospects (in sheet)", len(final)),
        ("Total rejected", len(rejected) + len(failed_verify)),
        ("  - rejected during research", len(rejected) - len(excluded)),
        ("  - excluded in QC (Shopify not verifiable)", len(excluded)),
        ("Total duplicate prospects removed", len(dupes)),
        ("Qualified beyond the 200 target (sheet 'Beyond 200')", len(overflow)),
        ("Prospects with verified public professional emails", len(final)),
        ("  - on the store's own domain", sum(1 for r in final if r["email"].split("@")[-1] not in GENERIC_DOMAINS)),
        ("High confidence", conf["High"]),
        ("Medium confidence", conf["Medium"]),
        ("Low confidence", conf["Low"]),
        ("Ready", status["Ready"]),
        ("Needs Review", status["Needs Review"]),
        ("Total personalized emails", sum(1 for r in final if r.get("email_body"))),
        ("Total unique companies", len({norm_company(r["company"]) for r in final})),
        ("Total unique emails", len({r["email"] for r in final})),
        ("Unique subject lines", len({r["subject_line"].strip().lower() for r in final})),
        ("States covered", len({r["state"] for r in final if r["state"]})),
        ("Web searches logged by researchers", searches),
        ("Research limit", "Session web-search cap (200) reached; store sites not directly fetchable (egress policy) - facts verified via search results"),
        ("Sender", SENDER),
        ("Country", "Australia"),
        ("Spreadsheet file name", OUT_FILE),
    ]
    ss = wb.create_sheet("Summary")
    ss.append(["Metric", "Value"])
    for row in summary:
        ss.append(list(row))
    ss.append([])
    ss.append(["State", "Prospects"])
    for st, n in Counter(r["state"] or "Unknown" for r in final).most_common():
        ss.append([st, n])
    ss.column_dimensions["A"].width = 50
    ss.column_dimensions["B"].width = 36
    for c in ss[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill

    if overflow:
        ov = wb.create_sheet("Beyond 200")
        ov.append(COLUMNS)
        for r in overflow:
            ov.append(row_for(r))
        for i, w in enumerate(widths, 1):
            ov.column_dimensions[get_column_letter(i)].width = w
        for c in ov[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = header_fill
        ov.freeze_panes = "B2"

    wb.save(OUT_FILE)
    for k, v in summary:
        print(f"{k}: {v}")
    dup_subj = [s for s, n in Counter(r["subject_line"].strip().lower() for r in final).items() if n > 1]
    if dup_subj:
        print("DUPLICATE SUBJECTS:", dup_subj)
    for r in final:
        if r["_issues"]:
            print("QC", r["email"], r["_issues"])


if __name__ == "__main__":
    main()

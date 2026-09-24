"""Build Australia_Trading_Bot_Prospects_200.xlsx from fresh researcher JSON.

Usage: python build_spreadsheet.py <research_dir>

<research_dir> holds seg*.json files from the research agents and verify_auto.json from
verify_emails.py (a live re-fetch of each source page confirming the email is displayed).
"""
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

RESEARCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "research"
OUT_FILE = "Australia_Trading_Bot_Prospects_200.xlsx"
TARGET = 200
SENDER_EMAIL = "goodfiberr@gmail.com"
SENDER_NAME = "Gabriel"

COLUMNS = [
    "Prospect Name", "Company", "First Name", "Email", "Country", "State", "City",
    "Trading Niche", "Trading Platform", "Trading Product or Project", "Buying Intent",
    "Personalization Detail", "Personalization Reason", "Personalized Opening",
    "Subject Line", "Email Body", "Source URL", "Evidence", "Evidence Type",
    "Research Confidence", "Lead Status", "Send Status", "Date Sent", "Notes",
]
AU_STATES = [
    "New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia",
    "Tasmania", "Australian Capital Territory", "Northern Territory",
]
STATE_ALIASES = {
    "nsw": "New South Wales", "vic": "Victoria", "qld": "Queensland", "wa": "Western Australia",
    "sa": "South Australia", "tas": "Tasmania", "act": "Australian Capital Territory",
    "nt": "Northern Territory",
}
EVIDENCE_TYPES = {
    "Official Website", "LinkedIn", "Public Business Profile", "Trading Website",
    "Developer Profile", "Public Forum", "Public Social Profile", "Search Result Verified", "Other",
}
BANNED_SUBJECT = [
    "urgent", "act now", "make money", "guarantee", "100%", "get rich", "free money",
    "investment opportunity", "crypto profits", "profit", "returns", "!!",
]
BANNED_BODY = [
    "tailored solution", "seamless", "cutting edge", "cutting-edge", "revolutioni",
    "unlock your", "transform your workflow", "leverage", "game changing", "game-changing",
    "guaranteed", "make money", "hope you're doing well", "hope you are doing well",
    "having a great day", "i came across your profile", "i noticed you are a trader",
]
BANNED_OPENINGS = ["i hope", "hope you", "i came across your profile", "i noticed you are a trader"]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
FREE_MAIL = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com", "live.com",
             "bigpond.com", "bigpond.net.au", "protonmail.com", "proton.me", "yahoo.com.au",
             "optusnet.com.au", "me.com"}
# GitHub's Acceptable Use Policy forbids using its data for unsolicited email.
EXCLUDED_SOURCE_HOSTS = {"github.com"}
CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}

# Sub-brands of one business count as the same prospect; map each email to its group key.
SAME_BUSINESS = {
    "support@blueberryfunded.com": "blueberry", "support@blueberrymarkets.com": "blueberry",
    "support@thinkcapital.com": "thinkmarkets", "support@thinkmarkets.com": "thinkmarkets",
    "support@challenges.eightcap.com": "eightcap", "customerservice@eightcap.com": "eightcap",
}
# Removed at QC: the Australian connection or the source page could not be established.
QC_EXCLUDE = {
    "info@sunrisetechs.com": "Australian presence unconfirmed (appears India-based; Sydney address may be a serviced office)",
    "info@motifmarkets.com": "Australian location unconfirmed; source page is the US site",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def norm_company(s):
    s = (s or "").lower()
    s = re.sub(r"\b(pty|ltd|limited|inc|llc|the|group|holdings|australia|au|co|trading|markets?)\b", " ", s)
    return norm(s)


def host(url):
    h = urlparse(url or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def clean_state(s):
    s = (s or "").strip()
    if s.lower() in STATE_ALIASES:
        return STATE_ALIASES[s.lower()]
    for st in AU_STATES:
        if st.lower() == s.lower():
            return st
    return s


def load():
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
    verify = {}
    vpath = f"{RESEARCH_DIR}/verify_auto.json"
    try:
        for v in json.load(open(vpath)):
            if v["status"] == "found" or v["email"] not in verify:
                verify[v["email"]] = v
    except FileNotFoundError:
        pass
    return records, rejected, searches, verify


def qc_issues(r):
    issues = []
    if not EMAIL_RE.match(r["email"]):
        issues.append("email format")
    if not (r.get("source_url") or "").startswith("http"):
        issues.append("missing source URL")
    subj = (r.get("subject_line") or "").lower()
    if not subj:
        issues.append("missing subject")
    elif len(subj.split()) > 10:
        issues.append("subject too long")
    issues += [f"subject contains '{b}'" for b in BANNED_SUBJECT if b in subj]
    body = r.get("email_body") or ""
    lb = body.lower()
    issues += [f"body contains '{b}'" for b in BANNED_BODY if b in lb]
    if SENDER_EMAIL not in lb:
        issues.append("sender email missing")
    if not lb.startswith("hi "):
        issues.append("body greeting")
    if "{sender_name}" in lb:
        issues.append("unfilled sender token")
    opening = (r.get("personalized_opening") or "").strip().lower()
    if not opening:
        issues.append("missing opening")
    elif any(opening.startswith(b) for b in BANNED_OPENINGS):
        issues.append("generic opening")
    if len(body.split()) > 200:
        issues.append(f"body long ({len(body.split())} words)")
    if not r.get("personalization_detail"):
        issues.append("missing personalization detail")
    if r["state"] not in AU_STATES:
        issues.append(f"state '{r['state']}' not an Australian state/territory")
    return issues


def main():
    records, rejected, searches, verify = load()
    researched = len(records) + len(rejected)

    policy = [r for r in records if host(r.get("source_url")) in EXCLUDED_SOURCE_HOSTS]
    records = [r for r in records if host(r.get("source_url")) not in EXCLUDED_SOURCE_HOSTS]
    rejected += [{"name": r.get("prospect_name"), "reason": "GitHub-only email source"} for r in policy]

    for r in records:
        r["email"] = (r.get("email") or "").strip().lower()
    excluded = [r for r in records if r["email"] in QC_EXCLUDE]
    records = [r for r in records if r["email"] not in QC_EXCLUDE]
    rejected += [{"name": r.get("prospect_name"), "reason": QC_EXCLUDE[r["email"]]} for r in excluded]

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
        r["email_body"] = (r.get("email_body") or "").replace("{SENDER_NAME}", SENDER_NAME).strip()
        r["_verified"] = verify.get(r["email"], {}).get("status") == "found"

    # Strongest record first, so a duplicate always drops the weaker copy.
    records.sort(key=lambda r: (not r["_verified"], -CONF_RANK[r["research_confidence"]],
                                not (r.get("buying_intent") or "").startswith("High")))
    kept, dupes = [], []
    seen = {"email": set(), "company": set(), "person": set(), "domain": set(), "group": set()}
    for r in records:
        dom = r["email"].split("@")[-1]
        keys = {
            "email": r["email"],
            "company": norm_company(r["company"]) or None,
            "person": norm(r["prospect_name"]) or None,
            "domain": dom if dom not in FREE_MAIL else None,
            "group": SAME_BUSINESS.get(r["email"]),
        }
        if any(v and v in seen[k] for k, v in keys.items()):
            dupes.append(r)
            continue
        for k, v in keys.items():
            if v:
                seen[k].add(v)
        kept.append(r)

    for r in kept:
        issues = qc_issues(r)
        if not r["_verified"]:
            issues.append("email seen in search results only - source page could not be opened this session; confirm it on the live page before sending")
        if r["email"].split("@")[-1] in FREE_MAIL:
            issues.append("free-mail address published by the prospect")
        r["_issues"] = issues
        hard = [i for i in issues if not i.startswith("free-mail")]
        r["_status"] = "Needs Review" if hard or r["research_confidence"] == "Low" else "Ready"

    kept.sort(key=lambda r: (r["_status"] != "Ready", -CONF_RANK[r["research_confidence"]],
                             not (r.get("buying_intent") or "").startswith("High"), r["state"], r["company"]))
    overflow = kept[TARGET:]
    final = kept[:TARGET]

    wb = Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append(COLUMNS)
    for r in final:
        notes = [r.get("notes") or ""]
        if r["_verified"]:
            notes.append(f"Email re-confirmed on {verify[r['email']]['url']} by live page fetch.")
        if r["_issues"]:
            notes.append("QC: " + "; ".join(r["_issues"]))
        if SENDER_NAME in r["email_body"]:
            notes.append("Replace the sender name in the sign-off before sending.")
        other = (r.get("other_urls") or "").strip()
        source = r["source_url"] + ("\n" + "\n".join(other.split()) if other else "")
        ws.append([
            r["prospect_name"], r["company"], r["first_name"], r["email"], "Australia",
            r["state"], r["city"], r.get("trading_niche", ""), r.get("trading_platform", ""),
            r.get("product_project", ""), r.get("buying_intent", ""),
            r.get("personalization_detail", ""), r.get("personalization_reason", ""),
            r.get("personalized_opening", ""), r.get("subject_line", ""), r["email_body"],
            source, r.get("evidence", ""), r["evidence_type"], r["research_confidence"],
            r["_status"], "Not Sent", None, " ".join(n for n in notes if n).strip(),
        ])

    widths = [24, 28, 12, 34, 11, 22, 16, 22, 22, 32, 36, 48, 48, 50, 34, 70, 48, 60, 20, 12, 14, 11, 11, 44]
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
    last = max(ws.max_row, 2)
    for col, opts in (("T", "High,Medium,Low"), ("U", "Ready,Needs Review,Excluded"),
                      ("V", "Not Sent,Sent,Bounced,Replied")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{last}")
    for row in range(2, last + 1):
        ws[f"W{row}"].number_format = "yyyy-mm-dd"

    conf = Counter(r["research_confidence"] for r in final)
    status = Counter(r["_status"] for r in final)
    summary = [
        ("Total prospects researched", researched),
        ("Total qualified prospects (in sheet)", len(final)),
        ("Total rejected", len(rejected)),
        ("  - of which GitHub-only email source (policy)", len(policy)),
        ("  - of which removed at final QC", len(excluded)),
        ("Total duplicate prospects removed", len(dupes)),
        ("Qualified but beyond the 200 cap", len(overflow)),
        ("Prospects with publicly displayed professional emails", len(final)),
        ("Emails re-confirmed by live page fetch", sum(r["_verified"] for r in final)),
        ("High confidence", conf["High"]),
        ("Medium confidence", conf["Medium"]),
        ("Low confidence", conf["Low"]),
        ("Ready", status["Ready"]),
        ("Needs Review", status["Needs Review"]),
        ("High buying intent", sum((r.get("buying_intent") or "").startswith("High") for r in final)),
        ("Total personalized emails", sum(1 for r in final if r["email_body"])),
        ("Total unique companies", len({norm_company(r["company"]) for r in final})),
        ("Total unique emails", len({r["email"] for r in final})),
        ("Unique subject lines", len({(r.get("subject_line") or "").strip().lower() for r in final})),
        ("States/territories covered", len({r["state"] for r in final if r["state"] in AU_STATES})),
        ("Searches logged by researchers", searches),
        ("Sender email", SENDER_EMAIL),
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
    ss.column_dimensions["A"].width = 52
    ss.column_dimensions["B"].width = 38
    for c in ss[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill

    wb.save(OUT_FILE)
    for k, v in summary:
        print(f"{k}: {v}")
    dup_subj = [s for s, n in Counter((r.get("subject_line") or "").strip().lower() for r in final).items() if n > 1]
    if dup_subj:
        print("DUPLICATE SUBJECTS:", dup_subj)
    for r in final:
        if r["_issues"]:
            print("QC", r["email"], r["_issues"])
    for r in dupes:
        print("DUPE", r["_seg"], r["email"], r["company"])


if __name__ == "__main__":
    main()

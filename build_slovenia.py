"""Merge Slovenia researcher JSON batches, dedupe, run quality checks and build the workbook."""
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

RESEARCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "research_si"
OUT_FILE = "Slovenia_Dashboard_Development_Prospects.xlsx"

COLUMNS = [
    "Prospect Name", "Company", "First Name", "Job Title", "Email", "Country", "State", "City",
    "Website", "Industry", "Prospect Type", "Dashboard Type", "Current Systems", "Data Sources",
    "Current Workflow", "Pain Point", "Reporting Problem", "Monitoring Problem", "Automation Signal",
    "Commercial Signal", "Dashboard Opportunity", "Buying Intent", "Personalization Detail",
    "Personalization Reason", "Personalized Opening", "Subject Line", "Email Body", "Source URL",
    "Evidence", "Evidence Type", "Research Confidence", "Lead Status", "Send Status", "Date Sent",
    "Notes",
]
KEYS = [
    "prospect_name", "company", "first_name", "job_title", "email", None, "state", "city",
    "website", "industry", "prospect_type", "dashboard_type", "current_systems", "data_sources",
    "current_workflow", "pain_point", "reporting_problem", "monitoring_problem", "automation_signal",
    "commercial_signal", "dashboard_opportunity", "buying_intent", "personalization_detail",
    "personalization_reason", "personalized_opening", "subject_line", "email_body", "source_url",
    "evidence", "evidence_type", "research_confidence", "lead_status", None, None, "notes",
]

SI_REGIONS = {
    "Osrednjeslovenska", "Podravska", "Gorenjska", "Savinjska", "Obalno-kraška",
    "Jugovzhodna Slovenija", "Goriška", "Pomurska", "Koroška", "Primorsko-notranjska",
    "Zasavska", "Posavska",
}
EVIDENCE_TYPES = {
    "Official Website", "LinkedIn", "Job Posting", "GitHub", "Product Page", "Company Blog",
    "Public Post", "YouTube", "Forum", "Business Directory", "Other",
}
LEVELS = ("HIGH", "MEDIUM", "LOW")
STATUSES = ("Qualified", "Review", "Disqualified")
BANNED_SUBJECT = [
    "guaranteed", "make money", "free money", "urgent", "limited offer", "act now",
    "ai revolution", "100%", "best solution", "cheap", "special offer", "!",
]
BANNED_BODY = [
    "guaranteed", "revolutioni", "game-changing", "game changing", "cutting-edge",
    "best solution", "i hope you", "hope you're", "i've followed", "i have followed",
    "i spoke with", "i used your",
]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
FREEMAIL = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "siol.net", "t-2.net",
            "amis.net", "guest.arnes.si", "icloud.com"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def norm_company(s):
    s = (s or "").lower()
    s = re.sub(r"\b(d\.?o\.?o\.?|d\.?d\.?|s\.?p\.?|ltd|gmbh|inc|llc|group|skupina|slovenija|slovenia)\b",
               " ", s)
    return norm(s)


def domain(url):
    host = urlparse(url if "//" in (url or "") else "https://" + (url or "")).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def root_domain(host):
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def clean(r):
    for k in [k for k in KEYS if k]:
        v = r.get(k)
        r[k] = v.strip() if isinstance(v, str) else ("" if v is None else str(v))
    r["email"] = r["email"].lower().rstrip(".")
    r["buying_intent"] = r["buying_intent"].upper()
    r["research_confidence"] = r["research_confidence"].upper()
    r["lead_status"] = r["lead_status"].title()
    if r["evidence_type"] not in EVIDENCE_TYPES:
        r["evidence_type"] = "Other"
    if r["state"] and r["state"] not in SI_REGIONS:
        match = [x for x in SI_REGIONS if norm(x) == norm(r["state"])]
        r["state"] = match[0] if match else r["state"]
    if r["website"] and not r["website"].startswith("http"):
        r["website"] = "https://" + r["website"]


def qc_issues(r):
    """Return (blocking issues, soft issues). Blocking issues force Review."""
    hard, soft = [], []
    for field, lv in (("buying_intent", LEVELS), ("research_confidence", LEVELS),
                      ("lead_status", STATUSES)):
        if r[field] not in lv:
            hard.append(f"invalid {field} '{r[field]}'")
    if not r["website"]:
        hard.append("missing website")
    if not r["source_url"].startswith("http"):
        hard.append("missing source URL")
    if not r["evidence"]:
        hard.append("missing evidence")
    if not r["personalization_detail"]:
        hard.append("missing personalization detail")
    if not r["dashboard_opportunity"]:
        hard.append("missing dashboard opportunity")
    if r["email"]:
        if not EMAIL_RE.match(r["email"]):
            hard.append("email format")
        else:
            edom = r["email"].split("@")[1]
            if edom in FREEMAIL:
                soft.append("email on a free-mail domain")
            elif root_domain(edom) != root_domain(domain(r["website"])):
                soft.append(f"email domain {edom} differs from website domain")
    subj = r["subject_line"].lower()
    if not subj:
        hard.append("missing subject")
    for b in BANNED_SUBJECT:
        if b in subj:
            hard.append(f"subject contains '{b}'")
    body = r["email_body"]
    lb = body.lower()
    if "[sender name]" not in lb or "[sender title]" not in lb:
        hard.append("body missing [Sender Name]/[Sender Title]")
    if not lb.startswith("hi "):
        hard.append("body greeting")
    for b in BANNED_BODY:
        if b in lb:
            hard.append(f"body contains '{b}'")
    if len(body.split()) > 160:
        soft.append(f"body long ({len(body.split())} words)")
    if r["buying_intent"] == "HIGH" and r["research_confidence"] == "LOW":
        hard.append("HIGH intent with LOW confidence")
    if re.search(r"(website|domain)[^.;]*inferred|website inferred|taken from (its |the )?email",
                 r["notes"].lower()):
        hard.append("website inferred, not seen as official site")
    if r["state"] and r["state"] not in SI_REGIONS:
        soft.append(f"region '{r['state']}' not a Slovenian statistical region")
    return hard, soft


RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def main():
    records, batches = [], Counter()
    for path in sorted(glob.glob(f"{RESEARCH_DIR}/b*.json")):
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("leads") or data.get("accepted") or []
        batch = path.rsplit("/", 1)[-1].split("_")[0]
        for r in data:
            r["_batch"] = batch
            clean(r)
            records.append(r)
            batches[batch] += 1
    researched = len(records)

    # Strongest copy first so duplicates drop the weaker one.
    records.sort(key=lambda r: (RANK.get(r["research_confidence"], 3),
                                RANK.get(r["buying_intent"], 3)))
    seen = {"company": set(), "domain": set(), "email": set(), "person": set()}
    kept, dupes = [], []
    for r in records:
        keys = {
            "company": norm_company(r["company"]),
            "domain": root_domain(domain(r["website"])) if r["website"] else "",
            "email": r["email"],
            "person": (norm(r["first_name"] + r["prospect_name"]) + "|" + norm_company(r["company"]))
            if r["first_name"] else "",
        }
        if any(v and v in seen[k] for k, v in keys.items()):
            dupes.append(r)
            continue
        for k, v in keys.items():
            if v:
                seen[k].add(v)
        kept.append(r)

    for r in kept:
        hard, soft = qc_issues(r)
        r["_hard"], r["_soft"] = hard, soft
        if hard and r["lead_status"] == "Qualified":
            r["lead_status"] = "Review"
        if r["lead_status"] == "Qualified" and r["research_confidence"] == "LOW":
            r["lead_status"] = "Review"
        if r["lead_status"] not in STATUSES:
            r["lead_status"] = "Review"

    kept.sort(key=lambda r: (STATUSES.index(r["lead_status"]), RANK.get(r["buying_intent"], 3),
                             RANK.get(r["research_confidence"], 3), r["company"].lower()))

    wb = Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append(COLUMNS)
    for r in kept:
        notes = [r["notes"]]
        if r["_hard"] or r["_soft"]:
            notes.append("QC: " + "; ".join(r["_hard"] + r["_soft"]))
        notes.append("Opt-out: honour any unsubscribe/opt-out request; include opt-out line and "
                     "sender identity when sending (GDPR / ZEKom-2).")
        row = []
        for col, key in zip(COLUMNS, KEYS):
            if col == "Country":
                row.append("Slovenia")
            elif col == "Send Status":
                row.append("Not Sent")
            elif col == "Date Sent":
                row.append(None)
            elif col == "Notes":
                row.append(" ".join(n for n in notes if n).strip())
            else:
                row.append(r[key])
        ws.append(row)

    width = {"Email Body": 70, "Evidence": 50, "Notes": 50, "Source URL": 40, "Website": 30}
    for i, col in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(i)].width = width.get(col, 26)
    header_fill = PatternFill("solid", fgColor="1F3864")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    last = max(ws.max_row, 2)
    for col, opts in (("Buying Intent", "HIGH,MEDIUM,LOW"), ("Research Confidence", "HIGH,MEDIUM,LOW"),
                      ("Lead Status", "Qualified,Review,Disqualified"),
                      ("Send Status", "Not Sent,Sent,Bounced,Replied,Opted Out")):
        letter = get_column_letter(COLUMNS.index(col) + 1)
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{letter}2:{letter}{last}")

    # Research Summary sheet
    ss = wb.create_sheet("Research Summary")
    bold = Font(bold=True)

    def section(title, counter):
        ss.append([])
        ss.append([title, "Count"])
        for c in ss[ss.max_row]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = header_fill
        for k, n in counter.most_common():
            ss.append([k or "(blank)", n])

    status = Counter(r["lead_status"] for r in kept)
    intent = Counter(r["buying_intent"] for r in kept)
    emails = sum(1 for r in kept if r["email"])
    top = [
        ("Campaign", "Slovenia Custom Dashboard & Business Automation Outreach"),
        ("Sender email", "akintomideokewole485@gmail.com"),
        ("Total prospects researched (before dedupe)", researched),
        ("Duplicates removed", len(dupes)),
        ("Total Prospects", len(kept)),
        ("Qualified Prospects", status["Qualified"]),
        ("Review Prospects", status["Review"]),
        ("Disqualified Prospects", status["Disqualified"]),
        ("HIGH Buying Intent", intent["HIGH"]),
        ("MEDIUM Buying Intent", intent["MEDIUM"]),
        ("LOW Buying Intent", intent["LOW"]),
        ("Verified Emails", emails),
        ("Missing Emails", len(kept) - emails),
        ("Send Status", "All rows Not Sent; no emails were sent"),
        ("Research method", "Public web search results (company pages could not be fetched from the "
                            "research environment); re-check each email on the official site before sending."),
    ]
    ss.append(["Metric", "Value"])
    for c in ss[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill
    for k, v in top:
        ss.append([k, v])
        ss.cell(ss.max_row, 1).font = bold

    def split_counter(field):
        c = Counter()
        for r in kept:
            vals = [v.strip() for v in re.split(r"[;,/]", r[field]) if v.strip()] or [""]
            c.update(vals)
        return c

    section("Batch Breakdown", Counter(r["_batch"] for r in kept))
    section("City Breakdown", Counter(r["city"] for r in kept))
    section("Region Breakdown", Counter(r["state"] for r in kept))
    section("Industry Breakdown", Counter(r["industry"] for r in kept))
    section("Prospect Type Breakdown", Counter(r["prospect_type"] for r in kept))
    section("Dashboard Type Breakdown", Counter(r["dashboard_type"] for r in kept))
    section("Current Systems Breakdown", split_counter("current_systems"))
    section("Pain Point Breakdown", Counter(r["pain_point"] for r in kept))
    section("Automation Signal Breakdown", Counter(r["automation_signal"] for r in kept))
    section("Buying Intent Breakdown", intent)
    section("Research Confidence Breakdown", Counter(r["research_confidence"] for r in kept))
    section("Lead Status Breakdown", status)
    section("Evidence Type Breakdown", Counter(r["evidence_type"] for r in kept))
    ss.column_dimensions["A"].width = 70
    ss.column_dimensions["B"].width = 60
    for row in ss.iter_rows():
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)

    wb.save(OUT_FILE)
    for k, v in top:
        print(f"{k}: {v}")
    print("Batches:", dict(batches))
    print("Hard QC issues:", sum(1 for r in kept if r["_hard"]))
    for r in kept:
        if r["_hard"]:
            print("  QC", r["company"], r["_hard"])
    dup_subj = [s for s, n in Counter(r["subject_line"].lower() for r in kept).items() if n > 1]
    print("Repeated subject lines:", len(dup_subj))


if __name__ == "__main__":
    main()

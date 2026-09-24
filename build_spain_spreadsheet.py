"""Merge Spain researcher JSON, dedupe, run quality checks and build the campaign workbook."""
import glob
import json
import re
import sys
import unicodedata
from collections import Counter
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

RESEARCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "research/spain"
OUT_FILE = "Spain_Invoice_AI_Automation_Prospects_1000.xlsx"
SENDER = "Oseni Ibrahim"
SENDER_EMAIL = "olalekanafolabii7072@gmail.com"
OPT_OUT = "responda \"baja\""

COLUMNS = [
    "Prospect Name", "Company", "First Name", "Job Title", "Email", "Country", "State", "City",
    "Company Type", "Industry", "Invoice Product or Service", "Accounting Platform", "ERP",
    "Payment Platform", "Company Size", "Website", "LinkedIn", "Buying Intent",
    "Automation Opportunity", "Personalization Detail", "Personalization Reason",
    "Personalized Opening", "Subject Line", "Email Body", "Source URL", "Evidence",
    "Evidence Type", "Research Confidence", "Lead Status", "Send Status", "Date Sent", "Notes",
]

REGIONS = {
    "Comunidad de Madrid", "Cataluña", "Comunitat Valenciana", "Andalucía", "País Vasco",
    "Navarra", "Galicia", "Aragón", "Castilla y León", "Castilla-La Mancha", "Región de Murcia",
    "Principado de Asturias", "Cantabria", "Canarias", "Illes Balears", "Extremadura",
    "La Rioja", "Ceuta", "Melilla",
}
REGION_ALIASES = {
    "madrid": "Comunidad de Madrid", "catalonia": "Cataluña", "catalunya": "Cataluña",
    "cataluna": "Cataluña", "valencia": "Comunitat Valenciana",
    "comunidad valenciana": "Comunitat Valenciana", "andalucia": "Andalucía",
    "andalusia": "Andalucía", "pais vasco": "País Vasco", "basque country": "País Vasco",
    "euskadi": "País Vasco", "comunidad foral de navarra": "Navarra", "aragon": "Aragón",
    "murcia": "Región de Murcia", "asturias": "Principado de Asturias",
    "baleares": "Illes Balears", "islas baleares": "Illes Balears",
    "balearic islands": "Illes Balears", "castilla y leon": "Castilla y León",
    "castilla la mancha": "Castilla-La Mancha", "canary islands": "Canarias",
}
BANNED = [
    "sin fisuras", "revolucion", "de vanguardia", "desbloque", "potenciar al máximo",
    "transformar su negocio", "transformar tu negocio", "seamless", "tailored", "stunning",
    "revolutioni", "game changer", "cutting edge", "cutting-edge", "unlock", "supercharge",
    "transform your business", "espero que esté bien", "espero que estés bien",
]
PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
EMAIL_RE = re.compile(r"^[a-z0-9._%+'-]+@[a-z0-9.-]+\.[a-z]{2,}$")
FREE_DOMAINS = {
    "gmail.com", "outlook.com", "outlook.es", "hotmail.com", "hotmail.es", "yahoo.com",
    "yahoo.es", "icloud.com", "live.com", "msn.com", "protonmail.com", "proton.me",
    "telefonica.net", "movistar.es", "gmx.es", "me.com",
}
# Records whose researcher flagged an open question: kept but held for review.
FORCE_REVIEW = {
    "crisóstomo asesores": "Website/email domains differ (.online vs .com).",
    "anfix software": "HQ city conflicts in results (Madrid vs Valladolid phone).",
    "advantys": "Named contact comes from a 2022 directory.",
    "solmicro": "City inferred from phone prefix only.",
    "novicap": "Location not confirmed in search results.",
}
ROLE_MAILBOXES = {
    "info", "hola", "hello", "contacto", "contact", "comercial", "ventas", "sales", "admin",
    "administracion", "administracio", "asesoria", "gestoria", "oficina", "despacho", "soporte",
    "support", "marketing", "clientes", "correo", "consultas", "empresa", "general", "atencion",
    "atencionalcliente", "recepcion", "informacion", "partners", "business", "hi", "sac",
    "direccio", "direccion", "assessoria", "general", "madrid", "barcelona", "castellon", "valencia", "ceg",
}


def is_personal_mailbox(email):
    """Role and company-named mailboxes are generic; anything else is treated as a person's."""
    local, dom = email.split("@")
    label = dom.split(".")[0].replace("-", "")
    local_n = local.replace("-", "").replace(".", "")
    return local not in ROLE_MAILBOXES and local_n not in label and label not in local_n

CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}
INTENT_RANK = {"High": 3, "Medium": 2, "Low": 1}


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s):
    return re.sub(r"[^a-z0-9]", "", strip_accents((s or "").lower()))


def norm_company(s):
    s = strip_accents((s or "").lower())
    s = re.sub(r"\b(s\.?\s?l\.?\s?u?\.?|s\.?\s?a\.?\s?u?\.?|slp|sl|sa|slu|sau|sociedad limitada|"
               r"asesores|asesoria|consultores|group|grupo|spain|espana|the)\b", " ", s)
    return norm(s)


def host(url):
    h = urlparse(url if "://" in (url or "") else "https://" + (url or "")).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def base_domain(h):
    parts = h.split(".")
    if len(parts) >= 3 and parts[-2] in {"com", "co", "org"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def clean_region(s):
    s = (s or "").strip()
    if s in REGIONS:
        return s
    return REGION_ALIASES.get(strip_accents(s.lower()), s)


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


def invalid_reason(r):
    if not r["company"]:
        return "empty company"
    if not r["website"]:
        return "empty website"
    email = r["email"]
    if email:
        if not EMAIL_RE.match(email):
            return "invalid email format"
        if email.split("@")[1] in FREE_DOMAINS:
            return "personal/free email domain"
    if not (r.get("source_url") or "").startswith("http"):
        return "missing source URL"
    return None


def qc_issues(r):
    issues = []
    body = r.get("email_body") or ""
    lb = body.lower()
    subj = (r.get("subject_line") or "").strip()
    if not subj:
        issues.append("missing subject")
    if not body:
        issues.append("missing email body")
    for text in (subj, body, r.get("personalized_opening") or ""):
        if PLACEHOLDER_RE.search(text):
            issues.append("unresolved placeholder")
            break
    for b in BANNED:
        if b in lb or b in subj.lower():
            issues.append(f"banned phrase '{b}'")
    if SENDER.lower() not in lb or SENDER_EMAIL not in lb:
        issues.append("sender signature missing")
    if r.get("language", "Spanish") == "Spanish" and OPT_OUT not in lb:
        issues.append("opt-out line missing")
    if r.get("language") == "English" and "unsubscribe" not in lb and "no longer" not in lb \
            and "not to receive" not in lb and OPT_OUT not in lb:
        issues.append("opt-out line missing")
    words = len(body.split())
    if words > 160:
        issues.append(f"body long ({words} words)")
    fn = r.get("first_name") or ""
    first_line = body.split("\n", 1)[0].lower()
    if not fn and first_line.startswith("hola ") and first_line.strip() not in {"hola,"}:
        if not first_line.startswith("hola equipo"):
            issues.append("greeting uses a name but first_name is empty")
    if fn and fn.lower() not in first_line and not first_line.startswith(("hola,", "buenos")):
        issues.append("greeting name mismatch")
    if not r.get("personalization_detail"):
        issues.append("missing personalization detail")
    if r["state"] not in REGIONS:
        issues.append(f"region '{r['state']}' not a Comunidad Autónoma")
    return issues


def main():
    records, rejected, searches = load_records()
    researched = len(records) + len(rejected)

    for r in records:
        for k in list(r.keys()):
            if isinstance(r[k], str):
                r[k] = r[k].strip()
        r["email"] = (r.get("email") or "").lower().rstrip(".")
        r["state"] = clean_region(r.get("state"))
        r["research_confidence"] = (r.get("research_confidence") or "Medium").title()
        if r["research_confidence"] not in CONF_RANK:
            r["research_confidence"] = "Medium"
        r["buying_intent"] = (r.get("buying_intent") or "Medium").split()[0].title()
        if r["buying_intent"] not in INTENT_RANK:
            r["buying_intent"] = "Medium"
        if not r.get("website", "").startswith("http") and r.get("website"):
            r["website"] = "https://" + r["website"]

    invalid = []
    valid = []
    for r in records:
        why = invalid_reason(r)
        if why:
            invalid.append({"company": r.get("company"), "reason": why})
        else:
            valid.append(r)

    # Strongest record first so duplicates drop the weaker copy.
    valid.sort(key=lambda r: (-CONF_RANK[r["research_confidence"]], 0 if r["email"] else 1,
                              -INTENT_RANK[r["buying_intent"]]))
    kept, dupes = [], []
    seen = {"company": set(), "site": set(), "email_dom": set(), "email": set()}
    for r in valid:
        keys = {
            "company": norm_company(r["company"]) or None,
            "site": base_domain(host(r["website"])) or None,
            "email_dom": base_domain(r["email"].split("@")[1]) if r["email"] else None,
            "email": r["email"] or None,
        }
        # Website and email domains share a namespace.
        doms = {keys["site"], keys["email_dom"]} - {None}
        if (keys["company"] in seen["company"] or keys["email"] in seen["email"]
                or doms & (seen["site"] | seen["email_dom"])):
            dupes.append(r)
            continue
        for k, v in keys.items():
            if v:
                seen[k].add(v)
        kept.append(r)

    for r in kept:
        issues = qc_issues(r)
        for key, why in FORCE_REVIEW.items():
            if r["company"].lower().startswith(key):
                issues.append("Review: " + why)
        if r["email"] and is_personal_mailbox(r["email"]):
            issues.append("Review: personal work email - check consent basis")
        r["_issues"] = issues
        ready = (not issues and r["email"] and r.get("email_verification") == "two_searches"
                 and r["research_confidence"] != "Low")
        r["_status"] = "ready" if ready else "review"

    kept.sort(key=lambda r: (r["_status"] != "ready", -CONF_RANK[r["research_confidence"]],
                             -INTENT_RANK[r["buying_intent"]], r["_seg"]))

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice Automation Prospects"
    ws.append(COLUMNS)
    for r in kept:
        notes = [r.get("notes", "")]
        if not r["email"]:
            notes.append("No verified email.")
        ver = r.get("email_verification", "none")
        if r["email"]:
            notes.append({"two_searches": "Email confirmed in two separate web searches.",
                          "one_search": "Email found in one web search only - confirm before sending."}
                         .get(ver, "Email verification not recorded."))
        notes.append("Verified from search results (direct site access unavailable during research).")
        if r.get("language") == "English":
            notes.append("English outreach.")
        if r["_issues"]:
            notes.append("QC: " + "; ".join(r["_issues"]))
        ws.append([
            r.get("prospect_name") or r["company"], r["company"], r.get("first_name", ""),
            r.get("job_title", ""), r["email"], "Spain", r["state"], r.get("city", ""),
            r.get("company_type", ""), r.get("industry", ""), r.get("invoice_product_or_service", ""),
            r.get("accounting_platform", ""), r.get("erp", ""), r.get("payment_platform", ""),
            r.get("company_size", ""), r["website"], r.get("linkedin", ""), r["buying_intent"],
            r.get("automation_opportunity", ""), r.get("personalization_detail", ""),
            r.get("personalization_reason", ""), r.get("personalized_opening", ""),
            r.get("subject_line", ""), r.get("email_body", ""), r["source_url"],
            r.get("evidence", ""), r.get("evidence_type", ""), r["research_confidence"],
            r["_status"], "Not Sent", None, " ".join(n for n in notes if n).strip(),
        ])

    widths = {1: 26, 2: 28, 5: 32, 9: 30, 11: 40, 16: 30, 19: 45, 20: 45, 21: 40, 22: 50,
              23: 36, 24: 80, 25: 45, 26: 55, 32: 50}
    for i in range(1, len(COLUMNS) + 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(i, 16)
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
    for col, opts in (("R", "High,Medium,Low"), ("AB", "High,Medium,Low"),
                      ("AC", "ready,review"), ("AD", "Not Sent,Sent,Bounced,Replied,Unsubscribed")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{last}")
    for cell in ws["AE"][1:]:
        cell.number_format = "yyyy-mm-dd"

    conf = Counter(r["research_confidence"] for r in kept)
    intent = Counter(r["buying_intent"] for r in kept)
    status = Counter(r["_status"] for r in kept)
    with_email = sum(1 for r in kept if r["email"])
    ss = wb.create_sheet("Research Summary")

    def section(title, rows):
        ss.append([title, ""])
        ss.cell(ss.max_row, 1).font = Font(bold=True, color="FFFFFF")
        ss.cell(ss.max_row, 1).fill = header_fill
        ss.cell(ss.max_row, 2).fill = header_fill
        for row in rows:
            ss.append(list(row))
        ss.append([])

    section("Overview", [
        ("Total researched (accepted + rejected by researchers)", researched),
        ("Total prospects (unique, in sheet)", len(kept)),
        ("Prospects with verified emails", with_email),
        ("Prospects without verified emails", len(kept) - with_email),
        ("Emails confirmed in two separate searches",
         sum(1 for r in kept if r["email"] and r.get("email_verification") == "two_searches")),
        ("Lead Status = ready", status["ready"]),
        ("Lead Status = review", status["review"]),
        ("Duplicate count removed", len(dupes)),
        ("Invalid prospects removed (rejected in research + failed validation)",
         len(rejected) + len(invalid)),
        ("  - rejected during research", len(rejected)),
        ("  - failed validation at merge", len(invalid)),
        ("Searches logged by researchers", searches),
        ("Sender", f"{SENDER} <{SENDER_EMAIL}>"),
    ])
    section("Prospects by country", [("Spain", len(kept))])
    section("Prospects by region (Comunidad Autónoma)",
            Counter(r["state"] or "Unknown" for r in kept).most_common())
    section("Prospects by city (top 15)",
            Counter(r.get("city") or "Unknown" for r in kept).most_common(15))
    section("Prospects by company type",
            Counter(r.get("company_type") or "Unknown" for r in kept).most_common())
    section("Prospects by buying intent", [(k, intent[k]) for k in ("High", "Medium", "Low")])
    section("Prospects by research confidence", [(k, conf[k]) for k in ("High", "Medium", "Low")])
    section("Outreach language split",
            Counter(r.get("language") or "Spanish" for r in kept).most_common())
    section("Compliance notes", [
        ("LSSI-CE art. 21", "Spain restricts unsolicited commercial email; the AEPD applies this to "
         "emails sent to companies too. Review your legal basis before sending."),
        ("Opt-out", "Every email includes a reply-'baja' opt-out. Honour opt-outs immediately and "
         "set Send Status to 'Unsubscribed'."),
        ("Sender identity", "Every email identifies the sender by name and email address."),
        ("Source records", "Source URL shows where each email/company was found publicly."),
        ("Personal work emails", "Rows flagged 'Personal work email' need an extra consent check."),
        ("Verification method", "Direct website access was blocked in the research environment; "
         "companies and emails were verified from web search results. Spot-check before sending."),
        ("Deliverability", "Cold email from a free Gmail address has poor deliverability; "
         "send small daily volumes or use a domain address."),
    ])
    ss.column_dimensions["A"].width = 62
    ss.column_dimensions["B"].width = 90
    for row in ss.iter_rows():
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)

    wb.save(OUT_FILE)
    print(f"researched={researched} unique={len(kept)} with_email={with_email} "
          f"dupes={len(dupes)} invalid={len(invalid)} rejected={len(rejected)}")
    print("confidence", dict(conf), "intent", dict(intent), "status", dict(status))
    print("types", dict(Counter(r.get("company_type") for r in kept)))
    for r in dupes:
        print("DUP", r["company"], r["email"])
    for x in invalid:
        print("INVALID", x)
    for r in kept:
        if r["_issues"]:
            print("QC", r["company"], r["_issues"])
    subj = Counter((r.get("subject_line") or "").lower() for r in kept)
    print("duplicate subjects:", [s for s, n in subj.items() if n > 1])


if __name__ == "__main__":
    main()

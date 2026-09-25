# Researcher spec — Slovenia dashboard-development prospects

ENVIRONMENT: Only the WebSearch tool works. WebFetch and curl are blocked by the network policy — do not try them.
Use many targeted WebSearch queries (English + Slovenian: "d.o.o.", "zaposlimo", "razvijalec", "poročanje",
"analitika", "spletna trgovina", "kontakt", "info@"), e.g. `"<company>" d.o.o. kontakt email`,
`site:<domain> kontakt`, `<company> zaposlitev razvijalec`, `<company> LinkedIn`.

RULES (strict):
- Slovenia ONLY: company HQ or verified operating entity in Slovenia (d.o.o., d.d., s.p. or Slovenian branch).
- Real companies only. Every fact must come from a search result you actually saw. NEVER invent anything.
- Email: include ONLY if the exact address appeared in a search result AND its domain matches the company's official
  domain (or is clearly the company's published address). NEVER guess or build an address from a name or pattern.
  If unsure, leave "" . Put "Email seen in search result for <url>; re-check on site before sending" in notes.
- First Name / Job Title: only if a search result names that person in that role at this company. Otherwise "".
  If there's no person, Prospect Name = company name.
- current_systems: only systems explicitly named in evidence (e.g. a job ad asking for Power BI, a site stating
  "Shopify"). Otherwise "Not publicly verified".
- buying_intent HIGH only with direct evidence (an active job ad for developer/BI/data/integration, a public
  tender or announced internal-system project). MEDIUM = clear operational/reporting complexity evidence
  (multi-location, multi-channel ecommerce, large product catalogue, fleet/logistics network, many branches).
  LOW = plausible fit, thin evidence.
- research_confidence: HIGH only if multiple consistent results incl. official domain; MEDIUM typical; LOW if thin.
- lead_status: Qualified (good evidence + clear opportunity), Review (weak evidence or unclear fit), Disqualified.
- Skip huge multinationals' global HQs; Slovenian subsidiaries OK if Slovenian entity is verifiable. Prefer SMEs and
  mid-market companies that would realistically hire an outside dashboard developer.
- No duplicates within your file. Avoid companies listed in EXCLUDE below (other researchers cover them).

EMAIL BODY template (short, English, no hype, keep placeholders exactly):
Hi <First Name or "there">,

I noticed <specific verified fact>.

If your team is currently handling <relevant workflow>, I can build a custom dashboard that brings <relevant data> into one place and makes <reporting/monitoring> easier.

I build custom dashboards and internal business tools using APIs, databases and automation workflows.

Would this be useful for your team?

Best regards,
[Sender Name]
[Sender Title]

Subject lines: short, e.g. "Dashboard idea for <Company>", "Question about your order reporting". No spam words.

OUTPUT: write a JSON array to the file path you are given, using Bash heredoc or Write. Each object has keys:
prospect_name, company, first_name, job_title, email, state (Slovenian statistical region e.g. "Osrednjeslovenska",
"Podravska", "Gorenjska", "Savinjska", "Obalno-kraška", "Jugovzhodna Slovenija", "Goriška", "Pomurska", "Koroška",
"Primorsko-notranjska", "Zasavska", "Posavska"), city, website (official, https://...), industry, prospect_type
(e.g. "Ecommerce Retailer", "SaaS Company", "Logistics Provider", "Manufacturer", "Agency"...), dashboard_type,
current_systems, data_sources, current_workflow, pain_point, reporting_problem, monitoring_problem,
automation_signal, commercial_signal, dashboard_opportunity, buying_intent, personalization_detail,
personalization_reason, personalized_opening, subject_line, email_body, source_url (the primary URL from search
results), evidence (short factual), evidence_type (one of: Official Website, LinkedIn, Job Posting, GitHub,
Product Page, Company Blog, Public Post, YouTube, Forum, Business Directory, Other), research_confidence,
lead_status, notes (include campaign segments like "Segments: Ecommerce Dashboard; Sales Dashboard" and
"Verified via search results only; page not fetched").
Write the file incrementally (every ~10 leads) so work isn't lost. Quality > quantity; target 50.
Finish with a one-paragraph summary: count, HIGH/MEDIUM/LOW, emails found.

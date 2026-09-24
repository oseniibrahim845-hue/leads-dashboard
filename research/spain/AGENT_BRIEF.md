# Researcher brief: Spain invoice AI automation prospects

Goal: find REAL Spanish companies for which invoicing, billing, accounts receivable, accounting, payments or finance administration is clearly relevant. Sender offers OpenClaw-based AI agents that automate invoice tracking, payment follow-ups, reporting, and finance admin around existing systems.

## Tools / constraints
- Only WebSearch works. WebFetch and curl are BLOCKED (don't try). Verify via search results.
- Use varied queries, e.g. `"@domain.es" contacto`, `site:domain.es email`, `"Company" aviso legal email`, `"Company" CIF`, `"Company" socio director`, Spanish keywords.
- NEVER invent companies, people, or emails. NEVER guess an email from a name pattern. Emails must appear verbatim in a search result for that company.
- Email must be on the company's own domain (no gmail/hotmail/yahoo/outlook/icloud/telefonica.net etc.).
- Prefer generic addresses (info@, contacto@, hola@, comercial@, administracion@...). A named employee email only if it appears publicly; flag it in notes "Personal work email - check consent basis".
- Person names: only if a search result clearly states the person and role at this company (e.g. LinkedIn, team page, press). Otherwise leave prospect-person fields blank and use the company name as prospect_name.
- Company must be based in Spain (or have a verified Spanish office, record that office).
- Skip: restaurants, hotels, retail, autónomos without a company, public bodies, big multinationals with no Spanish contact email.

## Verification standard
- email_verification: "two_searches" if the email was confirmed in 2 separate search queries/results; "one_search" otherwise. Aim for two.
- research_confidence: High = company + website + email confirmed (two_searches) + specific evidence; Medium = one_search email or limited contact info; Low = weak.
- If no email can be found but company is highly relevant, you MAY include it with email "" (max 3 per segment).

## Output
Write a JSON file to the path given in your task with this shape:
{"segment": "...", "searches_run": N, "accepted": [ ...records... ], "rejected": [{"company": "...", "reason": "..."}]}

Each record (all strings):
- prospect_name: verified person full name, else company name
- company: legal/trading name
- first_name: verified first name or ""
- job_title: verified title or ""
- email: lowercase or ""
- state: Comunidad Autónoma (Comunidad de Madrid, Cataluña, Comunitat Valenciana, Andalucía, País Vasco, Navarra, Galicia, Aragón, Castilla y León, Castilla-La Mancha, Región de Murcia, Principado de Asturias, Cantabria, Canarias, Illes Balears, Extremadura, La Rioja)
- city
- company_type: one of: "Accounting / bookkeeping firm (asesoría)", "Invoicing / e-invoicing software", "Accounting / tax software", "ERP vendor / implementation partner", "Accounts receivable / collections", "Payments / fintech / factoring", "Billing / subscription management", "Business management software", "Financial administration / CFO services"
- industry (short)
- invoice_product_or_service: what they do that touches invoicing/finance
- accounting_platform: only if evidence (e.g. "a3, Sage"), else ""
- erp: only if evidence, else ""
- payment_platform: only if evidence, else ""
- company_size: e.g. "11-50" if evidence (LinkedIn), else ""
- website: https://... (root domain)
- linkedin: company LinkedIn URL if found in results, else ""
- buying_intent: High/Medium/Low (be honest; not all High)
- automation_opportunity: English, start with "Potential opportunity: automate ..."
- personalization_detail: English, one specific evidence-based fact
- personalization_reason: English, why that fact matters for this pitch
- personalized_opening: Spanish, 1 sentence, specific (not "Espero que esté bien")
- subject_line: Spanish, specific, <= 9 words, unique per record
- email_body: Spanish (Spain), < 120 words, format below
- source_url: URL of the result showing the company/email
- evidence: English, what the source shows
- evidence_type: Website | Product page | Pricing page | LinkedIn | Company page | Documentation | Press release | Job posting | Partner directory | Aviso legal page | Business directory
- email_verification: two_searches | one_search | none
- research_confidence: High/Medium/Low
- language: "Spanish" (or "English" if the company is clearly English-only)
- notes: English, anything relevant

## Email body format (Spanish, usted for asesorías/traditional firms; tú OK for startups)
```
Hola Javier,            <- only if first_name verified; else "Hola," or "Buenos días,"

<personalized opening sentence>

Desarrollo agentes de IA con OpenClaw que se encargan de parte del seguimiento de facturas, los recordatorios de pago y los informes financieros, trabajando con los sistemas que ya utilizan.

<one sentence: specific workflow opportunity for this company, using real company name>

<one simple question>

Un saludo,
Oseni Ibrahim
AI Automation Specialist
olalekanafolabii7072@gmail.com

Si prefiere no recibir más correos, responda "baja" y no volveré a escribirle.
```
Vary the middle sentences naturally between records (don't copy-paste identical wording every time). Banned words: sin fisuras, revolucionar, de vanguardia, desbloquear, potenciar al máximo, transformar su negocio, seamless, cutting edge, game changer, unlock, supercharge. No placeholders like [Empresa] or [Nombre].

Use \n for newlines in JSON strings. Write valid JSON (use python json.dump via Bash to be safe).

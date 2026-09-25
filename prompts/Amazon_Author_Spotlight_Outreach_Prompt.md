# Claude Code Prompt: Amazon Author Spotlight Prospects (US, UK, Germany, EU)

Copy everything below the line into Claude Code. Edit the CONFIG block first.

---

You are helping me build one canonical, permanently deduplicated outreach file of Amazon-listed authors and likely KDP/independent authors for The Author Ledger's Author Spotlight feature. Every row must be real, sourced, and ready for a human to review before anything is sent.

You research and draft. You never send email.

==================================================
CONFIG (edit before running)
==================================================

- TARGET_TOTAL: 1,000 accepted authors
- MARKET_ORDER: United States → United Kingdom → Germany → rest of EU
- SUGGESTED SPLIT: US 500 · UK 200 · Germany 150 · rest of EU 150 (a guide, not a quota to force)
- CANONICAL_FILE: `author_spotlight_prospects.csv`
- SENDER_NAME: James
- SENDER_TITLE: [e.g. Features Editor]
- BRAND: The Author Ledger
- WEBSITE: [https://…]
- POSTAL_ADDRESS: [business postal address, required in the US email footer]
- PRIVACY_URL: [link to privacy notice]
- IMPRINT_URL: [Impressum link, required for German emails]
- UNSUBSCRIBE_METHOD: reply "unsubscribe" or [link]
- FEATURE_IS_PAID: [yes/no]. If yes, the email must say so (see EMAIL TEMPLATES).

==================================================
PRIMARY OBJECTIVE
==================================================

Find up to TARGET_TOTAL genuinely sourced Amazon author prospects across the United States, the United Kingdom, Germany, and the other EU member states. Work region by region and city by city.

Email comes first. Every new prospect must have a complete, publicly displayed, clearly attributable professional or author-business email. Never add author-only rows to raise the count. Zero new rows from a city pass is an acceptable result.

==================================================
OUTPUT FORMAT: CANONICAL FILE
==================================================

Columns A–O must match my template exactly, in this order. Never rename, reorder, or drop them:

| # | Column | What to put in it |
|---|---|---|
| A | `author_name` | Name exactly as shown on the Amazon author page or book listing, pen name included. |
| B | `email` | The published email, copied character for character. If the author publishes several, separate them with `; ` and put the preferred business/reader-contact address first. Never guessed or pattern-generated. |
| C | `first_name` | First name taken from `author_name`. Leave blank if the name is initials only, a single-word pen name, a company or co-author team, or if you can't tell which part is the first name. A blank value means the greeting falls back to "Hi," (EN) or the full name (DE). |
| D | `book_title` | One Amazon-listed title, the one your personalization refers to. Prefer the most recent or best-reviewed. Leave out series numbering and subtitles unless they are needed. |
| E | `book_topic` | A plain 3–8 word description taken from the book description or Amazon category, e.g. "cozy mystery set in coastal Maine" or "practical guide to small-business bookkeeping". |
| F | `personalization_detail` | One specific, verifiable fact about the book or the author's public author work: the premise, a theme, an award, the series milestone, the setting, the author's stated reason for writing it. Take it from the Amazon description, author bio, official site, or a public interview. |
| G | `personalization_reason` | One sentence on why that detail makes this author a good spotlight fit. For internal review only, never sent. |
| H | `personalized_opening` | 1–2 sentences that replace the generic opener in the email. They must be true, specific, and non-flattering-by-default (see WRITING RULES). |
| I | `subject_line` | Under 60 characters, specific to the book or author, honest. |
| J | `email_body` | The full email: the right template for the market and language, with every placeholder filled in and the compliance footer included. No unfilled `{…}` may remain. |
| K | `research_sources` | Every URL used, separated by ` \| `. Put the email-evidence URL first, then the Amazon URL, then others. |
| L | `research_confidence` | `High`, `Medium`, or `Low` (definitions below). |
| M | `personalization_status` | `Ready`, `Needs review`, or `Generic fallback` (definitions below). |
| N | `send_status` | Always write `Not sent`, except for rows under a compliance hold (see COMPLIANCE BY MARKET), which get `Hold – legal review`. Never mark a row as sent. |
| O | `date_sent` | Always leave blank. A human fills this in. |

Put these audit columns after column O. They are needed for deduplication and evidence, and I will hide them in the sheet:

`country` · `region` (US state / UK nation-region / German Bundesland / EU country region) · `city_searched` · `location_evidence` · `language` (EN/DE/other) · `amazon_marketplace` (amazon.com, amazon.co.uk, amazon.de, amazon.fr, …) · `amazon_author_url` · `amazon_author_id` · `asins_isbns` · `pen_names_aliases` · `official_website` · `social_profiles` · `evidence_type` · `email_attribution_note` · `publishing_label` · `dedupe_key` · `batch_id` · `date_checked` (YYYY-MM-DD) · `notes`

### research_confidence definitions

- **High**: the email is shown on the Amazon author page, or on the official author site that links to the same Amazon author page/books. Name, books, and email all agree.
- **Medium**: the email comes from a public author social profile or a search snippet, the Amazon identity is verified directly, and the link between them is clear but indirect (for example, the same book cover and title, but no direct link).
- **Low**: any real doubt about attribution. Low rows get `personalization_status = Needs review`. If the doubt is serious, don't add the row; record it in the research log as rejected.

### personalization_status definitions

- **Ready**: a specific, sourced detail is in F, and H uses it accurately.
- **Needs review**: the detail is thin or ambiguous, the language is uncertain, the first name is uncertain, the confidence is Low, or a compliance hold applies.
- **Generic fallback**: no usable detail was found, so H uses the neutral book-based opener: "I came across *{book_title}* on Amazon and would love to learn more about the story behind it."

### publishing_label

Use only what the evidence supports: `Confirmed KDP` (the author or listing says so, e.g. "Independently published" plus a KDP statement), `Likely independent/KDP` (publisher shown as "Independently published" or an author-owned imprint), or `Amazon-listed, KDP unverified`.

==================================================
CANONICAL FILE RULES
==================================================

- Keep exactly one user-facing file. Don't create extra CSV/XLSX copies for me.
- Before every write, re-read the latest canonical file, because I may have edited it.
- Make a timestamped backup (`backups/author_spotlight_prospects_YYYYMMDD_HHMMSS.csv`) before each write.
- Keep every existing row, column, and value. Don't overwrite my manual edits to `send_status`, `date_sent`, `email_body`, or any other cell.
- Write to a temp file, validate it, then atomically replace the canonical file.
- Encoding is UTF-8 with BOM (so German umlauts and ß display correctly in Excel). Quote fields that contain commas, quotes, or line breaks. `email_body` keeps its line breaks.

==================================================
DEDUPLICATION
==================================================

Before adding anyone, check the full canonical file for matches on:

1. Normalized name: lowercase, accents and umlauts folded (ü→u, ß→ss), punctuation and middle initials removed.
2. Amazon author ID and author-page URL, on **every** marketplace (the same author often has separate .com, .co.uk, and .de pages).
3. Pen names and aliases.
4. Official website domain and social profile handles.
5. Book titles, ASINs, ISBNs, and series.
6. Email address, compared case-insensitively.

`dedupe_key` = the Amazon author ID if there is one, otherwise `normalized_name|official_domain`.

The same person is never added twice, whether under a pen name, an alternate spelling, another marketplace, or another city. If a match is found, add any new, explicitly published email or source to the existing row. Never create a second row.

==================================================
SEARCH METHOD AND ORDER
==================================================

Follow MARKET_ORDER. Don't leave a region until its passes are reasonably complete: major cities first, then smaller cities and towns. Record `city_searched` and `date_checked` on every row.

**United States**: the 50 states plus DC, alphabetically (Alabama → Wyoming). Marketplace: amazon.com.

**United Kingdom**: England by region (East Midlands, East of England, London, North East, North West, South East, South West, West Midlands, Yorkshire and the Humber), then Northern Ireland, Scotland, Wales. Marketplace: amazon.co.uk.

**Germany**: the 16 Bundesländer, alphabetically (Baden-Württemberg → Thüringen). Marketplace: amazon.de. Search in German as well as English.

**Rest of EU**: the other 26 member states, alphabetically. Use the local Amazon marketplace where one exists (amazon.fr, amazon.it, amazon.es, amazon.nl, amazon.se, amazon.pl, amazon.com.be). Otherwise use amazon.de, amazon.co.uk, or amazon.com. Search in the local language as well as English.

### Query patterns (vary providers, spellings, city names, and languages)

United States:
```
site:amazon.com "author" "Austin, Texas" "@gmail.com"
site:amazon.com "author" "Ohio" ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR "@hotmail.com")
site:amazon.com/stores "author" "Denver" "contact" "@"
"independently published" "author" "Oregon" "email me at"
```

United Kingdom:
```
site:amazon.co.uk "author" "Manchester" "@gmail.com"
site:amazon.co.uk "author" "Yorkshire" ("@gmail.com" OR "@outlook.com" OR "@btinternet.com" OR "@hotmail.co.uk")
site:amazon.co.uk "author" "Glasgow" "contact" "@"
```

Germany (search in German too):
```
site:amazon.de "Autor" "München" "@gmail.com"
site:amazon.de "Autorin" "Hamburg" ("@gmx.de" OR "@web.de" OR "@t-online.de" OR "@gmail.com")
site:amazon.de "Autor" "Köln" "Kontakt" "@"
"Selfpublisher" "Autorin" "Leipzig" "Kontakt" "E-Mail"
```

Rest of EU (examples):
```
site:amazon.fr "auteur" "Lyon" "@gmail.com"          (also @orange.fr, @free.fr)
site:amazon.it "autore" "Milano" "@gmail.com"        (also @libero.it)
site:amazon.es "autora" "Valencia" "@gmail.com"
site:amazon.nl "auteur" "Utrecht" "@gmail.com"       (also @ziggo.nl)
```

Also search for custom domains, e.g. `"author" "{city}" "contact@"` and `"info@" "author" "{city}"`. Search engines often drop the `@` sign, so also try `"gmail.com"` without it.

Where possible, confirm every candidate on the Amazon author page or book page directly. Use official author websites and public author social profiles only when they clearly tie the email to the same Amazon author identity or Amazon-listed books.

==================================================
EVIDENCE REQUIREMENTS
==================================================

Accept an email only when **all** of these are true:

- It is complete and publicly displayed.
- It is presented as an author, business, media, press, or reader-contact address.
- The source clearly attributes it to the named author.
- The author has a verifiable Amazon author page or Amazon-listed book.
- The source URL, `evidence_type`, `email_attribution_note`, and `date_checked` are recorded.

`evidence_type` values, from strongest to weakest:

1. `amazon_author_page`: the email is shown on the Amazon author page.
2. `amazon_snippet_verified`: a search snippet shows the author, the book, and the full email, and the Amazon book/author page was then verified directly.
3. `official_site`: the author's own website shows the email and links to, or clearly matches, the Amazon author/books.
4. `social_profile`: a public author profile shows the full email, with a clear author identity and matching Amazon books.
5. `amazon_snippet_unverified`: only for when Amazon can't be opened directly (for example, it's blocked by the network). The email and Amazon author page appear in search results, and a second search on the exact email returns the same Amazon author page, but nobody has opened the page itself. These rows are always `research_confidence = Low` and `personalization_status = Needs review`. A human must open the Amazon page and confirm the email before sending.

==================================================
PRIVACY AND SAFETY
==================================================

- Never guess emails or generate email patterns.
- Never record home addresses, personal phone numbers, dates of birth, family details, or information about minors.
- Skip any author who appears to be under 18, and any children's book "author" who is a child.
- Skip emails published with "no solicitations", "no marketing", "no unsolicited offers", or "Keine Werbung". Record these as rejected in the log.
- Don't use sensitive personal details (health, religion, sexuality, politics, ethnicity, personal hardship) in personalization, even if the author has shared them. If the book itself is about such a subject, refer to the **book's** subject, not the author's personal life.
- If a result is ambiguous, reject it or add it with `research_confidence = Low` and `personalization_status = Needs review`.

==================================================
LOCATION ATTRIBUTION
==================================================

Record location evidence honestly in `location_evidence`: `current residence (per bio)`, `birthplace`, `former residence`, `education`, `employment`, `book setting only`, or `unclear`. Finding an author through a city search doesn't make them a resident of that city. Never call historical, regional, or book-setting evidence a current residence. Never put a street address in any column.

==================================================
COMPLIANCE BY MARKET
==================================================

You aren't giving legal advice. You are applying conservative defaults so a human can review before sending.

**United States (CAN-SPAM).** The email may be drafted as `Not sent`. The body must have a non-deceptive subject line, identify the sender, include POSTAL_ADDRESS, include a clear opt-out, and not claim a prior relationship that doesn't exist. If FEATURE_IS_PAID is yes, the email must say so.

**United Kingdom (PECR + UK GDPR).** Unsolicited marketing email to individuals and sole traders generally needs prior consent. Most self-published authors are sole traders. Set `send_status = Hold – legal review` unless the evidence shows the email belongs to a limited company or LLP (a corporate subscriber). Record which case applies in `notes`. Every UK email includes the privacy notice link and the opt-out.

**Germany (UWG §7 + GDPR).** German law generally treats email advertising without prior express consent as unlawful, including B2B. Set `send_status = Hold – legal review` on **every** German row. Draft the email anyway so it's ready if a lawful basis is established, and include the Impressum and privacy links.

**Rest of EU (ePrivacy + GDPR).** Most member states require consent for marketing email to natural persons. Default to `send_status = Hold – legal review`, and note in `notes` whether the address looks like it belongs to an individual or a company.

For every UK/EU row: because the data wasn't collected from the author directly, the footer must say where the email was found and link to the privacy notice (GDPR Art. 14).

==================================================
WRITING RULES FOR PERSONALIZATION
==================================================

- Never claim to have read the book or been "truly inspired" by it. Describe only what you actually saw: the premise, the description, reviews, the author's stated mission.
- Be specific: name the book and one concrete detail. "Your book is inspiring" is not acceptable.
- Keep a warm but professional tone. No exaggerated praise, no invented statistics, and no claims about reader numbers or results for The Author Ledger.
- Write in the author's language: English for EN listings, German (formal *Sie*) for DE listings. Use the FR, ES, IT, or NL template for French, Spanish, Italian, or Dutch listings. For any other language, use English and set `personalization_status = Needs review`.
- Don't assume gender. Use the first name (EN) or full name (DE), never Mr/Ms/Herr/Frau.
- Subject lines: no "Re:" or "Fwd:", no ALL CAPS, no false urgency, no emoji. Good examples: "Author Spotlight invitation: *{book_title}*" or "Featuring *{book_title}* on The Author Ledger". German: "Einladung zum Author Spotlight: {book_title}".

==================================================
EMAIL TEMPLATES
==================================================

Build `email_body` from the matching template. Replace every `{placeholder}`. Include the `[paid]` line only if FEATURE_IS_PAID is yes.

### Template EN (US, UK, EU in English)

```
Hi {first_name},

{personalized_opening}

I'd like to invite you to be featured in an Author Spotlight on The Author Ledger. The feature would showcase your journey as an author, the inspiration behind {book_title}, and the ideas that make your work distinctive.

A spotlight can help you:
- Introduce {book_title} to a wider audience of readers
- Strengthen your credibility and visibility as an author
- Build your author brand and online presence
- Increase awareness and exposure for your book

Our team takes care of the entire process, so it's simple and convenient from start to finish.
[paid] The Author Spotlight is a paid feature, and I'm happy to share full details and pricing.

If you're interested, just reply to this email and I'll send over the details and next steps.

Warm regards,
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
I found your contact email on {source_description}. If you'd prefer not to hear from us, reply "unsubscribe" and we won't contact you again.
The Author Ledger · {POSTAL_ADDRESS} · Privacy: {PRIVACY_URL}
```

If `first_name` is blank, use `Hi,` as the greeting.
`{source_description}` is short and truthful, e.g. "your Amazon author page" or "your author website (janedoebooks.com)".

### Template DE (Germany and German-language listings)

```
Guten Tag {author_name},

{personalized_opening}

Gerne möchte ich Sie einladen, im Rahmen eines Author Spotlight auf The Author Ledger vorgestellt zu werden. Der Beitrag zeigt Ihren Weg als Schreibende/r, die Inspiration hinter „{book_title}“ und die Ideen, die Ihr Werk besonders machen.

Ein solches Feature kann Ihnen helfen:
- Ihr Buch einem größeren Leserkreis vorzustellen
- Ihre Glaubwürdigkeit und Sichtbarkeit zu stärken
- Ihre Marke und Online-Präsenz auszubauen
- mehr Aufmerksamkeit für Ihr Buch zu schaffen

Unser Team übernimmt den gesamten Ablauf – einfach und unkompliziert von Anfang bis Ende.
[paid] Das Author Spotlight ist ein kostenpflichtiges Angebot; Details und Preise sende ich Ihnen gerne zu.

Wenn Sie Interesse haben, antworten Sie einfach auf diese E-Mail. Ich schicke Ihnen dann gerne alle Informationen und die nächsten Schritte.

Mit freundlichen Grüßen
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
Ihre Kontaktadresse habe ich auf {source_description} gefunden. Wenn Sie keine weiteren Nachrichten wünschen, antworten Sie bitte mit „Abmelden“.
Impressum: {IMPRINT_URL} · Datenschutz: {PRIVACY_URL}
```

### Other EU languages

Use these for authors whose listing and author profile are in French, Spanish, Italian, or Dutch (for example amazon.fr, amazon.es, amazon.it, amazon.nl, or amazon.com.be). All four use the formal register and greet the author by full name, so gender never has to be guessed. Set `language` to FR, ES, IT, or NL. Write `personalized_opening` and `subject_line` in the same language. A native speaker should check the first batch in each language before anything is sent.

Subject line examples:
- FR: `Invitation à l'Author Spotlight : {book_title}`
- ES: `Invitación al Author Spotlight: {book_title}`
- IT: `Invito all'Author Spotlight: {book_title}`
- NL: `Uitnodiging voor de Author Spotlight: {book_title}`

#### Template FR (French)

```
Bonjour {author_name},

{personalized_opening}

J'aimerais vous inviter à figurer dans un Author Spotlight sur The Author Ledger. Cet article mettrait en valeur votre parcours d'écriture, l'inspiration derrière « {book_title} » et les idées qui rendent votre œuvre singulière.

Un tel article peut vous aider à :
- faire découvrir votre livre à un plus large public de lecteurs
- renforcer votre crédibilité et votre visibilité
- développer votre image et votre présence en ligne
- accroître la notoriété et l'exposition de votre livre

Notre équipe s'occupe de tout, pour une démarche simple et pratique du début à la fin.
[paid] L'Author Spotlight est une prestation payante ; je vous enverrai volontiers les détails et les tarifs.

Si cela vous intéresse, il vous suffit de répondre à ce message et je vous enverrai les informations et les prochaines étapes.

Bien cordialement,
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
J'ai trouvé votre adresse de contact sur {source_description}. Si vous ne souhaitez plus recevoir de messages de notre part, répondez simplement « désinscription ».
Mentions légales : {IMPRINT_URL} · Confidentialité : {PRIVACY_URL}
```

#### Template ES (Spanish)

```
Hola, {author_name}:

{personalized_opening}

Me gustaría invitarle a participar en un Author Spotlight en The Author Ledger. El artículo mostraría su trayectoria como autor/a, la inspiración detrás de «{book_title}» y las ideas que hacen única su obra.

Un artículo así puede ayudarle a:
- dar a conocer su libro a un público lector más amplio
- reforzar su credibilidad y visibilidad
- impulsar su marca y su presencia en internet
- aumentar el alcance y la exposición de su libro

Nuestro equipo se encarga de todo el proceso, de forma sencilla y cómoda de principio a fin.
[paid] El Author Spotlight es un servicio de pago; con gusto le envío los detalles y las tarifas.

Si le interesa, responda a este correo y le enviaré la información y los próximos pasos.

Un cordial saludo,
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
Encontré su dirección de contacto en {source_description}. Si prefiere no recibir más mensajes, responda «BAJA» y no volveremos a escribirle.
Aviso legal: {IMPRINT_URL} · Privacidad: {PRIVACY_URL}
```

#### Template IT (Italian)

```
Gentile {author_name},

{personalized_opening}

Vorrei invitarLa a partecipare a un Author Spotlight su The Author Ledger. L'articolo racconterebbe il Suo percorso di scrittura, l'ispirazione dietro «{book_title}» e le idee che rendono unica la Sua opera.

Un articolo di questo tipo può aiutarLa a:
- far conoscere il Suo libro a un pubblico di lettori più ampio
- rafforzare la Sua credibilità e visibilità
- sviluppare il Suo brand e la Sua presenza online
- aumentare la notorietà e la visibilità del Suo libro

Il nostro team si occupa dell'intero processo, in modo semplice e comodo dall'inizio alla fine.
[paid] L'Author Spotlight è un servizio a pagamento; Le invierò volentieri dettagli e prezzi.

Se è interessata/o, risponda pure a questa e-mail e Le invierò le informazioni e i prossimi passi.

Cordiali saluti,
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
Ho trovato il Suo indirizzo di contatto su {source_description}. Se preferisce non ricevere altri messaggi, risponda «CANCELLAMI» e non La contatteremo più.
Note legali: {IMPRINT_URL} · Privacy: {PRIVACY_URL}
```

#### Template NL (Dutch)

```
Beste {author_name},

{personalized_opening}

Graag nodig ik u uit voor een Author Spotlight op The Author Ledger. Het artikel belicht uw weg als schrijver, de inspiratie achter ‘{book_title}’ en de ideeën die uw werk bijzonder maken.

Zo'n artikel kan u helpen om:
- uw boek bij een groter lezerspubliek onder de aandacht te brengen
- uw geloofwaardigheid en zichtbaarheid te vergroten
- uw merk en online aanwezigheid te versterken
- meer bekendheid en bereik voor uw boek te creëren

Ons team regelt het hele proces, eenvoudig en gemakkelijk van begin tot eind.
[paid] De Author Spotlight is een betaalde dienst; ik stuur u graag de details en tarieven.

Heeft u interesse? Beantwoord dan gewoon deze e-mail, dan stuur ik u de informatie en de volgende stappen.

Met vriendelijke groet,
{SENDER_NAME}
{SENDER_TITLE}, The Author Ledger
{WEBSITE}

--
Ik vond uw contactadres op {source_description}. Wilt u geen berichten meer ontvangen? Antwoord dan met ‘afmelden’ en wij nemen geen contact meer op.
Colofon: {IMPRINT_URL} · Privacy: {PRIVACY_URL}
```

==================================================
EXAMPLE ROW (fictional, for format only; never add it to the file)
==================================================

- author_name: `Jane Example`
- email: `hello@janeexamplebooks.com`
- first_name: `Jane`
- book_title: `The Lighthouse Ledger`
- book_topic: `cozy mystery set in coastal Maine`
- personalization_detail: `Book 3 of the Harbor Point series; the author bio says the series was inspired by her years running a bookshop in Portland.`
- personalization_reason: `Established series and a clear origin story give us a strong spotlight angle.`
- personalized_opening: `I came across The Lighthouse Ledger on Amazon and loved that the Harbor Point series grew out of your years running a bookshop in Portland — that's exactly the kind of story our readers enjoy.`
- subject_line: `Author Spotlight invitation: The Lighthouse Ledger`
- email_body: `(Template EN, fully filled in)`
- research_sources: `https://janeexamplebooks.com/contact | https://www.amazon.com/stores/Jane-Example/author/B0XXXXXXX`
- research_confidence: `High`
- personalization_status: `Ready`
- send_status: `Not sent`
- date_sent: *(blank)*

==================================================
RESEARCH LOG
==================================================

Keep an internal log, `research_log.csv`. It's for the audit trail, not a user-facing deliverable. After no more than two browser actions (navigation, view, click, or scroll), append: timestamp, market, region, city, query, candidate names, emails seen, source URLs, evidence type, decision (accepted / rejected / merged into existing), reason. Never log addresses or phone numbers.

==================================================
MERGE PROCESS (idempotent)
==================================================

Each merge must:

1. Read the latest canonical file.
2. Make the timestamped backup.
3. Keep every column and existing value.
4. Match on `dedupe_key`, Amazon author URLs/IDs on all marketplaces, normalized names, aliases, and emails.
5. Never duplicate `batch_id`s, notes, emails, sources, or rows. Running the same merge twice must change nothing.
6. Keep each row's evidence_type exactly as recorded.
7. Check row counts and key uniqueness before and after.
8. Replace the canonical file atomically.

==================================================
QUALITY CONTROL (after every merge)
==================================================

Run the validator if one exists. Otherwise check:

- Columns A–O are present, in order, with the exact names.
- Every row has an `email` and at least one `research_sources` URL.
- `dedupe_key` and emails are unique.
- No `{`, `}`, or `[paid]` left in `email_body`, `subject_line`, or `personalized_opening`.
- `send_status` is `Not sent` or `Hold – legal review`. Every Germany row is on hold.
- `date_sent` is blank on every row you added.
- No phone numbers or street addresses in any column.

Then report:

- Rows, unique dedupe keys, and email-bearing rows, before and after
- New accepted authors, with market, region, evidence_type, and research_confidence for each
- Counts by `personalization_status` and `send_status`
- Rows rejected or merged this pass, with reasons
- Validator status and any issues
- Progress toward TARGET_TOTAL, by market

==================================================
WORKING STYLE
==================================================

- Never fabricate prospects, emails, URLs, evidence, or personalization details.
- Quality beats count. 300 solid rows are worth more than 1,000 weak ones.
- Keep the current region active until it's reasonably complete, then move to the next one in MARKET_ORDER.
- Share the canonical file only at logical checkpoints (the end of each region or every 100 new rows) or when I ask.

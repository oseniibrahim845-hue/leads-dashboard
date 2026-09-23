# Researcher brief: Australian Shopify prospects for the Jarvis AI assistant

Sender: **Cynthia Nana**. She builds AI "Jarvis" personal assistants and automation for Shopify stores. They handle product listing creation, titles and descriptions, SEO descriptions, tags, collections, product updates and metadata, social and promotional content, email and customer-support workflows, and reports. The tools are Shopify, n8n, OpenAI or Gemini.

## Tooling constraint (important)
Direct page fetching (WebFetch or curl) to store websites is BLOCKED in this environment. Use only the **WebSearch** tool.
Verify facts through the search results the tool returns: result titles, URLs and the result summaries.
- The email must appear in the search output and be tied to that business. Never guess an email. Never build one from a name, and never infer a pattern (e.g. don't assume hello@domain exists).
- Before accepting, run a **second confirming search** with the exact email in quotes, e.g. `"hello@brand.com.au"`. Alternatively, search `brand contact email`. Accept only if the second search again shows that exact email tied to the business. If the confirming search doesn't show it, reject.
- The email domain should normally match the store's domain. A free-mail address (gmail etc.) is acceptable only if the business itself publishes it as its contact email; set confidence to Medium at most.
- Only list URLs that actually appeared in your search results. Never invent URLs or contact-page paths.

## Who qualifies
Australian businesses (based in AU) that operate a Shopify store or clear eCommerce store with active products. Shopify signals include: Shopify case studies, "powered by Shopify", myshopify domains, Shopify app/partner listings, Shopify store lists (e.g. storeleads, builtwith, Shopify stores directories), job ads mentioning Shopify, and founders talking about Shopify.
If Shopify can't be confirmed but it's clearly an active AU online store, you may still accept it. Set confidence to Medium and say "Shopify not confirmed" in notes.
Prefer independent brands and SMEs where a small team does the product-listing work. Skip giant corporates (e.g. Myer, JB Hi-Fi).
Reject: inactive stores, no public email, no location in Australia, unverifiable info, marketplaces-only sellers with no store.

## Buying intent labels
"High - <reason>": large or growing catalog, frequent new-product drops, hiring Shopify/eCommerce help, multi-channel selling, or explicit automation interest.
"Medium - <reason>": an established active store, active social promos, email marketing, etc.

## Writing (per prospect, all unique)
- first_name: the owner/founder first name if publicly known. Otherwise use a sensible team greeting like "there" is NOT allowed. Use "Team" only if no person is identifiable (keep prospect_name = company then).
- personalization_detail: one specific, verified fact about their store (e.g. number of collections, new drops, a product range, a stockist network, a recent launch).
- personalization_reason: why that fact makes AI product/listing/content automation relevant. Never claim they definitely need it.
- personalized_opening: 1-2 natural sentences that open with the specific reason for writing. NEVER start with "I hope you're doing well", "Hope you're having a great day", "I came across your profile", or "I noticed you have a Shopify store".
- subject_line: short (3-8 words), specific to them, no hype, no caps, no urgency. Every one unique; don't copy example subjects.
- email_body: "Hi <First Name>,\n\n<opening>\n\n<why it caught attention + 1-2 sentences on what Cynthia builds, only the services relevant to this store>\n\n<one simple question CTA>\n\nBest regards,\nCynthia Nana". 80-150 words. Plain, human language.
  Banned words and phrases: tailored solutions, seamless, cutting edge, revolutionize, unlock, transform your workflow, leverage, game changing, guaranteed.
  Never promise sales or revenue.

## Output
Write a JSON file (path given in your task) with this shape:
```json
{
  "segment": "...",
  "searches_run": 0,
  "accepted": [
    {
      "prospect_name": "Jane Smith (or company name if no person)",
      "company": "Brand Pty Ltd / Brand",
      "first_name": "Jane",
      "email": "hello@brand.com.au",
      "state": "Queensland",
      "city": "Brisbane",
      "shopify_niche": "Fashion - womenswear boutique",
      "shopify_store_url": "https://brand.com.au",
      "product_category": "Women's dresses, tops, accessories",
      "buying_intent": "High - ...",
      "personalization_detail": "...",
      "personalization_reason": "...",
      "personalized_opening": "...",
      "subject_line": "...",
      "email_body": "...",
      "source_url": "the URL where the email was shown in search results",
      "other_urls": "other checked URLs, newline separated",
      "evidence": "Who they are; what they sell; Shopify signal; why relevant; where the email was found + confirming search query used",
      "evidence_type": "one of: Official Website, Shopify Store, LinkedIn, Public Business Profile, Public Social Profile, Shopify Profile, Public Job Posting, Search Result Verified, Other",
      "research_confidence": "High or Medium",
      "notes": "anything reviewers should know"
    }
  ],
  "rejected": [{"company": "...", "reason": "..."}]
}
```
The state must be the full AU state name (New South Wales, Victoria, Queensland, Western Australia, South Australia, Tasmania, Australian Capital Territory, Northern Territory).
Log every business you evaluated but rejected in "rejected". Count your searches honestly.
Write the file incrementally (rewrite it every ~10 accepted) so progress isn't lost.

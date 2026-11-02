# CivicGuide — PPT Presentation Draft

**Suggested length:** 10–12 minutes, 12 slides  
**Audience:** project evaluator, faculty panel, civic-tech stakeholders  
**Presentation rule:** label all measured results and prototype limitations honestly. Do not present the demonstration catalog as live government data.

## Slide 1 — Title

**CivicGuide: Eligibility-First Government Scheme Discovery**

- Natural-language scheme discovery and eligibility explanation
- Name, institution, department, guide, and date: fill in before presenting
- Tagline: “Find relevant schemes. Understand why they may fit.”

**Speaker note:** Introduce the citizen problem rather than the technology stack.

**Visual:** CivicGuide home page screenshot from the running app.

## Slide 2 — The Problem

- Scheme information is spread across central and state government portals.
- Eligibility rules are written in administrative language.
- Citizens often know their need but not the scheme's name.
- A relevant-looking search result may still be ineligible.

**Speaker note:** Explain the difference between finding a page and understanding whether its rules fit a person.

**Visual:** Simple citizen → many portals → confusing conditions diagram.

## Slide 3 — Project Goal and Safety Principle

- Convert a citizen's plain-language situation into structured needs/profile fields.
- Evaluate explicit scheme rules and explain each pass, failure, or unknown.
- Rank only schemes not rejected by a required eligibility condition.
- **Invariant:** semantic similarity never overrides factual ineligibility.

**Visual:** “Required rule failed → excluded from primary recommendations” flow.

## Slide 4 — System Architecture

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS.
- **API:** FastAPI, Pydantic, SQLAlchemy.
- **Core logic:** deterministic NLP, eligibility engine, weighted recommendation.
- **Data/trust:** SQLite or configured Postgres, snapshots, extraction, trust gate.
- **Discovery:** robots-aware sitemap/index crawler and heuristic page classifier.

**Visual:** Use the architecture diagram in `CIVICGUIDE_IEEE_REPORT.md`.

## Slide 5 — User Journey

1. Citizen enters a natural-language request.
2. CivicGuide extracts profile details, needs, and life events.
3. Missing required details become clarifying questions.
4. Eligibility rules are evaluated with per-rule traces.
5. Results are ranked, grouped, filterable, and explainable.
6. Citizen can save a scheme or open its official source/application link.

**Visual:** 6-step horizontal process.

## Slide 6 — Eligibility-First Recommendation

- Deterministic rule engine returns eligible, likely eligible, needs-more-information, or not-eligible.
- A required failed rule blocks the scheme from the primary list.
- Semantic matching contributes only to need relevance.
- Near misses are separate and show why a result failed.

**Speaker note:** Give the PM-KISAN non-farmer test scenario as an example of the hard rule.

**Visual:** Example rule trace with “farmer status: fail.”

## Slide 7 — Scheme Data and Trust

- Current catalog: **71 records** (confirm against repository data before presenting).
- 12 real schemes marked verified; 4 real schemes pending rule review.
- 55 synthetic demonstration records, explicitly labelled as demo data.
- Discovery pages and application URLs are candidates; human review is required before verified-catalog promotion.
- Current verified geography is six Tamil Nadu schemes plus six central schemes—not national coverage.

**Speaker note:** “Verified” describes catalog review status; it is not a government endorsement.

**Visual:** 12 / 4 / 55 stacked bar with labels “verified / review / demo”.

## Slide 8 — Live Scheme Discovery and Link Extraction

- Sitemap and same-host index-page harvesting.
- URL keyword/blocklist filtering; page classification uses eligibility, benefit, application, and document signals.
- Tender, recruitment, error, and login pages are penalized or rejected.
- Extracts canonical source URL and candidate HTTPS application links for human review.
- Respects robots.txt, request delays, cache, and TLS verification.

**Speaker note:** State that network access varies by government portal. On 2026-10-19, the National Portal listing returned HTTP 403 and the configured Tamil Nadu listing returned HTTP 404; do not claim a full successful national crawl.

## Slide 9 — Citizen-Facing Features

- Natural-language search and profile wizard.
- Scheme cards with eligibility status, benefits, source/application links, and central/state label.
- Central-government / state-government filter buttons and category filters.
- Explainability drawer, near misses, opportunity map, saved schemes, and issue reports.

**Visual:** Results screenshot showing government-level filters and one scheme card.

## Slide 10 — Validation

- Backend API/unit tests and discovery heuristic tests.
- Frontend ESLint and production build.
- Include actual test/lint/build results from the current run here.
- Tests establish software behavior; they do not prove real-world eligibility accuracy.

**Speaker note:** Replace this text with the verified command output after the final run; do not reuse a stale test count.

## Slide 11 — Limitations and Risks

- Catalog coverage and state breadth are limited.
- Some rules and current application status require human verification.
- English-pattern NLP; no completed human user study.
- No measured precision@K, recall@K, NDCG, or human eligibility agreement yet.
- Government websites may block crawlers or change links/terms.
- Prototype needs production-grade privacy, deployment, and security review.

## Slide 12 — Roadmap and Closing

- Add state catalogs only after official-source and terms review.
- Human-review scraped links and eligibility rules; record evidence and review dates.
- Build an annotated evaluation set and measure retrieval plus eligibility accuracy.
- Add multilingual support, browser tests, and scheduled monitoring.
- Close: “CivicGuide helps people navigate public benefits; it does not replace government decisions.”

**Visual:** Three roadmap stages: data quality → evaluation → production readiness.

## Live Demo Plan

1. Start FastAPI and Next.js using the commands in the project report.
2. Search: “I am a 20-year-old female student from Tamil Nadu looking for education financial help.”
3. Show the state/central filter buttons and category filter.
4. Open a scheme explanation and point out the eligibility trace and official link.
5. Switch to saved schemes and the opportunity map.
6. If the backend is unavailable, use captured screenshots and clearly label them as screenshots.

## Final Pre-Presentation Checklist

- Replace all personal/institution placeholders on Slide 1.
- Re-run tests and enter actual results on Slide 10.
- Confirm catalog counts from `data/verified/schemes.json` and `data/demo/schemes.json`.
- Capture fresh CivicGuide screenshots; remove any personal profile data.
- Verify live official links and terms on the day of the presentation.
- Do not call candidate crawl output “verified schemes.”

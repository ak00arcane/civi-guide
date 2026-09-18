# Trust Pipeline — Architecture & Phase Status

This document tracks the scheme-verification pipeline that replaces manual,
per-scheme human review with an automated, source-cross-checked confidence
score. It is separate from the core app phases tracked in
[`PROJECT_STATE.md`](../PROJECT_STATE.md) (NLP, eligibility engine, ranking,
UI — all already complete). This pipeline only concerns **how a scheme
record earns the right to be stated as fact**.

## Design principle

No dashboard, no human sitting in the loop per scheme. Verification moves
from the per-scheme workflow into the pipeline itself: independent sources
are fetched, cross-checked, and scored; the eligibility engine reads the
score and changes *what it's allowed to claim* — assertive, hedged, or
discovery-only. Disagreement between sources never picks a winner — it
demotes. When the pipeline is unsure, the app stops asserting and links out
instead.

## Data flow

```
fetch layer -> raw snapshot store -> extractor (+ golden set) -> trust engine -> Scheme.confidence / mode -> eligibility engine language gate -> UI
                                                                        ^
                                                          weekly watcher re-runs this loop
```

## Score inputs (deterministic, no LLM judgement in the scoring step itself)

- **Source authority** — ministry `.gov.in` = 1.0, state portal = 0.9, myScheme = 0.8
- **Field agreement** — same field extracted from ≥2 independent sources,
  matching after normalisation → boost. Disagreement → hard penalty, auto-demote.
- **Extraction stability** — extractor run twice at temperature 0 on the same
  HTML; non-identical rule JSON → penalty.
- **Sanity rules** — income limit in plausible range, age min < age max, no
  contradictory clauses → penalty on failure.
- **Freshness** — days since last successful fetch decays the score.

## Phase status

| Phase | Description | Status |
| :--- | :--- | :--- |
| 0 | Handoff prep (README, junk cleanup) | **Done** |
| 1 | Schema + snapshot store | **Done** — provenance fields added, `confidence`/`trust_mode` on `Scheme`, `RawSnapshot` table + content-addressed disk store (`services/snapshots.py`), migrated (`alembic/versions/0002_trust_pipeline.py`) |
| 2 | Fetch layer (`httpx`, polite crawl) | **Done (httpx only, no Playwright yet).** `services/fetch_layer.py` (robots.txt per-domain, 1 req/sec, retry+backoff, OS-native TLS chain validation via `truststore`) and `scripts/fetch_sources.py`. Of the 12 verified schemes' official sources: 9 now fetch cleanly (`mudra.org.in` and `scd.tn.gov.in` were failing TLS verification — see the `truststore` fix below — and now work), 1 correctly skipped (`nha.gov.in` disallows `/PM-JAY` via robots.txt — by design, unfixable), 1 gets HTTP 403 (`education.gov.in`, likely blocking non-browser requests), 1 (`nsap.nic.in`) confirmed **genuinely down** — queried Google's public DNS resolver directly and got NXDOMAIN globally, not just locally; the catalog URL itself is correct per 3+ independent sources including myScheme. `pudhumaipenn.tn.gov.in` intermittently refuses the connection. Real bug found and fixed: the default `httpx.Client` used a static CA bundle that can't validate two of these sites' incomplete certificate chains; switched to `truststore.SSLContext` (OS-native chain building with AIA-fetching, same as a browser) — verification stays fully on, this is not `verify=False`. myScheme's own scheme-detail pages aren't in the source list yet (none of the 12 verified schemes cite myScheme as a source) — pulling those in needs a name→URL mapping step, not built. |
| 3 | Extractor + golden set | **Run for real, multiple times, against 9 of 12 schemes.** `extraction/extractor.py` supports `AnthropicSchemeExtractor` (billed, configured account has $0 credits) and `GeminiSchemeExtractor` (Google's free tier — what actually ran), chosen by `get_configured_extractor()` (prefers Gemini). `extraction/golden_set.py` uses the 12 hand-verified schemes as ground truth. As of the latest run: **6 of 12 schemes have a real, computed trust score**; the other 3 with snapshots (`TN-DIS-MAINTENANCE`, `IN-WCD-PMMVY`, `IN-FIN-CSIS`) are blocked purely on Gemini's **daily** quota (20 requests/day for `gemini-3.6-flash` on this account) — confirmed *not* a temporary new-project throttle, since it was still exactly 20 a day later; this looks like a sustained per-project cap. Extraction is frequently **unstable** between the two temperature=0 calls on the same input — flagged as worth softening later, not silently changed. Bugs found and fixed along the way: (a) `.env` variables were never actually loaded (nothing called `load_dotenv()`) — now goes through `Settings`; (b) `extract()` crashed on the `bytes` `read_snapshot_content()` actually returns; (c) `gemini-2.5-flash` is retired for new accounts, replaced with `gemini-3.6-flash`; (d) **a manual retry-on-429 loop was stacked on top of google-genai's own built-in retry (up to 5 attempts, backoff up to 60s each)** — on a real run the compounded retries across several schemes were indistinguishable from a hang and had to be killed. Fixed by removing the manual loop entirely and configuring the SDK's own `HttpOptions.timeout` (30s) + `HttpRetryOptions` (3 attempts, capped 30s delay) instead — bounded, and it now actually completes. |
| 4 | Trust engine (scoring, pure Python) | **Done, run against real extraction output, 12 unit tests.** `trust/engine.py` + `trust/sanity.py`. A real run surfaced and fixed a real gap: schemes with **zero** extracted rules were scoring `confidence≈0.70 mode=hedged` — the engine only validated the rules it had, not their absence, so "found nothing" misleadingly looked like "some confirmed info." `check_rule_sanity([])` now returns `["no eligibility rules extracted"]`, forcing `discovery_only`. All 6 scored schemes currently land at `discovery_only` (0.3–0.4) — the honestly-correct outcome for a first pass with one source per scheme (no cross-source agreement possible yet) and often-unstable extraction. |
| 5 | Gate in the UI (assertive/hedged/discovery-only language) | **Done** — `trust/language_gate.py`, wired into `services/recommend.py` (adds a `trust` field per recommendation) and rendered in `ExplainabilityDrawer.tsx`. Unscored schemes fall back to existing `is_demo`/`verification_status` flags rather than being silently hedged. |
| 6 | Weekly watcher (refetch, hash-diff, re-score, auto-demote) | **Code done, run multiple times manually, two real bugs found and fixed.** `services/watcher.py` + `scripts/watch_sources.py`. (1) Raw-byte hashing flagged markup noise (CSRF tokens, etc.) as "changed" — fixed with `RawSnapshot.normalized_hash` (tag-stripped text hash; migration `0004_normalized_hash.py`, backfilled). Confirmed on real data: `pmkisan.gov.in`, `cmchistn.com`, `pmmvy.wcd.gov.in` now correctly show unchanged between fetches; `msmeonline.tn.gov.in`, `pmay-urban.gov.in`, `education.gov.in` still show genuine visible-text volatility a text-hash can't solve. (2) The CLI scripts only called `db.commit()` once at the very end of the whole batch — an interrupted run (which happened, see Phase 3) lost all in-memory progress even though real work had completed. Fixed: all three scripts (`fetch_sources.py`, `watch_sources.py`, `score_from_snapshots.py`) now commit per-item and flush `print()` immediately, so progress is both durable and visible in real time instead of fully buffered until exit. No cron scheduled — manual trigger only. |
| 7 | Hardening | **Partially done.** Built: in-memory per-IP rate limiting (`app/rate_limit.py`, single-instance only — a multi-instance deploy needs a shared store like Redis), a "report wrong info" flow (`SchemeReport` model + `/api/scheme-reports` + admin review endpoints + a drawer UI), a timing-safe admin-token comparison, and OS-native TLS validation (see Phase 2). **Still open, and genuinely your call:** Postgres/hosting target and error-monitoring vendor (infra decisions), and DPDP-style data minimisation — the plan's original idea was "compute eligibility in-session and discard," but `CitizenProfile` currently persists income/disability/etc. across sessions on purpose (it's what makes saved schemes and personalization work). Ripping that out is a product-scope change, not a technical add-on — flagging rather than doing it silently. |
| 8 | Real users (5–10 people) | Not started — needs real people, not something to automate |

## myScheme scraping — investigated and rejected

Explored using myScheme.gov.in (the government's own 4,772-scheme aggregator)
as a much larger source of real data. Found that it's a JS-rendered SPA (a
plain HTTP fetch gets an empty shell), found its real backend search API
(`api.myscheme.gov.in/search/v6/schemes`, gated by an `x-api-key` embedded in
their own public frontend JS — not a secret, but also not a published
developer API), and confirmed via Playwright that it can be rendered and
queried. **Then checked their Terms of Use, which explicitly prohibit
automated access**: *"The use of any software (e.g. bots, scraper tools)...
is prohibited unless expressly authorized by myScheme in writing."*
robots.txt being permissive doesn't override that — ToS is the actual binding
policy. Not pursued, and won't be without written authorization from
myScheme. The official government API catalog (APISetu) lists a myScheme API
but it very likely requires registration/approval, which isn't something
completable in a session — worth pursuing yourself if you want that scale.

## Explanation-logic fixes (2026-09-12)

Two real correctness gaps, both found by working through "what does the app
say when nothing matches":

1. **A scheme with zero confirmed eligibility rules used to default to a
   confident `ELIGIBLE`** (`combine_status([])` fell through to `return
   ELIGIBLE` with no rules to fail against) — exactly the "claiming something
   we don't know" failure this whole pipeline exists to prevent. Fixed:
   `combine_status` now returns `NEEDS_INFO` for an empty rule list.
2. **The empty "no schemes found" state gave no reason.** `services/recommend.py`
   now returns a `no_match_explanation` field distinguishing three honestly
   different situations, rendered in `ExplainabilityDrawer`'s empty state:
   - `unclear_concern` — too little was shared to tell what's needed
   - `no_data_for_need` — we understood the need, but have no verified
     scheme for it (a data-coverage gap, not a fact about the citizen)
   - `not_eligible` — real schemes exist for this need and the citizen
     doesn't meet their criteria

## Real coverage expansion (2026-09-12)

Added 4 more real, individually-researched schemes via the same method as
the original 12 (find the real official ministry site, verify it's reachable
and robots.txt-permits it, let the pipeline extract rules from the live
page — never hand-written from memory): **Pradhan Mantri Ujjwala Yojana**
(`pmuy.gov.in`), **PM Fasal Bima Yojana** (`pmfby.gov.in`), **PM SVANidhi**
(`pmsvanidhi.mohua.gov.in`), **Atal Pension Yojana**
(`npscra.proteantech.in` — the old `npscra.nsdl.co.in` domain has migrated,
worth knowing if researching further schemes). Two more candidates (PMEGP,
Sukanya Samriddhi Yojana) were researched but every official URL found for
them returned 403 or 404 from this fetcher — dropped rather than force a
possibly-stale URL into the catalog. **Total real schemes: 16** (up from
12), all 4 new ones fetched successfully; extraction/scoring for them is
queued but blocked on today's already-exhausted Gemini quota — re-run
`scripts/score_from_snapshots.py` once it resets. New entries carry
`verification_status: "needs_review"` (not `"VERIFIED"`) since I confirmed
they're real, reachable schemes but haven't hand-verified their exact rules —
that's what the pipeline is for. `extraction/golden_set.py` now filters to
`VERIFIED` records only, since the new entries have no human-confirmed rules
to serve as ground truth.

## What's real vs stubbed right now

**Real:** the 12 schemes in `data/verified/schemes.json` were hand-verified
against live ministry/state portals at `last_verified_date`; the eligibility
engine, NLP pipeline, ranking, and UI are fully implemented and tested. The
fetch layer has run against all 12 sources multiple times (9 currently
fetchable). The full pipeline — fetch → snapshot → extract → trust-score →
language gate → UI — has run end to end for real: **6 of 12 schemes now
carry a genuine, computed `confidence`/`trust_mode`** instead of
`NULL`/`unscored`, all correctly conservative (`discovery_only`) given only
one source per scheme exists so far.

**Not yet real:** the other 6 schemes are `unscored` — 3 purely because of
Gemini's daily quota (retry `scripts/score_from_snapshots.py` when quota
allows; each scheme needs 2 calls), and 3 because no snapshot exists yet
(`nha.gov.in` is robots.txt-blocked by design, `nsap.nic.in` is genuinely
down, `pudhumaipenn.tn.gov.in` intermittently refuses connections — retry
`scripts/fetch_sources.py` for that last one). The watcher (Phase 6) has
never been scheduled as a cron, and production hardening (Phase 7) has open
items that are genuinely yours to decide, not mine to guess at (see the
table above).

**Bugs found only because this was actually run, not just written:**
1. `.env` was silently never loaded (`os.environ.get` with no `load_dotenv()` anywhere).
2. `extract()` crashed on real snapshot data — it assumed `str`, `read_snapshot_content()` returns `bytes`.
3. A hardcoded Gemini model name (`gemini-2.5-flash`) was already retired for new accounts.
4. A hand-rolled retry loop stacked on top of the SDK's own built-in retry, compounding into what looked like an infinite hang across a multi-scheme batch — had to be killed and fixed.
5. Schemes with zero extracted rules were scoring `hedged` instead of `discovery_only`, misrepresenting "we found nothing" as "somewhat confirmed."
6. `mudra.org.in`/`scd.tn.gov.in` failed TLS verification against a static CA bundle; fixed with OS-native chain validation (`truststore`), not by disabling verification.
7. Scripts committed once at the very end of a whole batch instead of per-item, so an interrupted run lost otherwise-completed work.

None of these would have surfaced from code review alone — each came from
actually executing the pipeline against real external sites and a real LLM
API under real rate limits.

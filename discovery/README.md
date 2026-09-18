# Discovery stage

Finds candidate scheme pages across government sites and filters out the ones
that aren't schemes — before any LLM call is made. This exists so extractor
quota is spent on real scheme pages instead of tender notices.

```
sitemaps + index pages  ->  harvest.py   ->  candidates.jsonl
candidates.jsonl        ->  classify.py  ->  classified.jsonl
classified.jsonl        ->  (existing extractor + trust engine)
```

Neither stage calls an LLM. Both are free to re-run.

## Install

```bash
pip install httpx beautifulsoup4 lxml pyyaml truststore
```

`truststore` is optional but strongly recommended — it's what makes the
`.gov.in` sites with incomplete certificate chains validate without ever
setting `verify=False`.

## Run

```bash
python harvest.py  --config sources.yaml --out candidates.jsonl
python classify.py --in candidates.jsonl --out classified.jsonl --min-score 0.55

# one source at a time while tuning
python harvest.py --only tn_gov --out tn.jsonl
python classify.py --in tn.jsonl --out tn_classified.jsonl --limit 50
```

```bash
pytest test_discovery.py -q     # 18 tests, no network
```

## Files

| File | What it does |
|---|---|
| `fetcher.py` | robots.txt, 1 req/sec per host, on-disk cache, OS-native TLS |
| `sources.yaml` | the seed list — adding a state is a config commit, not code |
| `harvest.py` | sitemap walking + index-page link extraction + keyword filter |
| `classify.py` | heuristic scoring of whether a page is a real scheme page |
| `test_discovery.py` | offline tests for every pure function |

## Adding a state

Append a block to `sources.yaml`:

```yaml
  - id: mh_gov
    name: Government of Maharashtra
    level: state
    state: MH
    method: both
    base_url: https://www.maharashtra.gov.in
    index_pages:
      - https://www.maharashtra.gov.in/schemes
    enabled: false
```

Leave `enabled: false` until you have read that domain's terms of use.
robots.txt being permissive does not override a terms page that bans
automated access — that distinction is exactly why `myscheme.gov.in` is not
in this file.

## How classification scores

Additive, transparent, no model involved. Positive signals (eligibility
language, benefits, how-to-apply, documents required, money figures,
issuing authority) add weight; negative signals (tender, recruitment, press
release, login wall, error page) subtract. A page with no eligibility
language is penalised regardless of how scheme-like it otherwise looks —
the eligibility engine has nothing to evaluate against without it.

Every accepted page carries its `signals` and `penalties` list into the
output, so the trust engine can cite why a page was let through.

Tune `--min-score` after your first real run. Check 20 accepted and 20
rejected pages by hand once, adjust the weights in `classify.py`, re-run.
That's the only calibration this stage needs, and it's a one-off.

## Second use for these signals

Once the extractor runs on an accepted page, the heuristic field values
(age bounds, income ceilings, state, category) can be compared against what
the LLM extracted. Agreement between two independent extraction methods is
a real trust signal, and it works even when a scheme has only one source —
which is currently every scheme in the catalog.

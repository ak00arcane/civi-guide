# CivicGuide implementation handoff

Greenfield MVP: Next.js + FastAPI + SQLite/Postgres. Local NLP (gazetteers + regex; optional spaCy). Hash embeddings by default; optional sentence-transformers.

**Do not edit** `.cursor/plans/civicguide_mvp_plan_e88f1eb0.plan.md`.

Phases: 0 bootstrap → 1 scheme KB → 2 eligibility → 3 NLP → 4 needs/life events → 5 ranker → 6 explain/opportunity map → 7 citizen UI → 8 admin → 9 evaluation → 10 saved/dashboard/README.

Hard rules: DB is factual source of truth; eligibility is deterministic; semantic similarity never overrides `not_eligible`; demo schemes always labeled demo.

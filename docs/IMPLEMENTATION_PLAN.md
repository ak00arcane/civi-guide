# CivicGuide implementation handoff

Greenfield MVP: Next.js + FastAPI + SQLite/Postgres. Local NLP (gazetteers + regex; optional spaCy). Hash embeddings by default; optional sentence-transformers.

**Do not edit** `.cursor/plans/civicguide_mvp_plan_e88f1eb0.plan.md`.

Phases:
- **Phase 0: Bootstrap** — Completed (FastAPI backend + Next.js App Router frontend).
- **Phase 1: Scheme KB** — Completed (12 real verified Central & TN schemes + 55 preserved demo schemes, SQLAlchemy models, data validators, CRUD APIs).
- **Phase 2: Eligibility Engine** — Completed (Deterministic rule evaluator & multi-status combiner).
- **Phase 3: NLP Engine** — Completed (Regex extractors, location gazetteers, clarifying questions, hashed embeddings).
- **Phase 4: Needs & Life Events** — Completed (11-category needs inference, life event detection, profile persistence).
- **Phase 5: Ranker** — Completed (Weighted multi-factor scorer, hard eligibility rejection).
- **Phase 6: Explainability & Opportunity Map** — Completed (Citizen match reasons, failure traces, near-misses, category maps).
- **Phase 7: Citizen Web UI** — Completed (Next.js responsive frontend, search bar, profile wizard, scheme cards, explainability drawer, opportunity map, bookmarks).
- **Phase 8: Admin & Quality Dashboard** — Backend API ready; Admin Web UI pending.
- **Phase 9: Evaluation & Test Suite** — Completed (19 comprehensive backend tests passing across all components).
- **Phase 10: Saved / Dashboard / README** — Completed (Saved schemes backend + UI complete, state and documentation updated).

Hard rules: DB is factual source of truth; eligibility is deterministic; semantic similarity never overrides `not_eligible`; demo schemes always labeled demo.

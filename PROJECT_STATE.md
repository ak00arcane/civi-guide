# CivicGuide — Project State & Architectural Summary

## 1. Project Overview
CivicGuide is an NLP-powered and deterministic recommendation system designed to assist citizens in discovering government schemes based on their natural-language needs and factual eligibility.

### Critical Design Principle
**Semantic similarity must NEVER override factual eligibility.**
If a scheme evaluates to `not_eligible` based on the citizen's profile attributes (e.g. age, income limit, state residency), the eligibility component score is strictly `0.0` and the scheme is excluded from primary recommendations regardless of high semantic query relevance.

---

## 2. Architecture & Components

```
civicguide/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI startup, verified auto-seeding & routing
│   │   ├── config.py            # Environment & ranking weight settings
│   │   ├── constants.py         # Category definitions & standard banners
│   │   ├── security.py          # Session cookie signer & admin token checks
│   │   ├── routers/             # API endpoints (schemes, eligibility, parse, profile, recommend, saved, admin, research)
│   │   └── schemas/             # Pydantic DTO contracts
│   ├── data_quality/
│   │   └── validators.py        # Scheme record validation & quality flags
│   ├── db/
│   │   ├── models.py            # Scheme, Rule, Source, CitizenProfile, LifeEvent, SavedScheme models
│   │   └── session.py           # SQLAlchemy database session setup
│   ├── eligibility/
│   │   ├── engine.py            # Deterministic rule evaluator (evaluate_rule, combine_status)
│   │   └── rules.py             # Rule types & supported operators
│   ├── nlp/
│   │   ├── extractors.py        # Regex & location gazetteer extractors (age, income, location, education, occupation)
│   │   ├── needs.py             # Explicit & inferred need detectors (11 categories)
│   │   ├── life_events.py       # Life event triggers (graduation, job loss, relocation, etc.)
│   │   ├── embeddings.py        # Deterministic 384-d hashed bag-of-words & cosine similarity
│   │   └── pipeline.py          # Complete parse_query pipeline & clarifying question generator
│   ├── recommendation/
│   │   ├── scorer.py            # Multi-factor weighted component scoring & hard eligibility invariant
│   │   ├── weights.py           # Configurable ranking weights
│   │   ├── grouping.py          # Category & need-based result grouping
│   │   └── opportunities.py     # Opportunity map generator & opportunity gap inference
│   ├── services/
│   │   ├── import_schemes.py    # Verified & demo catalog ingestion and embedding generator
│   │   ├── profile.py           # Profile persistence & change tracking
│   │   └── recommend.py         # End-to-end recommendation & audit log generator
│   └── tests/
│       ├── conftest.py          # Test fixtures and memory DB setup
│       ├── test_nlp.py          # NLP extraction, needs, and embedding tests
│       ├── test_eligibility.py  # Deterministic rule evaluator unit tests
│       ├── test_scorer_and_recommender.py # Scorer & hard eligibility invariant tests
│       ├── test_verified_catalog.py       # Verified catalog completeness and quality tests
│       └── test_api_endpoints.py          # FastAPI end-to-end route tests
├── frontend/
│   ├── next.config.ts           # Next.js configuration with proxy rewrite to FastAPI port 8000
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Primary Citizen discovery page
│   │   │   └── globals.css      # CivicGuide dark/light design system
│   │   ├── components/
│   │   │   ├── Header.tsx       # Navigation tabs & profile indicator
│   │   │   ├── SearchBox.tsx    # Natural-language prompt search with query chips
│   │   │   ├── ProfileWizard.tsx# Interactive profile & clarifying question modal
│   │   │   ├── SchemeCard.tsx   # Ranked scheme card with eligibility badges & bookmarking
│   │   │   ├── ExplainabilityDrawer.tsx # Transparent "Why you qualify / don't qualify" audit drawer
│   │   │   ├── OpportunityMap.tsx # Visual category bar charts & gap suggestions
│   │   │   └── SavedSchemesView.tsx # Bookmarks & personal reminder management
│   │   └── lib/
│   │       └── api.ts           # Type-safe API client
├── data/
│   ├── verified/
│   │   └── catalog.py           # 12 real, verified Central & Tamil Nadu government schemes
│   ├── demo/
│   │   └── catalog.py           # Labeled demo benefit schemes for research & fallback
│   └── gazetteers/
│       └── locations.json       # Indian states and major district mappings
```

---

## 3. Real Verified Schemes Catalog

| Scheme ID | Name | Category & Level | Official Info Source | Official Application Portal | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TN-EDU-PUDHUMAI-PENN` | Moovalur Ramamirtham Ammaiyar Higher Education Assurance Scheme (Pudhumai Penn) | Education (State - TN) | `https://www.pudhumaipenn.tn.gov.in/` | `https://www.pudhumaipenn.tn.gov.in/` | **VERIFIED** |
| `TN-SKL-NAAN-MUDHALVAN` | Naan Mudhalvan Skill Development Scheme | Employment (State - TN) | `https://www.naanmudhalvan.tn.gov.in/` | `https://www.naanmudhalvan.tn.gov.in/` | **VERIFIED** |
| `IN-AGR-PM-KISAN` | Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) | Agriculture (Central) | `https://pmkisan.gov.in/` | `https://pmkisan.gov.in/RegistrationFormNew.aspx` | **VERIFIED** |
| `TN-HLT-CMCHIS` | Chief Minister's Comprehensive Health Insurance Scheme (CMCHIS) | Healthcare (State - TN) | `https://www.cmchistn.com/` | `https://www.cmchistn.com/` | **VERIFIED** |
| `IN-HLT-PMJAY` | Ayushman Bharat - PM-JAY | Healthcare (Central) | `https://nha.gov.in/PM-JAY` | `https://beneficiary.nha.gov.in/` | **VERIFIED** |
| `IN-ENT-MUDRA` | Pradhan Mantri Mudra Yojana (PMMY) | Entrepreneurship (Central) | `https://www.mudra.org.in/` | `https://www.udyamimitra.in/` | **VERIFIED** |
| `TN-EMP-UYEGP` | Unemployed Youth Employment Generation Programme (UYEGP) | Employment (State - TN) | `https://www.msmeonline.tn.gov.in/uyegp/` | `https://www.msmeonline.tn.gov.in/uyegp/` | **VERIFIED** |
| `IN-HOU-PMAY-U` | Pradhan Mantri Awas Yojana - Urban (PMAY-U) | Housing (Central & TN) | `https://pmay-urban.gov.in/` | `https://pmay-urban.gov.in/` | **VERIFIED** |
| `IN-SEN-IGNOAPS` | Indira Gandhi National Old Age Pension Scheme (IGNOAPS) | Senior Citizens (Central & TN) | `https://nsap.nic.in/` | `https://tnesevai.tn.gov.in/` | **VERIFIED** |
| `TN-DIS-MAINTENANCE` | Tamil Nadu Maintenance Allowance for Differently Abled Persons | Disability (State - TN) | `https://scd.tn.gov.in/` | `https://tnesevai.tn.gov.in/` | **VERIFIED** |
| `IN-WCD-PMMVY` | Pradhan Mantri Matru Vandana Yojana (PMMVY) | Women & Child (Central & TN) | `https://pmmvy.wcd.gov.in/` | `https://pmmvy.wcd.gov.in/` | **VERIFIED** |
| `IN-FIN-CSIS` | Central Sector Interest Subsidy Scheme (CSIS) on Education Loans | Financial Assistance (Central) | `https://www.education.gov.in/scholarships-education-loan-0` | `https://www.vidyalakshmi.co.in/` | **VERIFIED** |

---

## 4. Phase Status

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | Bootstrap | **Completed** |
| **Phase 1** | Scheme Knowledge Base & Verified Catalog | **Completed (12 Real Verified Schemes + Demo Fallback)** |
| **Phase 2** | Deterministic Eligibility Engine | **Completed** |
| **Phase 3** | NLP & Attribute Extraction Engine | **Completed** |
| **Phase 4** | Needs Detection & Life Events | **Completed** |
| **Phase 5** | Multi-Factor Ranking Engine | **Completed** |
| **Phase 6** | Explainability & Opportunity Map | **Completed** |
| **Phase 7** | Citizen Web UI (Next.js Frontend) | **Completed** |
| **Phase 8** | Admin & Data Quality Dashboard | **Backend API Done / UI Pending** |
| **Phase 9** | Evaluation & Test Suite | **Completed (19 Unit Tests Passing)** |
| **Phase 10**| Saved Schemes & Documentation | **Completed** |

---

## 5. How to Run the Project & Run Tests

### Running Unit Tests
```bash
# In backend directory
python -m unittest discover tests -v
```
All 19 unit tests execute and pass covering NLP, Eligibility, Scoring Invariants, Catalog Quality, and API endpoints.

### Running the FastAPI Backend
```bash
# In backend directory
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### Running the Next.js Frontend
```bash
# In frontend directory
npm run dev -- --port 3000
```
- Citizen Web UI: `http://localhost:3000`

from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

root = Path(r'C:\Users\Akshaya\Projects\civicguide')
out = root / 'docs' / 'Review_II_CivicGuide.docx'
img_home = root / 'docs' / 'civicguide-home.png'
img_results = root / 'docs' / 'civicguide-results.png'
img_expl = root / 'docs' / 'civicguide-explanation.png'

for p in [img_home, img_results, img_expl]:
    if not p.exists():
        raise FileNotFoundError(f'Missing screenshot: {p}')

# Create document

doc = Document()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('CIVICGUIDE REVIEW II REPORT')
run.bold = True
run.font.size = 24

fields = [
    ('Name', '[Student Name]'),
    ('Registration Number', '[Registration Number]'),
    ('Course Details', '[Course Name / Semester / Department / Institution]'),
    ('Title of the Project', 'CivicGuide: NLP-Based Personalized Government Scheme Recommendation System with Eligibility-First Ranking and Explainable Decisions'),
]
for label, value in fields:
    para = doc.add_paragraph()
    para.add_run(f'{label}: ').bold = True
    para.add_run(str(value))

# Objectives

doc.add_heading('1. Objectives', level=1)
for item in [
    'To build a natural-language government scheme discovery system that accepts citizen queries in plain language.',
    'To extract citizen attributes such as age, income, state, education, occupation, disability, and employment status.',
    'To evaluate schemes using a deterministic eligibility engine so factual eligibility is prioritized over semantic similarity.',
    'To rank only eligible or likely eligible schemes using a weighted multi-factor scoring model.',
    'To provide explainability, trust labeling, near-miss reasoning, and official source links for transparency.',
    'To maintain a verified catalog and a demo/fallback catalog while clearly separating official and synthetic records.',
]:
    doc.add_paragraph(item, style='List Bullet')

# Architecture

doc.add_heading('2. System Architecture', level=1)
arch_text = (
    'Citizen Query -> Next.js Frontend -> FastAPI Backend -> NLP Parser -> User Profile + Needs + Life Events -> '
    'Eligibility Engine -> Recommendation Scorer -> Ranked Schemes / Near-Miss / Rejected Items -> Explainability UI\n\n'
    'Separate source-trust path: Official Sources -> Fetch & Snapshot Layer -> Rule Extraction -> Trust Engine -> Verified Catalog'
)
for line in arch_text.splitlines():
    para = doc.add_paragraph(line)
    if line.strip():
        para.runs[0].font.name = 'Consolas'
        para.runs[0].font.size = 10

# Screenshots

doc.add_heading('Figure 1: CivicGuide landing page', level=2)
doc.add_picture(str(img_home), width=Inches(6.5))

doc.add_heading('Figure 2: Recommendation results page', level=2)
doc.add_picture(str(img_results), width=Inches(6.5))

doc.add_heading('Figure 3: Explainability drawer', level=2)
doc.add_picture(str(img_expl), width=Inches(6.5))

# Experiments

doc.add_heading('3. Experiments Conducted to Date', level=1)
experiments = [
    ('Experiment 1: NLP Extraction Validation', 'The parser was tested on natural-language queries to extract age, income, state, education, occupation, disability, farmer and student status, plus need categories and life events. The deterministic extraction used regex rules and a location gazetteer.'),
    ('Experiment 2: Eligibility Engine Testing', 'Each scheme rule was evaluated against structured profile fields. Rules produced pass, fail, and unknown traces. A required failed rule caused the scheme to become not_eligible, while missing information led to needs_more_information.'),
    ('Experiment 3: Recommendation and Ranking Validation', 'The weighted recommender combined eligibility, need relevance, location match, profile/income fit, education/occupation fit, and usefulness. Semantic similarity was restricted to the need component instead of overriding eligibility.'),
    ('Experiment 4: Catalog Quality and Trust Validation', 'Verified, demo, and pending-review records were separated by trust status. The trust engine scored source authority, field agreement, extraction stability, sanity, and freshness.'),
    ('Experiment 5: API and End-to-End Integration', 'Backend endpoints were validated for parsing, recommendation, profile updates, saved schemes, and scheme reports. The frontend interacted successfully with the FastAPI backend.'),
]
for title, desc in experiments:
    p = doc.add_paragraph(title)
    p.runs[0].bold = True
    doc.add_paragraph(desc)

# Procedures and results

doc.add_heading('4. Procedures Followed and Results Obtained', level=1)
for item in [
    'The project was developed in stages: catalog creation, deterministic NLP parsing, rule-engine design, recommendation scoring, trust pipeline, and frontend integration.',
    'A verified catalog of government schemes was populated with official metadata and application links, while demo data was retained for research and labeled clearly as synthetic.',
    'The backend was implemented in Python using FastAPI and SQLAlchemy, while the frontend was developed using Next.js and TypeScript.',
    'Representative queries covering age limits, income conditions, education benefits, disability assistance, unemployment support, and housing assistance were used to verify the system behavior.',
    'The system was validated using the project test suite. Actual verification evidence: 92 backend tests passed in the completed pytest run.',
    'The system demonstrated that query relevance is not sufficient without eligibility support. Schemes failing mandatory criteria were excluded from primary recommendations and explained with near-miss reasoning.',
]:
    doc.add_paragraph(item, style='List Bullet')

# Summary

doc.add_heading('5. Summary', level=1)
doc.add_paragraph('CivicGuide is a working prototype for an eligibility-first recommendation system for government schemes. It combines natural-language understanding, deterministic eligibility checks, transparent rule traces, source trust labeling, and citizen-friendly results. The prototype is effective for research and demonstration purposes, while future work includes expanding the verified catalog and carrying out larger user evaluations.')

# Save
out.parent.mkdir(parents=True, exist_ok=True)
doc.save(out)
print(f'Created document: {out}')

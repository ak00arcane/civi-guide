"""50 labelled DEMO benefit records. Not real government schemes."""

DEMO_BANNER = "DEMO DATA – Replace with verified official scheme information."
COMMON_DOCS = [
    {"name": "Identity proof", "notes": "Demo only"},
    {"name": "Address proof", "notes": "Demo only"},
]
STEPS = ["Register on the demo portal", "Upload documents", "Submit application"]


def _src(path: str) -> list[dict]:
    return [
        {
            "official_source": f"https://example.gov.in/demo/{path}",
            "official_application_url": f"https://example.gov.in/demo/{path}/apply",
            "last_verified_date": "2026-08-01",
        }
    ]


def S(sid, name, cat, sub, state, desc, benefit, rules, **kw):
    rec = {
        "scheme_id": sid,
        "scheme_name": name,
        "category": cat,
        "sub_category": sub,
        "government_level": kw.get("level", "state" if state not in (None, "All") else "central"),
        "department": kw.get("dept", "Demo Department of Civic Benefits"),
        "state": None if state in (None, "All") else state,
        "district": kw.get("district"),
        "description": desc,
        "benefits_summary": benefit,
        "application_status": kw.get("status", "open"),
        "application_steps": STEPS,
        "deadline": kw.get("deadline", "2027-12-31"),
        "last_verified_date": "2026-08-01",
        "verification_status": kw.get("verification_status", "demo"),
        "is_demo": True,
        "demo_banner": DEMO_BANNER,
        "rules": rules,
        "benefits": [{"text": benefit}],
        "documents": kw.get("documents", COMMON_DOCS + [{"name": "Income certificate", "notes": "If applicable"}]),
        "sources": kw.get("sources", _src(sid.lower())),
    }
    return rec


def tn_rules(extra=None):
    r = [
        {"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
        {"rule_type": "max_age", "op": "lte", "value": 35, "required": True},
        {"rule_type": "income_max", "op": "lte", "value": 300000, "required": True},
        {"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True},
    ]
    if extra:
        r.extend(extra)
    return r


def catalog() -> list[dict]:
    items = []
    # Education
    items += [
        S("DEMO-TN-EDU-001", "DEMO TN Graduate Scholarship", "Education", "Scholarship", "Tamil Nadu",
          "Financial assistance for higher education for graduates in Tamil Nadu.", "₹50,000/year",
          tn_rules([{"rule_type": "education", "op": "in", "value": ["Graduate", "Engineering"], "required": True}])),
        S("DEMO-TN-EDU-002", "DEMO TN Engineering Tuition Support", "Education", "Tuition", "Tamil Nadu",
          "Support for engineering students paying college fees.", "₹40,000/year",
          tn_rules([{"rule_type": "education", "op": "in", "value": ["Engineering", "Student"], "required": True}])),
        S("DEMO-IN-EDU-003", "DEMO National Merit Grant", "Education", "Merit", "All",
          "National demo grant for students in higher education.", "₹30,000/year",
          [{"rule_type": "min_age", "op": "gte", "value": 16, "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 30, "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 800000, "required": True}]),
        S("DEMO-KA-EDU-004", "DEMO Karnataka Student Aid", "Education", "Aid", "Karnataka",
          "Student aid for Karnataka residents.", "₹25,000/year",
          [{"rule_type": "residency_state", "op": "in", "value": ["Karnataka"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 25, "required": True}]),
        S("DEMO-IN-EDU-005", "DEMO Hostel Stipend", "Education", "Hostel", "All",
          "Stipend for students living in hostels.", "₹2,000/month",
          [{"rule_type": "education", "op": "in", "value": ["Student", "Engineering"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 28, "required": True}]),
    ]
    # Employment + skill
    items += [
        S("DEMO-TN-EMP-001", "DEMO TN Job Seeker Support", "Employment", "Jobseeker", "Tamil Nadu",
          "Employment assistance for unemployed graduates in Tamil Nadu.", "Job matching stipend ₹8,000/month",
          tn_rules([{"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker"], "required": True},
                    {"rule_type": "education", "op": "in", "value": ["Graduate", "Engineering"], "required": False}])),
        S("DEMO-TN-SKL-001", "DEMO TN Skill Bridge", "Employment", "Skill", "Tamil Nadu",
          "Skill development training for unemployed youth.", "Free training + ₹5,000 stipend",
          tn_rules([{"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker"], "required": True}])),
        S("DEMO-IN-EMP-002", "DEMO National Apprentice Assist", "Employment", "Apprentice", "All",
          "Apprenticeship support for first-time job seekers.", "₹9,000/month",
          [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 30, "required": True},
           {"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker", "student"], "required": True}]),
        S("DEMO-IN-EMP-003", "DEMO Resume Clinic Grant", "Employment", "Placement", "All",
          "Placement preparation for graduates.", "Workshop access",
          [{"rule_type": "education", "op": "in", "value": ["Graduate", "Engineering"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 40, "required": True}]),
        S("DEMO-MH-EMP-004", "DEMO Maharashtra Wage Support", "Employment", "Wage", "Maharashtra",
          "Wage support for unemployed residents of Maharashtra.", "₹6,000/month",
          [{"rule_type": "residency_state", "op": "in", "value": ["Maharashtra"], "required": True},
           {"rule_type": "employment", "op": "in", "value": ["unemployed"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 250000, "required": True}]),
    ]
    # Healthcare
    items += [
        S("DEMO-IN-HLT-001", "DEMO National Health Cover Lite", "Healthcare", "Insurance", "All",
          "Demo health coverage for low-income families.", "Hospitalization cover ₹2 lakh",
          [{"rule_type": "income_max", "op": "lte", "value": 300000, "required": True}]),
        S("DEMO-TN-HLT-002", "DEMO TN Clinic Access", "Healthcare", "Primary", "Tamil Nadu",
          "Primary care access for Tamil Nadu residents.", "Free clinic visits",
          [{"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True}]),
        S("DEMO-IN-HLT-003", "DEMO Maternity Health Assist", "Healthcare", "Maternity", "All",
          "Maternity health support.", "₹12,000",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 45, "required": True}]),
        S("DEMO-IN-HLT-004", "DEMO Disability Rehab Care", "Healthcare", "Rehab", "All",
          "Rehabilitation support for persons with disability.", "Aid devices",
          [{"rule_type": "disability", "op": "in", "value": ["yes", "true", "disabled"], "required": True}]),
        S("DEMO-IN-HLT-005", "DEMO Senior Health Check", "Healthcare", "Geriatric", "All",
          "Annual health checks for seniors.", "Free checkup",
          [{"rule_type": "min_age", "op": "gte", "value": 60, "required": True}]),
    ]
    # Housing
    items += [
        S("DEMO-IN-HOU-001", "DEMO Affordable Home Interest Relief", "Housing", "Home", "All",
          "Interest relief for first home buyers with low income.", "Interest subsidy",
          [{"rule_type": "income_max", "op": "lte", "value": 600000, "required": True},
           {"rule_type": "min_age", "op": "gte", "value": 21, "required": True}]),
        S("DEMO-TN-HOU-002", "DEMO TN Rental Assist", "Housing", "Rent", "Tamil Nadu",
          "Rental assistance for urban youth.", "₹2,000/month",
          tn_rules()),
        S("DEMO-IN-HOU-003", "DEMO Rural Housing Demo", "Housing", "Rural", "All",
          "Rural housing construction support (demo).", "Construction grant",
          [{"rule_type": "income_max", "op": "lte", "value": 250000, "required": True}]),
        S("DEMO-KA-HOU-004", "DEMO Karnataka Shelter Aid", "Housing", "Shelter", "Karnataka",
          "Shelter aid for Karnataka low-income families.", "One-time grant",
          [{"rule_type": "residency_state", "op": "in", "value": ["Karnataka"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 200000, "required": True}]),
        S("DEMO-IN-HOU-005", "DEMO Women Home Ownership", "Housing", "Women", "All",
          "Home ownership support listed for women applicants.", "Down-payment assist",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 500000, "required": True}]),
    ]
    # Women & Child
    items += [
        S("DEMO-IN-WCD-001", "DEMO Child Nutrition Support", "Women & Child", "Nutrition", "All",
          "Nutrition support for young children.", "Ration kit",
          [{"rule_type": "other", "op": "eq", "value": {"name": "has_child", "allowed": ["yes"]}, "required": False}]),
        S("DEMO-IN-WCD-002", "DEMO Women Livelihood Starter", "Women & Child", "Livelihood", "All",
          "Livelihood support for women entrepreneurs.", "₹25,000 seed",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 50, "required": True}]),
        S("DEMO-TN-WCD-003", "DEMO TN Mother Assist", "Women & Child", "Maternity", "Tamil Nadu",
          "Maternal support for Tamil Nadu residents.", "₹8,000",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True}]),
        S("DEMO-IN-WCD-004", "DEMO Creche Access Demo", "Women & Child", "Childcare", "All",
          "Childcare access for working parents.", "Subsidised creche",
          [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True}]),
        S("DEMO-IN-WCD-005", "DEMO Girl Student Cycle", "Women & Child", "Education", "All",
          "Support listed for girl students in secondary school.", "Transport support",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 18, "required": True}]),
    ]
    # Agriculture
    items += [
        S("DEMO-IN-AGR-001", "DEMO Crop Support Lite", "Agriculture", "Crop", "All",
          "Input support for small farmers.", "Seed kit",
          [{"rule_type": "farmer", "op": "in", "value": ["farmer", "yes"], "required": True}]),
        S("DEMO-TN-AGR-002", "DEMO TN Irrigation Assist", "Agriculture", "Water", "Tamil Nadu",
          "Irrigation demo support for Tamil Nadu farmers.", "Pump subsidy",
          [{"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True},
           {"rule_type": "farmer", "op": "in", "value": ["farmer", "yes"], "required": True}]),
        S("DEMO-IN-AGR-003", "DEMO Farm Income Shield", "Agriculture", "Insurance", "All",
          "Demo crop income shield.", "Payout on loss",
          [{"rule_type": "farmer", "op": "in", "value": ["farmer", "yes"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 400000, "required": False}]),
        S("DEMO-PB-AGR-004", "DEMO Punjab Farmer Credit", "Agriculture", "Credit", "Punjab",
          "Credit support for Punjab farmers.", "Interest subvention",
          [{"rule_type": "residency_state", "op": "in", "value": ["Punjab"], "required": True},
           {"rule_type": "farmer", "op": "in", "value": ["farmer", "yes"], "required": True}]),
        S("DEMO-IN-AGR-005", "DEMO Agri Skill Youth", "Agriculture", "Skill", "All",
          "Agri skill program for rural youth.", "Training",
          [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 35, "required": True}]),
    ]
    # Financial assistance
    items += [
        S("DEMO-TN-FIN-001", "DEMO TN Livelihood Grant", "Financial Assistance", "Grant", "Tamil Nadu",
          "Financial assistance for low-income youth starting work or business.", "₹40,000 grant",
          tn_rules()),
        S("DEMO-IN-FIN-002", "DEMO Emergency Family Support", "Financial Assistance", "Relief", "All",
          "Short-term financial assistance for low-income families.", "₹10,000",
          [{"rule_type": "income_max", "op": "lte", "value": 250000, "required": True}]),
        S("DEMO-IN-FIN-003", "DEMO Education Loan Interest Demo", "Financial Assistance", "Education", "All",
          "Interest support for higher education loans.", "Interest subsidy",
          [{"rule_type": "education", "op": "in", "value": ["Student", "Engineering", "Graduate"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 800000, "required": True}]),
        S("DEMO-IN-FIN-004", "DEMO High Income Bond (control)", "Financial Assistance", "Bond", "All",
          "Control record requiring high income so most users are not eligible.", "N/A",
          [{"rule_type": "income_max", "op": "lte", "value": 50000, "required": True}]),
        S("DEMO-UP-FIN-005", "DEMO UP Family Assist", "Financial Assistance", "Family", "Uttar Pradesh",
          "Family assistance for Uttar Pradesh residents.", "₹15,000",
          [{"rule_type": "residency_state", "op": "in", "value": ["Uttar Pradesh"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 200000, "required": True}]),
    ]
    # Disability
    items += [
        S("DEMO-IN-DIS-001", "DEMO Assistive Device Grant", "Disability", "Device", "All",
          "Assistive device support for persons with disability.", "Device grant",
          [{"rule_type": "disability", "op": "in", "value": ["yes", "true", "disabled"], "required": True}]),
        S("DEMO-TN-DIS-002", "DEMO TN Inclusive Livelihood", "Disability", "Livelihood", "Tamil Nadu",
          "Livelihood support in Tamil Nadu for persons with disability.", "₹20,000",
          [{"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True},
           {"rule_type": "disability", "op": "in", "value": ["yes", "disabled"], "required": True}]),
        S("DEMO-IN-DIS-003", "DEMO Inclusive Education Aid", "Disability", "Education", "All",
          "Education aid for students with disability.", "₹15,000",
          [{"rule_type": "disability", "op": "in", "value": ["yes", "disabled"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 30, "required": True}]),
        S("DEMO-IN-DIS-004", "DEMO Caregiver Support", "Disability", "Care", "All",
          "Caregiver stipend demo.", "₹3,000/month",
          [{"rule_type": "disability", "op": "in", "value": ["yes", "disabled"], "required": False}]),
        S("DEMO-IN-DIS-005", "DEMO Accessible Transport", "Disability", "Transport", "All",
          "Transport concession demo.", "Pass",
          [{"rule_type": "disability", "op": "in", "value": ["yes", "disabled"], "required": True}]),
    ]
    # Senior
    items += [
        S("DEMO-IN-SEN-001", "DEMO Senior Pension Lite", "Senior Citizens", "Pension", "All",
          "Demo pension for seniors.", "₹1,000/month",
          [{"rule_type": "min_age", "op": "gte", "value": 60, "required": True}]),
        S("DEMO-TN-SEN-002", "DEMO TN Elder Care", "Senior Citizens", "Care", "Tamil Nadu",
          "Elder care support in Tamil Nadu.", "Care visits",
          [{"rule_type": "min_age", "op": "gte", "value": 60, "required": True},
           {"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True}]),
        S("DEMO-IN-SEN-003", "DEMO Senior Food Security", "Senior Citizens", "Food", "All",
          "Food support for seniors with low income.", "Ration",
          [{"rule_type": "min_age", "op": "gte", "value": 60, "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 200000, "required": True}]),
        S("DEMO-IN-SEN-004", "DEMO Reverse Mortgage Demo", "Senior Citizens", "Housing", "All",
          "Housing liquidity demo for seniors.", "Advisory",
          [{"rule_type": "min_age", "op": "gte", "value": 60, "required": True}]),
        S("DEMO-IN-SEN-005", "DEMO Elder Skill Volunteer", "Senior Citizens", "Community", "All",
          "Volunteer stipend for retired professionals.", "Honorarium",
          [{"rule_type": "min_age", "op": "gte", "value": 55, "required": True}]),
    ]
    # Entrepreneurship
    items += [
        S("DEMO-TN-ENT-001", "DEMO TN First Business Support", "Entrepreneurship", "Startup", "Tamil Nadu",
          "Support for residents of Tamil Nadu who want to start a small business.", "₹1,00,000 seed (demo)",
          tn_rules([{"rule_type": "business", "op": "in", "value": ["planning", "unknown", "none"], "required": False},
                    {"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker", "self_employed"], "required": False}])),
        S("DEMO-IN-ENT-002", "DEMO Micro Enterprise Credit", "Entrepreneurship", "Credit", "All",
          "Micro credit for new small businesses.", "Credit guarantee (demo)",
          [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 45, "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 500000, "required": True}]),
        S("DEMO-IN-ENT-003", "DEMO Women Startup Boost", "Entrepreneurship", "Women", "All",
          "Entrepreneurship support listed for women founders.", "₹50,000",
          [{"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 45, "required": True}]),
        S("DEMO-IN-ENT-004", "DEMO Street Vendor Cart", "Entrepreneurship", "Vendor", "All",
          "Cart/kiosk support for micro vendors.", "Equipment",
          [{"rule_type": "income_max", "op": "lte", "value": 300000, "required": True},
           {"rule_type": "min_age", "op": "gte", "value": 18, "required": True}]),
        S("DEMO-KA-ENT-005", "DEMO Karnataka Founder Fellowship", "Entrepreneurship", "Fellowship", "Karnataka",
          "Founder fellowship for Karnataka residents.", "Stipend",
          [{"rule_type": "residency_state", "op": "in", "value": ["Karnataka"], "required": True},
           {"rule_type": "min_age", "op": "gte", "value": 21, "required": True}]),
    ]
    # Extra mixed to reach ~50 + quality/expired controls
    items += [
        S("DEMO-IN-EDU-006", "DEMO Digital Learning Stipend", "Education", "Digital", "All",
          "Device stipend for students in higher education.", "Tablet stipend",
          [{"rule_type": "education", "op": "in", "value": ["Student", "Engineering"], "required": True},
           {"rule_type": "income_max", "op": "lte", "value": 300000, "required": True}]),
        S("DEMO-TN-EMP-005", "DEMO TN Career Counselling", "Employment", "Counselling", "Tamil Nadu",
          "Career counselling for unemployed youth in Tamil Nadu.", "Counselling sessions",
          tn_rules([{"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker"], "required": True}])),
        S("DEMO-XX-EXP-001", "DEMO Expired Youth Grant", "Financial Assistance", "Expired", "Tamil Nadu",
          "Expired demo record used to test deadline handling.", "₹1",
          tn_rules(), deadline="2020-01-01", verification_status="expired", status="closed"),
        S("DEMO-XX-REV-001", "DEMO Needs Review Incomplete", "Healthcare", "Review", "All",
          "Incomplete demo record missing official source.", "Unknown",
          [{"rule_type": "min_age", "op": "gte", "value": 1, "required": False}],
          sources=[], verification_status="needs_review"),
        S("DEMO-IN-EMP-006", "DEMO Graduate Placement Drive", "Employment", "Campus", "All",
          "Placement drive for recent graduates.", "Interview slots",
          [{"rule_type": "education", "op": "in", "value": ["Graduate", "Engineering"], "required": True},
           {"rule_type": "employment", "op": "in", "value": ["unemployed", "job_seeker"], "required": True},
           {"rule_type": "max_age", "op": "lte", "value": 28, "required": True}]),
    ]
    assert len(items) >= 50
    return items

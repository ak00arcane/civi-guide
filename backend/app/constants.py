DISCLAIMER = (
    "CivicGuide is an independent information and recommendation tool. "
    "Applications are completed on the official government portal."
)
DEMO_BANNER = "DEMO DATA – Replace with verified official scheme information."
UNVERIFIED = "Official information could not be verified."

CATEGORIES = [
    "Education",
    "Employment",
    "Healthcare",
    "Housing",
    "Women & Child",
    "Agriculture",
    "Financial Assistance",
    "Disability",
    "Senior Citizens",
    "Entrepreneurship",
]

NEED_TO_CATEGORY = {
    "education": "Education",
    "employment": "Employment",
    "healthcare": "Healthcare",
    "housing": "Housing",
    "women_child": "Women & Child",
    "agriculture": "Agriculture",
    "financial_assistance": "Financial Assistance",
    "disability": "Disability",
    "senior_citizens": "Senior Citizens",
    "entrepreneurship": "Entrepreneurship",
    "skill_development": "Employment",
}

CATEGORY_TO_NEED = {v: k for k, v in NEED_TO_CATEGORY.items()}
CATEGORY_TO_NEED["Employment"] = "employment"

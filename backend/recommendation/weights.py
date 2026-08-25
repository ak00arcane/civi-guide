from app.config import settings


def weights() -> dict[str, float]:
    return {
        "eligibility": settings.weight_eligibility,
        "need": settings.weight_need,
        "location": settings.weight_location,
        "profile": settings.weight_profile,
        "education_occupation": settings.weight_education_occupation,
        "usefulness": settings.weight_usefulness,
    }

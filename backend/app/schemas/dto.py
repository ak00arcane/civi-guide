from pydantic import BaseModel, Field


class ParseQueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class ProfileIn(BaseModel):
    fields: dict = Field(default_factory=dict)
    source_query: str | None = Field(default=None, max_length=4000)
    needs: list[dict] | None = None


class ProfileUpdateIn(BaseModel):
    fields: dict
    source_query: str | None = None


class DetectNeedsIn(BaseModel):
    text: str | None = Field(default=None, max_length=4000)
    fields: dict = Field(default_factory=dict)


class LifeEventIn(BaseModel):
    event_code: str
    from_value: str | None = None
    to_value: str | None = None
    text: str | None = None


class EligibilityIn(BaseModel):
    profile: dict
    scheme_id: str | None = None


class RecommendIn(BaseModel):
    profile: dict | None = None
    needs: list[dict] | None = None
    query: str | None = Field(default=None, max_length=4000)


class SavedIn(BaseModel):
    scheme_id: str
    personal_status: str = "saved"


class AdminSchemeIn(BaseModel):
    scheme_id: str
    scheme_name: str
    category: str
    description: str
    sub_category: str | None = None
    government_level: str | None = None
    department: str | None = None
    state: str | None = None
    district: str | None = None
    benefits_summary: str | None = None
    application_status: str | None = "open"
    application_steps: list[str] | None = None
    deadline: str | None = None
    last_verified_date: str | None = None
    verification_status: str = "demo"
    is_demo: bool = True
    rules: list[dict] = Field(default_factory=list)
    benefits: list[dict] = Field(default_factory=list)
    documents: list[dict] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)

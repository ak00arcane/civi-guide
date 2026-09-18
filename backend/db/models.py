from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


def uid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    anon_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CitizenProfile(Base):
    __tablename__ = "citizen_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    education: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    student_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    family_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    disability_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    farmer_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    business_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    annual_family_income: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locale: Mapped[str] = mapped_column(String(16), default="en")
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CitizenSituation(Base):
    __tablename__ = "citizen_situations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("citizen_profiles.id"))
    source_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    situation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Need(Base):
    __tablename__ = "needs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_profiles.id"), nullable=True)
    situation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_situations.id"), nullable=True)
    need_code: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    explicit: Mapped[bool] = mapped_column(Boolean, default=True)


class LifeEvent(Base):
    __tablename__ = "life_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("citizen_profiles.id"))
    event_code: Mapped[str] = mapped_column(String(64))
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    from_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ProfileChange(Base):
    __tablename__ = "profile_changes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("citizen_profiles.id"))
    field_name: Mapped[str] = mapped_column(String(64))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QueryHistory(Base):
    __tablename__ = "query_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_profiles.id"), nullable=True)
    raw_query: Mapped[str] = mapped_column(Text)
    parse_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Scheme(Base):
    __tablename__ = "schemes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scheme_name: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(64), index=True)
    sub_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    government_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    benefits_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    application_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_verified_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="demo")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_banner: Mapped[str] = mapped_column(
        Text, default="DEMO DATA – Replace with verified official scheme information."
    )
    quality_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Trust pipeline (see docs/TRUST_PIPELINE.md). Populated by the trust engine (Phase 4),
    # never by the catalog importer — NULL/"unscored" means the pipeline has not run yet.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    trust_mode: Mapped[str] = mapped_column(String(32), default="unscored")
    last_scored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    rules: Mapped[list["SchemeRule"]] = relationship(back_populates="scheme", cascade="all, delete-orphan")
    benefits: Mapped[list["SchemeBenefit"]] = relationship(back_populates="scheme", cascade="all, delete-orphan")
    documents: Mapped[list["SchemeDocument"]] = relationship(back_populates="scheme", cascade="all, delete-orphan")
    sources: Mapped[list["SchemeSource"]] = relationship(back_populates="scheme", cascade="all, delete-orphan")
    embedding: Mapped["SchemeEmbedding | None"] = relationship(back_populates="scheme", cascade="all, delete-orphan", uselist=False)


class SchemeRule(Base):
    __tablename__ = "scheme_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    rule_type: Mapped[str] = mapped_column(String(64))
    op: Mapped[str] = mapped_column(String(16), default="eq")
    value: Mapped[dict | list | str | int | float | None] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    scheme: Mapped[Scheme] = relationship(back_populates="rules")


class SchemeBenefit(Base):
    __tablename__ = "scheme_benefits"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    text: Mapped[str] = mapped_column(Text)
    scheme: Mapped[Scheme] = relationship(back_populates="benefits")


class SchemeDocument(Base):
    __tablename__ = "scheme_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    name: Mapped[str] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheme: Mapped[Scheme] = relationship(back_populates="documents")


class SchemeSource(Base):
    __tablename__ = "scheme_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    official_source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    official_application_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_verified_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Provenance (see docs/TRUST_PIPELINE.md), filled in by the fetch layer (Phase 2).
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_snapshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scheme: Mapped[Scheme] = relationship(back_populates="sources")


class RawSnapshot(Base):
    """A single fetch of a source URL, independent of whether it has been matched to a
    Scheme or extracted yet. This is the snapshot store the fetch layer (Phase 2) writes
    into; the extractor (Phase 3) reads from it. See docs/TRUST_PIPELINE.md."""

    __tablename__ = "raw_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str | None] = mapped_column(String(36), ForeignKey("schemes.id"), nullable=True)
    source_url: Mapped[str] = mapped_column(String(512), index=True)
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    # Hash of normalized (tag-stripped, whitespace-collapsed) text, not raw bytes. Change
    # detection (Phase 6) diffs on this instead of content_hash, since raw HTML on most
    # gov sites carries volatile bits (CSRF tokens, timestamps, rotating banners) that
    # would otherwise make nearly every fetch look "changed" even when it isn't.
    normalized_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_snapshot_path: Mapped[str] = mapped_column(String(512))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SchemeEmbedding(Base):
    __tablename__ = "scheme_embeddings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"), unique=True)
    vector: Mapped[list] = mapped_column(JSON)
    model_name: Mapped[str] = mapped_column(String(128), default="hash-bow-384")
    scheme: Mapped[Scheme] = relationship(back_populates="embedding")


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    situation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_situations.id"), nullable=True)
    profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_profiles.id"), nullable=True)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    scheme_id: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    eligibility_status: Mapped[str] = mapped_column(String(32))
    need_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecommendationReason(Base):
    __tablename__ = "recommendation_reasons"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    recommendation_id: Mapped[str] = mapped_column(String(36), ForeignKey("recommendations.id"))
    kind: Mapped[str] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SchemeReport(Base):
    """A citizen-submitted "this looks wrong" report on a scheme (Phase 7, see
    docs/TRUST_PIPELINE.md). Feeds a human review queue, not the automated
    trust score directly — a single anonymous report is too easy to spam or
    get wrong to auto-demote a scheme on its own."""

    __tablename__ = "scheme_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scheme_pk: Mapped[str] = mapped_column(String(36), ForeignKey("schemes.id"))
    scheme_id: Mapped[str] = mapped_column(String(64))
    profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("citizen_profiles.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SavedScheme(Base):
    __tablename__ = "saved_schemes"
    __table_args__ = (UniqueConstraint("profile_id", "scheme_id", name="uq_saved_profile_scheme"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("citizen_profiles.id"))
    scheme_id: Mapped[str] = mapped_column(String(64))
    personal_status: Mapped[str] = mapped_column(String(32), default="saved")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

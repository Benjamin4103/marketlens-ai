import uuid
from typing import List, Optional

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import ClaimType, TrendDirection


class Company(UUIDPKMixin, TimestampMixin, Base):
    """A company entity, reusable across research jobs (e.g. seen as both
    the subject and a competitor in different projects)."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    competitor_rows: Mapped[List["Competitor"]] = relationship(back_populates="company")


class Competitor(UUIDPKMixin, TimestampMixin, Base):
    """A company's role as a competitor within a specific research job,
    holding structured comparison data (products, pricing, positioning...)."""

    __tablename__ = "competitors"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))

    business_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    products: Mapped[list] = mapped_column(JSON, default=list)
    pricing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_market: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geography: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    positioning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recent_developments: Mapped[list] = mapped_column(JSON, default=list)
    market_position_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100, relative
    source_ids: Mapped[list] = mapped_column(JSON, default=list)  # citation trail

    company: Mapped["Company"] = relationship(back_populates="competitor_rows")


class MarketMetric(UUIDPKMixin, TimestampMixin, Base):
    """A quantitative claim (market size, growth rate, CAGR...) that MUST be
    tied to a source. Unsourced numeric claims are rejected by the
    Evidence/Fact-Check agent before reaching this table."""

    __tablename__ = "market_metrics"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Market Size 2025"
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # USD_BN, PERCENT, etc.
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Trend(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trends"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    direction: Mapped[TrendDirection] = mapped_column(
        SAEnum(TrendDirection), default=TrendDirection.stable
    )
    evidence: Mapped[list] = mapped_column(JSON, default=list)  # [{claim, source_id}]
    affected_companies: Mapped[list] = mapped_column(JSON, default=list)
    business_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class SentimentResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sentiment_results"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)  # company/product name
    positive_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    negative_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    neutral_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    recurring_themes: Mapped[list] = mapped_column(JSON, default=list)
    top_complaints: Mapped[list] = mapped_column(JSON, default=list)
    data_available: Mapped[bool] = mapped_column(default=True)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)


class Insight(UUIDPKMixin, TimestampMixin, Base):
    """A single analytical statement produced by the Market Analyst / Strategy
    agents, explicitly tagged as fact, inference, or recommendation."""

    __tablename__ = "insights"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    section: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "market_overview"
    claim_type: Mapped[ClaimType] = mapped_column(SAEnum(ClaimType), default=ClaimType.inference)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Recommendation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="")
    supporting_evidence: Mapped[list] = mapped_column(JSON, default=list)  # source_ids
    expected_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1 = highest

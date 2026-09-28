import uuid
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin


class Report(UUIDPKMixin, TimestampMixin, Base):
    """The final assembled market intelligence report for a job. Sections are
    stored as structured JSON so the frontend can render them directly and
    exporters (PDF/Markdown/JSON) can reuse the same source of truth."""

    __tablename__ = "reports"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_jobs.id"), unique=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    sections: Mapped[dict] = mapped_column(JSON, default=dict)
    # sections: {executive_summary, market_overview, market_size_growth, drivers,
    #   challenges, customer_segments, competitive_landscape, competitor_comparison,
    #   trends, recent_developments, sentiment, swot, opportunities, threats,
    #   recommendations, key_takeaways}  -- each value may be null with a note
    # if "Insufficient reliable data found."
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low/medium/high

    job: Mapped["ResearchJob"] = relationship(back_populates="report")

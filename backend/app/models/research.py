import uuid
from typing import List, Optional

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, JSON, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import ResearchDepth, JobStatus


class ResearchProject(UUIDPKMixin, TimestampMixin, Base):
    """A recurring research subject, e.g. 'Indian EV Market'. Each project can
    be (re)researched over time via multiple ResearchJobs, which enables the
    'what changed?' historical comparison feature."""

    __tablename__ = "research_projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(50), default="market")  # market | company | comparison
    is_archived: Mapped[bool] = mapped_column(default=False)

    owner: Mapped["User"] = relationship(back_populates="research_projects")
    queries: Mapped[List["ResearchQuery"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[List["ResearchJob"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    snapshots: Mapped[List["ResearchSnapshot"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ResearchQuery(UUIDPKMixin, TimestampMixin, Base):
    """The parameters of a single research request."""

    __tablename__ = "research_queries"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id")
    )
    raw_query: Mapped[str] = mapped_column(String(500), nullable=False)
    geography: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_period: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    depth: Mapped[ResearchDepth] = mapped_column(
        SAEnum(ResearchDepth), default=ResearchDepth.standard
    )
    competitors_requested: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    project: Mapped["ResearchProject"] = relationship(back_populates="queries")
    job: Mapped[Optional["ResearchJob"]] = relationship(back_populates="query", uselist=False)


class ResearchJob(UUIDPKMixin, TimestampMixin, Base):
    """Tracks execution of the async research pipeline for one query."""

    __tablename__ = "research_jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id")
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_queries.id"), unique=True
    )
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.pending)
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    steps_log: Mapped[list] = mapped_column(JSON, default=list)  # [{step, status, ts}]
    agent_runs: Mapped[list] = mapped_column(JSON, default=list)  # observability per agent
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo_mode: Mapped[bool] = mapped_column(default=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sources_retrieved_count: Mapped[int] = mapped_column(Integer, default=0)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["ResearchProject"] = relationship(back_populates="jobs")
    query: Mapped["ResearchQuery"] = relationship(back_populates="job")
    report: Mapped[Optional["Report"]] = relationship(back_populates="job", uselist=False)


class ResearchSnapshot(UUIDPKMixin, TimestampMixin, Base):
    """Point-in-time capture of a project's key findings, used to compute
    'What Changed?' diffs between research runs."""

    __tablename__ = "research_snapshots"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id")
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    snapshot_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # snapshot_data holds: {market_size, growth_rate, competitors: [...], trends: [...],
    #   top_recommendations: [...], risk_level, confidence}

    project: Mapped["ResearchProject"] = relationship(back_populates="snapshots")

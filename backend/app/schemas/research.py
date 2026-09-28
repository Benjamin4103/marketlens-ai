import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResearchDepth, JobStatus


class ResearchCreate(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="e.g. 'Indian EV market'")
    geography: Optional[str] = None
    time_period: Optional[str] = None
    depth: ResearchDepth = ResearchDepth.standard
    competitors: List[str] = Field(default_factory=list)


class ResearchQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    raw_query: str
    geography: Optional[str]
    time_period: Optional[str]
    depth: ResearchDepth
    competitors_requested: List[str] = Field(default_factory=list)


class ResearchJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    query_id: uuid.UUID
    status: JobStatus
    current_step: Optional[str]
    progress_pct: int
    is_demo_mode: bool
    sources_retrieved_count: int
    duration_seconds: Optional[float]
    error_message: Optional[str]
    created_at: datetime


class ResearchProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    subject_type: str
    is_archived: bool
    created_at: datetime


class ResearchProjectDetail(ResearchProjectOut):
    queries: List[ResearchQueryOut] = Field(default_factory=list)
    jobs: List[ResearchJobOut] = Field(default_factory=list)


class ResearchStatusOut(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    current_step: Optional[str]
    progress_pct: int
    steps_log: list = Field(default_factory=list)
    error_message: Optional[str] = None


class CompareRequest(BaseModel):
    companies: List[str] = Field(..., min_length=2, max_length=5)

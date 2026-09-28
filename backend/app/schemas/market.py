import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SourceType, ClaimType, TrendDirection


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    title: str
    publisher: Optional[str]
    published_at: Optional[datetime]
    retrieved_at: datetime
    source_type: SourceType
    topic: Optional[str]
    company: Optional[str]
    relevance_score: float
    is_demo: bool


class CompetitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_id: uuid.UUID
    business_model: Optional[str]
    products: List[str] = Field(default_factory=list)
    pricing: Optional[str]
    target_market: Optional[str]
    geography: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    positioning: Optional[str]
    recent_developments: List[str] = Field(default_factory=list)
    market_position_score: Optional[float]
    source_ids: List[uuid.UUID] = Field(default_factory=list)
    company_name: Optional[str] = None  # populated in route from join


class TrendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str
    direction: TrendDirection
    evidence: list = Field(default_factory=list)
    affected_companies: List[str] = Field(default_factory=list)
    business_impact: Optional[str]
    source_count: int
    confidence: float


class SentimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject: str
    positive_pct: Optional[float]
    negative_pct: Optional[float]
    neutral_pct: Optional[float]
    sample_size: int
    recurring_themes: List[str] = Field(default_factory=list)
    top_complaints: List[str] = Field(default_factory=list)
    data_available: bool


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    section: str
    claim_type: ClaimType
    text: str
    source_ids: List[uuid.UUID] = Field(default_factory=list)
    confidence: float


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    recommendation: str
    rationale: str
    supporting_evidence: List[uuid.UUID] = Field(default_factory=list)
    expected_impact: Optional[str]
    risk: Optional[str]
    confidence: float
    priority: int


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_id: uuid.UUID
    title: str
    sections: dict
    overall_confidence: float
    risk_level: Optional[str]
    created_at: datetime


class WhatChangedOut(BaseModel):
    project_id: uuid.UUID
    previous_job_id: Optional[uuid.UUID]
    current_job_id: uuid.UUID
    new_developments: List[str] = Field(default_factory=list)
    changed_metrics: List[dict] = Field(default_factory=list)
    new_competitors: List[str] = Field(default_factory=list)
    new_trends: List[str] = Field(default_factory=list)
    new_risks: List[str] = Field(default_factory=list)
    changed_recommendations: List[str] = Field(default_factory=list)
    note: Optional[str] = None

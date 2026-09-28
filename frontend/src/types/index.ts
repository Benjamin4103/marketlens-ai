export type ResearchDepth = "quick" | "standard" | "deep";
export type JobStatus =
  | "pending" | "planning" | "collecting" | "processing"
  | "analyzing" | "verifying" | "completed" | "failed";
export type ClaimType = "fact" | "inference" | "recommendation";
export type TrendDirection = "emerging" | "growing" | "stable" | "declining";
export type SourceType = "news" | "web" | "report" | "company_site" | "social" | "demo";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface ResearchProject {
  id: string;
  title: string;
  subject_type: string;
  is_archived: boolean;
  created_at: string;
}

export interface ResearchQuery {
  id: string;
  raw_query: string;
  geography: string | null;
  time_period: string | null;
  depth: ResearchDepth;
  competitors_requested: string[];
}

export interface ResearchJob {
  id: string;
  project_id: string;
  query_id: string;
  status: JobStatus;
  current_step: string | null;
  progress_pct: number;
  is_demo_mode: boolean;
  sources_retrieved_count: number;
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
}

export interface ResearchProjectDetail extends ResearchProject {
  queries: ResearchQuery[];
  jobs: ResearchJob[];
}

export interface ResearchStatus {
  job_id: string;
  status: JobStatus;
  current_step: string | null;
  progress_pct: number;
  steps_log: { step: string; status: string; ts: string }[];
  error_message: string | null;
}

export interface SourceItem {
  id: string;
  url: string;
  title: string;
  publisher: string | null;
  published_at: string | null;
  retrieved_at: string;
  source_type: SourceType;
  topic: string | null;
  company: string | null;
  relevance_score: number;
  is_demo: boolean;
}

export interface CompetitorItem {
  id: string;
  company_id: string;
  company_name: string | null;
  business_model: string | null;
  products: string[];
  pricing: string | null;
  target_market: string | null;
  geography: string[];
  strengths: string[];
  weaknesses: string[];
  positioning: string | null;
  recent_developments: string[];
  market_position_score: number | null;
}

export interface TrendItem {
  id: string;
  name: string;
  description: string;
  direction: TrendDirection;
  evidence: any[];
  affected_companies: string[];
  business_impact: string | null;
  source_count: number;
  confidence: number;
}

export interface SentimentItem {
  id: string;
  subject: string;
  positive_pct: number | null;
  negative_pct: number | null;
  neutral_pct: number | null;
  sample_size: number;
  recurring_themes: string[];
  top_complaints: string[];
  data_available: boolean;
}

export interface RecommendationItem {
  id: string;
  recommendation: string;
  rationale: string;
  supporting_evidence: string[];
  expected_impact: string | null;
  risk: string | null;
  confidence: number;
  priority: number;
}

export interface ReportData {
  id: string;
  job_id: string;
  title: string;
  sections: Record<string, any>;
  overall_confidence: number;
  risk_level: string | null;
  created_at: string;
}

export interface WhatChanged {
  project_id: string;
  previous_job_id: string | null;
  current_job_id: string;
  new_developments: string[];
  changed_metrics: { metric: string; previous: any; current: any }[];
  new_competitors: string[];
  new_trends: string[];
  new_risks: string[];
  changed_recommendations: string[];
  note?: string | null;
}

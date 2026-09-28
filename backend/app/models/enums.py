import enum


class ResearchDepth(str, enum.Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class JobStatus(str, enum.Enum):
    pending = "pending"
    planning = "planning"
    collecting = "collecting"
    processing = "processing"
    analyzing = "analyzing"
    verifying = "verifying"
    completed = "completed"
    failed = "failed"


class AgentName(str, enum.Enum):
    research_planner = "research_planner"
    web_research = "web_research"
    news_research = "news_research"
    competitor_intel = "competitor_intel"
    market_trend = "market_trend"
    sentiment = "sentiment"
    market_analyst = "market_analyst"
    strategy = "strategy"
    evidence_check = "evidence_check"


class SourceType(str, enum.Enum):
    news = "news"
    web = "web"
    report = "report"
    company_site = "company_site"
    social = "social"
    demo = "demo"


class ClaimType(str, enum.Enum):
    fact = "fact"
    inference = "inference"
    recommendation = "recommendation"


class TrendDirection(str, enum.Enum):
    emerging = "emerging"
    growing = "growing"
    stable = "stable"
    declining = "declining"


class ExportFormat(str, enum.Enum):
    pdf = "pdf"
    markdown = "markdown"
    json = "json"

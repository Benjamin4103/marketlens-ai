# Architecture

## System overview

```mermaid
flowchart TB
    U[User] --> FE[React Dashboard]
    FE --> API[FastAPI API]
    API --> ORCH[Research Orchestrator]
    ORCH --> AGENTS[Research Agents]
    ORCH --> DB[(PostgreSQL)]

    AGENTS --> WEB[Web Agent]
    AGENTS --> NEWS[News Agent]
    AGENTS --> COMP[Competitor Agent]
    AGENTS --> TREND[Trend Agent]
    AGENTS --> SENT[Sentiment Agent]

    WEB --> CLEAN[Data Cleaning]
    NEWS --> CLEAN
    COMP --> CLEAN
    CLEAN --> DB
    DB --> VEC[(pgvector)]
    VEC --> RAG[RAG Retrieval]
    RAG --> ANALYSIS[Analysis Agents]

    ANALYSIS --> MARKET[Market Analyst Agent]
    ANALYSIS --> STRAT[Strategy Agent]
    MARKET --> VERIFY[Evidence Verification Agent]
    STRAT --> VERIFY
    VERIFY --> REPORT[Final Report]
    REPORT --> FE
    REPORT --> PDF[PDF / Markdown / JSON Export]
```

## Research pipeline (per job)

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant O as Orchestrator
    participant D as Demo/Real Data Source
    participant DB as PostgreSQL

    U->>API: POST /research {query, depth, competitors}
    API->>DB: create ResearchProject + ResearchQuery + ResearchJob (pending)
    API-->>U: job_id

    U->>API: POST /research/{job_id}/run
    API->>O: run_research_pipeline(job_id) [background task]
    API-->>U: 200 OK (job now "planning")

    loop 8-step pipeline
        O->>D: collect / analyze data for this step
        O->>DB: persist sources / competitors / trends / insights
        O->>DB: update job.status, progress_pct, steps_log
    end

    O->>DB: build_report_sections() -> Report
    O->>DB: write ResearchSnapshot (for What Changed?)
    O->>DB: job.status = completed

    U->>API: GET /research/{job_id}/status (polled every ~900ms)
    API-->>U: {status, progress_pct, steps_log}
    U->>API: GET /research/{job_id}/report
    API-->>U: 19-section report
```

## Database schema

```mermaid
erDiagram
    USERS ||--o{ RESEARCH_PROJECTS : owns
    RESEARCH_PROJECTS ||--o{ RESEARCH_QUERIES : has
    RESEARCH_PROJECTS ||--o{ RESEARCH_JOBS : has
    RESEARCH_PROJECTS ||--o{ RESEARCH_SNAPSHOTS : has
    RESEARCH_QUERIES ||--|| RESEARCH_JOBS : triggers
    RESEARCH_JOBS ||--o{ SOURCES : collects
    RESEARCH_JOBS ||--o{ COMPETITORS : identifies
    RESEARCH_JOBS ||--o{ MARKET_METRICS : records
    RESEARCH_JOBS ||--o{ TRENDS : detects
    RESEARCH_JOBS ||--o{ SENTIMENT_RESULTS : analyzes
    RESEARCH_JOBS ||--o{ INSIGHTS : generates
    RESEARCH_JOBS ||--o{ RECOMMENDATIONS : generates
    RESEARCH_JOBS ||--|| REPORTS : produces
    SOURCES ||--o{ DOCUMENTS : extracted_into
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : chunked_into
    COMPANIES ||--o{ COMPETITORS : referenced_by

    USERS {
        uuid id PK
        string email
        string hashed_password
    }
    RESEARCH_PROJECTS {
        uuid id PK
        uuid owner_id FK
        string title
        string subject_type
    }
    RESEARCH_JOBS {
        uuid id PK
        uuid project_id FK
        uuid query_id FK
        enum status
        int progress_pct
        json steps_log
        bool is_demo_mode
    }
    SOURCES {
        uuid id PK
        uuid job_id FK
        string url
        string publisher
        datetime published_at
        float relevance_score
        bool is_demo
    }
    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        text text
        vector embedding
    }
    TRENDS {
        uuid id PK
        uuid job_id FK
        string name
        enum direction
        float confidence
    }
    RECOMMENDATIONS {
        uuid id PK
        uuid job_id FK
        text recommendation
        text rationale
        float confidence
        int priority
    }
    REPORTS {
        uuid id PK
        uuid job_id FK
        json sections
        float overall_confidence
        string risk_level
    }
```

## Agent responsibilities

| Agent | Input | Output |
|---|---|---|
| Research Planner | raw query | research plan (question list) |
| Web Research | plan | `Source` rows (web) |
| News Research | plan | `Source` rows (news), prioritized by recency |
| Competitor Intelligence | plan + competitor list | `Competitor` rows (structured comparison) |
| Market Trend | collected sources | `Trend` rows with direction + confidence |
| Sentiment Analysis | collected sources | `SentimentResult` rows (only where data supports it) |
| Market Analyst | RAG-retrieved context | `Insight` rows (fact/inference), market overview |
| Strategy | market analysis | `Recommendation` rows with rationale + risk |
| Evidence / Fact-Check | all of the above | rejects unsupported numeric claims before report assembly |

In this build, `app/services/demo_data.py` produces a deterministic,
clearly-labeled dataset that stands in for the combined output of all nine
agents so the full pipeline (steps, persistence, report assembly, export,
diffing) is exercised end-to-end without requiring paid API keys.
`app/services/orchestrator.py` has one clearly-marked seam
(`generate_demo_dataset(...)` call) where a real LangGraph agent graph would
be substituted once `OPENAI_API_KEY` / `SEARCH_API_KEY` / `NEWS_API_KEY` are
configured.

## RAG pipeline (schema-ready, not yet populated with real embeddings)

```mermaid
flowchart LR
    S[Sources] --> EX[Text Extraction]
    EX --> CL[Cleaning]
    CL --> CH[Chunking]
    CH --> EMB[Embeddings]
    EMB --> PG[(pgvector)]
    PG --> SEM[Semantic Retrieval]
    SEM --> CTX[Context Construction]
    CTX --> LLM[LLM]
    LLM --> OUT[Evidence-backed Analysis]
```

The `document_chunks` table (with a 1536-dim `vector` column matching
`text-embedding-3-small`) and the `pgvector` extension are live and verified
in this build's PostgreSQL instance. What's missing is real document text to
chunk and embed -- that arrives once the Web/News agents fetch live pages
instead of demo data.

## Why FastAPI BackgroundTasks instead of Celery (for now)

Celery + Redis are fully configured (`CELERY_BROKER_URL`,
`CELERY_RESULT_BACKEND` in settings, Redis running in docker-compose) but the
orchestrator currently runs as a FastAPI `BackgroundTask`. For a portfolio
demo this is simpler to reason about and debug; swapping in a Celery worker
means moving `run_research_pipeline` into a `@celery_app.task` and calling
`.delay()` from the route instead of `background_tasks.add_task(...)` -- the
orchestrator function itself doesn't need to change.

# API Reference

Base URL: `http://localhost:8000/api`

Interactive OpenAPI docs are always available at `/docs` (Swagger UI) and
`/redoc` while the backend is running. This file is a quick reference.

All endpoints except `/health`, `/auth/register`, and `/auth/login` require
an `Authorization: Bearer <token>` header, obtained from `/auth/login`.

## Auth

### `POST /auth/register`
```json
{ "email": "you@example.com", "password": "...", "full_name": "Your Name" }
```
Returns the created user (`201`).

### `POST /auth/login`
```json
{ "email": "you@example.com", "password": "..." }
```
Returns `{ "access_token": "...", "token_type": "bearer" }`.

## Research

### `POST /research`
Creates (or reuses, by title) a research project, a new query, and a
`pending` job.
```json
{
  "query": "Indian electric vehicle market",
  "geography": "India",
  "time_period": "2024-2026",
  "depth": "standard",
  "competitors": ["Tata Motors", "Ola Electric"]
}
```
Returns a `ResearchJob` (`201`). Re-running the same `query` title reuses the
same `ResearchProject`, which is what powers **What Changed?**.

### `GET /research`
Lists the current user's research projects, most recently updated first.

### `GET /research/{project_id}`
Full project detail including all `queries` and `jobs` for that project.

### `POST /research/{job_id}/run`
Kicks off the async pipeline for a `pending` or `failed` job. Returns
immediately; poll `/status` for progress.

### `GET /research/{job_id}/status`
```json
{
  "job_id": "...",
  "status": "analyzing",
  "current_step": "Analyzing trends",
  "progress_pct": 62,
  "steps_log": [{ "step": "Research plan created", "status": "done", "ts": "..." }],
  "error_message": null
}
```
`status` is one of: `pending, planning, collecting, processing, analyzing,
verifying, completed, failed`.

### `GET /research/{job_id}/sources`
List of `Source` objects (url, title, publisher, published_at, source_type,
relevance_score, is_demo).

### `GET /research/{job_id}/competitors`
List of `Competitor` objects with `company_name`, business model, pricing,
strengths/weaknesses, positioning, market_position_score.

### `GET /research/{job_id}/trends`
List of `Trend` objects with direction (`emerging|growing|stable|declining`),
confidence, source_count, business_impact.

### `GET /research/{job_id}/sentiment`
List of `SentimentResult` objects. Empty when sentiment data wasn't
available for the subject (never fabricated).

### `GET /research/{job_id}/insights`
List of `Insight` objects, each tagged `claim_type`: `fact | inference |
recommendation`.

### `GET /research/{job_id}/recommendations`
List of `Recommendation` objects with rationale, expected_impact, risk,
confidence, priority (1 = highest).

### `GET /research/{job_id}/report`
The assembled `Report`: `title`, `sections` (19-key dict), `overall_confidence`,
`risk_level`. Returns `404` until the job completes.

### `POST /research/{job_id}/export?fmt=json|markdown|pdf`
Streams the report in the requested format. `pdf` returns
`application/pdf` with a `Content-Disposition` header for download.

### `GET /research/{project_id}/what-changed`
Diffs the two most recent `ResearchSnapshot`s for a project.
```json
{
  "previous_job_id": "...",
  "current_job_id": "...",
  "new_competitors": ["NewEntrant Co"],
  "changed_metrics": [{ "metric": "market_size", "previous": 20.4, "current": 77.1 }],
  "new_trends": [],
  "new_risks": [],
  "note": null
}
```
`note` is set (and the diff arrays empty) when fewer than two runs exist yet.

## Companies & Compare

### `GET /companies/{company_id}`
Company detail (name, website, industry, headquarters).

### `POST /compare`
Convenience endpoint: creates a `comparison`-type project for the given
company names and immediately starts the pipeline.
```json
{ "companies": ["Zomato", "Swiggy"] }
```
Returns a `ResearchJob` — poll `/research/{job_id}/status` as usual, then use
`/research/{job_id}/competitors` for the structured comparison.

## Health

### `GET /health`
```json
{ "status": "ok", "app": "MarketLens AI", "demo_mode": true, "database": "connected" }
```

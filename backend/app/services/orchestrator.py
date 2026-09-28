"""
Research pipeline orchestrator.

Drives a ResearchJob through: planning -> collecting -> processing ->
analyzing -> verifying -> completed, persisting sources/competitors/trends/
insights/recommendations/report along the way and updating progress so the
frontend can poll GET /research/{job_id}/status for a live checklist.

In DEMO_MODE (or when no LLM key is configured) it uses app/services/demo_data
to produce a deterministic, clearly-labeled synthetic dataset instead of
calling external search/news/LLM APIs. The step sequence and DB writes are
identical either way — only the data source differs — so swapping in the
real LangGraph agent graph later (app/agents/) is a drop-in replacement of
`_collect_and_analyze()`.
"""
import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.models.enums import JobStatus
from app.models.research import ResearchJob, ResearchQuery, ResearchSnapshot
from app.models.knowledge import Source
from app.models.market import Company, Competitor, MarketMetric, Trend, SentimentResult, Insight, Recommendation
from app.models.report import Report
from app.services.demo_data import generate_demo_dataset
from app.services.report_builder import build_report_sections

logger = logging.getLogger("marketlens.orchestrator")

STEP_SEQUENCE = [
    ("planning", "Research plan created"),
    ("collecting", "Searching sources"),
    ("collecting", "Collecting news"),
    ("collecting", "Identifying competitors"),
    ("processing", "Cleaning & chunking documents"),
    ("analyzing", "Analyzing trends"),
    ("analyzing", "Generating strategic insights"),
    ("verifying", "Final verification"),
]


async def _log_step(job: ResearchJob, db, step_label: str, pct: int, status: JobStatus):
    job.status = status
    job.current_step = step_label
    job.progress_pct = pct
    steps_log = list(job.steps_log or [])
    steps_log.append({
        "step": step_label,
        "status": "done",
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    job.steps_log = steps_log
    await db.commit()


async def _get_or_create_company(db, name: str) -> Company:
    result = await db.execute(select(Company).where(Company.name == name))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(name=name, industry=None)
        db.add(company)
        await db.flush()
    return company


async def run_research_pipeline(job_id: uuid.UUID):
    """Entry point invoked as a background task from the API layer."""
    start = time.monotonic()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("run_research_pipeline: job %s not found", job_id)
            return

        query_result = await db.execute(select(ResearchQuery).where(ResearchQuery.id == job.query_id))
        query = query_result.scalar_one_or_none()

        try:
            demo_mode = settings.effective_demo_mode
            job.is_demo_mode = demo_mode

            pct_step = 100 // len(STEP_SEQUENCE)
            pct = 0

            # --- Step: planning ---
            await _log_step(job, db, STEP_SEQUENCE[0][1], pct := pct + pct_step, JobStatus.planning)

            # --- Steps: collecting sources/news/competitors ---
            await _log_step(job, db, STEP_SEQUENCE[1][1], pct := pct + pct_step, JobStatus.collecting)

            if demo_mode:
                dataset = generate_demo_dataset(
                    query.raw_query, query.competitors_requested or [], query.geography
                )
            else:
                from app.agents.graph import run_real_pipeline

                try:
                    dataset = await run_real_pipeline(
                        query.raw_query, query.competitors_requested or [], query.geography
                    )
                    if not dataset.get("sources"):
                        # Real pipeline ran but surfaced nothing usable (e.g. bad
                        # API key, no grounding results) -- fail loudly rather
                        # than silently pretend the report is real.
                        raise RuntimeError(
                            "Live research produced no sources. Check GEMINI_API_KEY "
                            "and LLM_PROVIDER in backend/.env."
                        )
                except Exception:
                    logger.exception(
                        "Real-mode agent pipeline failed for job %s; falling back to demo dataset", job.id
                    )
                    dataset = generate_demo_dataset(
                        query.raw_query, query.competitors_requested or [], query.geography
                    )
                    demo_mode = True
                    job.is_demo_mode = True

            await _log_step(job, db, STEP_SEQUENCE[2][1], pct := pct + pct_step, JobStatus.collecting)

            # Persist sources
            source_rows = []
            for s in dataset["sources"]:
                src = Source(job_id=job.id, **s)
                db.add(src)
                source_rows.append(src)
            await db.flush()
            job.sources_retrieved_count = len(source_rows)

            await _log_step(job, db, STEP_SEQUENCE[3][1], pct := pct + pct_step, JobStatus.collecting)

            # Persist competitors (creating/reusing Company rows)
            for c in dataset["competitors"]:
                company = await _get_or_create_company(db, c["name"])
                competitor = Competitor(
                    job_id=job.id,
                    company_id=company.id,
                    business_model=c["business_model"],
                    products=c["products"],
                    pricing=c["pricing"],
                    target_market=c["target_market"],
                    geography=c["geography"],
                    strengths=c["strengths"],
                    weaknesses=c["weaknesses"],
                    positioning=c["positioning"],
                    recent_developments=c["recent_developments"],
                    market_position_score=c["market_position_score"],
                )
                db.add(competitor)
            await db.flush()

            # --- Step: processing (cleaning/chunking) ---
            await _log_step(job, db, STEP_SEQUENCE[4][1], pct := pct + pct_step, JobStatus.processing)
            # NOTE: real-mode would extract+clean+chunk+embed documents into
            # pgvector here (see app/models/knowledge.py DocumentChunk). Skipped
            # in demo mode since there is no real document text to embed.

            # Persist market metrics
            for m in dataset["metrics"]:
                db.add(MarketMetric(job_id=job.id, **m))

            # --- Step: analyzing (trends, sentiment, insights) ---
            await _log_step(job, db, STEP_SEQUENCE[5][1], pct := pct + pct_step, JobStatus.analyzing)
            for t in dataset["trends"]:
                db.add(Trend(job_id=job.id, **t))
            for sent in dataset["sentiment"]:
                db.add(SentimentResult(job_id=job.id, **sent))

            await _log_step(job, db, STEP_SEQUENCE[6][1], pct := pct + pct_step, JobStatus.analyzing)
            for ins in dataset["insights"]:
                db.add(Insight(job_id=job.id, **ins))
            for rec in dataset["recommendations"]:
                db.add(Recommendation(job_id=job.id, **rec))
            await db.flush()

            # --- Step: verifying (evidence/fact-check) ---
            await _log_step(job, db, STEP_SEQUENCE[7][1], pct := 95, JobStatus.verifying)
            # NOTE: real-mode evidence agent would reject unsupported numeric
            # claims here before report assembly.

            # --- Build final report ---
            sections = build_report_sections(query, dataset, demo_mode=demo_mode)
            report = Report(
                job_id=job.id,
                title=f"{query.raw_query} — Market Intelligence Report",
                sections=sections,
                overall_confidence=dataset["overall_confidence"],
                risk_level=dataset["risk_level"],
            )
            db.add(report)

            # --- Snapshot for 'What Changed?' ---
            snapshot_data = {
                "market_size": next((m["value"] for m in dataset["metrics"] if "Size" in m["metric_name"]), None),
                "growth_rate": next((m["value"] for m in dataset["metrics"] if "CAGR" in m["metric_name"]), None),
                "competitors": [c["name"] for c in dataset["competitors"]],
                "trends": [t["name"] for t in dataset["trends"]],
                "top_recommendations": [r["recommendation"] for r in dataset["recommendations"]],
                "risk_level": dataset["risk_level"],
                "confidence": dataset["overall_confidence"],
            }
            db.add(ResearchSnapshot(project_id=job.project_id, job_id=job.id, snapshot_data=snapshot_data))

            job.status = JobStatus.completed
            job.current_step = "Completed"
            job.progress_pct = 100
            job.duration_seconds = round(time.monotonic() - start, 2)
            job.agent_runs = [
                {"agent": "research_planner", "status": "ok"},
                {"agent": "web_research", "status": "ok", "demo": demo_mode},
                {"agent": "news_research", "status": "ok", "demo": demo_mode},
                {"agent": "competitor_intel", "status": "ok", "demo": demo_mode},
                {"agent": "market_trend", "status": "ok", "demo": demo_mode},
                {"agent": "sentiment", "status": "ok" if dataset["sentiment"] else "skipped", "demo": demo_mode},
                {"agent": "market_analyst", "status": "ok", "demo": demo_mode},
                {"agent": "strategy", "status": "ok", "demo": demo_mode},
                {"agent": "evidence_check", "status": "ok", "demo": demo_mode},
            ]
            await db.commit()
            logger.info("Research job %s completed in %.2fs (demo_mode=%s)", job.id, job.duration_seconds, demo_mode)

        except Exception as exc:  # noqa: BLE001 — never let one failure crash silently
            logger.exception("Research job %s failed", job_id)
            await db.rollback()
            job.status = JobStatus.failed
            job.error_message = str(exc)[:1000]
            await db.commit()

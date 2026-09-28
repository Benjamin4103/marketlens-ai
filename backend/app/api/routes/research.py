import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.research import ResearchProject, ResearchQuery, ResearchJob
from app.models.knowledge import Source
from app.models.market import Competitor, Company, Trend, SentimentResult, Insight, Recommendation
from app.models.report import Report
from app.models.enums import JobStatus
from app.schemas.research import (
    ResearchCreate,
    ResearchJobOut,
    ResearchProjectOut,
    ResearchProjectDetail,
    ResearchStatusOut,
)
from app.schemas.market import (
    SourceOut,
    CompetitorOut,
    TrendOut,
    SentimentOut,
    InsightOut,
    RecommendationOut,
    ReportOut,
    WhatChangedOut,
)
from app.core.config import settings

router = APIRouter(prefix="/research", tags=["research"])


async def _get_owned_job(job_id: uuid.UUID, user: User, db: AsyncSession) -> ResearchJob:
    result = await db.execute(
        select(ResearchJob)
        .join(ResearchProject, ResearchJob.project_id == ResearchProject.id)
        .where(ResearchJob.id == job_id, ResearchProject.owner_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job


@router.post("", response_model=ResearchJobOut, status_code=201)
async def create_research(
    payload: ResearchCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Creates (or reuses) a ResearchProject for this subject, then a fresh
    ResearchQuery + pending ResearchJob. Reusing the project by title enables
    the 'What Changed?' comparison across repeated research runs."""
    normalized_title = payload.query.strip()

    existing_project = await db.execute(
        select(ResearchProject).where(
            ResearchProject.owner_id == user.id,
            ResearchProject.title.ilike(normalized_title),
        )
    )
    project = existing_project.scalar_one_or_none()
    if not project:
        project = ResearchProject(owner_id=user.id, title=normalized_title, subject_type="market")
        db.add(project)
        await db.flush()

    query = ResearchQuery(
        project_id=project.id,
        raw_query=normalized_title,
        geography=payload.geography,
        time_period=payload.time_period,
        depth=payload.depth,
        competitors_requested=payload.competitors,
    )
    db.add(query)
    await db.flush()

    job = ResearchJob(
        project_id=project.id,
        query_id=query.id,
        status=JobStatus.pending,
        is_demo_mode=settings.effective_demo_mode,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("", response_model=list[ResearchProjectOut])
async def list_research(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ResearchProject)
        .where(ResearchProject.owner_id == user.id)
        .order_by(ResearchProject.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ResearchProjectDetail)
async def get_research_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ResearchProject)
        .options(selectinload(ResearchProject.queries), selectinload(ResearchProject.jobs))
        .where(ResearchProject.id == project_id, ResearchProject.owner_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Research project not found")
    return project


@router.post("/{job_id}/run", response_model=ResearchJobOut)
async def run_research(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Kicks off the async research pipeline (orchestrator + agents) for this
    job. Runs as a FastAPI background task; in production this would be
    dispatched to a Celery worker instead (see app/workflows/tasks.py)."""
    job = await _get_owned_job(job_id, user, db)
    if job.status not in (JobStatus.pending, JobStatus.failed):
        raise HTTPException(status_code=400, detail=f"Job already in status '{job.status.value}'")

    job.status = JobStatus.planning
    job.error_message = None
    await db.commit()

    from app.services.orchestrator import run_research_pipeline  # local import avoids cycles

    background_tasks.add_task(run_research_pipeline, job_id)
    await db.refresh(job)
    return job


@router.get("/{job_id}/status", response_model=ResearchStatusOut)
async def get_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = await _get_owned_job(job_id, user, db)
    return ResearchStatusOut(
        job_id=job.id,
        status=job.status,
        current_step=job.current_step,
        progress_pct=job.progress_pct,
        steps_log=job.steps_log or [],
        error_message=job.error_message,
    )


@router.get("/{job_id}/sources", response_model=list[SourceOut])
async def get_sources(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(
        select(Source).where(Source.job_id == job_id).order_by(Source.relevance_score.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}/competitors", response_model=list[CompetitorOut])
async def get_competitors(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(
        select(Competitor, Company.name)
        .join(Company, Competitor.company_id == Company.id)
        .where(Competitor.job_id == job_id)
    )
    out = []
    for competitor, company_name in result.all():
        item = CompetitorOut.model_validate(competitor)
        item.company_name = company_name
        out.append(item)
    return out


@router.get("/{job_id}/trends", response_model=list[TrendOut])
async def get_trends(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(
        select(Trend).where(Trend.job_id == job_id).order_by(Trend.confidence.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}/sentiment", response_model=list[SentimentOut])
async def get_sentiment(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(select(SentimentResult).where(SentimentResult.job_id == job_id))
    return result.scalars().all()


@router.get("/{job_id}/insights", response_model=list[InsightOut])
async def get_insights(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(select(Insight).where(Insight.job_id == job_id))
    return result.scalars().all()


@router.get("/{job_id}/recommendations", response_model=list[RecommendationOut])
async def get_recommendations(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await _get_owned_job(job_id, user, db)
    result = await db.execute(
        select(Recommendation).where(Recommendation.job_id == job_id).order_by(Recommendation.priority)
    )
    return result.scalars().all()


@router.get("/{job_id}/report", response_model=ReportOut)
async def get_report(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    job = await _get_owned_job(job_id, user, db)
    result = await db.execute(select(Report).where(Report.job_id == job.id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return report


@router.post("/{job_id}/export")
async def export_report(
    job_id: uuid.UUID,
    fmt: str = "json",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = await _get_owned_job(job_id, user, db)
    result = await db.execute(select(Report).where(Report.job_id == job.id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")

    from fastapi.responses import Response
    from app.services.export_service import export_json, export_markdown, export_pdf

    if fmt == "json":
        return Response(content=export_json(report), media_type="application/json")
    elif fmt == "markdown":
        return Response(content=export_markdown(report), media_type="text/markdown")
    elif fmt == "pdf":
        pdf_bytes = export_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report-{job_id}.pdf"},
        )
    raise HTTPException(status_code=400, detail="fmt must be one of: json, markdown, pdf")


@router.get("/{project_id}/what-changed", response_model=WhatChangedOut)
async def what_changed(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.diff_service import compute_what_changed

    result = await compute_what_changed(project_id, user.id, db)
    return result

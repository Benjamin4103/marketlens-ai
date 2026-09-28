from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.research import ResearchProject, ResearchQuery, ResearchJob
from app.models.enums import JobStatus, ResearchDepth
from app.schemas.research import CompareRequest, ResearchJobOut
from app.core.config import settings

router = APIRouter(tags=["compare"])


@router.post("/compare", response_model=ResearchJobOut, status_code=201)
async def compare_companies(
    payload: CompareRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Convenience endpoint: creates a 'comparison' research project for the
    given companies (e.g. ['Zomato', 'Swiggy']) and immediately starts the
    pipeline. Poll GET /research/{job_id}/status, then /competitors."""
    title = " vs ".join(payload.companies)

    project = ResearchProject(owner_id=user.id, title=title, subject_type="comparison")
    db.add(project)
    await db.flush()

    query = ResearchQuery(
        project_id=project.id,
        raw_query=title,
        depth=ResearchDepth.standard,
        competitors_requested=payload.companies,
    )
    db.add(query)
    await db.flush()

    job = ResearchJob(
        project_id=project.id,
        query_id=query.id,
        status=JobStatus.planning,
        is_demo_mode=settings.effective_demo_mode,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from app.services.orchestrator import run_research_pipeline

    background_tasks.add_task(run_research_pipeline, job.id)
    return job

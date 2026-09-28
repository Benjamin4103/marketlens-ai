import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research import ResearchProject, ResearchSnapshot
from app.schemas.market import WhatChangedOut


async def compute_what_changed(project_id: uuid.UUID, owner_id: uuid.UUID, db: AsyncSession) -> WhatChangedOut:
    project_result = await db.execute(
        select(ResearchProject).where(ResearchProject.id == project_id, ResearchProject.owner_id == owner_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return WhatChangedOut(
            project_id=project_id, previous_job_id=None, current_job_id=project_id,
            note="Project not found.",
        )

    snap_result = await db.execute(
        select(ResearchSnapshot)
        .where(ResearchSnapshot.project_id == project_id)
        .order_by(ResearchSnapshot.created_at.desc())
        .limit(2)
    )
    snapshots = snap_result.scalars().all()

    if len(snapshots) < 2:
        current = snapshots[0] if snapshots else None
        return WhatChangedOut(
            project_id=project_id,
            previous_job_id=None,
            current_job_id=current.job_id if current else project_id,
            note="Only one research run exists for this project — nothing to compare yet. "
                 "Run research on this same query again later to see what changed.",
        )

    current, previous = snapshots[0], snapshots[1]
    cur_data, prev_data = current.snapshot_data, previous.snapshot_data

    prev_competitors = set(prev_data.get("competitors", []))
    cur_competitors = set(cur_data.get("competitors", []))
    new_competitors = sorted(cur_competitors - prev_competitors)

    prev_trends = set(prev_data.get("trends", []))
    cur_trends = set(cur_data.get("trends", []))
    new_trends = sorted(cur_trends - prev_trends)

    changed_metrics = []
    for key in ("market_size", "growth_rate"):
        old_v, new_v = prev_data.get(key), cur_data.get(key)
        if old_v != new_v:
            changed_metrics.append({"metric": key, "previous": old_v, "current": new_v})

    new_risks = []
    if prev_data.get("risk_level") != cur_data.get("risk_level"):
        new_risks.append(
            f"Risk level changed from {prev_data.get('risk_level')} to {cur_data.get('risk_level')}"
        )

    prev_recs = set(prev_data.get("top_recommendations", []))
    cur_recs = set(cur_data.get("top_recommendations", []))
    changed_recommendations = sorted(cur_recs - prev_recs)

    new_developments = [f"New competitor identified: {c}" for c in new_competitors] + [
        f"New trend identified: {t}" for t in new_trends
    ]

    return WhatChangedOut(
        project_id=project_id,
        previous_job_id=previous.job_id,
        current_job_id=current.job_id,
        new_developments=new_developments,
        changed_metrics=changed_metrics,
        new_competitors=new_competitors,
        new_trends=new_trends,
        new_risks=new_risks,
        changed_recommendations=changed_recommendations,
    )

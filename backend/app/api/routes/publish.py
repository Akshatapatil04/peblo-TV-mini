import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.publish_run import PublishRun
from backend.app.schemas.catalog import PublishRequest, PublishResponse, PublishRunResponse, PublishRunListResponse
from backend.app.services.publisher import execute_publish, PublishError
from backend.app.services.storage import get_storage
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/admin", tags=["Publishing & Admin"])

@router.post("/catalog/publish", response_model=PublishResponse, status_code=status.HTTP_200_OK)
async def publish_catalog_endpoint(
    payload: PublishRequest = PublishRequest(),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin"]))  # Strictly enforced: only Admin can publish!
):
    """
    Publish the catalogue JSON atomically.
    - Only published shows and published episodes appear.
    - Content group variants collapse into ONE entry with available languages.
    - Season 0 trailers are isolated in show metadata.
    - Grouped deterministically by section and sorted.
    - Atomically written to storage so viewers never read a partial file.
    - Enforced RBAC: Editors cannot execute this endpoint (returns 403 Forbidden).
    """
    initiated_by = user.get("email") or user.get("name") or payload.initiated_by or "admin"
    try:
        publish_result = await execute_publish(
            db=db,
            initiated_by=initiated_by,
            force=payload.force or False
        )
        return PublishResponse(**publish_result)
    except PublishError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PublishBlocked",
                "message": str(e),
                "remediation": "Check GET /admin/validation-report to review and resolve blocking issues."
            }
        )

@router.get("/publish-runs", response_model=PublishRunListResponse)
async def list_publish_runs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """List historical publish runs with metadata, counts, and status."""
    total_res = await db.execute(select(func.count(PublishRun.id)))
    total = total_res.scalar() or 0

    query = (
        select(PublishRun)
        .order_by(PublishRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    runs = result.scalars().all()

    items = [
        PublishRunResponse(
            id=r.id,
            initiated_by=r.initiated_by,
            started_at=r.started_at,
            completed_at=r.completed_at,
            status=r.status,
            shows_count=r.shows_count,
            episodes_count=r.episodes_count,
            sections_count=r.sections_count,
            catalogue_path=r.catalogue_path,
            catalogue_version=r.catalogue_version,
            error_message=r.error_message,
            created_at=r.created_at
        )
        for r in runs
    ]
    return PublishRunListResponse(total=total, items=items)

@router.get("/publish-runs/{run_id}")
async def get_publish_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Retrieve full details of a specific publish run, including the archived catalogue snapshot."""
    result = await db.execute(select(PublishRun).where(PublishRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Publish run '{run_id}' not found.")

    return {
        "id": run.id,
        "initiated_by": run.initiated_by,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "status": run.status,
        "shows_count": run.shows_count,
        "episodes_count": run.episodes_count,
        "sections_count": run.sections_count,
        "catalogue_version": run.catalogue_version,
        "catalogue_data": run.catalogue_data,
        "error_message": run.error_message,
        "created_at": run.created_at
    }

@router.post("/publish-runs/{run_id}/rollback")
async def rollback_to_publish_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin"]))  # Admin only rollback
):
    """
    Rollback the live published catalogue to the snapshot recorded in this publish run.
    """
    result = await db.execute(select(PublishRun).where(PublishRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Publish run '{run_id}' not found.")

    if not run.catalogue_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No snapshot data available for this run.")

    storage = get_storage()
    content_bytes = json.dumps(run.catalogue_data, indent=2, ensure_ascii=False).encode("utf-8")
    await storage.atomic_write("catalog/catalogue.json", content_bytes, content_type="application/json")

    return {
        "message": f"Successfully rolled back live catalogue to version {run.catalogue_version}",
        "version": run.catalogue_version,
        "shows_count": run.shows_count,
        "episodes_count": run.episodes_count
    }

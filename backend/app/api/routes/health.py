import time
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services.storage import get_storage
from backend.app.models.publish_run import PublishRun

router = APIRouter(tags=["Health & Monitoring"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint monitoring:
    1. Database connectivity & query latency
    2. Storage service accessibility
    3. Catalogue staleness (last successful publish age)
    """
    status = "healthy"
    checks = {}

    # 1. Database Check
    db_start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        checks["database"] = {
            "status": "up",
            "latency_ms": db_latency_ms
        }
    except Exception as e:
        status = "unhealthy"
        checks["database"] = {
            "status": "down",
            "error": str(e)
        }

    # 2. Storage Check
    storage_start = time.time()
    try:
        storage = get_storage()
        storage_exists = await storage.exists("catalog/catalogue.json")
        storage_latency_ms = round((time.time() - storage_start) * 1000, 2)
        checks["storage"] = {
            "status": "up",
            "catalogue_file_present": storage_exists,
            "latency_ms": storage_latency_ms
        }
    except Exception as e:
        status = "degraded" if status == "healthy" else status
        checks["storage"] = {
            "status": "down",
            "error": str(e)
        }

    # 3. Last Publish Run Age
    try:
        last_run_res = await db.execute(
            select(PublishRun)
            .where(PublishRun.status == "success")
            .order_by(PublishRun.completed_at.desc())
            .limit(1)
        )
        last_run = last_run_res.scalar_one_or_none()
        if last_run and last_run.completed_at:
            # Ensure timezone awareness
            completed_dt = last_run.completed_at
            if completed_dt.tzinfo is None:
                completed_dt = completed_dt.replace(tzinfo=timezone.utc)
            
            age_seconds = (datetime.now(timezone.utc) - completed_dt).total_seconds()
            checks["last_publish"] = {
                "version": last_run.catalogue_version,
                "timestamp": last_run.completed_at.isoformat(),
                "age_hours": round(age_seconds / 3600.0, 2),
                "shows_count": last_run.shows_count,
                "episodes_count": last_run.episodes_count
            }
        else:
            checks["last_publish"] = {
                "status": "never_published",
                "message": "No publish run has succeeded yet."
            }
    except Exception:
        checks["last_publish"] = {"status": "unknown"}

    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Peblo TV Mini API",
        "version": "1.0.0",
        "checks": checks
    }

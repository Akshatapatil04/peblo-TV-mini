from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.validation import ValidationReportResponse
from backend.app.services.validation_report import generate_validation_report
from backend.app.api.deps import require_role

router = APIRouter(prefix="/admin", tags=["Validation"])

@router.get("/validation-report", response_model=ValidationReportResponse)
async def get_validation_report_endpoint(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """
    Get live validation report of all issues currently blocking publish,
    grouped by show and category so a content editor can act on them unaided.
    """
    report = await generate_validation_report(db)
    return ValidationReportResponse(**report)

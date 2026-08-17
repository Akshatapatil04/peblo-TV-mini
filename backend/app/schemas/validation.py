from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ValidationErrorItem(BaseModel):
    entity_type: str  # "show" or "episode"
    entity_id: str
    db_id: Optional[str] = None
    show_id: Optional[str] = None
    show_slug: Optional[str] = None
    show_title: Optional[str] = None
    title: str
    field: str
    severity: str  # "blocking", "warning", "info"
    message: str
    remediation: str

class ShowValidationSummary(BaseModel):
    show_id: str
    show_slug: str
    show_title: str
    status: str
    section: Optional[str] = None
    blocking_count: int
    warning_count: int
    errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationErrorItem] = Field(default_factory=list)

class ValidationReportResponse(BaseModel):
    can_publish: bool
    total_shows: int
    total_blocking_errors: int
    total_warnings: int
    blocking_errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationErrorItem] = Field(default_factory=list)
    grouped_by_show: Dict[str, ShowValidationSummary] = Field(default_factory=dict)

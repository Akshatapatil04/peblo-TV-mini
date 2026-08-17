from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PublishRequest(BaseModel):
    initiated_by: Optional[str] = "admin"
    force: Optional[bool] = False

class PublishResponse(BaseModel):
    run_id: str
    version: str
    status: str
    shows_count: int
    episodes_count: int
    sections_count: int
    catalogue_url: str
    published_at: str

class PublishRunResponse(BaseModel):
    id: str
    initiated_by: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    shows_count: int
    episodes_count: int
    sections_count: int
    catalogue_path: Optional[str] = None
    catalogue_version: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PublishRunListResponse(BaseModel):
    total: int
    items: List[PublishRunResponse]

class SearchShowResult(BaseModel):
    id: str
    slug: str
    title: str
    synopsis: Optional[str] = None
    section: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    artwork: Dict[str, Optional[str]] = Field(default_factory=dict)
    matching_episodes: List[Dict[str, Any]] = Field(default_factory=list)

class SearchResponse(BaseModel):
    total_matches: int
    query: Optional[str] = None
    filters: Dict[str, Optional[str]] = Field(default_factory=dict)
    results: List[SearchShowResult] = Field(default_factory=list)

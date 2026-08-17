from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.show import ArtworkInfo

class EpisodeBase(BaseModel):
    show_id: str
    season_id: Optional[str] = None
    season_number: int = Field(default=1)
    episode_number: int = Field(default=1)
    episode_title: str = Field(..., min_length=1, max_length=256)
    duration_seconds: int = Field(default=0, ge=0)
    language: str = Field(default="en")
    content_group: str = Field(..., min_length=1, max_length=128)
    status: str = Field(default="draft")
    synopsis: Optional[str] = None
    episode_id: Optional[str] = None

class EpisodeCreate(EpisodeBase):
    pass

class EpisodeUpdate(BaseModel):
    show_id: Optional[str] = None
    season_id: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    status: Optional[str] = None
    synopsis: Optional[str] = None

class EpisodeResponse(EpisodeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    artworks: List[ArtworkInfo] = Field(default_factory=list)
    show_title: Optional[str] = None
    show_slug: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EpisodeListResponse(BaseModel):
    total: int
    items: List[EpisodeResponse]

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ShowBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128)
    synopsis: Optional[str] = None
    section: Optional[str] = None  # featured, series, minisodes, songs
    categories: List[str] = Field(default_factory=list)
    status: str = Field(default="draft")  # draft, published

class ShowCreate(ShowBase):
    pass

class ShowUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    synopsis: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    status: Optional[str] = None

class ArtworkInfo(BaseModel):
    id: str
    slot_type: str
    url: str
    width: int
    height: int
    file_size_bytes: int

class EpisodeSummary(BaseModel):
    id: str
    episode_id: Optional[str] = None
    season_number: int
    episode_number: int
    episode_title: str
    duration_seconds: int
    language: str
    content_group: str
    status: str
    synopsis: Optional[str] = None
    artworks: List[ArtworkInfo] = Field(default_factory=list)

class SeasonResponse(BaseModel):
    id: str
    show_id: str
    season_number: int
    title: Optional[str] = None
    episodes: List[EpisodeSummary] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ShowResponse(ShowBase):
    id: str
    created_at: datetime
    updated_at: datetime
    artworks: List[ArtworkInfo] = Field(default_factory=list)
    seasons_count: int = 0
    episodes_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class ShowDetailResponse(ShowResponse):
    seasons: List[SeasonResponse] = Field(default_factory=list)

class ShowListResponse(BaseModel):
    total: int
    items: List[ShowResponse]

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ArtworkUploadResponse(BaseModel):
    id: str
    slot_type: str
    url: str
    width: int
    height: int
    file_size_bytes: int
    file_size_kb: float
    mime_type: str
    aspect_ratio: str
    show_id: Optional[str] = None
    episode_id: Optional[str] = None
    created_at: datetime

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    show_id = Column(String(64), ForeignKey("shows.id", ondelete="CASCADE"), nullable=True, index=True)
    episode_id = Column(String(64), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True, index=True)
    
    slot_type = Column(String(32), nullable=False, index=True)  # "poster", "banner", "thumbnail"
    file_key = Column(String(512), nullable=False)
    url = Column(String(1024), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False, default="image/jpeg")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    show = relationship("Show", back_populates="artworks")
    episode = relationship("Episode", back_populates="artworks")

    def __repr__(self):
        return f"<Artwork {self.slot_type} ({self.width}x{self.height}, {self.file_size_bytes}B)>"

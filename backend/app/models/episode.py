import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    episode_id = Column(String(64), nullable=True, index=True)  # e.g. "ep_0001" from seed data
    show_id = Column(String(64), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False, index=True)
    season_id = Column(String(64), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    season_number = Column(Integer, nullable=False, default=1, index=True)
    episode_number = Column(Integer, nullable=False, default=1, index=True)
    episode_title = Column(String(256), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False, default=0)
    language = Column(String(16), nullable=False, default="en", index=True)  # "en", "hi"
    content_group = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)  # "draft", "published"
    synopsis = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    show = relationship("Show", back_populates="episodes")
    season = relationship("Season", back_populates="episodes")
    artworks = relationship("Artwork", back_populates="episode", cascade="all, delete-orphan")

    # Table arguments & indexes
    __table_args__ = (
        Index("ix_episodes_content_group_lang", "content_group", "language"),
        Index("ix_episodes_show_season", "show_id", "season_number", "episode_number"),
    )

    def __repr__(self):
        return f"<Episode {self.episode_id or self.id} ({self.content_group}, {self.language})>"

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Season(Base):
    __tablename__ = "seasons"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    show_id = Column(String(64), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False, index=True)
    season_number = Column(Integer, nullable=False, default=1, index=True)  # Season 0 reserved for trailers
    title = Column(String(256), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan", order_by="Episode.episode_number")

    def __repr__(self):
        return f"<Season {self.season_number} for Show {self.show_id}>"

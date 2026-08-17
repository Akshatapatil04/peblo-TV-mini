import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Show(Base):
    __tablename__ = "shows"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False, index=True)
    synopsis = Column(Text, nullable=True)
    section = Column(String(64), nullable=True, index=True)  # featured, series, minisodes, songs
    categories = Column(JSON, nullable=False, default=list)   # e.g. ["adventure", "india"]
    status = Column(String(32), nullable=False, default="draft", index=True)  # draft, published
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan", order_by="Season.season_number")
    episodes = relationship("Episode", back_populates="show", cascade="all, delete-orphan")
    artworks = relationship("Artwork", back_populates="show", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Show {self.slug} ({self.status})>"

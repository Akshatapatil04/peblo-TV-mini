import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class PublishRun(Base):
    __tablename__ = "publish_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    initiated_by = Column(String(128), nullable=False, default="admin", index=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(String(32), nullable=False, default="running", index=True)  # "running", "success", "failed"
    shows_count = Column(Integer, nullable=False, default=0)
    episodes_count = Column(Integer, nullable=False, default=0)
    sections_count = Column(Integer, nullable=False, default=0)
    
    catalogue_path = Column(String(512), nullable=True)
    catalogue_version = Column(String(64), nullable=True)
    catalogue_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self):
        return f"<PublishRun {self.id} ({self.status})>"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(128), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # "create", "update", "delete", "publish", "upload"
    entity_type = Column(String(64), nullable=False, index=True)  # "show", "episode", "artwork", "catalog"
    entity_id = Column(String(128), nullable=False, index=True)
    changes = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.user_id}>"

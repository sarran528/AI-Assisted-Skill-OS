from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    phase = Column(String(64), nullable=False)
    technique_id = Column(String(64), nullable=False)
    attempt_number = Column(Integer, nullable=False, server_default=text("1"))
    status = Column(String(32), nullable=False, server_default=text("'pending'"))
    metrics_captured = Column(JSONB, nullable=False, server_default=text("'{}'"))
    protocol_steps_completed = Column(JSONB, nullable=False, server_default=text("'[]'"))
    protocol_violations = Column(JSONB, nullable=False, server_default=text("'[]'"))
    failure_reason = Column(String(128), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

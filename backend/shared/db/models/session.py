from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, text

from backend.shared.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    roadmap_id = Column(String(36), ForeignKey("roadmaps.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    phase = Column(String(64), nullable=False)
    technique_id = Column(String(64), nullable=False)
    attempt_number = Column(Integer, nullable=False, server_default=text("1"))
    status = Column(String(32), nullable=False, server_default=text("'pending'"))
    metrics_captured = Column(JSON, nullable=False, server_default=text("'{}'"))
    protocol_steps_completed = Column(JSON, nullable=False, server_default=text("'[]'"))
    protocol_violations = Column(JSON, nullable=False, server_default=text("'[]'"))
    failure_reason = Column(String(128), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

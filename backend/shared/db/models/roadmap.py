from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, text

from backend.shared.db.base import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(64), nullable=False)
    template_version = Column(Integer, nullable=False)
    profile_version = Column(Integer, nullable=False)
    parameters_id = Column(String(36), ForeignKey("learning_parameters.id"), nullable=False)
    structure = Column(JSON, nullable=False)
    fingerprint = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, server_default=text("'active'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    completed_at = Column(DateTime(timezone=True), nullable=True)

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(64), nullable=False)
    template_version = Column(Integer, nullable=False)
    profile_version = Column(Integer, nullable=False)
    parameters_id = Column(UUID(as_uuid=True), ForeignKey("learning_parameters.id"), nullable=False)
    structure = Column(JSONB, nullable=False)
    fingerprint = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, server_default=text("'active'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    completed_at = Column(DateTime(timezone=True), nullable=True)

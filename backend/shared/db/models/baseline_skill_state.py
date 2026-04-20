"""ORM model for baseline skill states."""

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class BaselineSkillState(Base):
    __tablename__ = "baseline_skill_states"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(64), nullable=False)
    profile_version = Column(Numeric(5), nullable=False, server_default=text("1"))
    exposure_score = Column(Numeric(5, 4), nullable=False)
    declarative_score = Column(Numeric(5, 4), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    perceived_level = Column(Numeric(5, 4), nullable=False)
    actual_level = Column(Numeric(5, 4), nullable=False)
    confidence_bias = Column(Numeric(6, 5), nullable=False)
    raw_responses = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

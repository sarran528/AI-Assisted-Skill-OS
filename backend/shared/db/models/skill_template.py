from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class SkillTemplate(Base):
    __tablename__ = "skill_templates"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    skill_id = Column(String(64), nullable=False)
    version = Column(Integer, nullable=False, server_default=text("1"))
    name = Column(String(128), nullable=False)
    domain = Column(String(64), nullable=False)
    complexity_score = Column(Numeric(4, 3), nullable=False)
    structure = Column(JSONB, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

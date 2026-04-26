from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String(36), nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(32), nullable=False, server_default=text("'in_progress'"))
    submissions = Column(JSONB, nullable=False, server_default=text("'{}'"))
    completed_levels = Column(JSONB, nullable=False, server_default=text("'[]'"))
    score = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


Index("assessment_session_id_idx", AssessmentSession.session_id)
Index("assessment_user_status_idx", AssessmentSession.user_id, AssessmentSession.status)

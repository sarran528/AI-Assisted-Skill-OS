from sqlalchemy import Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    session_id = Column(String(36), nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(32), nullable=False, server_default=text("'in_progress'"))
    submissions = Column(JSONB, nullable=False, server_default=text("'{}'"))
    completed_levels = Column(JSONB, nullable=False, server_default=text("'[]'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


Index("assessment_session_id_idx", AssessmentSession.session_id)
Index("assessment_user_status_idx", AssessmentSession.user_id, AssessmentSession.status)

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from backend.shared.db.base import Base


class TipLog(Base):
    __tablename__ = "tip_log"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    technique_id = Column(String(64), nullable=False)
    failure_type = Column(String(64), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    tip = Column(Text, nullable=False)
    severity = Column(String(16), nullable=False)
    target_step = Column(String(64), nullable=True)
    chunks_used = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

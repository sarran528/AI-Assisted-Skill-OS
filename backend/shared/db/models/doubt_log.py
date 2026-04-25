from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from backend.shared.db.base import Base


class DoubtLog(Base):
    __tablename__ = "doubt_log"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True)
    skill_id = Column(String(64), nullable=False)
    phase = Column(String(64), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    chunks_used = Column(Integer, nullable=False)
    confidence = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

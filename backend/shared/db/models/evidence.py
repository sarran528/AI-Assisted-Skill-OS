from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, JSON, String, Text, text

from backend.shared.db.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    checkpoint_id = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    payload = Column(JSON, nullable=False)
    artifact_url = Column(Text, nullable=True)
    artifact_key = Column(Text, nullable=True)
    mime_type = Column(String(64), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    validated = Column(Boolean, nullable=False, server_default=text("false"))
    validation_result = Column(JSON, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

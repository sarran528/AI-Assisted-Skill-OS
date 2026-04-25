from sqlalchemy import Column, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from backend.shared.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    status = Column(String(32), nullable=False)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))

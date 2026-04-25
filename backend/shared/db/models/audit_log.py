from sqlalchemy import Column, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

from backend.shared.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=True)
    entity_id = Column(String(36), nullable=True)
    ip_address = Column(INET, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default=text("'{}'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

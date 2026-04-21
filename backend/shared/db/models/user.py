from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from backend.shared.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    status = Column(String(32), nullable=False, default="active", server_default=text("'active'"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=text("now()"))


Index("users_email_idx", User.email, unique=True)
Index("users_status_idx", User.status)

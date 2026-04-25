from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import INET

from backend.shared.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(Text, nullable=False)
    jti = Column(String(36), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=text("now()"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(INET, nullable=True)  # Use INET type for PostgreSQL compatibility
    user_agent = Column(Text, nullable=True)


Index("rt_user_id_idx", RefreshToken.user_id)
Index("rt_token_hash_idx", RefreshToken.token_hash)
Index("rt_jti_idx", RefreshToken.jti)
Index("rt_expires_idx", RefreshToken.expires_at)


class RevokedAccessToken(Base):
    __tablename__ = "revoked_access_tokens"

    jti = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=text("now()"))
    expires_at = Column(DateTime(timezone=True), nullable=False)


Index("revoked_access_user_idx", RevokedAccessToken.user_id)
Index("revoked_access_expires_idx", RevokedAccessToken.expires_at)

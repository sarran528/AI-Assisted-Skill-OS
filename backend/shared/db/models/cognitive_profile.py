from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, Numeric, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from backend.shared.db.base import Base


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("uuid_generate_v4()"),
    )
    user_id = Column(
        PG_UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    version = Column(Integer, nullable=False, server_default=text("1"))
    cognitive_capacity = Column(Numeric(6, 5), nullable=False)
    attention_stability = Column(Numeric(6, 5), nullable=False)
    learning_tolerance = Column(Numeric(6, 5), nullable=False)
    motor_baseline = Column(Numeric(6, 5), nullable=False)
    stress_resilience = Column(Numeric(6, 5), nullable=False)
    time_constraint = Column(Numeric(6, 5), nullable=False)
    raw_signals = Column(JSON, nullable=False)  # Use JSON instead of JSONB for SQLite compat
    assessment_metadata = Column(JSON, nullable=False, server_default=text("'{}'"))  # Changed from JSONB
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="cp_user_version_idx"),
    )


Index("cp_user_id_idx", CognitiveProfile.user_id)
Index("cp_created_at_idx", CognitiveProfile.created_at)

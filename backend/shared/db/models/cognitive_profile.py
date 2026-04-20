from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.shared.db.base import Base


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False, server_default=text("1"))
    cognitive_capacity = Column(Numeric(6, 5), nullable=False)
    attention_stability = Column(Numeric(6, 5), nullable=False)
    learning_tolerance = Column(Numeric(6, 5), nullable=False)
    motor_baseline = Column(Numeric(6, 5), nullable=False)
    stress_resilience = Column(Numeric(6, 5), nullable=False)
    time_constraint = Column(Numeric(6, 5), nullable=False)
    raw_signals = Column(JSONB, nullable=False)
    assessment_metadata = Column(JSONB, nullable=False, server_default=text("'{}'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="cp_user_version_idx"),
    )


Index("cp_user_id_idx", CognitiveProfile.user_id)
Index("cp_created_at_idx", CognitiveProfile.created_at)

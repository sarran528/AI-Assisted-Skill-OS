from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from backend.shared.db.base import Base


class LearningParameter(Base):
    __tablename__ = "learning_parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cognitive_profiles.id"), nullable=False)
    skill_id = Column(String(64), nullable=False)

    difficulty_slope = Column(Numeric(6, 5), nullable=False)
    phase_pacing = Column(Numeric(6, 5), nullable=False)
    entry_phase_offset = Column(Numeric(6, 5), nullable=False)
    repetition_intensity = Column(Numeric(6, 5), nullable=False)

    session_duration = Column(Numeric(6, 5), nullable=False)
    micro_session_enabled = Column(SmallInteger, nullable=False, server_default=text("0"))
    fatigue_threshold = Column(Numeric(6, 5), nullable=False)
    break_frequency = Column(Numeric(6, 5), nullable=False)

    technique_density = Column(Numeric(6, 5), nullable=False)
    concurrent_technique_limit = Column(SmallInteger, nullable=False)
    abstraction_level = Column(Numeric(6, 5), nullable=False)
    instruction_granularity = Column(Numeric(6, 5), nullable=False)

    checkpoint_frequency = Column(Numeric(6, 5), nullable=False)
    checkpoint_rigidity = Column(Numeric(6, 5), nullable=False)
    error_tolerance_threshold = Column(Numeric(6, 5), nullable=False)
    retry_limit = Column(SmallInteger, nullable=False)

    drill_depth = Column(Numeric(6, 5), nullable=False)
    variation_intensity = Column(Numeric(6, 5), nullable=False)
    stress_exposure_rate = Column(Numeric(6, 5), nullable=False)
    simulation_complexity = Column(Numeric(6, 5), nullable=False)

    feedback_detail_level = Column(Numeric(6, 5), nullable=False)
    correction_delay_window = Column(Numeric(6, 5), nullable=False)
    hint_activation_threshold = Column(Numeric(6, 5), nullable=False)

    precision_requirement = Column(Numeric(6, 5), nullable=False)
    speed_requirement = Column(Numeric(6, 5), nullable=False)
    coordination_complexity = Column(Numeric(6, 5), nullable=False)

    adaptation_sensitivity = Column(Numeric(6, 5), nullable=False)
    risk_zone_trigger_level = Column(Numeric(6, 5), nullable=False)
    regression_policy_strength = Column(Numeric(6, 5), nullable=False)
    phase_transition_sensitivity = Column(Numeric(6, 5), nullable=False)

    complexity_escalation_trigger = Column(Numeric(6, 5), nullable=False)
    plateau_detection_threshold = Column(Numeric(6, 5), nullable=False)
    stability_requirement_before_advance = Column(Numeric(6, 5), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="lp_profile_skill_idx"),
    )


Index("lp_profile_id_idx", LearningParameter.profile_id)

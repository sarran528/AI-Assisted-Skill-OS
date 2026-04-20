"""create learning parameters

Revision ID: 005
Revises: 004
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_parameters",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("cognitive_profiles.id"), nullable=False),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("difficulty_slope", sa.Numeric(6, 5), nullable=False),
        sa.Column("phase_pacing", sa.Numeric(6, 5), nullable=False),
        sa.Column("entry_phase_offset", sa.Numeric(6, 5), nullable=False),
        sa.Column("repetition_intensity", sa.Numeric(6, 5), nullable=False),
        sa.Column("session_duration", sa.Numeric(6, 5), nullable=False),
        sa.Column("micro_session_enabled", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("fatigue_threshold", sa.Numeric(6, 5), nullable=False),
        sa.Column("break_frequency", sa.Numeric(6, 5), nullable=False),
        sa.Column("technique_density", sa.Numeric(6, 5), nullable=False),
        sa.Column("concurrent_technique_limit", sa.SmallInteger(), nullable=False),
        sa.Column("abstraction_level", sa.Numeric(6, 5), nullable=False),
        sa.Column("instruction_granularity", sa.Numeric(6, 5), nullable=False),
        sa.Column("checkpoint_frequency", sa.Numeric(6, 5), nullable=False),
        sa.Column("checkpoint_rigidity", sa.Numeric(6, 5), nullable=False),
        sa.Column("error_tolerance_threshold", sa.Numeric(6, 5), nullable=False),
        sa.Column("retry_limit", sa.SmallInteger(), nullable=False),
        sa.Column("drill_depth", sa.Numeric(6, 5), nullable=False),
        sa.Column("variation_intensity", sa.Numeric(6, 5), nullable=False),
        sa.Column("stress_exposure_rate", sa.Numeric(6, 5), nullable=False),
        sa.Column("simulation_complexity", sa.Numeric(6, 5), nullable=False),
        sa.Column("feedback_detail_level", sa.Numeric(6, 5), nullable=False),
        sa.Column("correction_delay_window", sa.Numeric(6, 5), nullable=False),
        sa.Column("hint_activation_threshold", sa.Numeric(6, 5), nullable=False),
        sa.Column("precision_requirement", sa.Numeric(6, 5), nullable=False),
        sa.Column("speed_requirement", sa.Numeric(6, 5), nullable=False),
        sa.Column("coordination_complexity", sa.Numeric(6, 5), nullable=False),
        sa.Column("adaptation_sensitivity", sa.Numeric(6, 5), nullable=False),
        sa.Column("risk_zone_trigger_level", sa.Numeric(6, 5), nullable=False),
        sa.Column("regression_policy_strength", sa.Numeric(6, 5), nullable=False),
        sa.Column("phase_transition_sensitivity", sa.Numeric(6, 5), nullable=False),
        sa.Column("complexity_escalation_trigger", sa.Numeric(6, 5), nullable=False),
        sa.Column("plateau_detection_threshold", sa.Numeric(6, 5), nullable=False),
        sa.Column("stability_requirement_before_advance", sa.Numeric(6, 5), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("difficulty_slope BETWEEN 0 AND 1", name="lp_difficulty_slope_check"),
        sa.CheckConstraint("phase_pacing BETWEEN 0 AND 1", name="lp_phase_pacing_check"),
        sa.CheckConstraint("entry_phase_offset BETWEEN 0 AND 1", name="lp_entry_phase_offset_check"),
        sa.CheckConstraint("repetition_intensity BETWEEN 0 AND 1", name="lp_repetition_intensity_check"),
        sa.CheckConstraint("session_duration BETWEEN 0 AND 1", name="lp_session_duration_check"),
        sa.CheckConstraint("micro_session_enabled IN (0,1)", name="lp_micro_session_check"),
        sa.CheckConstraint("fatigue_threshold BETWEEN 0 AND 1", name="lp_fatigue_threshold_check"),
        sa.CheckConstraint("break_frequency BETWEEN 0 AND 1", name="lp_break_frequency_check"),
        sa.CheckConstraint("technique_density BETWEEN 0 AND 1", name="lp_technique_density_check"),
        sa.CheckConstraint("concurrent_technique_limit BETWEEN 0 AND 5", name="lp_concurrent_technique_limit_check"),
        sa.CheckConstraint("abstraction_level BETWEEN 0 AND 1", name="lp_abstraction_level_check"),
        sa.CheckConstraint("instruction_granularity BETWEEN 0 AND 1", name="lp_instruction_granularity_check"),
        sa.CheckConstraint("checkpoint_frequency BETWEEN 0 AND 1", name="lp_checkpoint_frequency_check"),
        sa.CheckConstraint("checkpoint_rigidity BETWEEN 0 AND 1", name="lp_checkpoint_rigidity_check"),
        sa.CheckConstraint("error_tolerance_threshold BETWEEN 0 AND 1", name="lp_error_tolerance_threshold_check"),
        sa.CheckConstraint("retry_limit BETWEEN 0 AND 5", name="lp_retry_limit_check"),
        sa.CheckConstraint("drill_depth BETWEEN 0 AND 1", name="lp_drill_depth_check"),
        sa.CheckConstraint("variation_intensity BETWEEN 0 AND 1", name="lp_variation_intensity_check"),
        sa.CheckConstraint("stress_exposure_rate BETWEEN 0 AND 1", name="lp_stress_exposure_rate_check"),
        sa.CheckConstraint("simulation_complexity BETWEEN 0 AND 1", name="lp_simulation_complexity_check"),
        sa.CheckConstraint("feedback_detail_level BETWEEN 0 AND 1", name="lp_feedback_detail_level_check"),
        sa.CheckConstraint("correction_delay_window BETWEEN 0 AND 1", name="lp_correction_delay_window_check"),
        sa.CheckConstraint("hint_activation_threshold BETWEEN 0 AND 1", name="lp_hint_activation_threshold_check"),
        sa.CheckConstraint("precision_requirement BETWEEN 0 AND 1", name="lp_precision_requirement_check"),
        sa.CheckConstraint("speed_requirement BETWEEN 0 AND 1", name="lp_speed_requirement_check"),
        sa.CheckConstraint("coordination_complexity BETWEEN 0 AND 1", name="lp_coordination_complexity_check"),
        sa.CheckConstraint("adaptation_sensitivity BETWEEN 0 AND 1", name="lp_adaptation_sensitivity_check"),
        sa.CheckConstraint("risk_zone_trigger_level BETWEEN 0 AND 1", name="lp_risk_zone_trigger_level_check"),
        sa.CheckConstraint("regression_policy_strength BETWEEN 0 AND 1", name="lp_regression_policy_strength_check"),
        sa.CheckConstraint("phase_transition_sensitivity BETWEEN 0 AND 1", name="lp_phase_transition_sensitivity_check"),
        sa.CheckConstraint("complexity_escalation_trigger BETWEEN 0 AND 1", name="lp_complexity_escalation_trigger_check"),
        sa.CheckConstraint("plateau_detection_threshold BETWEEN 0 AND 1", name="lp_plateau_detection_threshold_check"),
        sa.CheckConstraint("stability_requirement_before_advance BETWEEN 0 AND 1", name="lp_stability_requirement_check"),
        sa.UniqueConstraint("profile_id", "skill_id", name="lp_profile_skill_idx"),
    )

    op.create_index("lp_profile_id_idx", "learning_parameters", ["profile_id"])


def downgrade() -> None:
    op.drop_index("lp_profile_id_idx", table_name="learning_parameters")
    op.drop_table("learning_parameters")

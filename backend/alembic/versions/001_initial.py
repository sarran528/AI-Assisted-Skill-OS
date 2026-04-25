"""Create core tables for SkillOS.

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('users_email_idx', 'users', ['email'], unique=True)
    op.create_index('users_status_idx', 'users', ['status'])

    # Create cognitive_profiles table
    op.create_table(
        'cognitive_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cognitive_capacity', sa.Numeric(5, 4), nullable=False),
        sa.Column('attention_stability', sa.Numeric(5, 4), nullable=False),
        sa.Column('learning_tolerance', sa.Numeric(5, 4), nullable=False),
        sa.Column('motor_baseline', sa.Numeric(5, 4), nullable=False),
        sa.Column('stress_resilience', sa.Numeric(5, 4), nullable=False),
        sa.Column('time_constraint', sa.Numeric(5, 4), nullable=False),
        sa.Column('raw_signals', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('cognitive_profiles_user_id_idx', 'cognitive_profiles', ['user_id'])
    op.create_index('cognitive_profiles_version_idx', 'cognitive_profiles', ['user_id', 'version'])

    # Create learning_parameters table
    op.create_table(
        'learning_parameters',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('profile_id', sa.String(36), nullable=False),
        sa.Column('skill_id', sa.String(255), nullable=False),
        # Group A - Progression Control
        sa.Column('difficulty_slope', sa.Numeric(5, 4), nullable=False),
        sa.Column('phase_pacing', sa.Numeric(5, 4), nullable=False),
        sa.Column('entry_phase_offset', sa.Numeric(5, 4), nullable=False),
        sa.Column('repetition_intensity', sa.Numeric(5, 4), nullable=False),
        # Group B - Session Structure
        sa.Column('session_duration', sa.Numeric(5, 4), nullable=False),
        sa.Column('micro_session_enabled', sa.Integer(), nullable=False),
        sa.Column('fatigue_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('break_frequency', sa.Numeric(5, 4), nullable=False),
        # Group C - Cognitive Load
        sa.Column('technique_density', sa.Numeric(5, 4), nullable=False),
        sa.Column('concurrent_technique_limit', sa.Integer(), nullable=False),
        sa.Column('abstraction_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('instruction_granularity', sa.Numeric(5, 4), nullable=False),
        # Group D - Validation
        sa.Column('checkpoint_frequency', sa.Numeric(5, 4), nullable=False),
        sa.Column('checkpoint_rigidity', sa.Numeric(5, 4), nullable=False),
        sa.Column('error_tolerance_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('retry_limit', sa.Integer(), nullable=False),
        # Group E - Practice Dynamics
        sa.Column('drill_depth', sa.Numeric(5, 4), nullable=False),
        sa.Column('variation_intensity', sa.Numeric(5, 4), nullable=False),
        sa.Column('stress_exposure_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('simulation_complexity', sa.Numeric(5, 4), nullable=False),
        # Group F - Feedback
        sa.Column('feedback_detail_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('correction_delay_window', sa.Numeric(5, 4), nullable=False),
        sa.Column('hint_activation_threshold', sa.Numeric(5, 4), nullable=False),
        # Group G - Motor
        sa.Column('precision_requirement', sa.Numeric(5, 4), nullable=False),
        sa.Column('speed_requirement', sa.Numeric(5, 4), nullable=False),
        sa.Column('coordination_complexity', sa.Numeric(5, 4), nullable=False),
        # Group H - Adaptive Meta
        sa.Column('adaptation_sensitivity', sa.Numeric(5, 4), nullable=False),
        sa.Column('risk_zone_trigger_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('regression_policy_strength', sa.Numeric(5, 4), nullable=False),
        sa.Column('phase_transition_sensitivity', sa.Numeric(5, 4), nullable=False),
        sa.Column('complexity_escalation_trigger', sa.Numeric(5, 4), nullable=False),
        sa.Column('plateau_detection_threshold', sa.Numeric(5, 4), nullable=False),
        sa.Column('stability_requirement_before_advance', sa.Numeric(5, 4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['cognitive_profiles.id'], ondelete='CASCADE'),
    )
    op.create_index('learning_parameters_profile_id_idx', 'learning_parameters', ['profile_id'])
    op.create_index('learning_parameters_skill_id_idx', 'learning_parameters', ['skill_id'])

    # Create roadmaps table
    op.create_table(
        'roadmaps',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('skill_id', sa.String(255), nullable=False),
        sa.Column('profile_version', sa.Integer(), nullable=False),
        sa.Column('parameters_id', sa.String(36), nullable=True),
        sa.Column('structure', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parameters_id'], ['learning_parameters.id'], ondelete='SET NULL'),
    )
    op.create_index('roadmaps_user_id_idx', 'roadmaps', ['user_id'])
    op.create_index('roadmaps_skill_id_idx', 'roadmaps', ['skill_id'])
    op.create_index('roadmaps_status_idx', 'roadmaps', ['status'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('roadmap_id', sa.String(36), nullable=False),
        sa.Column('phase', sa.String(255), nullable=False),
        sa.Column('technique_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('metrics_captured', sa.JSON(), nullable=True),
        sa.Column('protocol_violations', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ondelete='CASCADE'),
    )
    op.create_index('sessions_roadmap_id_idx', 'sessions', ['roadmap_id'])
    op.create_index('sessions_status_idx', 'sessions', ['status'])

    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('checkpoint_id', sa.String(255), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('artifact_url', sa.String(2048), nullable=True),
        sa.Column('validated', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('validation_result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('evidence_session_id_idx', 'evidence', ['session_id'])
    op.create_index('evidence_checkpoint_id_idx', 'evidence', ['checkpoint_id'])

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('token_hash', sa.Text(), nullable=False),
        sa.Column('jti', sa.String(36), nullable=False, unique=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('jti'),
    )
    op.create_index('rt_user_id_idx', 'refresh_tokens', ['user_id'])
    op.create_index('rt_token_hash_idx', 'refresh_tokens', ['token_hash'])
    op.create_index('rt_jti_idx', 'refresh_tokens', ['jti'])
    op.create_index('rt_expires_idx', 'refresh_tokens', ['expires_at'])

    # Create revoked_access_tokens table
    op.create_table(
        'revoked_access_tokens',
        sa.Column('jti', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('jti'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('revoked_access_user_idx', 'revoked_access_tokens', ['user_id'])
    op.create_index('revoked_access_expires_idx', 'revoked_access_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_index('revoked_access_expires_idx')
    op.drop_index('revoked_access_user_idx')
    op.drop_table('revoked_access_tokens')
    
    op.drop_index('rt_expires_idx')
    op.drop_index('rt_jti_idx')
    op.drop_index('rt_token_hash_idx')
    op.drop_index('rt_user_id_idx')
    op.drop_table('refresh_tokens')
    
    op.drop_index('evidence_checkpoint_id_idx')
    op.drop_index('evidence_session_id_idx')
    op.drop_table('evidence')
    
    op.drop_index('sessions_status_idx')
    op.drop_index('sessions_roadmap_id_idx')
    op.drop_table('sessions')
    
    op.drop_index('roadmaps_status_idx')
    op.drop_index('roadmaps_skill_id_idx')
    op.drop_index('roadmaps_user_id_idx')
    op.drop_table('roadmaps')
    
    op.drop_index('learning_parameters_skill_id_idx')
    op.drop_index('learning_parameters_profile_id_idx')
    op.drop_table('learning_parameters')
    
    op.drop_index('cognitive_profiles_version_idx')
    op.drop_index('cognitive_profiles_user_id_idx')
    op.drop_table('cognitive_profiles')
    
    op.drop_index('users_status_idx')
    op.drop_index('users_email_idx')
    op.drop_table('users')

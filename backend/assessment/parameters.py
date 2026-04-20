"""Learning parameters derivation - generates all 32 skill-specific parameters.

The 32 parameters are derived from the 6-dimension ProfileVector using
deterministic formulas. They are organized in 8 groups (A-H) for clarity.
All outputs are clamped to valid ranges: floats [0,1], integers as specified.

Critical operations:
- floor() for concurrent_technique_limit (0-5)
- round() for retry_limit (0-5)
- Boolean check for micro_session_enabled (0 or 1)
"""

from math import floor

from backend.assessment.normalization import _clamp
from backend.assessment.schemas import LearningParameters, ProfileVector


def _compute_group_a(profile: ProfileVector) -> dict:
    """Group A: Difficulty and entry parameters (4 params)."""
    return {
        "difficulty_slope": _clamp(
            0.6 * profile.cognitive_capacity + 0.4 * profile.learning_tolerance
        ),
        "phase_pacing": _clamp(
            (profile.attention_stability + profile.time_constraint) / 2.0
        ),
        "entry_phase_offset": _clamp(
            0.5 * profile.cognitive_capacity + 0.5 * profile.learning_tolerance
        ),
        "repetition_intensity": _clamp(
            1.0 - profile.learning_tolerance
        ),
    }


def _compute_group_b(profile: ProfileVector) -> dict:
    """Group B: Session structure parameters (4 params)."""
    attn_stab = profile.attention_stability
    
    return {
        "session_duration": _clamp(
            profile.time_constraint * attn_stab
        ),
        "micro_session_enabled": 1 if attn_stab < 0.4 else 0,
        "fatigue_threshold": _clamp(
            attn_stab * profile.stress_resilience
        ),
        "break_frequency": _clamp(
            1.0 - attn_stab
        ),
    }


def _compute_group_c(profile: ProfileVector) -> dict:
    """Group C: Technique management parameters (4 params)."""
    cog_cap = profile.cognitive_capacity
    technique_density = _clamp(cog_cap * profile.attention_stability)
    
    return {
        "technique_density": technique_density,
        "concurrent_technique_limit": int(floor(technique_density * 5)),
        "abstraction_level": _clamp(cog_cap),
        "instruction_granularity": _clamp(1.0 - cog_cap),
    }


def _compute_group_d(profile: ProfileVector) -> dict:
    """Group D: Error handling and checkpoints (4 params)."""
    learn_tol = profile.learning_tolerance
    retry_limit_raw = learn_tol * 5.0
    
    return {
        "checkpoint_frequency": _clamp(
            1.0 - profile.attention_stability
        ),
        "checkpoint_rigidity": _clamp(
            profile.cognitive_capacity * profile.stress_resilience
        ),
        "error_tolerance_threshold": _clamp(learn_tol),
        "retry_limit": int(round(retry_limit_raw)),
    }


def _compute_group_e(profile: ProfileVector) -> dict:
    """Group E: Drill and variation parameters (4 params)."""
    cog_cap = profile.cognitive_capacity
    motor_base = profile.motor_baseline
    stress_res = profile.stress_resilience
    
    return {
        "drill_depth": _clamp(
            1.0 - motor_base
        ),
        "variation_intensity": _clamp(
            cog_cap * stress_res
        ),
        "stress_exposure_rate": _clamp(
            stress_res * cog_cap
        ),
        "simulation_complexity": _clamp(
            (cog_cap + motor_base) / 2.0
        ),
    }


def _compute_group_f(profile: ProfileVector) -> dict:
    """Group F: Feedback parameters (3 params)."""
    return {
        "feedback_detail_level": _clamp(
            1.0 - profile.cognitive_capacity
        ),
        "correction_delay_window": _clamp(
            profile.stress_resilience
        ),
        "hint_activation_threshold": _clamp(
            1.0 - profile.learning_tolerance
        ),
    }


def _compute_group_g(profile: ProfileVector) -> dict:
    """Group G: Motor/precision parameters (3 params)."""
    motor_base = profile.motor_baseline
    
    return {
        "precision_requirement": _clamp(motor_base),
        "speed_requirement": _clamp(
            motor_base * profile.cognitive_capacity
        ),
        "coordination_complexity": _clamp(motor_base),
    }


def _compute_group_h(profile: ProfileVector) -> dict:
    """Group H: Adaptation and transitions parameters (7 params)."""
    cog_cap = profile.cognitive_capacity
    learn_tol = profile.learning_tolerance
    stress_res = profile.stress_resilience
    
    return {
        "adaptation_sensitivity": _clamp(
            1.0 - stress_res
        ),
        "risk_zone_trigger_level": _clamp(
            1.0 - ((learn_tol + stress_res) / 2.0)
        ),
        "regression_policy_strength": _clamp(
            1.0 - learn_tol
        ),
        "phase_transition_sensitivity": _clamp(
            cog_cap * stress_res
        ),
        "complexity_escalation_trigger": _clamp(cog_cap),
        "plateau_detection_threshold": _clamp(
            1.0 - cog_cap
        ),
        "stability_requirement_before_advance": _clamp(
            profile.attention_stability
        ),
    }


def compute_learning_parameters(
    profile: ProfileVector,
    skill_id: str,
) -> LearningParameters:
    """Compute all 32 learning parameters from a cognitive profile.
    
    The computation is fully deterministic: the same ProfileVector
    always produces identical parameters. Parameters are grouped by
    function (A-H) for code clarity.
    
    Args:
        profile: The 6-dimension ProfileVector (all 0-1).
        skill_id: Skill template slug (for future skill-specific overrides).
        
    Returns:
        LearningParameters with all 32 derived parameters.
    """
    group_a = _compute_group_a(profile)
    group_b = _compute_group_b(profile)
    group_c = _compute_group_c(profile)
    group_d = _compute_group_d(profile)
    group_e = _compute_group_e(profile)
    group_f = _compute_group_f(profile)
    group_g = _compute_group_g(profile)
    group_h = _compute_group_h(profile)
    
    return LearningParameters(
        # Group A
        **group_a,
        # Group B
        **group_b,
        # Group C
        **group_c,
        # Group D
        **group_d,
        # Group E
        **group_e,
        # Group F
        **group_f,
        # Group G
        **group_g,
        # Group H
        **group_h,
    )

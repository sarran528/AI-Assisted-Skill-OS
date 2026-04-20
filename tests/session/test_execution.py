from backend.assessment.schemas import LearningParameters
from backend.session.execution import (
    SessionMetrics,
    compute_session_result,
    validate_protocol_adherence,
)


def _params() -> LearningParameters:
    return LearningParameters(
        difficulty_slope=0.5,
        phase_pacing=0.5,
        entry_phase_offset=0.5,
        repetition_intensity=0.5,
        session_duration=0.5,
        micro_session_enabled=0,
        fatigue_threshold=0.5,
        break_frequency=0.5,
        technique_density=0.5,
        concurrent_technique_limit=2,
        abstraction_level=0.5,
        instruction_granularity=0.5,
        checkpoint_frequency=0.5,
        checkpoint_rigidity=0.5,
        error_tolerance_threshold=0.8,
        retry_limit=2,
        drill_depth=0.5,
        variation_intensity=0.5,
        stress_exposure_rate=0.5,
        simulation_complexity=0.5,
        feedback_detail_level=0.5,
        correction_delay_window=0.5,
        hint_activation_threshold=0.5,
        precision_requirement=0.5,
        speed_requirement=0.5,
        coordination_complexity=0.5,
        adaptation_sensitivity=0.5,
        risk_zone_trigger_level=0.5,
        regression_policy_strength=0.5,
        phase_transition_sensitivity=0.5,
        complexity_escalation_trigger=0.5,
        plateau_detection_threshold=0.5,
        stability_requirement_before_advance=0.5,
    )


def test_protocol_adherence_cases():
    assert validate_protocol_adherence(["s1", "s2", "s3"], ["s1", "s2", "s3"]) == (True, [])
    assert validate_protocol_adherence(["s1", "s3"], ["s1", "s2", "s3"]) == (False, ["s2"])
    assert validate_protocol_adherence(["s2", "s1", "s3"], ["s1", "s2", "s3"]) == (False, ["s1"])
    assert validate_protocol_adherence(["s1", "s2"], ["s1", "s2", "s3"]) == (False, ["s3"])


def test_session_result_conditions():
    params = _params()
    metrics = SessionMetrics(
        accuracy_pct=0.9,
        time_taken_seconds=20.0,
        error_count=0,
        step_completion_rate=1.0,
        retry_count=0,
        raw_signals={},
    )

    violation = compute_session_result(metrics, params, adherence_ok=False)
    assert violation.passed is False
    assert violation.failure_reason == "protocol_violation"

    low_accuracy = SessionMetrics(
        accuracy_pct=0.7,
        time_taken_seconds=20.0,
        error_count=1,
        step_completion_rate=1.0,
        retry_count=0,
        raw_signals={},
    )
    threshold_fail = compute_session_result(low_accuracy, params, adherence_ok=True)
    assert threshold_fail.passed is False
    assert threshold_fail.failure_reason == "metric_threshold"

    success = compute_session_result(metrics, params, adherence_ok=True)
    assert success.passed is True
    assert success.failure_reason is None

from unittest.mock import AsyncMock, patch

import pytest

from backend.validation.schemas import ValidationResult
from backend.validation.validators import (
    validate_artifact,
    validate_behavioral_log,
    validate_numeric,
)


def test_validate_numeric_accuracy_and_error_count():
    pass_result = validate_numeric({"accuracy_pct": 0.91}, 0.85, "achieve accuracy")
    fail_result = validate_numeric({"accuracy_pct": 0.70}, 0.85, "achieve accuracy")
    error_result = validate_numeric({"error_count": 2}, 3.0, "max error count")

    assert pass_result.passed is True
    assert fail_result.passed is False
    assert error_result.passed is True


def test_validate_behavioral_log_cases():
    ok = validate_behavioral_log(
        {"steps_completed": ["s1", "s2"], "retry_count": 1, "retry_limit": 2},
        ["s1", "s2"],
    )
    missing = validate_behavioral_log(
        {"steps_completed": ["s1"], "retry_count": 1, "retry_limit": 2},
        ["s1", "s2"],
    )
    retry_fail = validate_behavioral_log(
        {"steps_completed": ["s1", "s2"], "retry_count": 3, "retry_limit": 2},
        ["s1", "s2"],
    )

    assert ok.passed is True
    assert missing.passed is False
    assert retry_fail.passed is False


@pytest.mark.asyncio
async def test_validate_artifact_success_and_fallback():
    with patch(
        "backend.validation.validators.llm_call",
        new=AsyncMock(return_value=type("R", (), {"passed": True, "confidence": 0.9, "reason": "ok"})()),
    ):
        result = await validate_artifact({}, "https://artifact", "desc", "criteria")
        assert result.passed is True

    with patch(
        "backend.validation.validators.llm_call",
        new=AsyncMock(return_value=type("R", (), {"passed": False, "confidence": 0.0, "reason": "validation_unavailable"})()),
    ):
        result = await validate_artifact({}, "https://artifact", "desc", "criteria")
        assert result.passed is False
        assert result.reason == "validation_unavailable"


@pytest.mark.asyncio
async def test_no_evidence_and_all_must_pass():
    from backend.assessment.schemas import LearningParameters
    from backend.validation.engine import validate_checkpoint

    params = LearningParameters(
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
        checkpoint_rigidity=0.85,
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

    db = AsyncMock()
    with patch("backend.validation.engine.EvidenceRepository.get_by_checkpoint", new=AsyncMock(return_value=[])):
        none_result = await validate_checkpoint(db, "sid", "cp", params, {"evidence_type": "numeric"})
        assert none_result.passed is False
        assert none_result.reason == "no_evidence_submitted"

    e1 = type("E", (), {"id": "1", "type": "numeric", "payload": {"accuracy_pct": 0.9}, "artifact_url": None})()
    e2 = type("E", (), {"id": "2", "type": "numeric", "payload": {"accuracy_pct": 0.5}, "artifact_url": None})()
    with patch("backend.validation.engine.EvidenceRepository.get_by_checkpoint", new=AsyncMock(return_value=[e1, e2])), patch(
        "backend.validation.engine.EvidenceRepository.mark_validated", new=AsyncMock()
    ):
        fail_result = await validate_checkpoint(
            db,
            "sid",
            "cp",
            params,
            {"evidence_type": "numeric", "threshold": 0.8, "pass_criteria": "accuracy"},
        )
        assert fail_result.passed is False

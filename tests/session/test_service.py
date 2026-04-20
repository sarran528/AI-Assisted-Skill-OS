from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from backend.assessment.schemas import LearningParameters
from backend.session.service import complete_session, start_session, submit_metrics
from backend.shared.errors import BusinessError


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


@pytest.mark.asyncio
async def test_start_session_blocks_second_active_session():
    db = AsyncMock()

    with patch(
        "backend.session.service.SessionRepository.get_active_session",
        new=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
    ):
        with pytest.raises(BusinessError, match="active session"):
            await start_session(db, uuid4(), uuid4(), "phase_1", "blend")


@pytest.mark.asyncio
async def test_submit_metrics_delegates_to_repository():
    db = AsyncMock()
    session_id = uuid4()

    with patch("backend.session.service.SessionRepository.append_metrics", new=AsyncMock()) as append_mock:
        await submit_metrics(db, session_id, {"accuracy_pct": 0.9})

    append_mock.assert_awaited_once_with(db, session_id, {"accuracy_pct": 0.9})


@pytest.mark.asyncio
async def test_complete_session_marks_completed_when_all_steps_pass():
    db = AsyncMock()
    session_id = uuid4()
    user_id = uuid4()
    roadmap_id = uuid4()

    fake_session = SimpleNamespace(
        id=session_id,
        roadmap_id=roadmap_id,
        user_id=user_id,
        phase="phase_1",
        technique_id="blend",
        metrics_captured={"records": [{"accuracy_pct": 0.95, "retry_count": 0}]},
    )
    fake_roadmap = SimpleNamespace(
        id=roadmap_id,
        skill_id="drawing",
        structure={
            "skill_id": "drawing",
            "user_id": str(user_id),
            "profile_version": 1,
            "template_version": 1,
            "parameters_id": str(uuid4()),
            "phases": {
                "phase_1": {
                    "phase_slug": "phase_1",
                    "competencies": [],
                    "techniques": [
                        {
                            "technique_id": "blend",
                            "name": "blend",
                            "session_count": 2,
                            "protocol_steps": ["s1", "s2", "s3"],
                        }
                    ],
                    "checkpoints": [],
                    "estimated_weeks": 2,
                    "status": "active",
                }
            },
            "total_estimated_weeks": 2,
            "fingerprint": "abc",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    db.get = AsyncMock(return_value=fake_roadmap)

    with patch("backend.session.service.SessionRepository.get_by_id", new=AsyncMock(return_value=fake_session)), patch(
        "backend.session.service._fetch_learning_params_for_session",
        new=AsyncMock(return_value=_params()),
    ), patch("backend.session.service.SessionRepository.set_completed_steps", new=AsyncMock()) as set_steps_mock, patch(
        "backend.session.service.transition_session", new=AsyncMock()
    ) as transition_mock, patch("backend.session.service.log_audit_event", new=AsyncMock()):
        result = await complete_session(db, None, session_id, ["s1", "s2", "s3"])

    assert result.passed is True
    transition_mock.assert_awaited_once_with(db, session_id, "completed")
    set_steps_mock.assert_awaited_once_with(db, session_id, ["s1", "s2", "s3"])


@pytest.mark.asyncio
async def test_complete_session_marks_failed_on_protocol_violation():
    db = AsyncMock()
    session_id = uuid4()
    user_id = uuid4()
    roadmap_id = uuid4()

    fake_session = SimpleNamespace(
        id=session_id,
        roadmap_id=roadmap_id,
        user_id=user_id,
        phase="phase_1",
        technique_id="blend",
        metrics_captured={"records": [{"accuracy_pct": 0.95, "retry_count": 0}]},
    )
    fake_roadmap = SimpleNamespace(
        id=roadmap_id,
        skill_id="drawing",
        structure={
            "skill_id": "drawing",
            "user_id": str(user_id),
            "profile_version": 1,
            "template_version": 1,
            "parameters_id": str(uuid4()),
            "phases": {
                "phase_1": {
                    "phase_slug": "phase_1",
                    "competencies": [],
                    "techniques": [
                        {
                            "technique_id": "blend",
                            "name": "blend",
                            "session_count": 2,
                            "protocol_steps": ["s1", "s2", "s3"],
                        }
                    ],
                    "checkpoints": [],
                    "estimated_weeks": 2,
                    "status": "active",
                }
            },
            "total_estimated_weeks": 2,
            "fingerprint": "abc",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    db.get = AsyncMock(return_value=fake_roadmap)

    with patch("backend.session.service.SessionRepository.get_by_id", new=AsyncMock(return_value=fake_session)), patch(
        "backend.session.service._fetch_learning_params_for_session",
        new=AsyncMock(return_value=_params()),
    ), patch("backend.session.service.SessionRepository.set_completed_steps", new=AsyncMock()), patch(
        "backend.session.service.transition_session", new=AsyncMock()
    ) as transition_mock, patch("backend.session.service.log_audit_event", new=AsyncMock()):
        result = await complete_session(db, None, session_id, ["s1", "s3"])

    assert result.passed is False
    assert result.failure_reason == "protocol_violation"
    transition_mock.assert_awaited_once_with(db, session_id, "failed", "protocol_violation")


@pytest.mark.asyncio
async def test_complete_session_rejects_unknown_technique():
    db = AsyncMock()
    session_id = uuid4()
    user_id = uuid4()
    roadmap_id = uuid4()

    fake_session = SimpleNamespace(
        id=session_id,
        roadmap_id=roadmap_id,
        user_id=user_id,
        phase="phase_1",
        technique_id="unknown",
        metrics_captured={"records": []},
    )
    fake_roadmap = SimpleNamespace(
        id=roadmap_id,
        skill_id="drawing",
        structure={
            "skill_id": "drawing",
            "user_id": str(user_id),
            "profile_version": 1,
            "template_version": 1,
            "parameters_id": str(uuid4()),
            "phases": {
                "phase_1": {
                    "phase_slug": "phase_1",
                    "competencies": [],
                    "techniques": [
                        {
                            "technique_id": "blend",
                            "name": "blend",
                            "session_count": 2,
                            "protocol_steps": ["s1", "s2", "s3"],
                        }
                    ],
                    "checkpoints": [],
                    "estimated_weeks": 2,
                    "status": "active",
                }
            },
            "total_estimated_weeks": 2,
            "fingerprint": "abc",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    db.get = AsyncMock(return_value=fake_roadmap)

    with patch("backend.session.service.SessionRepository.get_by_id", new=AsyncMock(return_value=fake_session)):
        with pytest.raises(BusinessError, match="Technique not found"):
            await complete_session(db, None, session_id, ["s1", "s2", "s3"])

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from backend.auth.dependencies import get_current_user
from backend.main import app
from backend.shared.db.session import get_db_session


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDbSession:
    def __init__(self):
        self._profile = SimpleNamespace(
            cognitive_capacity=0.8,
            attention_stability=0.75,
            learning_tolerance=0.7,
            motor_baseline=0.65,
            stress_resilience=0.72,
            time_constraint=0.6,
        )

    async def execute(self, *_args, **_kwargs):
        return _FakeResult(self._profile)

    async def commit(self):
        return None


class _FakeGroundingService:
    def __init__(self, _db_session):
        self._db_session = _db_session

    async def submit_grounding(self, **kwargs):
        return {
            "id": uuid4(),
            "skill_id": kwargs["skill_id"],
            "user_id": kwargs["user_id"],
            "exposure_score": 0.7,
            "declarative_score": 0.66,
            "confidence_score": 0.8,
            "perceived_level": 0.72,
            "actual_level": 0.8,
            "confidence_bias": -0.08,
            "created_at": datetime.now(timezone.utc),
        }


@pytest.fixture
def e2e_client(monkeypatch: pytest.MonkeyPatch):
    fake_user = SimpleNamespace(id=uuid4(), status="active")

    async def _override_user():
        return {"user": fake_user, "jti": "test-jti", "exp": 9999999999}

    async def _override_db():
        yield _FakeDbSession()

    async def _fake_log_audit_event(*_args, **_kwargs):
        return None

    async def _fake_validate_checkpoint(**_kwargs):
        return True, "validated"

    monkeypatch.setattr("backend.roadmap.router.generate_roadmap_task.delay", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("backend.roadmap.router.log_audit_event", _fake_log_audit_event)
    monkeypatch.setattr("backend.validation.router.validate_checkpoint", _fake_validate_checkpoint)
    monkeypatch.setattr("backend.skill.router.GroundingService", _FakeGroundingService)

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db_session] = _override_db

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.e2e
def test_complete_execution_loop(e2e_client: TestClient):
    headers = {"Authorization": "Bearer test-token"}

    start_assessment = e2e_client.post("/api/v1/assessment/start", headers=headers)
    assert start_assessment.status_code == 201
    assessment_session_id = start_assessment.json()["session_id"]

    complete_assessment = e2e_client.post(
        "/api/v1/assessment/complete",
        headers=headers,
        json={"session_id": assessment_session_id, "completed_levels": [1, 2, 3, 4, 5, 6]},
    )
    assert complete_assessment.status_code == 201

    baseline = e2e_client.post(
        "/api/v1/skills/baseline",
        headers=headers,
        json={
            "skill_id": "drawing",
            "recognition": {"items": [True, False, True]},
            "familiarity": {"answers": [0, 1, 2]},
            "confidence": {"level": 4},
        },
    )
    assert baseline.status_code == 200

    roadmap = e2e_client.post("/api/v1/roadmaps/generate", headers=headers)
    assert roadmap.status_code == 200
    assert roadmap.json()["status"] == "queued"

    start_session = e2e_client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={"skill_id": "drawing", "phase": "phase-1", "technique_id": "technique-1"},
    )
    assert start_session.status_code == 201
    session_id = start_session.json()["session_id"]

    metrics = e2e_client.post(
        "/api/v1/sessions/metrics",
        headers=headers,
        json={
            "session_id": session_id,
            "accuracy": 0.92,
            "elapsed_seconds": 240,
            "errors": 1,
            "retry": 0,
            "session_status": "active",
        },
    )
    assert metrics.status_code == 202

    complete_session = e2e_client.post(
        "/api/v1/sessions/complete",
        headers=headers,
        json={
            "session_id": session_id,
            "completed_steps": ["1", "2", "3", "4"],
            "required_steps": ["1", "2", "3", "4"],
            "current_status": "active",
            "metrics": {"accuracy": 0.91, "elapsed_seconds": 360, "errors": 1, "retry": 0},
        },
    )
    assert complete_session.status_code == 200
    assert complete_session.json()["passed"] is True

    checkpoint = e2e_client.post(
        "/api/v1/validation/checkpoint/validate",
        headers=headers,
        json={
            "session_id": session_id,
            "checkpoint_id": "checkpoint-1",
            "checkpoint_status": "attempted",
            "evidence_type": "behavioral_log",
            "steps_completed": ["1", "2", "3", "4"],
            "required_steps": ["1", "2", "3", "4"],
            "retry_count": 0,
            "max_retries": 2,
        },
    )
    assert checkpoint.status_code == 200
    assert checkpoint.json()["passed"] is True

    UUID(session_id)

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.auth.dependencies import get_current_user
from backend.main import app
from backend.shared.db.session import get_db_session


def _build_profile(user_id: UUID) -> SimpleNamespace:
    profile_vector = SimpleNamespace(
        cognitive_capacity=0.7,
        attention_stability=0.8,
        learning_tolerance=0.75,
        motor_baseline=0.65,
        stress_resilience=0.72,
        time_constraint=0.6,
    )
    return SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        version=1,
        profile_vector=profile_vector,
    )


def test_phase_c_end_to_end_smoke_flow() -> None:
    user_id = uuid4()
    roadmap_id = uuid4()
    session_id = uuid4()
    evidence_id = uuid4()

    phase_advanced = {"value": False}

    async def override_current_user() -> dict:
        return {"user": SimpleNamespace(id=user_id), "jti": "jti", "exp": 0}

    async def override_db_session():
        yield AsyncMock()

    def fake_generate_delay(_user_id: str, _skill_id: str) -> SimpleNamespace:
        return SimpleNamespace(id="roadmap-job-1")

    def fake_validate_delay(_session_id: str, _checkpoint_id: str) -> SimpleNamespace:
        phase_advanced["value"] = True
        return SimpleNamespace(id="validation-job-1")

    def fake_async_result(job_id: str) -> SimpleNamespace:
        if job_id == "roadmap-job-1":
            return SimpleNamespace(
                state="SUCCESS",
                result={"roadmap_id": str(roadmap_id), "status": "completed"},
            )
        if job_id == "validation-job-1":
            return SimpleNamespace(
                state="SUCCESS",
                result={"passed": True, "reason": "ok", "status": "completed"},
            )
        return SimpleNamespace(state="PENDING", result=None)

    async def fake_get_active(_db_session, _user_id: UUID, _skill_id: str) -> SimpleNamespace:
        phases = {
            "phase_1": {"status": "completed" if phase_advanced["value"] else "active"},
            "phase_2": {"status": "active" if phase_advanced["value"] else "locked"},
        }
        return SimpleNamespace(
            id=roadmap_id,
            skill_id="drawing",
            user_id=user_id,
            structure={"phases": phases},
            fingerprint="abc123",
            status="active",
        )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        with (
            patch(
                "backend.auth.router.register_user",
                new=AsyncMock(
                    return_value={
                        "user_id": str(user_id),
                        "email": "smoke@example.com",
                        "access_token": "token",
                        "token_type": "bearer",
                    }
                ),
            ),
            patch(
                "backend.assessment.router.process_assessment",
                new=AsyncMock(return_value=_build_profile(user_id)),
            ),
            patch("backend.roadmap.router.generate_roadmap_task.delay", side_effect=fake_generate_delay),
            patch("backend.validation.router.validate_checkpoint_task.delay", side_effect=fake_validate_delay),
            patch("backend.shared.jobs.router.celery_app.AsyncResult", side_effect=fake_async_result),
            patch("backend.roadmap.router.RoadmapRepository.get_active", side_effect=fake_get_active),
            patch("backend.session.router.start_session", new=AsyncMock(return_value=session_id)),
            patch("backend.session.router.submit_metrics", new=AsyncMock(return_value=None)),
            patch(
                "backend.session.router.complete_session",
                new=AsyncMock(
                    return_value=SimpleNamespace(
                        passed=True,
                        failure_reason=None,
                        metric_details={"accuracy_pct": 0.93},
                    )
                ),
            ),
            patch(
                "backend.evidence.router.upload_evidence",
                new=AsyncMock(
                    return_value=SimpleNamespace(
                        id=evidence_id,
                        checkpoint_id="phase_1_cp_1",
                        artifact_url="https://example.com/artifact",
                        mime_type="image/png",
                        file_size_bytes=9,
                        validated=False,
                    )
                ),
            ),
        ):
            client = TestClient(app)

            register_response = client.post(
                "/api/v1/auth/register",
                json={"email": "smoke@example.com", "password": "Passw0rd!"},
            )
            assert register_response.status_code == 201
            assert register_response.json()["userId"] == str(user_id)

            assessment_response = client.post(
                "/api/v1/assessment/assessment/submit",
                json={
                    "level": 1,
                    "metrics": {
                        "accuracy": 90,
                        "expected_time": 5,
                        "latency_stability": 10,
                        "decay_inverse": 0.8,
                        "dropout": 1,
                        "retry": 1,
                        "recovery": 0.9,
                    },
                    "time_constraint": {
                        "available_hours_per_week": 8,
                        "preferred_session_length": 45,
                    },
                },
            )
            assert assessment_response.status_code == 201

            generate_response = client.post(
                "/api/v1/roadmaps/generate",
                json={"skill_id": "drawing"},
            )
            assert generate_response.status_code == 202
            assert generate_response.json()["job_id"] == "roadmap-job-1"

            roadmap_job_response = client.get("/api/v1/jobs/roadmap-job-1")
            assert roadmap_job_response.status_code == 200
            assert roadmap_job_response.json()["status"] == "SUCCESS"
            assert roadmap_job_response.json()["result"]["roadmap_id"] == str(roadmap_id)

            session_start_response = client.post(
                "/api/v1/sessions/start",
                json={
                    "roadmap_id": str(roadmap_id),
                    "phase": "phase_1",
                    "technique_id": "blend",
                },
            )
            assert session_start_response.status_code == 200
            assert session_start_response.json()["session_id"] == str(session_id)

            metrics_response = client.post(
                "/api/v1/sessions/metrics",
                json={
                    "session_id": str(session_id),
                    "metrics": {"accuracy_pct": 0.93, "retry_count": 0},
                },
            )
            assert metrics_response.status_code == 200
            assert metrics_response.json() == {"acknowledged": True}

            complete_response = client.post(
                "/api/v1/sessions/complete",
                json={
                    "session_id": str(session_id),
                    "completed_steps": ["s1", "s2", "s3"],
                },
            )
            assert complete_response.status_code == 200
            assert complete_response.json()["passed"] is True

            evidence_upload_response = client.post(
                "/api/v1/evidence/upload",
                data={
                    "session_id": str(session_id),
                    "checkpoint_id": "phase_1_cp_1",
                    "evidence_type": "artifact",
                },
                files={"file": ("sample.png", b"png-bytes", "image/png")},
            )
            assert evidence_upload_response.status_code == 200
            assert evidence_upload_response.json()["validated"] is False

            validate_response = client.post(
                "/api/v1/validation/checkpoint/validate",
                json={"session_id": str(session_id), "checkpoint_id": "phase_1_cp_1"},
            )
            assert validate_response.status_code == 200
            assert validate_response.json()["job_id"] == "validation-job-1"

            validation_job_response = client.get("/api/v1/jobs/validation-job-1")
            assert validation_job_response.status_code == 200
            assert validation_job_response.json()["status"] == "SUCCESS"
            assert validation_job_response.json()["result"]["passed"] is True

            active_roadmap_response = client.get(f"/api/v1/roadmaps/{user_id}?skill_id=drawing")
            assert active_roadmap_response.status_code == 200
            active_roadmap = active_roadmap_response.json()["structure"]["phases"]
            assert active_roadmap["phase_1"]["status"] == "completed"
            assert active_roadmap["phase_2"]["status"] == "active"
    finally:
        app.dependency_overrides.clear()

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from backend.shared.errors import BusinessError, SystemError
from backend.shared.queue.tasks import generate_roadmap_task


def _fake_retry(exc):
    raise RuntimeError(f"retry_called:{exc}")


def test_generate_roadmap_task_business_error_no_retry():
    with patch.object(generate_roadmap_task, "retry", _fake_retry), patch(
        "backend.shared.queue.tasks.SyncSessionLocal"
    ) as session_local, patch(
        "backend.shared.queue.tasks.sync_create_roadmap",
        side_effect=BusinessError("research_required", "Skill research is required before roadmap generation"),
    ):
        session_local.return_value.__enter__.return_value = MagicMock()
        result = generate_roadmap_task("00000000-0000-0000-0000-000000000001", "drawing")

    assert result["status"] == "failed"
    assert result["error"] == "research_required"


def test_generate_roadmap_task_system_error_no_retry():
    with patch.object(generate_roadmap_task, "retry", _fake_retry), patch(
        "backend.shared.queue.tasks.SyncSessionLocal"
    ) as session_local, patch(
        "backend.shared.queue.tasks.sync_create_roadmap",
        side_effect=SystemError("db_unavailable"),
    ):
        session_local.return_value.__enter__.return_value = MagicMock()
        result = generate_roadmap_task("00000000-0000-0000-0000-000000000001", "drawing")

    assert result["status"] == "failed"
    assert result["error"] == "system_error"


def test_generate_roadmap_task_transient_retry_called():
    retry_called = {"called": False}

    def retry(exc):
        retry_called["called"] = True
        raise RuntimeError(f"retry:{exc}")

    with patch.object(generate_roadmap_task, "retry", retry), patch(
        "backend.shared.queue.tasks.SyncSessionLocal"
    ) as session_local, patch(
        "backend.shared.queue.tasks.sync_create_roadmap",
        side_effect=RuntimeError("temporary_db_issue"),
    ):
        session_local.return_value.__enter__.return_value = MagicMock()
        with pytest.raises(RuntimeError, match="retry:temporary_db_issue"):
            generate_roadmap_task("00000000-0000-0000-0000-000000000001", "drawing")

    assert retry_called["called"] is True


@pytest.mark.asyncio
async def test_create_roadmap_returns_existing_active():
    from backend.roadmap.service import create_roadmap

    generated_structure = {
        "skill_id": "drawing",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_version": 1,
        "template_version": 1,
        "parameters_id": "00000000-0000-0000-0000-000000000002",
        "phases": {},
        "total_estimated_weeks": 0,
        "fingerprint": "abc",
        "generated_at": "2026-04-20T00:00:00Z",
    }
    existing = type("RoadmapModel", (), {"structure": generated_structure})()

    with patch("backend.roadmap.service.RoadmapRepository.get_active", return_value=existing):
        result = await create_roadmap(MagicMock(), UUID("00000000-0000-0000-0000-000000000001"), "drawing")

    assert result.fingerprint == "abc"
    assert result.skill_id == "drawing"


def test_sync_create_roadmap_returns_existing_active_before_generation():
    from backend.roadmap.service import sync_create_roadmap

    db = MagicMock()
    existing = type(
        "RoadmapModel",
        (),
        {"id": "00000000-0000-0000-0000-000000000010", "fingerprint": "existing-fp"},
    )()

    execute_result = MagicMock()
    execute_result.scalars.return_value.first.return_value = existing
    db.execute.return_value = execute_result

    with patch("backend.roadmap.service.generate_roadmap") as generate_mock:
        result = sync_create_roadmap(db, UUID("00000000-0000-0000-0000-000000000001"), "drawing")

    assert result == {"id": "00000000-0000-0000-0000-000000000010", "fingerprint": "existing-fp"}
    generate_mock.assert_not_called()

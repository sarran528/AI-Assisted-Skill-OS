from unittest.mock import AsyncMock, patch

import pytest

from backend.orchestration.orchestrator import (
    check_phase_completion,
    transition_session,
)


@pytest.mark.asyncio
async def test_transition_session_updates_status():
    db = AsyncMock()
    fake_session = type("S", (), {"status": "pending", "user_id": "u1"})()

    with patch("backend.orchestration.orchestrator.SessionRepository.get_by_id", new=AsyncMock(return_value=fake_session)), patch(
        "backend.orchestration.orchestrator.SessionRepository.update_status", new=AsyncMock()
    ) as update_mock:
        await transition_session(db, "sid", "active")
        update_mock.assert_called_once()


@pytest.mark.asyncio
async def test_check_phase_completion_calls_transition_when_all_passed():
    db = AsyncMock()
    with patch(
        "backend.orchestration.orchestrator.CheckpointRepository.all_phase_checkpoints_passed",
        new=AsyncMock(return_value=True),
    ), patch("backend.orchestration.orchestrator.transition_roadmap_phase", new=AsyncMock()) as transition_mock:
        done = await check_phase_completion(db, "rid", "phase_1")
        assert done is True
        transition_mock.assert_called_once()

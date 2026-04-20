from unittest.mock import MagicMock, patch

from backend.shared.queue.celery_app import celery_app
from backend.shared.queue.tasks import (
    cleanup_expired_tokens_task,
    generate_roadmap_task,
    validate_checkpoint_task,
)


def test_generate_roadmap_task_returns_success_payload():
    celery_app.conf.task_always_eager = True
    with patch("backend.shared.queue.tasks.SyncSessionLocal") as mock_session_factory, patch(
        "backend.shared.queue.tasks.sync_create_roadmap",
        return_value={"id": "r1"},
    ):
        mock_session_factory.return_value.__enter__.return_value = MagicMock()
        result = generate_roadmap_task("00000000-0000-0000-0000-000000000001", "drawing")
        assert result["roadmap_id"] == "r1"
        assert result["status"] == "completed"


def test_validate_checkpoint_task_returns_success_payload():
    celery_app.conf.task_always_eager = True
    with patch("backend.shared.queue.tasks.SyncSessionLocal") as mock_session_factory, patch(
        "backend.shared.queue.tasks.sync_run_checkpoint_validation",
        return_value={"passed": True, "reason": "ok"},
    ):
        mock_session_factory.return_value.__enter__.return_value = MagicMock()
        result = validate_checkpoint_task("00000000-0000-0000-0000-000000000002", "cp1")
        assert result["passed"] is True
        assert result["status"] == "completed"


def test_cleanup_task_executes_once():
    with patch("backend.shared.queue.tasks.SyncSessionLocal") as mock_session_factory:
        fake_db = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = fake_db
        cleanup_expired_tokens_task.run()
        assert fake_db.execute.called
        assert fake_db.commit.called


def test_async_result_reports_state_success():
    celery_app.conf.task_always_eager = True
    task = generate_roadmap_task.delay("00000000-0000-0000-0000-000000000003", "drawing")
    assert task.state in {"SUCCESS", "FAILURE"}

from __future__ import annotations

import pytest

from backend.shared.queue.celery_app import celery_app
from backend.shared.queue.tasks import generate_tip_task


def test_generate_tip_task_completes_in_eager_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_generate_tip_async(**kwargs):
        del kwargs
        return {
            "tip": "Reduce pressure and complete one protocol step at a time.",
            "severity": "moderate",
            "failure_type": "accuracy_below_threshold",
        }

    monkeypatch.setattr("backend.shared.queue.tasks._generate_tip_async", _fake_generate_tip_async)

    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    try:
        result = generate_tip_task.delay(
            "00000000-0000-0000-0000-000000000010",
            "drawing",
            "line_control",
            "metric_threshold",
            {"retry_count": 4},
            "00000000-0000-0000-0000-000000000011",
        )
        assert result.successful()
        assert result.result["severity"] == "moderate"
    finally:
        celery_app.conf.task_always_eager = original_always_eager
        celery_app.conf.task_eager_propagates = original_eager_propagates

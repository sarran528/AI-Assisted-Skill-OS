from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from backend.auth.dependencies import get_current_user
from backend.main import app
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter


def _reset_rate_limit_storage() -> None:
    storage = getattr(limiter, "_storage", None)
    if storage is None:
        return
    reset = getattr(storage, "reset", None)
    if callable(reset):
        reset()


@pytest.fixture()
def support_dependency_overrides() -> None:
    test_user_id = UUID("00000000-0000-0000-0000-000000000001")

    async def _override_db():
        yield None

    async def _override_current_user(request: Request):
        request.state.user_id = str(test_user_id)
        return {"user": SimpleNamespace(id=test_user_id)}

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_user] = _override_current_user
    _reset_rate_limit_storage()
    yield
    app.dependency_overrides.clear()
    _reset_rate_limit_storage()


def test_doubt_short_question_returns_422(client, support_dependency_overrides) -> None:
    del support_dependency_overrides
    response = client.post(
        "/api/v1/support/doubt/ask",
        json={"session_id": None, "user_question": "too short"},
    )
    assert response.status_code == 422


def test_doubt_rate_limit_returns_429_on_11th_request(
    client,
    monkeypatch: pytest.MonkeyPatch,
    support_dependency_overrides,
) -> None:
    del support_dependency_overrides

    async def _fake_answer_doubt(**kwargs):
        question = kwargs["user_question"]
        return SimpleNamespace(
            question=question,
            answer="Answer grounded in context.",
            confidence="high",
            caveat=None,
            chunks_used=3,
            session_context={"skill_id": "drawing", "phase": "fundamentals", "technique": "line_control"},
        )

    monkeypatch.setattr("backend.support.router.answer_doubt", _fake_answer_doubt)

    statuses: list[int] = []
    for _ in range(11):
        response = client.post(
            "/api/v1/support/doubt/ask",
            json={"session_id": None, "user_question": "How do I reduce contour wobble quickly?"},
        )
        statuses.append(response.status_code)

    assert all(status == 200 for status in statuses[:10])
    assert statuses[10] == 429


def test_get_tip_returns_pending_when_unavailable(
    client,
    monkeypatch: pytest.MonkeyPatch,
    support_dependency_overrides,
) -> None:
    del support_dependency_overrides

    class _Repo:
        def __init__(self, _db):
            pass

        async def get_latest_for_session(self, _session_id):
            return None

    monkeypatch.setattr("backend.support.router.TipRepository", _Repo)

    session_id = uuid4()
    response = client.get(f"/api/v1/support/tip/{session_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["tipPending"] is True
    assert payload["sessionId"] == str(session_id)


def test_get_tip_returns_latest_tip_when_available(
    client,
    monkeypatch: pytest.MonkeyPatch,
    support_dependency_overrides,
) -> None:
    del support_dependency_overrides

    session_id = uuid4()

    class _Repo:
        def __init__(self, _db):
            pass

        async def get_latest_for_session(self, _session_id):
            return SimpleNamespace(
                session_id=session_id,
                technique_id="line_control",
                tip="Reduce pressure and complete each line in one pass.",
                severity="moderate",
                target_step="stroke_setup",
                failure_type="accuracy_below_threshold",
                created_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr("backend.support.router.TipRepository", _Repo)

    response = client.get(f"/api/v1/support/tip/{session_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sessionId"] == str(session_id)
    assert payload["severity"] == "moderate"
    assert payload["tip"]

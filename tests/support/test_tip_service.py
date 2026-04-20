from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.session.execution import SessionResult, should_generate_tip
from backend.shared.llm.schemas import TipSchema
from backend.support.tip_service import generate_tip


def test_should_generate_tip_trigger_matrix() -> None:
    params = SimpleNamespace(retry_limit=3)

    session_first_fail = SimpleNamespace(attempt_number=1, metrics_captured={"retry_count": 1, "performance_decay": 0.1})
    session_second_fail = SimpleNamespace(attempt_number=2, metrics_captured={"retry_count": 1, "performance_decay": 0.1})
    session_retry_fail = SimpleNamespace(attempt_number=1, metrics_captured={"retry_count": 4, "performance_decay": 0.1})
    session_decay_fail = SimpleNamespace(attempt_number=1, metrics_captured={"retry_count": 1, "performance_decay": 0.6})

    assert should_generate_tip(SessionResult(passed=False, failure_reason="metric_threshold"), session_first_fail, params) is False
    assert should_generate_tip(SessionResult(passed=False, failure_reason="metric_threshold"), session_second_fail, params) is True
    assert should_generate_tip(SessionResult(passed=False, failure_reason="metric_threshold"), session_retry_fail, params) is True
    assert should_generate_tip(SessionResult(passed=False, failure_reason="metric_threshold"), session_decay_fail, params) is True
    assert should_generate_tip(SessionResult(passed=True, failure_reason=None), session_second_fail, params) is False


def test_tip_schema_rejects_more_than_100_words() -> None:
    with pytest.raises(ValueError):
        TipSchema(tip="word " * 101, target_step=None, severity="moderate")


@pytest.mark.asyncio
async def test_tip_fallback_used_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = uuid4()
    user_id = uuid4()

    async def _retrieve(db, query):
        del db, query
        return []

    async def _llm_call(**kwargs):
        del kwargs
        raise RuntimeError("llm down")

    created = {"called": False}

    class _Repo:
        def __init__(self, session):
            del session

        async def create(self, data):
            created["called"] = True
            return data

    async def _audit(*args, **kwargs):
        return None

    monkeypatch.setattr("backend.support.tip_service.retrieve", _retrieve)
    monkeypatch.setattr("backend.support.tip_service.llm_call", _llm_call)
    monkeypatch.setattr("backend.support.tip_service.TipRepository", _Repo)
    monkeypatch.setattr("backend.support.tip_service.log_audit_event", _audit)

    response = await generate_tip(
        db=None,
        session_id=session_id,
        user_id=user_id,
        skill_id="drawing",
        technique_id="line_control",
        failure_reason="metric_threshold",
        session_metrics={"retry_count": 3},
        params=SimpleNamespace(retry_limit=2),
        attempt_number=2,
    )

    assert "Do not skip steps" in response.tip
    assert created["called"] is True

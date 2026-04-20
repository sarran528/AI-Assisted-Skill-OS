from __future__ import annotations

from uuid import uuid4

import pytest

from backend.shared.llm.schemas import DoubtAnswerSchema
from backend.support.doubt_service import answer_doubt


@pytest.mark.asyncio
async def test_doubt_returns_llm_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()

    async def _ctx(db, uid, sid):
        del db, uid, sid
        return "drawing", "fundamentals", "line_control", None

    async def _retrieve(db, query):
        del db, query
        return []

    async def _llm_call(**kwargs):
        assert kwargs["temperature"] == 0.2
        return DoubtAnswerSchema(
            answer="Use lighter pressure and check anchor points.",
            source_phases=["fundamentals"],
            confidence="high",
            caveat=None,
        )

    created = {"called": False}

    class _Repo:
        def __init__(self, session):
            del session

        async def create(self, data):
            created["called"] = True
            return data

    async def _audit(*args, **kwargs):
        return None

    monkeypatch.setattr("backend.support.doubt_service._get_session_context", _ctx)
    monkeypatch.setattr("backend.support.doubt_service.retrieve", _retrieve)
    monkeypatch.setattr("backend.support.doubt_service.llm_call", _llm_call)
    monkeypatch.setattr("backend.support.doubt_service.DoubtRepository", _Repo)
    monkeypatch.setattr("backend.support.doubt_service.log_audit_event", _audit)

    response = await answer_doubt(
        db=None,
        user_id=user_id,
        session_id=None,
        user_question="How can I keep smoother contour lines?",
        current_user={"user": {"id": str(user_id)}},
    )

    assert "lighter pressure" in response.answer
    assert created["called"] is True


@pytest.mark.asyncio
async def test_doubt_fallback_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()

    async def _ctx(db, uid, sid):
        del db, uid, sid
        return "drawing", "fundamentals", "line_control", None

    async def _retrieve(db, query):
        del db, query
        return []

    async def _llm_call(**kwargs):
        del kwargs
        raise RuntimeError("bad llm")

    class _Repo:
        def __init__(self, session):
            del session

        async def create(self, data):
            return data

    async def _audit(*args, **kwargs):
        return None

    monkeypatch.setattr("backend.support.doubt_service._get_session_context", _ctx)
    monkeypatch.setattr("backend.support.doubt_service.retrieve", _retrieve)
    monkeypatch.setattr("backend.support.doubt_service.llm_call", _llm_call)
    monkeypatch.setattr("backend.support.doubt_service.DoubtRepository", _Repo)
    monkeypatch.setattr("backend.support.doubt_service.log_audit_event", _audit)

    response = await answer_doubt(
        db=None,
        user_id=user_id,
        session_id=None,
        user_question="How can I fix this repeated line wobble?",
        current_user={"user": {"id": str(user_id)}},
    )

    assert "Unable to generate" in response.answer
    assert response.confidence == "low"

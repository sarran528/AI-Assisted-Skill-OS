from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Session


class SessionRepository:
    @staticmethod
    async def create(session: AsyncSession, data: dict) -> Session:
        model = Session(**data)
        session.add(model)
        await session.flush()
        await session.commit()
        await session.refresh(model)
        return model

    @staticmethod
    async def get_by_id(session: AsyncSession, session_id: UUID) -> Session | None:
        return await session.get(Session, session_id)

    @staticmethod
    async def append_metrics(session: AsyncSession, session_id: UUID, metrics: dict) -> None:
        model = await session.get(Session, session_id)
        if model is None:
            return
        captured = model.metrics_captured or {}
        records = list(captured.get("records", []))
        records.append(metrics)
        captured["records"] = records
        await session.execute(
            update(Session).where(Session.id == session_id).values(metrics_captured=captured)
        )
        await session.commit()

    @staticmethod
    async def update_status(
        session: AsyncSession,
        session_id: UUID,
        status: str,
        failure_reason: str | None = None,
    ) -> None:
        """This function is called only by backend/orchestration/orchestrator.py."""
        values: dict[str, object] = {"status": status}
        if failure_reason is not None:
            values["failure_reason"] = failure_reason
        if status == "active":
            values["started_at"] = datetime.now(timezone.utc)
        if status in {"completed", "failed"}:
            values["ended_at"] = datetime.now(timezone.utc)

        await session.execute(update(Session).where(Session.id == session_id).values(**values))
        await session.commit()

    @staticmethod
    async def get_active_session(session: AsyncSession, user_id: UUID) -> Session | None:
        stmt = (
            select(Session)
            .where(Session.user_id == user_id)
            .where(Session.status == "active")
            .order_by(Session.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def set_completed_steps(session: AsyncSession, session_id: UUID, steps: list[str]) -> None:
        await session.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(protocol_steps_completed=steps)
        )
        await session.commit()

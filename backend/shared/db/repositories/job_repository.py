from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _serialize_result(value: Any | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, default=str)

    async def get_by_id(self, job_id: str) -> Job | None:
        return await self.session.get(Job, job_id)

    async def create(self, job_id: str, status: str = "pending", result: Any | None = None) -> Job:
        model = Job(id=job_id, status=status, result=self._serialize_result(result))
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Any | None = None,
        error: str | None = None,
    ) -> Job:
        values: dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        payload: dict[str, Any] = {}
        if result is not None:
            payload["result"] = result
        if error is not None:
            payload["error"] = error
        if payload:
            values["result"] = self._serialize_result(payload)

        existing = await self.session.get(Job, job_id)
        if existing is None:
            model = Job(id=job_id, status=status, result=values.get("result"))
            self.session.add(model)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(model)
            return model

        await self.session.execute(update(Job).where(Job.id == job_id).values(**values))
        await self.session.commit()
        await self.session.refresh(existing)
        return existing
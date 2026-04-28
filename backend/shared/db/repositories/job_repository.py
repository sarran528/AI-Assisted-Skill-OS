from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _serialize_payload(payload: Any | None) -> str | None:
        if payload is None:
            return None
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False, default=str)

    async def create(self, job_id: str | UUID, status: str = "queued", result: Any | None = None) -> Job:
        model = Job(
            id=str(job_id),
            status=status,
            result=self._serialize_payload(result),
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def get_by_id(self, job_id: str | UUID) -> Job | None:
        return await self.session.get(Job, str(job_id))

    async def update_job_status(
        self,
        job_id: str | UUID,
        status: str,
        result: Any | None = None,
        error: str | None = None,
    ) -> None:
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
            values["result"] = self._serialize_payload(payload)

        await self.session.execute(
            update(Job).where(Job.id == str(job_id)).values(**values)
        )
        await self.session.commit()

    async def upsert_job(
        self,
        job_id: str | UUID,
        status: str = "queued",
        result: Any | None = None,
    ) -> Job:
        existing = await self.get_by_id(job_id)
        if existing is not None:
            await self.update_job_status(job_id, status, result=result)
            refreshed = await self.get_by_id(job_id)
            if refreshed is not None:
                return refreshed

        return await self.create(job_id, status=status, result=result)
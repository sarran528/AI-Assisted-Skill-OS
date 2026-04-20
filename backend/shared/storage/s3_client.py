from __future__ import annotations

from contextlib import asynccontextmanager

import aioboto3

from backend.shared.config import settings

_session: aioboto3.Session | None = None


def _get_session() -> aioboto3.Session:
    global _session
    if _session is None:
        _session = aioboto3.Session(
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
    return _session


@asynccontextmanager
async def get_s3_client():
    session = _get_session()
    kwargs = {}
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    async with session.client("s3", **kwargs) as client:
        yield client

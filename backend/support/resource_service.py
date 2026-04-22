from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.query_builder import build_resource_query
from backend.rag.retriever import RetrievedChunk, retrieve
from backend.shared.config import settings


logger = logging.getLogger(__name__)
PHASE_CACHE_TTL_SECONDS = 60 * 60
QUERY_CACHE_TTL_SECONDS = 30 * 60


@dataclass(slots=True)
class ResourceItem:
    title: str
    url: str | None
    doc_type: str


@dataclass(slots=True)
class ResourceResponse:
    skill_id: str
    phase: str
    resources: list[ResourceItem]
    query_used: str


def _query_hash(user_query: str | None) -> str:
    return hashlib.sha1((user_query or "").encode("utf-8")).hexdigest()


def _cache_key(skill_id: str, phase: str, user_query: str | None) -> str:
    return f"resources:{skill_id}:{phase}:{_query_hash(user_query)}"


def _derive_title(chunk: RetrievedChunk) -> str:
    first_line = chunk.content.strip().splitlines()[0] if chunk.content.strip() else ""
    if first_line:
        return first_line[:80]
    return chunk.doc_type.replace("_", " ").title()


async def _read_cached_response(redis: Redis, key: str) -> ResourceResponse | None:
    payload = await redis.get(key)
    if not payload:
        return None

    parsed = json.loads(payload)
    resources = [ResourceItem(**item) for item in parsed["resources"]]
    return ResourceResponse(
        skill_id=parsed["skill_id"],
        phase=parsed["phase"],
        resources=resources,
        query_used=parsed["query_used"],
    )


async def _write_cached_response(redis: Redis, key: str, value: ResourceResponse, ttl: int) -> None:
    payload = {
        "skill_id": value.skill_id,
        "phase": value.phase,
        "query_used": value.query_used,
        "resources": [asdict(item) for item in value.resources],
    }
    await redis.set(key, json.dumps(payload), ex=ttl)


async def get_resources(
    db: AsyncSession,
    skill_id: str,
    phase: str,
    user_query: str | None,
    current_user: dict,
) -> ResourceResponse:
    del current_user  # resources are auth-gated by router dependency

    redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    key = _cache_key(skill_id, phase, user_query)

    cached = await _read_cached_response(redis, key)
    if cached is not None:
        await redis.aclose()
        return cached

    retrieval_query = build_resource_query(skill_id, phase, user_query)
    chunks = await retrieve(db, retrieval_query)

    if len(chunks) < 2:
        logger.warning(
            "Resource retrieval returned low chunk count",
            extra={"skill_id": skill_id, "phase": phase, "count": len(chunks)},
        )

    response = ResourceResponse(
        skill_id=skill_id,
        phase=phase,
        resources=[
            ResourceItem(
                title=_derive_title(chunk),
                url=chunk.source_url,
                doc_type=chunk.doc_type,
            )
            for chunk in chunks
        ],
        query_used=retrieval_query.query_text,
    )

    ttl = QUERY_CACHE_TTL_SECONDS if user_query else PHASE_CACHE_TTL_SECONDS
    await _write_cached_response(redis, key, response, ttl=ttl)
    await redis.aclose()
    return response

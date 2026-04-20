from __future__ import annotations

import json
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.shared.config import settings
from backend.shared.errors import SystemError


SchemaT = TypeVar("SchemaT", bound=BaseModel)


def get_llm_provider() -> str:
    return settings.llm_provider


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
async def _call_openai_json(prompt: str, temperature: float) -> str:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned empty content")
    return content


async def llm_call(
    prompt: str,
    response_schema: type[SchemaT],
    temperature: float = 0.0,
) -> SchemaT:
    provider = get_llm_provider()
    if provider != "openai":
        raise SystemError("llm_provider_not_supported", context={"provider": provider})

    try:
        raw_json = await _call_openai_json(prompt, temperature)
        payload = json.loads(raw_json)
        return response_schema.model_validate(payload)
    except Exception as exc:  # pragma: no cover - network/provider behavior differs in runtime
        raise SystemError("llm_call_failed", context={"provider": provider}) from exc

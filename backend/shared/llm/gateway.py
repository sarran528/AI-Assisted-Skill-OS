"""LLM gateway with validation and retry logic."""
import logging
import json
import re
from typing import TypeVar, Any

from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.shared.config import settings
from backend.shared.errors import SystemError
from backend.shared.llm.client import (
    get_anthropic_client,
    get_groq_client,
    get_together_client,
    get_openai_client
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _strip_markdown_json(text: str) -> str:
    """Strip markdown code blocks from LLM response."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


async def llm_call(
    prompt: str,
    system_prompt: str,
    response_schema: type[T],
    fallback: T,
    temperature: float = 0.0,
) -> T:
    """
    Call LLM with structured output validation and retry logic.
    Supports Anthropic, Groq, Together, and OpenAI.
    """

    async def make_api_call() -> str:
        provider = settings.llm_provider.lower()
        
        if provider == "anthropic":
            client = get_anthropic_client()
            response = await client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
            
        elif provider == "groq":
            client = get_groq_client()
            response = await client.chat.completions.create(
                model=settings.groq_model,
                max_tokens=settings.llm_max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
            
        elif provider == "together":
            client = get_together_client()
            response = await client.chat.completions.create(
                model=settings.together_model,
                max_tokens=settings.llm_max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
            
        else: # Default to openai
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content

    api_call_retry = AsyncRetrying(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )

    try:
        content = ""
        try:
            content = await make_api_call()
        except Exception as e:
            logger.warning(f"LLM API call failed, retrying: {e}")
            try:
                async for attempt in api_call_retry:
                    with attempt:
                        content = await make_api_call()
            except Exception as retry_error:
                logger.error(f"LLM API call failed after retry: {retry_error}")
                raise SystemError("llm_gateway_failure") from retry_error

        # Strip markdown and validate
        clean_content = _strip_markdown_json(content)
        try:
            return response_schema.model_validate_json(clean_content)
        except ValidationError as val_error:
            logger.warning(f"LLM response validation failed, retrying: {val_error}")

            try:
                content = await make_api_call()
                clean_content = _strip_markdown_json(content)
                return response_schema.model_validate_json(clean_content)
            except (ValidationError, Exception) as retry_val_error:
                logger.warning(
                    f"LLM response validation failed after retry. Raw response: {content}. Error: {retry_val_error}"
                )
                return fallback

    except SystemError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in llm_call: {e}")
        raise SystemError("llm_gateway_failure") from e

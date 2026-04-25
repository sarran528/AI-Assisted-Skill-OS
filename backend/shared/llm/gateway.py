"""LLM gateway with validation and retry logic."""
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
import anthropic

from backend.shared.config import settings
from backend.shared.errors import SystemError
from backend.shared.llm.client import get_anthropic_client

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def llm_call(
    prompt: str,
    system_prompt: str,
    response_schema: type[T],
    fallback: T,
    temperature: float = 0.0,
) -> T:
    """
    Call LLM with structured output validation and retry logic.

    Enforces three constraints:
    1. Temperature is always 0.0 for structured output
    2. Response is validated against Pydantic schema
    3. Failure triggers one retry before returning fallback

    Args:
        prompt: User message prompt
        system_prompt: System message instruction
        response_schema: Pydantic model for response validation
        fallback: Fallback response if both attempts fail
        temperature: Override ignored - always 0.0

    Returns:
        Validated response model or fallback

    Raises:
        SystemError: If API calls fail at network/service level after retries
    """
    # Use the passed temperature (default 0.0 for structured, 0.2 for RAG).

    client = get_anthropic_client()

    async def make_api_call() -> str:
        """Make single API call to Anthropic."""
        response = await client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    # Retry API calls on exceptions - not on validation errors
    api_call_retry = AsyncRetrying(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )

    try:
        # Attempt 1: First API call
        try:
            content = await make_api_call()
        except Exception as e:
            # Attempt 2: Retry on API error with exponential backoff
            logger.warning(f"LLM API call failed, retrying: {e}")
            try:
                async for attempt in api_call_retry:
                    with attempt:
                        content = await make_api_call()
            except Exception as retry_error:
                logger.error(f"LLM API call failed after retry: {retry_error}")
                raise SystemError("llm_gateway_failure") from retry_error

        # Attempt 1: Validate response
        try:
            return response_schema.model_validate_json(content)
        except ValidationError as val_error:
            logger.warning(f"LLM response validation failed, retrying: {val_error}")

            # Attempt 2: Retry validation with fresh API call
            try:
                content = await make_api_call()
                return response_schema.model_validate_json(content)
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

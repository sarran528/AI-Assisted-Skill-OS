"""Tests for LLM gateway validation and retry logic."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from backend.shared.llm.gateway import llm_call
from backend.shared.llm.schemas import (
    DEFAULT_FEASIBILITY,
    FeasibilityResult,
)


class SimpleResponse(BaseModel):
    """Simple test response schema."""

    message: str
    value: int


@pytest.mark.asyncio
async def test_llm_call_valid_response():
    """Test successful LLM call with valid JSON response."""
    expected = SimpleResponse(message="test", value=42)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=expected.model_dump_json())]

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await llm_call(
            prompt="test prompt",
            system_prompt="test system",
            response_schema=SimpleResponse,
            fallback=SimpleResponse(message="fallback", value=0),
        )

    assert result.message == "test"
    assert result.value == 42


@pytest.mark.asyncio
async def test_llm_call_invalid_json_once():
    """Test LLM call that returns invalid JSON, then retries with valid JSON."""
    valid_response = SimpleResponse(message="success", value=99)
    mock_response_invalid = MagicMock()
    mock_response_invalid.content = [MagicMock(text="not valid json at all")]

    mock_response_valid = MagicMock()
    mock_response_valid.content = [MagicMock(text=valid_response.model_dump_json())]

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_response_invalid
        return mock_response_valid

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(side_effect=side_effect)

        result = await llm_call(
            prompt="test prompt",
            system_prompt="test system",
            response_schema=SimpleResponse,
            fallback=SimpleResponse(message="fallback", value=0),
        )

    assert result.message == "success"
    assert result.value == 99
    assert call_count == 2  # Verify retry happened


@pytest.mark.asyncio
async def test_llm_call_invalid_json_twice_returns_fallback():
    """Test that two validation failures return fallback instead of raising."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not valid json")]

    fallback = SimpleResponse(message="fallback_used", value=-1)

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await llm_call(
            prompt="test prompt",
            system_prompt="test system",
            response_schema=SimpleResponse,
            fallback=fallback,
        )

    assert result == fallback


@pytest.mark.asyncio
async def test_llm_call_api_error_retries():
    """Test that API exceptions trigger retry."""
    valid_response = SimpleResponse(message="recovered", value=77)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=valid_response.model_dump_json())]

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("API unavailable")
        return mock_response

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(side_effect=side_effect)

        result = await llm_call(
            prompt="test prompt",
            system_prompt="test system",
            response_schema=SimpleResponse,
            fallback=SimpleResponse(message="fallback", value=0),
        )

    assert result.message == "recovered"
    assert call_count == 2


@pytest.mark.asyncio
async def test_llm_call_api_error_twice_raises_system_error():
    """Test that two API failures raise SystemError, not return fallback."""
    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(side_effect=ConnectionError("API down"))

        with pytest.raises(SystemError, match="llm_gateway_failure"):
            await llm_call(
                prompt="test prompt",
                system_prompt="test system",
                response_schema=SimpleResponse,
                fallback=SimpleResponse(message="fallback", value=0),
            )


@pytest.mark.asyncio
async def test_llm_call_temperature_forced_to_zero():
    """Test that temperature parameter is always enforced as 0.0 in API call."""
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text=SimpleResponse(message="test", value=1).model_dump_json())
    ]

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        # Call with non-zero temperature - should be overridden
        await llm_call(
            prompt="test",
            system_prompt="system",
            response_schema=SimpleResponse,
            fallback=SimpleResponse(message="f", value=0),
            temperature=0.7,  # This should be ignored
        )

        # Verify temperature in API call was 0.0
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_llm_call_with_feasibility_schema():
    """Test gateway with actual FeasibilityResult schema."""
    expected = FeasibilityResult(
        feasible=True, risk_level="low", blockers=[], confidence=0.95
    )
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=expected.model_dump_json())]

    with patch("backend.shared.llm.gateway.get_anthropic_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client_factory.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await llm_call(
            prompt="Is this feasible?",
            system_prompt="You are an evaluator.",
            response_schema=FeasibilityResult,
            fallback=DEFAULT_FEASIBILITY,
        )

    assert isinstance(result, FeasibilityResult)
    assert result.feasible is True
    assert result.risk_level == "low"
    assert result.confidence == 0.95

"""LLM client factory for different providers."""
from functools import lru_cache
import anthropic
import openai
from backend.shared.config import settings


@lru_cache(maxsize=1)
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    """Get or create the singleton Anthropic async client."""
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


@lru_cache(maxsize=1)
def get_groq_client() -> openai.AsyncOpenAI:
    """Get or create the singleton Groq async client (OpenAI compatible)."""
    return openai.AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )


@lru_cache(maxsize=1)
def get_together_client() -> openai.AsyncOpenAI:
    """Get or create the singleton Together AI async client (OpenAI compatible)."""
    return openai.AsyncOpenAI(
        api_key=settings.together_api_key,
        base_url="https://api.together.xyz/v1"
    )


@lru_cache(maxsize=1)
def get_openai_client() -> openai.AsyncOpenAI:
    """Get or create the singleton OpenAI async client."""
    return openai.AsyncOpenAI(api_key=settings.openai_api_key)

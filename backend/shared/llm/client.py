"""Singleton Anthropic client factory."""
from functools import lru_cache
import anthropic

from backend.shared.config import settings


@lru_cache(maxsize=1)
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    """Get or create the singleton Anthropic async client."""
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

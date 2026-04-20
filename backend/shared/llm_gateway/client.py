from backend.shared.config import settings


def get_llm_provider() -> str:
    return settings.llm_provider

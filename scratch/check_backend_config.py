
import os
from backend.shared.config import settings
from dotenv import load_dotenv

def check_config():
    load_dotenv(".env.local")
    print(f"App Env: {settings.app_env}")
    print(f"Database URL: {settings.database_url}")
    print(f"LLM Provider: {settings.llm_provider}")

if __name__ == "__main__":
    check_config()

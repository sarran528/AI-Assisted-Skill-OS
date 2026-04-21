from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.shared.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# For sync engine, handle both PostgreSQL and SQLite
if "postgresql" in settings.database_url:
    sync_database_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
elif "sqlite" in settings.database_url:
    sync_database_url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")
else:
    sync_database_url = settings.database_url

sync_engine = create_engine(sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)

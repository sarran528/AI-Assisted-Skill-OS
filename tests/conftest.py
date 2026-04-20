import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.shared.db.engine import SessionLocal


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
async def db_session() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()

import pytest
from src.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_database_url_config():
    assert "postgresql+asyncpg" in settings.DATABASE_URL
    assert "pg_finanser" in settings.DATABASE_URL

@pytest.mark.asyncio
async def test_healthcheck(ac):
    response = await ac.get("/health")
    assert response.status_code == 200
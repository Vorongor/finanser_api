import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def ac() -> AsyncGenerator[AsyncClient, None]:
    """Client for requests API"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

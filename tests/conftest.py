import os

# Point the app at a dedicated test database before app.db is imported,
# so the app's own engine/session factory targets it — no dependency
# overrides needed.
TEST_DB_NAME = "tally_test"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://postgres:postgres@localhost:5432/{TEST_DB_NAME}",
)

import asyncpg  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db import BaseModel, engine  # noqa: E402
from app.main import app  # noqa: E402

MAINTENANCE_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


async def _ensure_database_exists() -> None:
    conn = await asyncpg.connect(MAINTENANCE_DATABASE_URL)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _database():
    await _ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    yield
    async with engine.begin() as conn:
        for table in reversed(BaseModel.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture(autouse=True)
async def _reset_rate_limiter():
    # Rate limit storage is in-memory and shared across tests within the
    # process, so reset it before each test to avoid cross-test bleed.
    app.state.limiter.reset()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_client(ip: str) -> AsyncClient:
    """A client whose requests appear to originate from a given IP —
    used to simulate distinct visitors for unique-click tests."""
    transport = ASGITransport(app=app, client=(ip, 1))
    return AsyncClient(transport=transport, base_url="http://test")

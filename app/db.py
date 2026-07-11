import os
from collections.abc import AsyncGenerator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Falls back to the local Postgres from docker-compose.yml if DATABASE_URL is not set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

# Connection pool to the database; echo=True logs every SQL statement (handy for debugging)
engine = create_async_engine(DATABASE_URL, echo=True)
# Factory for per-request sessions; expire_on_commit=False keeps loaded objects usable after commit
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Base class every ORM model (LinkModel, StatsModel, ...) inherits from
class BaseModel(DeclarativeBase):
    pass


# FastAPI dependency: yields a session for one request and closes it afterwards
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _upgrade_to_head(connection: Connection) -> None:
    cfg = Config(str(ALEMBIC_INI))
    # hand our connection to migrations/env.py so it doesn't open its own
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


# Brings the database schema up to date by applying pending Alembic migrations
async def run_migrations() -> None:
    async with engine.begin() as conn:
        # alembic's command API is sync, so it needs run_sync on the async connection
        await conn.run_sync(_upgrade_to_head)

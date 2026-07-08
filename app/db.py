import os
from collections.abc import AsyncGenerator

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


# Creates all tables registered on BaseModel.metadata if they don't exist yet
async def init_models() -> None:
    async with engine.begin() as conn:
        # create_all is sync, so it needs run_sync on the async connection
        await conn.run_sync(BaseModel.metadata.create_all)

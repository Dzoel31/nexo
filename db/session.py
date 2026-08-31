import os
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

# Format URL: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nexo_dev:nexo_1234@localhost:5432/nexo_db",
)

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True untuk debug query SQL
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

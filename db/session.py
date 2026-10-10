from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from config.settings import settings

# Format URL: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = settings.DATABASE_URL

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True untuk debug query SQL
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validasi koneksi sebelum checkout dari pool
    pool_recycle=1800,  # Daur ulang koneksi setiap 30 menit (1800s)
    pool_timeout=30.0,  # Mencegah worker hang jika connection pool penuh
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

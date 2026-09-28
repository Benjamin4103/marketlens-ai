from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool avoids reusing asyncpg connections across different event loops.
# This matters for the test suite (pytest-asyncio creates a fresh loop per
# test function) and is a negligible cost for a research app's request volume.
engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

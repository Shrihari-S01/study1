"""Database engine configuration."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

print("=" * 80)
print("DATABASE:", settings.DATABASE_URL)
print("ENGINE:", engine)
print("DIALECT:", engine.dialect)
print("DIALECT CLASS:", engine.dialect.__class__)
print("=" * 80)
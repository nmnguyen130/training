from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

app_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

app_session = async_sessionmaker(
    bind=app_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

owner_engine = create_async_engine(
    settings.DATABASE_OWNER_URL,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_OWNER_POOL_SIZE,
    max_overflow=0,
)

owner_session = async_sessionmaker(
    bind=owner_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings

# Determine database URL and connect args
db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Async engine
engine = create_async_engine(
    db_url,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    if db_url.startswith("sqlite"):
        import os
        # Extract directory from sqlite path
        path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if path and not path.startswith(":memory:"):
            db_dir = os.path.dirname(os.path.abspath(path))
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

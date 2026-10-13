"""
Database Engine and Session Configuration.
Supports PostgreSQL 16 + PostGIS for production and SQLite for local portable execution.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# If DATABASE_URL is set (e.g. postgresql+asyncpg://user:pass@localhost:5432/carbonkheti), use it.
# Otherwise, fallback gracefully to local SQLite async database.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    os.makedirs(DB_DIR, exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DB_DIR, 'carbonkheti.db')}"

# Normalise postgres:// or postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

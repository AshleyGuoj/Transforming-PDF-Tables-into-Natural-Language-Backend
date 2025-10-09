"""
Database session management with async and sync support.
Handles connection pooling and session lifecycle for both paradigms.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ============================================================
# Async Engine & Sessions (for FastAPI endpoints)
# ============================================================

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    echo_pool=settings.DEBUG,  # Log connection pool events
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    max_overflow=10,  # Allow up to 10 overflow connections
    pool_size=5,  # Maintain 5 connections in pool
    # Use NullPool for testing to avoid connection issues
    poolclass=NullPool if settings.APP_ENV == "test" else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=True,  # Auto-flush before queries
    autocommit=False,  # Manual transaction control
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with automatic cleanup.
    
    Usage:
        async with get_async_session() as session:
            # Use session here
            result = await session.execute(select(User))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get async database session.
    
    Usage in FastAPI routes:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with get_async_session() as session:
        yield session


# ============================================================
# Sync Engine & Sessions (for Celery workers and scripts)
# ============================================================

# Convert async DATABASE_URL to sync version for synchronous operations
# Only create sync engine if DATABASE_URL is available
try:
    sync_database_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )

    # Create sync engine
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=3600,
        max_overflow=10,
        pool_size=5,
        poolclass=NullPool if settings.APP_ENV == "test" else None,
    )

    # Create sync session factory
    SyncSessionLocal = sessionmaker(
        bind=sync_engine,
        autocommit=False,
        autoflush=True,
        expire_on_commit=False,
    )
except Exception as e:
    logger.warning(f"Could not create sync engine: {e}")
    sync_engine = None
    SyncSessionLocal = None


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Get sync database session with automatic cleanup.
    
    Usage:
        with get_sync_session() as session:
            # Use session here
            users = session.query(User).all()
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """
    Get sync database session (for Celery tasks).
    
    Usage in Celery tasks:
        @celery_app.task
        def process_data():
            with get_sync_db() as db:
                users = db.query(User).all()
    """
    with get_sync_session() as session:
        yield session


# ============================================================
# Database Utilities
# ============================================================

async def create_tables():
    """Create all database tables (async)."""
    from app.db.base import Base
    
    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables (async)."""
    from app.db.base import Base
    
    logger.warning("Dropping all database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Database tables dropped")


def create_tables_sync():
    """Create all database tables (sync)."""
    from app.db.base import Base
    
    logger.info("Creating database tables (sync)")
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")


def drop_tables_sync():
    """Drop all database tables (sync)."""
    from app.db.base import Base
    
    logger.warning("Dropping all database tables (sync)")
    Base.metadata.drop_all(bind=sync_engine)
    logger.warning("Database tables dropped")


async def check_database_connection() -> bool:
    """
    Check if async database connection is working.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Async database connection successful")
        return True
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        return False


def check_database_connection_sync() -> bool:
    """
    Check if sync database connection is working.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        with sync_engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Sync database connection successful")
        return True
    except Exception as e:
        logger.error(f"Sync database connection failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information for health checks (async).
    
    Returns:
        dict: Database connection information
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute("""
                SELECT 
                    version() as version,
                    current_database() as database,
                    current_user as user,
                    inet_server_addr() as host,
                    inet_server_port() as port
            """)
            row = result.fetchone()
            
            return {
                "status": "connected",
                "version": row.version,
                "database": row.database,
                "user": row.user,
                "host": row.host,
                "port": row.port,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

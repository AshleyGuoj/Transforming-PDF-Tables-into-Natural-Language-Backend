"""
Database session management with async support.
Handles connection pooling and session lifecycle.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

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
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    from app.db.base import Base
    
    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables."""
    from app.db.base import Base
    
    logger.warning("Dropping all database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Database tables dropped")


async def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information for health checks.
    
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


# For backward compatibility and FastAPI dependency injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session.
    
    This is a wrapper around get_async_session for use with FastAPI's
    dependency injection system.
    """
    async with get_async_session() as session:
        yield session 
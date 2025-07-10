from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine with appropriate configuration
def create_engine(database_url: str = None, echo: bool = None):
    """
    Create SQLAlchemy async engine with proper configuration.
    
    Args:
        database_url: Database URL (defaults to settings)
        echo: Enable SQL echo logging (defaults to settings)
        
    Returns:
        AsyncEngine instance
    """
    url = database_url or settings.DATABASE_URL
    echo_sql = echo if echo is not None else settings.DATABASE_ECHO
    
    # Use NullPool for SQLite to avoid connection issues
    engine_args = {
        "poolclass": NullPool,
    }
    
    engine = create_async_engine(
        url,
        echo=echo_sql,
        future=True,
        **engine_args
    )
    
    return engine


# Create the default engine
engine = create_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
        
    Usage:
        ```python
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            # Use session here
            pass
        ```
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


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.
    
    Usage:
        ```python
        async with get_session_context() as session:
            # Use session here
            pass
        ```
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


async def create_test_engine(database_url: str = None):
    """
    Create test engine with test database.
    
    Args:
        database_url: Test database URL
        
    Returns:
        AsyncEngine instance for testing
    """
    url = database_url or settings.TEST_DATABASE_URL
    return create_engine(url, echo=False)


class DatabaseSessionManager:
    """
    Manager for database sessions with transaction support.
    """
    
    def __init__(self):
        self._engine = None
        self._sessionmaker = None
    
    def init(self, database_url: str = None, echo: bool = None):
        """
        Initialize the session manager.
        
        Args:
            database_url: Database URL
            echo: Enable SQL echo logging
        """
        self._engine = create_engine(database_url, echo)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    async def close(self):
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Yields:
            AsyncSession: Database session
        """
        if not self._sessionmaker:
            raise RuntimeError("DatabaseSessionManager not initialized")
        
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def transaction(self, session: AsyncSession = None):
        """
        Create a database transaction.
        
        Args:
            session: Existing session to use (creates new if None)
            
        Yields:
            AsyncSession: Database session with transaction
        """
        if session:
            # Use existing session with savepoint
            async with session.begin_nested():
                yield session
        else:
            # Create new session with transaction
            async with self.session() as new_session:
                async with new_session.begin():
                    yield new_session


# Create global session manager instance
db_manager = DatabaseSessionManager()
db_manager.init()


# Utility functions
async def init_db():
    """
    Initialize database (create tables).
    This should be called during application startup.
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def drop_db():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")


async def check_db_connection():
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Execute a simple query
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# Export commonly used items
__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "get_session_context",
    "db_manager",
    "init_db",
    "drop_db",
    "check_db_connection",
]
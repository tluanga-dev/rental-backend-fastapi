from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, text
from typing import AsyncGenerator
import datetime

from app.core.config import settings


# Performance-optimized engine configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    
    # Connection pool optimization
    pool_size=20,  # Increased from default 5 for high concurrency
    max_overflow=40,  # Increased from default 10
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
    
    # Query execution optimization
    connect_args={
        "server_settings": {
            "application_name": "rental_manager",
            "jit": "off",  # Disable JIT for consistent performance
        },
        "command_timeout": 60,  # Query timeout in seconds
        "prepared_statement_cache_size": 0,  # Disable PS cache for better pooling
    },
    
    # Engine-level optimizations
    query_cache_size=1200,  # Increase query cache
    echo_pool=settings.DEBUG,  # Log pool checkouts/checkins in debug mode
)

# Optimized session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    
    # Session-level optimizations
    autoflush=False,  # Disable autoflush for better control
    autocommit=False,
)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all database models"""
    
    # Common columns for all models
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Database utility functions
async def init_db():
    """Initialize database with performance optimizations"""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Run ANALYZE on critical tables for query planner (if tables exist)
        try:
            await conn.execute(text("ANALYZE stock_levels;"))
            await conn.execute(text("ANALYZE transaction_headers;"))
            await conn.execute(text("ANALYZE transaction_lines;"))
            await conn.execute(text("ANALYZE items;"))
        except Exception:
            pass  # Tables might not exist yet


async def close_db():
    """Close database connections"""
    await engine.dispose()


# Connection pool monitoring utilities
async def get_pool_status() -> dict:
    """Get current connection pool statistics"""
    pool = engine.pool
    return {
        "size": getattr(pool, 'size', lambda: 0)() if hasattr(pool, 'size') else 0,
        "checked_out": getattr(pool, 'checked_out_connections', lambda: 0)() if hasattr(pool, 'checked_out_connections') else 0,
        "overflow": getattr(pool, 'overflow', lambda: 0)() if hasattr(pool, 'overflow') else 0,
        "total": (getattr(pool, 'size', lambda: 0)() + getattr(pool, 'overflow', lambda: 0)()) if hasattr(pool, 'size') else 0
    }
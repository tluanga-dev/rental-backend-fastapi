"""
Optimized database configuration with performance tuning for rental operations.
This can replace or be merged with the existing database.py file.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, pool
from typing import AsyncGenerator
import datetime

from app.core.config import settings


# Performance-optimized engine configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    
    # Connection pool optimization
    poolclass=pool.NullPool if settings.TESTING else pool.AsyncAdaptedQueuePool,
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
        "prepared_statement_name_func": lambda:None,  # Disable prepared statements
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
    """Base class for all database models with common fields"""
    
    # Common columns for all models
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True  # Add index for time-based queries
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True  # Add index for update tracking
    )


# Optimized database dependency with connection pooling stats
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with performance monitoring.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Log pool statistics in debug mode
            if settings.DEBUG:
                pool_status = engine.pool.status()  # type: ignore
                if hasattr(engine.pool, 'size'):
                    print(f"DB Pool - Size: {engine.pool.size()}, "
                          f"Checked out: {engine.pool.checked_out_connections()}")
            
            yield session
            
            # Commit only if there are pending changes
            if session.in_transaction():
                await session.commit()
                
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Optimized database utility functions
async def init_db():
    """Initialize database with performance optimizations"""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Run ANALYZE on critical tables for query planner
        await conn.execute(text("ANALYZE stock_levels;"))
        await conn.execute(text("ANALYZE transaction_headers;"))
        await conn.execute(text("ANALYZE transaction_lines;"))
        await conn.execute(text("ANALYZE items;"))
        
        # Set PostgreSQL performance parameters for session
        await conn.execute(text("SET work_mem = '256MB';"))
        await conn.execute(text("SET maintenance_work_mem = '512MB';"))


async def close_db():
    """Close database connections and cleanup"""
    await engine.dispose()


# Connection pool monitoring utilities
async def get_pool_status() -> dict:
    """Get current connection pool statistics"""
    pool = engine.pool
    return {
        "size": pool.size() if hasattr(pool, 'size') else 0,
        "checked_out": pool.checked_out_connections() if hasattr(pool, 'checked_out_connections') else 0,
        "overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
        "total": pool.size() + pool.overflow() if hasattr(pool, 'size') else 0
    }


# Database performance helpers
class DatabasePerformance:
    """Helper class for database performance monitoring and optimization"""
    
    @staticmethod
    async def explain_query(session: AsyncSession, query: str) -> list:
        """Get query execution plan"""
        result = await session.execute(text(f"EXPLAIN ANALYZE {query}"))
        return result.fetchall()
    
    @staticmethod
    async def get_slow_queries(session: AsyncSession, min_duration_ms: int = 100) -> list:
        """Get slow queries from pg_stat_statements"""
        query = """
        SELECT 
            query,
            calls,
            mean_exec_time,
            total_exec_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE mean_exec_time > :min_duration
        ORDER BY mean_exec_time DESC
        LIMIT 20
        """
        result = await session.execute(text(query), {"min_duration": min_duration_ms})
        return result.fetchall()
    
    @staticmethod
    async def vacuum_analyze_table(session: AsyncSession, table_name: str):
        """Run VACUUM ANALYZE on a specific table"""
        await session.execute(text(f"VACUUM ANALYZE {table_name}"))
        await session.commit()


# Example usage in the application
"""
# In app/main.py, update the engine import:
from app.core.database_optimized import engine, init_db, close_db, get_pool_status

# Add a health check endpoint that includes pool status:
@app.get("/health/detailed")
async def health_check_detailed():
    pool_status = await get_pool_status()
    return {
        "status": "healthy",
        "database_pool": pool_status,
        "timestamp": datetime.now()
    }
"""
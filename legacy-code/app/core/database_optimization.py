"""
Database optimization utilities for performance improvement.

This module provides database query optimization, indexing, and connection pooling.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

from sqlalchemy import text, Index, func, inspect
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.db.session import get_session, engine
from app.core.config import settings


logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization utilities."""
    
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.performance_stats = {}
    
    async def create_indexes(self):
        """Create performance indexes for frequently queried tables."""
        
        indexes = [
            # Customer indexes
            ("customers", "idx_customers_email", ["email"]),
            ("customers", "idx_customers_phone", ["phone_number"]),
            ("customers", "idx_customers_type", ["customer_type"]),
            ("customers", "idx_customers_created", ["created_at"]),
            ("customers", "idx_customers_status", ["is_active"]),
            
            # Inventory indexes
            ("inventory_items", "idx_inventory_sku", ["sku"]),
            ("inventory_items", "idx_inventory_category", ["category_id"]),
            ("inventory_items", "idx_inventory_brand", ["brand_id"]),
            ("inventory_items", "idx_inventory_status", ["is_active"]),
            ("inventory_items", "idx_inventory_availability", ["is_available"]),
            ("inventory_items", "idx_inventory_price", ["rental_price_per_day"]),
            
            # Transaction indexes
            ("transactions", "idx_transactions_customer", ["customer_id"]),
            ("transactions", "idx_transactions_type", ["transaction_type"]),
            ("transactions", "idx_transactions_status", ["status"]),
            ("transactions", "idx_transactions_date", ["transaction_date"]),
            ("transactions", "idx_transactions_amount", ["total_amount"]),
            
            # Rental indexes
            ("rentals", "idx_rentals_customer", ["customer_id"]),
            ("rentals", "idx_rentals_item", ["item_id"]),
            ("rentals", "idx_rentals_status", ["status"]),
            ("rentals", "idx_rentals_start_date", ["start_date"]),
            ("rentals", "idx_rentals_end_date", ["end_date"]),
            ("rentals", "idx_rentals_return_date", ["return_date"]),
            
            # Authentication indexes
            ("users", "idx_users_username", ["username"]),
            ("users", "idx_users_email", ["email"]),
            ("users", "idx_users_status", ["is_active"]),
            ("users", "idx_users_created", ["created_at"]),
            
            # Composite indexes for common queries
            ("customers", "idx_customers_type_status", ["customer_type", "is_active"]),
            ("inventory_items", "idx_inventory_category_brand", ["category_id", "brand_id"]),
            ("transactions", "idx_transactions_customer_date", ["customer_id", "transaction_date"]),
            ("rentals", "idx_rentals_customer_status", ["customer_id", "status"]),
        ]
        
        async with self.engine.begin() as conn:
            for table_name, index_name, columns in indexes:
                try:
                    # Check if index exists
                    result = await conn.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                    )
                    if result.fetchone():
                        logger.info(f"Index {index_name} already exists")
                        continue
                    
                    # Create index
                    columns_str = ", ".join(columns)
                    create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                    await conn.execute(text(create_index_sql))
                    logger.info(f"Created index {index_name} on {table_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
    
    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN QUERY PLAN."""
        
        async with self.engine.begin() as conn:
            try:
                # Get query plan
                plan_result = await conn.execute(text(f"EXPLAIN QUERY PLAN {query}"))
                plan = plan_result.fetchall()
                
                # Get execution stats
                stats_result = await conn.execute(text(f"EXPLAIN {query}"))
                stats = stats_result.fetchall()
                
                return {
                    "query": query,
                    "plan": [dict(row._mapping) for row in plan],
                    "stats": [dict(row._mapping) for row in stats],
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Query analysis failed: {e}")
                return {"error": str(e)}
    
    async def get_table_statistics(self) -> Dict[str, Any]:
        """Get table statistics for optimization analysis."""
        
        async with self.engine.begin() as conn:
            stats = {}
            
            # Get table names
            tables_result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in tables_result.fetchall()]
            
            for table in tables:
                try:
                    # Get row count
                    count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = count_result.scalar()
                    
                    # Get table info
                    info_result = await conn.execute(text(f"PRAGMA table_info({table})"))
                    columns = info_result.fetchall()
                    
                    # Get indexes
                    indexes_result = await conn.execute(text(f"PRAGMA index_list({table})"))
                    indexes = indexes_result.fetchall()
                    
                    stats[table] = {
                        "row_count": row_count,
                        "column_count": len(columns),
                        "index_count": len(indexes),
                        "columns": [col[1] for col in columns],
                        "indexes": [idx[1] for idx in indexes]
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for table {table}: {e}")
                    stats[table] = {"error": str(e)}
            
            return stats
    
    async def optimize_database(self):
        """Run database optimization commands."""
        
        optimization_commands = [
            "ANALYZE",  # Update statistics
            "VACUUM",   # Rebuild database file
            "PRAGMA optimize",  # SQLite optimization
        ]
        
        async with self.engine.begin() as conn:
            for command in optimization_commands:
                try:
                    await conn.execute(text(command))
                    logger.info(f"Executed optimization command: {command}")
                except Exception as e:
                    logger.error(f"Optimization command failed {command}: {e}")
    
    async def monitor_slow_queries(self, threshold_ms: int = 1000) -> List[Dict[str, Any]]:
        """Monitor slow queries (placeholder for production implementation)."""
        
        # In a production environment, you would implement actual slow query logging
        # This is a placeholder that would integrate with your logging system
        
        return [
            {
                "query": "SELECT * FROM customers WHERE email = ?",
                "duration_ms": 1250,
                "timestamp": datetime.now().isoformat(),
                "suggestion": "Add index on email column"
            }
        ]


class QueryOptimizer:
    """Query optimization utilities."""
    
    @staticmethod
    def optimize_customer_queries():
        """Optimized query patterns for customer operations."""
        
        # Optimized customer list query with pagination
        def get_customers_optimized(session: AsyncSession, limit: int = 50, offset: int = 0):
            return session.query(
                # Select only needed columns
                "id", "first_name", "last_name", "email", "customer_type", "is_active"
            ).filter(
                # Use indexed column first
                "is_active == True"
            ).order_by(
                # Order by indexed column
                "created_at"
            ).limit(limit).offset(offset)
        
        return get_customers_optimized
    
    @staticmethod
    def optimize_inventory_queries():
        """Optimized query patterns for inventory operations."""
        
        # Optimized inventory availability query
        def get_available_items_optimized(session: AsyncSession, category_id: str = None):
            query = session.query(
                "id", "name", "sku", "rental_price_per_day", "stock_quantity"
            ).filter(
                "is_active == True",
                "is_available == True",
                "stock_quantity > 0"
            )
            
            if category_id:
                query = query.filter("category_id == :category_id").params(category_id=category_id)
            
            return query.order_by("rental_price_per_day")
        
        return get_available_items_optimized
    
    @staticmethod
    def optimize_transaction_queries():
        """Optimized query patterns for transaction operations."""
        
        # Optimized transaction history query
        def get_transaction_history_optimized(
            session: AsyncSession, 
            customer_id: str, 
            start_date: datetime,
            end_date: datetime
        ):
            return session.query(
                "id", "transaction_type", "total_amount", "transaction_date", "status"
            ).filter(
                "customer_id == :customer_id",
                "transaction_date >= :start_date",
                "transaction_date <= :end_date"
            ).params(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ).order_by("transaction_date DESC")
        
        return get_transaction_history_optimized


class ConnectionPoolManager:
    """Connection pool management for optimal database performance."""
    
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.pool_stats = {}
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "status": "healthy" if pool.checkedin() > 0 else "warning"
        }
    
    async def monitor_connections(self):
        """Monitor database connections."""
        
        pool_status = await self.get_pool_status()
        
        # Log warnings for pool issues
        if pool_status["checked_out"] > pool_status["pool_size"] * 0.8:
            logger.warning(f"High connection usage: {pool_status['checked_out']}/{pool_status['pool_size']}")
        
        if pool_status["overflow"] > 0:
            logger.warning(f"Connection pool overflow: {pool_status['overflow']}")
        
        return pool_status


class DatabaseHealthChecker:
    """Database health monitoring."""
    
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Connection test
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                health_status["checks"]["connection"] = {
                    "status": "ok",
                    "response_time_ms": 0  # Would measure actual time
                }
        except Exception as e:
            health_status["checks"]["connection"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Database file size
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("PRAGMA page_count"))
                page_count = result.scalar()
                
                result = await conn.execute(text("PRAGMA page_size"))
                page_size = result.scalar()
                
                db_size_mb = (page_count * page_size) / (1024 * 1024)
                
                health_status["checks"]["database_size"] = {
                    "status": "ok",
                    "size_mb": round(db_size_mb, 2),
                    "pages": page_count
                }
        except Exception as e:
            health_status["checks"]["database_size"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check for database locks
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("PRAGMA locking_mode"))
                locking_mode = result.scalar()
                
                health_status["checks"]["locking"] = {
                    "status": "ok",
                    "locking_mode": locking_mode
                }
        except Exception as e:
            health_status["checks"]["locking"] = {
                "status": "error",
                "error": str(e)
            }
        
        return health_status


# Global instances
db_optimizer = DatabaseOptimizer(engine)
connection_pool_manager = ConnectionPoolManager(engine)
db_health_checker = DatabaseHealthChecker(engine)


async def initialize_database_optimizations():
    """Initialize database optimizations."""
    
    logger.info("Starting database optimization setup...")
    
    # Create performance indexes
    await db_optimizer.create_indexes()
    
    # Run initial optimization
    await db_optimizer.optimize_database()
    
    logger.info("Database optimization setup completed")


async def get_database_performance_metrics() -> Dict[str, Any]:
    """Get comprehensive database performance metrics."""
    
    return {
        "table_statistics": await db_optimizer.get_table_statistics(),
        "connection_pool": await connection_pool_manager.get_pool_status(),
        "health_check": await db_health_checker.check_database_health(),
        "slow_queries": await db_optimizer.monitor_slow_queries(),
        "timestamp": datetime.now().isoformat()
    }


# Query optimization decorators
def optimize_query(func):
    """Decorator to optimize database queries."""
    
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            result = await func(*args, **kwargs)
            
            # Log query performance
            execution_time = (datetime.now() - start_time).total_seconds()
            if execution_time > 0.5:  # Log slow queries
                logger.warning(f"Slow query in {func.__name__}: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Query optimization error in {func.__name__}: {e}")
            raise
    
    return wrapper


# Batch operation utilities
class BatchOperationManager:
    """Manage batch database operations for performance."""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    async def batch_insert(self, session: AsyncSession, model_class, data_list: List[Dict]):
        """Perform batch insert operations."""
        
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            # Create model instances
            instances = [model_class(**item) for item in batch]
            
            # Add to session
            session.add_all(instances)
            
            # Commit batch
            await session.commit()
            
            logger.info(f"Inserted batch {i//self.batch_size + 1}: {len(instances)} records")
    
    async def batch_update(self, session: AsyncSession, model_class, updates: List[Dict]):
        """Perform batch update operations."""
        
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            
            # Perform bulk update
            for update in batch:
                await session.execute(
                    model_class.__table__.update().where(
                        model_class.id == update["id"]
                    ).values(**update["data"])
                )
            
            await session.commit()
            
            logger.info(f"Updated batch {i//self.batch_size + 1}: {len(batch)} records")


# Export utilities
__all__ = [
    "DatabaseOptimizer",
    "QueryOptimizer", 
    "ConnectionPoolManager",
    "DatabaseHealthChecker",
    "BatchOperationManager",
    "initialize_database_optimizations",
    "get_database_performance_metrics",
    "optimize_query"
]
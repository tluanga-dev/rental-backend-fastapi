"""
Performance monitoring system for rental endpoint optimization.
Tracks metrics, identifies bottlenecks, and provides real-time insights.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import statistics
from collections import defaultdict, deque
from functools import wraps
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PerformanceMetrics:
    """Singleton class to track performance metrics across the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize metrics storage."""
        self.request_times = defaultdict(lambda: deque(maxlen=1000))
        self.query_times = defaultdict(lambda: deque(maxlen=1000))
        self.operation_times = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self.active_requests = 0
        self.start_time = datetime.now()
    
    def record_request(self, endpoint: str, duration: float, success: bool = True):
        """Record API request metrics."""
        self.request_times[endpoint].append({
            'duration': duration,
            'timestamp': datetime.now(),
            'success': success
        })
        
        if success:
            self.success_counts[endpoint] += 1
        else:
            self.error_counts[endpoint] += 1
    
    def record_query(self, query_type: str, duration: float):
        """Record database query metrics."""
        self.query_times[query_type].append({
            'duration': duration,
            'timestamp': datetime.now()
        })
    
    def record_operation(self, operation: str, duration: float, metadata: Dict = None):
        """Record specific operation metrics."""
        self.operation_times[operation].append({
            'duration': duration,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        times = [r['duration'] for r in self.request_times[endpoint]]
        
        if not times:
            return {'error': 'No data available'}
        
        return {
            'endpoint': endpoint,
            'total_requests': len(times),
            'success_count': self.success_counts[endpoint],
            'error_count': self.error_counts[endpoint],
            'average_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'p95_time': self._calculate_percentile(times, 95),
            'p99_time': self._calculate_percentile(times, 99),
            'std_deviation': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        endpoint_stats = {}
        for endpoint in self.request_times:
            endpoint_stats[endpoint] = self.get_endpoint_stats(endpoint)
        
        query_stats = {}
        for query_type in self.query_times:
            times = [q['duration'] for q in self.query_times[query_type]]
            if times:
                query_stats[query_type] = {
                    'count': len(times),
                    'average': statistics.mean(times),
                    'total': sum(times)
                }
        
        return {
            'uptime_seconds': uptime,
            'active_requests': self.active_requests,
            'endpoints': endpoint_stats,
            'queries': query_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


# Global metrics instance
metrics = PerformanceMetrics()


# Decorators for automatic performance tracking
def track_performance(operation_name: str = None):
    """Decorator to track function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                metrics.record_operation(name, duration)
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                metrics.record_operation(name, duration, {'error': str(e)})
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                metrics.record_operation(name, duration)
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                metrics.record_operation(name, duration, {'error': str(e)})
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_query(query_type: str):
    """Decorator to track database query performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                metrics.record_query(query_type, duration)
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                metrics.record_query(f"{query_type}_error", duration)
                raise
        return wrapper
    return decorator


class RentalPerformanceAnalyzer:
    """Specialized analyzer for rental endpoint performance."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def analyze_rental_performance(self) -> Dict[str, Any]:
        """Analyze rental endpoint performance in detail."""
        analysis = {
            'endpoint_metrics': metrics.get_endpoint_stats('/api/transactions/new-rental-optimized'),
            'operation_breakdown': await self._get_operation_breakdown(),
            'database_performance': await self._analyze_database_performance(),
            'recommendations': self._generate_recommendations()
        }
        
        return analysis
    
    async def _get_operation_breakdown(self) -> Dict[str, Any]:
        """Break down performance by operation."""
        operations = [
            'batch_validate_rental_items',
            'batch_get_stock_levels',
            'validate_stock_availability',
            'generate_transaction_number',
            'create_transaction',
            'batch_stock_updates'
        ]
        
        breakdown = {}
        for op in operations:
            op_times = [o['duration'] for o in metrics.operation_times.get(op, [])]
            if op_times:
                breakdown[op] = {
                    'count': len(op_times),
                    'average': statistics.mean(op_times),
                    'percentage': 0  # Will calculate after
                }
        
        # Calculate percentages
        total_time = sum(b['average'] for b in breakdown.values())
        if total_time > 0:
            for op in breakdown:
                breakdown[op]['percentage'] = (breakdown[op]['average'] / total_time) * 100
        
        return breakdown
    
    async def _analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database-specific performance metrics."""
        try:
            # Get connection pool stats
            pool_query = """
            SELECT 
                count(*) as total_connections,
                count(*) filter (where state = 'active') as active_connections,
                count(*) filter (where state = 'idle') as idle_connections,
                count(*) filter (where wait_event_type = 'Lock') as blocked_connections
            FROM pg_stat_activity 
            WHERE datname = current_database()
            """
            pool_result = await self.session.execute(text(pool_query))
            pool_stats = pool_result.fetchone()
            
            # Get cache hit ratio
            cache_query = """
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read) + 0.001) as cache_hit_ratio
            FROM pg_statio_user_tables
            """
            cache_result = await self.session.execute(text(cache_query))
            cache_stats = cache_result.fetchone()
            
            # Get index usage
            index_query = """
            SELECT 
                schemaname,
                tablename,
                100 * idx_scan / (seq_scan + idx_scan + 0.001) as index_usage_percent
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' 
                AND (tablename LIKE 'transaction%' OR tablename LIKE 'stock%')
            ORDER BY index_usage_percent
            """
            index_result = await self.session.execute(text(index_query))
            index_stats = index_result.fetchall()
            
            return {
                'connection_pool': {
                    'total': pool_stats[0] if pool_stats else 0,
                    'active': pool_stats[1] if pool_stats else 0,
                    'idle': pool_stats[2] if pool_stats else 0,
                    'blocked': pool_stats[3] if pool_stats else 0
                },
                'cache_performance': {
                    'hit_ratio': float(cache_stats[2]) if cache_stats else 0,
                    'heap_reads': cache_stats[0] if cache_stats else 0,
                    'heap_hits': cache_stats[1] if cache_stats else 0
                },
                'index_usage': [
                    {
                        'table': row[1],
                        'index_usage_percent': float(row[2])
                    }
                    for row in index_stats
                ]
            }
        except Exception as e:
            return {'error': f'Database analysis failed: {str(e)}'}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on metrics."""
        recommendations = []
        
        # Check endpoint performance
        endpoint_stats = metrics.get_endpoint_stats('/api/transactions/new-rental-optimized')
        if endpoint_stats.get('average_time', 0) > 2.0:
            recommendations.append("Average response time exceeds 2 seconds target")
        
        if endpoint_stats.get('p95_time', 0) > 5.0:
            recommendations.append("95th percentile response time is too high (>5s)")
        
        # Check specific operations
        stock_update_times = [o['duration'] for o in metrics.operation_times.get('batch_stock_updates', [])]
        if stock_update_times and statistics.mean(stock_update_times) > 0.5:
            recommendations.append("Stock update operations are slow - ensure bulk updates are implemented")
        
        # Check error rate
        total_requests = endpoint_stats.get('total_requests', 0)
        error_count = endpoint_stats.get('error_count', 0)
        if total_requests > 0 and (error_count / total_requests) > 0.05:
            recommendations.append(f"High error rate: {(error_count/total_requests)*100:.1f}%")
        
        return recommendations


# API Routes for monitoring
from fastapi import APIRouter, Depends
from app.core.database import get_db

monitoring_router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@monitoring_router.get("/metrics")
async def get_performance_metrics():
    """Get all performance metrics."""
    return metrics.get_all_stats()


@monitoring_router.get("/metrics/rental")
async def get_rental_performance(session: AsyncSession = Depends(get_db)):
    """Get detailed rental endpoint performance analysis."""
    analyzer = RentalPerformanceAnalyzer(session)
    return await analyzer.analyze_rental_performance()


@monitoring_router.get("/metrics/endpoint/{endpoint_path:path}")
async def get_endpoint_metrics(endpoint_path: str):
    """Get metrics for a specific endpoint."""
    endpoint = f"/api/{endpoint_path}"
    return metrics.get_endpoint_stats(endpoint)


@monitoring_router.post("/metrics/reset")
async def reset_metrics():
    """Reset all performance metrics."""
    metrics.initialize()
    return {"message": "Metrics reset successfully"}


# Middleware for automatic request tracking
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track request performance."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip non-API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Track active requests
        metrics.active_requests += 1
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            # Record metrics
            success = 200 <= response.status_code < 400
            metrics.record_request(request.url.path, duration, success)
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            response.headers["X-Server-Time"] = datetime.now().isoformat()
            
            return response
        finally:
            metrics.active_requests -= 1


# Usage example:
"""
# In app/main.py:
from app.modules.monitoring.performance_monitor import monitoring_router, PerformanceTrackingMiddleware

# Add middleware
app.add_middleware(PerformanceTrackingMiddleware)

# Include monitoring routes
app.include_router(monitoring_router)

# In service methods, use decorators:
@track_performance("rental_creation")
async def create_new_rental_optimized(self, rental_data):
    # ... method implementation
    
@track_query("batch_validate_items")
async def _batch_validate_rental_items(self, item_ids):
    # ... method implementation
"""
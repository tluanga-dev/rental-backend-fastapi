"""
Redis caching layer for performance optimization.
Caches frequently accessed data to reduce database load.
"""

import json
import pickle
from typing import Any, Optional, Union, Callable
from datetime import timedelta
from functools import wraps
import hashlib
import asyncio

from redis import asyncio as aioredis
from app.core.config import settings


class CacheManager:
    """Manages Redis cache operations with async support."""
    
    _instance = None
    _redis_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize Redis connection."""
        if not self._redis_client:
            self._redis_client = await aioredis.from_url(
                settings.REDIS_URL or "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding/decoding
                max_connections=50,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 60,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                }
            )
    
    async def get_client(self) -> aioredis.Redis:
        """Get Redis client, initializing if needed."""
        if not self._redis_client:
            await self.initialize()
        return self._redis_client
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        # Create a unique key from arguments
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # For complex objects, use hash
                key_parts.append(hashlib.md5(
                    json.dumps(arg, sort_keys=True, default=str).encode()
                ).hexdigest()[:8])
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await self.get_client()
        try:
            value = await client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            # Log error but don't fail
            print(f"Cache get error for {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds."""
        client = await self.get_client()
        try:
            serialized = pickle.dumps(value)
            await client.setex(key, ttl, serialized)
        except Exception as e:
            # Log error but don't fail
            print(f"Cache set error for {key}: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache."""
        client = await self.get_client()
        try:
            await client.delete(key)
        except Exception as e:
            print(f"Cache delete error for {key}: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        client = await self.get_client()
        try:
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")


# Global cache instance
cache = CacheManager()


# Decorators for caching
def cached(
    prefix: str = None,
    ttl: int = 300,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix (defaults to function name)
        ttl: Time to live in seconds (default 5 minutes)
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_prefix = prefix or f"{func.__module__}.{func.__name__}"
            
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Skip 'self' argument for methods
                cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
                cache_key = cache.generate_key(cache_prefix, *cache_args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(
            cache.generate_key(prefix or f"{func.__module__}.{func.__name__}", *args, **kwargs)
        )
        wrapper.invalidate_pattern = lambda pattern: cache.delete_pattern(pattern)
        
        return wrapper
    return decorator


def cache_aside(
    prefix: str,
    ttl: int = 300,
    serialize_func: Optional[Callable] = None,
    deserialize_func: Optional[Callable] = None
):
    """
    Cache-aside pattern decorator with custom serialization.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = cache.generate_key(prefix, *args[1:], **kwargs)
            
            # Try cache first
            cached_data = await cache.get(cache_key)
            if cached_data is not None:
                if deserialize_func:
                    return deserialize_func(cached_data)
                return cached_data
            
            # Get from source
            result = await func(*args, **kwargs)
            
            # Serialize and cache
            to_cache = serialize_func(result) if serialize_func else result
            await cache.set(cache_key, to_cache, ttl)
            
            return result
        
        return wrapper
    return decorator


# Specialized caching functions for rental operations
class RentalCache:
    """Specialized caching for rental-related data."""
    
    @staticmethod
    @cached(prefix="items:rentable", ttl=600)  # 10 minutes
    async def get_rentable_items(session, item_ids: list):
        """Cache rentable items lookup."""
        from sqlalchemy import select
        from app.modules.master_data.item_master.models import Item
        
        result = await session.execute(
            select(Item).where(
                Item.id.in_([str(id) for id in item_ids]),
                Item.is_rentable == True,
                Item.is_active == True
            )
        )
        return result.scalars().all()
    
    @staticmethod
    @cached(prefix="stock:levels", ttl=60)  # 1 minute for stock levels
    async def get_stock_levels(session, item_ids: list, location_id: str):
        """Cache stock levels lookup with shorter TTL."""
        from sqlalchemy import select, and_
        from app.modules.inventory.models import StockLevel
        
        result = await session.execute(
            select(StockLevel).where(
                and_(
                    StockLevel.item_id.in_([str(id) for id in item_ids]),
                    StockLevel.location_id == str(location_id),
                    StockLevel.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def invalidate_stock_cache(item_ids: list, location_id: str):
        """Invalidate stock cache after updates."""
        for item_id in item_ids:
            await cache.delete(f"stock:levels:{item_id}:{location_id}")
    
    @staticmethod
    @cached(prefix="customer:details", ttl=900)  # 15 minutes
    async def get_customer_details(session, customer_id: str):
        """Cache customer information."""
        from sqlalchemy import select
        from app.modules.customers.models import Customer
        
        result = await session.execute(
            select(Customer).where(Customer.id == str(customer_id))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    @cached(prefix="location:details", ttl=1800)  # 30 minutes
    async def get_location_details(session, location_id: str):
        """Cache location information."""
        from sqlalchemy import select
        from app.modules.master_data.locations.models import Location
        
        result = await session.execute(
            select(Location).where(Location.id == str(location_id))
        )
        return result.scalar_one_or_none()


# Cache warming utilities
class CacheWarmer:
    """Utilities to pre-warm cache with frequently accessed data."""
    
    @staticmethod
    async def warm_item_cache(session):
        """Pre-warm cache with active rentable items."""
        from sqlalchemy import select
        from app.modules.master_data.item_master.models import Item
        
        # Get all active rentable items
        result = await session.execute(
            select(Item).where(
                Item.is_rentable == True,
                Item.is_active == True
            )
        )
        items = result.scalars().all()
        
        # Cache items in batches
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            item_ids = [item.id for item in batch]
            
            # Trigger cache population
            await RentalCache.get_rentable_items(session, item_ids)
    
    @staticmethod
    async def warm_location_cache(session):
        """Pre-warm cache with all active locations."""
        from sqlalchemy import select
        from app.modules.master_data.locations.models import Location
        
        result = await session.execute(
            select(Location).where(Location.is_active == True)
        )
        locations = result.scalars().all()
        
        # Cache each location
        for location in locations:
            await RentalCache.get_location_details(session, location.id)


# Usage example:
"""
# In service methods:
from app.core.cache import cached, RentalCache, cache

class TransactionService:
    @cached(prefix="transaction:summary", ttl=300)
    async def get_transaction_summary(self, transaction_id: str):
        # This result will be cached for 5 minutes
        return await self._fetch_transaction_summary(transaction_id)
    
    async def create_new_rental_optimized(self, rental_data):
        # Use cached lookups
        validated_items = await RentalCache.get_rentable_items(
            self.session, rental_data.item_ids
        )
        
        stock_levels = await RentalCache.get_stock_levels(
            self.session, rental_data.item_ids, rental_data.location_id
        )
        
        # ... create rental ...
        
        # Invalidate relevant caches after update
        await RentalCache.invalidate_stock_cache(
            rental_data.item_ids, rental_data.location_id
        )

# In app startup:
@app.on_event("startup")
async def startup_event():
    await cache.initialize()
    
    # Warm cache with frequently accessed data
    async with AsyncSessionLocal() as session:
        warmer = CacheWarmer()
        await warmer.warm_item_cache(session)
        await warmer.warm_location_cache(session)

@app.on_event("shutdown")
async def shutdown_event():
    await cache.close()
"""
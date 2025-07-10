"""
Middleware for performance optimization and monitoring.

This module provides middleware for caching, performance monitoring, and request tracking.
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional, List
from contextlib import asynccontextmanager
import json
import hashlib

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import settings
# Cache functionality removed for SQLite-only setup
# from app.core.cache import cache_manager, CacheConfig


class CacheMiddleware(BaseHTTPMiddleware):
    """HTTP caching middleware for GET requests (disabled for SQLite-only setup)."""
    
    def __init__(self, app: ASGIApp, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_methods = {"GET"}
        self.cache_headers = {
            "Cache-Control": f"public, max-age={cache_ttl}",
            "X-Cache": "HIT"
        }
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached."""
        # Only cache GET requests
        if request.method not in self.cacheable_methods:
            return False
        
        # Skip caching for requests with sensitive data
        if "authorization" in request.headers:
            return False
        
        # Skip caching for certain paths
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return False
        
        # Skip caching if query parameters indicate dynamic content
        skip_params = ["nocache", "timestamp", "random"]
        if any(param in request.query_params for param in skip_params):
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, and query parameters
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add user context if available (for user-specific caching)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        key_string = "|".join(key_parts)
        return f"http_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching logic (disabled for SQLite-only setup)."""
        # Caching is disabled - just pass through the request
        response = await call_next(request)
        
        # Add cache headers to indicate caching is disabled
        response.headers["X-Cache"] = "DISABLED"
        response.headers["X-Cache-Status"] = "SQLite-only mode"
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and request tracking."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.slow_request_threshold = 1.0  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Track request start time
        start_time = time.time()
        
        # Add request ID to logs context
        request.state.start_time = start_time
        
        # Process request
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            await self._log_slow_request(request, response, duration)
        
        # Update metrics
        await self._update_metrics(request, response, duration)
        
        return response
    
    async def _log_slow_request(self, request: Request, response: Response, duration: float):
        """Log slow request for analysis (cache storage disabled)."""
        slow_request_data = {
            "request_id": request.state.request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration": duration,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": time.time()
        }
        
        # Log to console instead of cache (cache disabled for SQLite-only setup)
        print(f"SLOW REQUEST: {slow_request_data}")
    
    async def _update_metrics(self, request: Request, response: Response, duration: float):
        """Update performance metrics (disabled for SQLite-only setup)."""
        # Metrics storage is disabled - just pass through
        # In production with Redis, this would store metrics in cache
        pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.rate_limit_window = 60  # seconds
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Get IP address for rate limiting
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting (disabled for SQLite-only setup)."""
        # Rate limiting is disabled - just pass through the request
        response = await call_next(request)
        
        # Add headers to indicate rate limiting is disabled
        response.headers["X-RateLimit-Status"] = "DISABLED"
        response.headers["X-RateLimit-Reason"] = "SQLite-only mode"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware."""
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = {
            "application/json",
            "application/javascript",
            "text/html",
            "text/css",
            "text/plain",
            "text/xml"
        }
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False
        
        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply compression to response."""
        response = await call_next(request)
        
        # Disable compression for now to avoid content encoding issues
        # In production, you would implement actual gzip compression here
        # For now, we'll just pass through without compression
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class OpenAPIFixMiddleware(BaseHTTPMiddleware):
    """Middleware to fix OpenAPI JSON response encoding issues."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Fix OpenAPI JSON response encoding."""
        response = await call_next(request)
        
        # For OpenAPI JSON endpoint, ensure no compression headers
        if request.url.path == "/openapi.json":
            # Remove any compression headers using proper method
            if "content-encoding" in response.headers:
                del response.headers["content-encoding"]
            if "content-length" in response.headers:
                del response.headers["content-length"]
            # Ensure correct content type
            response.headers["content-type"] = "application/json"
        
        return response


# Middleware configuration
def setup_middleware(app):
    """Setup all middleware for the application."""
    
    # Add middleware in reverse order (last added = first executed)
    
    # Security headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # OpenAPI fix middleware to prevent content encoding issues
    app.add_middleware(OpenAPIFixMiddleware)
    
    # Performance monitoring
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    # Rate limiting (disabled for SQLite-only setup)
    # app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Compression disabled to avoid content encoding issues
    # app.add_middleware(CompressionMiddleware)
    
    # HTTP caching disabled to avoid content encoding issues
    # if settings.REDIS_ENABLED:
    #     app.add_middleware(CacheMiddleware, cache_ttl=settings.CACHE_TTL)


# Monitoring utilities (disabled for SQLite-only setup)
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics (disabled for SQLite-only setup)."""
    return {
        "status": "cache_disabled",
        "reason": "SQLite-only mode - Redis caching disabled",
        "requests_total": 0,
        "status_codes": {},
        "methods": {}
    }


async def get_slow_requests(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent slow requests (disabled for SQLite-only setup)."""
    return []
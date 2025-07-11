"""
Custom middleware for whitelist enforcement and security.
"""

import logging
import time
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.whitelist import whitelist_manager

logger = logging.getLogger(__name__)


class WhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce whitelist rules for API endpoints."""
    
    def __init__(self, app: ASGIApp, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.rate_limiter: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through whitelist rules."""
        
        if not self.enabled:
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Check CORS origin if present
            origin = request.headers.get("origin")
            if origin and not whitelist_manager.is_origin_allowed(origin):
                logger.warning(f"Blocked request from disallowed origin: {origin}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Origin not allowed"}
                )
            
            # Get the request path
            path = request.url.path
            
            # Check rate limiting
            if self._is_rate_limited(request, path):
                logger.warning(f"Rate limit exceeded for {request.client.host} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log request details
            process_time = time.time() - start_time
            self._log_request(request, response, process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in WhitelistMiddleware: {e}")
            return await call_next(request)
    
    def _is_rate_limited(self, request: Request, path: str) -> bool:
        """Check if request should be rate limited."""
        rate_config = whitelist_manager.get_rate_limiting_config()
        
        if not rate_config.get("enabled", False):
            return False
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._clean_rate_limiter(current_time)
        
        # Check endpoint-specific rate limits
        endpoint_limits = rate_config.get("endpoint_specific", {})
        for endpoint, limits in endpoint_limits.items():
            if self._path_matches(path, endpoint):
                return self._check_rate_limit(
                    client_ip, 
                    endpoint, 
                    limits.get("requests", 100),
                    limits.get("window", "1h"),
                    current_time
                )
        
        # Check global rate limit
        global_limits = rate_config.get("global_rate_limit", {})
        if global_limits:
            return self._check_rate_limit(
                client_ip,
                "global",
                global_limits.get("requests", 1000),
                global_limits.get("window", "1h"),
                current_time
            )
        
        return False
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern."""
        if pattern == path:
            return True
        
        # Simple pattern matching
        if pattern.endswith("/**"):
            return path.startswith(pattern[:-3])
        elif pattern.endswith("/*"):
            prefix = pattern[:-2]
            return path.startswith(prefix) and "/" not in path[len(prefix):]
        
        return False
    
    def _check_rate_limit(self, client_ip: str, endpoint: str, max_requests: int, window: str, current_time: float) -> bool:
        """Check if client has exceeded rate limit for endpoint."""
        window_seconds = self._parse_time_window(window)
        key = f"{client_ip}:{endpoint}"
        
        if key not in self.rate_limiter:
            self.rate_limiter[key] = {
                "requests": [],
                "window_start": current_time
            }
        
        client_data = self.rate_limiter[key]
        
        # Remove old requests outside the window
        window_start = current_time - window_seconds
        client_data["requests"] = [
            req_time for req_time in client_data["requests"] 
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(client_data["requests"]) >= max_requests:
            return True
        
        # Add current request
        client_data["requests"].append(current_time)
        return False
    
    def _parse_time_window(self, window: str) -> int:
        """Parse time window string to seconds."""
        if window.endswith("s"):
            return int(window[:-1])
        elif window.endswith("m"):
            return int(window[:-1]) * 60
        elif window.endswith("h"):
            return int(window[:-1]) * 3600
        elif window.endswith("d"):
            return int(window[:-1]) * 86400
        else:
            return int(window)  # Assume seconds
    
    def _clean_rate_limiter(self, current_time: float) -> None:
        """Clean old entries from rate limiter."""
        # Remove entries older than 1 hour
        cutoff_time = current_time - 3600
        
        keys_to_remove = []
        for key, data in self.rate_limiter.items():
            if not data["requests"] or max(data["requests"]) < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.rate_limiter[key]
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        client = request.client
        return client.host if client else "unknown"
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        security_config = whitelist_manager.get_security_config()
        
        # Add expose headers for CORS
        expose_headers = security_config.get("expose_headers", [])
        if expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)
        
        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
    
    def _log_request(self, request: Request, response: Response, process_time: float) -> None:
        """Log request details."""
        client_ip = self._get_client_ip(request)
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"Client: {client_ip}"
        )


class EndpointAccessMiddleware(BaseHTTPMiddleware):
    """Middleware to control access to specific endpoints based on whitelist configuration."""
    
    def __init__(self, app: ASGIApp, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check endpoint access permissions."""
        
        if not self.enabled:
            return await call_next(request)
        
        path = request.url.path
        
        # Skip middleware for public endpoints
        if whitelist_manager.is_endpoint_public(path):
            return await call_next(request)
        
        # For protected endpoints, check authentication in the actual endpoint
        # This middleware just logs access attempts
        logger.debug(f"Access attempt to protected endpoint: {path}")
        
        return await call_next(request)
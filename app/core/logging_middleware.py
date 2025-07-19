"""
Logging Middleware

This middleware provides comprehensive request/response logging for all API calls,
with special attention to transaction-related endpoints. It tracks timing,
user context, and request details for audit and debugging purposes.
"""

import time
import json
import uuid
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.core.config import settings


class TransactionLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses with focus on transactions.
    
    This middleware:
    - Logs all incoming requests with timing
    - Tracks transaction-related API calls
    - Captures user context and session information
    - Logs response status and errors
    - Provides correlation IDs for request tracking
    """
    
    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = "transaction_api",
        log_level: str = "INFO",
        exclude_paths: Optional[list] = None,
        include_request_body: bool = True,
        include_response_body: bool = False,
        max_body_size: int = 10000
    ):
        """
        Initialize the logging middleware.
        
        Args:
            app: ASGI application
            logger_name: Name of the logger to use
            log_level: Logging level
            exclude_paths: Paths to exclude from logging
            include_request_body: Whether to log request bodies
            include_response_body: Whether to log response bodies
            max_body_size: Maximum body size to log (bytes)
        """
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"
        ]
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
        self.max_body_size = max_body_size
        
        # Transaction-related endpoints that need special tracking
        self.transaction_endpoints = [
            "/api/transactions/sales/new",
            "/api/transactions/purchases/new", 
            "/api/transactions/rentals/new",
            "/api/transactions/rental-returns/",
            "/api/rentals/",
            "/api/transactions/",
        ]
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response with comprehensive logging.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
            
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request context
        request_context = await self._extract_request_context(request)
        
        # Check if this is a transaction-related request
        is_transaction_request = any(
            request.url.path.startswith(endpoint) 
            for endpoint in self.transaction_endpoints
        )
        
        # Log incoming request
        await self._log_request(request, request_context, correlation_id, is_transaction_request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            await self._log_response(
                request, response, request_context, correlation_id, 
                process_time, is_transaction_request
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
            
        except Exception as e:
            # Calculate processing time for error case
            process_time = time.time() - start_time
            
            # Log error
            await self._log_error(
                request, e, request_context, correlation_id, 
                process_time, is_transaction_request
            )
            
            # Re-raise the exception
            raise
            
    async def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        """
        Extract relevant context information from the request.
        
        Args:
            request: HTTP request
            
        Returns:
            Dictionary containing request context
        """
        context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
            "timestamp": time.time()
        }
        
        # Extract user information if available
        if hasattr(request.state, "current_user"):
            context["user_id"] = str(request.state.current_user.id)
            context["username"] = request.state.current_user.username
        
        # Extract session information if available
        if hasattr(request.state, "session_id"):
            context["session_id"] = request.state.session_id
            
        # Extract authorization information
        auth_header = request.headers.get("authorization")
        if auth_header:
            context["auth_type"] = auth_header.split(" ")[0] if " " in auth_header else "unknown"
            context["has_auth"] = True
        else:
            context["has_auth"] = False
            
        return context
        
    async def _log_request(
        self,
        request: Request,
        context: Dict[str, Any],
        correlation_id: str,
        is_transaction: bool
    ) -> None:
        """
        Log incoming request details.
        
        Args:
            request: HTTP request
            context: Request context
            correlation_id: Correlation ID for tracking
            is_transaction: Whether this is a transaction request
        """
        log_data = {
            "event_type": "REQUEST_RECEIVED",
            "correlation_id": correlation_id,
            "method": context["method"],
            "path": context["path"],
            "client_ip": context["client_ip"],
            "user_agent": context["user_agent"],
            "has_auth": context["has_auth"],
            "is_transaction_request": is_transaction,
            "query_params": context["query_params"],
            "timestamp": context["timestamp"]
        }
        
        # Add user context if available
        if "user_id" in context:
            log_data["user_id"] = context["user_id"]
            log_data["username"] = context["username"]
            
        # Add request body for transaction requests if enabled
        # Temporarily disabled for debugging - body consumption causes issues
        # if is_transaction and self.include_request_body:
        #     try:
        #         body = await self._get_request_body(request)
        #         if body and len(body) <= self.max_body_size:
        #             # Try to parse as JSON for better logging
        #             try:
        #                 log_data["request_body"] = json.loads(body)
        #             except json.JSONDecodeError:
        #                 log_data["request_body"] = body[:self.max_body_size]
        #         elif body:
        #             log_data["request_body_truncated"] = True
        #             log_data["request_body_size"] = len(body)
        #     except Exception as e:
        #         log_data["request_body_error"] = str(e)
                
        # Log with appropriate level
        if is_transaction:
            self.logger.info(f"Transaction API Request: {json.dumps(log_data)}")
        else:
            self.logger.debug(f"API Request: {json.dumps(log_data)}")
            
    async def _log_response(
        self,
        request: Request,
        response: Response,
        context: Dict[str, Any],
        correlation_id: str,
        process_time: float,
        is_transaction: bool
    ) -> None:
        """
        Log response details.
        
        Args:
            request: HTTP request
            response: HTTP response
            context: Request context
            correlation_id: Correlation ID for tracking
            process_time: Request processing time
            is_transaction: Whether this is a transaction request
        """
        log_data = {
            "event_type": "REQUEST_COMPLETED",
            "correlation_id": correlation_id,
            "method": context["method"],
            "path": context["path"],
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "is_transaction_request": is_transaction,
            "response_size": len(response.body) if hasattr(response, 'body') else None,
            "timestamp": time.time()
        }
        
        # Add user context if available
        if "user_id" in context:
            log_data["user_id"] = context["user_id"]
            
        # Add response body for transaction requests if enabled and successful
        if (is_transaction and self.include_response_body and 
            200 <= response.status_code < 300):
            try:
                if hasattr(response, 'body') and response.body:
                    body = response.body
                    if len(body) <= self.max_body_size:
                        try:
                            log_data["response_body"] = json.loads(body)
                        except json.JSONDecodeError:
                            log_data["response_body"] = body.decode('utf-8')[:self.max_body_size]
                    else:
                        log_data["response_body_truncated"] = True
            except Exception as e:
                log_data["response_body_error"] = str(e)
                
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        elif is_transaction:
            log_level = "info"
        else:
            log_level = "debug"
            
        # Log the response
        getattr(self.logger, log_level)(
            f"API Response ({response.status_code}): {json.dumps(log_data)}"
        )
        
        # Special logging for transaction completions
        if is_transaction and 200 <= response.status_code < 300:
            self._log_transaction_completion(request, response, context, correlation_id)
            
    async def _log_error(
        self,
        request: Request,
        error: Exception,
        context: Dict[str, Any],
        correlation_id: str,
        process_time: float,
        is_transaction: bool
    ) -> None:
        """
        Log error details.
        
        Args:
            request: HTTP request
            error: Exception that occurred
            context: Request context
            correlation_id: Correlation ID for tracking
            process_time: Request processing time
            is_transaction: Whether this is a transaction request
        """
        log_data = {
            "event_type": "REQUEST_ERROR",
            "correlation_id": correlation_id,
            "method": context["method"],
            "path": context["path"],
            "error_type": type(error).__name__,
            "error_message": str(error),
            "process_time_ms": round(process_time * 1000, 2),
            "is_transaction_request": is_transaction,
            "timestamp": time.time()
        }
        
        # Add user context if available
        if "user_id" in context:
            log_data["user_id"] = context["user_id"]
            
        # Add stack trace for transaction requests
        if is_transaction:
            import traceback
            log_data["stack_trace"] = traceback.format_exc()
            
        self.logger.error(f"API Error: {json.dumps(log_data)}")
        
    def _log_transaction_completion(
        self,
        request: Request,
        response: Response,
        context: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """
        Log successful transaction completion with extracted transaction ID.
        
        Args:
            request: HTTP request
            response: HTTP response
            context: Request context
            correlation_id: Correlation ID for tracking
        """
        try:
            # Try to extract transaction ID from response
            transaction_id = None
            if hasattr(response, 'body') and response.body:
                try:
                    response_data = json.loads(response.body)
                    transaction_id = response_data.get('transaction_id')
                except json.JSONDecodeError:
                    pass
                    
            log_data = {
                "event_type": "TRANSACTION_COMPLETED",
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "endpoint": context["path"],
                "user_id": context.get("user_id"),
                "timestamp": time.time()
            }
            
            self.logger.info(f"Transaction Completed: {json.dumps(log_data)}")
            
        except Exception as e:
            self.logger.warning(f"Failed to log transaction completion: {e}")
            
    async def _get_request_body(self, request: Request) -> Optional[bytes]:
        """
        Extract request body safely and cache it for reuse.
        
        Args:
            request: HTTP request
            
        Returns:
            Request body as bytes or None
        """
        try:
            # Check if body was already read and cached
            if hasattr(request, '_body'):
                return request._body
            
            # Read and cache the body for later use by the endpoint
            body = await request.body()
            request._body = body
            return body
        except Exception:
            return None
            
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
            
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        # Fall back to direct client
        if request.client:
            return request.client.host
            
        return "unknown"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding request context to all requests.
    
    This middleware adds correlation IDs and timing information
    that can be used by other components for logging and tracking.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add context information to the request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with added context
        """
        # Add correlation ID if not already present
        if not hasattr(request.state, "correlation_id"):
            request.state.correlation_id = str(uuid.uuid4())
            
        # Add request start time
        request.state.start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add timing and correlation headers to response
        if hasattr(request.state, "correlation_id"):
            response.headers["X-Correlation-ID"] = request.state.correlation_id
            
        if hasattr(request.state, "start_time"):
            process_time = time.time() - request.state.start_time
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
        return response
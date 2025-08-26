"""
FastAPI Error Handling Middleware
Automatically catches exceptions and converts them to standardized error responses.
"""
import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.error_recovery import error_recovery_manager, ErrorInfo, ErrorClassifier
from src.web.models.error_responses import (
    create_error_response, 
    create_error_from_error_info,
    StandardErrorResponse,
    ErrorResponseType,
    SystemErrorResponse,
    ValidationErrorResponse,
    AuthenticationErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware that provides comprehensive error handling with standardized responses."""
    
    def __init__(self, app: ASGIApp, include_debug_info: bool = False):
        super().__init__(app)
        self.include_debug_info = include_debug_info
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive error handling."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request context for error tracking
        request_context = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except HTTPException as http_exc:
            # Handle FastAPI HTTPExceptions
            return await self._handle_http_exception(http_exc, request_context)
            
        except Exception as exc:
            # Handle all other exceptions
            return await self._handle_general_exception(exc, request_context)
    
    async def _handle_http_exception(self, exc: HTTPException, context: Dict[str, Any]) -> JSONResponse:
        """Handle FastAPI HTTPException with standardized response."""
        request_id = context.get("request_id")
        
        # Create appropriate error response based on status code
        if exc.status_code == 400:
            error_response = ValidationErrorResponse(
                message=exc.detail,
                request_id=request_id
            )
        elif exc.status_code == 401:
            error_response = AuthenticationErrorResponse(
                message=exc.detail,
                request_id=request_id
            )
        elif exc.status_code == 404:
            error_response = NotFoundErrorResponse(
                error_code="RESOURCE_NOT_FOUND",
                message=exc.detail,
                request_id=request_id
            )
        elif exc.status_code == 429:
            error_response = RateLimitErrorResponse(
                message=exc.detail,
                request_id=request_id
            )
        else:
            error_response = SystemErrorResponse(
                message=exc.detail,
                request_id=request_id
            )
        
        # Log the error
        logger.warning(
            f"HTTP Exception {exc.status_code}: {exc.detail}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "context": context
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    async def _handle_general_exception(self, exc: Exception, context: Dict[str, Any]) -> JSONResponse:
        """Handle general exceptions with intelligent classification."""
        request_id = context.get("request_id")
        
        try:
            # Use error classifier to determine appropriate response
            error_info = ErrorClassifier.classify_error(exc, context)
            
            # Add to error history
            error_recovery_manager.error_history.append(error_info)
            
            # Create standardized error response
            error_response = create_error_from_error_info(error_info, request_id)
            
            # Add debug information if enabled
            if self.include_debug_info:
                error_response.context = error_response.context or {}
                error_response.context.update({
                    "exception_type": type(exc).__name__,
                    "traceback": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
                })
            
            # Log the error with appropriate level
            log_level = logging.ERROR if error_info.severity.value in ["high", "critical"] else logging.WARNING
            logger.log(
                log_level,
                f"Exception handled: {error_info.message}",
                extra={
                    "request_id": request_id,
                    "error_category": error_info.category.value,
                    "error_severity": error_info.severity.value,
                    "context": context
                },
                exc_info=log_level == logging.ERROR
            )
            
            # Determine HTTP status code based on error type
            status_code = self._get_status_code_for_error(error_info)
            
            return JSONResponse(
                status_code=status_code,
                content=error_response.dict()
            )
            
        except Exception as handler_exc:
            # If error handling itself fails, return basic error response
            logger.critical(
                f"Error handler failed: {handler_exc}",
                extra={"request_id": request_id, "original_error": str(exc)},
                exc_info=True
            )
            
            fallback_response = SystemErrorResponse(
                message="An unexpected system error occurred",
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=fallback_response.dict()
            )
    
    def _get_status_code_for_error(self, error_info: ErrorInfo) -> int:
        """Determine HTTP status code based on error information."""
        from src.core.error_recovery import ErrorCategory
        
        category_mapping = {
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.TIMEOUT: 504,
            ErrorCategory.NETWORK: 502,
            ErrorCategory.PROCESSING: 422,
            ErrorCategory.STORAGE: 500,
            ErrorCategory.API_ERROR: 502,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.UNKNOWN: 500
        }
        
        return category_mapping.get(error_info.category, 500)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request context to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Add request context and timing information."""
        start_time = datetime.now()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Add context to request state
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Process request
        response = await call_next(request)
        
        # Add timing and request ID to response headers
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = f"{duration_ms:.2f}ms"
        
        return response


# Global exception handlers for specific exception types

async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation exceptions specifically."""
    request_id = getattr(request.state, 'request_id', None)
    
    error_response = ValidationErrorResponse.from_validation_error(exc, request_id)
    
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized responses."""
    request_id = getattr(request.state, 'request_id', None)
    
    # Create appropriate error response
    if exc.status_code == 401:
        error_response = AuthenticationErrorResponse(
            message=exc.detail,
            request_id=request_id
        )
    elif exc.status_code == 404:
        error_response = NotFoundErrorResponse(
            error_code="RESOURCE_NOT_FOUND",
            message=exc.detail,
            request_id=request_id
        )
    elif exc.status_code == 429:
        error_response = RateLimitErrorResponse(
            message=exc.detail,
            request_id=request_id
        )
    else:
        error_response = create_error_response(
            exc, 
            ErrorResponseType.SYSTEM_ERROR, 
            request_id
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


# Utility functions

def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state."""
    return getattr(request.state, 'request_id', None)


def add_error_context(request: Request, context: Dict[str, Any]) -> Dict[str, Any]:
    """Add standard request context to error context."""
    request_context = {
        "method": request.method,
        "url": str(request.url),
        "request_id": get_request_id(request),
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.now().isoformat()
    }
    
    # Merge with provided context
    if context:
        request_context.update(context)
    
    return request_context


# Export middleware and utilities
__all__ = [
    "ErrorHandlingMiddleware",
    "RequestContextMiddleware", 
    "validation_exception_handler",
    "http_exception_handler",
    "get_request_id",
    "add_error_context"
]
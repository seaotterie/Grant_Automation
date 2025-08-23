#!/usr/bin/env python3
"""
Security Middleware for Catalynx
Implements comprehensive security headers and request validation
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import re
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add comprehensive security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "connect-src 'self' ws: wss: https://cdn.jsdelivr.net; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            "X-Permitted-Cross-Domain-Policies": "none"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to protect against XSS attacks"""
    
    def __init__(self, app):
        super().__init__(app)
        # Common XSS attack patterns
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'<object[^>]*>', re.IGNORECASE),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
            re.compile(r'<form[^>]*>', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'expression\s*\(', re.IGNORECASE),
            re.compile(r'<svg[^>]*onload', re.IGNORECASE),
            re.compile(r'<img[^>]*onerror', re.IGNORECASE)
        ]
    
    def _contains_xss(self, text: str) -> bool:
        """Check if text contains potential XSS patterns"""
        if not text:
            return False
        
        # Decode URL encoding
        try:
            decoded_text = unquote(text)
        except:
            decoded_text = text
        
        # Check against XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(decoded_text):
                return True
        
        return False
    
    def _sanitize_dict(self, data: dict, path: str = "") -> dict:
        """Recursively sanitize dictionary data"""
        sanitized = {}
        
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, str):
                if self._contains_xss(value):
                    logger.warning(f"XSS attempt detected in {current_path}: {value[:100]}...")
                    # Remove dangerous content instead of blocking request
                    sanitized[key] = self._sanitize_string(value)
                else:
                    sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value, current_path)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_string(item) if isinstance(item, str) and self._contains_xss(item)
                    else item for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string by removing dangerous content"""
        if not text:
            return text
        
        # Remove script tags and their content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: URLs
        text = re.sub(r'javascript:[^"\']*', '', text, flags=re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r'on\w+\s*=[^"\']*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=[^"\'>\s]*', '', text, flags=re.IGNORECASE)
        
        # Remove dangerous tags
        dangerous_tags = ['iframe', 'object', 'embed', 'form', 'svg']
        for tag in dangerous_tags:
            text = re.sub(f'<{tag}[^>]*>', '', text, flags=re.IGNORECASE)
            text = re.sub(f'</{tag}>', '', text, flags=re.IGNORECASE)
        
        return text
    
    async def dispatch(self, request: Request, call_next):
        # Check request body for XSS patterns
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Only process JSON content
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        try:
                            import json
                            data = json.loads(body)
                            if isinstance(data, dict):
                                sanitized_data = self._sanitize_dict(data)
                                
                                # Replace request body with sanitized data
                                if sanitized_data != data:
                                    logger.info("Request data sanitized for XSS protection")
                                    sanitized_body = json.dumps(sanitized_data)
                                    
                                    # Create new request with sanitized body
                                    async def receive():
                                        return {
                                            "type": "http.request",
                                            "body": sanitized_body.encode()
                                        }
                                    
                                    request._receive = receive
                        except json.JSONDecodeError:
                            pass  # Not JSON, skip processing
            except Exception as e:
                logger.error(f"Error in XSS protection middleware: {e}")
        
        # Check query parameters
        query_params = dict(request.query_params)
        for param, value in query_params.items():
            if self._contains_xss(str(value)):
                logger.warning(f"XSS attempt detected in query parameter {param}: {value}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters"
                )
        
        response = await call_next(request)
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization"""
    
    def __init__(self, app):
        super().__init__(app)
        # Dangerous file path patterns
        self.path_traversal_patterns = [
            re.compile(r'\.\.[\\/]'),  # Directory traversal
            re.compile(r'[\\/]\.\.'),
            re.compile(r'\\x2e\\x2e'),  # URL encoded ..
            re.compile(r'%2e%2e'),
            re.compile(r'\\x2f'),  # URL encoded /
            re.compile(r'%2f'),
            re.compile(r'\\x5c'),  # URL encoded \
            re.compile(r'%5c'),
        ]
        
        # Dangerous input patterns
        self.dangerous_patterns = [
            re.compile(r'/etc/passwd', re.IGNORECASE),
            re.compile(r'windows/system32', re.IGNORECASE),
            re.compile(r'\\x00'),  # Null bytes
            re.compile(r'%00'),
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b)", re.IGNORECASE),
            re.compile(r"';\s*--", re.IGNORECASE),
            re.compile(r"';\s*/\*", re.IGNORECASE),
        ]
    
    def _check_path_traversal(self, value: str) -> bool:
        """Check for path traversal attempts"""
        for pattern in self.path_traversal_patterns:
            if pattern.search(value):
                return True
        return False
    
    def _check_dangerous_input(self, value: str) -> bool:
        """Check for dangerous input patterns"""
        for pattern in self.dangerous_patterns:
            if pattern.search(value):
                return True
        return False
    
    def _check_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns"""
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True
        return False
    
    def _validate_input(self, value: str, field_name: str = "") -> bool:
        """Validate input for security threats"""
        if not value:
            return True
        
        # Check for path traversal
        if self._check_path_traversal(value):
            logger.warning(f"Path traversal attempt detected in {field_name}: {value[:100]}")
            return False
        
        # Check for dangerous patterns
        if self._check_dangerous_input(value):
            logger.warning(f"Dangerous input detected in {field_name}: {value[:100]}")
            return False
        
        # Check for SQL injection
        if self._check_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in {field_name}: {value[:100]}")
            return False
        
        return True
    
    def _validate_dict(self, data: dict, path: str = "") -> bool:
        """Recursively validate dictionary data"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, str):
                if not self._validate_input(value, current_path):
                    return False
            elif isinstance(value, dict):
                if not self._validate_dict(value, current_path):
                    return False
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        if not self._validate_input(item, f"{current_path}[{i}]"):
                            return False
                    elif isinstance(item, dict):
                        if not self._validate_dict(item, f"{current_path}[{i}]"):
                            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for static files and basic routes
        path = request.url.path
        if path.startswith(('/static/', '/favicon.ico')) or path in ('/', '/api/health', '/api/auth/health'):
            response = await call_next(request)
            return response
        
        # Validate URL path for other routes
        if not self._validate_input(path, "url_path"):
            raise HTTPException(
                status_code=400,
                detail="Invalid request path"
            )
        
        # Validate query parameters
        for param, value in request.query_params.items():
            if not self._validate_input(str(value), f"query.{param}"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters"
                )
        
        # Validate request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        try:
                            import json
                            data = json.loads(body)
                            if isinstance(data, dict):
                                if not self._validate_dict(data):
                                    raise HTTPException(
                                        status_code=400,
                                        detail="Invalid request data"
                                    )
                        except json.JSONDecodeError:
                            pass  # Not JSON, skip validation
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                logger.error(f"Error in input validation middleware: {e}")
        
        response = await call_next(request)
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, List[float]] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        minute_ago = now - 60
        
        # Initialize or clean old requests
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []
        
        # Remove old requests outside the window
        self.request_counts[client_id] = [
            timestamp for timestamp in self.request_counts[client_id]
            if timestamp > minute_ago
        ]
        
        # Check if over limit
        if len(self.request_counts[client_id]) >= self.requests_per_minute:
            return True
        
        # Record this request
        self.request_counts[client_id].append(now)
        return False
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        
        if self._is_rate_limited(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.request_counts.get(client_id, [])))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response

# Security utilities
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal"""
    import os
    # Remove directory traversal patterns
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    # Limit length
    filename = filename[:255]
    return filename

def validate_content_type(request: Request, allowed_types: List[str]) -> bool:
    """Validate request content type"""
    content_type = request.headers.get("content-type", "")
    return any(allowed_type in content_type for allowed_type in allowed_types)

def is_safe_redirect_url(url: str, allowed_hosts: Set[str]) -> bool:
    """Check if redirect URL is safe"""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        # Only allow relative URLs or URLs to allowed hosts
        if not parsed.netloc:  # Relative URL
            return True
        
        return parsed.netloc in allowed_hosts
    except:
        return False

# Export main components
__all__ = [
    "SecurityHeadersMiddleware",
    "XSSProtectionMiddleware", 
    "InputValidationMiddleware",
    "RateLimitingMiddleware",
    "sanitize_filename",
    "validate_content_type",
    "is_safe_redirect_url"
]
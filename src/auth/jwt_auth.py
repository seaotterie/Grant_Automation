#!/usr/bin/env python3
"""
JWT Authentication System for Catalynx
Implements secure JWT-based authentication for API endpoints
"""

import jwt
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Security configuration - Load from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable is required. "
        "Please set it in your .env file. "
        "Generate a secure key with: python3 -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()

class User:
    """User model for authentication"""
    
    def __init__(self, user_id: str, username: str, email: str, role: str = "user", 
                 hashed_password: str = "", is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.created_at = datetime.now()
        self.last_login = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class AuthenticationService:
    """JWT Authentication Service"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self._init_default_users()
    
    def _init_default_users(self):
        """Initialize default users from environment variables"""
        # Load credentials from environment - fail if not set
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        user_username = os.getenv("USER_USERNAME", "user")
        user_password = os.getenv("USER_PASSWORD")

        if not admin_password:
            raise ValueError(
                "ADMIN_PASSWORD environment variable is required. "
                "Please set it in your .env file for security."
            )

        if not user_password:
            raise ValueError(
                "USER_PASSWORD environment variable is required. "
                "Please set it in your .env file for security."
            )

        # Create default admin user
        admin_user = User(
            user_id="admin",
            username=admin_username,
            email="admin@catalynx.com",
            role="admin",
            hashed_password=self.hash_password(admin_password),
            is_active=True
        )

        # Create default user
        regular_user = User(
            user_id="user",
            username=user_username,
            email="user@catalynx.com",
            role="user",
            hashed_password=self.hash_password(user_password),
            is_active=True
        )

        self.users[admin_user.username] = admin_user
        self.users[regular_user.username] = regular_user

        logger.info(f"Default users initialized for Catalynx authentication: {admin_username}, {user_username}")
        logger.warning("Remember to change default passwords immediately after first login!")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.users.get(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
            
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.now()
        logger.info(f"User authenticated: {username}")
        return user
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user"""
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
        expire = datetime.utcnow() + expires_delta
        
        token_data = {
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.info(f"Access token created for user: {user.username}")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            
            if username is None:
                return None
            
            # Check if user still exists and is active
            user = self.users.get(username)
            if not user or not user.is_active:
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return None
    
    def get_current_user(self, token_payload: Dict[str, Any]) -> Optional[User]:
        """Get current user from token payload"""
        username = token_payload.get("sub")
        if username:
            return self.users.get(username)
        return None

# Global authentication service instance
auth_service = AuthenticationService()

async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth_service.get_current_user(payload)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

async def get_admin_user_dependency(current_user: User = Depends(get_current_user_dependency)) -> User:
    """FastAPI dependency to ensure current user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

def require_auth(roles: List[str] = None):
    """Decorator to require authentication with optional role requirements"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need to be implemented based on your specific framework
            # For FastAPI, use the dependencies above
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class AuthenticationError(Exception):
    """Authentication error exception"""
    pass

class AuthorizationError(Exception):
    """Authorization error exception"""
    pass

# Authentication utilities
def generate_api_key() -> str:
    """Generate secure API key for service-to-service authentication"""
    return secrets.token_urlsafe(32)

def validate_api_key(api_key: str) -> bool:
    """Validate API key (placeholder for future implementation)"""
    # TODO: Implement API key validation against database
    return len(api_key) >= 32

def get_user_permissions(user: User) -> List[str]:
    """Get user permissions based on role"""
    role_permissions = {
        "admin": [
            "read:profiles",
            "write:profiles", 
            "delete:profiles",
            "read:discovery",
            "write:discovery",
            "read:analytics",
            "write:analytics",
            "admin:system"
        ],
        "user": [
            "read:profiles",
            "write:profiles",
            "read:discovery",
            "write:discovery",
            "read:analytics"
        ]
    }
    
    return role_permissions.get(user.role, [])

def check_permission(user: User, required_permission: str) -> bool:
    """Check if user has required permission"""
    user_permissions = get_user_permissions(user)
    return required_permission in user_permissions

# Security headers helper
def get_security_headers() -> Dict[str, str]:
    """Get security headers to add to responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self';",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

# Rate limiting support (basic implementation)
class RateLimiter:
    """Basic rate limiter for authentication endpoints"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts: Dict[str, List[datetime]] = {}
    
    def is_rate_limited(self, identifier: str) -> bool:
        """Check if identifier is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Get attempts for this identifier
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Remove old attempts outside window
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if attempt > window_start
        ]
        
        # Check if rate limited
        return len(self.attempts[identifier]) >= self.max_attempts
    
    def record_attempt(self, identifier: str):
        """Record an authentication attempt"""
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier].append(datetime.now())

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Use IP address as identifier
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# Export main components
__all__ = [
    "User",
    "AuthenticationService", 
    "auth_service",
    "get_current_user_dependency",
    "get_admin_user_dependency",
    "AuthenticationError",
    "AuthorizationError",
    "get_security_headers",
    "RateLimiter", 
    "rate_limiter",
    "get_client_identifier"
]
#!/usr/bin/env python3
"""
Authentication Routes for Catalynx
Implements login, logout, and user management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging

from src.auth.jwt_auth import (
    auth_service, 
    User, 
    get_current_user_dependency,
    get_admin_user_dependency,
    rate_limiter,
    get_client_identifier
)

logger = logging.getLogger(__name__)

# Create router for authentication endpoints
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    expires_in: int = 86400  # 24 hours in seconds

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"

class SystemStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    permissions: Optional[list] = None

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, request: Request):
    """
    Authenticate user and return JWT token
    """
    client_id = get_client_identifier(request)
    
    # Check rate limiting
    if rate_limiter.is_rate_limited(client_id):
        logger.warning(f"Rate limit exceeded for login attempt from {client_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": "900"}  # 15 minutes
        )
    
    # Record the attempt
    rate_limiter.record_attempt(client_id)
    
    # Authenticate user
    user = auth_service.authenticate_user(login_request.username, login_request.password)
    
    if not user:
        logger.warning(f"Failed login attempt for username: {login_request.username} from {client_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create access token
    access_token = auth_service.create_access_token(user)
    
    logger.info(f"Successful login for user: {user.username} from {client_id}")
    
    return LoginResponse(
        access_token=access_token,
        user=user.to_dict()
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user_dependency)):
    """
    Logout user (token-based logout would require token blacklisting)
    """
    logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user_dependency)):
    """
    Get current authenticated user information
    """
    return UserResponse(**current_user.to_dict())

@router.get("/status", response_model=SystemStatusResponse)
async def get_auth_status(request: Request):
    """
    Get authentication status without requiring authentication
    """
    try:
        # Try to get user from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = auth_service.verify_token(token)
            
            if payload:
                user = auth_service.get_current_user(payload)
                if user:
                    from src.auth.jwt_auth import get_user_permissions
                    permissions = get_user_permissions(user)
                    
                    return SystemStatusResponse(
                        authenticated=True,
                        user=UserResponse(**user.to_dict()),
                        permissions=permissions
                    )
        
        return SystemStatusResponse(authenticated=False)
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return SystemStatusResponse(authenticated=False)

@router.put("/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Change user password
    """
    # Verify current password
    if not auth_service.verify_password(password_request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = auth_service.hash_password(password_request.new_password)
    
    logger.info(f"Password changed for user: {current_user.username}")
    
    return {"message": "Password changed successfully"}

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_request: CreateUserRequest,
    admin_user: User = Depends(get_admin_user_dependency)
):
    """
    Create new user (admin only)
    """
    # Check if username already exists
    if user_request.username in auth_service.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    new_user = User(
        user_id=user_request.username,  # Simple ID for now
        username=user_request.username,
        email=user_request.email,
        role=user_request.role,
        hashed_password=auth_service.hash_password(user_request.password),
        is_active=True
    )
    
    # Add to users
    auth_service.users[new_user.username] = new_user
    
    logger.info(f"New user created: {new_user.username} by admin: {admin_user.username}")
    
    return UserResponse(**new_user.to_dict())

@router.get("/users", response_model=list[UserResponse])
async def list_users(admin_user: User = Depends(get_admin_user_dependency)):
    """
    List all users (admin only)
    """
    users = [UserResponse(**user.to_dict()) for user in auth_service.users.values()]
    return users

@router.delete("/users/{username}")
async def delete_user(
    username: str,
    admin_user: User = Depends(get_admin_user_dependency)
):
    """
    Delete user (admin only)
    """
    if username not in auth_service.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if username == admin_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    del auth_service.users[username]
    
    logger.info(f"User deleted: {username} by admin: {admin_user.username}")
    
    return {"message": f"User {username} deleted successfully"}

@router.put("/users/{username}/activate")
async def activate_user(
    username: str,
    admin_user: User = Depends(get_admin_user_dependency)
):
    """
    Activate user account (admin only)
    """
    if username not in auth_service.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    auth_service.users[username].is_active = True
    
    logger.info(f"User activated: {username} by admin: {admin_user.username}")
    
    return {"message": f"User {username} activated successfully"}

@router.put("/users/{username}/deactivate")
async def deactivate_user(
    username: str,
    admin_user: User = Depends(get_admin_user_dependency)
):
    """
    Deactivate user account (admin only)
    """
    if username not in auth_service.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if username == admin_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    auth_service.users[username].is_active = False
    
    logger.info(f"User deactivated: {username} by admin: {admin_user.username}")
    
    return {"message": f"User {username} deactivated successfully"}

# Health check endpoint (no authentication required)
@router.get("/health")
async def auth_health():
    """
    Authentication service health check
    """
    return {
        "status": "healthy",
        "service": "Authentication Service",
        "version": "1.0.0",
        "users_count": len(auth_service.users),
        "default_users_available": "admin" in auth_service.users and "user" in auth_service.users
    }
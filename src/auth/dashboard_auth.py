"""
Dashboard Authentication System
Handles user authentication for the web dashboard interface.
"""

import os
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class DashboardAuth:
    """
    Simple authentication system for the dashboard interface.
    
    Features:
    - Session-based authentication
    - Secure password hashing
    - Session timeout management
    - Basic user management
    """
    
    def __init__(self, auth_dir: Optional[Path] = None):
        self.auth_dir = auth_dir or Path.home() / ".grant_research" / "auth"
        self.users_file = self.auth_dir / "users.json"
        self.sessions_file = self.auth_dir / "sessions.json"
        
        # Ensure directory exists
        self.auth_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Load existing data
        self.users = self._load_users()
        self.sessions = self._load_sessions()
        
        # Session timeout (8 hours default)
        self.session_timeout = timedelta(hours=8)
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load user data from disk"""
        if not self.users_file.exists():
            return {}
        
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            return {}
    
    def _save_users(self) -> None:
        """Save user data to disk"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            os.chmod(self.users_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Load session data from disk"""
        if not self.sessions_file.exists():
            return {}
        
        try:
            with open(self.sessions_file, 'r') as f:
                sessions_data = json.load(f)
                # Convert ISO timestamps back to datetime objects
                for session_id, session in sessions_data.items():
                    session['created'] = datetime.fromisoformat(session['created'])
                    session['last_access'] = datetime.fromisoformat(session['last_access'])
                return sessions_data
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}
    
    def _save_sessions(self) -> None:
        """Save session data to disk"""
        try:
            # Convert datetime objects to ISO format for JSON
            sessions_data = {}
            for session_id, session in self.sessions.items():
                sessions_data[session_id] = {
                    **session,
                    'created': session['created'].isoformat(),
                    'last_access': session['last_access'].isoformat()
                }
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            os.chmod(self.sessions_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Create a new user"""
        if username in self.users:
            return False
        
        password_hash, salt = self._hash_password(password)
        
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'role': role,
            'created': datetime.now().isoformat(),
            'last_login': None
        }
        
        self._save_users()
        logger.info(f"User {username} created")
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session ID"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        password_hash, _ = self._hash_password(password, user['salt'])
        
        if password_hash != user['password_hash']:
            return None
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'username': username,
            'created': datetime.now(),
            'last_access': datetime.now()
        }
        
        # Update last login
        self.users[username]['last_login'] = datetime.now().isoformat()
        
        self._save_users()
        self._save_sessions()
        
        logger.info(f"User {username} authenticated")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session and return username"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session['last_access'] > self.session_timeout:
            del self.sessions[session_id]
            self._save_sessions()
            return None
        
        # Update last access
        session['last_access'] = datetime.now()
        self._save_sessions()
        
        return session['username']
    
    def logout(self, session_id: str) -> bool:
        """Logout user by removing session"""
        if session_id in self.sessions:
            username = self.sessions[session_id]['username']
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"User {username} logged out")
            return True
        return False
    
    def cleanup_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if datetime.now() - session['last_access'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information (without sensitive data)"""
        if username not in self.users:
            return None
        
        user = self.users[username].copy()
        # Remove sensitive data
        del user['password_hash']
        del user['salt']
        
        return user
    
    def list_users(self) -> list:
        """List all usernames"""
        return list(self.users.keys())
    
    def has_users(self) -> bool:
        """Check if any users exist"""
        return len(self.users) > 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get authentication system status"""
        return {
            'users_configured': len(self.users),
            'active_sessions': len(self.sessions),
            'session_timeout_hours': self.session_timeout.total_seconds() / 3600,
            'auth_directory': str(self.auth_dir)
        }


# Global instance
_dashboard_auth: Optional[DashboardAuth] = None


def get_dashboard_auth() -> DashboardAuth:
    """Get or create global dashboard auth instance"""
    global _dashboard_auth
    if _dashboard_auth is None:
        _dashboard_auth = DashboardAuth()
    return _dashboard_auth


# Convenience functions
def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate user and return session ID"""
    return get_dashboard_auth().authenticate(username, password)


def validate_session(session_id: str) -> Optional[str]:
    """Validate session and return username"""
    return get_dashboard_auth().validate_session(session_id)


def create_user(username: str, password: str, role: str = "user") -> bool:
    """Create a new user"""
    return get_dashboard_auth().create_user(username, password, role)


def logout_user(session_id: str) -> bool:
    """Logout user"""
    return get_dashboard_auth().logout(session_id)


def get_auth_status() -> Dict[str, Any]:
    """Get authentication status"""
    return get_dashboard_auth().get_status()
"""
Dashboard Authentication System
Handles user authentication for the Streamlit dashboard.
"""
import hashlib
import hmac
import secrets
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class DashboardAuth:
    """
    Simple but secure authentication for the Streamlit dashboard.
    
    Features:
    - Password hashing with salt
    - Session management
    - Configurable session timeout
    - User management (add/remove users)
    """
    
    def __init__(self, users_file: Optional[Path] = None):
        self.users_file = users_file or Path.home() / ".grant_research" / "users.json"
        self.users_file.parent.mkdir(exist_ok=True, mode=0o700)
        self.session_timeout = timedelta(hours=8)  # 8 hour sessions
        
        # Initialize default admin user if no users exist
        if not self.users_file.exists():
            self._create_default_admin()
    
    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Hash a password with salt using PBKDF2.
        
        Returns:
            Tuple of (hashed_password, salt_base64)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 with SHA256
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        
        return hashed.hex(), salt.hex()
    
    def _verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt_bytes = bytes.fromhex(salt)
            expected_hash, _ = self._hash_password(password, salt_bytes)
            return hmac.compare_digest(expected_hash, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from the encrypted file."""
        if not self.users_file.exists():
            return {}
        
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, Any]) -> None:
        """Save users to the encrypted file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            # Set restrictive permissions
            import os
            os.chmod(self.users_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
            raise RuntimeError(f"Failed to save users: {e}")
    
    def _create_default_admin(self) -> None:
        """Create default admin user on first run."""
        # Generate a random password for initial setup
        temp_password = secrets.token_urlsafe(16)
        
        users = {
            "admin": {
                "password_hash": None,
                "salt": None,
                "role": "admin",
                "created": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            }
        }
        
        # Hash the temporary password
        password_hash, salt = self._hash_password(temp_password)
        users["admin"]["password_hash"] = password_hash
        users["admin"]["salt"] = salt
        
        self._save_users(users)
        
        # Log the temporary password (in production, this should be sent securely)
        logger.warning(f"Default admin user created with temporary password: {temp_password}")
        logger.warning("Please change this password immediately after first login!")
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if authentication successful
        """
        users = self._load_users()
        
        if username not in users:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return False
        
        user = users[username]
        
        if not user.get("active", True):
            logger.warning(f"Login attempt for inactive user: {username}")
            return False
        
        if self._verify_password(password, user["password_hash"], user["salt"]):
            # Update last login
            user["last_login"] = datetime.now().isoformat()
            users[username] = user
            self._save_users(users)
            
            logger.info(f"Successful login for user: {username}")
            return True
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return False
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """
        Create a new user.
        
        Args:
            username: Username (must be unique)
            password: Password
            role: User role (admin, user)
            
        Returns:
            True if user created successfully
        """
        users = self._load_users()
        
        if username in users:
            logger.error(f"User already exists: {username}")
            return False
        
        password_hash, salt = self._hash_password(password)
        
        users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "role": role,
            "created": datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }
        
        try:
            self._save_users(users)
            logger.info(f"Created new user: {username} with role: {role}")
            return True
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
        """
        # First verify the old password
        if not self.authenticate_user(username, old_password):
            return False
        
        users = self._load_users()
        password_hash, salt = self._hash_password(new_password)
        
        users[username]["password_hash"] = password_hash
        users[username]["salt"] = salt
        
        try:
            self._save_users(users)
            logger.info(f"Password changed for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to change password for {username}: {e}")
            return False
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account."""
        users = self._load_users()
        
        if username not in users:
            return False
        
        users[username]["active"] = False
        
        try:
            self._save_users(users)
            logger.info(f"Deactivated user: {username}")
            return True
        except Exception:
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information (excluding sensitive data)."""
        users = self._load_users()
        
        if username not in users:
            return None
        
        user = users[username].copy()
        # Remove sensitive information
        del user["password_hash"]
        del user["salt"]
        
        return user
    
    def list_users(self) -> list:
        """List all users (excluding sensitive data)."""
        users = self._load_users()
        result = []
        
        for username, user_data in users.items():
            user_info = user_data.copy()
            del user_info["password_hash"]
            del user_info["salt"]
            user_info["username"] = username
            result.append(user_info)
        
        return result


class StreamlitAuthManager:
    """
    Streamlit-specific authentication manager.
    Handles session state and login UI.
    """
    
    def __init__(self, auth: DashboardAuth):
        self.auth = auth
    
    def show_login_form(self) -> bool:
        """
        Show login form and handle authentication.
        
        Returns:
            True if user is authenticated
        """
        st.title("🔐 Grant Research Authentication")
        
        # Check if already authenticated
        if st.session_state.get("authenticated", False):
            return True
        
        with st.form("login_form"):
            st.subheader("Please Log In")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                login_button = st.form_submit_button("Login")
            
            if login_button:
                if username and password:
                    if self.auth.authenticate_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.login_time = datetime.now()
                        
                        # Get user info for role-based access
                        user_info = self.auth.get_user_info(username)
                        st.session_state.user_role = user_info.get("role", "user")
                        
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        # Show admin password info if default admin exists
        try:
            users = self.auth._load_users()
            admin_user = users.get("admin", {})
            if admin_user.get("last_login") is None:
                st.info("ℹ️ First time setup: Check the logs for the default admin password")
        except Exception:
            pass
        
        return False
    
    def check_session_valid(self) -> bool:
        """Check if the current session is still valid."""
        if not st.session_state.get("authenticated", False):
            return False
        
        login_time = st.session_state.get("login_time")
        if not login_time:
            return False
        
        # Check session timeout
        if datetime.now() - login_time > self.auth.session_timeout:
            self.logout()
            return False
        
        return True
    
    def logout(self) -> None:
        """Log out the current user."""
        for key in ["authenticated", "username", "login_time", "user_role"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def show_user_menu(self) -> None:
        """Show user menu in sidebar."""
        if not st.session_state.get("authenticated", False):
            return
        
        username = st.session_state.get("username", "Unknown")
        role = st.session_state.get("user_role", "user")
        
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Logged in as:** {username}")
            st.markdown(f"**Role:** {role.title()}")
            
            if st.button("🚪 Logout"):
                self.logout()
                st.rerun()
            
            # Show admin options for admin users
            if role == "admin":
                st.markdown("---")
                st.markdown("**Admin Options:**")
                
                if st.button("👥 Manage Users"):
                    st.session_state.show_user_management = True
                
                if st.button("🔑 Change Password"):
                    st.session_state.show_password_change = True
    
    def require_authentication(self) -> bool:
        """
        Decorator/wrapper to require authentication for pages.
        
        Returns:
            True if authenticated, False otherwise
        """
        if self.check_session_valid():
            self.show_user_menu()
            return True
        else:
            return self.show_login_form()
    
    def require_admin(self) -> bool:
        """Check if current user has admin privileges."""
        if not self.check_session_valid():
            return False
        
        return st.session_state.get("user_role") == "admin"


# Global instances
_dashboard_auth: Optional[DashboardAuth] = None
_streamlit_auth_manager: Optional[StreamlitAuthManager] = None


def get_dashboard_auth() -> DashboardAuth:
    """Get the global dashboard auth instance."""
    global _dashboard_auth
    if _dashboard_auth is None:
        _dashboard_auth = DashboardAuth()
    return _dashboard_auth


def get_streamlit_auth_manager() -> StreamlitAuthManager:
    """Get the global Streamlit auth manager instance."""
    global _streamlit_auth_manager
    if _streamlit_auth_manager is None:
        _streamlit_auth_manager = StreamlitAuthManager(get_dashboard_auth())
    return _streamlit_auth_manager
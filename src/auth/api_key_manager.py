"""
Secure API Key Management System
Handles encrypted storage and retrieval of API keys for external services.
"""
import os
import json
import base64
from typing import Dict, Optional, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Secure API key management with encryption at rest.
    
    Features:
    - Password-based encryption of API keys
    - Environment variable fallback
    - Automatic key derivation from master password
    - Secure storage in encrypted JSON file
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".grant_research" / "api_keys.enc"
        self.storage_path.parent.mkdir(exist_ok=True, mode=0o700)
        self._fernet: Optional[Fernet] = None
        self._keys_cache: Dict[str, str] = {}
    
    def _get_encryption_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _initialize_encryption(self, password: str) -> None:
        """Initialize Fernet encryption with user password."""
        if self.storage_path.exists():
            # Load existing salt
            with open(self.storage_path, 'rb') as f:
                data = json.loads(f.read().decode())
                salt = base64.b64decode(data['salt'])
        else:
            # Generate new salt for new installation
            salt = os.urandom(16)
            # Create initial encrypted file structure
            key = self._get_encryption_key(password, salt)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json.dumps({}).encode())
            
            initial_data = {
                'salt': base64.b64encode(salt).decode(),
                'data': encrypted_data.decode()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(initial_data, f)
            
            # Set restrictive permissions
            os.chmod(self.storage_path, 0o600)
        
        key = self._get_encryption_key(password, salt)
        self._fernet = Fernet(key)
    
    def authenticate(self, password: Optional[str] = None) -> bool:
        """
        Authenticate and initialize encryption.
        
        Args:
            password: Master password. If None, prompts user.
            
        Returns:
            True if authentication successful, False otherwise
        """
        if not password:
            password = getpass.getpass("Enter master password for API keys: ")
        
        try:
            self._initialize_encryption(password)
            
            # Test decryption with existing file
            if self.storage_path.exists():
                self._load_keys()
            
            logger.info("API key manager authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._fernet = None
            return False
    
    def _load_keys(self) -> Dict[str, str]:
        """Load and decrypt API keys from storage."""
        if not self._fernet:
            raise RuntimeError("Not authenticated - call authenticate() first")
        
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            encrypted_data = data['data'].encode()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())
            
            self._keys_cache = keys
            return keys
            
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            raise RuntimeError(f"Failed to decrypt API keys: {e}")
    
    def _save_keys(self, keys: Dict[str, str]) -> None:
        """Encrypt and save API keys to storage."""
        if not self._fernet:
            raise RuntimeError("Not authenticated - call authenticate() first")
        
        try:
            # Read existing salt
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    existing_data = json.load(f)
                    salt = existing_data['salt']
            else:
                salt = base64.b64encode(os.urandom(16)).decode()
            
            # Encrypt the keys
            encrypted_data = self._fernet.encrypt(json.dumps(keys).encode())
            
            # Save to file
            data = {
                'salt': salt,
                'data': encrypted_data.decode()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f)
            
            os.chmod(self.storage_path, 0o600)
            self._keys_cache = keys.copy()
            
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
            raise RuntimeError(f"Failed to encrypt and save API keys: {e}")
    
    def set_api_key(self, service: str, api_key: str) -> None:
        """
        Store an API key for a service.
        
        Args:
            service: Service name (e.g., 'propublica', 'openai')
            api_key: The API key to store
        """
        if not self._fernet:
            raise RuntimeError("Not authenticated - call authenticate() first")
        
        keys = self._load_keys()
        keys[service] = api_key
        self._save_keys(keys)
        
        logger.info(f"API key stored for service: {service}")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Retrieve an API key for a service.
        
        Args:
            service: Service name
            
        Returns:
            API key if found, None otherwise
        """
        # First check environment variables (for development/CI)
        env_var = f"{service.upper()}_API_KEY"
        env_key = os.getenv(env_var)
        if env_key:
            return env_key
        
        # Then check encrypted storage
        if not self._fernet:
            logger.warning("API key manager not authenticated")
            return None
        
        try:
            keys = self._keys_cache or self._load_keys()
            return keys.get(service)
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service}: {e}")
            return None
    
    def list_services(self) -> list:
        """List all services with stored API keys."""
        if not self._fernet:
            return []
        
        try:
            keys = self._keys_cache or self._load_keys()
            return list(keys.keys())
        except Exception:
            return []
    
    def remove_api_key(self, service: str) -> bool:
        """
        Remove an API key for a service.
        
        Args:
            service: Service name
            
        Returns:
            True if key was removed, False if not found
        """
        if not self._fernet:
            raise RuntimeError("Not authenticated - call authenticate() first")
        
        keys = self._load_keys()
        if service in keys:
            del keys[service]
            self._save_keys(keys)
            logger.info(f"API key removed for service: {service}")
            return True
        
        return False
    
    def validate_key(self, service: str) -> bool:
        """
        Validate that an API key exists and is non-empty.
        
        Args:
            service: Service name
            
        Returns:
            True if key exists and is valid
        """
        key = self.get_api_key(service)
        return key is not None and len(key.strip()) > 0


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


# Convenience functions
def get_api_key(service: str) -> Optional[str]:
    """Get API key for a service."""
    return get_api_key_manager().get_api_key(service)


def set_api_key(service: str, api_key: str) -> None:
    """Set API key for a service."""
    get_api_key_manager().set_api_key(service, api_key)


def authenticate_api_keys(password: Optional[str] = None) -> bool:
    """Authenticate the API key manager."""
    return get_api_key_manager().authenticate(password)
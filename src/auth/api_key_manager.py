"""
Secure API Key Management System
Handles encrypted storage and retrieval of API keys for external services.
"""
import os
import json
import base64
import hashlib
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime, timedelta
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
        self.audit_path = self.storage_path.parent / "api_audit.log"
        self.metadata_path = self.storage_path.parent / "api_metadata.enc"
        self.storage_path.parent.mkdir(exist_ok=True, mode=0o700)
        self._fernet: Optional[Fernet] = None
        self._keys_cache: Dict[str, str] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
    
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
        
        # Load metadata cache
        self._load_metadata()
    
    def _create_audit_hash(self, operation: str, service: str, success: bool) -> str:
        """Create encrypted audit hash for logging"""
        audit_data = f"{datetime.now().isoformat()}:{operation}:{service}:{success}"
        return hashlib.sha256(audit_data.encode()).hexdigest()[:16]
    
    def _log_audit_event(self, operation: str, service: str, success: bool = True, details: str = ""):
        """Log audit event with encrypted hash"""
        try:
            audit_hash = self._create_audit_hash(operation, service, success)
            timestamp = datetime.now().isoformat()
            
            audit_entry = {
                "timestamp": timestamp,
                "operation": operation,
                "service": service,
                "success": success,
                "audit_hash": audit_hash,
                "details": details
            }
            
            # Append to audit log
            with open(self.audit_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            os.chmod(self.audit_path, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _load_metadata(self) -> None:
        """Load key metadata (creation dates, rotation info)"""
        if not self.metadata_path.exists() or not self._fernet:
            self._metadata_cache = {}
            return
        
        try:
            with open(self.metadata_path, 'r') as f:
                data = json.load(f)
            
            encrypted_data = data['data'].encode()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            metadata = json.loads(decrypted_data.decode())
            
            # Convert ISO dates back to datetime objects
            for service, info in metadata.items():
                if 'created_date' in info:
                    info['created_date'] = datetime.fromisoformat(info['created_date'])
                if 'last_rotated' in info:
                    info['last_rotated'] = datetime.fromisoformat(info['last_rotated'])
            
            self._metadata_cache = metadata
            
        except Exception as e:
            logger.warning(f"Failed to load key metadata: {e}")
            self._metadata_cache = {}
    
    def _save_metadata(self) -> None:
        """Save key metadata with encryption"""
        if not self._fernet:
            return
        
        try:
            # Convert datetime objects to ISO format
            metadata_for_storage = {}
            for service, info in self._metadata_cache.items():
                storage_info = info.copy()
                if 'created_date' in storage_info:
                    storage_info['created_date'] = storage_info['created_date'].isoformat()
                if 'last_rotated' in storage_info:
                    storage_info['last_rotated'] = storage_info['last_rotated'].isoformat()
                metadata_for_storage[service] = storage_info
            
            # Read existing salt or create new one
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    existing_data = json.load(f)
                    salt = existing_data['salt']
            else:
                salt = base64.b64encode(os.urandom(16)).decode()
            
            # Encrypt metadata
            encrypted_data = self._fernet.encrypt(json.dumps(metadata_for_storage).encode())
            
            # Save to file
            data = {
                'salt': salt,
                'data': encrypted_data.decode()
            }
            
            with open(self.metadata_path, 'w') as f:
                json.dump(data, f)
            
            os.chmod(self.metadata_path, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
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
        Store an API key for a service with audit logging and metadata tracking.
        
        Args:
            service: Service name (e.g., 'propublica', 'openai')
            api_key: The API key to store
        """
        if not self._fernet:
            raise RuntimeError("Not authenticated - call authenticate() first")
        
        try:
            # Load existing keys and metadata
            keys = self._load_keys()
            is_new_key = service not in keys
            is_rotation = not is_new_key and keys[service] != api_key
            
            # Update key
            keys[service] = api_key
            self._save_keys(keys)
            
            # Update metadata
            current_time = datetime.now()
            if service not in self._metadata_cache:
                self._metadata_cache[service] = {}
            
            metadata = self._metadata_cache[service]
            
            if is_new_key:
                metadata['created_date'] = current_time
                metadata['rotation_count'] = 0
                operation = "key_created"
            elif is_rotation:
                metadata['last_rotated'] = current_time
                metadata['rotation_count'] = metadata.get('rotation_count', 0) + 1
                operation = "key_rotated"
            else:
                operation = "key_updated"
            
            # Save metadata
            self._save_metadata()
            
            # Log audit event
            details = f"Service: {service}"
            if is_rotation:
                details += f", Rotation #{metadata['rotation_count']}"
            
            self._log_audit_event(operation, service, True, details)
            
            logger.info(f"API key {'created' if is_new_key else 'rotated' if is_rotation else 'updated'} for service: {service}")
            
        except Exception as e:
            self._log_audit_event("key_storage_failed", service, False, str(e))
            raise
    
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
    
    def check_rotation_alerts(self) -> List[Dict[str, Any]]:
        """Check for API keys that need rotation"""
        alerts = []
        
        for service, metadata in self._metadata_cache.items():
            config = SERVICE_CONFIGS.get(service, {})
            rotation_days = config.get('rotation_days', 30)
            
            created_date = metadata.get('created_date')
            last_rotated = metadata.get('last_rotated', created_date)
            
            if last_rotated:
                days_since_rotation = (datetime.now() - last_rotated).days
                
                if days_since_rotation >= rotation_days:
                    alerts.append({
                        'service': service,
                        'service_name': config.get('name', service),
                        'days_overdue': days_since_rotation - rotation_days,
                        'last_rotated': last_rotated.isoformat(),
                        'rotation_count': metadata.get('rotation_count', 0),
                        'severity': 'critical' if days_since_rotation > rotation_days + 7 else 'warning'
                    })
                elif days_since_rotation >= rotation_days - 5:
                    alerts.append({
                        'service': service,
                        'service_name': config.get('name', service),
                        'days_until_rotation': rotation_days - days_since_rotation,
                        'last_rotated': last_rotated.isoformat(),
                        'rotation_count': metadata.get('rotation_count', 0),
                        'severity': 'info'
                    })
        
        return alerts
    
    def get_key_metadata(self, service: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific service key"""
        if service not in self._metadata_cache:
            return None
        
        metadata = self._metadata_cache[service].copy()
        
        # Convert datetime objects to ISO strings for JSON serialization
        if 'created_date' in metadata:
            metadata['created_date'] = metadata['created_date'].isoformat()
        if 'last_rotated' in metadata:
            metadata['last_rotated'] = metadata['last_rotated'].isoformat()
        
        # Add rotation status
        config = SERVICE_CONFIGS.get(service, {})
        rotation_days = config.get('rotation_days', 30)
        
        last_rotated = self._metadata_cache[service].get('last_rotated', 
                        self._metadata_cache[service].get('created_date'))
        
        if last_rotated:
            days_since_rotation = (datetime.now() - last_rotated).days
            metadata['days_since_rotation'] = days_since_rotation
            metadata['rotation_recommended'] = days_since_rotation >= rotation_days
            metadata['rotation_overdue'] = days_since_rotation > rotation_days + 7
        
        return metadata
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        if not self.audit_path.exists():
            return []
        
        entries = []
        try:
            with open(self.audit_path, 'r') as f:
                lines = f.readlines()
            
            # Get the most recent entries
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            return []


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


# Enhanced Service Configurations with ChatGPT Suggestions
SERVICE_CONFIGS = {
    "openai": {
        "name": "OpenAI API",
        "required": True,
        "description": "Required for AI Lite batch analysis and Deep AI strategic dossiers",
        "cost_info": "Pay-per-use: ~$0.0001/candidate (AI Lite), ~$0.10-0.25/target (Deep AI)",
        "setup_url": "https://platform.openai.com/api-keys",
        "env_var": "OPENAI_API_KEY",
        "validation": lambda key: key.startswith("sk-") and len(key) >= 48,
        "aliases": ["gpt", "gpt-3.5", "gpt-4", "chatgpt"],
        "models": ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4"],
        "rotation_days": 30
    },
    "anthropic": {
        "name": "Anthropic Claude API",
        "required": False,
        "description": "Alternative AI provider with Claude models for analysis",
        "cost_info": "Pay-per-use: competitive pricing with OpenAI",
        "setup_url": "https://console.anthropic.com/",
        "env_var": "ANTHROPIC_API_KEY",
        "validation": lambda key: key.startswith("sk-ant-") and len(key) >= 50,
        "aliases": ["claude", "anthropic-claude", "claude-3"],
        "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
        "rotation_days": 30
    },
    "google": {
        "name": "Google Gemini API",
        "required": False,
        "description": "Google's Gemini models for AI analysis",
        "cost_info": "Competitive pricing with free tier available",
        "setup_url": "https://aistudio.google.com/app/apikey",
        "env_var": "GOOGLE_API_KEY",
        "validation": lambda key: len(key.strip()) > 20,
        "aliases": ["gemini", "google-ai", "bard"],
        "models": ["gemini-pro", "gemini-pro-vision", "gemini-ultra"],
        "rotation_days": 30
    },
    "groq": {
        "name": "Groq API",
        "required": False,
        "description": "High-speed inference with Groq LPUs",
        "cost_info": "Fast inference with competitive pricing",
        "setup_url": "https://console.groq.com/keys",
        "env_var": "GROQ_API_KEY",
        "validation": lambda key: key.startswith("gsk_") and len(key) >= 40,
        "aliases": ["groq-llama", "llama-groq"],
        "models": ["llama2-70b-4096", "mixtral-8x7b-32768", "gemma-7b-it"],
        "rotation_days": 30
    },
    "foundation_directory": {
        "name": "Foundation Directory API", 
        "required": False,
        "description": "Enhanced foundation data access (premium features)",
        "cost_info": "May be free for basic access, premium features may require subscription",
        "setup_url": "https://foundationdirectory.org/",
        "env_var": "FOUNDATION_DIRECTORY_API_KEY",
        "validation": lambda key: len(key.strip()) > 0,
        "aliases": ["foundation-dir", "candid"],
        "models": [],
        "rotation_days": 60
    }
}

# Free APIs that don't need keys (for reference)
FREE_APIS = {
    "propublica": "ProPublica Nonprofit Explorer API - Free",
    "grants_gov": "Grants.gov API - Free", 
    "usaspending": "USASpending.gov API - Free"
}


def validate_api_key(service: str, api_key: str) -> tuple[bool, str]:
    """
    Validate API key format for a specific service.
    
    Args:
        service: Service name (e.g., 'openai', 'foundation_directory')
        api_key: The API key to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    
    config = SERVICE_CONFIGS.get(service)
    if not config:
        return False, f"Unknown service: {service}"
    
    validator = config.get("validation")
    if validator:
        try:
            if validator(api_key):
                return True, "API key format appears valid"
            else:
                if service == "openai":
                    return False, "OpenAI API keys must start with 'sk-' and be at least 48 characters"
                else:
                    return False, "API key format appears invalid"
        except Exception:
            return False, "API key validation failed"
    
    return True, "API key format not validated but appears non-empty"


def get_service_status() -> Dict[str, Any]:
    """
    Get configuration status for all API services.
    
    Returns:
        Dictionary with service status information
    """
    manager = get_api_key_manager()
    status = {}
    
    # Check configured services
    for service, config in SERVICE_CONFIGS.items():
        has_key = manager.get_api_key(service) is not None
        status[service] = {
            "name": config["name"],
            "configured": has_key,
            "required": config["required"],
            "description": config["description"],
            "cost_info": config["cost_info"],
            "setup_url": config["setup_url"],
            "env_var": config["env_var"],
            "status": "✅ Configured" if has_key else ("⚠️ Required" if config["required"] else "ℹ️ Optional")
        }
    
    # Add info about free APIs
    status["free_apis"] = {
        "name": "Free APIs",
        "configured": True,
        "required": False,
        "description": "These APIs are free and don't require API keys",
        "services": FREE_APIS,
        "status": "✅ Available"
    }
    
    return status


def get_missing_required_keys() -> list:
    """Get list of required services missing API keys."""
    manager = get_api_key_manager()
    missing = []
    
    for service, config in SERVICE_CONFIGS.items():
        if config["required"] and not manager.get_api_key(service):
            missing.append(service)
    
    return missing


def is_ai_analysis_available() -> bool:
    """Check if AI analysis features are available (OpenAI key configured)."""
    manager = get_api_key_manager()
    return manager.get_api_key("openai") is not None


def get_openai_key() -> Optional[str]:
    """Get OpenAI API key for AI analysis."""
    return get_api_key_manager().get_api_key("openai")


def get_foundation_directory_key() -> Optional[str]:
    """Get Foundation Directory API key."""
    return get_api_key_manager().get_api_key("foundation_directory")


def generate_setup_instructions() -> str:
    """Generate user-friendly setup instructions for missing API keys."""
    missing = get_missing_required_keys()
    
    if not missing:
        return "✅ All required API keys are configured!"
    
    instructions = "🔑 **API Key Setup Required**\n\n"
    
    for service in missing:
        config = SERVICE_CONFIGS[service]
        instructions += f"**{config['name']}** (Required)\n"
        instructions += f"• Description: {config['description']}\n"
        instructions += f"• Cost: {config['cost_info']}\n"
        instructions += f"• Setup URL: {config['setup_url']}\n"
        instructions += f"• Environment Variable: {config['env_var']}\n\n"
    
    instructions += "💡 **Setup Options:**\n"
    instructions += "1. Set environment variables before starting Catalynx\n"
    instructions += "2. Use the API key management interface in SETTINGS tab\n"
    instructions += "3. Add keys to your .env file (not committed to git)\n\n"
    
    instructions += "ℹ️ **Free APIs:**\n"
    for service, description in FREE_APIS.items():
        instructions += f"• {description}\n"
    
    return instructions
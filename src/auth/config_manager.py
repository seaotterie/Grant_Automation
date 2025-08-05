"""
Configuration Management with Encrypted Secrets
Handles application configuration with secure secret management.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

from .api_key_manager import get_api_key_manager

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///grant_research.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max connection overflow")
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class APIConfig(BaseSettings):
    """API service configuration settings."""
    
    # ProPublica NonProfit Explorer API
    propublica_base_url: str = Field(
        default="https://projects.propublica.org/nonprofits/api/v2",
        description="ProPublica API base URL"
    )
    propublica_rate_limit: int = Field(default=10, description="Requests per second")
    propublica_timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # IRS Data Sources
    irs_bmf_url: str = Field(
        default="https://www.irs.gov/pub/irs-teb/",
        description="IRS Business Master File URL"
    )
    
    # Request settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    backoff_factor: float = Field(default=1.0, description="Backoff factor for retries")
    
    model_config = SettingsConfigDict(env_prefix="API_")
    
    def get_propublica_api_key(self) -> Optional[str]:
        """Get ProPublica API key from secure storage."""
        return get_api_key_manager().get_api_key("propublica")


class ProcessingConfig(BaseSettings):
    """Data processing configuration settings."""
    
    # Concurrency settings
    max_concurrent_downloads: int = Field(default=3, description="Max concurrent downloads")
    max_concurrent_processors: int = Field(default=2, description="Max concurrent processors")
    
    # File processing
    temp_dir: Path = Field(default=Path("temp"), description="Temporary files directory")
    cache_dir: Path = Field(default=Path("cache"), description="Cache directory")
    output_dir: Path = Field(default=Path("output"), description="Output directory")
    
    # Data retention
    cache_expiry_days: int = Field(default=30, description="Cache expiry in days")
    temp_file_cleanup: bool = Field(default=True, description="Auto-cleanup temp files")
    
    # OCR settings
    ocr_enabled: bool = Field(default=True, description="Enable OCR processing")
    ocr_language: str = Field(default="eng", description="OCR language")
    ocr_dpi: int = Field(default=300, description="OCR DPI setting")
    
    model_config = SettingsConfigDict(env_prefix="PROCESSING_")
    
    @validator('temp_dir', 'cache_dir', 'output_dir')
    def ensure_absolute_path(cls, v):
        """Ensure paths are absolute."""
        if not v.is_absolute():
            v = Path.cwd() / v
        v.mkdir(parents=True, exist_ok=True)
        return v


class SecurityConfig(BaseSettings):
    """Security and authentication configuration."""
    
    # Session settings
    session_timeout_hours: int = Field(default=8, description="Session timeout in hours")
    session_secret_key: str = Field(default="", description="Session encryption key")
    
    # API security
    api_rate_limit: int = Field(default=100, description="API requests per minute")
    require_api_auth: bool = Field(default=False, description="Require API authentication")
    
    # Data privacy
    log_sensitive_data: bool = Field(default=False, description="Log sensitive data")
    encrypt_database: bool = Field(default=False, description="Encrypt database")
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")
    
    @validator('session_secret_key')
    def generate_secret_key(cls, v):
        """Generate secret key if not provided."""
        if not v:
            import secrets
            v = secrets.token_urlsafe(32)
            logger.info("Generated new session secret key")
        return v


class DashboardConfig(BaseSettings):
    """Dashboard and UI configuration."""
    
    # Streamlit settings
    title: str = Field(default="Grant Research Automation", description="Dashboard title")
    theme: str = Field(default="light", description="UI theme")
    layout: str = Field(default="wide", description="Page layout")
    
    # Features
    enable_real_time_updates: bool = Field(default=True, description="Enable real-time updates")
    refresh_interval_seconds: int = Field(default=5, description="Auto-refresh interval")
    max_results_display: int = Field(default=100, description="Max results to display")
    
    # Export options
    enable_excel_export: bool = Field(default=True, description="Enable Excel export")
    enable_pdf_export: bool = Field(default=True, description="Enable PDF export")
    enable_csv_export: bool = Field(default=True, description="Enable CSV export")
    
    model_config = SettingsConfigDict(env_prefix="DASHBOARD_")


class GrantResearchConfig(BaseSettings):
    """Main application configuration."""
    
    # Environment
    app_name: str = Field(default="Grant Research Automation", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (dev/prod)")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        if v not in ['development', 'testing', 'production']:
            raise ValueError('Environment must be one of: development, testing, production')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    def setup_logging(self) -> None:
        """Configure application logging."""
        import logging
        import logging.handlers
        
        # Set log level
        log_level = getattr(logging, self.log_level)
        logging.basicConfig(
            level=log_level,
            format=self.log_format,
            handlers=[]
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(self.log_format)
        console_handler.setFormatter(console_formatter)
        
        # File handler (if specified)
        handlers = [console_handler]
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(console_formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.handlers = handlers
        
        logger.info(f"Logging configured: level={self.log_level}, file={self.log_file}")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


class ConfigManager:
    """
    Configuration manager with support for environment-specific configs.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".grant_research"
        self.config_dir.mkdir(exist_ok=True, mode=0o700)
        self._config: Optional[GrantResearchConfig] = None
    
    def load_config(self, environment: Optional[str] = None) -> GrantResearchConfig:
        """
        Load configuration for the specified environment.
        
        Args:
            environment: Environment name (dev/test/prod)
            
        Returns:
            Loaded configuration object
        """
        # Set environment if specified
        if environment:
            os.environ["ENVIRONMENT"] = environment
        
        # Load base configuration
        self._config = GrantResearchConfig()
        
        # Set up logging
        self._config.setup_logging()
        
        # Load environment-specific overrides
        env_config_file = self.config_dir / f"config.{self._config.environment}.json"
        if env_config_file.exists():
            self._load_config_overrides(env_config_file)
        
        logger.info(f"Configuration loaded for environment: {self._config.environment}")
        return self._config
    
    def _load_config_overrides(self, config_file: Path) -> None:
        """Load configuration overrides from JSON file."""
        try:
            with open(config_file, 'r') as f:
                overrides = json.load(f)
            
            # Apply overrides (simple implementation)
            for key, value in overrides.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                    logger.debug(f"Applied config override: {key} = {value}")
            
        except Exception as e:
            logger.warning(f"Failed to load config overrides from {config_file}: {e}")
    
    def save_config_template(self, environment: str) -> Path:
        """
        Save a configuration template file for the specified environment.
        
        Args:
            environment: Environment name
            
        Returns:
            Path to the saved template file
        """
        template_file = self.config_dir / f"config.{environment}.json.template"
        
        # Create template with example values
        template = {
            "debug": environment == "development",
            "log_level": "DEBUG" if environment == "development" else "INFO",
            "database": {
                "url": f"sqlite:///{environment}_grant_research.db",
                "echo": environment == "development"
            },
            "api": {
                "propublica_rate_limit": 10 if environment == "production" else 5,
                "max_retries": 3
            },
            "processing": {
                "max_concurrent_downloads": 3 if environment == "production" else 1,
                "cache_expiry_days": 30 if environment == "production" else 7
            },
            "security": {
                "session_timeout_hours": 8 if environment == "production" else 24,
                "require_api_auth": environment == "production"
            }
        }
        
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Configuration template saved: {template_file}")
        return template_file
    
    def get_config(self) -> GrantResearchConfig:
        """Get the loaded configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config


# Global configuration manager
_config_manager: Optional[ConfigManager] = None
_config: Optional[GrantResearchConfig] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> GrantResearchConfig:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = get_config_manager().load_config()
    return _config


def reload_config(environment: Optional[str] = None) -> GrantResearchConfig:
    """Reload the global configuration."""
    global _config
    _config = get_config_manager().load_config(environment)
    return _config
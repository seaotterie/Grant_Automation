"""
Command Line Authentication Interface
Provides CLI tools for managing authentication and API keys.
"""
import click
import getpass
import sys
from typing import Optional
from pathlib import Path
import logging

from .api_key_manager import get_api_key_manager
from .dashboard_auth import get_dashboard_auth
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def auth_cli(verbose: bool):
    """Grant Research Authentication CLI."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@auth_cli.group()
def api_keys():
    """Manage API keys for external services."""
    pass


@api_keys.command()
@click.option('--password', '-p', help='Master password (will prompt if not provided)')
def setup(password: Optional[str]):
    """Set up API key management with master password."""
    click.echo("🔐 Setting up API key management...")
    
    manager = get_api_key_manager()
    
    if not password:
        password = getpass.getpass("Enter master password for API keys: ")
        confirm_password = getpass.getpass("Confirm master password: ")
        
        if password != confirm_password:
            click.echo("❌ Passwords do not match!")
            sys.exit(1)
    
    if manager.authenticate(password):
        click.echo("✅ API key management set up successfully!")
        click.echo("You can now add API keys using the 'add' command.")
    else:
        click.echo("❌ Failed to set up API key management.")
        sys.exit(1)


@api_keys.command()
@click.argument('service')
@click.option('--key', '-k', help='API key (will prompt if not provided)')
@click.option('--password', '-p', help='Master password (will prompt if not provided)')
def add(service: str, key: Optional[str], password: Optional[str]):
    """Add an API key for a service."""
    click.echo(f"🔑 Adding API key for service: {service}")
    
    manager = get_api_key_manager()
    
    # Authenticate
    if not password:
        password = getpass.getpass("Enter master password: ")
    
    if not manager.authenticate(password):
        click.echo("❌ Authentication failed!")
        sys.exit(1)
    
    # Get API key
    if not key:
        key = getpass.getpass(f"Enter API key for {service}: ")
    
    if not key.strip():
        click.echo("❌ API key cannot be empty!")
        sys.exit(1)
    
    try:
        manager.set_api_key(service, key)
        click.echo(f"✅ API key added successfully for {service}")
    except Exception as e:
        click.echo(f"❌ Failed to add API key: {e}")
        sys.exit(1)


@api_keys.command()
@click.option('--password', '-p', help='Master password (will prompt if not provided)')
def list(password: Optional[str]):
    """List all services with stored API keys."""
    manager = get_api_key_manager()
    
    # Authenticate
    if not password:
        password = getpass.getpass("Enter master password: ")
    
    if not manager.authenticate(password):
        click.echo("❌ Authentication failed!")
        sys.exit(1)
    
    services = manager.list_services()
    
    if services:
        click.echo("📋 Services with stored API keys:")
        for service in services:
            status = "✅" if manager.validate_key(service) else "❌"
            click.echo(f"  {status} {service}")
    else:
        click.echo("📭 No API keys stored.")


@api_keys.command()
@click.argument('service')
@click.option('--password', '-p', help='Master password (will prompt if not provided)')
def remove(service: str, password: Optional[str]):
    """Remove an API key for a service."""
    click.echo(f"🗑️  Removing API key for service: {service}")
    
    if not click.confirm(f"Are you sure you want to remove the API key for {service}?"):
        click.echo("Operation cancelled.")
        return
    
    manager = get_api_key_manager()
    
    # Authenticate
    if not password:
        password = getpass.getpass("Enter master password: ")
    
    if not manager.authenticate(password):
        click.echo("❌ Authentication failed!")
        sys.exit(1)
    
    if manager.remove_api_key(service):
        click.echo(f"✅ API key removed for {service}")
    else:
        click.echo(f"❌ No API key found for {service}")


@api_keys.command()
@click.argument('service')
@click.option('--password', '-p', help='Master password (will prompt if not provided)')
def test(service: str, password: Optional[str]):
    """Test an API key for a service."""
    click.echo(f"🧪 Testing API key for service: {service}")
    
    manager = get_api_key_manager()
    
    # Authenticate
    if not password:
        password = getpass.getpass("Enter master password: ")
    
    if not manager.authenticate(password):
        click.echo("❌ Authentication failed!")
        sys.exit(1)
    
    # Test basic key existence and format
    if manager.validate_key(service):
        click.echo(f"✅ API key for {service} is present and non-empty")
        
        # Additional service-specific testing could be added here
        if service == "propublica":
            click.echo("ℹ️  For ProPublica API testing, run a workflow to verify connectivity")
    else:
        click.echo(f"❌ No valid API key found for {service}")


@auth_cli.group() 
def users():
    """Manage dashboard users."""
    pass


@users.command()
@click.argument('username')
@click.option('--password', '-p', help='User password (will prompt if not provided)')
@click.option('--role', '-r', type=click.Choice(['admin', 'user']), default='user', help='User role')
def create(username: str, password: Optional[str], role: str):
    """Create a new dashboard user."""
    click.echo(f"👤 Creating user: {username} with role: {role}")
    
    auth = get_dashboard_auth()
    
    # Check if user already exists
    if auth.get_user_info(username):
        click.echo(f"❌ User {username} already exists!")
        sys.exit(1)
    
    # Get password
    if not password:
        password = getpass.getpass("Enter password for new user: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            click.echo("❌ Passwords do not match!")
            sys.exit(1)
    
    if len(password) < 8:
        click.echo("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    if auth.create_user(username, password, role):
        click.echo(f"✅ User {username} created successfully!")
    else:
        click.echo(f"❌ Failed to create user {username}")
        sys.exit(1)


@users.command()
def list_users():
    """List all dashboard users."""
    auth = get_dashboard_auth()
    users = auth.list_users()
    
    if users:
        click.echo("👥 Dashboard users:")
        for user in users:
            status = "🟢 Active" if user.get("active", True) else "🔴 Inactive"
            last_login = user.get("last_login", "Never")
            click.echo(f"  • {user['username']} ({user['role']}) - {status} - Last login: {last_login}")
    else:
        click.echo("📭 No users found.")


@users.command()
@click.argument('username')
@click.option('--current-password', '-c', help='Current password (will prompt if not provided)')
@click.option('--new-password', '-n', help='New password (will prompt if not provided)')
def change_password(username: str, current_password: Optional[str], new_password: Optional[str]):
    """Change a user's password."""
    click.echo(f"🔑 Changing password for user: {username}")
    
    auth = get_dashboard_auth()
    
    # Check if user exists
    if not auth.get_user_info(username):
        click.echo(f"❌ User {username} does not exist!")
        sys.exit(1)
    
    # Get current password
    if not current_password:
        current_password = getpass.getpass("Enter current password: ")
    
    # Get new password
    if not new_password:
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            click.echo("❌ Passwords do not match!")
            sys.exit(1)
    
    if len(new_password) < 8:
        click.echo("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    if auth.change_password(username, current_password, new_password):
        click.echo(f"✅ Password changed successfully for {username}")
    else:
        click.echo(f"❌ Failed to change password for {username}")
        sys.exit(1)


@users.command()
@click.argument('username')
def deactivate(username: str):
    """Deactivate a user account."""
    click.echo(f"⛔ Deactivating user: {username}")
    
    if not click.confirm(f"Are you sure you want to deactivate user {username}?"):
        click.echo("Operation cancelled.")
        return
    
    auth = get_dashboard_auth()
    
    if auth.deactivate_user(username):
        click.echo(f"✅ User {username} deactivated successfully")
    else:
        click.echo(f"❌ Failed to deactivate user {username}")
        sys.exit(1)


@auth_cli.group()
def config():
    """Manage application configuration."""
    pass


@config.command()
@click.option('--environment', '-e', type=click.Choice(['development', 'testing', 'production']), 
              default='development', help='Environment to create template for')
def create_template(environment: str):
    """Create configuration template for an environment."""
    click.echo(f"📝 Creating configuration template for: {environment}")
    
    manager = get_config_manager()
    template_file = manager.save_config_template(environment)
    
    click.echo(f"✅ Template created: {template_file}")
    click.echo("Edit this file and rename it (remove .template) to apply the configuration.")


@config.command()
@click.option('--environment', '-e', help='Environment to load')
def show(environment: Optional[str]):
    """Show current configuration."""
    click.echo("⚙️  Current configuration:")
    
    try:
        config = get_config_manager().load_config(environment)
        
        click.echo(f"App Name: {config.app_name}")
        click.echo(f"Version: {config.version}")
        click.echo(f"Environment: {config.environment}")
        click.echo(f"Debug: {config.debug}")
        click.echo(f"Log Level: {config.log_level}")
        
        click.echo("\nDatabase:")
        click.echo(f"  URL: {config.database.url}")
        click.echo(f"  Echo: {config.database.echo}")
        
        click.echo("\nAPI:")
        click.echo(f"  ProPublica URL: {config.api.propublica_base_url}")
        click.echo(f"  Rate Limit: {config.api.propublica_rate_limit}")
        
        click.echo("\nProcessing:")
        click.echo(f"  Max Concurrent Downloads: {config.processing.max_concurrent_downloads}")
        click.echo(f"  Cache Directory: {config.processing.cache_dir}")
        click.echo(f"  OCR Enabled: {config.processing.ocr_enabled}")
        
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}")
        sys.exit(1)


@auth_cli.command()
def status():
    """Show authentication system status."""
    click.echo("Authentication System Status")
    click.echo("=" * 40)
    
    # API Key Manager
    manager = get_api_key_manager()
    storage_exists = manager.storage_path.exists()
    click.echo(f"API Key Storage: {'Found' if storage_exists else 'Not found'}")
    
    if storage_exists:
        # Try to get services (will fail without authentication, but that's ok)
        try:
            # This will show 0 if not authenticated, which is expected
            services = manager.list_services()
            click.echo(f"Stored API Keys: {len(services)} services")
        except Exception:
            click.echo("Stored API Keys: Authentication required")
    
    # Dashboard Users
    auth = get_dashboard_auth()
    users = auth.list_users()
    click.echo(f"Dashboard Users: {len(users)} users")
    
    active_users = [u for u in users if u.get('active', True)]
    click.echo(f"Active Users: {len(active_users)}")
    
    # Configuration
    try:
        config = get_config_manager().get_config()
        click.echo(f"Configuration: Loaded ({config.environment})")
    except Exception as e:
        click.echo(f"Configuration: Error ({e})")


@auth_cli.command()
def init():
    """Initialize the authentication system."""
    click.echo("Initializing Grant Research Authentication System")
    click.echo("=" * 50)
    
    # Step 1: Set up API key management
    click.echo("\n1. Setting up API key management...")
    manager = get_api_key_manager()
    
    password = getpass.getpass("Create master password for API keys: ")
    confirm_password = getpass.getpass("Confirm master password: ")
    
    if password != confirm_password:
        click.echo("❌ Passwords do not match!")
        sys.exit(1)
    
    if len(password) < 8:
        click.echo("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    if not manager.authenticate(password):
        click.echo("❌ Failed to initialize API key management!")
        sys.exit(1)
    
    click.echo("✅ API key management initialized")
    
    # Step 2: Create admin user
    click.echo("\n2. Creating admin user...")
    auth = get_dashboard_auth()
    
    admin_username = click.prompt("Admin username", default="admin")
    admin_password = getpass.getpass("Admin password: ")
    confirm_admin = getpass.getpass("Confirm admin password: ")
    
    if admin_password != confirm_admin:
        click.echo("❌ Passwords do not match!")
        sys.exit(1)
    
    if len(admin_password) < 8:
        click.echo("❌ Password must be at least 8 characters long!")
        sys.exit(1)
    
    # Remove existing admin if it exists
    existing_users = auth.list_users()
    admin_exists = any(u['username'] == admin_username for u in existing_users)
    
    if admin_exists:
        if click.confirm(f"Admin user '{admin_username}' already exists. Replace?"):
            auth.deactivate_user(admin_username)
        else:
            click.echo("Keeping existing admin user.")
            admin_exists = False
    
    if not admin_exists:
        if auth.create_user(admin_username, admin_password, "admin"):
            click.echo(f"✅ Admin user '{admin_username}' created")
        else:
            click.echo("❌ Failed to create admin user!")
            sys.exit(1)
    
    # Step 3: Configuration
    click.echo("\n3. Setting up configuration...")
    config_manager = get_config_manager()
    
    environment = click.prompt("Environment", 
                              type=click.Choice(['development', 'testing', 'production']),
                              default='development')
    
    template_file = config_manager.save_config_template(environment)
    click.echo(f"✅ Configuration template created: {template_file}")
    
    click.echo("\n🎉 Authentication system initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("1. Add API keys using: auth api-keys add <service>")
    click.echo("2. Edit configuration template if needed")
    click.echo("3. Start the modern web interface: python src/web/main.py")


if __name__ == '__main__':
    auth_cli()
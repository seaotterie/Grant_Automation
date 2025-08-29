#!/usr/bin/env python3
"""
Simple script to check API authentication status
"""

import os
import sys

# Add project root to path
sys.path.append('.')

def check_api_authentication():
    """Check current API authentication status"""
    
    print("=== API KEY AUTHENTICATION CHECK ===\n")
    
    try:
        from src.auth.api_key_manager import get_api_key_manager, get_service_status
        
        # Check environment variables first
        print("1. ENVIRONMENT VARIABLES:")
        openai_env = os.getenv('OPENAI_API_KEY')
        if openai_env:
            print(f"   OPENAI_API_KEY: Available (length: {len(openai_env)})")
        else:
            print("   OPENAI_API_KEY: Not set")
        
        anthropic_env = os.getenv('ANTHROPIC_API_KEY') 
        if anthropic_env:
            print(f"   ANTHROPIC_API_KEY: Available (length: {len(anthropic_env)})")
        else:
            print("   ANTHROPIC_API_KEY: Not set")
            
        print()
        
        # Check API key manager
        print("2. API KEY MANAGER:")
        manager = get_api_key_manager()
        
        # Try to get keys without authentication (will check env vars)
        openai_key = manager.get_api_key('openai')
        if openai_key:
            print(f"   OpenAI key available: Yes (length: {len(openai_key)})")
        else:
            print("   OpenAI key available: No")
            
        anthropic_key = manager.get_api_key('anthropic') 
        if anthropic_key:
            print(f"   Anthropic key available: Yes (length: {len(anthropic_key)})")
        else:
            print("   Anthropic key available: No")
            
        print()
        
        # Service status
        print("3. SERVICE STATUS:")
        try:
            status = get_service_status()
            for service, config in status.items():
                if service != 'free_apis':
                    name = config.get('name', service)
                    configured = config.get('configured', False)
                    required = config.get('required', False)
                    
                    status_text = "Configured" if configured else ("Required" if required else "Optional")
                    print(f"   {name}: {status_text}")
                    
        except Exception as e:
            print(f"   Error getting service status: {e}")
            
        print()
        
    except Exception as e:
        print(f"Error checking API authentication: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = check_api_authentication()
    
    if not success:
        print("Authentication check failed!")
        sys.exit(1)
    else:
        print("Authentication check completed.")
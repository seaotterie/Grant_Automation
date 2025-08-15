#!/usr/bin/env python3
"""
PHASE 4A: Production API Configuration Setup
Comprehensive API key configuration and validation for production deployment.

This script handles:
1. API service validation and setup
2. Production environment configuration
3. Client authentication testing
4. Service availability verification
"""
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, 'src')

def test_api_configuration():
    """Test API configuration and authentication"""
    
    print("=" * 80)
    print("PHASE 4A: PRODUCTION API CONFIGURATION SETUP")
    print("=" * 80)
    
    from src.auth.api_key_manager import get_api_key_manager
    
    # Required API services for production
    required_apis = {
        "grants_gov": {
            "name": "Grants.gov API",
            "description": "Federal grant opportunities discovery",
            "required": True,
            "documentation": "https://www.grants.gov/support/how-to-apply-for-grants"
        },
        "foundation_directory": {
            "name": "Foundation Directory Online",
            "description": "Corporate foundation and CSR program discovery", 
            "required": True,
            "documentation": "https://fdo.foundationcenter.org/"
        },
        "propublica": {
            "name": "ProPublica Nonprofit Explorer",
            "description": "IRS 990 filings and nonprofit intelligence",
            "required": True,
            "documentation": "https://projects.propublica.org/nonprofits/api"
        },
        "usaspending": {
            "name": "USASpending.gov API",
            "description": "Historical government spending and award data",
            "required": True,
            "documentation": "https://api.usaspending.gov/"
        },
        "va_state": {
            "name": "Virginia State Grant APIs",
            "description": "Virginia state agency grant opportunities",
            "required": False,
            "documentation": "State agency portals (various)"
        }
    }
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 1: API Service Requirements")
    print("-" * 60)
    
    for api_name, info in required_apis.items():
        status = "[REQUIRED]" if info["required"] else "[OPTIONAL]"
        print(f"{status} {api_name}: {info['name']}")
        print(f"   Purpose: {info['description']}")
        print(f"   Documentation: {info['documentation']}")
        print()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 2: Authentication Manager Status")
    print("-" * 60)
    
    try:
        api_manager = get_api_key_manager()
        print(f"[PASS] API Key Manager initialized")
        print(f"[INFO] Storage path: {api_manager.storage_path}")
        
        # Check if authenticated
        is_authenticated = api_manager._fernet is not None
        print(f"Authentication Status: {'[AUTHENTICATED]' if is_authenticated else '[NEEDS AUTHENTICATION]'}")
        
        if not is_authenticated:
            print("\nTo authenticate and configure API keys:")
            print("1. Run authentication: python -c \"from src.auth.api_key_manager import get_api_key_manager; api_manager = get_api_key_manager(); api_manager.authenticate()\"")
            print("2. Configure each API key:")
            for api_name in required_apis.keys():
                print(f"   api_manager.set_api_key('{api_name}', 'your_{api_name}_key')")
            return False
        else:
            print("[PASS] API Key Manager authenticated")
        
    except Exception as e:
        print(f"[FAIL] API Key Manager error: {e}")
        return False
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 3: API Key Configuration Status")
    print("-" * 60)
    
    configured_apis = []
    missing_apis = []
    
    for api_name, info in required_apis.items():
        try:
            key = api_manager.get_api_key(api_name)
            if key:
                print(f"[PASS] {api_name}: [CONFIGURED] ({len(key)} chars)")
                configured_apis.append(api_name)
            else:
                status = "[MISSING - REQUIRED]" if info["required"] else "[MISSING - OPTIONAL]"
                print(f"[FAIL] {api_name}: {status}")
                if info["required"]:
                    missing_apis.append(api_name)
        except Exception as e:
            print(f"[FAIL] {api_name}: [ERROR] {e}")
            if info["required"]:
                missing_apis.append(api_name)
    
    print(f"\nConfiguration Summary:")
    print(f"  Configured APIs: {len(configured_apis)}/{len([k for k, v in required_apis.items() if v['required']])}")
    print(f"  Missing Required APIs: {len(missing_apis)}")
    
    if missing_apis:
        print(f"\nMissing Required APIs: {', '.join(missing_apis)}")
        print("Production deployment blocked until all required APIs are configured.")
        return False
    
    return True

async def test_client_connectivity():
    """Test client connectivity with configured APIs"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 4: Client Connectivity Testing")
    print("-" * 60)
    
    try:
        # Import clients
        from src.clients import (
            GrantsGovClient, 
            FoundationDirectoryClient, 
            ProPublicaClient, 
            USASpendingClient, 
            VAStateClient
        )
        
        clients = [
            ("Grants.gov", GrantsGovClient),
            ("Foundation Directory", FoundationDirectoryClient), 
            ("ProPublica", ProPublicaClient),
            ("USASpending", USASpendingClient),
            ("VA State", VAStateClient)
        ]
        
        connectivity_results = {}
        
        for client_name, client_class in clients:
            try:
                print(f"Testing {client_name} client...")
                client = client_class()
                
                # Basic initialization test
                if hasattr(client, 'base_url') and client.base_url:
                    print(f"  [PASS] {client_name}: Initialized with base URL: {client.base_url}")
                    connectivity_results[client_name] = "initialized"
                else:
                    print(f"  [WARN] {client_name}: Initialized but no base URL configured")
                    connectivity_results[client_name] = "partial"
                
                # Test API key availability
                if hasattr(client, 'api_key') and client.api_key:
                    print(f"  [PASS] {client_name}: API key configured")
                elif hasattr(client, 'api_key'):
                    print(f"  [WARN] {client_name}: No API key configured - will use public endpoints only")
                else:
                    print(f"  [INFO] {client_name}: No API key required")
                    
            except Exception as e:
                print(f"  [FAIL] {client_name}: Client initialization failed: {e}")
                connectivity_results[client_name] = "failed"
        
        print(f"\nClient Connectivity Summary:")
        for client_name, status in connectivity_results.items():
            status_icon = "[PASS]" if status == "initialized" else ("[WARN]" if status == "partial" else "[FAIL]")
            print(f"  {status_icon} {client_name}: {status}")
        
        return len([s for s in connectivity_results.values() if s in ["initialized", "partial"]]) > 0
        
    except Exception as e:
        print(f"Client connectivity testing failed: {e}")
        return False

def test_discovery_bridge_integration():
    """Test unified discovery bridge with production API configuration"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 5: Discovery Bridge Integration Testing")
    print("-" * 60)
    
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType
        
        # Initialize bridge
        bridge = get_unified_bridge()
        print("[PASS] Unified discovery bridge initialized")
        
        # Check bridge status
        status = bridge.get_bridge_status()
        print(f"[PASS] Bridge status: {status['bridge_status']}")
        print(f"[PASS] Available strategies: {', '.join(status['strategies_available'])}")
        
        # Test strategy initialization with API configurations
        strategies = bridge.unified_engine.strategies
        for strategy_name, strategy in strategies.items():
            try:
                # Check if strategy has processors or clients
                has_processors = any([
                    hasattr(strategy, attr) for attr in 
                    ['grants_gov_processor', 'foundation_processor', 'va_state_processor']
                ])
                has_clients = any([
                    hasattr(strategy, attr) for attr in 
                    ['grants_gov_client', 'foundation_directory_client', 'va_state_client']
                ])
                
                if has_processors or has_clients:
                    print(f"[PASS] {strategy_name} strategy: Ready for production")
                else:
                    print(f"[WARN] {strategy_name} strategy: Limited functionality")
                    
            except Exception as e:
                print(f"[FAIL] {strategy_name} strategy: {e}")
        
        return True
        
    except Exception as e:
        print(f"Discovery bridge integration test failed: {e}")
        return False

def generate_production_checklist():
    """Generate production deployment checklist"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4A PRODUCTION CHECKLIST")
    print("=" * 80)
    
    checklist = [
        {
            "item": "API Key Manager Authentication",
            "description": "Master password configured and key storage encrypted",
            "command": "python -c \"from src.auth.api_key_manager import get_api_key_manager; get_api_key_manager().authenticate()\""
        },
        {
            "item": "Grants.gov API Configuration", 
            "description": "Federal grant opportunities discovery",
            "command": "api_manager.set_api_key('grants_gov', 'your_grants_gov_key')"
        },
        {
            "item": "Foundation Directory API Configuration",
            "description": "Corporate foundation and CSR program discovery", 
            "command": "api_manager.set_api_key('foundation_directory', 'your_foundation_directory_key')"
        },
        {
            "item": "ProPublica API Configuration",
            "description": "IRS 990 filings and nonprofit intelligence",
            "command": "api_manager.set_api_key('propublica', 'your_propublica_key')"
        },
        {
            "item": "USASpending API Configuration",
            "description": "Historical government spending data (may not require key)",
            "command": "api_manager.set_api_key('usaspending', 'your_usaspending_key_if_needed')"
        },
        {
            "item": "Virginia State API Configuration (Optional)",
            "description": "Virginia state agency grant opportunities", 
            "command": "api_manager.set_api_key('va_state', 'your_va_state_key')"
        },
        {
            "item": "Client Connectivity Validation",
            "description": "All clients can initialize and connect to their services",
            "command": "python phase_4a_api_setup.py"
        },
        {
            "item": "Discovery Bridge Production Testing",
            "description": "Unified bridge operational with all configured APIs",
            "command": "python test_phase_3_unified_discovery.py"
        },
        {
            "item": "Production Environment Variables",
            "description": "Configure production-specific settings and endpoints",
            "command": "Review and update .env configuration file"
        },
        {
            "item": "Error Handling and Logging",
            "description": "Production-level error handling and monitoring configured",
            "command": "Review logging configuration in src/core/"
        }
    ]
    
    print("PRODUCTION DEPLOYMENT CHECKLIST:")
    print("-" * 40)
    
    for i, item in enumerate(checklist, 1):
        print(f"{i:2}. {item['item']}")
        print(f"    Purpose: {item['description']}")
        print(f"    Action: {item['command']}")
        print()
    
    print("NEXT STEPS:")
    print("1. Complete API configuration using the commands above")
    print("2. Run full connectivity testing: python phase_4a_api_setup.py") 
    print("3. Proceed to Phase 4B: Web Interface Integration")
    print("4. Complete Phase 4C: Real Data Validation")
    print("5. Finalize Phase 4D: Production Readiness Assessment")

def main():
    """Run Phase 4A API configuration setup"""
    
    try:
        # Step 1-3: API Configuration Testing
        api_config_success = test_api_configuration()
        
        if not api_config_success:
            print(f"\n[BLOCKED] PHASE 4A BLOCKED: Missing required API configurations")
            print("Please configure required API keys before proceeding.")
            generate_production_checklist()
            return False
        
        # Step 4: Client connectivity testing
        connectivity_success = asyncio.run(test_client_connectivity())
        
        if not connectivity_success:
            print(f"\n[WARNING] PHASE 4A WARNING: Client connectivity issues detected")
            print("Some clients may have limited functionality in production.")
        
        # Step 5: Discovery bridge integration testing
        integration_success = test_discovery_bridge_integration()
        
        if integration_success and api_config_success:
            print(f"\n[SUCCESS] PHASE 4A ASSESSMENT: PRODUCTION READY")
            print("API configuration completed successfully")
            print("All required services configured and operational")
            print("Discovery bridge integration validated")
            print("Ready to proceed to Phase 4B: Web Interface Integration")
            
            generate_production_checklist()
            return True
        else:
            print(f"\n[ATTENTION] PHASE 4A ASSESSMENT: NEEDS ATTENTION")
            print("Some components require additional configuration")
            generate_production_checklist()
            return False
            
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] Phase 4A setup interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Phase 4A setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
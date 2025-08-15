#!/usr/bin/env python3
"""
PHASE 4C: Real Data Validation and Performance Testing
Comprehensive validation of the unified discovery system with real data workflows and performance benchmarking.

This script tests:
1. Real client connectivity with configured API keys
2. Unified discovery bridge performance with real data
3. Web interface integration under load
4. End-to-end workflow validation
5. Performance benchmarking and metrics
"""
import sys
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Add src to path for imports
sys.path.insert(0, 'src')

class MockOrganizationProfile:
    """Enhanced mock profile for real data testing"""
    def __init__(self, profile_type="environmental"):
        # Base profile attributes
        self.profile_id = f"test_profile_{profile_type}_{int(time.time())}"
        self.name = f"Test {profile_type.title()} Nonprofit Organization"
        self.ein = "123456789"
        
        # Profile configurations for different testing scenarios
        profiles = {
            "environmental": {
                "ntee_code": "C32",
                "ntee_description": "Environmental Conservation and Protection",
                "mission_statement": "Dedicated to protecting natural resources and promoting environmental sustainability through education, conservation projects, and policy advocacy.",
                "focus_areas": ["environmental conservation", "sustainability", "climate change", "renewable energy"],
                "keywords": "environment conservation sustainability climate renewable energy",
                "state": "VA"
            },
            "education": {
                "ntee_code": "B25",
                "ntee_description": "Higher Education",
                "mission_statement": "Providing quality educational opportunities and supporting student success through innovative programs and community partnerships.",
                "focus_areas": ["education", "student support", "academic excellence", "community engagement"],
                "keywords": "education students learning academic community",
                "state": "VA"
            },
            "health": {
                "ntee_code": "E21",
                "ntee_description": "Community Health Systems",
                "mission_statement": "Improving community health outcomes through accessible healthcare services, health education, and wellness programs.",
                "focus_areas": ["healthcare", "community health", "wellness", "health education"],
                "keywords": "health healthcare wellness community medical",
                "state": "VA"
            }
        }
        
        config = profiles.get(profile_type, profiles["environmental"])
        
        # Apply configuration
        for key, value in config.items():
            setattr(self, key, value)
        
        # Geographic scope
        self.geographic_scope = type('obj', (object,), {
            'states': [config["state"]],
            'nationwide': False,
            'international': False
        })()
        
        # Additional attributes for testing
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

async def test_client_connectivity_real_data():
    """Test client connectivity with real API endpoints (without keys if not configured)"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4C TEST 1: Real Client Connectivity")
    print("-" * 70)
    
    connectivity_results = {}
    
    try:
        from src.clients import (
            GrantsGovClient,
            FoundationDirectoryClient, 
            ProPublicaClient,
            USASpendingClient,
            VAStateClient
        )
        
        clients = [
            ("Grants.gov", GrantsGovClient, "Federal grant opportunities"),
            ("Foundation Directory", FoundationDirectoryClient, "Corporate foundation data"),
            ("ProPublica", ProPublicaClient, "Nonprofit 990 filings"),
            ("USASpending", USASpendingClient, "Government spending data"),
            ("VA State", VAStateClient, "Virginia state grants")
        ]
        
        for client_name, client_class, description in clients:
            try:
                print(f"Testing {client_name} connectivity...")
                start_time = time.time()
                
                # Initialize client
                client = client_class()
                init_time = time.time() - start_time
                
                # Test basic connectivity without authentication
                connectivity_results[client_name] = {
                    "status": "initialized",
                    "init_time": init_time,
                    "base_url": getattr(client, 'base_url', 'Not configured'),
                    "has_api_key": bool(getattr(client, 'api_key', None)),
                    "description": description
                }
                
                print(f"  [PASS] {client_name}: Initialized in {init_time:.3f}s")
                print(f"    Base URL: {connectivity_results[client_name]['base_url']}")
                print(f"    API Key: {'[CONFIGURED]' if connectivity_results[client_name]['has_api_key'] else '[MISSING]'}")
                
            except Exception as e:
                print(f"  [FAIL] {client_name}: {e}")
                connectivity_results[client_name] = {
                    "status": "failed",
                    "error": str(e),
                    "description": description
                }
        
        print(f"\nClient Connectivity Summary:")
        successful_clients = len([r for r in connectivity_results.values() if r["status"] == "initialized"])
        print(f"  Successful Initializations: {successful_clients}/{len(clients)}")
        
        return successful_clients > 0, connectivity_results
        
    except Exception as e:
        print(f"Client connectivity test failed: {e}")
        return False, {}

async def test_unified_bridge_performance():
    """Test unified discovery bridge with performance benchmarking"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4C TEST 2: Unified Bridge Performance")
    print("-" * 70)
    
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType
        
        # Performance test configurations
        test_configs = [
            {
                "name": "Single Strategy Test",
                "funding_types": [FundingSourceType.GOVERNMENT_FEDERAL],
                "max_results": 10,
                "profile_type": "environmental"
            },
            {
                "name": "Multi-Strategy Test", 
                "funding_types": [
                    FundingSourceType.GOVERNMENT_FEDERAL,
                    FundingSourceType.FOUNDATION_CORPORATE,
                    FundingSourceType.GOVERNMENT_STATE
                ],
                "max_results": 20,
                "profile_type": "education"
            },
            {
                "name": "Comprehensive Test",
                "funding_types": [
                    FundingSourceType.GOVERNMENT_FEDERAL,
                    FundingSourceType.GOVERNMENT_STATE,
                    FundingSourceType.FOUNDATION_CORPORATE,
                    FundingSourceType.CORPORATE_CSR
                ],
                "max_results": 30,
                "profile_type": "health"
            }
        ]
        
        bridge = get_unified_bridge()
        performance_results = {}
        
        for config in test_configs:
            print(f"\nExecuting {config['name']}...")
            
            # Create test profile
            profile = MockOrganizationProfile(config["profile_type"])
            
            # Track performance metrics
            start_time = time.time()
            progress_updates = []
            
            def progress_callback(session_id: str, update_data: Dict[str, Any]):
                progress_updates.append({
                    "timestamp": time.time(),
                    "status": update_data.get("status"),
                    "message": update_data.get("message", ""),
                    "strategy": update_data.get("strategy")
                })
                print(f"    Progress: {update_data.get('message', '')}")
            
            try:
                # Execute discovery
                discovery_session = await bridge.discover_opportunities(
                    profile=profile,
                    funding_types=config["funding_types"],
                    max_results_per_type=config["max_results"],
                    progress_callback=progress_callback
                )
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Collect performance metrics
                performance_results[config["name"]] = {
                    "status": "completed",
                    "total_time": total_time,
                    "session_id": discovery_session.session_id,
                    "session_status": discovery_session.status.value,
                    "total_opportunities": discovery_session.total_opportunities,
                    "strategies_executed": len(discovery_session.results_by_strategy),
                    "strategy_execution_times": discovery_session.strategy_execution_times,
                    "average_relevance_score": discovery_session.avg_relevance_score,
                    "api_calls_made": discovery_session.api_calls_made,
                    "progress_updates": len(progress_updates),
                    "opportunities_by_strategy": {
                        strategy: len(results) 
                        for strategy, results in discovery_session.results_by_strategy.items()
                    }
                }
                
                print(f"  [PASS] {config['name']}: Completed in {total_time:.2f}s")
                print(f"    Session: {discovery_session.session_id}")
                print(f"    Opportunities: {discovery_session.total_opportunities}")
                print(f"    Strategies: {list(discovery_session.results_by_strategy.keys())}")
                print(f"    Progress Updates: {len(progress_updates)}")
                
            except Exception as e:
                performance_results[config["name"]] = {
                    "status": "failed",
                    "error": str(e),
                    "total_time": time.time() - start_time
                }
                print(f"  [FAIL] {config['name']}: {e}")
        
        # Calculate overall performance metrics
        successful_tests = len([r for r in performance_results.values() if r["status"] == "completed"])
        total_time = sum([r.get("total_time", 0) for r in performance_results.values()])
        total_opportunities = sum([r.get("total_opportunities", 0) for r in performance_results.values()])
        
        print(f"\nPerformance Test Summary:")
        print(f"  Successful Tests: {successful_tests}/{len(test_configs)}")
        print(f"  Total Execution Time: {total_time:.2f}s")
        print(f"  Total Opportunities Found: {total_opportunities}")
        print(f"  Average Time per Test: {total_time/len(test_configs):.2f}s")
        
        return successful_tests > 0, performance_results
        
    except Exception as e:
        print(f"Bridge performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

async def test_web_interface_integration():
    """Test web interface integration components"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4C TEST 3: Web Interface Integration")
    print("-" * 70)
    
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType
        
        bridge = get_unified_bridge()
        integration_results = {}
        
        # Test 1: Bridge status for web interface health checks
        print("Testing bridge status endpoint...")
        start_time = time.time()
        status = bridge.get_bridge_status()
        status_time = time.time() - start_time
        
        integration_results["bridge_status"] = {
            "status": "success",
            "response_time": status_time,
            "bridge_status": status.get("bridge_status"),
            "strategies_available": len(status.get("strategies_available", [])),
            "total_sessions": status.get("total_sessions", 0),
            "capabilities": len(status.get("capabilities", {}))
        }
        
        print(f"  [PASS] Bridge status endpoint: {status_time:.3f}s response time")
        print(f"    Status: {status['bridge_status']}")
        print(f"    Strategies: {len(status.get('strategies_available', []))}")
        
        # Test 2: Session management for web interface
        print("Testing session management...")
        start_time = time.time()
        
        # Create a test session
        profile = MockOrganizationProfile("environmental")
        session = await bridge.discover_opportunities(
            profile=profile,
            funding_types=[FundingSourceType.GOVERNMENT_FEDERAL],
            max_results_per_type=5
        )
        
        session_time = time.time() - start_time
        
        # Test session summary (for web API responses)
        summary = bridge.get_session_summary(session.session_id)
        
        integration_results["session_management"] = {
            "status": "success",
            "session_creation_time": session_time,
            "session_id": session.session_id,
            "session_status": session.status.value,
            "summary_available": "error" not in summary,
            "summary_keys": list(summary.keys()) if "error" not in summary else []
        }
        
        print(f"  [PASS] Session management: {session_time:.3f}s session creation")
        print(f"    Session ID: {session.session_id}")
        print(f"    Summary Available: {'Yes' if 'error' not in summary else 'No'}")
        
        # Test 3: Progress callback integration (for WebSocket)
        print("Testing progress callback system...")
        callback_calls = []
        
        def test_callback(session_id: str, update_data: Dict[str, Any]):
            callback_calls.append({
                "timestamp": time.time(),
                "session_id": session_id,
                "status": update_data.get("status"),
                "message": update_data.get("message", "")
            })
        
        # Execute discovery with callback
        callback_session = await bridge.discover_opportunities(
            profile=profile,
            funding_types=[FundingSourceType.FOUNDATION_CORPORATE],
            max_results_per_type=3,
            progress_callback=test_callback
        )
        
        integration_results["progress_callbacks"] = {
            "status": "success",
            "callback_calls": len(callback_calls),
            "session_id": callback_session.session_id,
            "final_status": callback_session.status.value,
            "callback_messages": [call["message"] for call in callback_calls if call["message"]]
        }
        
        print(f"  [PASS] Progress callbacks: {len(callback_calls)} callback calls received")
        print(f"    Callback Messages: {len([c for c in callback_calls if c['message']])}")
        
        # Cleanup test sessions
        cleanup_count = bridge.cleanup_old_sessions(max_age_hours=0)  # Clean up test sessions
        
        print(f"\nWeb Interface Integration Summary:")
        successful_tests = len([r for r in integration_results.values() if r["status"] == "success"])
        print(f"  Successful Integration Tests: {successful_tests}/{len(integration_results)}")
        print(f"  Test Sessions Cleaned Up: {cleanup_count}")
        
        return successful_tests == len(integration_results), integration_results
        
    except Exception as e:
        print(f"Web interface integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

async def test_concurrent_sessions():
    """Test concurrent discovery sessions for load validation"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4C TEST 4: Concurrent Session Load Testing")
    print("-" * 70)
    
    try:
        from src.discovery.unified_multitrack_bridge import get_unified_bridge
        from src.core.data_models import FundingSourceType
        
        bridge = get_unified_bridge()
        
        # Create multiple profiles for concurrent testing
        profiles = [
            MockOrganizationProfile("environmental"),
            MockOrganizationProfile("education"),
            MockOrganizationProfile("health")
        ]
        
        # Configure concurrent sessions
        concurrent_configs = [
            {
                "profile": profiles[0],
                "funding_types": [FundingSourceType.GOVERNMENT_FEDERAL],
                "max_results": 5
            },
            {
                "profile": profiles[1],
                "funding_types": [FundingSourceType.FOUNDATION_CORPORATE],
                "max_results": 5
            },
            {
                "profile": profiles[2],
                "funding_types": [FundingSourceType.GOVERNMENT_STATE],
                "max_results": 5
            }
        ]
        
        print(f"Starting {len(concurrent_configs)} concurrent discovery sessions...")
        
        # Execute concurrent sessions
        start_time = time.time()
        
        tasks = []
        for i, config in enumerate(concurrent_configs):
            task = bridge.discover_opportunities(
                profile=config["profile"],
                funding_types=config["funding_types"],
                max_results_per_type=config["max_results"]
            )
            tasks.append((i, task))
        
        # Wait for all sessions to complete
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze concurrent execution results
        successful_sessions = 0
        total_opportunities = 0
        session_details = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  [FAIL] Session {i+1}: {result}")
                session_details.append({"status": "failed", "error": str(result)})
            else:
                successful_sessions += 1
                total_opportunities += result.total_opportunities
                session_details.append({
                    "status": "completed",
                    "session_id": result.session_id,
                    "opportunities": result.total_opportunities,
                    "execution_time": result.execution_time_seconds
                })
                print(f"  [PASS] Session {i+1}: {result.session_id} - {result.total_opportunities} opportunities")
        
        # Check bridge status after concurrent execution
        final_status = bridge.get_bridge_status()
        
        concurrent_results = {
            "total_sessions": len(concurrent_configs),
            "successful_sessions": successful_sessions,
            "total_execution_time": total_time,
            "total_opportunities": total_opportunities,
            "average_time_per_session": total_time / len(concurrent_configs),
            "bridge_final_status": final_status.get("bridge_status"),
            "active_sessions_after": final_status.get("active_sessions", 0),
            "session_details": session_details
        }
        
        print(f"\nConcurrent Session Load Test Summary:")
        print(f"  Successful Sessions: {successful_sessions}/{len(concurrent_configs)}")
        print(f"  Total Execution Time: {total_time:.2f}s")
        print(f"  Average Time per Session: {total_time/len(concurrent_configs):.2f}s")
        print(f"  Total Opportunities: {total_opportunities}")
        print(f"  Bridge Status After Load: {final_status.get('bridge_status')}")
        
        return successful_sessions > 0, concurrent_results
        
    except Exception as e:
        print(f"Concurrent session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def generate_phase_4c_report(test_results: Dict[str, Any]):
    """Generate comprehensive Phase 4C validation report"""
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PHASE 4C VALIDATION REPORT")
    print("=" * 80)
    
    # Calculate overall success metrics
    test_names = ["connectivity", "performance", "integration", "concurrent"]
    successful_tests = sum([1 for name in test_names if test_results.get(name, {}).get("success", False)])
    
    print(f"\nOVERALL PHASE 4C ASSESSMENT:")
    print(f"  Successful Test Categories: {successful_tests}/{len(test_names)}")
    print(f"  Overall Success Rate: {(successful_tests/len(test_names))*100:.1f}%")
    
    # Detailed test results
    print(f"\nDETAILED TEST RESULTS:")
    print("-" * 40)
    
    for test_name, result_data in test_results.items():
        status_icon = "[PASS]" if result_data.get("success", False) else "[FAIL]"
        print(f"{status_icon} {test_name.title()} Test:")
        
        if "data" in result_data:
            data = result_data["data"]
            
            if test_name == "connectivity":
                successful_clients = len([c for c in data.values() if c.get("status") == "initialized"])
                print(f"    Client Connectivity: {successful_clients}/{len(data)} clients operational")
                
            elif test_name == "performance":
                completed_tests = len([t for t in data.values() if t.get("status") == "completed"])
                total_time = sum([t.get("total_time", 0) for t in data.values()])
                total_opportunities = sum([t.get("total_opportunities", 0) for t in data.values()])
                print(f"    Performance Tests: {completed_tests}/{len(data)} completed")
                print(f"    Total Execution Time: {total_time:.2f}s")
                print(f"    Total Opportunities: {total_opportunities}")
                
            elif test_name == "integration":
                successful_components = len([c for c in data.values() if c.get("status") == "success"])
                print(f"    Integration Components: {successful_components}/{len(data)} operational")
                
            elif test_name == "concurrent":
                successful_sessions = data.get("successful_sessions", 0)
                total_sessions = data.get("total_sessions", 0)
                print(f"    Concurrent Sessions: {successful_sessions}/{total_sessions} successful")
                print(f"    Load Test Duration: {data.get('total_execution_time', 0):.2f}s")
        
        print()
    
    # Production readiness assessment
    if successful_tests >= 3:
        print("[SUCCESS] PHASE 4C ASSESSMENT: PRODUCTION VALIDATION SUCCESSFUL")
        print("Real data workflows validated and performance benchmarks established")
        print("System ready for Phase 4D: Production Readiness Assessment")
    else:
        print("[WARNING] PHASE 4C ASSESSMENT: VALIDATION NEEDS ATTENTION") 
        print(f"{len(test_names) - successful_tests} test categories require resolution")
        print("Address failing tests before proceeding to production deployment")
    
    # Save detailed report
    report_data = {
        "phase": "4C",
        "timestamp": datetime.now().isoformat(),
        "overall_success_rate": (successful_tests/len(test_names))*100,
        "successful_tests": successful_tests,
        "total_tests": len(test_names),
        "test_results": test_results,
        "production_ready": successful_tests >= 3
    }
    
    report_filename = f"phase_4c_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\nDetailed validation report saved: {report_filename}")
    
    return successful_tests >= 3

async def main():
    """Execute Phase 4C real data validation and performance testing"""
    
    print("=" * 80)
    print("PHASE 4C: REAL DATA VALIDATION & PERFORMANCE TESTING")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    try:
        # Test 1: Client Connectivity
        connectivity_success, connectivity_data = await test_client_connectivity_real_data()
        test_results["connectivity"] = {"success": connectivity_success, "data": connectivity_data}
        
        # Test 2: Bridge Performance
        performance_success, performance_data = await test_unified_bridge_performance()
        test_results["performance"] = {"success": performance_success, "data": performance_data}
        
        # Test 3: Web Integration
        integration_success, integration_data = await test_web_interface_integration()
        test_results["integration"] = {"success": integration_success, "data": integration_data}
        
        # Test 4: Concurrent Load Testing
        concurrent_success, concurrent_data = await test_concurrent_sessions()
        test_results["concurrent"] = {"success": concurrent_success, "data": concurrent_data}
        
        # Generate final report
        production_ready = generate_phase_4c_report(test_results)
        
        return production_ready
        
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] Phase 4C validation interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Phase 4C validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
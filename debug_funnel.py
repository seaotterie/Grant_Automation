#!/usr/bin/env python3
"""
Debug script to test FunnelManager integration
"""

from src.discovery.funnel_manager import funnel_manager, FunnelManager
from src.discovery.base_discoverer import DiscoveryResult, FunnelStage, FundingType
from datetime import datetime

print("=== FunnelManager Debug Test ===")

# Test 1: Direct FunnelManager usage
print("\n1. Testing direct FunnelManager creation:")
fm1 = FunnelManager()
test_opportunity = DiscoveryResult(
    organization_name="Test Organization",
    source_type=FundingType.GRANTS,
    discovery_source='debug_test',
    opportunity_id="test_001",
    description="Test opportunity for debugging",
    funnel_stage=FunnelStage.PROSPECTS
)
fm1.add_opportunities("debug_profile", [test_opportunity])
print(f"FM1 opportunities for debug_profile: {len(fm1.get_all_opportunities('debug_profile'))}")

# Test 2: Global instance usage
print("\n2. Testing global funnel_manager instance:")
test_opportunity2 = DiscoveryResult(
    organization_name="Global Test Organization",
    source_type=FundingType.GRANTS,
    discovery_source='global_debug_test',
    opportunity_id="global_test_001",
    description="Global test opportunity for debugging",
    funnel_stage=FunnelStage.PROSPECTS
)
funnel_manager.add_opportunities("global_debug_profile", [test_opportunity2])
print(f"Global funnel_manager opportunities for global_debug_profile: {len(funnel_manager.get_all_opportunities('global_debug_profile'))}")

# Test 3: Check existing profile opportunities
print("\n3. Checking existing profile opportunities:")
for profile_id in ["test_profile_001", "test_profile_002", "test_profile"]:
    opportunities = funnel_manager.get_all_opportunities(profile_id)
    print(f"Profile {profile_id}: {len(opportunities)} opportunities")
    if opportunities:
        for opp in opportunities:
            print(f"  - {opp.organization_name} ({opp.opportunity_id})")

# Test 4: Check all stored profiles
print("\n4. All profiles in funnel_manager:")
print(f"Profiles with opportunities: {list(funnel_manager.opportunities.keys())}")
for profile_id, opportunities in funnel_manager.opportunities.items():
    print(f"  {profile_id}: {len(opportunities)} opportunities")

print("\n=== Debug Test Complete ===")
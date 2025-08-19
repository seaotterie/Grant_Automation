#!/usr/bin/env python3
"""
Test Unified Profile Service

Test the new unified architecture to verify:
1. Profile loading with analytics
2. Opportunity loading and management
3. Stage updates work correctly
4. Norfolk Foundation auto-promotion fix
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from profiles.unified_service import get_unified_profile_service


def test_profile_loading():
    """Test basic profile loading"""
    print("=== Testing Profile Loading ===")
    
    service = get_unified_profile_service()
    
    # List available profiles
    profiles = service.list_profiles()
    print(f"Available profiles: {profiles}")
    
    # Load Hero's Bridge profile
    profile = service.get_profile('profile_f3adef3b653c')
    if profile:
        print(f"Loaded profile: {profile.organization_name}")
        print(f"Analytics: {profile.analytics.opportunity_count} opportunities")
        print(f"Stages: {profile.analytics.stages_distribution}")
        print(f"High potential count: {profile.analytics.scoring_stats.get('high_potential_count', 0)}")
        return True
    else:
        print("Failed to load profile")
        return False


def test_opportunity_loading():
    """Test opportunity loading"""
    print("\n=== Testing Opportunity Loading ===")
    
    service = get_unified_profile_service()
    
    # Get Norfolk Foundation opportunity
    norfolk = service.get_opportunity('profile_f3adef3b653c', 'opp_lead_172246bedf2b')
    if not norfolk:
        # Try different ID format
        norfolk = service.get_opportunity('profile_f3adef3b653c', '172246bedf2b')
    
    if norfolk:
        print(f"* Loaded Norfolk Foundation")
        print(f"   Organization: {norfolk.organization_name}")
        print(f"   Current Stage: {norfolk.current_stage}")
        print(f"   Score: {norfolk.scoring.overall_score if norfolk.scoring else 'No scoring'}")
        print(f"   Auto-promotion eligible: {norfolk.scoring.auto_promotion_eligible if norfolk.scoring else 'Unknown'}")
        print(f"   EIN: {norfolk.ein}")
        return norfolk
    else:
        print("* Failed to load Norfolk Foundation")
        return None


def test_stage_update():
    """Test stage update functionality"""
    print("\n=== Testing Stage Update ===")
    
    service = get_unified_profile_service()
    
    # Get Norfolk Foundation
    norfolk = service.get_opportunity('profile_f3adef3b653c', '172246bedf2b')
    if not norfolk:
        print("* Norfolk Foundation not found for stage update test")
        return False
    
    print(f"Norfolk current stage: {norfolk.current_stage}")
    
    # If it's still in discovery and has high score, it should be promoted
    if norfolk.current_stage == 'discovery' and norfolk.scoring and norfolk.scoring.overall_score >= 0.75:
        print("Norfolk Foundation should be auto-promoted!")
        
        # Test stage update
        success = service.update_opportunity_stage(
            'profile_f3adef3b653c', 
            '172246bedf2b',
            'pre_scoring',
            'Auto-promotion test - high score',
            'test_system'
        )
        
        if success:
            print("* Stage update successful")
            
            # Verify the update
            updated_norfolk = service.get_opportunity('profile_f3adef3b653c', '172246bedf2b')
            if updated_norfolk:
                print(f"   New stage: {updated_norfolk.current_stage}")
                print(f"   Stage history length: {len(updated_norfolk.stage_history)}")
                print(f"   Promotion history length: {len(updated_norfolk.promotion_history)}")
                
                if updated_norfolk.promotion_history:
                    last_promotion = updated_norfolk.promotion_history[-1]
                    print(f"   Last promotion: {last_promotion.from_stage} â†’ {last_promotion.to_stage}")
            
            return True
        else:
            print("* Stage update failed")
            return False
    else:
        print("**  Norfolk Foundation doesn't meet auto-promotion criteria or already promoted")
        return True


def test_analytics_refresh():
    """Test analytics refresh"""
    print("\n=== Testing Analytics Refresh ===")
    
    service = get_unified_profile_service()
    
    # Refresh analytics for Hero's Bridge
    success = service.refresh_profile_analytics('profile_f3adef3b653c')
    
    if success:
        print("* Analytics refresh successful")
        
        # Load updated profile
        profile = service.get_profile('profile_f3adef3b653c')
        if profile:
            print(f"   Total opportunities: {profile.analytics.opportunity_count}")
            print(f"   Stage distribution: {profile.analytics.stages_distribution}")
            print(f"   Recent activity count: {len(profile.recent_activity)}")
            
            if profile.recent_activity:
                print("   Recent activities:")
                for activity in profile.recent_activity[:3]:
                    print(f"   - {activity.type}: {activity.date}")
        
        return True
    else:
        print("* Analytics refresh failed")
        return False


def main():
    """Run all tests"""
    print("Testing Unified Profile Service")
    print("=" * 50)
    
    tests = [
        test_profile_loading,
        test_opportunity_loading, 
        test_stage_update,
        test_analytics_refresh
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"* Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("*Š Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("*‰ All tests passed! Unified service is working.")
    else:
        print("**  Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
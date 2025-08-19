#!/usr/bin/env python3
"""
Comprehensive Test Script for Grant Automation Fixes
Verify all implemented fixes are working correctly

This script tests:
1. Data cleanup results (no corrupt records)
2. Auto-promotion threshold changes (75% working)
3. Stage progression functionality
4. High-scoring opportunities in correct stages
"""

import json
import requests
from pathlib import Path
import logging
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveFixTest:
    def __init__(self, data_dir: str = "data/profiles", api_base: str = "http://localhost:8000"):
        self.data_dir = Path(data_dir)
        self.leads_dir = self.data_dir / "leads"
        self.profiles_dir = self.data_dir / "profiles"
        self.api_base = api_base
        
        self.test_results = {
            'data_cleanup': {'passed': False, 'details': []},
            'promotion_thresholds': {'passed': False, 'details': []},
            'stage_progression': {'passed': False, 'details': []},
            'api_integration': {'passed': False, 'details': []},
            'overall_success': False
        }
        
    def run_comprehensive_test(self):
        """Run all test suites"""
        logger.info("Starting comprehensive fix verification...")
        
        # Test 1: Data cleanup verification
        self._test_data_cleanup()
        
        # Test 2: Promotion threshold verification
        self._test_promotion_thresholds()
        
        # Test 3: Stage progression verification
        self._test_stage_progression()
        
        # Test 4: API integration test
        self._test_api_integration()
        
        # Generate final report
        self._generate_test_report()
        
    def _test_data_cleanup(self):
        """Test that data cleanup was successful"""
        logger.info("Testing data cleanup results...")
        
        empty_name_count = 0
        low_score_foundation_count = 0
        total_leads = 0
        
        for lead_file in self.leads_dir.glob("*.json"):
            total_leads += 1
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                org_name = data.get("organization_name", "").strip()
                source = data.get("source", "")
                score = data.get("compatibility_score", 0.0)
                
                # Check for empty names
                if not org_name or org_name in ["[Organization Name Missing]", "N/A"]:
                    empty_name_count += 1
                    
                # Check for low-score foundation records
                if source == "unified_discovery_foundation" and score < 0.5:
                    low_score_foundation_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        # Evaluate results
        if empty_name_count == 0 and low_score_foundation_count == 0:
            self.test_results['data_cleanup']['passed'] = True
            self.test_results['data_cleanup']['details'].append(f"✅ No corrupt records found ({total_leads} clean leads)")
        else:
            self.test_results['data_cleanup']['details'].append(f"❌ Found {empty_name_count} empty names, {low_score_foundation_count} low-score foundation records")
            
        logger.info(f"Data cleanup test: {'PASSED' if self.test_results['data_cleanup']['passed'] else 'FAILED'}")
        
    def _test_promotion_thresholds(self):
        """Test that promotion thresholds are working correctly"""
        logger.info("Testing promotion threshold changes...")
        
        high_scorers_discovery = 0
        high_scorers_promoted = 0
        promotion_threshold_met = 0
        
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                score = data.get("compatibility_score", 0.0)
                stage = data.get("pipeline_stage", "discovery")
                auto_promoted = data.get("match_factors", {}).get("auto_promoted", False)
                
                # Count high scorers (75%+)
                if score >= 0.75:
                    promotion_threshold_met += 1
                    
                    if stage == "discovery":
                        high_scorers_discovery += 1
                    elif stage in ["pre_scoring", "qualified_prospects"]:
                        high_scorers_promoted += 1
                        
            except Exception as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        # Evaluate results - most high scorers should be promoted
        promotion_rate = high_scorers_promoted / promotion_threshold_met if promotion_threshold_met > 0 else 0
        
        if promotion_rate > 0.8:  # 80%+ of high scorers should be promoted
            self.test_results['promotion_thresholds']['passed'] = True
            self.test_results['promotion_thresholds']['details'].append(f"✅ {high_scorers_promoted}/{promotion_threshold_met} high scorers promoted ({promotion_rate:.1%})")
        else:
            self.test_results['promotion_thresholds']['details'].append(f"❌ Only {high_scorers_promoted}/{promotion_threshold_met} high scorers promoted ({promotion_rate:.1%})")
            
        logger.info(f"Promotion threshold test: {'PASSED' if self.test_results['promotion_thresholds']['passed'] else 'FAILED'}")
        
    def _test_stage_progression(self):
        """Test that stage progression is working"""
        logger.info("Testing stage progression...")
        
        stage_counts = {}
        high_score_stages = {}
        
        for lead_file in self.leads_dir.glob("*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                score = data.get("compatibility_score", 0.0)
                stage = data.get("pipeline_stage", "discovery")
                
                # Count by stage
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                
                # Count high scorers by stage
                if score >= 0.75:
                    high_score_stages[stage] = high_score_stages.get(stage, 0) + 1
                    
            except Exception as e:
                logger.warning(f"Error processing {lead_file}: {e}")
        
        # Evaluate results
        qualified_prospects = stage_counts.get("pre_scoring", 0)
        discovery_stage = stage_counts.get("discovery", 0)
        
        if qualified_prospects > 0:
            self.test_results['stage_progression']['passed'] = True
            self.test_results['stage_progression']['details'].append(f"✅ Found {qualified_prospects} opportunities in qualified_prospects stage")
            self.test_results['stage_progression']['details'].append(f"Stage distribution: {stage_counts}")
        else:
            self.test_results['stage_progression']['details'].append(f"❌ No opportunities found in qualified_prospects stage")
            
        logger.info(f"Stage progression test: {'PASSED' if self.test_results['stage_progression']['passed'] else 'FAILED'}")
        
    def _test_api_integration(self):
        """Test API integration and data accessibility"""
        logger.info("Testing API integration...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                self.test_results['api_integration']['details'].append("✅ API health check passed")
                
                # Test profile endpoints
                profile_response = requests.get(f"{self.api_base}/api/profiles", timeout=5)
                if profile_response.status_code == 200:
                    profiles = profile_response.json()
                    heros_bridge = next((p for p in profiles if "Heros Bridge" in p.get("name", "")), None)
                    
                    if heros_bridge:
                        profile_id = heros_bridge["profile_id"]
                        
                        # Test opportunities endpoint
                        opp_response = requests.get(f"{self.api_base}/api/profiles/{profile_id}/opportunities", timeout=5)
                        if opp_response.status_code == 200:
                            opportunities = opp_response.json()
                            self.test_results['api_integration']['details'].append(f"✅ Found {len(opportunities)} opportunities via API")
                            
                            # Check for qualified prospects
                            qualified = [o for o in opportunities if o.get("pipeline_stage") == "pre_scoring"]
                            if len(qualified) > 0:
                                self.test_results['api_integration']['passed'] = True
                                self.test_results['api_integration']['details'].append(f"✅ Found {len(qualified)} qualified prospects via API")
                            else:
                                self.test_results['api_integration']['details'].append("❌ No qualified prospects found via API")
                        else:
                            self.test_results['api_integration']['details'].append(f"❌ Opportunities API failed: {opp_response.status_code}")
                    else:
                        self.test_results['api_integration']['details'].append("❌ Heros Bridge profile not found")
                else:
                    self.test_results['api_integration']['details'].append(f"❌ Profiles API failed: {profile_response.status_code}")
            else:
                self.test_results['api_integration']['details'].append(f"❌ API health check failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.test_results['api_integration']['details'].append(f"❌ API connection failed: {e}")
            
        logger.info(f"API integration test: {'PASSED' if self.test_results['api_integration']['passed'] else 'FAILED'}")
        
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("COMPREHENSIVE FIX VERIFICATION REPORT")
        print("="*70)
        
        overall_passed = 0
        total_tests = 0
        
        for test_name, result in self.test_results.items():
            if test_name == 'overall_success':
                continue
                
            total_tests += 1
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            
            if result['passed']:
                overall_passed += 1
                
            print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
            for detail in result['details']:
                print(f"  {detail}")
        
        print("\n" + "-"*70)
        print(f"OVERALL RESULT: {overall_passed}/{total_tests} tests passed")
        
        # Determine overall success
        self.test_results['overall_success'] = overall_passed == total_tests
        
        if self.test_results['overall_success']:
            print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
            print("\nSYSTEM IS READY FOR PRODUCTION USE:")
            print("• No corrupt legacy data remains")
            print("• Auto-promotion working at 75% threshold")
            print("• High-scoring opportunities in qualified_prospects stage")
            print("• PLAN tab will now show promoted opportunities")
            print("• API integration fully functional")
        else:
            print("⚠️  SOME ISSUES DETECTED - REVIEW FAILED TESTS")
            
        print("="*70)


if __name__ == "__main__":
    test = ComprehensiveFixTest()
    test.run_comprehensive_test()
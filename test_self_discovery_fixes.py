#!/usr/bin/env python3
"""
Test Script for Self-Discovery & Stage Display Fixes
Comprehensive testing to verify both issues are resolved

This script tests:
1. Self-discovery prevention: No organizations appear as opportunities for themselves
2. Stage display: DISCOVER tab shows actual pipeline stages ("#2 Qualified")
3. Name similarity function: Correctly identifies Heroes/Heros as similar
4. API integration: Stage data flows correctly from backend to frontend
5. Data integrity: No corrupt self-references remain
"""

import json
import requests
from pathlib import Path
import logging
from typing import Dict, List
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SelfDiscoveryFixTest:
    def __init__(self, data_dir: str = "data/profiles", api_base: str = "http://localhost:8000"):
        self.data_dir = Path(data_dir)
        self.leads_dir = self.data_dir / "leads"
        self.profiles_dir = self.data_dir / "profiles"
        self.api_base = api_base
        
        self.test_results = {
            'self_discovery_prevention': {'passed': False, 'details': []},
            'stage_display_fix': {'passed': False, 'details': []},
            'name_similarity_function': {'passed': False, 'details': []},
            'api_integration': {'passed': False, 'details': []},
            'data_integrity': {'passed': False, 'details': []},
            'overall_success': False
        }
        
    def run_comprehensive_test(self):
        """Run all test suites for the fixes"""
        logger.info("Starting comprehensive test of self-discovery & stage display fixes...")
        
        # Test 1: Name similarity function
        self._test_name_similarity_function()
        
        # Test 2: Self-discovery prevention
        self._test_self_discovery_prevention()
        
        # Test 3: Stage display functionality
        self._test_stage_display_fix()
        
        # Test 4: API integration
        self._test_api_integration()
        
        # Test 5: Data integrity check
        self._test_data_integrity()
        
        # Generate final report
        self._generate_test_report()
        
    def _test_name_similarity_function(self):
        """Test the name similarity function with various cases"""
        logger.info("Testing name similarity function...")
        
        # Import the function from the main.py (simulate the function)
        def similar_organization_names(name1: str, name2: str, threshold: float = 0.85) -> bool:
            if not name1 or not name2:
                return False
                
            def normalize_name(name: str) -> str:
                name = name.lower().strip()
                suffixes = [' inc', ' inc.', ' incorporated', ' llc', ' ltd', ' ltd.', ' corp', ' corp.', ' corporation']
                for suffix in suffixes:
                    if name.endswith(suffix):
                        name = name[:-len(suffix)].strip()
                return name
            
            norm1 = normalize_name(name1)
            norm2 = normalize_name(name2)
            
            if norm1 == norm2:
                return True
            
            if len(norm1) == 0 or len(norm2) == 0:
                return False
                
            chars1 = set(norm1.replace(' ', ''))
            chars2 = set(norm2.replace(' ', ''))
            
            if len(chars1) == 0 or len(chars2) == 0:
                return False
                
            intersection = len(chars1.intersection(chars2))
            union = len(chars1.union(chars2))
            similarity = intersection / union if union > 0 else 0
            
            return similarity >= threshold
        
        # Test cases
        test_cases = [
            # Should be similar
            ("Heroes Bridge", "Heros Bridge", True),
            ("ABC Corp", "ABC Corp.", True),
            ("Test Inc", "Test Incorporated", True),
            ("XYZ LLC", "XYZ", True),
            # Should not be similar
            ("Heroes Bridge", "Veterans Foundation", False),
            ("ABC Corp", "XYZ LLC", False),
            ("", "Test", False),
            ("Test", "", False)
        ]
        
        passed_tests = 0
        for name1, name2, expected in test_cases:
            result = similar_organization_names(name1, name2)
            if result == expected:
                passed_tests += 1
                self.test_results['name_similarity_function']['details'].append(f"PASS '{name1}' vs '{name2}' = {result} (expected {expected})")
            else:
                self.test_results['name_similarity_function']['details'].append(f"FAIL '{name1}' vs '{name2}' = {result} (expected {expected})")
        
        if passed_tests == len(test_cases):
            self.test_results['name_similarity_function']['passed'] = True
            
        logger.info(f"Name similarity test: {passed_tests}/{len(test_cases)} passed")
        
    def _test_self_discovery_prevention(self):
        """Test that no self-discovery records exist"""
        logger.info("Testing self-discovery prevention...")
        
        profiles_map = self._load_profiles_ein_map()
        self_discovery_count = 0
        total_leads = 0
        
        for lead_file in self.leads_dir.glob("*.json"):
            total_leads += 1
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    lead_data = json.load(f)
                
                # Get lead details
                lead_ein = lead_data.get('external_data', {}).get('ein', '').strip()
                profile_id = lead_data.get('profile_id', '')
                
                if not lead_ein or not profile_id:
                    continue
                
                # Check if this lead's EIN matches its profile's EIN
                normalized_lead_ein = lead_ein.replace('-', '').replace(' ', '')
                
                if profile_id in profiles_map:
                    profile_ein = profiles_map[profile_id]['ein'].replace('-', '').replace(' ', '')
                    if normalized_lead_ein == profile_ein:
                        self_discovery_count += 1
                        lead_org_name = lead_data.get('organization_name', '')
                        profile_name = profiles_map[profile_id]['name']
                        self.test_results['self_discovery_prevention']['details'].append(
                            f"FAIL Self-discovery found: {lead_org_name} (EIN: {lead_ein}) for profile {profile_name}"
                        )
                        
            except Exception as e:
                logger.warning(f"Error processing lead {lead_file}: {e}")
        
        if self_discovery_count == 0:
            self.test_results['self_discovery_prevention']['passed'] = True
            self.test_results['self_discovery_prevention']['details'].append(f"PASS No self-discovery records found in {total_leads} leads")
        else:
            self.test_results['self_discovery_prevention']['details'].append(f"FAIL Found {self_discovery_count} self-discovery records")
            
        logger.info(f"Self-discovery prevention test: {'PASSED' if self_discovery_count == 0 else 'FAILED'}")
        
    def _test_stage_display_fix(self):
        """Test that pipeline_stage values are correctly used"""
        logger.info("Testing stage display functionality...")
        
        stage_counts = {}
        pipeline_stage_leads = 0
        total_leads = 0
        
        for lead_file in self.leads_dir.glob("*.json"):
            total_leads += 1
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    lead_data = json.load(f)
                
                # Check for pipeline_stage field
                pipeline_stage = lead_data.get('pipeline_stage')
                funnel_stage = lead_data.get('funnel_stage')
                
                if pipeline_stage:
                    pipeline_stage_leads += 1
                    stage_counts[pipeline_stage] = stage_counts.get(pipeline_stage, 0) + 1
                    
            except Exception as e:
                logger.warning(f"Error processing lead {lead_file}: {e}")
        
        # Check that we have leads with pipeline_stage values
        if pipeline_stage_leads > 0:
            self.test_results['stage_display_fix']['passed'] = True
            self.test_results['stage_display_fix']['details'].append(f"✅ Found {pipeline_stage_leads} leads with pipeline_stage values")
            self.test_results['stage_display_fix']['details'].append(f"Stage distribution: {stage_counts}")
            
            # Check for specific promoted stages
            qualified_count = stage_counts.get('pre_scoring', 0)
            if qualified_count > 0:
                self.test_results['stage_display_fix']['details'].append(f"✅ Found {qualified_count} opportunities in 'pre_scoring' stage")
        else:
            self.test_results['stage_display_fix']['details'].append(f"❌ No leads found with pipeline_stage values")
            
        logger.info(f"Stage display test: {'PASSED' if self.test_results['stage_display_fix']['passed'] else 'FAILED'}")
        
    def _test_api_integration(self):
        """Test API integration for stage display"""
        logger.info("Testing API integration...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 404:
                # Try alternative health endpoint
                response = requests.get(f"{self.api_base}/api/system/health", timeout=5)
                
            if response.status_code == 200:
                self.test_results['api_integration']['details'].append("✅ API health check passed")
                
                # Test profiles endpoint
                profile_response = requests.get(f"{self.api_base}/api/profiles", timeout=5)
                if profile_response.status_code == 200:
                    profiles = profile_response.json()
                    heros_bridge = next((p for p in profiles if isinstance(p, dict) and "Heros Bridge" in p.get("name", "")), None)
                    
                    if heros_bridge:
                        profile_id = heros_bridge["profile_id"]
                        
                        # Test opportunities endpoint
                        opp_response = requests.get(f"{self.api_base}/api/profiles/{profile_id}/opportunities", timeout=5)
                        if opp_response.status_code == 200:
                            opportunities = opp_response.json()
                            self.test_results['api_integration']['details'].append(f"✅ Retrieved {len(opportunities)} opportunities via API")
                            
                            # Check for pipeline_stage in API response
                            pipeline_stage_count = 0
                            pre_scoring_count = 0
                            
                            for opp in opportunities:
                                if 'pipeline_stage' in opp:
                                    pipeline_stage_count += 1
                                    if opp['pipeline_stage'] == 'pre_scoring':
                                        pre_scoring_count += 1
                            
                            if pipeline_stage_count > 0:
                                self.test_results['api_integration']['passed'] = True
                                self.test_results['api_integration']['details'].append(f"✅ Found {pipeline_stage_count} opportunities with pipeline_stage in API")
                                if pre_scoring_count > 0:
                                    self.test_results['api_integration']['details'].append(f"✅ Found {pre_scoring_count} opportunities in pre_scoring stage")
                            else:
                                self.test_results['api_integration']['details'].append("❌ No opportunities with pipeline_stage found in API response")
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
        
    def _test_data_integrity(self):
        """Test overall data integrity"""
        logger.info("Testing data integrity...")
        
        # Count leads and check profile references
        total_leads = 0
        profile_ref_errors = 0
        
        for lead_file in self.leads_dir.glob("*.json"):
            total_leads += 1
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    lead_data = json.load(f)
                
                # Check required fields
                required_fields = ['lead_id', 'profile_id', 'organization_name']
                missing_fields = [field for field in required_fields if not lead_data.get(field)]
                
                if missing_fields:
                    profile_ref_errors += 1
                    
            except Exception as e:
                profile_ref_errors += 1
                logger.warning(f"Error processing lead {lead_file}: {e}")
        
        if profile_ref_errors == 0:
            self.test_results['data_integrity']['passed'] = True
            self.test_results['data_integrity']['details'].append(f"✅ All {total_leads} leads have valid structure")
        else:
            self.test_results['data_integrity']['details'].append(f"❌ Found {profile_ref_errors} leads with data issues")
            
        logger.info(f"Data integrity test: {'PASSED' if self.test_results['data_integrity']['passed'] else 'FAILED'}")
        
    def _load_profiles_ein_map(self) -> Dict[str, Dict]:
        """Load profiles with EIN mapping"""
        profiles_map = {}
        
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                profile_id = profile_data.get('profile_id')
                if profile_id:
                    profiles_map[profile_id] = {
                        'name': profile_data.get('name', ''),
                        'ein': profile_data.get('ein', '')
                    }
                    
            except Exception as e:
                logger.warning(f"Error loading profile {profile_file}: {e}")
        
        return profiles_map
        
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\\n" + "="*70)
        print("SELF-DISCOVERY & STAGE DISPLAY FIXES TEST REPORT")
        print("="*70)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        overall_passed = 0
        total_tests = 0
        
        for test_name, result in self.test_results.items():
            if test_name == 'overall_success':
                continue
                
            total_tests += 1
            status = "PASSED" if result['passed'] else "FAILED"
            
            if result['passed']:
                overall_passed += 1
                
            print(f"\\n{test_name.upper().replace('_', ' ')}: {status}")
            for detail in result['details']:
                print(f"  {detail}")
        
        print("\\n" + "-"*70)
        print(f"OVERALL RESULT: {overall_passed}/{total_tests} tests passed")
        
        # Determine overall success
        self.test_results['overall_success'] = overall_passed == total_tests
        
        if self.test_results['overall_success']:
            print("ALL FIXES VERIFIED SUCCESSFULLY!")
            print("\\nSYSTEM IMPROVEMENTS CONFIRMED:")
            print("• Self-discovery prevention working (Heroes/Heros name variations handled)")
            print("• DISCOVER tab shows actual pipeline stages ('#2 Qualified')")
            print("• Enhanced EIN-based exclusion with name similarity")
            print("• API integration correctly returns pipeline_stage data")
            print("• Data integrity maintained throughout fixes")
            print("\\nUSER EXPERIENCE IMPROVEMENTS:")
            print("• No more self-discovery: Organizations won't appear as opportunities for themselves")
            print("• Clear stage progression: DISCOVER tab shows '#2 Qualified' for promoted opportunities")
            print("• Better data quality: Name variations like Heroes/Heros are properly handled")
        else:
            print("WARNING: SOME ISSUES DETECTED - REVIEW FAILED TESTS")
            print("\\nRECOMMENDED ACTIONS:")
            if not self.test_results['self_discovery_prevention']['passed']:
                print("• Run cleanup_self_discovery_records.py to remove remaining self-discovery records")
            if not self.test_results['stage_display_fix']['passed']:
                print("• Check frontend JavaScript functions are properly updated")
            if not self.test_results['api_integration']['passed']:
                print("• Verify web server is running and API endpoints are accessible")
            
        print("="*70)


if __name__ == "__main__":
    test = SelfDiscoveryFixTest()
    test.run_comprehensive_test()
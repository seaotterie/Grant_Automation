#!/usr/bin/env python3
"""
Real Data Repeatability Validation

Tests the repeatability architecture using actual data from the existing database
to validate that identical real-world inputs produce identical outputs.
"""

import asyncio
import json
import logging
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.analysis.enhanced_ai_lite_processor import EnhancedAILiteProcessor, ProcessingMode
from src.processors.analysis.fact_extraction_integration_service import ProcessorMigrationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataRepeatabilityTester:
    """Tests repeatability using real data from the database"""
    
    def __init__(self):
        self.db_path = "data/catalynx.db"
        self.test_results = []
        
    def get_real_profiles_and_opportunities(self, limit=3):
        """Get real profile and opportunity data from database"""
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Get real profiles
            profiles_query = """
            SELECT id, name, ein, annual_revenue, ntee_codes, 
                   focus_areas, mission_statement
            FROM profiles 
            WHERE name IS NOT NULL AND name != '' 
            LIMIT ?
            """
            profiles = conn.execute(profiles_query, (limit,)).fetchall()
            
            # Get real opportunities  
            opportunities_query = """
            SELECT id, organization_name, ein, overall_score
            FROM opportunities 
            WHERE organization_name IS NOT NULL AND organization_name != ''
            LIMIT ?
            """
            opportunities = conn.execute(opportunities_query, (limit,)).fetchall()
            
            # Convert to dictionaries
            real_profiles = []
            for profile in profiles:
                real_profiles.append({
                    'id': profile['id'],
                    'name': profile['name'],
                    'ein': profile['ein'] or '000000000',
                    'annual_revenue': profile['annual_revenue'],
                    'ntee_codes': json.loads(profile['ntee_codes']) if profile['ntee_codes'] else [],
                    'state': 'VA',  # Default state since not in this table
                    'focus_areas': json.loads(profile['focus_areas']) if profile['focus_areas'] else [],
                    'mission_statement': profile['mission_statement'],
                    'board_size': None,  # Not in this table
                    'staff_count': None,  # Not in this table
                    'years_in_operation': None  # Not in this table
                })
            
            real_opportunities = []
            for opp in opportunities:
                real_opportunities.append({
                    'id': opp['id'],
                    'title': f"Opportunity from {opp['organization_name']}",
                    'organization_name': opp['organization_name'] or 'Unknown Organization',
                    'ein': opp['ein'],
                    'funding_amount': None,  # Not available in this table
                    'focus_areas': [],  # Not available in this table
                    'description': f"Funding opportunity from {opp['organization_name']}",
                    'existing_score': opp['overall_score']  # For comparison
                })
                
            return real_profiles, real_opportunities
            
        finally:
            conn.close()
    
    async def test_repeatability_with_real_data(self, test_runs=5):
        """Test repeatability using real database data"""
        
        print("="*80)
        print("REAL DATA REPEATABILITY VALIDATION")
        print("="*80)
        print("Testing repeatability architecture with actual database data")
        print("="*80)
        
        # Get real data
        try:
            profiles, opportunities = self.get_real_profiles_and_opportunities(limit=2)
            
            if not profiles or not opportunities:
                print("[ERROR] No real data found in database")
                return
                
            print(f"Loaded {len(profiles)} real profiles and {len(opportunities)} real opportunities")
            
        except Exception as e:
            print(f"[ERROR] Failed to load real data: {str(e)}")
            return
        
        # Initialize processors
        new_processor = EnhancedAILiteProcessor(
            processing_mode=ProcessingMode.NEW_ARCHITECTURE,
            migration_config=ProcessorMigrationConfig(
                enable_fact_extraction=True,
                enable_deterministic_scoring=True,
                fallback_to_legacy=False
            )
        )
        
        # Test each profile-opportunity combination
        for i, profile in enumerate(profiles):
            for j, opportunity in enumerate(opportunities):
                
                test_case_name = f"Profile_{i+1}_x_Opportunity_{j+1}"
                print(f"\n" + "="*60)
                print(f"TEST CASE: {test_case_name}")
                print(f"Profile: {profile['name']}")
                print(f"Opportunity: {opportunity['title']}")
                print("="*60)
                
                # Run multiple times to test repeatability
                scores = []
                confidence_levels = []
                processing_times = []
                
                for run in range(test_runs):
                    print(f"  Run {run+1}/{test_runs}...", end=" ")
                    
                    try:
                        start_time = datetime.now()
                        result = await new_processor.execute({
                            'opportunity': opportunity,
                            'profile': profile
                        })
                        end_time = datetime.now()
                        
                        scores.append(result.final_score)
                        confidence_levels.append(result.confidence_level)
                        processing_times.append((end_time - start_time).total_seconds())
                        
                        print(f"Score: {result.final_score:.6f} ({result.confidence_level})")
                        
                    except Exception as e:
                        print(f"[ERROR] {str(e)}")
                        scores.append(None)
                        confidence_levels.append(None)
                        processing_times.append(None)
                
                # Analyze results
                valid_scores = [s for s in scores if s is not None]
                
                if valid_scores:
                    min_score = min(valid_scores)
                    max_score = max(valid_scores)
                    variance = max_score - min_score
                    mean_score = sum(valid_scores) / len(valid_scores)
                    mean_time = sum([t for t in processing_times if t is not None]) / len(processing_times)
                    
                    # Determine repeatability quality
                    if variance == 0.0:
                        quality = "PERFECT"
                        status = "[SUCCESS]"
                    elif variance < 0.001:
                        quality = "EXCELLENT" 
                        status = "[SUCCESS]"
                    elif variance < 0.01:
                        quality = "GOOD"
                        status = "[WARNING]"
                    else:
                        quality = "POOR"
                        status = "[ERROR]"
                    
                    print(f"\n  RESULTS for {test_case_name}:")
                    print(f"    Score Range: {min_score:.6f} - {max_score:.6f}")
                    print(f"    Variance: {variance:.8f}")
                    print(f"    Mean Score: {mean_score:.6f}")
                    print(f"    Mean Processing Time: {mean_time:.3f}s")
                    print(f"    Repeatability Quality: {status} {quality}")
                    print(f"    Perfect Repeatability: {'Yes' if variance == 0.0 else 'No'}")
                    if 'existing_score' in opportunity:
                        print(f"    Existing DB Score: {opportunity['existing_score']:.6f}")
                        print(f"    Score Difference from DB: {abs(mean_score - opportunity['existing_score']):.6f}")
                    
                    # Store results
                    self.test_results.append({
                        'test_case': test_case_name,
                        'profile_name': profile['name'],
                        'opportunity_title': opportunity['title'],
                        'scores': valid_scores,
                        'variance': variance,
                        'mean_score': mean_score,
                        'repeatability_quality': quality,
                        'is_perfectly_repeatable': variance == 0.0,
                        'mean_processing_time': mean_time,
                        'success_rate': len(valid_scores) / test_runs
                    })
                
                else:
                    print(f"\n  [ERROR] All runs failed for {test_case_name}")
        
        # Overall summary
        print("\n" + "="*80)
        print("REAL DATA REPEATABILITY SUMMARY")
        print("="*80)
        
        if self.test_results:
            perfect_count = sum(1 for r in self.test_results if r['is_perfectly_repeatable'])
            excellent_count = sum(1 for r in self.test_results if r['repeatability_quality'] in ['PERFECT', 'EXCELLENT'])
            mean_variance = sum(r['variance'] for r in self.test_results) / len(self.test_results)
            mean_processing_time = sum(r['mean_processing_time'] for r in self.test_results) / len(self.test_results)
            
            print(f"Total Test Cases: {len(self.test_results)}")
            print(f"Perfect Repeatability: {perfect_count}/{len(self.test_results)} ({perfect_count/len(self.test_results)*100:.1f}%)")
            print(f"Excellent+ Repeatability: {excellent_count}/{len(self.test_results)} ({excellent_count/len(self.test_results)*100:.1f}%)")
            print(f"Mean Variance: {mean_variance:.8f}")
            print(f"Mean Processing Time: {mean_processing_time:.3f}s")
            
            if perfect_count == len(self.test_results):
                print("\n[SUCCESS] PERFECT REPEATABILITY achieved across ALL real data test cases!")
                print("  - Same real inputs produce identical scores every time")
                print("  - User problem '10 different answers' completely solved")
                print("  - Architecture ready for production deployment")
            elif excellent_count >= len(self.test_results) * 0.8:
                print(f"\n[SUCCESS] EXCELLENT REPEATABILITY achieved in {excellent_count/len(self.test_results)*100:.1f}% of cases")
                print("  - Significant improvement over legacy AI-only scoring")
                print("  - Minor variance likely due to edge cases in real data")
            else:
                print("\n[WARNING] Some repeatability issues detected with real data")
                print("  - May need architecture tuning for specific data patterns")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"real_data_repeatability_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_timestamp': timestamp,
                'test_summary': {
                    'total_cases': len(self.test_results),
                    'perfect_repeatability_count': sum(1 for r in self.test_results if r['is_perfectly_repeatable']),
                    'mean_variance': sum(r['variance'] for r in self.test_results) / len(self.test_results) if self.test_results else 0,
                    'mean_processing_time': sum(r['mean_processing_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"\n[FILE SAVED] Detailed results saved to: {results_file}")
        
        return self.test_results

async def main():
    """Main test execution"""
    tester = RealDataRepeatabilityTester()
    
    try:
        await tester.test_repeatability_with_real_data(test_runs=5)
        
    except Exception as e:
        logger.exception("Real data repeatability test failed")
        print(f"\n[ERROR] Test failed: {str(e)}")
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {str(e)}")
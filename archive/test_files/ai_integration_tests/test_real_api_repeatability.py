#!/usr/bin/env python3
"""
Real API Repeatability Validation

Tests the repeatability architecture using actual OpenAI API calls with real database data
to validate that identical real-world inputs produce consistent outputs while measuring API costs.
"""

import asyncio
import json
import logging
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.analysis.enhanced_ai_lite_processor import EnhancedAILiteProcessor, ProcessingMode
from src.processors.analysis.fact_extraction_integration_service import ProcessorMigrationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealAPIRepeatabilityTester:
    """Tests repeatability using real OpenAI API calls with database data"""
    
    def __init__(self):
        self.db_path = "data/catalynx.db"
        self.test_results = []
        
    def get_real_profiles_and_opportunities(self, limit=2):
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
    
    async def test_api_repeatability_with_real_data(self, test_runs=3):
        """Test repeatability using real database data and OpenAI API calls"""
        
        print("="*80)
        print("REAL API REPEATABILITY VALIDATION")
        print("="*80)
        print("Testing repeatability architecture with actual OpenAI API calls")
        print("WARNING: This test will consume OpenAI API tokens and incur costs")
        print("="*80)
        
        # Get real data
        try:
            profiles, opportunities = self.get_real_profiles_and_opportunities(limit=1)  # Reduced for API cost management
            
            if not profiles or not opportunities:
                print("[ERROR] No real data found in database")
                return
                
            print(f"Loaded {len(profiles)} real profiles and {len(opportunities)} real opportunities")
            
        except Exception as e:
            print(f"[ERROR] Failed to load real data: {str(e)}")
            return
        
        # Initialize processor with real API calls enabled
        processor = EnhancedAILiteProcessor(
            processing_mode=ProcessingMode.NEW_ARCHITECTURE,
            migration_config=ProcessorMigrationConfig(
                enable_fact_extraction=True,
                enable_deterministic_scoring=True,
                fallback_to_legacy=False
            )
        )
        
        # Get initial stats
        integration_service = processor.integration_service
        initial_stats = integration_service.get_processing_statistics()
        
        print(f"\nInitial API Statistics:")
        print(f"  API Calls Made: {initial_stats['api_calls_made']}")
        print(f"  Total Cost: ${initial_stats['total_api_cost']:.6f}")
        
        # Test the first profile-opportunity combination
        profile = profiles[0]
        opportunity = opportunities[0]
        
        test_case_name = f"RealAPI_Profile_x_Opportunity"
        print(f"\n" + "="*60)
        print(f"TEST CASE: {test_case_name}")
        print(f"Profile: {profile['name']}")
        print(f"Opportunity: {opportunity['title']}")
        print("="*60)
        print("WARNING: Making actual OpenAI API calls - costs will be incurred")
        
        # Run multiple times to test repeatability with real API
        scores = []
        confidence_levels = []
        processing_times = []
        api_responses = []
        
        for run in range(test_runs):
            print(f"  Run {run+1}/{test_runs} (API call)...", end=" ")
            
            try:
                start_time = datetime.now()
                result = await processor.execute({
                    'opportunity': opportunity,
                    'profile': profile
                })
                end_time = datetime.now()
                
                scores.append(result.final_score)
                confidence_levels.append(result.confidence_level)
                processing_times.append((end_time - start_time).total_seconds())
                
                # Get current stats to track API usage
                current_stats = integration_service.get_processing_statistics()
                api_responses.append(current_stats)
                
                print(f"Score: {result.final_score:.6f} ({result.confidence_level})")
                
            except Exception as e:
                print(f"[ERROR] {str(e)}")
                scores.append(None)
                confidence_levels.append(None)
                processing_times.append(None)
                api_responses.append(None)
        
        # Get final stats
        final_stats = integration_service.get_processing_statistics()
        
        # Analyze results
        valid_scores = [s for s in scores if s is not None]
        
        if valid_scores:
            min_score = min(valid_scores)
            max_score = max(valid_scores)
            variance = max_score - min_score
            mean_score = sum(valid_scores) / len(valid_scores)
            mean_time = sum([t for t in processing_times if t is not None]) / len(processing_times)
            
            # Calculate API costs
            api_calls_made = final_stats['api_calls_made'] - initial_stats['api_calls_made']
            tokens_used = final_stats['total_tokens_used'] - initial_stats['total_tokens_used']
            cost_incurred = final_stats['total_api_cost'] - initial_stats['total_api_cost']
            
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
            
            print(f"\n  API COST ANALYSIS:")
            print(f"    API Calls Made: {api_calls_made}")
            print(f"    Total Tokens Used: {tokens_used}")
            print(f"    Total Cost Incurred: ${cost_incurred:.6f}")
            print(f"    Cost per Call: ${cost_incurred/max(api_calls_made, 1):.6f}")
            print(f"    Cost per Token: ${cost_incurred/max(tokens_used, 1):.8f}")
            
            if 'existing_score' in opportunity:
                print(f"    Existing DB Score: {opportunity['existing_score']:.6f}")
                print(f"    Score Difference from DB: {abs(mean_score - opportunity['existing_score']):.6f}")
            
            # Store results with API cost data
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
                'success_rate': len(valid_scores) / test_runs,
                'api_calls_made': api_calls_made,
                'total_tokens_used': tokens_used,
                'total_cost_incurred': cost_incurred,
                'cost_per_call': cost_incurred/max(api_calls_made, 1),
                'cost_efficiency': cost_incurred/mean_score if mean_score > 0 else 0
            })
        
        else:
            print(f"\n  [ERROR] All runs failed for {test_case_name}")
        
        # Overall summary
        print("\n" + "="*80)
        print("REAL API REPEATABILITY SUMMARY")
        print("="*80)
        
        if self.test_results:
            result = self.test_results[0]
            
            print(f"Test Case Completed: 1")
            print(f"Repeatability Quality: {result['repeatability_quality']}")
            print(f"Perfect Repeatability: {'Yes' if result['is_perfectly_repeatable'] else 'No'}")
            print(f"Score Variance: {result['variance']:.8f}")
            print(f"Mean Processing Time: {result['mean_processing_time']:.3f}s")
            
            print(f"\nAPI COST SUMMARY:")
            print(f"Total API Calls: {result['api_calls_made']}")
            print(f"Total Tokens: {result['total_tokens_used']}")
            print(f"Total Cost: ${result['total_cost_incurred']:.6f}")
            print(f"Cost per Analysis: ${result['cost_per_call']:.6f}")
            
            if result['is_perfectly_repeatable']:
                print("\n[SUCCESS] PERFECT REPEATABILITY achieved with real API calls!")
                print("  - Same real inputs + OpenAI API produce identical scores")
                print("  - User problem '10 different answers' solved even with AI variability")
                print("  - Deterministic scoring successfully isolates AI from final results")
            elif result['repeatability_quality'] in ['EXCELLENT', 'GOOD']:
                print(f"\n[SUCCESS] {result['repeatability_quality']} REPEATABILITY with real API calls")
                print("  - Minor variance likely due to AI response variations")
                print("  - Significant improvement over pure AI-based scoring")
            else:
                print("\n[WARNING] Repeatability issues detected with real API calls")
                print("  - AI response variations may be affecting deterministic scoring")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"real_api_repeatability_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_timestamp': timestamp,
                'test_type': 'real_api_repeatability',
                'api_costs_incurred': True,
                'test_summary': {
                    'total_cases': len(self.test_results),
                    'perfect_repeatability_count': sum(1 for r in self.test_results if r['is_perfectly_repeatable']),
                    'mean_variance': sum(r['variance'] for r in self.test_results) / len(self.test_results) if self.test_results else 0,
                    'total_api_cost': sum(r['total_cost_incurred'] for r in self.test_results),
                    'total_tokens_used': sum(r['total_tokens_used'] for r in self.test_results),
                    'total_api_calls': sum(r['api_calls_made'] for r in self.test_results)
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"\n[FILE SAVED] Detailed results saved to: {results_file}")
        print(f"[COST TRACKING] Total session cost: ${final_stats['total_api_cost']:.6f}")
        
        return self.test_results

async def main():
    """Main test execution with API cost awareness"""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY environment variable not set")
        print("This test requires a valid OpenAI API key to make real API calls")
        return
    
    print("="*80)
    print("REAL API COST WARNING")
    print("="*80)
    print("This test will make actual OpenAI API calls and incur costs.")
    print("Estimated cost: $0.10 - $0.50 depending on response size")
    print("="*80)
    
    # Get user confirmation in interactive mode
    try:
        confirmation = input("Continue with real API testing? (yes/no): ").lower().strip()
        if confirmation not in ['yes', 'y']:
            print("Test cancelled by user")
            return
    except EOFError:
        print("Running in non-interactive mode, proceeding with test...")
    
    tester = RealAPIRepeatabilityTester()
    
    try:
        await tester.test_api_repeatability_with_real_data(test_runs=3)
        
    except Exception as e:
        logger.exception("Real API repeatability test failed")
        print(f"\n[ERROR] Test failed: {str(e)}")
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {str(e)}")
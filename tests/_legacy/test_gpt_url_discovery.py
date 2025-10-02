#!/usr/bin/env python3
"""
GPT URL Discovery Validation Test
Tests the complete GPT URL discovery pipeline with real BMF data.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import system components
from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig
from src.database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTURLDiscoveryValidator:
    """Comprehensive validation of GPT URL Discovery system"""
    
    def __init__(self):
        self.processor = GPTURLDiscoveryProcessor()
        self.db_manager = DatabaseManager("data/catalynx.db")
        
    async def test_url_discovery_pipeline(self):
        """Test complete URL discovery pipeline with sample organizations"""
        
        test_organizations = [
            {
                'organization_name': 'American Red Cross',
                'ein': '530196605',
                'city': 'Washington',
                'state': 'DC',
                'organization_type': 'Human Services',
                'expected_domain': 'redcross.org'
            },
            {
                'organization_name': 'Boys and Girls Club of America',
                'ein': '131624228', 
                'city': 'Atlanta',
                'state': 'GA',
                'organization_type': 'Youth Development',
                'expected_domain': 'bgca.org'
            },
            {
                'organization_name': 'United Way Worldwide',
                'ein': '131635294',
                'city': 'Alexandria', 
                'state': 'VA',
                'organization_type': 'Community Development',
                'expected_domain': 'unitedway.org'
            }
        ]
        
        results = []
        
        for org in test_organizations:
            logger.info(f"\n=== Testing URL Discovery for {org['organization_name']} ===")
            
            # Create processor config
            config = ProcessorConfig(
                workflow_id=f"test_url_discovery_{org['ein']}",
                processor_name="gpt_url_discovery",
                workflow_config=WorkflowConfig(),
                processor_specific_config={
                    'organization_data': org,
                    'force_refresh': True  # Force GPT call for testing
                }
            )
            
            # Execute URL discovery
            start_time = datetime.now()
            result = await self.processor.execute(config)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            test_result = {
                'organization': org['organization_name'],
                'ein': org['ein'],
                'success': result.success,
                'processing_time': processing_time,
                'urls_found': len(result.data.get('urls', [])) if result.success else 0,
                'source': result.data.get('source', 'unknown') if result.success else None,
                'predictions': result.data.get('predictions', []) if result.success else [],
                'error': result.errors[0] if result.errors else None
            }
            
            # Check URL quality
            if result.success and result.data.get('urls'):
                predicted_urls = result.data['urls']
                expected_domain = org['expected_domain']
                
                # Check if any predicted URL contains the expected domain
                domain_match = any(expected_domain in url.lower() for url in predicted_urls)
                test_result['domain_accuracy'] = domain_match
                test_result['top_url'] = predicted_urls[0] if predicted_urls else None
                
                logger.info(f"✓ Found {len(predicted_urls)} URLs")
                logger.info(f"✓ Top prediction: {predicted_urls[0]}")
                logger.info(f"✓ Domain accuracy: {'PASS' if domain_match else 'FAIL'}")
                
                # Display all predictions with confidence scores
                if result.data.get('predictions'):
                    logger.info("URL Predictions:")
                    for i, pred in enumerate(result.data['predictions'][:3]):
                        logger.info(f"  {i+1}. {pred['url']} (confidence: {pred['confidence']:.2f})")
            else:
                test_result['domain_accuracy'] = False
                logger.error(f"✗ Failed: {result.errors[0] if result.errors else 'Unknown error'}")
            
            results.append(test_result)
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        return results
    
    async def test_sql_caching(self):
        """Test SQL caching functionality"""
        logger.info("\n=== Testing SQL Caching ===")
        
        test_ein = "530196605"  # American Red Cross
        test_url = "https://redcross.org"
        
        # Test caching a URL
        await self.processor.cache_successful_url(test_ein, test_url, 1.0)
        logger.info(f"✓ Cached URL for EIN {test_ein}")
        
        # Test cache retrieval
        cached_url = await self.processor._get_cached_url(test_ein)
        if cached_url == test_url:
            logger.info(f"✓ Successfully retrieved cached URL: {cached_url}")
        else:
            logger.error(f"✗ Cache retrieval failed. Expected: {test_url}, Got: {cached_url}")
        
        # Test cache stats
        stats = await self.processor.get_cache_stats()
        logger.info(f"✓ Cache stats: {stats}")
        
        return cached_url == test_url
    
    async def test_bmf_integration(self):
        """Test integration with BMF data from database"""
        logger.info("\n=== Testing BMF Integration ===")
        
        # Try to get a real profile from the database
        try:
            # Check if we have any profiles with EINs
            profiles = self.db_manager.get_all_profiles()
            bmf_profiles = [p for p in profiles if hasattr(p, 'ein') and p.ein]
            
            if bmf_profiles:
                test_profile = bmf_profiles[0]
                logger.info(f"Testing with real profile: {test_profile.organization_name} (EIN: {test_profile.ein})")
                
                # Create config from profile data
                config = ProcessorConfig(
                    workflow_id=f"test_bmf_integration_{test_profile.ein}",
                    processor_name="gpt_url_discovery",
                    workflow_config=WorkflowConfig(),
                    processor_specific_config={
                        'organization_data': {
                            'organization_name': test_profile.organization_name,
                            'ein': test_profile.ein,
                            'city': getattr(test_profile, 'city', ''),
                            'state': getattr(test_profile, 'state', ''),
                            'organization_type': 'nonprofit'
                        }
                    }
                )
                
                # Test URL discovery
                result = await self.processor.execute(config)
                
                if result.success:
                    logger.info(f"✓ BMF integration successful")
                    logger.info(f"✓ Found {len(result.data.get('urls', []))} URLs")
                    if result.data.get('urls'):
                        logger.info(f"✓ Top URL: {result.data['urls'][0]}")
                    return True
                else:
                    logger.error(f"✗ BMF integration failed: {result.error_message}")
                    return False
            else:
                logger.warning("No profiles with EINs found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error testing BMF integration: {e}")
            return False
    
    def generate_validation_report(self, results, cache_test, bmf_test):
        """Generate comprehensive validation report"""
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'url_discovery_tests': results,
            'cache_functionality': cache_test,
            'bmf_integration': bmf_test,
            'summary': {
                'total_orgs_tested': len(results),
                'successful_discoveries': sum(1 for r in results if r['success']),
                'domain_accuracy_rate': sum(1 for r in results if r.get('domain_accuracy', False)) / len(results),
                'average_processing_time': sum(r['processing_time'] for r in results) / len(results) if results else 0,
                'cache_working': cache_test,
                'bmf_integration_working': bmf_test
            }
        }
        
        # Save report
        report_path = Path("gpt_url_discovery_validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n=== VALIDATION REPORT ===")
        logger.info(f"Report saved to: {report_path}")
        logger.info(f"Organizations tested: {report['summary']['total_orgs_tested']}")
        logger.info(f"Success rate: {report['summary']['successful_discoveries']}/{report['summary']['total_orgs_tested']}")
        logger.info(f"Domain accuracy: {report['summary']['domain_accuracy_rate']:.1%}")
        logger.info(f"Average processing time: {report['summary']['average_processing_time']:.2f}s")
        logger.info(f"Cache functionality: {'WORKING' if cache_test else 'FAILED'}")
        logger.info(f"BMF integration: {'WORKING' if bmf_test else 'FAILED'}")
        
        return report

async def main():
    """Run comprehensive GPT URL Discovery validation"""
    logger.info("Starting GPT URL Discovery Validation Tests")
    
    # Verify OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("CRITICAL: No OpenAI API key found in environment")
        logger.error("Please ensure OPENAI_API_KEY is set in your .env file")
        return
    else:
        logger.info(f"OpenAI API key found: {api_key[:10]}...{api_key[-4:] if len(api_key) > 10 else api_key}")
    
    validator = GPTURLDiscoveryValidator()
    
    try:
        # Test 1: URL Discovery Pipeline
        logger.info("Phase 1: Testing URL Discovery Pipeline...")
        discovery_results = await validator.test_url_discovery_pipeline()
        
        # Test 2: SQL Caching
        logger.info("Phase 2: Testing SQL Caching...")
        cache_result = await validator.test_sql_caching()
        
        # Test 3: BMF Integration
        logger.info("Phase 3: Testing BMF Integration...")
        bmf_result = await validator.test_bmf_integration()
        
        # Generate Report
        logger.info("Phase 4: Generating Validation Report...")
        report = validator.generate_validation_report(discovery_results, cache_result, bmf_result)
        
        # Overall assessment
        if (len([r for r in discovery_results if r['success']]) >= 2 and 
            cache_result and 
            bmf_result is not False):
            logger.info("\n*** VALIDATION SUCCESSFUL - GPT URL Discovery Ready for Production ***")
        else:
            logger.warning("\n*** VALIDATION ISSUES DETECTED - Review Results ***")
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
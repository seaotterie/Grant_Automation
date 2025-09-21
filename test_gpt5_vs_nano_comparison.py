#!/usr/bin/env python3
"""
GPT-5 vs GPT-5-nano Model Comparison Test
Tests URL prediction accuracy between different GPT-5 models
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.processors.analysis.gpt_url_discovery import GPTURLDiscoveryProcessor
from src.core.data_models import ProcessorConfig, WorkflowConfig
from src.core.openai_service import get_openai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_comparison():
    """Compare GPT-5 vs GPT-5-nano for Heroes Bridge URL prediction"""
    logger.info("GPT-5 vs GPT-5-nano Model Comparison Test")
    
    # Heroes Bridge EIN - will get real BMF data from processor
    test_ein = '812827604'
    
    # Get real BMF data for Heroes Bridge first
    processor = GPTURLDiscoveryProcessor()
    bmf_data = await processor._query_bmf_organization(test_ein)
    
    if not bmf_data:
        print(f"ERROR: No BMF data found for EIN {test_ein}")
        print("Make sure the nonprofit_intelligence.db exists and contains BMF data")
        return {}
    
    print("\n" + "="*80)
    print("GPT-5 vs GPT-5-NANO MODEL COMPARISON - HEROES BRIDGE URL PREDICTION")
    print("="*80)
    print(f"Organization: {bmf_data['organization_name']} (FROM BMF DATABASE)")
    print(f"Location: {bmf_data['city']}, {bmf_data['state']}")
    print(f"Type: {bmf_data['organization_type']}")
    print(f"EIN: {bmf_data['ein']}")
    print(f"Data Source: {bmf_data['data_source']}")
    
    models_to_test = [
        ("gpt-5-nano", "Cost-optimized GPT-5 model"),
        ("gpt-5", "Full GPT-5 model")
    ]
    
    results = {}
    
    for model_name, model_desc in models_to_test:
        print(f"\n{'='*50}")
        print(f"Testing {model_name.upper()}: {model_desc}")
        print(f"{'='*50}")
        
        try:
            # Create fresh processor instance
            processor = GPTURLDiscoveryProcessor()
            
            # Temporarily override model in processor
            openai_service = get_openai_service()
            
            # Create direct GPT call with specific model using real BMF data
            prompt = processor._create_url_prediction_prompt(bmf_data)
            
            logger.info(f"Calling {model_name} for URL prediction...")
            
            response = await openai_service.create_completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.3,
                tools=[],
                tool_choice="none"
            )
            
            # Parse the response
            predictions = processor._parse_gpt_response(response.content)
            
            print(f"Success: {len(predictions)} URLs predicted")
            print(f"Processing cost: ${response.cost_estimate:.4f}")
            print(f"Tokens used: {response.usage.get('total_tokens', 0)}")
            
            if predictions:
                print(f"\nTop 3 URL Predictions:")
                for i, pred in enumerate(predictions[:3], 1):
                    url = pred.url
                    confidence = pred.confidence
                    reasoning = pred.reasoning[:100] + "..." if len(pred.reasoning) > 100 else pred.reasoning
                    
                    # Check if this prediction matches the correct URL
                    correct_match = "CORRECT!" if "herosbridge.org" in url else ""
                    
                    print(f"  {i}. {url} (confidence: {confidence:.2f}) {correct_match}")
                    print(f"     Reasoning: {reasoning}")
                
                # Store results for comparison
                results[model_name] = {
                    'predictions': predictions,
                    'cost': response.cost_estimate,
                    'tokens': response.usage.get('total_tokens', 0),
                    'top_url': predictions[0].url if predictions else None,
                    'correct_spelling': any("herosbridge.org" in p.url for p in predictions),
                    'total_predictions': len(predictions)
                }
            else:
                print("No predictions generated")
                results[model_name] = {'predictions': [], 'error': 'No predictions'}
                
        except Exception as e:
            logger.error(f"Error testing {model_name}: {e}")
            print(f"Error: {e}")
            results[model_name] = {'error': str(e)}
        
        # Add delay between tests
        await asyncio.sleep(2)
    
    # Comparison Analysis
    print(f"\n{'='*80}")
    print("MODEL COMPARISON ANALYSIS")
    print(f"{'='*80}")
    
    if 'gpt-5-nano' in results and 'gpt-5' in results:
        nano_result = results['gpt-5-nano']
        full_result = results['gpt-5']
        
        print(f"URL Accuracy:")
        nano_correct = nano_result.get('correct_spelling', False)
        full_correct = full_result.get('correct_spelling', False)
        print(f"  GPT-5-nano: {'Found herosbridge.org' if nano_correct else 'Missed correct spelling'}")
        print(f"  GPT-5 (full): {'Found herosbridge.org' if full_correct else 'Missed correct spelling'}")
        
        print(f"\nCost Comparison:")
        nano_cost = nano_result.get('cost', 0)
        full_cost = full_result.get('cost', 0)
        print(f"  GPT-5-nano: ${nano_cost:.4f}")
        print(f"  GPT-5 (full): ${full_cost:.4f}")
        print(f"  Cost difference: {((full_cost - nano_cost) / nano_cost * 100):+.1f}%" if nano_cost > 0 else "N/A")
        
        print(f"\nPrediction Count:")
        print(f"  GPT-5-nano: {nano_result.get('total_predictions', 0)} URLs")
        print(f"  GPT-5 (full): {full_result.get('total_predictions', 0)} URLs")
        
        print(f"\nTop URL Comparison:")
        print(f"  GPT-5-nano: {nano_result.get('top_url', 'N/A')}")
        print(f"  GPT-5 (full): {full_result.get('top_url', 'N/A')}")
        
        # Recommendation
        print(f"\n{'='*50}")
        print("RECOMMENDATION")
        print(f"{'='*50}")
        
        if full_correct and not nano_correct:
            print("GPT-5 (full) provides superior URL accuracy")
            print("Consider using GPT-5 for URL discovery despite higher cost")
            print("Enhanced accuracy justifies cost for profile enhancement use case")
        elif nano_correct and full_correct:
            print("Both models provide correct results")
            print("GPT-5-nano offers better cost efficiency")
        elif not nano_correct and not full_correct:
            print("Both models missed correct spelling - need additional enhancement")
        else:
            print("GPT-5-nano provides adequate accuracy at lower cost")
    
    return results

async def main():
    """Run model comparison test"""
    try:
        results = await test_model_comparison()
        
        # Save detailed results
        import json
        with open('gpt5_model_comparison.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: gpt5_model_comparison.json")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
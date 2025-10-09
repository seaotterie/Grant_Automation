#!/usr/bin/env python3
"""
Test script for Smart URL Resolution Service

Tests the intelligent URL prioritization system with Heroes Bridge EIN
to demonstrate the complete data source hierarchy.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.smart_url_resolution_service import SmartURLResolutionService


async def test_url_resolution_scenarios():
    """Test various URL resolution scenarios"""
    print("=" * 70)
    print("SMART URL RESOLUTION SERVICE TEST")
    print("=" * 70)
    
    service = SmartURLResolutionService()
    ein = "812827604"
    org_name = "Heroes Bridge"
    
    # Test Scenario 1: No user-provided URL (990 + GPT only)
    print("\nSCENARIO 1: No User URL (990 + GPT Sources)")
    print("-" * 50)
    
    result1 = await service.resolve_organization_url(
        ein=ein,
        organization_name=org_name,
        user_provided_url=None
    )
    
    print(f"Organization: {result1.organization_name}")
    print(f"Primary URL: {result1.primary_url.url if result1.primary_url else 'None'}")
    print(f"Primary Source: {result1.primary_url.source if result1.primary_url else 'None'}")
    print(f"Confidence: {result1.confidence_assessment.get('overall_confidence', 0):.2%}")
    print(f"Strategy: {result1.resolution_strategy}")
    print(f"Data Quality: {result1.confidence_assessment.get('data_quality', 'unknown')}")
    
    print(f"\nAll Candidates ({len(result1.all_candidates)}):")
    for i, candidate in enumerate(result1.all_candidates, 1):
        print(f"  {i}. {candidate.url}")
        print(f"     Source: {candidate.source} (confidence: {candidate.confidence_score:.2%})")
        print(f"     Status: {candidate.validation_status}")
        print(f"     Description: {candidate.source_description}")
    
    print(f"\nRecommendations:")
    for rec in result1.recommendations:
        print(f"  - {rec}")
    
    # Test Scenario 2: With user-provided URL (highest priority)
    print("\n" + "=" * 70)
    print("SCENARIO 2: With User-Provided URL (All Sources)")
    print("-" * 50)
    
    user_url = "https://herosbridge.org"  # User provides official URL
    
    result2 = await service.resolve_organization_url(
        ein=ein,
        organization_name=org_name,
        user_provided_url=user_url
    )
    
    print(f"Organization: {result2.organization_name}")
    print(f"User Provided: {user_url}")
    print(f"Primary URL: {result2.primary_url.url if result2.primary_url else 'None'}")
    print(f"Primary Source: {result2.primary_url.source if result2.primary_url else 'None'}")
    print(f"Confidence: {result2.confidence_assessment.get('overall_confidence', 0):.2%}")
    print(f"Strategy: {result2.resolution_strategy}")
    print(f"Data Quality: {result2.confidence_assessment.get('data_quality', 'unknown')}")
    
    print(f"\nAll Candidates ({len(result2.all_candidates)}):")
    for i, candidate in enumerate(result2.all_candidates, 1):
        print(f"  {i}. {candidate.url}")
        print(f"     Source: {candidate.source} (confidence: {candidate.confidence_score:.2%})")
        print(f"     Status: {candidate.validation_status}")
        print(f"     Description: {candidate.source_description}")
        if candidate.notes:
            print(f"     Notes: {', '.join(candidate.notes)}")
    
    print(f"\nConfidence Assessment:")
    conf_assessment = result2.confidence_assessment
    if conf_assessment.get('confidence_factors'):
        print(f"  Confidence Factors:")
        for factor in conf_assessment['confidence_factors']:
            print(f"    + {factor}")
    
    if conf_assessment.get('risk_factors'):
        print(f"  Risk Factors:")
        for risk in conf_assessment['risk_factors']:
            print(f"    - {risk}")
    
    print(f"\nRecommendations:")
    for rec in result2.recommendations:
        print(f"  - {rec}")
    
    # Test Scenario 3: Comparison of 990 vs User URL
    print("\n" + "=" * 70)
    print("SCENARIO 3: URL Source Comparison")
    print("-" * 50)
    
    tax_url = None
    user_sources = [c for c in result2.all_candidates if c.source == "user_provided"]
    tax_sources = [c for c in result2.all_candidates if c.source == "990_declared"]
    gpt_sources = [c for c in result2.all_candidates if c.source == "gpt_predicted"]
    
    if tax_sources:
        tax_url = tax_sources[0].url
    
    print("URL Source Analysis:")
    print(f"  User-Provided: {user_url}")
    print(f"  990-Declared:  {tax_url or 'Not available'}")
    print(f"  GPT-Predicted: {len(gpt_sources)} candidate(s)")
    
    if user_url and tax_url:
        if user_url.lower().replace('www.', '') == tax_url.lower().replace('www.', ''):
            print("  ✅ User URL matches 990 declaration - highest confidence!")
        else:
            print("  ⚠️  User URL differs from 990 declaration - verification recommended")
    
    print(f"\nPriority Hierarchy Demonstration:")
    print(f"  1. User-Provided URL: {user_sources[0].confidence_score:.2%} confidence" if user_sources else "  1. User-Provided URL: Not available")
    print(f"  2. 990-Declared URL:  {tax_sources[0].confidence_score:.2%} confidence" if tax_sources else "  2. 990-Declared URL: Not available")
    print(f"  3. GPT-Predicted URLs: {gpt_sources[0].confidence_score:.2%} confidence" if gpt_sources else "  3. GPT-Predicted URLs: Not available")
    
    print(f"\nSelected URL: {result2.primary_url.url} ({result2.primary_url.source})")
    print(f"Reason: Highest priority source with validation: {result2.primary_url.validation_status}")
    
    print("\n[SUCCESS] Smart URL resolution test completed")


if __name__ == "__main__":
    asyncio.run(test_url_resolution_scenarios())
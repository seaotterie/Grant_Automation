#!/usr/bin/env python3
"""
Test script for 990 Leadership Extraction Service

Tests the tax filing leadership service with Heroes Bridge EIN to verify
that we can extract authoritative leadership data from 990 filings.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tax_filing_leadership_service import TaxFilingLeadershipService


async def test_heroes_bridge_leadership():
    """Test leadership extraction with Heroes Bridge (812827604)"""
    print("=" * 60)
    print("990 LEADERSHIP EXTRACTION TEST")
    print("=" * 60)
    
    service = TaxFilingLeadershipService()
    
    # Test Heroes Bridge EIN
    ein = "812827604"
    print(f"Testing EIN: {ein} (Heroes Bridge)")
    print("-" * 40)
    
    try:
        # Extract leadership baseline from 990 filing
        baseline = await service.get_leadership_baseline(ein)
        
        if baseline:
            print(f"[OK] Successfully extracted baseline data")
            print(f"Organization: {baseline.organization_name}")
            print(f"Filing Year: {baseline.filing_year}")
            print(f"Revenue: ${baseline.total_revenue:,.0f}" if baseline.total_revenue else "Revenue: Not available")
            print(f"Declared Website: {baseline.declared_website or 'Not declared'}")
            print()
            
            print(f"OFFICERS AND DIRECTORS ({len(baseline.officers)} found):")
            print("-" * 40)
            
            if baseline.officers:
                for i, officer in enumerate(baseline.officers, 1):
                    print(f"{i}. {officer.name}")
                    print(f"   Title: {officer.title}")
                    if officer.compensation:
                        print(f"   Compensation: ${officer.compensation:,.0f}")
                    if officer.hours_per_week:
                        print(f"   Hours/Week: {officer.hours_per_week}")
                    
                    # Position flags
                    positions = []
                    if officer.is_director:
                        positions.append("Director")
                    if officer.is_officer:
                        positions.append("Officer")
                    if officer.is_trustee:
                        positions.append("Trustee")
                    if officer.is_key_employee:
                        positions.append("Key Employee")
                    
                    if positions:
                        print(f"   Positions: {', '.join(positions)}")
                    
                    print(f"   Confidence: {officer.confidence_score}")
                    print()
            else:
                print("No officers found in 990 filing")
            
            # Test verification against sample scraped data
            print("VERIFICATION TEST:")
            print("-" * 40)
            
            # Sample scraped data (mix of real and fake)
            sample_scraped_leadership = [
                {"name": "John Smith", "title": "Executive Director"},
                {"name": "Jane Doe", "title": "Board Chair"},
                {"name": "Board of", "title": "Director"},  # Fake fragment
                {"name": "Mike Johnson", "title": "Treasurer"}  # Potentially real
            ]
            
            verification = service.verify_web_scraping_against_baseline(
                sample_scraped_leadership, baseline
            )
            
            print(f"Baseline Officers: {verification['baseline_officers_count']}")
            print(f"Scraped Leadership: {verification['scraped_leadership_count']}")
            print(f"Verified Matches: {len(verification['verified_matches'])}")
            print(f"Unverified Scraped: {len(verification['unverified_scraped'])}")
            print(f"Missing from Scraped: {len(verification['missing_from_scraped'])}")
            print(f"Overall Confidence: {verification['overall_confidence']:.2%}")
            print()
            
            if verification['verified_matches']:
                print("VERIFIED MATCHES:")
                for match in verification['verified_matches']:
                    print(f"- {match['scraped_data']['name']} -> {match['baseline_data']['name']}")
                    print(f"  Confidence: {match['confidence_score']:.2%}")
            
            if verification['unverified_scraped']:
                print("UNVERIFIED SCRAPED DATA:")
                for item in verification['unverified_scraped']:
                    print(f"- {item['name']} ({item['title']}) - No 990 match")
            
            print("\n[SUCCESS] 990 leadership extraction test completed")
            
        else:
            print("[ERROR] Failed to extract baseline data")
            print("This could mean:")
            print("- No XML data available for this EIN")
            print("- XML parsing failed")
            print("- Network connectivity issues")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_heroes_bridge_leadership())
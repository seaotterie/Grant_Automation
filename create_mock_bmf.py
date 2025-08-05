#!/usr/bin/env python3
"""
Create Mock BMF Data for Testing
Creates a small sample BMF file for testing purposes.
"""
import csv
from pathlib import Path


def create_mock_bmf_file():
    """Create a mock BMF file with sample data."""
    cache_dir = Path("cache/bmf")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    mock_file = cache_dir / "eo_bmf.csv"
    
    # Sample BMF data with different NTEE codes and states
    sample_data = [
        {
            'EIN': '131624868',
            'NAME': 'Sample Health Foundation',
            'CITY': 'Richmond',
            'STATE': 'VA',
            'NTEE_CD': 'P81',
            'INCOME_AMT': '500000',
            'ASSET_AMT': '2000000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PF',
            'ACTIVITY': '150'
        },
        {
            'EIN': '234567890',
            'NAME': 'Virginia Medical Research Institute',
            'CITY': 'Norfolk',
            'STATE': 'VA',
            'NTEE_CD': 'E31',
            'INCOME_AMT': '1200000',
            'ASSET_AMT': '5000000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PC',
            'ACTIVITY': '031'
        },
        {
            'EIN': '345678901',
            'NAME': 'Baltimore Health Alliance',
            'CITY': 'Baltimore',
            'STATE': 'MD',
            'NTEE_CD': 'P81',
            'INCOME_AMT': '800000',
            'ASSET_AMT': '3500000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PC',
            'ACTIVITY': '150'
        },
        {
            'EIN': '456789012',
            'NAME': 'DC Education Foundation',
            'CITY': 'Washington',
            'STATE': 'DC',
            'NTEE_CD': 'B25',
            'INCOME_AMT': '300000',
            'ASSET_AMT': '1500000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PF',
            'ACTIVITY': '025'
        },
        {
            'EIN': '567890123',
            'NAME': 'Small VA Nonprofit',
            'CITY': 'Alexandria',
            'STATE': 'VA',
            'NTEE_CD': 'P81',
            'INCOME_AMT': '25000',  # Below min revenue threshold
            'ASSET_AMT': '100000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PC',
            'ACTIVITY': '150'
        },
        {
            'EIN': '678901234',
            'NAME': 'Large Hospital System',
            'CITY': 'Virginia Beach',
            'STATE': 'VA',
            'NTEE_CD': 'E31',
            'INCOME_AMT': '50000000',
            'ASSET_AMT': '200000000',
            'CLASSIFICATION': '501c3',
            'FOUNDATION': 'PC',
            'ACTIVITY': '031'
        }
    ]
    
    # Write to CSV file
    with open(mock_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['EIN', 'NAME', 'CITY', 'STATE', 'NTEE_CD', 'INCOME_AMT', 
                     'ASSET_AMT', 'CLASSIFICATION', 'FOUNDATION', 'ACTIVITY']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in sample_data:
            writer.writerow(row)
    
    print(f"Mock BMF file created: {mock_file}")
    print(f"Contains {len(sample_data)} sample organizations")
    
    # Show what should match our test criteria
    print("\nExpected matches for test criteria (VA, P81/E31, min revenue $50K):")
    for org in sample_data:
        if (org['STATE'] == 'VA' and 
            org['NTEE_CD'] in ['P81', 'E31'] and 
            int(org['INCOME_AMT']) >= 50000):
            print(f"  - {org['NAME']} (EIN: {org['EIN']}, NTEE: {org['NTEE_CD']}, Revenue: ${int(org['INCOME_AMT']):,})")


if __name__ == "__main__":
    create_mock_bmf_file()
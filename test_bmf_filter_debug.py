#!/usr/bin/env python3
"""
Debug BMF Filter Issues
Test to understand why only 5 records are returned when 86 are expected.
"""

import csv
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_bmf_file():
    """Analyze the BMF file to understand filtering issues."""
    bmf_file = Path("cache/bmf/eo_va.csv")
    
    if not bmf_file.exists():
        print(f"ERROR: BMF file not found: {bmf_file}")
        return
    
    print(f"Analyzing BMF file: {bmf_file}")
    
    # Target criteria from your test
    target_ntee_codes = ["P81", "E31", "P30", "W70"]
    target_state = "VA"
    
    # Counters
    total_records = 0
    records_with_ntee = 0
    records_matching_state = 0
    records_matching_ntee = 0
    records_matching_both = 0
    empty_ntee_records = 0
    
    # Track specific matches
    matching_records = []
    ntee_distribution = {}
    
    try:
        with open(bmf_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_records += 1
                
                # Get data
                ein = row.get('EIN', '').strip()
                name = row.get('NAME', '').strip()
                state = row.get('STATE', '').strip()
                ntee_code = row.get('NTEE_CD', '').strip()
                
                # Track state matches
                if state == target_state:
                    records_matching_state += 1
                
                # Track NTEE codes
                if ntee_code:
                    records_with_ntee += 1
                    
                    # Count NTEE distribution
                    ntee_prefix = ntee_code[:3] if len(ntee_code) >= 3 else ntee_code
                    ntee_distribution[ntee_prefix] = ntee_distribution.get(ntee_prefix, 0) + 1
                    
                    # Check if matches target NTEE codes
                    if any(ntee_code.startswith(code) for code in target_ntee_codes):
                        records_matching_ntee += 1
                        
                        # Check if also matches state
                        if state == target_state:
                            records_matching_both += 1
                            matching_records.append({
                                'ein': ein,
                                'name': name[:60],
                                'state': state,
                                'ntee_code': ntee_code
                            })
                else:
                    empty_ntee_records += 1
    
    except Exception as e:
        print(f"ERROR: Error reading BMF file: {e}")
        return
    
    # Print analysis results
    print(f"\nBMF File Analysis Results:")
    print(f"Total records: {total_records:,}")
    print(f"Records with NTEE codes: {records_with_ntee:,} ({records_with_ntee/total_records*100:.1f}%)")
    print(f"Records with empty NTEE: {empty_ntee_records:,} ({empty_ntee_records/total_records*100:.1f}%)")
    print(f"Records matching state '{target_state}': {records_matching_state:,}")
    print(f"Records matching NTEE codes {target_ntee_codes}: {records_matching_ntee:,}")
    print(f"Records matching BOTH state AND NTEE: {records_matching_both:,}")
    
    print(f"\nExpected vs Actual:")
    print(f"Expected matches: 86")
    print(f"Actual matches found: {records_matching_both}")
    print(f"Difference: {86 - records_matching_both}")
    
    # Show top NTEE code distribution
    print(f"\nTop 20 NTEE Code Distribution:")
    sorted_ntee = sorted(ntee_distribution.items(), key=lambda x: x[1], reverse=True)
    for ntee, count in sorted_ntee[:20]:
        indicator = "YES" if any(ntee.startswith(code) for code in target_ntee_codes) else "   "
        print(f"  {indicator} {ntee}: {count}")
    
    # Show matching records
    print(f"\nRecords matching both criteria (first 20):")
    for i, record in enumerate(matching_records[:20]):
        print(f"  {i+1:2d}. {record['ein']} - {record['name']} - {record['ntee_code']}")
    
    if len(matching_records) > 20:
        print(f"  ... and {len(matching_records) - 20} more")
    
    # Check for similar NTEE codes that might be missed
    print(f"\nChecking for similar NTEE codes:")
    similar_codes = {}
    for ntee, count in sorted_ntee:
        for target in target_ntee_codes:
            if target in ntee and not ntee.startswith(target):
                similar_codes[ntee] = count
    
    if similar_codes:
        print("Found potentially related NTEE codes:")
        for ntee, count in similar_codes.items():
            print(f"  {ntee}: {count}")
    
    return matching_records

def test_manual_filter():
    """Test manual filtering to verify results."""
    print(f"\nTesting Manual Filter Logic:")
    
    # Simulate the current filtering logic
    bmf_file = Path("cache/bmf/eo_va.csv")
    target_ntee_codes = ["P81", "E31", "P30", "W70"]
    target_state = "VA"
    
    matching_records = []
    
    try:
        with open(bmf_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Simulate current parsing logic
                ein = row.get('EIN', '').strip()
                name = row.get('NAME', '').strip()
                state = row.get('STATE', '').strip()
                ntee_code = row.get('NTEE_CD', '').strip()
                
                # Skip invalid records
                if not ein or not name or not state or not ntee_code:
                    continue
                
                # Current matching logic
                if (state == target_state and 
                    any(ntee_code.startswith(code) for code in target_ntee_codes)):
                    matching_records.append({
                        'ein': ein,
                        'name': name,
                        'state': state,
                        'ntee_code': ntee_code
                    })
    
    except Exception as e:
        print(f"ERROR: Error in manual filter: {e}")
        return
    
    print(f"Manual filter found: {len(matching_records)} records")
    
    # Show first few matches
    for i, record in enumerate(matching_records[:10]):
        print(f"  {i+1}. {record['ein']} - {record['name'][:50]} - {record['ntee_code']}")
    
    return matching_records

if __name__ == "__main__":
    print("BMF Filter Debug Analysis")
    print("=" * 50)
    
    # Analyze the BMF file
    matches = analyze_bmf_file()
    
    # Test manual filtering
    manual_matches = test_manual_filter()
    
    print(f"\nSummary:")
    print(f"Expected: 86 records")
    print(f"Analysis found: {len(matches) if matches else 0} records")
    print(f"Manual filter: {len(manual_matches) if manual_matches else 0} records")
    
    if matches and manual_matches and len(matches) != len(manual_matches):
        print(f"WARNING: Discrepancy detected between analysis and manual filter!")
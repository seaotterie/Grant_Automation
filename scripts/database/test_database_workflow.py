#!/usr/bin/env python3
"""
Test Database Persistence Workflow

This script tests the complete workflow:
1. Discovery → Save to database
2. View details from database
3. Promote to INTELLIGENCE stage

Usage:
    python test_database_workflow.py
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
PROFILE_ID = "profile_aefa1d788b1e"  # The Fauquier Free Clinic Inc (has NTEE codes)

def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def test_discovery():
    """Test Step 1: Run discovery and save to database"""
    print_section("TEST 1: Discovery + Database Persistence")

    url = f"{BASE_URL}/api/v2/profiles/{PROFILE_ID}/discover"
    payload = {
        "max_results": 10,
        "min_score_threshold": 0.50,
        "auto_scrapy_count": 0
    }

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload)

    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Discovery successful!")
        print(f"  - Total returned: {len(data.get('opportunities', []))}")
        print(f"  - Saved to database: {data.get('summary', {}).get('saved_to_database', 0)}")

        opportunities = data.get('opportunities', [])
        if opportunities:
            first_opp = opportunities[0]
            print(f"\n  First opportunity:")
            print(f"    - ID: {first_opp.get('opportunity_id', 'NO ID!')}")
            print(f"    - Name: {first_opp.get('organization_name')}")
            print(f"    - EIN: {first_opp.get('ein')}")
            print(f"    - Score: {first_opp.get('overall_score')}")
            print(f"    - Category: {first_opp.get('stage_category')}")

            return opportunities
    else:
        print(f"\n[FAIL] Discovery failed!")
        print(f"  Error: {response.text}")
        return []

def test_view_details(opportunities):
    """Test Step 2: View details from database"""
    print_section("TEST 2: View Details from Database")

    if not opportunities:
        print("[FAIL] No opportunities to test!")
        return None

    opp_id = opportunities[0].get('opportunity_id')
    if not opp_id:
        print("[FAIL] First opportunity has no ID!")
        return None

    url = f"{BASE_URL}/api/v2/opportunities/{opp_id}/details"

    print(f"GET {url}")

    response = requests.get(url)

    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Details retrieved successfully!")
        print(f"  - Opportunity ID: {data.get('opportunity_id')}")
        print(f"  - Organization: {data.get('organization_name')}")
        print(f"  - EIN: {data.get('ein')}")
        print(f"  - Overall Score: {data.get('overall_score')}")
        print(f"  - Stage Category: {data.get('stage_category')}")
        print(f"  - Current Stage: {data.get('current_stage')}")
        print(f"  - Dimensional Scores: {len(data.get('dimensional_scores', {}))} dimensions")

        return opp_id
    else:
        print(f"\n[FAIL] Failed to retrieve details!")
        print(f"  Error: {response.text}")
        return None

def test_promote(opp_id):
    """Test Step 3: Promote to INTELLIGENCE stage"""
    print_section("TEST 3: Promote to INTELLIGENCE Stage")

    if not opp_id:
        print("[FAIL] No opportunity ID to test!")
        return

    url = f"{BASE_URL}/api/v2/opportunities/{opp_id}/promote"
    payload = {
        "notes": "Test promotion - high priority foundation with strong mission alignment",
        "priority": "high"
    }

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload)

    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Promotion successful!")
        print(f"  - Opportunity ID: {data.get('opportunity_id')}")
        print(f"  - Previous Stage: {data.get('previous_stage')}")
        print(f"  - Promoted To: {data.get('promoted_to')}")
        print(f"  - Priority: {data.get('priority')}")
        print(f"  - Timestamp: {data.get('timestamp')}")
    else:
        print(f"\n[FAIL] Promotion failed!")
        print(f"  Error: {response.text}")

def verify_in_database(opp_id):
    """Verify opportunity is in database with correct stage"""
    print_section("VERIFICATION: Check Database Directly")

    import sqlite3

    conn = sqlite3.connect("data/catalynx.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, organization_name, current_stage, overall_score,
               priority_level, discovery_date, updated_at
        FROM opportunities
        WHERE id = ?
    """, (opp_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        print(f"[OK] Found in database!")
        print(f"  - ID: {row[0]}")
        print(f"  - Name: {row[1]}")
        print(f"  - Current Stage: {row[2]}")
        print(f"  - Score: {row[3]}")
        print(f"  - Priority: {row[4]}")
        print(f"  - Discovery Date: {row[5]}")
        print(f"  - Updated At: {row[6]}")
    else:
        print(f"[FAIL] NOT found in database!")

def main():
    """Run all tests"""
    print_section("DATABASE PERSISTENCE WORKFLOW TEST")
    print(f"Profile ID: {PROFILE_ID}")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")

    # Test 1: Discovery
    opportunities = test_discovery()

    if not opportunities:
        print("\n[FAIL] Discovery failed - cannot continue tests")
        return

    time.sleep(1)

    # Test 2: View Details
    opp_id = test_view_details(opportunities)

    if not opp_id:
        print("\n[FAIL] View details failed - cannot continue tests")
        return

    time.sleep(1)

    # Test 3: Promote
    test_promote(opp_id)

    time.sleep(1)

    # Verification
    verify_in_database(opp_id)

    print_section("TEST COMPLETE")
    print("All database persistence tests completed!")

if __name__ == "__main__":
    main()

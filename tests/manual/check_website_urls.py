#!/usr/bin/env python3
"""Check website_url values in the profiles database."""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "data" / "catalynx.db"

def check_website_urls():
    """Check website_url column values."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all profiles with website_url
    cursor.execute("""
        SELECT id, name, ein, website_url
        FROM profiles
        ORDER BY id
    """)

    profiles = cursor.fetchall()

    print(f"\nTotal profiles: {len(profiles)}")
    print("=" * 80)

    profiles_with_url = 0
    profiles_without_url = 0

    for profile in profiles:
        if profile['website_url']:
            profiles_with_url += 1
            print(f"[+] {profile['id']} | {profile['name'][:40]:40} | {profile['website_url']}")
        else:
            profiles_without_url += 1
            print(f"[-] {profile['id']} | {profile['name'][:40]:40} | (null)")

    print("=" * 80)
    print(f"Profiles WITH website_url: {profiles_with_url}")
    print(f"Profiles WITHOUT website_url: {profiles_without_url}")

    # Check specific profile
    print("\n" + "=" * 80)
    print("Checking profile_208958070 specifically:")
    cursor.execute("""
        SELECT id, name, ein, website_url, ntee_code_990
        FROM profiles
        WHERE id = 'profile_208958070'
    """)

    specific = cursor.fetchone()
    if specific:
        print(f"ID: {specific['id']}")
        print(f"Name: {specific['name']}")
        print(f"EIN: {specific['ein']}")
        print(f"Website URL: {specific['website_url']}")
        print(f"NTEE Code 990: {specific['ntee_code_990']}")
    else:
        print("Profile not found!")

    conn.close()

if __name__ == "__main__":
    check_website_urls()

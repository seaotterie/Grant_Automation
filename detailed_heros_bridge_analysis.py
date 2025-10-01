#!/usr/bin/env python3
"""
Detailed analysis of Heros Bridge profile including opportunities schema and enhanced data
"""

import sqlite3
import json
from datetime import datetime

def connect_to_database() -> sqlite3.Connection:
    """Connect to the Catalynx SQLite database"""
    db_path = "data/catalynx.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def show_opportunities_schema_and_data(conn: sqlite3.Connection, profile_id: str):
    """Show opportunities table schema and detailed data for Heros Bridge"""

    print("OPPORTUNITIES TABLE SCHEMA:")
    print("-" * 50)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(opportunities)")
    opp_schema = cursor.fetchall()

    for col in opp_schema:
        print(f"{col[1]:30} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10}")

    print()
    print("DETAILED OPPORTUNITIES FOR HEROS BRIDGE:")
    print("-" * 50)

    # Get first 5 opportunities with all available data
    cursor.execute("SELECT * FROM opportunities WHERE profile_id = ? LIMIT 5", (profile_id,))
    opportunities = cursor.fetchall()

    for i, opp in enumerate(opportunities, 1):
        print(f"\nOPPORTUNITY #{i}:")
        print("-" * 20)
        for key in opp.keys():
            value = opp[key]
            if value is not None:
                if len(str(value)) > 100:
                    print(f"{key:25}: {str(value)[:100]}...")
                else:
                    print(f"{key:25}: {value}")
            else:
                print(f"{key:25}: NULL")

def analyze_enhanced_data_fields(conn: sqlite3.Connection, profile_id: str):
    """Analyze the enhanced data fields in detail"""

    print("\nENHANCED DATA FIELDS ANALYSIS:")
    print("=" * 50)

    cursor = conn.cursor()
    cursor.execute("SELECT verification_data, web_enhanced_data FROM profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()

    if row:
        print("VERIFICATION DATA:")
        print("-" * 30)
        if row['verification_data']:
            try:
                verification_data = json.loads(row['verification_data'])
                print(json.dumps(verification_data, indent=2))
            except json.JSONDecodeError:
                print("Could not parse verification data JSON")
                print(f"Raw data: {row['verification_data']}")
        else:
            print("NULL - No verification data stored")

        print("\nWEB ENHANCED DATA:")
        print("-" * 30)
        if row['web_enhanced_data']:
            try:
                enhanced_data = json.loads(row['web_enhanced_data'])
                print(json.dumps(enhanced_data, indent=2))
            except json.JSONDecodeError:
                print("Could not parse web enhanced data JSON")
                print(f"Raw data: {row['web_enhanced_data']}")
        else:
            print("NULL - No web enhanced data stored")

def show_database_statistics(conn: sqlite3.Connection):
    """Show overall database statistics"""

    print("\nDATABASE STATISTICS:")
    print("=" * 30)

    cursor = conn.cursor()

    # Count profiles
    cursor.execute("SELECT COUNT(*) as count FROM profiles")
    profile_count = cursor.fetchone()['count']
    print(f"Total Profiles: {profile_count}")

    # Count opportunities
    cursor.execute("SELECT COUNT(*) as count FROM opportunities")
    opp_count = cursor.fetchone()['count']
    print(f"Total Opportunities: {opp_count}")

    # Count opportunities for Heros Bridge
    cursor.execute("SELECT COUNT(*) as count FROM opportunities WHERE profile_id = ?", ("profile_f3adef3b653c",))
    heros_opp_count = cursor.fetchone()['count']
    print(f"Heros Bridge Opportunities: {heros_opp_count}")

    # Check for enhanced data usage
    cursor.execute("SELECT COUNT(*) as count FROM profiles WHERE verification_data IS NOT NULL")
    verified_count = cursor.fetchone()['count']
    print(f"Profiles with Verification Data: {verified_count}")

    cursor.execute("SELECT COUNT(*) as count FROM profiles WHERE web_enhanced_data IS NOT NULL")
    enhanced_count = cursor.fetchone()['count']
    print(f"Profiles with Web Enhanced Data: {enhanced_count}")

def main():
    """Main execution function"""
    profile_id = "profile_f3adef3b653c"  # Heros Bridge profile ID

    try:
        conn = connect_to_database()

        show_opportunities_schema_and_data(conn, profile_id)
        analyze_enhanced_data_fields(conn, profile_id)
        show_database_statistics(conn)

        conn.close()
        print("\nSUCCESS: Detailed analysis completed successfully")

    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")

if __name__ == "__main__":
    main()
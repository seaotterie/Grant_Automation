#!/usr/bin/env python3
"""
Query and display complete Heros Bridge profile data from SQLite database
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional

def connect_to_database() -> sqlite3.Connection:
    """Connect to the Catalynx SQLite database"""
    db_path = "data/catalynx.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def get_table_schema(conn: sqlite3.Connection, table_name: str) -> list:
    """Get the schema information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def format_json_field(value: str, field_name: str) -> str:
    """Format JSON fields for readable display"""
    if not value:
        return "NULL"

    try:
        parsed = json.loads(value)
        if isinstance(parsed, (dict, list)) and len(str(parsed)) > 100:
            return json.dumps(parsed, indent=2)
        else:
            return json.dumps(parsed)
    except (json.JSONDecodeError, TypeError):
        return str(value)

def display_profile_data(conn: sqlite3.Connection, profile_id: str):
    """Query and display all data for the Heros Bridge profile"""

    print("=" * 80)
    print("HEROS BRIDGE PROFILE - COMPLETE SQL DATABASE DATA")
    print("=" * 80)
    print()

    # First, show the profiles table schema
    print("PROFILES TABLE SCHEMA:")
    print("-" * 40)
    schema = get_table_schema(conn, "profiles")
    for col in schema:
        print(f"{col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else 'NULLABLE':10} {col[4] if col[4] else ''}")
    print()

    # Query the profile data
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()

    if not row:
        print(f"ERROR: No profile found with ID: {profile_id}")
        return

    print("PROFILE DATA:")
    print("-" * 40)

    # Define JSON fields that need special formatting
    json_fields = {
        'focus_areas', 'program_areas', 'target_populations', 'ntee_codes',
        'government_criteria', 'geographic_scope', 'service_areas',
        'funding_preferences', 'foundation_grants', 'board_members',
        'performance_metrics', 'processing_history', 'verification_data',
        'web_enhanced_data'
    }

    # Display each field
    for key in row.keys():
        value = row[key]
        print(f"{key:25}: ", end="")

        if value is None:
            print("NULL")
        elif key in json_fields and isinstance(value, str):
            formatted_value = format_json_field(value, key)
            if '\n' in formatted_value:
                print()
                # Indent multi-line JSON
                for line in formatted_value.split('\n'):
                    print(f"{'':27}{line}")
            else:
                print(formatted_value)
        else:
            print(repr(value))

    print()

    # Query associated opportunities
    print("ASSOCIATED OPPORTUNITIES:")
    print("-" * 40)

    # First check what columns exist in opportunities table
    opp_schema = get_table_schema(conn, "opportunities")
    opp_columns = [col[1] for col in opp_schema]

    # Build query based on available columns
    base_columns = "id, organization_name"
    optional_columns = []
    if "funding_amount" in opp_columns:
        optional_columns.append("funding_amount")
    if "amount" in opp_columns:
        optional_columns.append("amount")
    if "deadline" in opp_columns:
        optional_columns.append("deadline")
    if "application_deadline" in opp_columns:
        optional_columns.append("application_deadline")

    query_columns = base_columns + (", " + ", ".join(optional_columns) if optional_columns else "")

    try:
        cursor.execute(f"SELECT {query_columns} FROM opportunities WHERE profile_id = ? LIMIT 10", (profile_id,))
        opportunities = cursor.fetchall()

        if opportunities:
            for opp in opportunities:
                opp_info = f"  * {opp['id']}: {opp['organization_name']}"
                if 'funding_amount' in opp.keys() and opp['funding_amount']:
                    opp_info += f" - ${opp['funding_amount']:,}"
                elif 'amount' in opp.keys() and opp['amount']:
                    opp_info += f" - ${opp['amount']:,}"

                if 'deadline' in opp.keys() and opp['deadline']:
                    opp_info += f" (Due: {opp['deadline']})"
                elif 'application_deadline' in opp.keys() and opp['application_deadline']:
                    opp_info += f" (Due: {opp['application_deadline']})"

                print(opp_info)
        else:
            print("  No opportunities found")
    except sqlite3.Error as e:
        print(f"  Error querying opportunities: {e}")

    print()

    # Enhanced data summary
    if row['verification_data']:
        print("VERIFICATION DATA SUMMARY:")
        print("-" * 40)
        try:
            verification_data = json.loads(row['verification_data'])
            for key, value in verification_data.items():
                print(f"  {key}: {value}")
        except json.JSONDecodeError:
            print("  Could not parse verification data")
        print()

    if row['web_enhanced_data']:
        print("WEB ENHANCED DATA SUMMARY:")
        print("-" * 40)
        try:
            enhanced_data = json.loads(row['web_enhanced_data'])
            for key, value in enhanced_data.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    print(f"  {key}: {len(value)} fields")
                else:
                    print(f"  {key}: {value}")
        except json.JSONDecodeError:
            print("  Could not parse web enhanced data")
        print()

def main():
    """Main execution function"""
    profile_id = "profile_f3adef3b653c"  # Heros Bridge profile ID

    try:
        conn = connect_to_database()
        display_profile_data(conn, profile_id)
        conn.close()

        print("SUCCESS: Database query completed successfully")

    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")

if __name__ == "__main__":
    main()
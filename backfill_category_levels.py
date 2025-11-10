"""
Backfill category_level for opportunities that don't have it.

Calculates category_level based on overall_score and updates analysis_discovery JSON.
"""

import sqlite3
import json
from src.config.database_config import get_catalynx_db

def backfill_category_levels():
    """Backfill missing category_level based on overall_score."""

    db_path = get_catalynx_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find opportunities without category_level
    cursor.execute("""
        SELECT id, overall_score, analysis_discovery
        FROM opportunities
        WHERE json_extract(analysis_discovery, '$.category_level') IS NULL
    """)

    opportunities = cursor.fetchall()
    print(f"Found {len(opportunities)} opportunities without category_level")

    updated = 0
    for opp_id, overall_score, analysis_discovery_str in opportunities:
        # Parse existing analysis_discovery
        analysis_discovery = json.loads(analysis_discovery_str) if analysis_discovery_str else {}

        # Calculate category_level from overall_score
        if overall_score >= 0.74:
            category_level = "qualified"
        elif overall_score >= 0.71:
            category_level = "review"
        elif overall_score >= 0.68:
            category_level = "consider"
        else:
            category_level = "low_priority"

        # Add category_level to analysis_discovery
        analysis_discovery['category_level'] = category_level

        # Update database
        cursor.execute("""
            UPDATE opportunities
            SET analysis_discovery = ?
            WHERE id = ?
        """, (json.dumps(analysis_discovery), opp_id))

        updated += 1
        if updated % 100 == 0:
            print(f"Updated {updated} opportunities...")

    conn.commit()
    conn.close()

    print(f"\n✅ Backfill complete! Updated {updated} opportunities with category_level")

    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            json_extract(analysis_discovery, '$.category_level') as category,
            COUNT(*) as count
        FROM opportunities
        GROUP BY category
    """)

    print("\nCategory breakdown after backfill:")
    for category, count in cursor.fetchall():
        print(f"  {category or 'NULL'}: {count}")

    conn.close()

if __name__ == "__main__":
    backfill_category_levels()

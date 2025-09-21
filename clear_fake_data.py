#!/usr/bin/env python3
"""
Clear contaminated fake data from the database for Heroes Bridge and other test organizations
"""
import sqlite3
import json
from datetime import datetime

def clear_fake_data():
    """Clear fake data from web_intelligence table"""
    db_path = "data/catalynx.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check what's currently in the database for Heroes Bridge
            cursor.execute("""
                SELECT ein, url, leadership_data, program_data, intelligence_quality_score, scrape_date 
                FROM web_intelligence 
                WHERE ein = '812827604'
            """)
            
            existing_records = cursor.fetchall()
            print(f"Found {len(existing_records)} existing records for EIN 812827604")
            
            for record in existing_records:
                ein, url, leadership_data, program_data, score, scrape_date = record
                print(f"\nRecord: EIN={ein}, URL={url}, Score={score}, Date={scrape_date}")
                
                # Parse leadership data to check for fake data
                if leadership_data:
                    try:
                        leaders = json.loads(leadership_data)
                        print(f"Leadership count: {len(leaders)}")
                        for leader in leaders[:3]:  # Show first 3
                            print(f"  - {leader.get('name', 'N/A')}: {leader.get('title', 'N/A')}")
                    except:
                        print(f"  Leadership data: {leadership_data[:100]}...")
            
            # Delete records with fake/test data for Heroes Bridge
            cursor.execute("""
                DELETE FROM web_intelligence 
                WHERE ein = '812827604'
            """)
            
            deleted_count = cursor.rowcount
            print(f"\nDeleted {deleted_count} contaminated records for EIN 812827604")
            
            # Also clear any board member intelligence records
            cursor.execute("""
                DELETE FROM board_member_intelligence 
                WHERE ein = '812827604'
            """)
            
            board_deleted = cursor.rowcount
            print(f"Deleted {board_deleted} board member records for EIN 812827604")
            
            # Clear any scraping activity records
            cursor.execute("""
                DELETE FROM web_scraping_activity 
                WHERE organization_ein = '812827604'
            """)
            
            activity_deleted = cursor.rowcount
            print(f"Deleted {activity_deleted} scraping activity records for EIN 812827604")
            
            conn.commit()
            print("\nDatabase cleanup completed successfully!")
            
    except Exception as e:
        print(f"Error cleaning database: {e}")

if __name__ == "__main__":
    clear_fake_data()
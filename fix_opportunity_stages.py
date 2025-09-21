#!/usr/bin/env python3
"""
Fix Opportunity Stage Migration Script
Updates all opportunities with invalid 'discovery' stage to valid 'prospects' stage
This resolves the frontend validation errors preventing opportunities from displaying
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

def fix_opportunity_stages():
    """Fix all opportunity stages from 'discovery' to 'prospects'"""
    
    print("=== Opportunity Stage Migration Script ===")
    print(f"Timestamp: {datetime.now()}")
    
    db_path = "data/catalynx.db"
    
    if not Path(db_path).exists():
        print(f"ERROR: Database not found at {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check current stage distribution
            print("\n1. Checking current stage distribution...")
            cursor.execute("SELECT current_stage, COUNT(*) FROM opportunities GROUP BY current_stage")
            stages = cursor.fetchall()
            
            if not stages:
                print("   No opportunities found in database")
                return True
                
            for stage, count in stages:
                print(f"   - {stage}: {count} opportunities")
            
            # Count opportunities with 'discovery' stage
            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE current_stage = 'discovery'")
            discovery_count = cursor.fetchone()[0]
            
            if discovery_count == 0:
                print("   No opportunities with 'discovery' stage found. Migration not needed.")
                return True
            
            print(f"\n2. Found {discovery_count} opportunities with invalid 'discovery' stage")
            print("   Updating to 'prospects' stage...")
            
            # Update current_stage from 'discovery' to 'prospects'
            cursor.execute("""
                UPDATE opportunities 
                SET current_stage = 'prospects',
                    updated_at = datetime('now')
                WHERE current_stage = 'discovery'
            """)
            
            updated_count = cursor.rowcount
            print(f"   SUCCESS: Updated {updated_count} opportunities")
            
            # Update stage_history JSON to reflect the change
            print("\n3. Updating stage history records...")
            cursor.execute("""
                SELECT id, stage_history FROM opportunities 
                WHERE current_stage = 'prospects' 
                AND stage_history LIKE '%"stage":"discovery"%'
            """)
            
            opportunities_to_update = cursor.fetchall()
            history_updates = 0
            
            for opp_id, stage_history_json in opportunities_to_update:
                if stage_history_json:
                    # Simple string replacement for the JSON
                    updated_history = stage_history_json.replace('"stage":"discovery"', '"stage":"prospects"')
                    cursor.execute("""
                        UPDATE opportunities 
                        SET stage_history = ?
                        WHERE id = ?
                    """, (updated_history, opp_id))
                    history_updates += 1
            
            print(f"   SUCCESS: Updated {history_updates} stage history records")
            
            # Verify the changes
            print("\n4. Verifying migration results...")
            cursor.execute("SELECT current_stage, COUNT(*) FROM opportunities GROUP BY current_stage")
            new_stages = cursor.fetchall()
            
            for stage, count in new_stages:
                print(f"   - {stage}: {count} opportunities")
            
            # Check for any remaining 'discovery' stages
            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE current_stage = 'discovery'")
            remaining_discovery = cursor.fetchone()[0]
            
            if remaining_discovery > 0:
                print(f"   WARNING: {remaining_discovery} opportunities still have 'discovery' stage")
                return False
            else:
                print("   SUCCESS: All opportunities now have valid stages")
            
            conn.commit()
            print(f"\n5. Migration completed successfully!")
            print("   - All opportunities moved from 'discovery' to 'prospects' stage")
            print("   - Stage history records updated")
            print("   - Frontend validation should now pass")
            print("   - Discovery tab should display all opportunities")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_opportunity_stages()
    if success:
        print("\nSUCCESS: Opportunity stage migration completed!")
        print("You can now refresh the Discovery tab to see all opportunities.")
    else:
        print("\nERROR: Migration failed. Please check the error messages above.")
        sys.exit(1)
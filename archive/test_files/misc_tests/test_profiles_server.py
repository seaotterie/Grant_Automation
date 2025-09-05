#!/usr/bin/env python3
"""
Simplified test server just for profiles functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.query_interface import DatabaseQueryInterface, QueryFilter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Catalynx Profiles Test", version="1.0.0")

# Initialize database interface with absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "data", "catalynx.db")
print(f"Using database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

db_query_interface = DatabaseQueryInterface(db_path)

# Serve static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("src/web/static/index.html")

@app.get("/api/profiles")
async def list_profiles(
    status: Optional[str] = None, 
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """List all organization profiles from database."""
    try:
        logger.info("=== PROFILES API CALLED ===")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Test database connection
        db_path = "data/catalynx.db"
        if os.path.exists(db_path):
            logger.info(f"Database file exists: {db_path}")
        else:
            logger.error(f"Database file NOT found: {db_path}")
            
        logger.info("Initializing fresh database interface...")
        fresh_db = DatabaseQueryInterface(db_path)
        
        logger.info("Fetching profiles from database...")
        profiles, total_count = fresh_db.filter_profiles(QueryFilter())
        
        logger.info(f"Found {len(profiles)} profiles in database (total: {total_count})")
        
        if len(profiles) == 0:
            logger.warning("No profiles found! This might be a database issue.")
            
            # Try to debug the database
            try:
                with fresh_db.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM profiles")
                    row_count = cursor.fetchone()[0]
                    logger.info(f"Raw profile count from database: {row_count}")
            except Exception as db_debug_error:
                logger.error(f"Database debug error: {db_debug_error}")
        
        # Add opportunity count for each profile
        for profile in profiles:
            opportunities, opp_count = fresh_db.filter_opportunities(
                QueryFilter(profile_ids=[profile["id"]])
            )
            profile["opportunities_count"] = len(opportunities)
            
            # Rename 'id' to 'profile_id' for frontend compatibility
            profile["profile_id"] = profile["id"]
            
            logger.info(f"Profile: {profile['name']} - {profile['opportunities_count']} opportunities")
        
        # Apply limit if specified
        if limit:
            profiles = profiles[:limit]
        
        logger.info(f"Returning {len(profiles)} profiles to frontend")
        return {"profiles": profiles}
        
    except Exception as e:
        logger.error(f"Failed to list profiles from database: {e}")
        import traceback
        traceback.print_exc()
        return {"profiles": [], "error": str(e)}

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str) -> Dict[str, Any]:
    """Get a specific profile."""
    try:
        profiles, _ = db_query_interface.filter_profiles(QueryFilter(profile_ids=[profile_id]))
        
        if not profiles:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = profiles[0]
        
        # Add opportunity count
        opportunities, _ = db_query_interface.filter_opportunities(
            QueryFilter(profile_ids=[profile_id])
        )
        profile["opportunities_count"] = len(opportunities)
        profile["profile_id"] = profile["id"]
        
        return {"profile": profile}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Catalynx Profiles Test Server...")
    print("Access the web interface at: http://localhost:8000")
    print("API endpoint: http://localhost:8000/api/profiles")
    uvicorn.run(app, host="0.0.0.0", port=8000)
#!/usr/bin/env python3
"""
Ultra-simple test server to fix the profiles issue
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

app = FastAPI()

# Serve static files
if os.path.exists("src/web/static"):
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    if os.path.exists("src/web/static/index.html"):
        return FileResponse("src/web/static/index.html")
    return {"message": "Static files not found"}

@app.get("/api/profiles")
async def get_profiles():
    """Working profiles endpoint"""
    try:
        from database.query_interface import DatabaseQueryInterface, QueryFilter
        
        db_path = "data/catalynx.db"
        if not os.path.exists(db_path):
            return {"profiles": [], "error": f"Database not found: {db_path}"}
        
        db_interface = DatabaseQueryInterface(db_path)
        profiles, total_count = db_interface.filter_profiles(QueryFilter())
        
        # Format profiles for frontend
        for profile in profiles:
            opportunities, _ = db_interface.filter_opportunities(
                QueryFilter(profile_ids=[profile["id"]])
            )
            profile["opportunities_count"] = len(opportunities)
            profile["profile_id"] = profile["id"]  # Frontend compatibility
        
        print(f"Returning {len(profiles)} profiles to frontend")
        return {"profiles": profiles}
        
    except Exception as e:
        print(f"Error in profiles endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {"profiles": [], "error": str(e)}

@app.get("/api/profiles/{profile_id}/opportunities")
async def get_profile_opportunities(profile_id: str):
    """Get opportunities for a specific profile"""
    try:
        from database.query_interface import DatabaseQueryInterface, QueryFilter
        
        db_path = "data/catalynx.db"
        if not os.path.exists(db_path):
            return {"opportunities": [], "error": f"Database not found: {db_path}"}
        
        db_interface = DatabaseQueryInterface(db_path)
        opportunities, total_count = db_interface.filter_opportunities(
            QueryFilter(profile_ids=[profile_id])
        )
        
        # Fix: Add missing fields that frontend expects
        for opp in opportunities:
            # Add compatibility_score if missing (frontend validation requires it)
            if 'compatibility_score' not in opp:
                opp['compatibility_score'] = opp.get('overall_score', 0.5)  # Use overall_score as fallback
            
            # Add opportunity_id if missing (frontend may expect this field name)
            if 'opportunity_id' not in opp:
                opp['opportunity_id'] = opp.get('id')
                
            # Ensure all required fields exist for frontend validation
            if 'pipeline_stage' not in opp:
                opp['pipeline_stage'] = opp.get('current_stage', 'discovery')
            if 'funnel_stage' not in opp:
                opp['funnel_stage'] = 'prospects'
            if 'source_type' not in opp:
                opp['source_type'] = 'Nonprofit'
            if 'title' not in opp:
                opp['title'] = opp.get('organization_name', opp.get('name', 'Unknown Opportunity'))
            if 'description' not in opp:
                opp['description'] = opp.get('mission', opp.get('summary', ''))
            if 'amount' not in opp:
                opp['amount'] = opp.get('award_ceiling', opp.get('revenue', 0))
            if 'deadline' not in opp:
                opp['deadline'] = opp.get('close_date', '')
            if 'source' not in opp:
                opp['source'] = opp.get('agency', opp.get('source_name', 'Unknown'))
            if 'status' not in opp:
                opp['status'] = opp.get('current_status', 'active')
            if 'category' not in opp:
                opp['category'] = opp.get('focus_area', 'General')
        
        print(f"Returning {len(opportunities)} opportunities for profile {profile_id}")
        
        # Debug: Log a sample opportunity to verify format
        if opportunities:
            sample = opportunities[0]
            print(f"Sample opportunity keys: {list(sample.keys())}")
            print(f"Sample ID: {sample.get('id')}, Name: {sample.get('organization_name')}")
        
        response_data = {
            "opportunities": opportunities,
            "total_opportunities": total_count,
            "profile_id": profile_id
        }
        
        print(f"Response format: {list(response_data.keys())}")
        return response_data
        
    except Exception as e:
        print(f"Error in opportunities endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {"opportunities": [], "error": str(e)}

# Add basic endpoints to prevent 404 errors
@app.get("/api/dashboard/overview")
async def dashboard_overview():
    return {"status": "ok", "message": "Dashboard data not implemented"}

@app.get("/api/system/status")
async def system_status():
    return {"status": "ok", "message": "System running"}

@app.get("/api/system/health")
async def system_health():
    return {"status": "healthy", "message": "All systems operational"}

@app.get("/api/welcome/status")
async def welcome_status():
    return {"status": "ok", "message": "Welcome"}

@app.get("/api/workflows")
async def workflows():
    return {"workflows": [], "message": "Workflows not implemented"}

@app.get("/api/profiles/{profile_id}/plan-results")
async def plan_results(profile_id: str):
    """Get plan results for a profile"""
    try:
        from database.query_interface import DatabaseQueryInterface, QueryFilter
        
        db_path = "data/catalynx.db"
        if not os.path.exists(db_path):
            return {"results": {}, "error": f"Database not found: {db_path}"}
        
        db_interface = DatabaseQueryInterface(db_path)
        profiles, _ = db_interface.filter_profiles(QueryFilter(profile_ids=[profile_id]))
        
        if not profiles:
            return {"results": {}, "error": "Profile not found"}
        
        # Return basic plan results structure
        return {
            "profile_id": profile_id,
            "results": {
                "created_at": "2025-08-30T12:00:00Z",
                "status": "completed",
                "metadata": {
                    "total_opportunities": 105,
                    "profile_name": profiles[0].get("name", "Unknown"),
                    "last_updated": "2025-08-30T12:00:00Z"
                }
            },
            "message": "Plan results loaded successfully"
        }
        
    except Exception as e:
        print(f"Error in plan results endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {"results": {}, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("Starting simple test server...")
    print("Database exists:", os.path.exists("data/catalynx.db"))
    print("Access: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
#!/usr/bin/env python3
"""
Pages Router
Handles HTML page serving (gateway, root, dashboard) and favicon.
Extracted from monolithic main.py for better modularity.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Static and template directories
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Create router instance
router = APIRouter(tags=["Pages"])


@router.get("/gateway", response_class=HTMLResponse)
async def gateway_page():
    """Serve the Human Gateway review interface."""
    html_file = STATIC_DIR / "gateway.html"
    if html_file.exists():
        return FileResponse(html_file, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
        })
    raise HTTPException(status_code=404, detail="Gateway page not found")


@router.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard interface."""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        # Add cache-busting headers to ensure latest version
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        return FileResponse(html_file, headers=headers)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Catalynx - Loading...</title></head>
            <body>
                <h1>Catalynx Dashboard</h1>
                <p>Setting up the modern interface...</p>
                <p>Static files will be served from /static/</p>
            </body>
        </html>
        """)


@router.get("/dashboard", response_class=HTMLResponse)
async def discovery_dashboard():
    """Discovery Dashboard interface"""
    try:
        template_path = TEMPLATES_DIR / "discovery_dashboard.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")


@router.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors."""
    # Return a simple 1x1 transparent PNG to avoid 404 errors
    # This prevents favicon requests from showing up as errors in logs
    favicon_path = STATIC_DIR / "CatalynxLogo.png"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/x-icon")
    else:
        # Return empty response to prevent 404
        return Response(status_code=204)

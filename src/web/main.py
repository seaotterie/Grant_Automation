#!/usr/bin/env python3
"""
Catalynx - Modern Web Interface
FastAPI backend with real-time progress monitoring
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import os
import uvicorn
from pathlib import Path

# When installed via ``pip install -e .`` (pyproject.toml), setuptools makes
# ``src.*`` and ``tools.*`` importable automatically.  The fallback below only
# activates for *uninstalled* development runs (``python src/web/main.py``).
try:
    from importlib.util import find_spec as _find_spec
    if _find_spec("src") is None:
        _project_root = str(Path(__file__).resolve().parent.parent.parent)
        if _project_root not in sys.path:
            sys.path.insert(0, _project_root)
    del _find_spec
except Exception:
    pass

# Security and Authentication imports
from src.middleware.security import (
    SecurityHeadersMiddleware,
    XSSProtectionMiddleware,
    InputValidationMiddleware,
    RateLimitingMiddleware
)
from src.web.auth_routes import router as auth_router
from src.web.routers.intelligence import router as intelligence_router
from src.web.routers.workflows import router as workflows_router
from src.web.routers.gateway import router as gateway_router
from src.web.routers.learning import router as learning_router
from src.web.routers.profiles import router as profiles_router
from src.web.routers.profiles_v2 import router as profiles_v2_router
from src.web.routers.profiles_intelligence import router as profiles_intelligence_router
from src.web.routers.discovery_v2 import router as discovery_v2_router
from src.web.routers.discovery_legacy import router as discovery_legacy_router
from src.web.routers.discovery import router as discovery_router

# Optional enhanced scraping router (requires scrapy)
try:
    from src.web.routers.enhanced_scraping import router as enhanced_scraping_router
    enhanced_scraping_available = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"Enhanced scraping not available: {e}")
    enhanced_scraping_router = None
    enhanced_scraping_available = False

# Error Handling imports
from src.web.middleware.error_handling import (
    ErrorHandlingMiddleware,
    RequestContextMiddleware,
    validation_exception_handler,
    http_exception_handler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    logger.info("Starting Catalynx Web Interface...")
    logger.info("Initializing 12-factor tool architecture...")

    try:
        from src.core.tool_registry import get_registry
        tool_registry = get_registry()
        operational_tools = tool_registry.get_operational_tools()
        logger.info(f"Loaded {len(operational_tools)} operational 12-factor tools")
    except Exception as e:
        logger.warning(f"Failed to initialize tool registry: {e}")

    logger.info("Catalynx API ready!")
    yield
    logger.info("Shutting down Catalynx Web Interface...")


# Create FastAPI application
app = FastAPI(
    title="Catalynx - Grant Research Automation",
    description="Modern web interface for intelligent grant research and classification",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS — explicit origins, methods, and headers
_cors_origins = [o.strip() for o in os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Custom middleware to disable TRACE method
@app.middleware("http")
async def disable_trace_method(request: Request, call_next):
    if request.method == "TRACE":
        raise HTTPException(status_code=405, detail="Method not allowed")
    return await call_next(request)

# Add error handling middleware (order matters - add in reverse order of execution)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(ErrorHandlingMiddleware, include_debug_info=False)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(XSSProtectionMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=60)

# Add deprecation middleware for Phase 9 API consolidation
from src.web.middleware.deprecation import add_deprecation_headers
app.middleware("http")(add_deprecation_headers)

# Include authentication routes
app.include_router(auth_router)

# Include Intelligence (Tiered Analysis) routes
app.include_router(intelligence_router)

# Include Workflow execution routes
app.include_router(workflows_router)

# Human Gateway
app.include_router(gateway_router)
app.include_router(learning_router)

# Include unified tool execution routes
from src.web.routers.tools import router as tools_router
app.include_router(tools_router)

# Include profile routes
app.include_router(profiles_router)
app.include_router(profiles_v2_router)
app.include_router(profiles_intelligence_router)

# Include discovery routes
app.include_router(discovery_v2_router)
app.include_router(discovery_legacy_router)
app.include_router(discovery_router)

# Include opportunities routes
from src.web.routers.opportunities import router as opportunities_router
app.include_router(opportunities_router)

# Include admin routes
from src.web.routers.admin import router as admin_router
app.include_router(admin_router)

# Include Foundation Network Intelligence routes
from src.web.routers.foundation_network import router as foundation_network_router
app.include_router(foundation_network_router)

# Include Network Graph routes
from src.web.routers.network import router as network_router
app.include_router(network_router)

# Include Enhanced Scraping routes (optional)
if enhanced_scraping_available and enhanced_scraping_router:
    app.include_router(enhanced_scraping_router)

# Include extracted route modules
from src.web.routers.docs_help import router as docs_help_router
app.include_router(docs_help_router)

from src.web.routers.welcome import router as welcome_router
app.include_router(welcome_router)

from src.web.routers.pages import router as pages_router
app.include_router(pages_router)

from src.web.routers.pipeline import router as pipeline_router
app.include_router(pipeline_router)

from src.web.routers.funnel import router as funnel_router
app.include_router(funnel_router)

from src.web.routers.analysis import router as analysis_router
app.include_router(analysis_router)

from src.web.routers.ai_endpoints import router as ai_endpoints_router
app.include_router(ai_endpoints_router)

from src.web.routers.scoring_promotion import router as scoring_promotion_router
app.include_router(scoring_promotion_router)

from src.web.routers.dossier import router as dossier_router
app.include_router(dossier_router)

from src.web.routers.visualizations import router as visualizations_router
app.include_router(visualizations_router)

from src.web.routers.classification import router as classification_router
app.include_router(classification_router)

from src.web.routers.search_export import router as search_export_router
app.include_router(search_export_router)

from src.web.routers.research import router as research_router
app.include_router(research_router)

from src.web.routers.profiles_extras import router as profiles_extras_router
app.include_router(profiles_extras_router)

from src.web.routers.websocket import router as websocket_router
app.include_router(websocket_router)

# Add global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
try:
    from pydantic import ValidationError
    app.add_exception_handler(ValidationError, validation_exception_handler)
except ImportError:
    logger.warning("Pydantic ValidationError handler not available")

# Serve static files using FastAPI's built-in StaticFiles (secure, no path traversal)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Entry point for the ``catalynx`` console script (pyproject.toml)."""
    logger.info("Starting Catalynx Web Interface on http://%s:%s", host, port)
    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    main()

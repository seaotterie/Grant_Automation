"""
HTTP Server for BMF Filter Tool
==============================

12-Factor Factor 7: Port binding - export services via port binding

This server provides HTTP endpoints for the BMF Filter Tool, demonstrating
how a 12-factor tool can be accessed via HTTP API.

Key Features:
- Pure tool execution (no LLM integration at server level)
- Structured input/output (BMFFilterIntent -> BMFFilterResult)
- Health checks and capabilities discovery
- Integration with existing Catalynx patterns
"""

import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

# Import our tool and types
from .bmf_filter import BMFFilterTool
from .generated import BMFFilterIntent, BMFFilterResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global tool instance (stateless, so this is safe)
bmf_tool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management (Factor 9: Disposability)"""
    global bmf_tool

    # Startup
    logger.info("BMF Filter Tool server starting up...")
    bmf_tool = BMFFilterTool()
    logger.info("BMF Filter Tool initialized")

    yield

    # Shutdown
    logger.info("BMF Filter Tool server shutting down...")
    bmf_tool = None
    logger.info("BMF Filter Tool shutdown complete")

# Create FastAPI app with proper 12-factor configuration
app = FastAPI(
    title="BMF Filter Tool - 12-Factor Implementation",
    description="Demonstration of 12-factor agents framework for BMF data filtering",
    version="1.0.0",
    lifespan=lifespan,
    # Factor 11: Logs as event streams
    docs_url="/docs" if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true" else None
)

# CORS middleware for integration with existing Catalynx web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Catalynx main service
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Request logging middleware (Factor 11: Logs as event streams)"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )

    return response

@app.post("/filter", response_model=BMFFilterResult)
async def filter_bmf_data(intent: BMFFilterIntent):
    """
    Execute BMF filtering with structured intent

    This endpoint demonstrates Factor 4: Tools are structured outputs
    - Accepts structured BMFFilterIntent
    - Returns structured BMFFilterResult
    - Pure deterministic processing

    Args:
        intent: Structured filtering intent

    Returns:
        BMFFilterResult: Filtered organizations with metadata
    """
    try:
        logger.info(f"Executing BMF filter: {intent.what_youre_looking_for}")

        if not bmf_tool:
            raise HTTPException(status_code=503, detail="BMF Filter Tool not initialized")

        # Execute the tool (pure deterministic processing)
        result = await bmf_tool.execute(intent)

        logger.info(f"BMF filter completed: {len(result.organizations)} results in {result.execution_metadata.execution_time_ms:.1f}ms")

        return result

    except ValueError as e:
        logger.warning(f"BMF filter validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"BMF filter file error: {str(e)}")
        raise HTTPException(status_code=503, detail="BMF data file not available")
    except Exception as e:
        logger.error(f"BMF filter execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint (Factor 9: Fast startup/graceful shutdown)

    Returns:
        Health status and tool information
    """
    try:
        # Check if tool is available and CSV file exists
        csv_available = bmf_tool and os.path.exists(bmf_tool.input_path) if bmf_tool else False

        status = "healthy" if bmf_tool and csv_available else "degraded"

        health_info = {
            "status": status,
            "tool": "bmf-filter",
            "version": "1.0.0",
            "framework": "12-factor-agents",
            "csv_available": csv_available,
            "input_path": bmf_tool.input_path if bmf_tool else None,
            "timestamp": time.time()
        }

        if status == "healthy":
            return health_info
        else:
            return JSONResponse(
                status_code=503,
                content=health_info
            )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/capabilities")
async def get_capabilities():
    """
    Return tool capabilities and configuration

    Useful for tool discovery and orchestration

    Returns:
        Tool capabilities and metadata
    """
    try:
        capabilities = {
            "tool_name": "bmf-filter",
            "tool_type": "12-factor-agent",
            "framework_version": "1.0.0",

            # Core capabilities
            "capabilities": [
                "bmf_filtering",
                "nonprofit_discovery",
                "csv_data_processing",
                "structured_input_output"
            ],

            # Input/Output contracts (Factor 4)
            "input_type": "BMFFilterIntent",
            "output_type": "BMFFilterResult",
            "input_schema": "/docs#/schemas/BMFFilterIntent",
            "output_schema": "/docs#/schemas/BMFFilterResult",

            # Configuration
            "max_results": bmf_tool.max_results if bmf_tool else 1000,
            "cache_enabled": bmf_tool.cache_enabled if bmf_tool else False,
            "data_source": "local_csv",
            "stateless": True,

            # 12-Factor compliance
            "twelve_factor_compliance": {
                "factor_3_config": True,      # Config from environment
                "factor_4_structured_io": True, # Structured input/output
                "factor_6_stateless": True,   # Stateless processes
                "factor_7_port_binding": True, # Export via port binding
                "factor_9_disposable": True   # Fast startup/shutdown
            },

            # Integration info
            "integration": {
                "can_chain_with_other_tools": True,
                "output_compatible_with": ["ai-analysis-tool", "network-analysis-tool"],
                "designed_for_workflows": True
            }
        }

        return capabilities

    except Exception as e:
        logger.error(f"Capabilities endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """
    Basic metrics endpoint for monitoring (Factor 11: Logs as event streams)

    Returns:
        Basic tool metrics and performance data
    """
    try:
        if not bmf_tool:
            raise HTTPException(status_code=503, detail="Tool not available")

        # Simple metrics (in production, would use proper metrics system)
        metrics = {
            "tool_status": "running",
            "cache_enabled": bmf_tool.cache_enabled,
            "cache_size": len(bmf_tool._cache),
            "input_file_exists": os.path.exists(bmf_tool.input_path),
            "input_file_path": bmf_tool.input_path,
            "max_results_limit": bmf_tool.max_results,
            "memory_limit_mb": bmf_tool.memory_limit_mb,
            "timestamp": time.time()
        }

        return metrics

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "tool": "BMF Filter Tool",
        "framework": "12-factor-agents",
        "version": "1.0.0",
        "description": "Demonstrates 12-factor principles for nonprofit data filtering",
        "endpoints": {
            "filter": "/filter (POST)",
            "health": "/health (GET)",
            "capabilities": "/capabilities (GET)",
            "metrics": "/metrics (GET)",
            "docs": "/docs (GET)" if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true" else None
        },
        "factor_4_demo": "Send BMFFilterIntent to /filter endpoint for structured processing"
    }

def main():
    """
    Main entry point for HTTP server (Factor 7: Port binding)

    Configuration comes from environment variables (Factor 3)
    """
    # Factor 3: Config from environment
    host = os.getenv("BMF_HOST", "0.0.0.0")
    port = int(os.getenv("BMF_FILTER_PORT", "8001"))
    workers = int(os.getenv("BMF_WORKERS", "1"))
    reload = os.getenv("BMF_RELOAD", "false").lower() == "true"
    log_level = os.getenv("BMF_LOG_LEVEL", "info").lower()

    logger.info(f"Starting BMF Filter Tool server on {host}:{port}")
    logger.info(f"Workers: {workers}, Reload: {reload}, Log Level: {log_level}")

    # Factor 7: Port binding - export service via port binding
    uvicorn.run(
        "app.server:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level=log_level,
        # Factor 9: Disposability - graceful shutdown
        timeout_keep_alive=int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "10"))
    )

if __name__ == "__main__":
    main()
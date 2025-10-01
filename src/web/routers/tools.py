"""
Unified Tool Execution API Router
Provides RESTful API for executing all 12-factor tools
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


# Request/Response Models
class ToolExecutionRequest(BaseModel):
    """Request model for tool execution"""
    inputs: Dict[str, Any] = Field(..., description="Tool input parameters")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional tool configuration")


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    success: bool
    tool_name: str
    tool_version: str
    execution_time_ms: float
    cost: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ToolMetadata(BaseModel):
    """Tool metadata response"""
    name: str
    version: str
    status: str
    category: str
    description: str
    single_responsibility: str
    cost_per_operation: float
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


class ToolListResponse(BaseModel):
    """List of available tools"""
    tools: List[Dict[str, str]]
    total_count: int
    operational_count: int


# Initialize tool registry
tool_registry = ToolRegistry()


@router.get("", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List all available tools

    Query Parameters:
    - category: Filter by category (e.g., 'parsing', 'analysis', 'scoring')
    - status: Filter by status (e.g., 'operational', 'deprecated')
    """
    try:
        all_tools = tool_registry.list_tools()

        # Apply filters
        if category:
            all_tools = [t for t in all_tools if t.get('category') == category]

        if status:
            all_tools = [t for t in all_tools if t.get('status') == status]

        operational = [t for t in all_tools if t.get('status') == 'operational']

        return ToolListResponse(
            tools=all_tools,
            total_count=len(all_tools),
            operational_count=len(operational)
        )

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tool_name}", response_model=ToolMetadata)
async def get_tool_metadata(tool_name: str):
    """
    Get metadata for a specific tool

    Path Parameters:
    - tool_name: Name of the tool (e.g., 'xml-990-parser-tool')
    """
    try:
        metadata = tool_registry.get_tool_metadata(tool_name)

        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )

        return ToolMetadata(
            name=metadata.get('name', tool_name),
            version=metadata.get('version', 'unknown'),
            status=metadata.get('status', 'unknown'),
            category=metadata.get('category', 'uncategorized'),
            description=metadata.get('description', ''),
            single_responsibility=metadata.get('single_responsibility', ''),
            cost_per_operation=metadata.get('cost_per_operation', 0.0),
            inputs=metadata.get('inputs', {}),
            outputs=metadata.get('outputs', {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool metadata for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest = Body(...)
):
    """
    Execute a specific tool

    Path Parameters:
    - tool_name: Name of the tool to execute

    Request Body:
    - inputs: Tool-specific input parameters (see tool metadata for schema)
    - config: Optional configuration overrides

    Example:
    ```json
    {
        "inputs": {
            "organization_ein": "81-2827604",
            "historical_data": [...]
        },
        "config": {
            "analysis_years": 5
        }
    }
    ```
    """
    import time

    try:
        # Get tool instance
        tool_instance = tool_registry.get_tool_instance(tool_name, request.config)

        if not tool_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found or could not be instantiated"
            )

        # Validate tool status
        metadata = tool_registry.get_tool_metadata(tool_name)
        if metadata.get('status') != 'operational':
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool_name}' is not operational (status: {metadata.get('status')})"
            )

        # Execute tool
        start_time = time.time()
        result = await tool_instance.execute(**request.inputs)
        execution_time = (time.time() - start_time) * 1000  # ms

        # Get cost estimate
        cost = tool_instance.get_cost_estimate() or 0.0

        # Format response
        if result.is_success:
            # Convert dataclass to dict if necessary
            data = result.data
            if hasattr(data, '__dataclass_fields__'):
                import dataclasses
                data = dataclasses.asdict(data)

            return ToolExecutionResponse(
                success=True,
                tool_name=tool_instance.get_tool_name(),
                tool_version=tool_instance.get_tool_version(),
                execution_time_ms=execution_time,
                cost=cost,
                data=data
            )
        else:
            return ToolExecutionResponse(
                success=False,
                tool_name=tool_instance.get_tool_name(),
                tool_version=tool_instance.get_tool_version(),
                execution_time_ms=execution_time,
                cost=cost,
                error=result.error
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
async def list_categories():
    """
    List all tool categories

    Returns a list of unique categories across all tools
    """
    try:
        all_tools = tool_registry.list_tools()
        categories = set(t.get('category', 'uncategorized') for t in all_tools)

        return {
            "categories": sorted(list(categories)),
            "count": len(categories)
        }

    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for tool API

    Returns operational status and tool counts
    """
    try:
        all_tools = tool_registry.list_tools()
        operational = [t for t in all_tools if t.get('status') == 'operational']
        deprecated = [t for t in all_tools if t.get('status') == 'deprecated']

        return {
            "status": "healthy",
            "total_tools": len(all_tools),
            "operational_tools": len(operational),
            "deprecated_tools": len(deprecated),
            "registry_initialized": True
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

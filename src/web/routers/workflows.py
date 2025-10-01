"""
Workflow API Router
REST API endpoints for workflow execution and management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import uuid
import logging

from src.workflows.workflow_engine import WorkflowEngine, WorkflowResult, WorkflowStatus
from src.workflows.workflow_parser import WorkflowParser
from src.workflows.tool_loader import get_tool_loader

# Initialize router
router = APIRouter(prefix="/api/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)

# In-memory workflow execution tracking (TODO: persist to database)
_workflow_executions: Dict[str, WorkflowResult] = {}
_workflow_status: Dict[str, str] = {}  # execution_id -> "running" | "completed" | "failed"


# Pydantic Models

class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_name: str = Field(..., description="Name of workflow to execute (e.g., 'opportunity_screening', 'deep_intelligence')")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context variables")
    async_execution: bool = Field(default=True, description="Execute asynchronously in background")


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution request"""
    execution_id: str
    workflow_name: str
    status: str
    message: str
    started_at: datetime


class WorkflowStatusResponse(BaseModel):
    """Workflow execution status"""
    execution_id: str
    workflow_name: str
    status: str
    step_count: int
    completed_steps: int
    failed_steps: int
    total_execution_time_ms: float
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


class WorkflowResultResponse(BaseModel):
    """Complete workflow execution result"""
    execution_id: str
    workflow_name: str
    status: str
    step_results: Dict[str, Any]
    total_execution_time_ms: float
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


class ScreeningBatchRequest(BaseModel):
    """Request to screen opportunities"""
    opportunities: List[Dict[str, Any]]
    organization_profile: Dict[str, Any]
    output_directory: str = Field(default="data/workflows/screening")
    fast_threshold: float = Field(default=0.35)
    thorough_threshold: float = Field(default=0.55)


class DeepIntelligenceBatchRequest(BaseModel):
    """Request for deep intelligence analysis"""
    opportunities: List[Dict[str, Any]]  # List of opportunities with context
    organization_ein: str
    organization_name: str
    organization_mission: str
    analysis_depth: str = Field(default="quick", description="quick | standard | enhanced | complete")
    export_format: str = Field(default="pdf", description="pdf | json | excel")
    output_directory: str = Field(default="data/workflows/intelligence")


# Helper Functions

def _get_workflow_definition(workflow_name: str):
    """Load workflow definition from YAML file"""
    workflow_file = Path("src/workflows/definitions") / f"{workflow_name}.yaml"

    if not workflow_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_name}' not found"
        )

    try:
        return WorkflowParser.parse_file(workflow_file)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse workflow: {str(e)}"
        )


async def _execute_workflow_background(
    execution_id: str,
    workflow_name: str,
    context: Dict[str, Any]
):
    """Execute workflow in background"""
    global _workflow_executions, _workflow_status

    logger.info(f"Starting background workflow execution: {execution_id}")
    _workflow_status[execution_id] = "running"

    try:
        # Load workflow definition
        workflow_def = _get_workflow_definition(workflow_name)

        # Execute workflow
        engine = WorkflowEngine()
        result = await engine.execute_workflow(workflow_def, context)

        # Store result
        _workflow_executions[execution_id] = result
        _workflow_status[execution_id] = result.status.value

        logger.info(
            f"Workflow execution completed: {execution_id} - "
            f"status={result.status.value}, time={result.total_execution_time_ms:.2f}ms"
        )

    except Exception as e:
        logger.error(f"Workflow execution failed: {execution_id} - {e}", exc_info=True)
        _workflow_status[execution_id] = "failed"
        # Store error in result (create minimal result object)
        from src.workflows.workflow_engine import WorkflowResult
        _workflow_executions[execution_id] = WorkflowResult(
            workflow_name=workflow_name,
            status=WorkflowStatus.FAILED,
            error=str(e)
        )


# API Endpoints

@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a workflow by name.

    Supports both synchronous and asynchronous execution.
    For long-running workflows, use async_execution=True.
    """
    # Generate execution ID
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now()

    logger.info(
        f"Workflow execution request: {request.workflow_name} "
        f"(execution_id={execution_id}, async={request.async_execution})"
    )

    if request.async_execution:
        # Execute in background
        background_tasks.add_task(
            _execute_workflow_background,
            execution_id,
            request.workflow_name,
            request.context
        )

        return WorkflowExecutionResponse(
            execution_id=execution_id,
            workflow_name=request.workflow_name,
            status="running",
            message=f"Workflow execution started. Use /api/workflows/status/{execution_id} to check progress.",
            started_at=started_at
        )

    else:
        # Execute synchronously
        try:
            workflow_def = _get_workflow_definition(request.workflow_name)
            engine = WorkflowEngine()
            result = await engine.execute_workflow(workflow_def, request.context)

            # Store result
            _workflow_executions[execution_id] = result
            _workflow_status[execution_id] = result.status.value

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                workflow_name=request.workflow_name,
                status=result.status.value,
                message=f"Workflow execution completed: {result.status.value}",
                started_at=started_at
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: str):
    """Get workflow execution status"""

    if execution_id not in _workflow_status:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow execution not found: {execution_id}"
        )

    status = _workflow_status[execution_id]
    result = _workflow_executions.get(execution_id)

    if result:
        # Full result available
        step_count = len(result.step_results)
        completed_steps = sum(
            1 for r in result.step_results.values()
            if r.status == WorkflowStatus.COMPLETED
        )
        failed_steps = sum(
            1 for r in result.step_results.values()
            if r.status == WorkflowStatus.FAILED
        )

        return WorkflowStatusResponse(
            execution_id=execution_id,
            workflow_name=result.workflow_name,
            status=status,
            step_count=step_count,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_execution_time_ms=result.total_execution_time_ms,
            started_at=result.start_time,
            completed_at=result.end_time,
            error=result.error
        )
    else:
        # Still running, no result yet
        return WorkflowStatusResponse(
            execution_id=execution_id,
            workflow_name="unknown",
            status=status,
            step_count=0,
            completed_steps=0,
            failed_steps=0,
            total_execution_time_ms=0.0,
            started_at=datetime.now()
        )


@router.get("/results/{execution_id}", response_model=WorkflowResultResponse)
async def get_workflow_results(execution_id: str):
    """Get complete workflow execution results"""

    if execution_id not in _workflow_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow results not available: {execution_id}"
        )

    result = _workflow_executions[execution_id]

    # Convert step results to dict
    step_results_dict = {
        name: {
            "status": r.status.value,
            "output": r.output,
            "error": r.error,
            "execution_time_ms": r.execution_time_ms
        }
        for name, r in result.step_results.items()
    }

    return WorkflowResultResponse(
        execution_id=execution_id,
        workflow_name=result.workflow_name,
        status=result.status.value,
        step_results=step_results_dict,
        total_execution_time_ms=result.total_execution_time_ms,
        started_at=result.start_time,
        completed_at=result.end_time,
        error=result.error
    )


@router.get("/list")
async def list_workflows():
    """List available workflows"""

    workflows_dir = Path("src/workflows/definitions")
    if not workflows_dir.exists():
        return {"workflows": []}

    workflows = []
    for workflow_file in workflows_dir.glob("*.yaml"):
        try:
            workflow_def = WorkflowParser.parse_file(workflow_file)
            workflows.append({
                "name": workflow_def.name,
                "description": workflow_def.description,
                "version": workflow_def.version,
                "steps": len(workflow_def.steps),
                "metadata": workflow_def.metadata
            })
        except Exception as e:
            logger.warning(f"Failed to parse workflow {workflow_file}: {e}")

    return {"workflows": workflows}


@router.get("/executions")
async def list_executions():
    """List all workflow executions"""

    executions = []
    for execution_id, status in _workflow_status.items():
        result = _workflow_executions.get(execution_id)

        executions.append({
            "execution_id": execution_id,
            "workflow_name": result.workflow_name if result else "unknown",
            "status": status,
            "started_at": result.start_time if result else None,
            "completed_at": result.end_time if result else None
        })

    return {"executions": executions}


# Convenience Endpoints for Common Workflows

@router.post("/screen-opportunities", response_model=WorkflowExecutionResponse)
async def screen_opportunities(
    request: ScreeningBatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Convenience endpoint for opportunity screening workflow.

    Executes two-stage screening (fast → thorough) and returns recommended opportunities.
    """
    execution_id = f"screening_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now()

    # Build workflow context
    context = {
        "opportunities": request.opportunities,
        "organization_profile": request.organization_profile,
        "output_directory": request.output_directory,
        "fast_threshold": request.fast_threshold,
        "thorough_threshold": request.thorough_threshold
    }

    # Execute workflow in background
    background_tasks.add_task(
        _execute_workflow_background,
        execution_id,
        "opportunity_screening",
        context
    )

    return WorkflowExecutionResponse(
        execution_id=execution_id,
        workflow_name="opportunity_screening",
        status="running",
        message=f"Screening {len(request.opportunities)} opportunities. Check /api/workflows/status/{execution_id}",
        started_at=started_at
    )


@router.post("/deep-intelligence", response_model=WorkflowExecutionResponse)
async def deep_intelligence_analysis(
    request: DeepIntelligenceBatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Convenience endpoint for deep intelligence workflow.

    Executes comprehensive intelligence analysis with configurable depth.
    """
    execution_id = f"intelligence_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now()

    # Build workflow context for each opportunity
    for i, opp in enumerate(request.opportunities):
        opp_execution_id = f"{execution_id}_opp{i+1}"

        context = {
            "opportunity_id": opp.get("opportunity_id"),
            "opportunity_title": opp.get("title"),
            "opportunity_description": opp.get("description"),
            "opportunity_deadline": opp.get("deadline"),
            "funder_name": opp.get("funder"),
            "funder_type": opp.get("funder_type"),
            "organization_ein": request.organization_ein,
            "organization_name": request.organization_name,
            "organization_mission": request.organization_mission,
            "analysis_depth": request.analysis_depth,
            "export_format": request.export_format,
            "output_directory": request.output_directory,
            "screening_score": opp.get("screening_score")
        }

        # Execute each opportunity analysis
        background_tasks.add_task(
            _execute_workflow_background,
            opp_execution_id,
            "deep_intelligence",
            context
        )

    return WorkflowExecutionResponse(
        execution_id=execution_id,
        workflow_name="deep_intelligence",
        status="running",
        message=f"Analyzing {len(request.opportunities)} opportunities. Parent execution ID: {execution_id}",
        started_at=started_at
    )

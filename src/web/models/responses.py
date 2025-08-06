#!/usr/bin/env python3
"""
Response models for Catalynx Web API
Pydantic models for API response serialization
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class SystemStatus(BaseModel):
    """System health status response."""
    
    status: str = Field(..., description="System status")
    processors_available: int = Field(..., description="Number of available processors")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="System version")
    error: Optional[str] = Field(default=None, description="Error message if any")

class DashboardStats(BaseModel):
    """Dashboard overview statistics."""
    
    active_workflows: int = Field(..., description="Number of active workflows")
    total_processed: int = Field(..., description="Total organizations processed")
    success_rate: float = Field(..., description="Overall success rate")
    recent_workflows: List[dict] = Field(..., description="Recent workflow summaries")

class WorkflowResponse(BaseModel):
    """Response for workflow operations."""
    
    workflow_id: str = Field(..., description="Workflow identifier")
    status: WorkflowStatus = Field(..., description="Workflow status")
    message: str = Field(..., description="Status message")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    progress_percentage: Optional[float] = Field(default=None, description="Progress percentage")
    organizations_processed: Optional[int] = Field(default=None, description="Organizations processed")
    errors: Optional[List[str]] = Field(default=None, description="Error messages")

class ProgressUpdate(BaseModel):
    """Real-time progress update."""
    
    workflow_id: str = Field(..., description="Workflow identifier")
    timestamp: datetime = Field(..., description="Update timestamp")
    progress_percentage: float = Field(..., description="Progress percentage")
    current_processor: Optional[str] = Field(default=None, description="Current processor")
    current_organization: Optional[str] = Field(default=None, description="Current organization")
    processed_count: int = Field(..., description="Number processed")
    total_count: int = Field(..., description="Total to process")
    processing_speed: Optional[float] = Field(default=None, description="Organizations per second")
    eta_minutes: Optional[float] = Field(default=None, description="Estimated time remaining")
    qualification_breakdown: Optional[Dict[str, int]] = Field(
        default=None, description="Live qualification factor breakdown"
    )
    status: str = Field(..., description="Current status")

class OrganizationResult(BaseModel):
    """Individual organization result."""
    
    ein: str = Field(..., description="EIN")
    name: str = Field(..., description="Organization name")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State")
    zip_code: Optional[str] = Field(default=None, description="ZIP code")
    composite_score: float = Field(..., description="Composite score")
    predicted_category: Optional[str] = Field(default=None, description="Predicted category")
    primary_qualification_reason: Optional[str] = Field(
        default=None, description="Primary qualification reason"
    )
    qualification_strength: Optional[str] = Field(
        default=None, description="Qualification strength"
    )
    assets: Optional[float] = Field(default=None, description="Assets")
    revenue: Optional[float] = Field(default=None, description="Revenue")
    foundation_code: Optional[str] = Field(default=None, description="Foundation code")
    keyword_scores: Optional[Dict[str, float]] = Field(
        default=None, description="Keyword category scores"
    )
    financial_score: Optional[float] = Field(default=None, description="Financial score")
    geographic_score: Optional[float] = Field(default=None, description="Geographic score")
    foundation_score: Optional[float] = Field(default=None, description="Foundation score")

class ClassificationResults(BaseModel):
    """Classification results response."""
    
    workflow_id: str = Field(..., description="Workflow identifier")
    total_analyzed: int = Field(..., description="Total organizations analyzed")
    promising_candidates: List[OrganizationResult] = Field(..., description="Promising candidates")
    category_breakdown: Dict[str, int] = Field(..., description="Category distribution")
    qualification_breakdown: Dict[str, int] = Field(..., description="Qualification factor breakdown")
    score_distribution: Dict[str, int] = Field(..., description="Score distribution")
    processing_time: float = Field(..., description="Processing time in seconds")
    success_rate: float = Field(..., description="Success rate")

class WorkflowResults(BaseModel):
    """Complete workflow results response."""
    
    workflow_id: str = Field(..., description="Workflow identifier")
    organizations: List[OrganizationResult] = Field(..., description="Organization results")
    processors_completed: List[str] = Field(..., description="Completed processors")
    total_processing_time: float = Field(..., description="Total processing time")
    success_rate: float = Field(..., description="Success rate")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")

class ExportResponse(BaseModel):
    """Export operation response."""
    
    export_id: str = Field(..., description="Export identifier")
    filename: str = Field(..., description="Generated filename")
    download_url: str = Field(..., description="Download URL")
    format: str = Field(..., description="Export format")
    record_count: int = Field(..., description="Number of records exported")
    file_size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")

class ProcessorInfo(BaseModel):
    """Processor information."""
    
    name: str = Field(..., description="Processor name")
    description: str = Field(..., description="Processor description")
    version: str = Field(..., description="Processor version")
    processor_type: str = Field(..., description="Processor type")
    dependencies: List[str] = Field(..., description="Dependencies")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    status: str = Field(..., description="Current status")

class SystemInfo(BaseModel):
    """System information response."""
    
    version: str = Field(..., description="System version")
    processors: List[ProcessorInfo] = Field(..., description="Available processors")
    active_workflows: int = Field(..., description="Active workflows")
    cache_size: int = Field(..., description="Cache size in bytes")
    uptime: str = Field(..., description="System uptime")

class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    workflow_id: Optional[str] = Field(default=None, description="Related workflow ID")

class SearchResults(BaseModel):
    """Search results response."""
    
    query: str = Field(..., description="Search query")
    results: List[OrganizationResult] = Field(..., description="Search results")
    total_matches: int = Field(..., description="Total matches found")
    search_time: float = Field(..., description="Search time in seconds")
    facets: Optional[Dict[str, Dict[str, int]]] = Field(
        default=None, description="Search facets"
    )
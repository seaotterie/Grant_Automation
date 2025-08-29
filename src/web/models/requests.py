#!/usr/bin/env python3
"""
Request models for Catalynx Web API
Pydantic models for API request validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ClassificationRequest(BaseModel):
    """Request model for intelligent classification."""
    
    state: str = Field(default="VA", description="State to analyze")
    min_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum composite score threshold")
    max_results: Optional[int] = Field(default=None, gt=0, description="Maximum results to process")
    categories: List[str] = Field(
        default=["health", "nutrition", "safety", "education"],
        description="Categories to include in classification"
    )
    export_format: str = Field(default="csv", description="Export format (csv, json)")
    detailed_analysis: bool = Field(default=True, description="Include detailed qualification analysis")

class WorkflowRequest(BaseModel):
    """Request model for complete workflow execution."""
    
    name: Optional[str] = Field(default=None, description="Workflow name")
    target_ein: Optional[str] = Field(default=None, description="Target EIN for similarity analysis")
    states: List[str] = Field(default=["VA"], description="States to analyze")
    ntee_codes: List[str] = Field(
        default=["E21", "E30", "E32", "E60", "E86", "F30", "F32"],
        description="NTEE codes to include"
    )
    min_revenue: int = Field(default=0, ge=0, description="Minimum revenue threshold (0 = no filter)")
    max_results: int = Field(default=1000, gt=0, description="Maximum results to process")
    include_classified: bool = Field(default=False, description="Include classified organizations")
    classification_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, 
        description="Minimum classification score threshold"
    )

class ProgressSubscriptionRequest(BaseModel):
    """Request model for WebSocket progress subscription."""
    
    workflow_id: str = Field(..., description="Workflow ID to monitor")
    update_frequency: int = Field(default=1, ge=1, le=10, description="Update frequency in seconds")

class ExportRequest(BaseModel):
    """Request model for data export."""
    
    workflow_id: str = Field(..., description="Workflow ID to export")
    format: str = Field(default="csv", description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    min_score: Optional[float] = Field(default=None, description="Minimum score filter")
    categories: Optional[List[str]] = Field(default=None, description="Categories to include")

class SystemConfigRequest(BaseModel):
    """Request model for system configuration updates."""
    
    max_concurrent_workflows: int = Field(default=2, ge=1, le=5)
    default_export_format: str = Field(default="csv")
    cache_retention_days: int = Field(default=30, ge=1, le=365)
    enable_real_time_updates: bool = Field(default=True)

class SearchRequest(BaseModel):
    """Request model for organization search."""
    
    query: str = Field(..., min_length=1, description="Search query")
    search_fields: List[str] = Field(
        default=["name", "city", "state"],
        description="Fields to search in"
    )
    limit: int = Field(default=50, gt=0, le=500, description="Maximum results")
    filters: Optional[dict] = Field(default=None, description="Additional filters")
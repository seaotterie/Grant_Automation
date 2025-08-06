#!/usr/bin/env python3
"""
Workflow Service for Web Interface
Integrates with existing workflow engine and provides web-friendly interface
"""

import asyncio
import logging
import json
import csv
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
import traceback

from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.processors.analysis.intelligent_classifier import IntelligentClassifier
from src.web.models.requests import ClassificationRequest, WorkflowRequest
from src.web.models.responses import WorkflowResponse, ClassificationResults, WorkflowResults
from src.web.services.progress_service import ProgressTracker

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service layer for workflow management and execution."""
    
    def __init__(self):
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.completed_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def run_classification_with_progress(self, 
                                             workflow_id: str, 
                                             request: ClassificationRequest,
                                             progress_callback: Callable):
        """Run intelligent classification with real-time progress updates."""
        
        try:
            # Create progress tracker
            from src.web.services.progress_service import ProgressService
            progress_service = ProgressService()
            tracker = ProgressTracker(workflow_id, progress_service)
            
            # Store workflow info
            self.active_workflows[workflow_id] = {
                "type": "classification",
                "request": request.dict(),
                "started_at": datetime.now(),
                "status": "running"
            }
            
            # Initialize progress
            await tracker.update_progress(
                processed=0,
                total=0,
                current_processor="intelligent_classifier",
                status="initializing"
            )
            
            # Create configuration for classification
            config = WorkflowConfig(
                workflow_id=workflow_id,
                name="Web Classification",
                states=[request.state],
                max_results=50000  # Process all available
            )
            
            # Create processor config
            processor_config = ProcessorConfig(
                workflow_id=workflow_id,
                processor_name="intelligent_classifier",
                workflow_config=config
            )
            
            # Initialize classifier
            classifier = IntelligentClassifier()
            
            # Custom progress callback to update tracker
            original_update_progress = classifier._update_progress
            
            def enhanced_update_progress(current_step, total_steps, message):
                # Call original progress update
                original_update_progress(current_step, total_steps, message)
                
                # Update our tracker
                asyncio.create_task(tracker.update_progress(
                    processed=current_step * 1000,  # Estimate based on step
                    current_processor="intelligent_classifier",
                    status=message
                ))
            
            classifier._update_progress = enhanced_update_progress
            
            # Execute classification
            logger.info(f"Starting classification for workflow {workflow_id}")
            await tracker.update_progress(status="loading_organizations")
            
            result = await classifier.execute(processor_config)
            
            if not result.success:
                error_msg = f"Classification failed: {'; '.join(result.errors)}"
                await tracker.error(error_msg)
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["error"] = error_msg
                return
            
            # Extract results
            classified_orgs = result.data.get('classified_organizations', [])
            promising_candidates = result.data.get('promising_candidates', [])
            total_unclassified = result.data.get('total_unclassified', 0)
            
            # Filter by request parameters
            if request.min_score:
                promising_candidates = [
                    org for org in promising_candidates 
                    if org['composite_score'] >= request.min_score
                ]
            
            if request.max_results:
                promising_candidates = promising_candidates[:request.max_results]
            
            # Update progress with qualification breakdown
            qualification_breakdown = {}
            for org in promising_candidates:
                if 'primary_qualification_reason' in org:
                    reason = org['primary_qualification_reason']
                    if 'keyword match' in reason.lower():
                        primary_factor = 'Keyword Match'
                    elif 'financial capacity' in reason.lower():
                        primary_factor = 'Financial Strength'
                    elif 'foundation type' in reason.lower():
                        primary_factor = 'Foundation Type'
                    elif 'geographic' in reason.lower():
                        primary_factor = 'Geographic Match'
                    else:
                        primary_factor = 'Other'
                    
                    qualification_breakdown[primary_factor] = qualification_breakdown.get(primary_factor, 0) + 1
            
            tracker.update_qualification_breakdown(qualification_breakdown)
            
            # Final progress update
            await tracker.update_progress(
                processed=total_unclassified,
                total=total_unclassified,
                status="completed"
            )
            
            # Store results
            classification_results = {
                "workflow_id": workflow_id,
                "total_analyzed": total_unclassified,
                "promising_candidates": promising_candidates,
                "category_breakdown": result.metadata.get('category_breakdown', {}),
                "qualification_breakdown": qualification_breakdown,
                "processing_time": result.execution_time or 0,
                "success_rate": len(promising_candidates) / total_unclassified if total_unclassified > 0 else 0
            }
            
            # Move to completed workflows
            self.completed_workflows[workflow_id] = {
                **self.active_workflows[workflow_id],
                "status": "completed",
                "completed_at": datetime.now(),
                "results": classification_results
            }
            
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            # Broadcast completion
            await tracker.complete(classification_results)
            
            logger.info(f"Classification completed for workflow {workflow_id}: "
                       f"{len(promising_candidates)} candidates found")
        
        except Exception as e:
            logger.error(f"Classification workflow {workflow_id} failed: {e}")
            logger.error(traceback.format_exc())
            
            error_msg = str(e)
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["error"] = error_msg
            
            # Create progress tracker if not exists
            try:
                await tracker.error(error_msg)
            except:
                pass
    
    async def run_workflow_with_progress(self, 
                                       config: WorkflowConfig,
                                       progress_callback: Callable):
        """Run complete workflow with real-time progress updates."""
        
        workflow_id = config.workflow_id
        
        try:
            # Create progress tracker
            from src.web.services.progress_service import ProgressService
            progress_service = ProgressService()
            tracker = ProgressTracker(workflow_id, progress_service)
            
            # Store workflow info
            self.active_workflows[workflow_id] = {
                "type": "workflow",
                "config": config.dict(),
                "started_at": datetime.now(),
                "status": "running"
            }
            
            # Initialize progress
            await tracker.update_progress(
                processed=0,
                total=config.max_results,
                status="initializing"
            )
            
            # Get workflow engine
            engine = get_workflow_engine()
            
            # Add progress callback to engine
            def workflow_progress_callback(wf_id: str, progress: float, message: str):
                processed = int((progress / 100) * config.max_results)
                asyncio.create_task(tracker.update_progress(
                    processed=processed,
                    total=config.max_results,
                    status=message
                ))
            
            engine.add_progress_callback(workflow_progress_callback)
            
            # Execute workflow
            logger.info(f"Starting workflow {workflow_id}")
            workflow_state = await engine.run_workflow(config)
            
            if workflow_state.status.value == "completed":
                # Store successful results
                workflow_results = {
                    "workflow_id": workflow_id,
                    "organizations_processed": workflow_state.organizations_processed,
                    "processors_completed": workflow_state.completed_processors,
                    "total_processing_time": workflow_state.get_execution_time(),
                    "success_rate": 0.8  # Placeholder - calculate from actual results
                }
                
                # Move to completed workflows
                self.completed_workflows[workflow_id] = {
                    **self.active_workflows[workflow_id],
                    "status": "completed",
                    "completed_at": datetime.now(),
                    "results": workflow_results
                }
                
                if workflow_id in self.active_workflows:
                    del self.active_workflows[workflow_id]
                
                await tracker.complete(workflow_results)
                
                logger.info(f"Workflow {workflow_id} completed successfully")
            
            else:
                # Handle workflow failure
                error_msg = f"Workflow failed with status: {workflow_state.status.value}"
                if workflow_state.errors:
                    error_msg += f" Errors: {'; '.join(workflow_state.errors)}"
                
                if workflow_id in self.active_workflows:
                    self.active_workflows[workflow_id]["status"] = "failed"
                    self.active_workflows[workflow_id]["error"] = error_msg
                
                await tracker.error(error_msg)
        
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            logger.error(traceback.format_exc())
            
            error_msg = str(e)
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["error"] = error_msg
            
            try:
                await tracker.error(error_msg)
            except:
                pass
    
    async def get_classification_results(self, workflow_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get classification results for a workflow."""
        
        # Check completed workflows first
        if workflow_id in self.completed_workflows:
            results = self.completed_workflows[workflow_id].get("results", {})
            if limit and "promising_candidates" in results:
                results = results.copy()
                results["promising_candidates"] = results["promising_candidates"][:limit]
            return results
        
        # Check active workflows
        if workflow_id in self.active_workflows:
            return {
                "workflow_id": workflow_id,
                "status": self.active_workflows[workflow_id]["status"],
                "message": "Workflow is still running"
            }
        
        # Workflow not found
        raise ValueError(f"Workflow {workflow_id} not found")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow status."""
        
        # Check active workflows
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check completed workflows
        if workflow_id in self.completed_workflows:
            return self.completed_workflows[workflow_id]
        
        # Workflow not found
        raise ValueError(f"Workflow {workflow_id} not found")
    
    async def export_classification_results(self, workflow_id: str, format: str = "csv") -> str:
        """Export classification results to file."""
        
        results = await self.get_classification_results(workflow_id)
        
        if "promising_candidates" not in results:
            raise ValueError("No results available for export")
        
        candidates = results["promising_candidates"]
        
        # Create export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"classification_{workflow_id}_{timestamp}.{format}"
        filepath = Path(filename)
        
        if format.lower() == "csv":
            # Export to CSV
            if candidates:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=candidates[0].keys())
                    writer.writeheader()
                    writer.writerows(candidates)
        
        elif format.lower() == "json":
            # Export to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return str(filepath)
    
    async def export_workflow_results(self, workflow_id: str, format: str = "csv") -> str:
        """Export workflow results to file."""
        
        workflow_data = await self.get_workflow_status(workflow_id)
        
        if "results" not in workflow_data:
            raise ValueError("No results available for export")
        
        results = workflow_data["results"]
        
        # Create export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{workflow_id}_{timestamp}.{format}"
        filepath = Path(filename)
        
        if format.lower() == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format for workflow: {format}")
        
        return str(filepath)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows (active and completed)."""
        
        workflows = []
        
        # Add active workflows
        for workflow_id, data in self.active_workflows.items():
            workflows.append({
                "workflow_id": workflow_id,
                "status": "active",
                **data
            })
        
        # Add completed workflows
        for workflow_id, data in self.completed_workflows.items():
            workflows.append({
                "workflow_id": workflow_id,
                "status": "completed",
                **data
            })
        
        # Sort by start time (newest first)
        workflows.sort(key=lambda x: x.get("started_at", datetime.min), reverse=True)
        
        return workflows
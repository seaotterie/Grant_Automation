"""
Workflow Engine
Core orchestration engine for managing and executing processing workflows.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Set, Any
from datetime import datetime
from pathlib import Path

from .data_models import (
    WorkflowConfig, WorkflowState, WorkflowStatus, 
    ProcessorResult, ProcessorConfig
)
from .base_processor import BaseProcessor
from ..utils.decorators import log_execution_time


class ProcessorRegistry:
    """Registry for managing available processors."""
    
    def __init__(self):
        self._processors: Dict[str, BaseProcessor] = {}
        self._processor_classes: Dict[str, type] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_processor(self, processor_class: type) -> None:
        """Register a processor class."""
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError(f"Processor must inherit from BaseProcessor: {processor_class}")
        
        # Create instance to get metadata
        instance = processor_class()
        processor_name = instance.metadata.name
        
        self._processor_classes[processor_name] = processor_class
        self.logger.info(f"Registered processor: {processor_name}")
    
    def get_processor(self, name: str) -> Optional[BaseProcessor]:
        """Get a processor instance by name."""
        if name in self._processor_classes:
            return self._processor_classes[name]()
        return None
    
    def list_processors(self) -> List[str]:
        """List all registered processor names."""
        return list(self._processor_classes.keys())
    
    def get_processor_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get processor information."""
        processor = self.get_processor(name)
        return processor.get_processor_info() if processor else None


class DependencyResolver:
    """Resolves processor dependencies and determines execution order."""
    
    def __init__(self, registry: ProcessorRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)
    
    def resolve_execution_order(self, processor_names: List[str]) -> List[str]:
        """
        Resolve processor dependencies and return execution order.
        
        Args:
            processor_names: List of processor names to execute
            
        Returns:
            List of processor names in dependency-resolved order
            
        Raises:
            ValueError: If circular dependency detected or processor not found
        """
        # Get all processor metadata
        processors_metadata = {}
        for name in processor_names:
            processor = self.registry.get_processor(name)
            if not processor:
                raise ValueError(f"Processor not found: {name}")
            processors_metadata[name] = processor.metadata
        
        # Topological sort to resolve dependencies
        visited = set()
        visiting = set()
        execution_order = []
        
        def visit(processor_name: str):
            if processor_name in visiting:
                raise ValueError(f"Circular dependency detected involving: {processor_name}")
            
            if processor_name in visited:
                return
            
            visiting.add(processor_name)
            metadata = processors_metadata.get(processor_name)
            
            if metadata:
                # Visit all dependencies first
                for dep in metadata.dependencies:
                    if dep in processor_names:  # Only consider dependencies that are in our execution list
                        visit(dep)
            
            visiting.remove(processor_name)
            visited.add(processor_name)
            execution_order.append(processor_name)
        
        # Visit all processors
        for name in processor_names:
            visit(name)
        
        self.logger.info(f"Resolved execution order: {execution_order}")
        return execution_order
    
    def get_standard_execution_order(self) -> List[str]:
        """
        Get the standard execution order for grant research workflow.
        
        Returns:
            List of processor names in standard order
        """
        # Enhanced Multi-Track Workflow (Phase 2 Complete)
        standard_order = [
            # DISCOVERY TRACK - Organization Discovery
            "ein_lookup",              # Step 0: EIN lookup and validation  
            "bmf_filter",              # Step 1: Filter IRS Business Master File
            "propublica_fetch",        # Step 2: Fetch data from ProPublica API
            
            # GOVERNMENT TRACK - Federal Opportunities & Historical Awards
            "grants_gov_fetch",        # Step 2a: Discover federal grant opportunities
            "usaspending_fetch",       # Step 2b: Historical federal award analysis
            
            # ANALYSIS TRACK - Scoring and Intelligence
            "financial_scorer",        # Step 3: Score organizations based on financial data
            "government_opportunity_scorer",  # Step 3a: Score government opportunity matches
            
            # EXTENDED ANALYSIS - Advanced Intelligence
            "xml_downloader",          # Step 4a: Download XML 990 filings
            "trend_analyzer",          # Step 4b: Multi-year trend analysis
            "risk_assessor",           # Step 4c: Risk assessment
            "competitive_intelligence", # Step 4d: Competitive analysis
            "board_network_analyzer",  # Step 4e: Board network analysis
            "intelligent_classifier",  # Step 4f: Intelligent classification
            
            # NOTE: pdf_downloader and pdf_ocr are fallback processors
            # They automatically run when XML files are not available
        ]
        
        # Filter to only include processors that are registered
        available_processors = self.registry.list_processors()
        filtered_order = [p for p in standard_order if p in available_processors]
        
        return filtered_order


class WorkflowEngine:
    """
    Core workflow orchestration engine.
    
    Features:
    - Asynchronous execution with progress tracking
    - Automatic dependency resolution
    - Error recovery and retry logic
    - Real-time status updates
    - Workflow pause/resume capability
    - Resource management and concurrency control
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use the global processor registry instead of creating a new one
        from src.processors import get_all_processors, get_processor, list_processors
        self.get_all_processors = get_all_processors
        self.get_processor = get_processor
        self.list_processors = list_processors
        
        # Create a dummy registry that uses global functions for compatibility
        class GlobalProcessorRegistry:
            def get_processor(self, name: str):
                return get_processor(name)
            def list_processors(self):
                return list_processors()
            def register_processor(self, processor_class: type):
                # This is handled automatically by the global system
                pass
            def get_processor_info(self, name: str):
                processor = get_processor(name)
                return processor.get_processor_info() if processor else None
        
        self.registry = GlobalProcessorRegistry()
        self.dependency_resolver = DependencyResolver(self.registry)
        
        # Workflow state management
        self.workflow_states: Dict[str, WorkflowState] = {}
        self.running_workflows: Set[str] = set()
        
        # Event callbacks
        self.status_callbacks: List[Callable] = []
        self.progress_callbacks: List[Callable] = []
        
        # Concurrency control
        self.max_concurrent_workflows = 3
        self.workflow_semaphore = asyncio.Semaphore(self.max_concurrent_workflows)
    
    def register_processor(self, processor_class: type) -> None:
        """Register a processor class with the engine."""
        # This is handled automatically by the global processor system
        pass
    
    def add_status_callback(self, callback: Callable[[str, WorkflowStatus, Dict], None]) -> None:
        """Add callback for workflow status updates."""
        self.status_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable[[str, float, str], None]) -> None:
        """Add callback for workflow progress updates."""
        self.progress_callbacks.append(callback)
    
    def _notify_status_change(self, workflow_id: str, status: WorkflowStatus, data: Dict = None) -> None:
        """Notify all registered callbacks of status changes."""
        for callback in self.status_callbacks:
            try:
                callback(workflow_id, status, data or {})
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def _notify_progress_update(self, workflow_id: str, progress: float, message: str) -> None:
        """Notify all registered callbacks of progress updates."""
        for callback in self.progress_callbacks:
            try:
                callback(workflow_id, progress, message)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
    
    def create_workflow(self, config: WorkflowConfig) -> WorkflowState:
        """
        Create a new workflow state.
        
        Args:
            config: Workflow configuration
            
        Returns:
            WorkflowState object
        """
        workflow_state = WorkflowState(
            workflow_id=config.workflow_id,
            config=config,
            status=WorkflowStatus.PENDING
        )
        
        self.workflow_states[config.workflow_id] = workflow_state
        self.logger.info(f"Created workflow: {config.workflow_id}")
        
        return workflow_state
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID."""
        return self.workflow_states.get(workflow_id)
    
    def list_workflows(self, status_filter: Optional[WorkflowStatus] = None) -> List[WorkflowState]:
        """
        List workflows, optionally filtered by status.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of workflow states
        """
        workflows = list(self.workflow_states.values())
        
        if status_filter:
            workflows = [w for w in workflows if w.status == status_filter]
        
        return workflows
    
    @log_execution_time
    async def run_workflow(self, config: WorkflowConfig) -> WorkflowState:
        """
        Execute a complete workflow asynchronously.
        
        Args:
            config: Workflow configuration
            
        Returns:
            Final workflow state
        """
        workflow_id = config.workflow_id
        
        # Use semaphore to limit concurrent workflows
        async with self.workflow_semaphore:
            try:
                # Create or get workflow state
                if workflow_id not in self.workflow_states:
                    workflow_state = self.create_workflow(config)
                else:
                    workflow_state = self.workflow_states[workflow_id]
                
                # Mark as running
                self.running_workflows.add(workflow_id)
                workflow_state.status = WorkflowStatus.RUNNING
                workflow_state.start_time = datetime.now()
                
                self.logger.info(f"Starting workflow: {workflow_id}")
                self._notify_status_change(workflow_id, WorkflowStatus.RUNNING)
                
                # Determine processors to run
                processors_to_run = config.processors_to_run
                if not processors_to_run:
                    processors_to_run = self.dependency_resolver.get_standard_execution_order()
                
                # Remove processors to skip
                processors_to_run = [p for p in processors_to_run if p not in config.processors_to_skip]
                
                # Resolve execution order
                execution_order = self.dependency_resolver.resolve_execution_order(processors_to_run)
                
                self.logger.info(f"Executing processors in order: {execution_order}")
                
                # Execute processors
                total_processors = len(execution_order)
                for i, processor_name in enumerate(execution_order):
                    # Check if workflow was cancelled
                    if workflow_id not in self.running_workflows:
                        workflow_state.status = WorkflowStatus.CANCELLED
                        self._notify_status_change(workflow_id, WorkflowStatus.CANCELLED)
                        break
                    
                    # Skip if processor already completed (for resumable workflows)
                    if processor_name in workflow_state.completed_processors:
                        self.logger.info(f"Skipping completed processor: {processor_name}")
                        continue
                    
                    # Update progress
                    progress = (i / total_processors) * 100
                    message = f"Running {processor_name}"
                    workflow_state.update_progress(progress, message)
                    self._notify_progress_update(workflow_id, progress, message)
                    
                    # Execute processor
                    result = await self._execute_processor(
                        processor_name, config, workflow_state
                    )
                    
                    # Update workflow state based on result
                    if result.success:
                        workflow_state.mark_processor_completed(processor_name, result)
                        
                        # Check if we need to run fallback processors after XML downloader
                        if processor_name == "xml_downloader":
                            fallback_results = await self._check_and_run_fallback_processors(workflow_id, workflow_state)
                            for fallback_name, fallback_result in fallback_results.items():
                                if fallback_result.success:
                                    self.logger.info(f"Fallback processor {fallback_name} completed successfully")
                                else:
                                    workflow_state.mark_processor_failed(fallback_name, fallback_result)
                                    self.logger.warning(f"Fallback processor {fallback_name} failed")
                    else:
                        workflow_state.mark_processor_failed(processor_name, result)
                        
                        # Decide whether to continue or stop
                        if not config.continue_on_error:
                            workflow_state.status = WorkflowStatus.FAILED
                            workflow_state.add_error(f"Critical processor failed: {processor_name}")
                            break
                
                # Determine final status
                if workflow_state.status == WorkflowStatus.RUNNING:
                    if workflow_state.failed_processors and not config.continue_on_error:
                        workflow_state.status = WorkflowStatus.FAILED
                    else:
                        workflow_state.status = WorkflowStatus.COMPLETED
                
                # Set end time and final progress
                workflow_state.end_time = datetime.now()
                workflow_state.update_progress(100.0, "Workflow completed")
                
                self.logger.info(f"Workflow {workflow_id} finished with status: {workflow_state.status}")
                self._notify_status_change(workflow_id, workflow_state.status)
                
                return workflow_state
                
            except Exception as e:
                self.logger.error(f"Workflow {workflow_id} failed with error: {e}", exc_info=True)
                
                # Update workflow state
                if workflow_id in self.workflow_states:
                    workflow_state = self.workflow_states[workflow_id]
                    workflow_state.status = WorkflowStatus.FAILED
                    workflow_state.end_time = datetime.now()
                    workflow_state.add_error(f"Workflow execution error: {str(e)}")
                    self._notify_status_change(workflow_id, WorkflowStatus.FAILED)
                    return workflow_state
                
                raise
                
            finally:
                # Clean up
                self.running_workflows.discard(workflow_id)
    
    async def _execute_processor(
        self, 
        processor_name: str, 
        workflow_config: WorkflowConfig,
        workflow_state: WorkflowState
    ) -> ProcessorResult:
        """
        Execute a single processor.
        
        Args:
            processor_name: Name of processor to execute
            workflow_config: Workflow configuration
            workflow_state: Current workflow state
            
        Returns:
            ProcessorResult
        """
        # Use global processor registry instead of local one
        processor = self.get_processor(processor_name)
        if not processor:
            error_msg = f"Processor not found: {processor_name}"
            self.logger.error(error_msg)
            return ProcessorResult(
                success=False,
                processor_name=processor_name,
                errors=[error_msg]
            )
        
        # Mark processor as started
        workflow_state.mark_processor_started(processor_name)
        
        # Create processor configuration
        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name=processor_name,
            workflow_config=workflow_config
        )
        
        # Set up progress callback
        def progress_callback(current: int, total: int, message: str = ""):
            base_progress = (len(workflow_state.completed_processors) / 
                           len(workflow_config.processors_to_run or 
                               self.dependency_resolver.get_standard_execution_order())) * 100
            processor_progress = (current / total) * (100 / len(workflow_config.processors_to_run or 
                                                     self.dependency_resolver.get_standard_execution_order()))
            total_progress = base_progress + processor_progress
            
            full_message = f"{processor_name}: {message}" if message else processor_name
            workflow_state.update_progress(total_progress, full_message)
            self._notify_progress_update(workflow_config.workflow_id, total_progress, full_message)
        
        processor.set_progress_callback(progress_callback)
        
        # Execute processor
        self.logger.info(f"Executing processor: {processor_name}")
        result = await processor.run(processor_config, workflow_state)
        
        return result
    
    async def _check_and_run_fallback_processors(self, workflow_id: str, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Check if fallback processors (PDF/OCR) need to run and execute them."""
        fallback_results = {}
        
        # Check if XML downloader succeeded but some orgs don't have XML files
        if 'xml_downloader' not in workflow_state.processor_results:
            return fallback_results
        
        xml_results = workflow_state.processor_results['xml_downloader']
        if not xml_results.success:
            return fallback_results
        
        # Check download stats to see if any downloads failed
        xml_data = xml_results.data
        download_stats = xml_data.get('download_stats', {})
        failed_downloads = download_stats.get('failed_downloads', 0)
        
        if failed_downloads > 0:
            self.logger.info(f"Running fallback processors for {failed_downloads} organizations without XML")
            
            # Run PDF downloader as fallback
            if 'pdf_downloader' in self.registry.list_processors():
                pdf_processor = self.registry.get_processor('pdf_downloader')
                if pdf_processor:
                    config = ProcessorConfig(
                        workflow_id=workflow_id,
                        processor_name='pdf_downloader'
                    )
                    pdf_result = await pdf_processor.run(config, workflow_state)
                    fallback_results['pdf_downloader'] = pdf_result
                    workflow_state.mark_processor_completed('pdf_downloader', pdf_result)
                    
                    # If PDF download successful, run OCR
                    if pdf_result.success and 'pdf_ocr' in self.registry.list_processors():
                        ocr_processor = self.registry.get_processor('pdf_ocr')
                        if ocr_processor:
                            ocr_config = ProcessorConfig(
                                workflow_id=workflow_id,
                                processor_name='pdf_ocr'
                            )
                            ocr_result = await ocr_processor.run(ocr_config, workflow_state)
                            fallback_results['pdf_ocr'] = ocr_result
                            workflow_state.mark_processor_completed('pdf_ocr', ocr_result)
        
        return fallback_results
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Workflow ID to cancel
            
        Returns:
            True if workflow was cancelled, False if not found or not running
        """
        if workflow_id not in self.running_workflows:
            return False
        
        self.running_workflows.remove(workflow_id)
        
        if workflow_id in self.workflow_states:
            workflow_state = self.workflow_states[workflow_id]
            workflow_state.status = WorkflowStatus.CANCELLED
            workflow_state.end_time = datetime.now()
            workflow_state.add_error("Workflow cancelled by user")
            self._notify_status_change(workflow_id, WorkflowStatus.CANCELLED)
        
        self.logger.info(f"Cancelled workflow: {workflow_id}")
        return True
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pause a running workflow.
        
        Args:
            workflow_id: Workflow ID to pause
            
        Returns:
            True if workflow was paused, False if not found or not running
        """
        if workflow_id not in self.running_workflows:
            return False
        
        if workflow_id in self.workflow_states:
            workflow_state = self.workflow_states[workflow_id]
            workflow_state.status = WorkflowStatus.PAUSED
            self._notify_status_change(workflow_id, WorkflowStatus.PAUSED)
        
        self.logger.info(f"Paused workflow: {workflow_id}")
        return True
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a paused workflow.
        
        Args:
            workflow_id: Workflow ID to resume
            
        Returns:
            True if workflow was resumed, False if not found or not paused
        """
        if workflow_id not in self.workflow_states:
            return False
        
        workflow_state = self.workflow_states[workflow_id]
        if workflow_state.status != WorkflowStatus.PAUSED:
            return False
        
        self.running_workflows.add(workflow_id)
        workflow_state.status = WorkflowStatus.RUNNING
        self._notify_status_change(workflow_id, WorkflowStatus.RUNNING)
        
        self.logger.info(f"Resumed workflow: {workflow_id}")
        return True
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all workflows.
        
        Returns:
            Dictionary with workflow statistics
        """
        total_workflows = len(self.workflow_states)
        status_counts = {}
        
        for status in WorkflowStatus:
            count = len([w for w in self.workflow_states.values() if w.status == status])
            status_counts[status.value] = count
        
        active_workflows = len(self.running_workflows)
        
        # Calculate average execution time for completed workflows
        completed_workflows = [w for w in self.workflow_states.values() 
                             if w.status == WorkflowStatus.COMPLETED and w.get_execution_time()]
        avg_execution_time = None
        if completed_workflows:
            avg_execution_time = sum(w.get_execution_time() for w in completed_workflows) / len(completed_workflows)
        
        return {
            "total_workflows": total_workflows,
            "status_counts": status_counts,
            "active_workflows": active_workflows,
            "available_processors": len(self.registry.list_processors()),
            "average_execution_time": avg_execution_time
        }


# Global workflow engine instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
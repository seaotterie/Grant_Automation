"""
Base Processor Framework
Abstract base class and common functionality for all workflow processors.
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from .data_models import ProcessorConfig, ProcessorResult, WorkflowState
from ..utils.decorators import retry_on_failure, log_execution_time
from ..utils.validators import validate_ein


@dataclass
class ProcessorMetadata:
    """Metadata about a processor's capabilities and requirements."""
    name: str
    description: str
    version: str
    dependencies: List[str]  # List of required processor names
    estimated_duration: int  # Estimated seconds for execution
    requires_network: bool = False
    requires_api_key: bool = False
    can_run_parallel: bool = True
    processor_type: str = "generic"  # lookup, filter, analysis, export, etc.


class BaseProcessor(ABC):
    """
    Abstract base class for all workflow processors.
    
    Provides common functionality:
    - Logging and error handling
    - Input validation
    - Progress tracking
    - Cleanup operations
    - Standardized result format
    - Async execution support
    """
    
    def __init__(self, metadata: ProcessorMetadata):
        self.metadata = metadata
        self.logger = logging.getLogger(f"processors.{metadata.name}")
        self._start_time: Optional[datetime] = None
        self._progress_callback: Optional[Callable] = None
        self._is_cancelled = False
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set callback function for progress updates."""
        self._progress_callback = callback
    
    def _update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress if callback is set."""
        if self._progress_callback and not self._is_cancelled:
            try:
                self._progress_callback(current, total, message)
            except Exception as e:
                self.logger.warning(f"Progress callback error: {e}")
    
    def cancel(self) -> None:
        """Cancel the processor execution."""
        self._is_cancelled = True
        self.logger.info(f"Processor {self.metadata.name} cancellation requested")
    
    def is_cancelled(self) -> bool:
        """Check if processor execution has been cancelled."""
        return self._is_cancelled
    
    @abstractmethod
    async def execute(self, config: ProcessorConfig) -> ProcessorResult:
        """
        Execute the main processing logic.
        
        Args:
            config: Configuration object with all necessary parameters
            
        Returns:
            ProcessorResult with success/failure status and any output data
        """
        pass
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """
        Validate inputs before execution.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Common validations
        if hasattr(config.workflow_config, 'target_ein') and config.workflow_config.target_ein:
            if not validate_ein(config.workflow_config.target_ein):
                errors.append(f"Invalid EIN format: {config.workflow_config.target_ein}")
        
        # Processor-specific validation (override in subclasses)
        processor_errors = self.validate_processor_inputs(config)
        errors.extend(processor_errors)
        
        return errors
    
    def validate_processor_inputs(self, config: ProcessorConfig) -> List[str]:
        """
        Validate processor-specific inputs.
        Override in subclasses for custom validation.
        
        Returns:
            List of validation error messages
        """
        return []
    
    def validate_dependencies(self, workflow_state: WorkflowState) -> List[str]:
        """
        Check if all required dependencies have completed successfully.
        
        Returns:
            List of missing dependencies
        """
        missing = []
        for dep in self.metadata.dependencies:
            if dep not in workflow_state.completed_processors:
                missing.append(dep)
        return missing
    
    def check_api_requirements(self, config: ProcessorConfig) -> List[str]:
        """
        Check if required API keys are available.
        
        Returns:
            List of missing API key requirements
        """
        errors = []
        
        if self.metadata.requires_api_key:
            # Import here to avoid circular imports
            from ..auth.api_key_manager import get_api_key_manager
            
            manager = get_api_key_manager()
            
            # Check for common API keys based on processor type
            if "propublica" in self.metadata.name.lower():
                if not manager.get_api_key("propublica"):
                    errors.append("ProPublica API key required but not found")
            
            # Override in subclasses for specific API key requirements
            specific_errors = self.check_processor_api_requirements(config)
            errors.extend(specific_errors)
        
        return errors
    
    def check_processor_api_requirements(self, config: ProcessorConfig) -> List[str]:
        """
        Check processor-specific API requirements.
        Override in subclasses.
        
        Returns:
            List of missing API requirements
        """
        return []
    
    @log_execution_time
    @retry_on_failure(max_attempts=3, delay=1.0)
    async def run(self, config: ProcessorConfig, workflow_state: Optional[WorkflowState] = None) -> ProcessorResult:
        """
        Main entry point with error handling and logging.
        """
        self._start_time = datetime.now()
        self.logger.info(f"Starting {self.metadata.name} for workflow {config.workflow_id}")
        
        # Create result object
        result = ProcessorResult(
            success=False,
            processor_name=self.metadata.name,
            start_time=self._start_time
        )
        
        try:
            # Check for cancellation
            if self._is_cancelled:
                result.add_error("Processor execution was cancelled")
                return result
            
            # Pre-execution validation
            validation_errors = self.validate_inputs(config)
            if validation_errors:
                for error in validation_errors:
                    result.add_error(error)
                return result
            
            # Check dependencies
            if workflow_state:
                missing_deps = self.validate_dependencies(workflow_state)
                if missing_deps:
                    result.add_error(f"Missing dependencies: {', '.join(missing_deps)}")
                    return result
            
            # Check API requirements
            api_errors = self.check_api_requirements(config)
            if api_errors:
                for error in api_errors:
                    result.add_error(error)
                return result
            
            # Execute pre-processing setup
            await self.pre_execute(config, result)
            
            if not result.success and result.errors:
                return result
            
            # Execute main logic (with cancellation checks)
            if not self._is_cancelled:
                execution_result = await self.execute(config, workflow_state)
                
                # Store execution result for copying
                self._execution_result = execution_result
                
                # Copy execution result data
                if hasattr(self, '_execution_result'):
                    execution_result = getattr(self, '_execution_result')
                    if isinstance(execution_result, ProcessorResult):
                        result.success = execution_result.success
                        result.data = execution_result.data
                        result.errors = execution_result.errors
                        result.warnings = execution_result.warnings
                        result.metadata = execution_result.metadata
                    else:
                        result.success = True
                        result.data = execution_result if execution_result else {}
                else:
                    result.success = True
            
            # Execute post-processing cleanup
            await self.post_execute(config, result)
            
            # Set end time
            result.end_time = datetime.now()
            
            if result.start_time and result.end_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
            
            # Log completion
            duration = result.execution_time or 0
            if result.success:
                self.logger.info(f"Completed {self.metadata.name} in {duration:.2f}s")
            else:
                self.logger.error(f"Failed {self.metadata.name} after {duration:.2f}s")
            
            return result
            
        except asyncio.CancelledError:
            result.add_error("Processor execution was cancelled")
            self.logger.info(f"Cancelled {self.metadata.name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in {self.metadata.name}: {str(e)}", exc_info=True)
            result.add_error(f"Unexpected error: {str(e)}")
            return result
            
        finally:
            # Always run cleanup
            try:
                await self.cleanup(config)
            except Exception as e:
                self.logger.warning(f"Cleanup error in {self.metadata.name}: {e}")
    
    async def pre_execute(self, config: ProcessorConfig, result: ProcessorResult) -> None:
        """
        Pre-execution setup. Override in subclasses if needed.
        
        Args:
            config: Processor configuration
            result: Result object to populate with any setup data or errors
        """
        pass
    
    async def post_execute(self, config: ProcessorConfig, result: ProcessorResult) -> None:
        """
        Post-execution processing. Override in subclasses if needed.
        
        Args:
            config: Processor configuration
            result: Result object with execution results
        """
        pass
    
    async def cleanup(self, config: ProcessorConfig) -> None:
        """
        Cleanup resources after execution (override if needed).
        
        Args:
            config: Processor configuration
        """
        pass
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about this processor."""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "version": self.metadata.version,
            "dependencies": self.metadata.dependencies,
            "estimated_duration": self.metadata.estimated_duration,
            "requires_network": self.metadata.requires_network,
            "requires_api_key": self.metadata.requires_api_key,
            "can_run_parallel": self.metadata.can_run_parallel,
            "processor_type": self.metadata.processor_type
        }


class SyncProcessorMixin:
    """
    Mixin for processors that need to run synchronous code.
    Provides helper methods for running sync code in async context.
    """
    
    async def run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """Run a synchronous function in a thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


class BatchProcessorMixin:
    """
    Mixin for processors that process data in batches.
    Provides common batch processing functionality.
    """
    
    async def process_in_batches(
        self, 
        items: List[Any], 
        batch_processor: Callable,
        batch_size: int = 10,
        max_concurrent: int = 3
    ) -> List[Any]:
        """
        Process items in batches with concurrency control.
        
        Args:
            items: List of items to process
            batch_processor: Async function to process each batch
            batch_size: Number of items per batch
            max_concurrent: Maximum concurrent batches
            
        Returns:
            List of processed results
        """
        # Split into batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_batch_with_semaphore(batch):
            async with semaphore:
                if self._is_cancelled:
                    return []
                return await batch_processor(batch)
        
        # Process all batches concurrently
        results = await asyncio.gather(
            *[process_batch_with_semaphore(batch) for batch in batches],
            return_exceptions=True
        )
        
        # Flatten results and handle exceptions
        flattened_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Batch processing error: {result}")
                continue
            if isinstance(result, list):
                flattened_results.extend(result)
            else:
                flattened_results.append(result)
        
        return flattened_results


class DataValidationMixin:
    """
    Mixin for processors that need data validation.
    Provides common validation utilities.
    """
    
    def validate_organization_data(self, org_data: Dict[str, Any]) -> List[str]:
        """Validate organization data structure."""
        errors = []
        
        required_fields = ['ein', 'name']
        for field in required_fields:
            if field not in org_data or not org_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate EIN format
        if 'ein' in org_data and org_data['ein']:
            if not validate_ein(org_data['ein']):
                errors.append(f"Invalid EIN format: {org_data['ein']}")
        
        return errors
    
    def clean_financial_data(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize financial data."""
        cleaned = {}
        
        financial_fields = ['revenue', 'assets', 'expenses', 'net_assets', 'program_expenses']
        for field in financial_fields:
            if field in financial_data:
                value = financial_data[field]
                if value is not None:
                    try:
                        # Convert to float and handle negative values
                        cleaned_value = float(value)
                        # Some financial data might be reported as negative, convert to positive
                        if cleaned_value < 0 and field in ['revenue', 'assets', 'expenses']:
                            cleaned_value = abs(cleaned_value)
                        cleaned[field] = cleaned_value
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid financial data for {field}: {value}")
        
        return cleaned
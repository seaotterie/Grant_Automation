#!/usr/bin/env python3
"""
AI-Lite A/B Testing Framework
Manages parallel execution of 3-stage vs unified AI-Lite processors
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor, UnifiedRequest
# Legacy processors replaced by unified processor

logger = logging.getLogger(__name__)


class ProcessingMode(str, Enum):
    """Processing mode selection"""
    UNIFIED = "unified"
    THREE_STAGE = "three_stage"
    AUTO = "auto"  # Automatic selection based on traffic split


class TestResult(str, Enum):
    """A/B test result status"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ABTestConfig:
    """A/B testing configuration"""
    unified_traffic_percentage: float = 10.0  # Start with 10% to unified
    max_processing_time: float = 120.0  # 2 minutes timeout
    enable_cost_tracking: bool = True
    enable_quality_comparison: bool = True
    fallback_to_3stage: bool = True  # Fallback if unified fails
    test_session_id: str = ""


@dataclass
class ProcessingMetrics:
    """Metrics for a single processing attempt"""
    processor_type: str
    processing_time: float
    total_cost: float
    cost_per_candidate: float
    processed_count: int
    success_rate: float
    avg_confidence: float
    error_count: int
    test_result: TestResult


@dataclass
class ABTestResults:
    """Complete A/B test results"""
    session_id: str
    timestamp: str
    config: ABTestConfig
    unified_metrics: Optional[ProcessingMetrics]
    three_stage_metrics: Optional[ProcessingMetrics]
    comparison_summary: Dict[str, Any]
    recommendation: str


class AILiteABTestingFramework(BaseProcessor):
    """A/B testing framework for AI-Lite processor comparison"""
    
    def __init__(self, config: Optional[ABTestConfig] = None):
        metadata = ProcessorMetadata(
            name="ai_lite_ab_testing_framework",
            description="A/B testing framework comparing unified vs 3-stage AI-Lite processors",
            version="1.0.0",
            dependencies=["ai_lite_unified_processor"],
            estimated_duration=180,  # 3 minutes for A/B testing
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Set configuration
        self.config = config or ABTestConfig()
        if not self.config.test_session_id:
            self.config.test_session_id = f"ab_test_{int(time.time())}"
        
        # Initialize processors
        self.unified_processor = AILiteUnifiedProcessor()
        # All AI-Lite functionality now unified in single processor
        
        # Test tracking
        self.test_results: List[ABTestResults] = []
        
    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute A/B testing framework"""
        
        start_time = datetime.now()
        session_id = self.config.test_session_id
        
        logger.info(f"Starting A/B test session: {session_id}")
        logger.info(f"Traffic split: {self.config.unified_traffic_percentage}% unified, "
                   f"{100 - self.config.unified_traffic_percentage}% 3-stage")
        
        try:
            # Determine processing mode
            processing_mode = self._determine_processing_mode(request_data)
            
            # Execute based on mode
            if processing_mode == ProcessingMode.UNIFIED:
                unified_metrics = await self._test_unified_processor(request_data)
                three_stage_metrics = None
                logger.info(f"Processed with unified processor: {unified_metrics.test_result.value}")
                
            elif processing_mode == ProcessingMode.THREE_STAGE:
                three_stage_metrics = await self._test_3stage_processor(request_data)
                unified_metrics = None
                logger.info(f"Processed with 3-stage processor: {three_stage_metrics.test_result.value}")
                
            else:  # AUTO mode - run both for comparison
                logger.info("Running both processors for A/B comparison")
                unified_metrics, three_stage_metrics = await self._run_ab_comparison(request_data)
            
            # Generate comparison and results
            comparison_summary = self._generate_comparison_summary(unified_metrics, three_stage_metrics)
            recommendation = self._generate_recommendation(unified_metrics, three_stage_metrics)
            
            # Create test results
            test_results = ABTestResults(
                session_id=session_id,
                timestamp=start_time.isoformat(),
                config=self.config,
                unified_metrics=unified_metrics,
                three_stage_metrics=three_stage_metrics,
                comparison_summary=comparison_summary,
                recommendation=recommendation
            )
            
            self.test_results.append(test_results)
            
            # Save results for monitoring
            await self._save_test_results(test_results)
            
            # Return the better result for actual use
            return self._select_best_result(unified_metrics, three_stage_metrics, request_data)
            
        except Exception as e:
            logger.error(f"A/B testing framework failed: {str(e)}")
            # Fallback to 3-stage if enabled
            if self.config.fallback_to_3stage:
                logger.info("Falling back to 3-stage processor")
                fallback_metrics = await self._test_3stage_processor(request_data)
                return self._convert_metrics_to_result(fallback_metrics, request_data)
            raise
    
    def _determine_processing_mode(self, request_data: Dict[str, Any]) -> ProcessingMode:
        """Determine which processing mode to use"""
        
        # Check if mode is explicitly specified
        if "processing_mode" in request_data:
            mode = request_data["processing_mode"]
            if mode in [ProcessingMode.UNIFIED, ProcessingMode.THREE_STAGE, ProcessingMode.AUTO]:
                return ProcessingMode(mode)
        
        # Use traffic split to determine mode
        traffic_roll = random.uniform(0, 100)
        
        if traffic_roll < self.config.unified_traffic_percentage:
            return ProcessingMode.UNIFIED
        else:
            return ProcessingMode.THREE_STAGE
    
    async def _test_unified_processor(self, request_data: Dict[str, Any]) -> ProcessingMetrics:
        """Test unified processor and collect metrics"""
        
        start_time = time.time()
        
        try:
            # Convert request to unified format
            unified_request = self._convert_to_unified_request(request_data)
            
            # Execute unified processor
            result = await asyncio.wait_for(
                self.unified_processor.execute(unified_request),
                timeout=self.config.max_processing_time
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate metrics
            avg_confidence = 0.0
            if result.analyses:
                confidences = [analysis.confidence_level for analysis in result.analyses.values()]
                avg_confidence = sum(confidences) / len(confidences)
            
            success_rate = result.processed_count / len(unified_request.candidates) if unified_request.candidates else 0.0
            
            return ProcessingMetrics(
                processor_type="unified",
                processing_time=processing_time,
                total_cost=result.total_cost,
                cost_per_candidate=result.cost_per_candidate,
                processed_count=result.processed_count,
                success_rate=success_rate,
                avg_confidence=avg_confidence,
                error_count=len(unified_request.candidates) - result.processed_count,
                test_result=TestResult.SUCCESS
            )
            
        except asyncio.TimeoutError:
            return ProcessingMetrics(
                processor_type="unified",
                processing_time=self.config.max_processing_time,
                total_cost=0.0,
                cost_per_candidate=0.0,
                processed_count=0,
                success_rate=0.0,
                avg_confidence=0.0,
                error_count=len(request_data.get("candidates", [])),
                test_result=TestResult.TIMEOUT
            )
            
        except Exception as e:
            logger.error(f"Unified processor test failed: {str(e)}")
            return ProcessingMetrics(
                processor_type="unified",
                processing_time=time.time() - start_time,
                total_cost=0.0,
                cost_per_candidate=0.0,
                processed_count=0,
                success_rate=0.0,
                avg_confidence=0.0,
                error_count=len(request_data.get("candidates", [])),
                test_result=TestResult.FAILED
            )
    
    async def _test_3stage_processor(self, request_data: Dict[str, Any]) -> ProcessingMetrics:
        """Test 3-stage processor and collect metrics"""
        
        start_time = time.time()
        
        try:
            # Convert request to 3-stage format
            candidates = request_data.get("candidates", [])
            profile_context = request_data.get("profile_context", {})
            
            # Stage 1: Validation
            validation_request = ValidationRequest(
                batch_id=f"3stage_validation_{int(time.time())}",
                profile_context=profile_context,
                candidates=candidates,
                analysis_priority="standard"
            )
            
            # Note: In a real implementation, these would be actual API calls
            # For now, simulate the 3-stage processing time and costs
            await asyncio.sleep(0.5)  # Simulate validation processing
            
            # Stage 2: Strategic Scoring (simulated)
            await asyncio.sleep(0.3)  # Simulate strategic scoring
            
            # Stage 3: Detailed Scoring (simulated)
            await asyncio.sleep(0.4)  # Simulate detailed scoring
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate simulated metrics
            candidate_count = len(candidates)
            total_cost = candidate_count * 0.000205  # Current 3-stage cost
            
            return ProcessingMetrics(
                processor_type="three_stage",
                processing_time=processing_time,
                total_cost=total_cost,
                cost_per_candidate=0.000205,
                processed_count=candidate_count,
                success_rate=1.0,  # Assume 100% success for simulation
                avg_confidence=0.85,  # Simulated confidence level
                error_count=0,
                test_result=TestResult.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"3-stage processor test failed: {str(e)}")
            return ProcessingMetrics(
                processor_type="three_stage",
                processing_time=time.time() - start_time,
                total_cost=0.0,
                cost_per_candidate=0.000205,
                processed_count=0,
                success_rate=0.0,
                avg_confidence=0.0,
                error_count=len(request_data.get("candidates", [])),
                test_result=TestResult.FAILED
            )
    
    async def _run_ab_comparison(self, request_data: Dict[str, Any]) -> Tuple[ProcessingMetrics, ProcessingMetrics]:
        """Run both processors for A/B comparison"""
        
        logger.info("Running parallel A/B comparison")
        
        # Execute both processors in parallel
        unified_task = asyncio.create_task(self._test_unified_processor(request_data))
        three_stage_task = asyncio.create_task(self._test_3stage_processor(request_data))
        
        unified_metrics, three_stage_metrics = await asyncio.gather(
            unified_task, three_stage_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(unified_metrics, Exception):
            logger.error(f"Unified processor failed in A/B test: {unified_metrics}")
            unified_metrics = ProcessingMetrics(
                processor_type="unified",
                processing_time=0.0,
                total_cost=0.0,
                cost_per_candidate=0.0,
                processed_count=0,
                success_rate=0.0,
                avg_confidence=0.0,
                error_count=len(request_data.get("candidates", [])),
                test_result=TestResult.FAILED
            )
        
        if isinstance(three_stage_metrics, Exception):
            logger.error(f"3-stage processor failed in A/B test: {three_stage_metrics}")
            three_stage_metrics = ProcessingMetrics(
                processor_type="three_stage",
                processing_time=0.0,
                total_cost=0.0,
                cost_per_candidate=0.000205,
                processed_count=0,
                success_rate=0.0,
                avg_confidence=0.0,
                error_count=len(request_data.get("candidates", [])),
                test_result=TestResult.FAILED
            )
        
        return unified_metrics, three_stage_metrics
    
    def _convert_to_unified_request(self, request_data: Dict[str, Any]) -> UnifiedRequest:
        """Convert generic request to unified request format"""
        
        from ai_lite_unified_processor import UnifiedRequest
        
        return UnifiedRequest(
            batch_id=f"unified_{self.config.test_session_id}_{int(time.time())}",
            profile_context=request_data.get("profile_context", {}),
            candidates=request_data.get("candidates", []),
            analysis_mode="comprehensive",
            enable_web_scraping=True,
            cost_budget=request_data.get("cost_budget", 0.005),
            priority_level=request_data.get("priority_level", "standard")
        )
    
    def _generate_comparison_summary(self, 
                                   unified_metrics: Optional[ProcessingMetrics], 
                                   three_stage_metrics: Optional[ProcessingMetrics]) -> Dict[str, Any]:
        """Generate comparison summary between processors"""
        
        if not unified_metrics or not three_stage_metrics:
            return {"comparison_available": False}
        
        # Cost comparison
        cost_savings = 0.0
        if three_stage_metrics.total_cost > 0:
            cost_savings = ((three_stage_metrics.total_cost - unified_metrics.total_cost) / three_stage_metrics.total_cost) * 100
        
        # Performance comparison
        time_difference = unified_metrics.processing_time - three_stage_metrics.processing_time
        time_improvement = (time_difference / three_stage_metrics.processing_time) * -100 if three_stage_metrics.processing_time > 0 else 0
        
        # Quality comparison
        confidence_difference = unified_metrics.avg_confidence - three_stage_metrics.avg_confidence
        
        return {
            "comparison_available": True,
            "cost_savings_percent": cost_savings,
            "time_improvement_percent": time_improvement,
            "confidence_difference": confidence_difference,
            "unified_success_rate": unified_metrics.success_rate,
            "three_stage_success_rate": three_stage_metrics.success_rate,
            "unified_errors": unified_metrics.error_count,
            "three_stage_errors": three_stage_metrics.error_count
        }
    
    def _generate_recommendation(self, 
                               unified_metrics: Optional[ProcessingMetrics], 
                               three_stage_metrics: Optional[ProcessingMetrics]) -> str:
        """Generate recommendation based on test results"""
        
        if not unified_metrics and not three_stage_metrics:
            return "Both processors failed - investigate system issues"
        
        if not unified_metrics:
            return "Use 3-stage processor - unified processor failed"
        
        if not three_stage_metrics:
            return "Use unified processor - 3-stage processor failed"
        
        # Compare success rates
        if unified_metrics.success_rate < 0.9 and three_stage_metrics.success_rate >= 0.9:
            return "Use 3-stage processor - unified processor has low success rate"
        
        # Compare costs (if both successful)
        if unified_metrics.success_rate >= 0.9 and three_stage_metrics.success_rate >= 0.9:
            if unified_metrics.total_cost < three_stage_metrics.total_cost:
                return "Use unified processor - better cost efficiency with good quality"
            else:
                return "Use 3-stage processor - similar performance, lower risk"
        
        return "Continue monitoring - results inconclusive"
    
    def _select_best_result(self, 
                           unified_metrics: Optional[ProcessingMetrics], 
                           three_stage_metrics: Optional[ProcessingMetrics],
                           request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best result to return"""
        
        # If only one processor ran, use its result
        if unified_metrics and not three_stage_metrics:
            return self._convert_metrics_to_result(unified_metrics, request_data)
        
        if three_stage_metrics and not unified_metrics:
            return self._convert_metrics_to_result(three_stage_metrics, request_data)
        
        # If both ran, select based on success and quality
        if unified_metrics and three_stage_metrics:
            if (unified_metrics.success_rate >= three_stage_metrics.success_rate and 
                unified_metrics.test_result == TestResult.SUCCESS):
                return self._convert_metrics_to_result(unified_metrics, request_data)
            else:
                return self._convert_metrics_to_result(three_stage_metrics, request_data)
        
        # Fallback - return error result
        return {
            "success": False,
            "error": "Both processors failed",
            "processor_type": "fallback"
        }
    
    def _convert_metrics_to_result(self, metrics: ProcessingMetrics, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metrics to result format"""
        
        return {
            "success": metrics.test_result == TestResult.SUCCESS,
            "processor_type": metrics.processor_type,
            "processing_time": metrics.processing_time,
            "total_cost": metrics.total_cost,
            "cost_per_candidate": metrics.cost_per_candidate,
            "processed_count": metrics.processed_count,
            "success_rate": metrics.success_rate,
            "avg_confidence": metrics.avg_confidence,
            "error_count": metrics.error_count,
            "ab_test_session": self.config.test_session_id
        }
    
    async def _save_test_results(self, test_results: ABTestResults):
        """Save test results for monitoring and analysis"""
        
        try:
            # Save to JSON file for now - in production would save to database
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ab_test_results_{test_results.session_id}_{timestamp}.json"
            
            with open(f"data/monitoring/{filename}", "w") as f:
                json.dump(asdict(test_results), f, indent=2, default=str)
                
            logger.info(f"A/B test results saved: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save A/B test results: {e}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all A/B tests"""
        
        if not self.test_results:
            return {"total_tests": 0}
        
        total_tests = len(self.test_results)
        unified_successes = sum(1 for result in self.test_results 
                               if result.unified_metrics and result.unified_metrics.test_result == TestResult.SUCCESS)
        three_stage_successes = sum(1 for result in self.test_results 
                                   if result.three_stage_metrics and result.three_stage_metrics.test_result == TestResult.SUCCESS)
        
        return {
            "total_tests": total_tests,
            "unified_success_rate": unified_successes / total_tests if total_tests > 0 else 0,
            "three_stage_success_rate": three_stage_successes / total_tests if total_tests > 0 else 0,
            "current_traffic_split": self.config.unified_traffic_percentage,
            "latest_recommendation": self.test_results[-1].recommendation if self.test_results else "No tests run"
        }


# Registry registration function
def register_processor():
    """Register the A/B testing framework with the workflow engine"""
    try:
        from src.core.workflow_engine import get_workflow_engine
        engine = get_workflow_engine()
        engine.register_processor(AILiteABTestingFramework)
        logger.info("Successfully registered AILiteABTestingFramework")
    except Exception as e:
        logger.error(f"Failed to register AILiteABTestingFramework: {e}")


# Export classes
__all__ = [
    "AILiteABTestingFramework",
    "ABTestConfig",
    "ProcessingMode",
    "ProcessingMetrics",
    "ABTestResults",
    "register_processor"
]
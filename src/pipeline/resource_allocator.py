"""
Intelligent Resource Allocator
Manages processing resources across multiple pipelines and priorities
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .pipeline_engine import ProcessingPriority, PipelineConfig


class ResourceType(str, Enum):
    """Types of processing resources"""
    CPU_INTENSIVE = "cpu_intensive"
    IO_BOUND = "io_bound" 
    MEMORY_INTENSIVE = "memory_intensive"
    API_CALLS = "api_calls"


@dataclass
class ResourceQuota:
    """Resource allocation quotas"""
    max_concurrent_pipelines: int = 3
    max_concurrent_operations_per_pipeline: int = 5
    max_api_calls_per_minute: int = 100
    max_memory_mb: int = 1024
    
    # Priority-based allocation
    priority_weights: Dict[ProcessingPriority, float] = None
    
    def __post_init__(self):
        if self.priority_weights is None:
            self.priority_weights = {
                ProcessingPriority.LOW: 0.5,
                ProcessingPriority.STANDARD: 1.0, 
                ProcessingPriority.HIGH: 2.0,
                ProcessingPriority.URGENT: 4.0
            }


@dataclass
class ResourceUsage:
    """Current resource usage tracking"""
    active_pipelines: int = 0
    active_operations: int = 0
    api_calls_last_minute: int = 0
    memory_usage_mb: int = 0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class IntelligentResourceAllocator:
    """Manages resource allocation across multiple processing pipelines"""
    
    def __init__(self, quota: Optional[ResourceQuota] = None):
        self.quota = quota or ResourceQuota()
        self.current_usage = ResourceUsage()
        
        # Pipeline queue management
        self.pipeline_queue: List[Dict[str, Any]] = []
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.resource_locks: Dict[ResourceType, asyncio.Semaphore] = {}
        
        # API rate limiting
        self.api_call_timestamps: List[datetime] = []
        
        self._initialize_resource_locks()
    
    def _initialize_resource_locks(self):
        """Initialize semaphores for resource management"""
        self.resource_locks[ResourceType.CPU_INTENSIVE] = asyncio.Semaphore(self.quota.max_concurrent_pipelines)
        self.resource_locks[ResourceType.IO_BOUND] = asyncio.Semaphore(self.quota.max_concurrent_operations_per_pipeline * self.quota.max_concurrent_pipelines)
        self.resource_locks[ResourceType.API_CALLS] = asyncio.Semaphore(self.quota.max_api_calls_per_minute)
    
    async def request_pipeline_resources(
        self,
        pipeline_id: str,
        config: PipelineConfig,
        estimated_duration_minutes: int = 10
    ) -> bool:
        """Request resources for pipeline execution"""
        
        # Check if resources are available
        if not await self._check_resource_availability(config, estimated_duration_minutes):
            # Queue the pipeline if resources not available
            await self._queue_pipeline(pipeline_id, config, estimated_duration_minutes)
            return False
        
        # Allocate resources
        await self._allocate_pipeline_resources(pipeline_id, config)
        return True
    
    async def _check_resource_availability(
        self,
        config: PipelineConfig,
        estimated_duration: int
    ) -> bool:
        """Check if resources are available for pipeline"""
        
        # Update current usage
        await self._update_resource_usage()
        
        # Check concurrent pipeline limit
        if self.current_usage.active_pipelines >= self.quota.max_concurrent_pipelines:
            return False
        
        # Check API rate limits
        if await self._would_exceed_api_limits(config):
            return False
        
        # Check priority-based allocation
        available_priority_weight = self._calculate_available_priority_weight()
        required_weight = self.quota.priority_weights[config.priority]
        
        return available_priority_weight >= required_weight
    
    async def _queue_pipeline(
        self,
        pipeline_id: str,
        config: PipelineConfig,
        estimated_duration: int
    ):
        """Add pipeline to processing queue"""
        
        queue_item = {
            "pipeline_id": pipeline_id,
            "config": config,
            "estimated_duration": estimated_duration,
            "queued_at": datetime.now(),
            "priority_weight": self.quota.priority_weights[config.priority]
        }
        
        # Insert in priority order
        self.pipeline_queue.append(queue_item)
        self.pipeline_queue.sort(key=lambda x: x["priority_weight"], reverse=True)
    
    async def _allocate_pipeline_resources(self, pipeline_id: str, config: PipelineConfig):
        """Allocate resources for pipeline execution"""
        
        allocation = {
            "pipeline_id": pipeline_id,
            "config": config,
            "allocated_at": datetime.now(),
            "concurrent_operations": min(
                config.max_concurrent_operations,
                self.quota.max_concurrent_operations_per_pipeline
            ),
            "api_quota": self._calculate_api_quota(config.priority),
            "memory_quota": self._calculate_memory_quota(config.priority)
        }
        
        self.active_pipelines[pipeline_id] = allocation
        self.current_usage.active_pipelines += 1
    
    def _calculate_api_quota(self, priority: ProcessingPriority) -> int:
        """Calculate API call quota based on priority"""
        base_quota = self.quota.max_api_calls_per_minute // self.quota.max_concurrent_pipelines
        priority_multiplier = self.quota.priority_weights[priority]
        return int(base_quota * priority_multiplier)
    
    def _calculate_memory_quota(self, priority: ProcessingPriority) -> int:
        """Calculate memory quota based on priority"""
        base_quota = self.quota.max_memory_mb // self.quota.max_concurrent_pipelines
        priority_multiplier = self.quota.priority_weights[priority]
        return int(base_quota * priority_multiplier)
    
    async def _would_exceed_api_limits(self, config: PipelineConfig) -> bool:
        """Check if pipeline would exceed API rate limits"""
        
        # Clean old API call timestamps
        cutoff_time = datetime.now() - timedelta(minutes=1)
        self.api_call_timestamps = [
            ts for ts in self.api_call_timestamps if ts > cutoff_time
        ]
        
        # Estimate API calls for this pipeline
        estimated_calls = self._estimate_pipeline_api_calls(config)
        
        return len(self.api_call_timestamps) + estimated_calls > self.quota.max_api_calls_per_minute
    
    def _estimate_pipeline_api_calls(self, config: PipelineConfig) -> int:
        """Estimate API calls required for pipeline"""
        
        # Discovery stage: calls per funding type
        discovery_calls = len(config.funding_types) * 20  # Estimated
        
        # Deep analysis stage: calls for detailed analysis
        deep_analysis_calls = min(config.deep_analysis_limit, 50) * 2  # Estimated
        
        return discovery_calls + deep_analysis_calls
    
    def _calculate_available_priority_weight(self) -> float:
        """Calculate available priority weight capacity"""
        
        total_used_weight = sum(
            self.quota.priority_weights[pipeline["config"].priority]
            for pipeline in self.active_pipelines.values()
        )
        
        max_total_weight = sum(self.quota.priority_weights.values())
        return max_total_weight - total_used_weight
    
    async def release_pipeline_resources(self, pipeline_id: str):
        """Release resources after pipeline completion"""
        
        if pipeline_id in self.active_pipelines:
            del self.active_pipelines[pipeline_id]
            self.current_usage.active_pipelines -= 1
            
            # Process queued pipelines
            await self._process_pipeline_queue()
    
    async def _process_pipeline_queue(self):
        """Process queued pipelines when resources become available"""
        
        while self.pipeline_queue and self.current_usage.active_pipelines < self.quota.max_concurrent_pipelines:
            # Get highest priority queued pipeline
            next_pipeline = self.pipeline_queue[0]
            
            # Check if resources are now available
            if await self._check_resource_availability(
                next_pipeline["config"], 
                next_pipeline["estimated_duration"]
            ):
                # Remove from queue and allocate resources
                self.pipeline_queue.pop(0)
                await self._allocate_pipeline_resources(
                    next_pipeline["pipeline_id"],
                    next_pipeline["config"]
                )
                
                # TODO: Trigger pipeline execution
                # This would integrate with the pipeline engine
                
            else:
                break  # No resources available, wait for next release
    
    async def _update_resource_usage(self):
        """Update current resource usage metrics"""
        
        self.current_usage.last_updated = datetime.now()
        
        # Clean up completed pipelines
        current_time = datetime.now()
        expired_pipelines = [
            pid for pid, allocation in self.active_pipelines.items()
            if (current_time - allocation["allocated_at"]).total_seconds() > 3600  # 1 hour timeout
        ]
        
        for pipeline_id in expired_pipelines:
            await self.release_pipeline_resources(pipeline_id)
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource allocation status"""
        
        return {
            "quota": {
                "max_concurrent_pipelines": self.quota.max_concurrent_pipelines,
                "max_concurrent_operations": self.quota.max_concurrent_operations_per_pipeline,
                "max_api_calls_per_minute": self.quota.max_api_calls_per_minute,
                "max_memory_mb": self.quota.max_memory_mb
            },
            "current_usage": {
                "active_pipelines": self.current_usage.active_pipelines,
                "api_calls_last_minute": len(self.api_call_timestamps),
                "memory_usage_estimate": sum(
                    self._calculate_memory_quota(p["config"].priority)
                    for p in self.active_pipelines.values()
                ),
                "last_updated": self.current_usage.last_updated.isoformat()
            },
            "queue_status": {
                "queued_pipelines": len(self.pipeline_queue),
                "queue_by_priority": self._analyze_queue_by_priority(),
                "estimated_wait_time_minutes": self._estimate_queue_wait_time()
            },
            "active_pipelines": [
                {
                    "pipeline_id": pid,
                    "priority": allocation["config"].priority.value,
                    "allocated_at": allocation["allocated_at"].isoformat(),
                    "api_quota": allocation["api_quota"],
                    "memory_quota": allocation["memory_quota"]
                }
                for pid, allocation in self.active_pipelines.items()
            ]
        }
    
    def _analyze_queue_by_priority(self) -> Dict[str, int]:
        """Analyze queue composition by priority"""
        
        priority_counts = {}
        for item in self.pipeline_queue:
            priority = item["config"].priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return priority_counts
    
    def _estimate_queue_wait_time(self) -> int:
        """Estimate wait time for queued pipelines"""
        
        if not self.pipeline_queue:
            return 0
        
        # Simple estimation based on current pipeline load
        avg_pipeline_duration = 15  # minutes
        pipelines_ahead = len(self.pipeline_queue)
        available_slots = max(1, self.quota.max_concurrent_pipelines - self.current_usage.active_pipelines)
        
        return int((pipelines_ahead * avg_pipeline_duration) / available_slots)
    
    async def record_api_call(self):
        """Record an API call for rate limiting"""
        self.api_call_timestamps.append(datetime.now())
    
    def optimize_resource_allocation(self) -> Dict[str, Any]:
        """Analyze and suggest resource allocation optimizations"""
        
        recommendations = []
        
        # Analyze queue length
        if len(self.pipeline_queue) > 5:
            recommendations.append("Consider increasing max_concurrent_pipelines to reduce queue wait times")
        
        # Analyze API usage
        recent_api_calls = len([
            ts for ts in self.api_call_timestamps
            if (datetime.now() - ts).total_seconds() < 300  # Last 5 minutes
        ])
        
        if recent_api_calls > self.quota.max_api_calls_per_minute * 0.8:
            recommendations.append("API usage approaching limits. Consider implementing more aggressive caching")
        
        # Priority distribution analysis
        priority_distribution = self._analyze_queue_by_priority()
        if priority_distribution.get("urgent", 0) > 3:
            recommendations.append("High number of urgent pipelines. Consider dedicated urgent processing capacity")
        
        return {
            "current_efficiency": self._calculate_resource_efficiency(),
            "recommendations": recommendations,
            "optimization_score": self._calculate_optimization_score()
        }
    
    def _calculate_resource_efficiency(self) -> float:
        """Calculate current resource utilization efficiency"""
        
        pipeline_utilization = self.current_usage.active_pipelines / self.quota.max_concurrent_pipelines
        api_utilization = len(self.api_call_timestamps) / self.quota.max_api_calls_per_minute
        
        return (pipeline_utilization + api_utilization) / 2
    
    def _calculate_optimization_score(self) -> float:
        """Calculate optimization score (0-1, higher is better)"""
        
        # Base score from efficiency
        efficiency = self._calculate_resource_efficiency()
        
        # Penalty for long queues
        queue_penalty = min(0.3, len(self.pipeline_queue) * 0.05)
        
        # Bonus for balanced priority distribution
        priority_balance_bonus = 0.1 if len(set(
            item["config"].priority for item in self.pipeline_queue
        )) <= 2 else 0
        
        return max(0, min(1, efficiency - queue_penalty + priority_balance_bonus))


# Global resource allocator instance
resource_allocator = IntelligentResourceAllocator()
"""
Intelligence Router
API endpoints for tiered grant intelligence analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import uuid
import time
import logging
from datetime import datetime

from src.intelligence.standard_tier_processor import StandardTierProcessor, StandardTierResult

logger = logging.getLogger(__name__)

# Request/Response Models
class ServiceTier(str, Enum):
    CURRENT = "current"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    COMPLETE = "complete"

class AddOnModule(str, Enum):
    BOARD_NETWORK = "board_network_analysis"
    DECISION_MAKER = "decision_maker_intelligence"
    RFP_ANALYSIS = "complete_rfp_analysis"
    HISTORICAL_PATTERNS = "historical_success_patterns"
    WARM_INTRODUCTIONS = "warm_introduction_pathways"
    COMPETITIVE_ANALYSIS = "competitive_deep_dive"

class IntelligenceRequest(BaseModel):
    opportunity_id: str = Field(..., description="Grant opportunity ID")
    tier: ServiceTier = Field(..., description="Intelligence analysis tier")
    add_ons: Optional[List[AddOnModule]] = Field(default=[], description="Additional analysis modules")
    custom_priorities: Optional[Dict[str, Any]] = Field(default=None, description="Custom analysis priorities")

class CostEstimateRequest(BaseModel):
    tier: ServiceTier = Field(..., description="Analysis tier")
    add_ons: Optional[List[AddOnModule]] = Field(default=[], description="Additional modules")
    opportunity_type: Optional[str] = Field(default=None, description="Opportunity type (government, foundation, corporate)")
    opportunity_size: Optional[str] = Field(default=None, description="Opportunity size (small, medium, large)")

class CostBreakdown(BaseModel):
    api_tokens: float = Field(..., description="API token costs")
    infrastructure: float = Field(..., description="Infrastructure processing costs")
    platform_margin: float = Field(..., description="Platform margin")
    total: float = Field(..., description="Total cost")

class ValueComparison(BaseModel):
    consultant_equivalent_hours: float = Field(..., description="Equivalent consultant hours")
    consultant_cost_range: Dict[str, float] = Field(..., description="Consultant cost range (min/max)")
    savings_range: Dict[str, float] = Field(..., description="Savings range (min/max)")
    roi_multiplier: float = Field(..., description="ROI multiplier vs consultant")

class CostEstimateResponse(BaseModel):
    tier: ServiceTier
    add_ons: List[AddOnModule]
    cost_breakdown: CostBreakdown
    estimated_delivery_time: str
    poc_effort_required: str
    value_comparison: ValueComparison

class IntelligenceResponse(BaseModel):
    task_id: Optional[str] = Field(default=None, description="Background task ID for async processing")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Analysis result for immediate processing")
    estimated_cost: float = Field(..., description="Estimated processing cost")
    actual_cost: Optional[float] = Field(default=None, description="Actual processing cost")
    estimated_completion_time: str = Field(..., description="Estimated completion time")
    status: str = Field(..., description="Processing status")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress_percentage: int
    estimated_completion: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_cost: Optional[float] = None

# Cost Calculator
class TierCostCalculator:
    """Calculate costs for different intelligence tiers"""
    
    def __init__(self):
        self.base_costs = {
            ServiceTier.CURRENT: 0.75,
            ServiceTier.STANDARD: 7.50,
            ServiceTier.ENHANCED: 22.00,
            ServiceTier.COMPLETE: 42.00
        }
        
        self.addon_costs = {
            AddOnModule.BOARD_NETWORK: 6.50,
            AddOnModule.DECISION_MAKER: 9.50,
            AddOnModule.RFP_ANALYSIS: 15.50,
            AddOnModule.HISTORICAL_PATTERNS: 8.50,
            AddOnModule.WARM_INTRODUCTIONS: 8.50,
            AddOnModule.COMPETITIVE_ANALYSIS: 12.50
        }
        
        self.delivery_times = {
            ServiceTier.CURRENT: "5-10 minutes",
            ServiceTier.STANDARD: "15-20 minutes",
            ServiceTier.ENHANCED: "30-45 minutes",
            ServiceTier.COMPLETE: "60-90 minutes"
        }
        
        self.poc_efforts = {
            ServiceTier.CURRENT: "0 hours",
            ServiceTier.STANDARD: "0 hours",
            ServiceTier.ENHANCED: "0-1 hours",
            ServiceTier.COMPLETE: "2-4 hours"
        }
    
    def calculate_cost(self, tier: ServiceTier, add_ons: List[AddOnModule]) -> float:
        """Calculate total cost for tier and add-ons"""
        base_cost = self.base_costs.get(tier, 0)
        addon_cost = sum(self.addon_costs.get(addon, 0) for addon in add_ons)
        return base_cost + addon_cost
    
    def get_cost_breakdown(self, tier: ServiceTier, add_ons: List[AddOnModule]) -> CostBreakdown:
        """Get detailed cost breakdown"""
        base_cost = self.base_costs.get(tier, 0)
        addon_cost = sum(self.addon_costs.get(addon, 0) for addon in add_ons)
        total_cost = base_cost + addon_cost
        
        # Estimate breakdown (simplified for MVP)
        api_tokens = total_cost * 0.15  # ~15% API costs
        platform_margin = total_cost * 0.20  # ~20% margin
        infrastructure = total_cost - api_tokens - platform_margin
        
        return CostBreakdown(
            api_tokens=api_tokens,
            infrastructure=infrastructure,
            platform_margin=platform_margin,
            total=total_cost
        )
    
    def get_value_comparison(self, tier: ServiceTier, add_ons: List[AddOnModule]) -> ValueComparison:
        """Calculate value comparison vs consultant"""
        total_cost = self.calculate_cost(tier, add_ons)
        
        # Estimate consultant equivalent based on tier complexity
        base_hours = {
            ServiceTier.CURRENT: 2,
            ServiceTier.STANDARD: 4,
            ServiceTier.ENHANCED: 8,
            ServiceTier.COMPLETE: 16
        }
        
        addon_hours = len(add_ons) * 2  # 2 hours per add-on module
        total_hours = base_hours.get(tier, 2) + addon_hours
        
        consultant_min = total_hours * 50  # $50/hour junior
        consultant_max = total_hours * 100  # $100/hour senior
        
        return ValueComparison(
            consultant_equivalent_hours=total_hours,
            consultant_cost_range={"min": consultant_min, "max": consultant_max},
            savings_range={"min": consultant_min - total_cost, "max": consultant_max - total_cost},
            roi_multiplier=consultant_min / total_cost if total_cost > 0 else 0
        )

# Task Manager for Background Processing
class TaskManager:
    """Simple in-memory task management for MVP"""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_id: str, tier: ServiceTier, profile_id: str, opportunity_id: str) -> str:
        """Create a new background task"""
        self.tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "created_at": datetime.now(),
            "tier": tier,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "result": None,
            "error": None,
            "cost": None
        }
        return task_id
    
    def update_task_progress(self, task_id: str, progress: int, status: str = None):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            if status:
                self.tasks[task_id]["status"] = status
    
    def complete_task(self, task_id: str, result: Any, cost: float):
        """Mark task as complete"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "result": result,
                "cost": cost,
                "completed_at": datetime.now()
            })
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "failed",
                "progress": 0,
                "error": error,
                "failed_at": datetime.now()
            })
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        return self.tasks.get(task_id)

# Global instances
cost_calculator = TierCostCalculator()
task_manager = TaskManager()
standard_tier_processor = StandardTierProcessor()

# Router
router = APIRouter(prefix="/api/intelligence", tags=["Intelligence Analysis"])

@router.post("/profiles/{profile_id}/analysis", response_model=IntelligenceResponse)
async def generate_intelligence_analysis(
    profile_id: str,
    request: IntelligenceRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate tiered intelligence analysis for a grant opportunity
    """
    try:
        # Calculate estimated cost
        estimated_cost = cost_calculator.calculate_cost(request.tier, request.add_ons)
        
        # For Standard tier, process immediately (for MVP)
        if request.tier == ServiceTier.STANDARD:
            start_time = time.time()
            
            # Process with Standard tier processor
            result = await standard_tier_processor.process_opportunity(
                profile_id=profile_id,
                opportunity_id=request.opportunity_id
            )
            
            processing_time = time.time() - start_time
            
            return IntelligenceResponse(
                result=result.to_dict(),
                estimated_cost=estimated_cost,
                actual_cost=result.total_processing_cost,
                estimated_completion_time=f"Completed in {processing_time:.2f}s",
                status="completed"
            )
        
        # For other tiers, return not implemented for MVP
        elif request.tier == ServiceTier.CURRENT:
            return IntelligenceResponse(
                result={"message": "Current tier available through existing system"},
                estimated_cost=estimated_cost,
                actual_cost=0.75,
                estimated_completion_time="5-10 minutes",
                status="available_via_existing_system"
            )
        
        else:
            # Enhanced and Complete tiers - create background task
            task_id = str(uuid.uuid4())
            task_manager.create_task(task_id, request.tier, profile_id, request.opportunity_id)
            
            # Add background processing
            background_tasks.add_task(
                process_advanced_tier, 
                task_id, 
                profile_id, 
                request.opportunity_id, 
                request.tier, 
                request.add_ons
            )
            
            return IntelligenceResponse(
                task_id=task_id,
                estimated_cost=estimated_cost,
                estimated_completion_time=cost_calculator.delivery_times[request.tier],
                status="processing"
            )
        
    except Exception as e:
        logger.error(f"Intelligence analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analysis/{task_id}", response_model=TaskStatusResponse)
async def get_analysis_status(task_id: str):
    """
    Get status of background analysis task
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress_percentage=task["progress"],
        estimated_completion=None,  # Could calculate based on start time
        result=task["result"],
        error_message=task["error"],
        processing_cost=task["cost"]
    )

@router.post("/cost-estimate", response_model=CostEstimateResponse)
async def calculate_cost_estimate(request: CostEstimateRequest):
    """
    Calculate cost estimate for tier selection
    """
    try:
        cost_breakdown = cost_calculator.get_cost_breakdown(request.tier, request.add_ons)
        value_comparison = cost_calculator.get_value_comparison(request.tier, request.add_ons)
        
        return CostEstimateResponse(
            tier=request.tier,
            add_ons=request.add_ons,
            cost_breakdown=cost_breakdown,
            estimated_delivery_time=cost_calculator.delivery_times[request.tier],
            poc_effort_required=cost_calculator.poc_efforts[request.tier],
            value_comparison=value_comparison
        )
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {str(e)}")

@router.get("/tiers")
async def get_available_tiers():
    """
    Get available intelligence tiers and their features
    """
    return {
        "tiers": [
            {
                "id": "current",
                "name": "Current Intelligence",
                "price": 0.75,
                "delivery_time": "5-10 minutes",
                "poc_effort": "0 hours",
                "features": [
                    "4-Stage AI Analysis (PLAN, ANALYZE, EXAMINE, APPROACH)",
                    "Multi-dimensional scoring and risk assessment",
                    "Success probability modeling (75-80% confidence)",
                    "Implementation roadmap with resource allocation"
                ],
                "best_for": ["Quick opportunity assessment", "Initial screening", "Budget-conscious analysis"]
            },
            {
                "id": "standard",
                "name": "Standard Intelligence",
                "price": 7.50,
                "delivery_time": "15-20 minutes", 
                "poc_effort": "0 hours",
                "features": [
                    "Everything in Current Intelligence",
                    "5-year historical funding analysis",
                    "Award pattern intelligence and success factors",
                    "Geographic distribution and competitive analysis",
                    "Temporal trends and market timing insights"
                ],
                "best_for": ["Serious opportunity pursuit", "Proposal development", "Competitive intelligence"]
            },
            {
                "id": "enhanced",
                "name": "Enhanced Intelligence",
                "price": 22.00,
                "delivery_time": "30-45 minutes",
                "poc_effort": "0-1 hours",
                "features": [
                    "Everything in Standard Intelligence",
                    "Complete RFP/NOFO analysis and requirements extraction",
                    "Board network intelligence and relationship mapping",
                    "Decision maker profiles and engagement strategies",
                    "Strategic partnership opportunity identification"
                ],
                "best_for": ["High-value opportunities", "Strategic partnerships", "Relationship-driven funding"],
                "status": "coming_soon"
            },
            {
                "id": "complete",
                "name": "Complete Intelligence",
                "price": 42.00,
                "delivery_time": "60-90 minutes",
                "poc_effort": "2-4 hours",
                "features": [
                    "Everything in Enhanced Intelligence",
                    "Masters thesis-level comprehensive analysis",
                    "Advanced network mapping and warm introduction pathways",
                    "Policy context analysis and regulatory insights",
                    "Real-time monitoring and premium documentation"
                ],
                "best_for": ["Major institutional opportunities", "Multi-million dollar programs", "Complex partnerships"],
                "status": "coming_soon"
            }
        ],
        "add_ons": [
            {"id": "board_network_analysis", "name": "Board Network Analysis", "price": 6.50},
            {"id": "decision_maker_intelligence", "name": "Decision Maker Intelligence", "price": 9.50},
            {"id": "complete_rfp_analysis", "name": "Complete RFP Analysis", "price": 15.50},
            {"id": "historical_success_patterns", "name": "Historical Success Patterns", "price": 8.50},
            {"id": "warm_introduction_pathways", "name": "Warm Introduction Pathways", "price": 8.50},
            {"id": "competitive_deep_dive", "name": "Competitive Deep Dive", "price": 12.50}
        ]
    }

# Background task processor
async def process_advanced_tier(
    task_id: str, 
    profile_id: str, 
    opportunity_id: str, 
    tier: ServiceTier, 
    add_ons: List[AddOnModule]
):
    """
    Background processor for Enhanced and Complete tiers
    """
    try:
        task_manager.update_task_progress(task_id, 10, "processing")
        
        # Simulate processing for MVP
        await asyncio.sleep(2)
        task_manager.update_task_progress(task_id, 50)
        
        await asyncio.sleep(2)
        task_manager.update_task_progress(task_id, 80)
        
        # Simulate completion
        result = {
            "tier": tier.value,
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "add_ons": [addon.value for addon in add_ons],
            "message": f"{tier.value.title()} tier processing completed",
            "status": "coming_soon_in_next_release"
        }
        
        cost = cost_calculator.calculate_cost(tier, add_ons)
        task_manager.complete_task(task_id, result, cost)
        
    except Exception as e:
        logger.error(f"Background processing failed for task {task_id}: {e}")
        task_manager.fail_task(task_id, str(e))

# Health check
@router.get("/health")
async def intelligence_health_check():
    """
    Health check for intelligence services
    """
    return {
        "status": "healthy",
        "services": {
            "standard_tier_processor": "available",
            "historical_funding_analyzer": "available", 
            "cost_calculator": "available",
            "task_manager": "available"
        },
        "timestamp": datetime.now().isoformat()
    }
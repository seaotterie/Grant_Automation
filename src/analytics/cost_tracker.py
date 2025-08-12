#!/usr/bin/env python3
"""
AI Cost Tracking and Optimization System
Monitors expensive AI operations, prevents redundant processing, and manages cost budgets
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from decimal import Decimal, ROUND_HALF_UP

from src.core.processing_state import ProcessingStep, get_processing_state_manager
from src.core.cache_manager import CacheType, get_cache_manager

logger = logging.getLogger(__name__)


class AIService(str, Enum):
    """AI service providers"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT3_5 = "openai_gpt3_5" 
    ANTHROPIC_CLAUDE = "anthropic_claude"
    GOOGLE_GEMINI = "google_gemini"
    LOCAL_LLM = "local_llm"


class CostCategory(str, Enum):
    """Cost categories for tracking"""
    AI_ANALYSIS = "ai_analysis"
    AI_CLASSIFICATION = "ai_classification"
    AI_SCORING = "ai_scoring"
    AI_CONTENT_GENERATION = "ai_content_generation"
    API_CALLS = "api_calls"
    DATA_PROCESSING = "data_processing"


@dataclass
class CostEstimate:
    """Cost estimation for AI operations"""
    service: AIService
    operation_type: CostCategory
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['estimated_cost_usd'] = str(self.estimated_cost_usd)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostEstimate':
        """Create from dictionary"""
        data = data.copy()
        data['estimated_cost_usd'] = Decimal(data['estimated_cost_usd'])
        data['service'] = AIService(data['service'])
        data['operation_type'] = CostCategory(data['operation_type'])
        return cls(**data)


@dataclass
class CostRecord:
    """Record of actual AI operation cost"""
    record_id: str
    profile_id: Optional[str]
    opportunity_id: Optional[str]
    service: AIService
    operation_type: CostCategory
    processing_step: Optional[ProcessingStep]
    
    # Usage metrics
    input_tokens: int
    output_tokens: int
    processing_time_seconds: float
    
    # Cost information  
    actual_cost_usd: Decimal
    estimated_cost_usd: Optional[Decimal]
    cost_variance: Optional[Decimal]  # actual - estimated
    
    # Metadata
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_variance(self) -> Optional[Decimal]:
        """Calculate cost variance if estimate available"""
        if self.estimated_cost_usd:
            variance = self.actual_cost_usd - self.estimated_cost_usd
            self.cost_variance = variance
            return variance
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert Decimal to string for JSON
        data['actual_cost_usd'] = str(self.actual_cost_usd)
        if self.estimated_cost_usd:
            data['estimated_cost_usd'] = str(self.estimated_cost_usd)
        if self.cost_variance:
            data['cost_variance'] = str(self.cost_variance)
        # Convert datetime to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        # Convert enums to string
        data['service'] = self.service.value
        data['operation_type'] = self.operation_type.value
        if self.processing_step:
            data['processing_step'] = self.processing_step.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostRecord':
        """Create from dictionary"""
        data = data.copy()
        # Convert strings back to Decimal
        data['actual_cost_usd'] = Decimal(data['actual_cost_usd'])
        if data.get('estimated_cost_usd'):
            data['estimated_cost_usd'] = Decimal(data['estimated_cost_usd'])
        if data.get('cost_variance'):
            data['cost_variance'] = Decimal(data['cost_variance'])
        # Convert ISO format back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Convert strings back to enums
        data['service'] = AIService(data['service'])
        data['operation_type'] = CostCategory(data['operation_type'])
        if data.get('processing_step'):
            data['processing_step'] = ProcessingStep(data['processing_step'])
        return cls(**data)


@dataclass
class CostBudget:
    """Budget configuration and tracking"""
    budget_id: str
    name: str
    total_budget_usd: Decimal
    spent_usd: Decimal = Decimal('0.00')
    period_start: datetime = field(default_factory=datetime.now)
    period_end: Optional[datetime] = None
    
    # Budget allocation by category
    category_budgets: Dict[CostCategory, Decimal] = field(default_factory=dict)
    category_spent: Dict[CostCategory, Decimal] = field(default_factory=dict)
    
    # Alert thresholds (percentage of budget)
    warning_threshold: float = 0.75  # 75%
    critical_threshold: float = 0.90  # 90%
    
    def remaining_budget(self) -> Decimal:
        """Get remaining budget"""
        return self.total_budget_usd - self.spent_usd
    
    def budget_utilization(self) -> float:
        """Get budget utilization percentage"""
        if self.total_budget_usd == 0:
            return 0.0
        return float(self.spent_usd / self.total_budget_usd)
    
    def is_over_threshold(self, threshold: float) -> bool:
        """Check if spending is over threshold"""
        return self.budget_utilization() >= threshold
    
    def can_spend(self, amount: Decimal) -> bool:
        """Check if amount can be spent within budget"""
        return self.spent_usd + amount <= self.total_budget_usd
    
    def add_cost(self, cost: CostRecord) -> None:
        """Add cost to budget tracking"""
        self.spent_usd += cost.actual_cost_usd
        
        # Update category spending
        category = cost.operation_type
        if category not in self.category_spent:
            self.category_spent[category] = Decimal('0.00')
        self.category_spent[category] += cost.actual_cost_usd
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert Decimal to string
        data['total_budget_usd'] = str(self.total_budget_usd)
        data['spent_usd'] = str(self.spent_usd)
        # Convert datetime to ISO format
        data['period_start'] = self.period_start.isoformat()
        if self.period_end:
            data['period_end'] = self.period_end.isoformat()
        # Convert category mappings
        data['category_budgets'] = {k.value: str(v) for k, v in self.category_budgets.items()}
        data['category_spent'] = {k.value: str(v) for k, v in self.category_spent.items()}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostBudget':
        """Create from dictionary"""
        data = data.copy()
        # Convert strings back to Decimal
        data['total_budget_usd'] = Decimal(data['total_budget_usd'])
        data['spent_usd'] = Decimal(data['spent_usd'])
        # Convert ISO format back to datetime
        data['period_start'] = datetime.fromisoformat(data['period_start'])
        if data.get('period_end'):
            data['period_end'] = datetime.fromisoformat(data['period_end'])
        # Convert category mappings back
        data['category_budgets'] = {CostCategory(k): Decimal(v) for k, v in data.get('category_budgets', {}).items()}
        data['category_spent'] = {CostCategory(k): Decimal(v) for k, v in data.get('category_spent', {}).items()}
        return cls(**data)


class CostTracker:
    """Main cost tracking and optimization system"""
    
    # Cost per token for different services (in USD)
    TOKEN_COSTS = {
        AIService.OPENAI_GPT4: {
            'input': Decimal('0.00003'),   # $0.03 per 1K tokens
            'output': Decimal('0.00006')   # $0.06 per 1K tokens
        },
        AIService.OPENAI_GPT3_5: {
            'input': Decimal('0.0000015'), # $0.0015 per 1K tokens
            'output': Decimal('0.000002')  # $0.002 per 1K tokens
        },
        AIService.ANTHROPIC_CLAUDE: {
            'input': Decimal('0.000008'),  # $0.008 per 1K tokens
            'output': Decimal('0.000024') # $0.024 per 1K tokens
        },
        AIService.GOOGLE_GEMINI: {
            'input': Decimal('0.00000125'), # $0.00125 per 1K tokens
            'output': Decimal('0.00000375') # $0.00375 per 1K tokens
        },
        AIService.LOCAL_LLM: {
            'input': Decimal('0.0'),      # Free for local
            'output': Decimal('0.0')      # Free for local
        }
    }
    
    def __init__(self, cost_dir: Optional[Path] = None):
        self.cost_dir = cost_dir or Path("data/cost_tracking")
        self.records_file = self.cost_dir / "cost_records.json"
        self.budgets_file = self.cost_dir / "budgets.json"
        
        self.cost_records: List[CostRecord] = []
        self.budgets: Dict[str, CostBudget] = {}
        self.lock = asyncio.Lock()
        
        # Ensure directory exists
        self.cost_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load cost records and budgets from disk"""
        try:
            # Load cost records
            if self.records_file.exists():
                with open(self.records_file, 'r') as f:
                    records_data = json.load(f)
                    self.cost_records = [CostRecord.from_dict(data) for data in records_data]
                logger.info(f"Loaded {len(self.cost_records)} cost records")
            
            # Load budgets
            if self.budgets_file.exists():
                with open(self.budgets_file, 'r') as f:
                    budgets_data = json.load(f)
                    self.budgets = {
                        budget_id: CostBudget.from_dict(data)
                        for budget_id, data in budgets_data.items()
                    }
                logger.info(f"Loaded {len(self.budgets)} budgets")
                
        except Exception as e:
            logger.error(f"Failed to load cost tracking data: {e}")
            self.cost_records = []
            self.budgets = {}
    
    async def _save_data(self) -> None:
        """Save cost records and budgets to disk"""
        try:
            # Save cost records
            records_data = [record.to_dict() for record in self.cost_records]
            with open(self.records_file, 'w') as f:
                json.dump(records_data, f, indent=2)
            
            # Save budgets
            budgets_data = {
                budget_id: budget.to_dict() 
                for budget_id, budget in self.budgets.items()
            }
            with open(self.budgets_file, 'w') as f:
                json.dump(budgets_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cost tracking data: {e}")
    
    def estimate_cost(self, 
                     service: AIService, 
                     operation_type: CostCategory,
                     input_tokens: int, 
                     output_tokens: int) -> CostEstimate:
        """Estimate cost for AI operation"""
        costs = self.TOKEN_COSTS.get(service)
        if not costs:
            logger.warning(f"No cost data for service {service}")
            return CostEstimate(
                service=service,
                operation_type=operation_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=Decimal('0.00'),
                confidence=0.0
            )
        
        # Calculate cost based on tokens
        input_cost = costs['input'] * Decimal(input_tokens)
        output_cost = costs['output'] * Decimal(output_tokens)
        total_cost = input_cost + output_cost
        
        # Round to 4 decimal places
        total_cost = total_cost.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        return CostEstimate(
            service=service,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=total_cost,
            confidence=0.95  # High confidence for token-based pricing
        )
    
    async def should_run_ai_operation(self,
                                    opportunity_id: str,
                                    processing_step: ProcessingStep,
                                    estimated_cost: CostEstimate,
                                    force_refresh: bool = False) -> tuple[bool, str]:
        """Determine if AI operation should be run based on cost and cache"""
        
        # Check processing state first
        state_manager = get_processing_state_manager()
        should_run_step = await state_manager.should_run_step(
            opportunity_id, processing_step, force_refresh
        )
        
        if not should_run_step:
            return False, "Step already completed or in progress"
        
        # Check if we have cached results
        cache_manager = get_cache_manager()
        cached_result = await cache_manager.get(
            identifier=opportunity_id,
            cache_type=CacheType.AI_ANALYSIS
        )
        
        if cached_result and not force_refresh:
            return False, "Cached AI analysis available"
        
        # Check budget constraints
        async with self.lock:
            for budget in self.budgets.values():
                if not budget.can_spend(estimated_cost.estimated_cost_usd):
                    return False, f"Would exceed budget {budget.name}"
                
                if budget.is_over_threshold(budget.critical_threshold):
                    return False, f"Budget {budget.name} over critical threshold"
        
        return True, "OK to proceed"
    
    async def record_ai_operation(self,
                                profile_id: Optional[str],
                                opportunity_id: Optional[str],
                                service: AIService,
                                operation_type: CostCategory,
                                processing_step: Optional[ProcessingStep],
                                input_tokens: int,
                                output_tokens: int,
                                processing_time_seconds: float,
                                actual_cost_usd: Decimal,
                                success: bool,
                                estimated_cost: Optional[CostEstimate] = None,
                                error_message: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> CostRecord:
        """Record actual AI operation cost"""
        
        record = CostRecord(
            record_id=f"{datetime.now().isoformat()}_{opportunity_id or 'unknown'}",
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            service=service,
            operation_type=operation_type,
            processing_step=processing_step,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time_seconds=processing_time_seconds,
            actual_cost_usd=actual_cost_usd,
            estimated_cost_usd=estimated_cost.estimated_cost_usd if estimated_cost else None,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        # Calculate cost variance
        record.calculate_variance()
        
        async with self.lock:
            # Add to records
            self.cost_records.append(record)
            
            # Update budgets
            for budget in self.budgets.values():
                budget.add_cost(record)
            
            # Save data
            await self._save_data()
        
        # Log significant cost variances
        if record.cost_variance and abs(record.cost_variance) > Decimal('0.01'):
            logger.warning(
                f"Significant cost variance for {operation_type}: "
                f"estimated ${record.estimated_cost_usd}, actual ${record.actual_cost_usd}"
            )
        
        return record
    
    async def create_budget(self,
                          budget_id: str,
                          name: str,
                          total_budget_usd: Decimal,
                          period_days: Optional[int] = None) -> CostBudget:
        """Create new cost budget"""
        
        period_start = datetime.now()
        period_end = None
        if period_days:
            period_end = period_start + timedelta(days=period_days)
        
        budget = CostBudget(
            budget_id=budget_id,
            name=name,
            total_budget_usd=total_budget_usd,
            period_start=period_start,
            period_end=period_end
        )
        
        async with self.lock:
            self.budgets[budget_id] = budget
            await self._save_data()
        
        logger.info(f"Created budget {name} with ${total_budget_usd}")
        return budget
    
    async def get_cost_analytics(self) -> Dict[str, Any]:
        """Get comprehensive cost analytics"""
        async with self.lock:
            total_records = len(self.cost_records)
            if total_records == 0:
                return {
                    'total_records': 0,
                    'total_cost': '0.00',
                    'avg_cost_per_operation': '0.00',
                    'cost_by_service': {},
                    'cost_by_category': {},
                    'budget_status': {}
                }
            
            # Calculate totals
            total_cost = sum(record.actual_cost_usd for record in self.cost_records)
            successful_operations = sum(1 for record in self.cost_records if record.success)
            
            # Cost by service
            cost_by_service = {}
            for record in self.cost_records:
                service = record.service.value
                cost_by_service[service] = cost_by_service.get(service, Decimal('0.00')) + record.actual_cost_usd
            
            # Cost by category
            cost_by_category = {}
            for record in self.cost_records:
                category = record.operation_type.value
                cost_by_category[category] = cost_by_category.get(category, Decimal('0.00')) + record.actual_cost_usd
            
            # Budget status
            budget_status = {}
            for budget_id, budget in self.budgets.items():
                budget_status[budget_id] = {
                    'name': budget.name,
                    'total_budget': str(budget.total_budget_usd),
                    'spent': str(budget.spent_usd),
                    'remaining': str(budget.remaining_budget()),
                    'utilization_percent': round(budget.budget_utilization() * 100, 2),
                    'over_warning': budget.is_over_threshold(budget.warning_threshold),
                    'over_critical': budget.is_over_threshold(budget.critical_threshold)
                }
            
            return {
                'total_records': total_records,
                'successful_operations': successful_operations,
                'success_rate': round(successful_operations / total_records * 100, 2),
                'total_cost': str(total_cost),
                'avg_cost_per_operation': str(total_cost / total_records),
                'cost_by_service': {k: str(v) for k, v in cost_by_service.items()},
                'cost_by_category': {k: str(v) for k, v in cost_by_category.items()},
                'budget_status': budget_status
            }
    
    async def cleanup_old_records(self, max_age: timedelta = timedelta(days=90)) -> int:
        """Clean up old cost records"""
        async with self.lock:
            cutoff_date = datetime.now() - max_age
            old_count = len(self.cost_records)
            
            self.cost_records = [
                record for record in self.cost_records 
                if record.timestamp > cutoff_date
            ]
            
            removed_count = old_count - len(self.cost_records)
            
            if removed_count > 0:
                await self._save_data()
                logger.info(f"Cleaned up {removed_count} old cost records")
            
            return removed_count


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


# Convenience functions
async def estimate_ai_cost(service: AIService, 
                          operation_type: CostCategory,
                          input_tokens: int, 
                          output_tokens: int) -> CostEstimate:
    """Estimate cost for AI operation"""
    tracker = get_cost_tracker()
    return tracker.estimate_cost(service, operation_type, input_tokens, output_tokens)


async def should_run_ai_analysis(opportunity_id: str,
                               processing_step: ProcessingStep,
                               service: AIService,
                               operation_type: CostCategory,
                               input_tokens: int,
                               output_tokens: int,
                               force_refresh: bool = False) -> tuple[bool, str, CostEstimate]:
    """Check if AI analysis should be run"""
    tracker = get_cost_tracker()
    
    # Get cost estimate
    estimate = tracker.estimate_cost(service, operation_type, input_tokens, output_tokens)
    
    # Check if should run
    should_run, reason = await tracker.should_run_ai_operation(
        opportunity_id, processing_step, estimate, force_refresh
    )
    
    return should_run, reason, estimate
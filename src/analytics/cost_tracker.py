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
    """Enhanced AI service providers with model granularity"""
    # OpenAI Services - Granular Model Support
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT4_TURBO = "openai_gpt4_turbo"
    OPENAI_GPT4O = "openai_gpt4o"
    OPENAI_GPT4O_MINI = "openai_gpt4o_mini"
    OPENAI_GPT3_5_TURBO = "openai_gpt3_5_turbo"
    OPENAI_GPT3_5 = "openai_gpt3_5"  # Legacy compatibility
    
    # Anthropic Services - Claude Models
    ANTHROPIC_CLAUDE_3_OPUS = "anthropic_claude_3_opus"
    ANTHROPIC_CLAUDE_3_SONNET = "anthropic_claude_3_sonnet"
    ANTHROPIC_CLAUDE_3_HAIKU = "anthropic_claude_3_haiku"
    ANTHROPIC_CLAUDE = "anthropic_claude"  # Legacy compatibility
    
    # Google Services - Gemini Models
    GOOGLE_GEMINI_PRO = "google_gemini_pro"
    GOOGLE_GEMINI_PRO_VISION = "google_gemini_pro_vision"
    GOOGLE_GEMINI_ULTRA = "google_gemini_ultra"
    GOOGLE_GEMINI = "google_gemini"  # Legacy compatibility
    
    # Groq Services - High Speed Inference
    GROQ_LLAMA2_70B = "groq_llama2_70b_4096"
    GROQ_MIXTRAL_8X7B = "groq_mixtral_8x7b_32768"
    GROQ_GEMMA_7B = "groq_gemma_7b_it"
    
    # Local and Free Services
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
    
    # Enhanced Cost per token for different services with model granularity (in USD)
    TOKEN_COSTS = {
        # OpenAI Services - Updated with latest pricing (2024)
        AIService.OPENAI_GPT4O: {
            'input': Decimal('0.000005'),   # $0.005 per 1K tokens (latest GPT-4o)
            'output': Decimal('0.000015'),  # $0.015 per 1K tokens
            'tier': 'premium',
            'speed': 'fast',
            'quality': 'highest'
        },
        AIService.OPENAI_GPT4O_MINI: {
            'input': Decimal('0.00000015'), # $0.00015 per 1K tokens (cost-optimized)
            'output': Decimal('0.0000006'), # $0.0006 per 1K tokens  
            'tier': 'economy',
            'speed': 'very_fast',
            'quality': 'high'
        },
        AIService.OPENAI_GPT4_TURBO: {
            'input': Decimal('0.00001'),    # $0.01 per 1K tokens
            'output': Decimal('0.00003'),   # $0.03 per 1K tokens
            'tier': 'standard',
            'speed': 'fast', 
            'quality': 'highest'
        },
        AIService.OPENAI_GPT4: {
            'input': Decimal('0.00003'),    # $0.03 per 1K tokens (legacy)
            'output': Decimal('0.00006'),   # $0.06 per 1K tokens
            'tier': 'premium',
            'speed': 'medium',
            'quality': 'highest'
        },
        AIService.OPENAI_GPT3_5_TURBO: {
            'input': Decimal('0.0000015'),  # $0.0015 per 1K tokens
            'output': Decimal('0.000002'),  # $0.002 per 1K tokens
            'tier': 'economy',
            'speed': 'very_fast',
            'quality': 'good'
        },
        AIService.OPENAI_GPT3_5: {  # Legacy compatibility
            'input': Decimal('0.0000015'),
            'output': Decimal('0.000002'),
            'tier': 'economy',
            'speed': 'very_fast',
            'quality': 'good'
        },
        
        # Anthropic Services - Claude 3 Family
        AIService.ANTHROPIC_CLAUDE_3_OPUS: {
            'input': Decimal('0.000015'),   # $0.015 per 1K tokens (most capable)
            'output': Decimal('0.000075'),  # $0.075 per 1K tokens
            'tier': 'premium',
            'speed': 'medium',
            'quality': 'highest'
        },
        AIService.ANTHROPIC_CLAUDE_3_SONNET: {
            'input': Decimal('0.000003'),   # $0.003 per 1K tokens (balanced)
            'output': Decimal('0.000015'),  # $0.015 per 1K tokens
            'tier': 'standard',
            'speed': 'fast',
            'quality': 'high'
        },
        AIService.ANTHROPIC_CLAUDE_3_HAIKU: {
            'input': Decimal('0.00000025'), # $0.00025 per 1K tokens (fastest)
            'output': Decimal('0.00000125'), # $0.00125 per 1K tokens
            'tier': 'economy',
            'speed': 'very_fast',
            'quality': 'good'
        },
        AIService.ANTHROPIC_CLAUDE: {  # Legacy compatibility
            'input': Decimal('0.000008'),
            'output': Decimal('0.000024'),
            'tier': 'standard',
            'speed': 'medium',
            'quality': 'high'
        },
        
        # Google Services - Gemini Family
        AIService.GOOGLE_GEMINI_ULTRA: {
            'input': Decimal('0.0000125'),  # $0.0125 per 1K tokens (most capable)
            'output': Decimal('0.0000375'), # $0.0375 per 1K tokens
            'tier': 'premium',
            'speed': 'medium',
            'quality': 'highest'
        },
        AIService.GOOGLE_GEMINI_PRO: {
            'input': Decimal('0.00000125'), # $0.00125 per 1K tokens (balanced)
            'output': Decimal('0.00000375'), # $0.00375 per 1K tokens
            'tier': 'standard',
            'speed': 'fast',
            'quality': 'high'
        },
        AIService.GOOGLE_GEMINI_PRO_VISION: {
            'input': Decimal('0.00000125'), # $0.00125 per 1K tokens + image costs
            'output': Decimal('0.00000375'), # $0.00375 per 1K tokens
            'tier': 'standard',
            'speed': 'fast',
            'quality': 'high'
        },
        AIService.GOOGLE_GEMINI: {  # Legacy compatibility
            'input': Decimal('0.00000125'),
            'output': Decimal('0.00000375'),
            'tier': 'standard',
            'speed': 'fast',
            'quality': 'high'
        },
        
        # Groq Services - High-Speed Inference
        AIService.GROQ_LLAMA2_70B: {
            'input': Decimal('0.0000007'),  # $0.0007 per 1K tokens (very fast)
            'output': Decimal('0.0000008'), # $0.0008 per 1K tokens
            'tier': 'economy',
            'speed': 'ultra_fast',
            'quality': 'good'
        },
        AIService.GROQ_MIXTRAL_8X7B: {
            'input': Decimal('0.0000002'),  # $0.0002 per 1K tokens (ultra fast)
            'output': Decimal('0.0000002'), # $0.0002 per 1K tokens
            'tier': 'economy',
            'speed': 'ultra_fast',
            'quality': 'good'
        },
        AIService.GROQ_GEMMA_7B: {
            'input': Decimal('0.0000001'),  # $0.0001 per 1K tokens (cheapest)
            'output': Decimal('0.0000001'), # $0.0001 per 1K tokens
            'tier': 'economy',
            'speed': 'ultra_fast',
            'quality': 'fair'
        },
        
        # Local and Free Services
        AIService.LOCAL_LLM: {
            'input': Decimal('0.0'),
            'output': Decimal('0.0'),
            'tier': 'free',
            'speed': 'variable',
            'quality': 'variable'
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
    
    def compare_service_costs(self, 
                            services: List[AIService], 
                            input_tokens: int, 
                            output_tokens: int) -> Dict[str, Any]:
        """Compare costs across multiple AI services for scenario planning"""
        comparisons = {}
        
        for service in services:
            estimate = self.estimate_cost(service, CostCategory.AI_ANALYSIS, input_tokens, output_tokens)
            cost_data = self.TOKEN_COSTS.get(service, {})
            
            comparisons[service.value] = {
                'service_name': service.value.replace('_', ' ').title(),
                'estimated_cost': str(estimate.estimated_cost_usd),
                'cost_per_1k_input': str(cost_data.get('input', Decimal('0.0'))),
                'cost_per_1k_output': str(cost_data.get('output', Decimal('0.0'))),
                'tier': cost_data.get('tier', 'unknown'),
                'speed': cost_data.get('speed', 'unknown'),
                'quality': cost_data.get('quality', 'unknown'),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
        
        # Sort by cost
        sorted_services = sorted(comparisons.items(), key=lambda x: Decimal(x[1]['estimated_cost']))
        
        return {
            'comparisons': dict(sorted_services),
            'cheapest': sorted_services[0][0] if sorted_services else None,
            'most_expensive': sorted_services[-1][0] if sorted_services else None,
            'cost_range': {
                'min': sorted_services[0][1]['estimated_cost'] if sorted_services else '0.00',
                'max': sorted_services[-1][1]['estimated_cost'] if sorted_services else '0.00'
            }
        }
    
    def scenario_planner(self, 
                        candidate_count: int, 
                        avg_input_tokens: int = 1500,
                        avg_output_tokens: int = 300) -> Dict[str, Any]:
        """Generate cost scenarios for different service options"""
        
        # Define service tiers for analysis
        economy_services = [AIService.OPENAI_GPT4O_MINI, AIService.ANTHROPIC_CLAUDE_3_HAIKU, 
                           AIService.GROQ_GEMMA_7B, AIService.GOOGLE_GEMINI_PRO]
        standard_services = [AIService.OPENAI_GPT3_5_TURBO, AIService.ANTHROPIC_CLAUDE_3_SONNET, 
                            AIService.GOOGLE_GEMINI_PRO, AIService.GROQ_MIXTRAL_8X7B]
        premium_services = [AIService.OPENAI_GPT4O, AIService.OPENAI_GPT4_TURBO, 
                           AIService.ANTHROPIC_CLAUDE_3_OPUS, AIService.GOOGLE_GEMINI_ULTRA]
        
        scenarios = {}
        
        for tier, services in [('economy', economy_services), ('standard', standard_services), ('premium', premium_services)]:
            tier_costs = []
            best_service = None
            best_cost = None
            
            for service in services:
                try:
                    cost_per_candidate = self.estimate_cost(service, CostCategory.AI_ANALYSIS, 
                                                         avg_input_tokens, avg_output_tokens)
                    total_cost = cost_per_candidate.estimated_cost_usd * candidate_count
                    
                    service_info = self.TOKEN_COSTS.get(service, {})
                    tier_costs.append({
                        'service': service.value,
                        'service_name': service.value.replace('_', ' ').title(),
                        'cost_per_candidate': str(cost_per_candidate.estimated_cost_usd),
                        'total_cost': str(total_cost),
                        'speed': service_info.get('speed', 'unknown'),
                        'quality': service_info.get('quality', 'unknown')
                    })
                    
                    if best_cost is None or total_cost < best_cost:
                        best_cost = total_cost
                        best_service = service.value
                        
                except Exception as e:
                    logger.warning(f"Failed to calculate cost for {service}: {e}")
                    continue
            
            scenarios[tier] = {
                'services': tier_costs,
                'recommended_service': best_service,
                'best_total_cost': str(best_cost) if best_cost else '0.00',
                'candidate_count': candidate_count
            }
        
        # Calculate cross-tier comparisons
        all_costs = []
        for tier_data in scenarios.values():
            all_costs.extend([(s['service'], Decimal(s['total_cost'])) for s in tier_data['services']])
        
        if all_costs:
            all_costs.sort(key=lambda x: x[1])
            cheapest_overall = all_costs[0]
            most_expensive = all_costs[-1]
            
            cost_summary = {
                'total_candidates': candidate_count,
                'cheapest_option': {
                    'service': cheapest_overall[0],
                    'total_cost': str(cheapest_overall[1])
                },
                'most_expensive_option': {
                    'service': most_expensive[0], 
                    'total_cost': str(most_expensive[1])
                },
                'cost_savings': str(most_expensive[1] - cheapest_overall[1]),
                'savings_percentage': round((1 - (cheapest_overall[1] / most_expensive[1])) * 100, 1) if most_expensive[1] > 0 else 0
            }
        else:
            cost_summary = {
                'total_candidates': candidate_count,
                'error': 'No cost data available'
            }
        
        return {
            'scenarios': scenarios,
            'summary': cost_summary,
            'parameters': {
                'candidate_count': candidate_count,
                'avg_input_tokens': avg_input_tokens,
                'avg_output_tokens': avg_output_tokens
            }
        }
    
    def get_billing_export_data(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               format_type: str = 'json') -> Dict[str, Any]:
        """Export billing data in various formats for ChatGPT's billing export suggestion"""
        
        # Filter records by date range
        filtered_records = self.cost_records
        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]
        
        # Group by different dimensions
        by_model = {}
        by_task_type = {}
        by_batch_id = {}
        by_date = {}
        
        for record in filtered_records:
            # By model/service
            model = record.service.value
            if model not in by_model:
                by_model[model] = {'count': 0, 'total_cost': Decimal('0.0'), 'total_tokens': 0}
            by_model[model]['count'] += 1
            by_model[model]['total_cost'] += record.actual_cost_usd
            by_model[model]['total_tokens'] += record.input_tokens + record.output_tokens
            
            # By task type
            task = record.operation_type.value
            if task not in by_task_type:
                by_task_type[task] = {'count': 0, 'total_cost': Decimal('0.0')}
            by_task_type[task]['count'] += 1
            by_task_type[task]['total_cost'] += record.actual_cost_usd
            
            # By batch ID (from metadata)
            batch_id = record.metadata.get('batch_id', 'unknown')
            if batch_id not in by_batch_id:
                by_batch_id[batch_id] = {'count': 0, 'total_cost': Decimal('0.0')}
            by_batch_id[batch_id]['count'] += 1
            by_batch_id[batch_id]['total_cost'] += record.actual_cost_usd
            
            # By date
            date_key = record.timestamp.date().isoformat()
            if date_key not in by_date:
                by_date[date_key] = {'count': 0, 'total_cost': Decimal('0.0')}
            by_date[date_key]['count'] += 1
            by_date[date_key]['total_cost'] += record.actual_cost_usd
        
        # Convert Decimals to strings for JSON serialization
        def convert_decimals(data):
            if isinstance(data, dict):
                return {k: convert_decimals(v) for k, v in data.items()}
            elif isinstance(data, Decimal):
                return str(data)
            return data
        
        export_data = {
            'export_info': {
                'generated_at': datetime.now().isoformat(),
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                },
                'total_records': len(filtered_records),
                'format': format_type
            },
            'summary': {
                'total_cost': str(sum(r.actual_cost_usd for r in filtered_records)),
                'total_operations': len(filtered_records),
                'avg_cost_per_operation': str(sum(r.actual_cost_usd for r in filtered_records) / len(filtered_records)) if filtered_records else '0.00'
            },
            'breakdowns': {
                'by_model': convert_decimals(by_model),
                'by_task_type': convert_decimals(by_task_type), 
                'by_batch_id': convert_decimals(by_batch_id),
                'by_date': convert_decimals(by_date)
            },
            'detailed_records': [record.to_dict() for record in filtered_records] if format_type == 'detailed' else []
        }
        
        return export_data
    
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
#!/usr/bin/env python3
"""
AI Cost Tracker - Enhanced cost tracking with database integration
Connects OpenAI service with database cost tracking and monitoring
"""

import logging
from datetime import datetime, date
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .openai_service import OpenAIService, CompletionResponse, get_openai_service

# Import with proper path handling
try:
    from ..database.database_manager import DatabaseManager
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingCostRecord:
    """Record of AI processing costs for database storage"""
    opportunity_id: str
    processor_type: str
    processing_stage: str
    model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    processing_cost: float
    processing_time_seconds: float
    success: bool
    error_details: Optional[Dict] = None
    processed_at: datetime = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now()


class AICostTracker:
    """
    Enhanced AI cost tracker with database integration
    Handles cost tracking, budgeting, and usage monitoring
    """
    
    def __init__(self, database_path: Optional[str] = None, daily_budget: float = 10.0, monthly_budget: float = 300.0):
        self.db = DatabaseManager(database_path or "data/catalynx.db")
        self.openai_service = get_openai_service()
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        
        # In-memory tracking for session
        self.session_costs = []
        self.session_start = datetime.now()
        
        logger.info(f"AI Cost Tracker initialized with budgets: ${daily_budget}/day, ${monthly_budget}/month")
    
    def record_processing_result(
        self,
        opportunity_id: str,
        processor_type: str,
        processing_stage: str,
        response: CompletionResponse,
        processing_time: float,
        input_data: Dict = None,
        output_data: Dict = None,
        success: bool = True,
        error_details: Dict = None
    ) -> bool:
        """
        Record AI processing result with full cost tracking
        
        Args:
            opportunity_id: ID of the opportunity being processed
            processor_type: Type of AI processor (ai_lite_unified, ai_heavy_research, etc.)
            processing_stage: Stage of processing (plan, analyze, examine, approach)
            response: OpenAI completion response
            processing_time: Processing time in seconds
            input_data: Input data sent to AI
            output_data: Output data received from AI
            success: Whether processing succeeded
            error_details: Error information if failed
            
        Returns:
            bool: Success status of recording
        """
        try:
            # Create cost record
            cost_record = ProcessingCostRecord(
                opportunity_id=opportunity_id,
                processor_type=processor_type,
                processing_stage=processing_stage,
                model_used=response.model,
                input_tokens=response.usage.get('prompt_tokens', 0),
                output_tokens=response.usage.get('completion_tokens', 0),
                total_tokens=response.usage.get('total_tokens', 0),
                processing_cost=response.cost_estimate,
                processing_time_seconds=processing_time,
                success=success,
                error_details=error_details
            )
            
            # Record in database
            success_recorded = self.db.record_ai_processing_cost(
                opportunity_id=opportunity_id,
                processor_type=processor_type,
                processing_stage=processing_stage,
                cost=response.cost_estimate,
                processing_time=int(processing_time),
                token_usage=response.usage.get('total_tokens', 0),
                model_used=response.model,
                input_data=input_data or {},
                output_data=output_data or {},
                success=success,
                error_details=error_details
            )
            
            # Track in session
            self.session_costs.append(cost_record)
            
            if success_recorded:
                logger.info(f"Recorded AI cost: ${response.cost_estimate:.4f} for {processor_type}/{processing_stage}")
            else:
                logger.warning(f"Failed to record AI cost in database")
                
            return success_recorded
            
        except Exception as e:
            logger.error(f"Failed to record processing result: {e}")
            return False
    
    def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget usage and status"""
        try:
            # Get budget alert status from database
            alerts = self.db.check_budget_alerts()
            
            # Get recent costs
            daily_costs = self.db.get_daily_cost_summary(days=1)
            weekly_costs = self.db.get_daily_cost_summary(days=7)
            monthly_costs = self.db.get_daily_cost_summary(days=30)
            
            # Calculate totals
            today_total = daily_costs[0]['total_cost'] if daily_costs else 0.0
            week_total = sum(day['total_cost'] for day in weekly_costs)
            month_total = sum(day['total_cost'] for day in monthly_costs)
            
            # Calculate usage percentages
            daily_usage_pct = (today_total / self.daily_budget) * 100 if self.daily_budget > 0 else 0
            monthly_usage_pct = (month_total / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0
            
            # Determine status
            status = "normal"
            if daily_usage_pct >= 90 or monthly_usage_pct >= 90:
                status = "critical"
            elif daily_usage_pct >= 75 or monthly_usage_pct >= 75:
                status = "warning"
            elif daily_usage_pct >= 50 or monthly_usage_pct >= 50:
                status = "caution"
            
            return {
                'status': status,
                'daily_budget': self.daily_budget,
                'monthly_budget': self.monthly_budget,
                'today_spent': today_total,
                'week_spent': week_total,
                'month_spent': month_total,
                'daily_usage_pct': round(daily_usage_pct, 1),
                'monthly_usage_pct': round(monthly_usage_pct, 1),
                'daily_remaining': max(0, self.daily_budget - today_total),
                'monthly_remaining': max(0, self.monthly_budget - month_total),
                'alerts': alerts,
                'recommendations': self._get_budget_recommendations(daily_usage_pct, monthly_usage_pct)
            }
            
        except Exception as e:
            logger.error(f"Failed to check budget status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_budget_recommendations(self, daily_pct: float, monthly_pct: float) -> List[str]:
        """Get budget management recommendations"""
        recommendations = []
        
        if daily_pct >= 90:
            recommendations.append("CRITICAL: Daily budget nearly exhausted - consider pausing AI processing")
        elif daily_pct >= 75:
            recommendations.append("WARNING: High daily usage - prioritize only essential AI processing")
        elif daily_pct >= 50:
            recommendations.append("CAUTION: Monitor remaining daily budget carefully")
            
        if monthly_pct >= 90:
            recommendations.append("CRITICAL: Monthly budget nearly exhausted - review processing efficiency")
        elif monthly_pct >= 75:
            recommendations.append("WARNING: High monthly usage - consider optimizing AI processor usage")
        elif monthly_pct >= 50:
            recommendations.append("Monitor monthly trends and adjust daily limits if needed")
            
        if not recommendations:
            recommendations.append("Budget usage is within normal limits")
            
        return recommendations
    
    def get_cost_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed cost analytics and insights"""
        try:
            # Get cost summary from database
            daily_costs = self.db.get_daily_cost_summary(days=days)
            
            if not daily_costs:
                return {'error': 'No cost data available'}
            
            # Calculate analytics
            total_cost = sum(day['total_cost'] for day in daily_costs)
            total_calls = sum(day['api_calls_count'] for day in daily_costs)
            total_tokens = sum(day['tokens_used'] for day in daily_costs)
            
            avg_cost_per_day = total_cost / len(daily_costs) if daily_costs else 0
            avg_cost_per_call = total_cost / max(total_calls, 1)
            avg_tokens_per_call = total_tokens / max(total_calls, 1)
            
            # Get cost breakdown by processor type
            cost_breakdown = {}
            for day in daily_costs:
                for field in ['cost_ai_lite', 'cost_ai_heavy_light', 'cost_ai_heavy_deep', 'cost_ai_heavy_impl']:
                    processor_type = field.replace('cost_', '')
                    if processor_type not in cost_breakdown:
                        cost_breakdown[processor_type] = 0
                    cost_breakdown[processor_type] += day.get(field, 0)
            
            # Calculate trends
            recent_costs = [day['total_cost'] for day in daily_costs[-3:]] if len(daily_costs) >= 3 else []
            trend = 'stable'
            if len(recent_costs) >= 2:
                if recent_costs[-1] > recent_costs[-2] * 1.2:
                    trend = 'increasing'
                elif recent_costs[-1] < recent_costs[-2] * 0.8:
                    trend = 'decreasing'
            
            return {
                'period_days': days,
                'total_cost': round(total_cost, 4),
                'total_api_calls': total_calls,
                'total_tokens': total_tokens,
                'avg_cost_per_day': round(avg_cost_per_day, 4),
                'avg_cost_per_call': round(avg_cost_per_call, 4),
                'avg_tokens_per_call': round(avg_tokens_per_call, 0),
                'cost_breakdown': cost_breakdown,
                'daily_costs': daily_costs,
                'cost_trend': trend,
                'efficiency_metrics': {
                    'cost_per_thousand_tokens': round((total_cost / max(total_tokens, 1)) * 1000, 6),
                    'tokens_per_dollar': round(max(total_tokens, 1) / max(total_cost, 0.0001), 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get cost analytics: {e}")
            return {'error': str(e)}
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session costs"""
        try:
            session_duration = (datetime.now() - self.session_start).total_seconds()
            
            if not self.session_costs:
                return {
                    'session_duration_minutes': round(session_duration / 60, 1),
                    'total_cost': 0.0,
                    'total_calls': 0,
                    'total_tokens': 0,
                    'by_processor': {}
                }
            
            total_cost = sum(record.processing_cost for record in self.session_costs)
            total_tokens = sum(record.total_tokens for record in self.session_costs)
            
            # Group by processor type
            by_processor = {}
            for record in self.session_costs:
                if record.processor_type not in by_processor:
                    by_processor[record.processor_type] = {
                        'calls': 0,
                        'cost': 0.0,
                        'tokens': 0,
                        'success_rate': 0.0
                    }
                
                by_processor[record.processor_type]['calls'] += 1
                by_processor[record.processor_type]['cost'] += record.processing_cost
                by_processor[record.processor_type]['tokens'] += record.total_tokens
            
            # Calculate success rates
            for processor_type, stats in by_processor.items():
                successful = sum(1 for record in self.session_costs 
                               if record.processor_type == processor_type and record.success)
                stats['success_rate'] = (successful / stats['calls']) * 100 if stats['calls'] > 0 else 0
            
            return {
                'session_duration_minutes': round(session_duration / 60, 1),
                'total_cost': round(total_cost, 4),
                'total_calls': len(self.session_costs),
                'total_tokens': total_tokens,
                'avg_cost_per_call': round(total_cost / len(self.session_costs), 4),
                'by_processor': by_processor
            }
            
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return {'error': str(e)}
    
    def export_cost_report(self, start_date: date, end_date: date, format: str = 'json') -> Optional[str]:
        """Export detailed cost report for specified date range"""
        try:
            # Calculate days between dates
            days = (end_date - start_date).days + 1
            
            # Get cost data
            daily_costs = self.db.get_daily_cost_summary(days=days)
            analytics = self.get_cost_analytics(days=days)
            
            # Filter by date range
            filtered_costs = [
                day for day in daily_costs 
                if start_date <= date.fromisoformat(day['date']) <= end_date
            ]
            
            report = {
                'report_generated': datetime.now().isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': len(filtered_costs)
                },
                'summary': {
                    'total_cost': sum(day['total_cost'] for day in filtered_costs),
                    'total_calls': sum(day['api_calls_count'] for day in filtered_costs),
                    'total_tokens': sum(day['tokens_used'] for day in filtered_costs),
                    'average_daily_cost': analytics.get('avg_cost_per_day', 0)
                },
                'daily_breakdown': filtered_costs,
                'analytics': analytics,
                'budget_analysis': self.check_budget_status()
            }
            
            if format == 'json':
                # Save to consolidated directory
                report_path = Path("data/consolidated/cost_reports")
                report_path.mkdir(exist_ok=True)
                
                filename = f"cost_report_{start_date}_{end_date}.json"
                full_path = report_path / filename
                
                with open(full_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                logger.info(f"Cost report exported to {full_path}")
                return str(full_path)
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to export cost report: {e}")
            return None
    
    def optimize_processor_usage(self) -> Dict[str, Any]:
        """Analyze processor usage and provide optimization recommendations"""
        try:
            analytics = self.get_cost_analytics(days=30)
            
            if 'cost_breakdown' not in analytics:
                return {'error': 'Insufficient data for optimization analysis'}
            
            cost_breakdown = analytics['cost_breakdown']
            total_cost = analytics['total_cost']
            
            recommendations = []
            
            # Analyze cost distribution
            if total_cost > 0:
                for processor, cost in cost_breakdown.items():
                    percentage = (cost / total_cost) * 100
                    
                    if processor == 'ai_heavy_impl' and percentage > 40:
                        recommendations.append(f"HIGH COST: {processor} accounts for {percentage:.1f}% of costs - consider using lighter processors for initial screening")
                    elif processor == 'ai_heavy_deep' and percentage > 30:
                        recommendations.append(f"MODERATE COST: {processor} usage is {percentage:.1f}% - ensure it's used only for high-value opportunities")
                    elif processor == 'ai_lite' and percentage < 20:
                        recommendations.append(f"UNDERUTILIZED: {processor} only {percentage:.1f}% - consider using more for initial filtering")
            
            # Efficiency recommendations
            avg_cost_per_call = analytics['avg_cost_per_call']
            if avg_cost_per_call > 0.05:
                recommendations.append("High average cost per call - review processor selection strategy")
            elif avg_cost_per_call < 0.001:
                recommendations.append("Very efficient cost per call - current strategy is well-optimized")
            
            return {
                'current_efficiency': analytics['efficiency_metrics'],
                'cost_distribution': cost_breakdown,
                'recommendations': recommendations,
                'optimization_score': self._calculate_optimization_score(analytics)
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize processor usage: {e}")
            return {'error': str(e)}
    
    def _calculate_optimization_score(self, analytics: Dict) -> float:
        """Calculate optimization score based on usage patterns"""
        try:
            score = 100.0
            
            # Penalize if heavy processors are overused
            cost_breakdown = analytics.get('cost_breakdown', {})
            total_cost = analytics.get('total_cost', 0)
            
            if total_cost > 0:
                heavy_percentage = (cost_breakdown.get('ai_heavy_impl', 0) + 
                                  cost_breakdown.get('ai_heavy_deep', 0)) / total_cost * 100
                
                if heavy_percentage > 60:
                    score -= (heavy_percentage - 60) * 0.5  # Penalize excessive heavy usage
                
                # Reward good lite usage
                lite_percentage = cost_breakdown.get('ai_lite', 0) / total_cost * 100
                if 20 <= lite_percentage <= 40:
                    score += 5  # Bonus for good lite usage
            
            # Factor in cost efficiency
            cost_per_call = analytics.get('avg_cost_per_call', 0)
            if cost_per_call < 0.01:
                score += 10
            elif cost_per_call > 0.05:
                score -= 10
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Failed to calculate optimization score: {e}")
            return 50.0  # Default neutral score


# Global cost tracker instance
_cost_tracker = None


def get_cost_tracker(database_path: Optional[str] = None, daily_budget: float = 10.0, monthly_budget: float = 300.0) -> AICostTracker:
    """Get the global AI cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = AICostTracker(database_path, daily_budget, monthly_budget)
    return _cost_tracker


def configure_cost_tracker(database_path: str, daily_budget: float = 10.0, monthly_budget: float = 300.0) -> AICostTracker:
    """Configure the global AI cost tracker"""
    global _cost_tracker
    _cost_tracker = AICostTracker(database_path, daily_budget, monthly_budget)
    return _cost_tracker


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    tracker = get_cost_tracker("data/catalynx.db")
    
    # Check budget status
    budget_status = tracker.check_budget_status()
    print(f"Budget Status: {budget_status}")
    
    # Get cost analytics
    analytics = tracker.get_cost_analytics(days=7)
    print(f"Cost Analytics: {analytics}")
    
    print("AI Cost Tracker testing completed!")
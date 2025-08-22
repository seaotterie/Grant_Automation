"""
AI Lite Scorer
Simple implementation for Phase 3 testing
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AILiteScorer:
    """Simple AI Lite scorer for testing Phase 3 functionality"""
    
    def __init__(self):
        """Initialize the AI Lite scorer"""
        self.cost_per_analysis = 0.001
        self.total_analyses = 0
        
    async def score_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score an opportunity using simplified logic
        
        Args:
            opportunity_data: Opportunity data to score
            
        Returns:
            Scoring results
        """
        try:
            # Simple scoring logic for testing
            base_score = 0.65
            
            # Adjust score based on available data
            if opportunity_data.get('funding_amount'):
                base_score += 0.1
            
            if opportunity_data.get('current_stage') in ['recommendations', 'deep_analysis']:
                base_score += 0.05
            
            if opportunity_data.get('organization_name'):
                base_score += 0.05
            
            # Ensure score is within bounds
            final_score = min(max(base_score, 0.0), 1.0)
            
            self.total_analyses += 1
            
            return {
                'overall_score': final_score,
                'confidence_level': 0.75,
                'auto_promotion_eligible': final_score >= 0.7,
                'dimension_scores': {
                    'strategic_fit': final_score,
                    'financial_potential': min(final_score + 0.05, 1.0),
                    'risk_assessment': max(final_score - 0.1, 0.0)
                },
                'scored_at': datetime.now().isoformat(),
                'scorer_version': 'ai_lite_test_v1.0',
                'cost': self.cost_per_analysis
            }
            
        except Exception as e:
            logger.error(f"Error in AI Lite scoring: {e}")
            return {
                'overall_score': 0.5,
                'confidence_level': 0.3,
                'auto_promotion_eligible': False,
                'error': str(e),
                'cost': 0.0
            }
    
    async def batch_score_opportunities(self, opportunities: list) -> list:
        """
        Score multiple opportunities in batch
        
        Args:
            opportunities: List of opportunities to score
            
        Returns:
            List of scoring results
        """
        results = []
        
        for opportunity in opportunities:
            result = await self.score_opportunity(opportunity)
            results.append(result)
            
            # Small delay for cost optimization
            await asyncio.sleep(0.1)
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_analyses': self.total_analyses,
            'cost_per_analysis': self.cost_per_analysis,
            'total_cost': self.total_analyses * self.cost_per_analysis
        }
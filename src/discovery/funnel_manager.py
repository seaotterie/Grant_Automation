"""
Grant Opportunity Funnel Management
Handles stage progression, filtering, and analytics for the grant opportunity funnel
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter

from .base_discoverer import DiscoveryResult, FunnelStage
from src.profiles.models import OrganizationProfile


class FunnelManager:
    """Manages grant opportunity funnel progression and analytics"""
    
    def __init__(self):
        self.opportunities: Dict[str, List[DiscoveryResult]] = defaultdict(list)
        self.stage_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def add_opportunities(self, profile_id: str, opportunities: List[DiscoveryResult]) -> None:
        """Add opportunities to profile's funnel"""
        self.opportunities[profile_id].extend(opportunities)
        
        # Track initial stage entry
        for opp in opportunities:
            self._record_stage_transition(profile_id, opp, None, opp.funnel_stage)
    
    def get_opportunities_by_stage(
        self, 
        profile_id: str, 
        stage: FunnelStage
    ) -> List[DiscoveryResult]:
        """Get all opportunities at a specific funnel stage"""
        return [
            opp for opp in self.opportunities.get(profile_id, [])
            if opp.funnel_stage == stage
        ]
    
    def get_all_opportunities(self, profile_id: str) -> List[DiscoveryResult]:
        """Get all opportunities for a profile"""
        return self.opportunities.get(profile_id, [])
    
    def promote_opportunity(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        notes: Optional[str] = None
    ) -> bool:
        """Promote opportunity to next funnel stage"""
        opportunity = self._find_opportunity(profile_id, opportunity_id)
        if not opportunity:
            return False
        
        old_stage = opportunity.funnel_stage
        if opportunity.promote_to_next_stage(notes):
            self._record_stage_transition(profile_id, opportunity, old_stage, opportunity.funnel_stage)
            return True
        return False
    
    def demote_opportunity(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        notes: Optional[str] = None
    ) -> bool:
        """Demote opportunity to previous funnel stage"""
        opportunity = self._find_opportunity(profile_id, opportunity_id)
        if not opportunity:
            return False
        
        old_stage = opportunity.funnel_stage
        if opportunity.demote_to_previous_stage(notes):
            self._record_stage_transition(profile_id, opportunity, old_stage, opportunity.funnel_stage)
            return True
        return False
    
    def set_opportunity_stage(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        new_stage: FunnelStage,
        notes: Optional[str] = None
    ) -> bool:
        """Set opportunity to specific funnel stage"""
        opportunity = self._find_opportunity(profile_id, opportunity_id)
        if not opportunity:
            return False
        
        old_stage = opportunity.funnel_stage
        opportunity.set_stage(new_stage, notes)
        self._record_stage_transition(profile_id, opportunity, old_stage, new_stage)
        return True
    
    def get_funnel_metrics(self, profile_id: str) -> Dict[str, Any]:
        """Get comprehensive funnel analytics for a profile"""
        opportunities = self.opportunities.get(profile_id, [])
        
        if not opportunities:
            return self._empty_metrics()
        
        # Stage distribution
        stage_counts = Counter(opp.funnel_stage for opp in opportunities)
        
        # Conversion metrics
        total_opps = len(opportunities)
        conversion_rates = {}
        stage_order = [
            FunnelStage.PROSPECTS,
            FunnelStage.QUALIFIED_PROSPECTS,
            FunnelStage.CANDIDATES,
            FunnelStage.TARGETS,
            FunnelStage.OPPORTUNITIES
        ]
        
        for i, stage in enumerate(stage_order):
            if i == 0:
                conversion_rates[stage.value] = 100.0  # All start as prospects
            else:
                current_count = stage_counts.get(stage, 0)
                # Calculate conversion from prospects (total) to current stage
                conversion_rates[stage.value] = (current_count / total_opps * 100) if total_opps > 0 else 0.0
        
        # Time in stages
        stage_times = self._calculate_stage_durations(profile_id)
        
        # Recent activity
        recent_transitions = self._get_recent_transitions(profile_id, days=7)
        
        return {
            "profile_id": profile_id,
            "total_opportunities": total_opps,
            "stage_distribution": dict(stage_counts),
            "conversion_rates": conversion_rates,
            "average_stage_duration_hours": stage_times,
            "recent_transitions": recent_transitions,
            "funnel_velocity": self._calculate_funnel_velocity(profile_id),
            "top_performers": self._get_top_performing_opportunities(profile_id),
            "at_risk_opportunities": self._identify_stalled_opportunities(profile_id)
        }
    
    def bulk_stage_transition(
        self,
        profile_id: str,
        opportunity_ids: List[str],
        target_stage: FunnelStage,
        notes: Optional[str] = None
    ) -> Dict[str, bool]:
        """Bulk transition multiple opportunities to target stage"""
        results = {}
        for opp_id in opportunity_ids:
            results[opp_id] = self.set_opportunity_stage(profile_id, opp_id, target_stage, notes)
        return results
    
    def apply_stage_filter(
        self,
        opportunities: List[DiscoveryResult],
        stage_filter: Optional[FunnelStage] = None,
        min_score: Optional[float] = None,
        funding_type_filter: Optional[str] = None
    ) -> List[DiscoveryResult]:
        """Apply filters to opportunity list"""
        filtered = opportunities
        
        if stage_filter:
            filtered = [opp for opp in filtered if opp.funnel_stage == stage_filter]
        
        if min_score is not None:
            filtered = [opp for opp in filtered if opp.compatibility_score >= min_score]
        
        if funding_type_filter:
            filtered = [opp for opp in filtered if opp.source_type.value == funding_type_filter]
        
        return filtered
    
    def get_stage_recommendations(self, profile_id: str) -> Dict[str, List[str]]:
        """Get recommendations for stage transitions"""
        opportunities = self.opportunities.get(profile_id, [])
        recommendations = defaultdict(list)
        
        for opp in opportunities:
            # High-scoring prospects should be qualified
            if (opp.funnel_stage == FunnelStage.PROSPECTS and 
                opp.compatibility_score > 0.7):
                recommendations["promote_to_qualified"].append(opp.opportunity_id)
            
            # Well-qualified candidates with high scores should be targets
            elif (opp.funnel_stage == FunnelStage.CANDIDATES and 
                  opp.compatibility_score > 0.8 and
                  opp.confidence_level > 0.7):
                recommendations["promote_to_targets"].append(opp.opportunity_id)
            
            # Targets with very high scores should be opportunities
            elif (opp.funnel_stage == FunnelStage.TARGETS and
                  opp.compatibility_score > 0.9):
                recommendations["promote_to_opportunities"].append(opp.opportunity_id)
            
            # Low-performing opportunities should be demoted or archived
            elif opp.compatibility_score < 0.3:
                recommendations["consider_demotion"].append(opp.opportunity_id)
        
        return dict(recommendations)
    
    def _find_opportunity(self, profile_id: str, opportunity_id: str) -> Optional[DiscoveryResult]:
        """Find opportunity by ID within profile"""
        for opp in self.opportunities.get(profile_id, []):
            if opp.opportunity_id == opportunity_id:
                return opp
        return None
    
    def _record_stage_transition(
        self,
        profile_id: str,
        opportunity: DiscoveryResult,
        old_stage: Optional[FunnelStage],
        new_stage: FunnelStage
    ) -> None:
        """Record stage transition for analytics"""
        transition_record = {
            "opportunity_id": opportunity.opportunity_id,
            "organization_name": opportunity.organization_name,
            "old_stage": old_stage.value if old_stage else None,
            "new_stage": new_stage.value,
            "timestamp": datetime.now(),
            "compatibility_score": opportunity.compatibility_score,
            "notes": opportunity.stage_notes
        }
        self.stage_history[profile_id].append(transition_record)
    
    def _calculate_stage_durations(self, profile_id: str) -> Dict[str, float]:
        """Calculate average time spent in each stage"""
        stage_durations = defaultdict(list)
        transitions = self.stage_history.get(profile_id, [])
        
        # Group transitions by opportunity
        opp_transitions = defaultdict(list)
        for transition in transitions:
            opp_transitions[transition["opportunity_id"]].append(transition)
        
        # Calculate durations for each opportunity
        for opp_id, opp_transitions_list in opp_transitions.items():
            # Sort by timestamp
            opp_transitions_list.sort(key=lambda x: x["timestamp"])
            
            for i in range(len(opp_transitions_list) - 1):
                current = opp_transitions_list[i]
                next_transition = opp_transitions_list[i + 1]
                
                if current["new_stage"]:
                    duration_hours = (
                        next_transition["timestamp"] - current["timestamp"]
                    ).total_seconds() / 3600
                    stage_durations[current["new_stage"]].append(duration_hours)
        
        # Calculate averages
        return {
            stage: sum(durations) / len(durations) if durations else 0.0
            for stage, durations in stage_durations.items()
        }
    
    def _get_recent_transitions(self, profile_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent stage transitions"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        transitions = self.stage_history.get(profile_id, [])
        
        return [
            t for t in transitions
            if t["timestamp"] >= cutoff_date
        ]
    
    def _calculate_funnel_velocity(self, profile_id: str) -> Dict[str, float]:
        """Calculate how quickly opportunities move through funnel"""
        opportunities = self.opportunities.get(profile_id, [])
        
        if not opportunities:
            return {}
        
        # Calculate average days since discovery for each stage
        now = datetime.now()
        velocity_metrics = {}
        
        for stage in FunnelStage:
            stage_opps = [opp for opp in opportunities if opp.funnel_stage == stage]
            if stage_opps:
                avg_days = sum(
                    (now - opp.discovered_at).days for opp in stage_opps
                ) / len(stage_opps)
                velocity_metrics[stage.value] = avg_days
        
        return velocity_metrics
    
    def _get_top_performing_opportunities(self, profile_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top-performing opportunities by compatibility score"""
        opportunities = self.opportunities.get(profile_id, [])
        
        # Sort by compatibility score descending
        top_opps = sorted(
            opportunities,
            key=lambda x: x.compatibility_score,
            reverse=True
        )[:limit]
        
        return [
            {
                "opportunity_id": opp.opportunity_id,
                "organization_name": opp.organization_name,
                "funnel_stage": opp.funnel_stage.value,
                "compatibility_score": opp.compatibility_score,
                "source_type": opp.source_type.value
            }
            for opp in top_opps
        ]
    
    def _identify_stalled_opportunities(self, profile_id: str, days_threshold: int = 14) -> List[Dict[str, Any]]:
        """Identify opportunities that haven't progressed in a while"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days_threshold)
        opportunities = self.opportunities.get(profile_id, [])
        
        stalled = []
        for opp in opportunities:
            if opp.stage_updated_at and opp.stage_updated_at < cutoff_date:
                days_stalled = (datetime.now() - opp.stage_updated_at).days
                stalled.append({
                    "opportunity_id": opp.opportunity_id,
                    "organization_name": opp.organization_name,
                    "funnel_stage": opp.funnel_stage.value,
                    "days_stalled": days_stalled,
                    "compatibility_score": opp.compatibility_score
                })
        
        return sorted(stalled, key=lambda x: x["days_stalled"], reverse=True)
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "profile_id": "",
            "total_opportunities": 0,
            "stage_distribution": {},
            "conversion_rates": {},
            "average_stage_duration_hours": {},
            "recent_transitions": [],
            "funnel_velocity": {},
            "top_performers": [],
            "at_risk_opportunities": []
        }


# Global funnel manager instance
funnel_manager = FunnelManager()
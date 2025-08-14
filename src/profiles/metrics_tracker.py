#!/usr/bin/env python3
"""
Profile Metrics Tracker Service
Manages real-time metrics collection and updates for organization profiles
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path

from .models import ProfileMetrics, OrganizationProfile
from .service import ProfileService

logger = logging.getLogger(__name__)


class ProfileMetricsTracker:
    """Service for tracking and updating profile-based metrics"""
    
    def __init__(self, profile_service: Optional[ProfileService] = None):
        self.profile_service = profile_service or ProfileService()
        self._metrics_cache: Dict[str, ProfileMetrics] = {}
        self._lock = asyncio.Lock()
    
    async def get_profile_metrics(self, profile_id: str) -> Optional[ProfileMetrics]:
        """Get metrics for a specific profile"""
        async with self._lock:
            # Check cache first
            if profile_id in self._metrics_cache:
                return self._metrics_cache[profile_id]
            
            # Load profile and initialize metrics if needed
            profile = self.profile_service.get_profile(profile_id)
            if not profile:
                return None
            
            # Initialize metrics if not present
            if not profile.metrics:
                profile.metrics = ProfileMetrics(profile_id=profile_id)
                self.profile_service.save_profile(profile)
            
            # Cache and return
            self._metrics_cache[profile_id] = profile.metrics
            return profile.metrics
    
    async def update_funnel_stage(self, profile_id: str, stage: str, count: int = 1) -> None:
        """Update funnel stage metrics for a profile"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            metrics.update_funnel_metrics(stage, count)
            await self._save_metrics(profile_id, metrics)
            logger.debug(f"Updated {stage} count by {count} for profile {profile_id}")
    
    async def track_api_call(self, profile_id: str, api_source: str) -> None:
        """Track an API call for a profile"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            metrics.add_api_call(api_source)
            await self._save_metrics(profile_id, metrics)
            logger.debug(f"Tracked {api_source} API call for profile {profile_id}")
    
    async def track_ai_processing(self, profile_id: str, ai_type: str, cost_usd: float = 0.0) -> None:
        """Track AI processing usage and costs"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            if ai_type.lower() == 'lite':
                metrics.ai_lite_calls += 1
            elif ai_type.lower() == 'heavy':
                metrics.ai_heavy_calls += 1
            
            metrics.total_ai_cost_usd += cost_usd
            metrics.last_updated = datetime.now()
            
            await self._save_metrics(profile_id, metrics)
            logger.debug(f"Tracked {ai_type} AI processing (${cost_usd}) for profile {profile_id}")
    
    async def track_processing_time(self, profile_id: str, minutes: float, success: bool = True) -> None:
        """Track processor execution time and success/failure"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            metrics.add_processing_time(minutes)
            
            if success:
                metrics.successful_processors += 1
            else:
                metrics.failed_processors += 1
            
            await self._save_metrics(profile_id, metrics)
            logger.debug(f"Tracked processing time: {minutes}min, success: {success} for profile {profile_id}")
    
    async def track_cache_usage(self, profile_id: str, hit: bool) -> None:
        """Track cache hit/miss statistics"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            if hit:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
            
            metrics.last_updated = datetime.now()
            await self._save_metrics(profile_id, metrics)
    
    async def start_discovery_session(self, profile_id: str) -> None:
        """Mark the start of a discovery session"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            metrics.total_discovery_sessions += 1
            metrics.last_discovery_session = datetime.now()
            await self._save_metrics(profile_id, metrics)
            logger.info(f"Started discovery session for profile {profile_id}")
    
    async def update_session_duration(self, profile_id: str, duration_minutes: float) -> None:
        """Update average session duration"""
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            # Calculate running average
            total_sessions = metrics.total_discovery_sessions
            if total_sessions > 0:
                current_total = metrics.avg_session_duration_minutes * (total_sessions - 1)
                metrics.avg_session_duration_minutes = (current_total + duration_minutes) / total_sessions
            
            await self._save_metrics(profile_id, metrics)
    
    async def update_match_scores(self, profile_id: str, scores: List[float]) -> None:
        """Update average match score based on new results"""
        if not scores:
            return
        
        metrics = await self.get_profile_metrics(profile_id)
        if metrics:
            new_average = sum(scores) / len(scores)
            
            # Update running average if we have existing data
            if metrics.average_match_score is not None:
                total_opps = metrics.total_opportunities_discovered
                if total_opps > 0:
                    current_total = metrics.average_match_score * total_opps
                    total_opps += len(scores)
                    metrics.average_match_score = (current_total + sum(scores)) / total_opps
            else:
                metrics.average_match_score = new_average
            
            await self._save_metrics(profile_id, metrics)
    
    async def generate_efficiency_report(self, profile_id: str) -> Dict[str, Any]:
        """Generate comprehensive efficiency report for a profile"""
        metrics = await self.get_profile_metrics(profile_id)
        if not metrics:
            return {"error": "No metrics found for profile"}
        
        # Calculate derived metrics
        fte_hours_saved = metrics.calculate_fte_hours_saved()
        cost_efficiency = metrics.calculate_cost_efficiency()
        
        total_processing_hours = metrics.total_processing_time_minutes / 60.0
        roi_multiplier = fte_hours_saved / total_processing_hours if total_processing_hours > 0 else 0
        
        # Calculate cache efficiency
        total_cache_ops = metrics.cache_hits + metrics.cache_misses
        cache_hit_rate = metrics.cache_hits / total_cache_ops if total_cache_ops > 0 else 0
        
        # Success rate
        total_processors = metrics.successful_processors + metrics.failed_processors
        success_rate = metrics.successful_processors / total_processors if total_processors > 0 else 0
        
        return {
            "profile_id": profile_id,
            "last_updated": metrics.last_updated.isoformat(),
            
            # Volume Metrics
            "total_opportunities": metrics.total_opportunities_discovered,
            "funnel_breakdown": metrics.funnel_stage_counts,
            "discovery_sessions": metrics.total_discovery_sessions,
            
            # Efficiency Metrics
            "fte_hours_saved": round(fte_hours_saved, 2),
            "processing_hours": round(total_processing_hours, 2),
            "roi_multiplier": round(roi_multiplier, 1),
            "success_rate": round(success_rate * 100, 1),
            "cache_hit_rate": round(cache_hit_rate * 100, 1),
            
            # Cost Metrics
            "total_ai_cost": round(metrics.total_ai_cost_usd, 2),
            "cost_per_qualified_opp": round(cost_efficiency, 2) if cost_efficiency > 0 else None,
            "ai_lite_calls": metrics.ai_lite_calls,
            "ai_heavy_calls": metrics.ai_heavy_calls,
            
            # API Usage
            "api_calls": metrics.api_calls_made,
            "total_api_calls": sum(metrics.api_calls_made.values()),
            
            # Quality Metrics
            "average_match_score": round(metrics.average_match_score * 100, 1) if metrics.average_match_score else None,
            "avg_session_duration": round(metrics.avg_session_duration_minutes, 1)
        }
    
    async def get_all_profile_metrics_summary(self) -> List[Dict[str, Any]]:
        """Get summary metrics for all profiles"""
        profiles = self.profile_service.list_profiles()  # Remove await - this method is sync
        summaries = []
        
        for profile in profiles:
            if profile.metrics:
                summary = {
                    "profile_id": profile.profile_id,
                    "profile_name": profile.name,
                    "total_opportunities": profile.metrics.total_opportunities_discovered,
                    "fte_hours_saved": round(profile.metrics.calculate_fte_hours_saved(), 1),
                    "total_cost": round(profile.metrics.total_ai_cost_usd, 2),
                    "last_discovery": profile.metrics.last_discovery_session.isoformat() if profile.metrics.last_discovery_session else None,
                    "discovery_sessions": profile.metrics.total_discovery_sessions
                }
                summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x["fte_hours_saved"], reverse=True)
    
    async def _save_metrics(self, profile_id: str, metrics: ProfileMetrics) -> None:
        """Save updated metrics back to profile"""
        profile = self.profile_service.get_profile(profile_id)
        if profile:
            profile.metrics = metrics
            self.profile_service.save_profile(profile)
            
            # Update cache
            async with self._lock:
                self._metrics_cache[profile_id] = metrics


# Global instance
_metrics_tracker = None

def get_metrics_tracker() -> ProfileMetricsTracker:
    """Get global metrics tracker instance"""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = ProfileMetricsTracker()
    return _metrics_tracker
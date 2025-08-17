#!/usr/bin/env python3
"""
Workflow Optimizer Service
Advanced workflow optimization and filtering for nonprofit research processes.

This service provides:
1. Intelligent filtering and search across all entity types
2. Workflow state management and optimization
3. Advanced opportunity prioritization
4. Batch processing optimization
5. Performance analytics and recommendations
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Nonprofit research workflow stages."""
    PROSPECTS = "prospects"
    QUALIFIED_PROSPECTS = "qualified_prospects"
    CANDIDATES = "candidates"
    TARGETS = "targets"
    OPPORTUNITIES = "opportunities"


class FilterCriteria(Enum):
    """Available filter criteria."""
    REVENUE_RANGE = "revenue_range"
    GEOGRAPHIC_LOCATION = "geographic_location"
    NTEE_CODES = "ntee_codes"
    OPPORTUNITY_TYPE = "opportunity_type"
    FUNDING_AMOUNT = "funding_amount"
    DEADLINE_PROXIMITY = "deadline_proximity"
    MATCH_SCORE = "match_score"
    LAST_ACTIVITY = "last_activity"


@dataclass
class FilterSet:
    """Represents a set of filters to apply."""
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    states: Optional[List[str]] = None
    ntee_codes: Optional[List[str]] = None
    min_match_score: Optional[float] = None
    max_days_since_activity: Optional[int] = None
    opportunity_types: Optional[List[str]] = None
    deadline_within_days: Optional[int] = None


@dataclass
class WorkflowOptimization:
    """Workflow optimization recommendation."""
    stage: WorkflowStage
    entity_count: int
    optimization_type: str
    description: str
    impact_score: float
    implementation_effort: str
    estimated_time_savings: str


@dataclass
class AdvancedSearchResult:
    """Advanced search result with relevance scoring."""
    entity_id: str
    entity_type: str
    relevance_score: float
    match_reasons: List[str]
    entity_data: Dict[str, Any]
    stage: WorkflowStage


class WorkflowOptimizer:
    """Advanced workflow optimization and filtering service."""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.logger = logging.getLogger(__name__)
        
        # Workflow stage progression rules
        self.stage_progression = {
            WorkflowStage.PROSPECTS: WorkflowStage.QUALIFIED_PROSPECTS,
            WorkflowStage.QUALIFIED_PROSPECTS: WorkflowStage.CANDIDATES,
            WorkflowStage.CANDIDATES: WorkflowStage.TARGETS,
            WorkflowStage.TARGETS: WorkflowStage.OPPORTUNITIES
        }
        
        # Performance thresholds for optimization
        self.performance_thresholds = {
            'high_volume': 100,  # Entities requiring batch processing
            'stale_data': 30,    # Days since last activity
            'low_score': 0.4,    # Minimum viable match score
            'urgent_deadline': 14  # Days until deadline
        }
    
    async def optimize_workflow(self, profile_id: str) -> List[WorkflowOptimization]:
        """Generate workflow optimization recommendations for a profile."""
        self.logger.info(f"Analyzing workflow optimization for profile {profile_id}")
        
        optimizations = []
        
        try:
            # Load profile data
            profile_data = await self._load_profile_data(profile_id)
            if not profile_data:
                return []
            
            # Analyze each workflow stage
            for stage in WorkflowStage:
                stage_entities = await self._get_stage_entities(profile_id, stage)
                stage_opts = await self._analyze_stage_optimization(stage, stage_entities, profile_data)
                optimizations.extend(stage_opts)
            
            # Cross-stage optimizations
            cross_stage_opts = await self._analyze_cross_stage_optimization(profile_id, profile_data)
            optimizations.extend(cross_stage_opts)
            
            # Sort by impact score
            optimizations.sort(key=lambda x: x.impact_score, reverse=True)
            
            self.logger.info(f"Generated {len(optimizations)} optimization recommendations")
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Error optimizing workflow for {profile_id}: {e}")
            return []
    
    async def advanced_search(
        self, 
        query: str, 
        filters: FilterSet, 
        profile_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AdvancedSearchResult]:
        """Perform advanced search across all entities with intelligent filtering."""
        self.logger.info(f"Performing advanced search: '{query}' with filters")
        
        results = []
        
        try:
            # Search nonprofits
            nonprofit_results = await self._search_nonprofits(query, filters, profile_id)
            results.extend(nonprofit_results)
            
            # Search opportunities
            opportunity_results = await self._search_opportunities(query, filters, profile_id)
            results.extend(opportunity_results)
            
            # Search discovery leads if profile specified
            if profile_id:
                lead_results = await self._search_discovery_leads(query, filters, profile_id)
                results.extend(lead_results)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Apply limit
            results = results[:limit]
            
            self.logger.info(f"Advanced search returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in advanced search: {e}")
            return []
    
    async def get_workflow_analytics(self, profile_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow analytics for a profile."""
        try:
            analytics = {
                'profile_id': profile_id,
                'generated_at': datetime.now().isoformat(),
                'stage_distribution': {},
                'performance_metrics': {},
                'optimization_opportunities': [],
                'trend_analysis': {}
            }
            
            # Analyze stage distribution
            total_entities = 0
            for stage in WorkflowStage:
                entities = await self._get_stage_entities(profile_id, stage)
                count = len(entities)
                analytics['stage_distribution'][stage.value] = count
                total_entities += count
            
            # Calculate performance metrics
            analytics['performance_metrics'] = {
                'total_entities': total_entities,
                'conversion_rates': await self._calculate_conversion_rates(profile_id),
                'average_match_scores': await self._calculate_average_scores(profile_id),
                'processing_efficiency': await self._calculate_processing_efficiency(profile_id)
            }
            
            # Get optimization opportunities
            optimizations = await self.optimize_workflow(profile_id)
            analytics['optimization_opportunities'] = [
                {
                    'stage': opt.stage.value,
                    'type': opt.optimization_type,
                    'description': opt.description,
                    'impact_score': opt.impact_score
                } for opt in optimizations[:5]  # Top 5
            ]
            
            # Trend analysis
            analytics['trend_analysis'] = await self._analyze_trends(profile_id)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error generating workflow analytics: {e}")
            return {}
    
    async def batch_process_recommendations(self, profile_id: str) -> Dict[str, Any]:
        """Generate batch processing recommendations for efficiency."""
        try:
            recommendations = {
                'profile_id': profile_id,
                'batch_opportunities': [],
                'estimated_time_savings': 0,
                'processing_order': []
            }
            
            # Identify batch processing opportunities
            for stage in WorkflowStage:
                entities = await self._get_stage_entities(profile_id, stage)
                
                if len(entities) >= self.performance_thresholds['high_volume']:
                    batch_opp = {
                        'stage': stage.value,
                        'entity_count': len(entities),
                        'batch_size': min(50, len(entities)),
                        'estimated_time_savings': len(entities) * 0.5,  # 0.5 minutes per entity
                        'priority': self._calculate_batch_priority(entities)
                    }
                    recommendations['batch_opportunities'].append(batch_opp)
            
            # Calculate total time savings
            recommendations['estimated_time_savings'] = sum(
                opp['estimated_time_savings'] for opp in recommendations['batch_opportunities']
            )
            
            # Optimize processing order
            recommendations['processing_order'] = await self._optimize_processing_order(
                recommendations['batch_opportunities']
            )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating batch recommendations: {e}")
            return {}
    
    async def _load_profile_data(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Load profile data from storage."""
        profile_file = self.data_path / "profiles" / "profiles" / f"profile_{profile_id}.json"
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading profile {profile_id}: {e}")
            return None
    
    async def _get_stage_entities(self, profile_id: str, stage: WorkflowStage) -> List[Dict[str, Any]]:
        """Get entities for a specific workflow stage."""
        entities = []
        
        # Load discovery leads for this profile
        leads_path = self.data_path / "profiles" / "leads"
        if leads_path.exists():
            for lead_file in leads_path.glob(f"*_{profile_id}_*.json"):
                try:
                    with open(lead_file, 'r') as f:
                        lead_data = json.load(f)
                    
                    if lead_data.get('funnel_stage') == stage.value:
                        entities.append(lead_data)
                        
                except Exception:
                    continue
        
        return entities
    
    async def _analyze_stage_optimization(
        self, 
        stage: WorkflowStage, 
        entities: List[Dict[str, Any]], 
        profile_data: Dict[str, Any]
    ) -> List[WorkflowOptimization]:
        """Analyze optimization opportunities for a specific stage."""
        optimizations = []
        entity_count = len(entities)
        
        if entity_count == 0:
            return optimizations
        
        # High volume optimization
        if entity_count >= self.performance_thresholds['high_volume']:
            optimizations.append(WorkflowOptimization(
                stage=stage,
                entity_count=entity_count,
                optimization_type="batch_processing",
                description=f"Process {entity_count} entities in batches for efficiency",
                impact_score=0.8,
                implementation_effort="Low",
                estimated_time_savings=f"{entity_count * 0.5:.0f} minutes"
            ))
        
        # Low score filtering
        low_score_entities = [e for e in entities if e.get('compatibility_score', 1.0) < self.performance_thresholds['low_score']]
        if len(low_score_entities) > entity_count * 0.3:  # More than 30% low scores
            optimizations.append(WorkflowOptimization(
                stage=stage,
                entity_count=len(low_score_entities),
                optimization_type="score_filtering",
                description=f"Filter out {len(low_score_entities)} low-scoring entities",
                impact_score=0.6,
                implementation_effort="Low",
                estimated_time_savings=f"{len(low_score_entities) * 0.2:.0f} minutes"
            ))
        
        # Stale data cleanup
        now = datetime.now()
        stale_entities = []
        for entity in entities:
            try:
                discovered_at = datetime.fromisoformat(entity.get('discovered_at', ''))
                if (now - discovered_at).days > self.performance_thresholds['stale_data']:
                    stale_entities.append(entity)
            except:
                continue
        
        if stale_entities:
            optimizations.append(WorkflowOptimization(
                stage=stage,
                entity_count=len(stale_entities),
                optimization_type="stale_cleanup",
                description=f"Archive {len(stale_entities)} stale entities",
                impact_score=0.4,
                implementation_effort="Low",
                estimated_time_savings=f"{len(stale_entities) * 0.1:.0f} minutes"
            ))
        
        return optimizations
    
    async def _analyze_cross_stage_optimization(self, profile_id: str, profile_data: Dict[str, Any]) -> List[WorkflowOptimization]:
        """Analyze cross-stage optimization opportunities."""
        optimizations = []
        
        # Check for stage imbalances
        stage_counts = {}
        for stage in WorkflowStage:
            entities = await self._get_stage_entities(profile_id, stage)
            stage_counts[stage] = len(entities)
        
        # Detect bottlenecks
        total_entities = sum(stage_counts.values())
        if total_entities > 0:
            for stage, count in stage_counts.items():
                percentage = count / total_entities
                
                # Too many entities stuck in early stages
                if stage in [WorkflowStage.PROSPECTS, WorkflowStage.QUALIFIED_PROSPECTS] and percentage > 0.6:
                    optimizations.append(WorkflowOptimization(
                        stage=stage,
                        entity_count=count,
                        optimization_type="stage_progression",
                        description=f"Consider moving qualified entities from {stage.value} to next stage",
                        impact_score=0.7,
                        implementation_effort="Medium",
                        estimated_time_savings="30-60 minutes"
                    ))
        
        return optimizations
    
    async def _search_nonprofits(self, query: str, filters: FilterSet, profile_id: Optional[str]) -> List[AdvancedSearchResult]:
        """Search nonprofit entities."""
        results = []
        nonprofits_path = self.data_path / "source_data" / "nonprofits"
        
        if not nonprofits_path.exists():
            return results
        
        for entity_dir in nonprofits_path.iterdir():
            if not entity_dir.is_dir():
                continue
            
            metadata_file = entity_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, 'r') as f:
                    entity_data = json.load(f)
                
                # Apply filters
                if not self._apply_filters(entity_data, filters):
                    continue
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance(entity_data, query)
                
                if relevance_score > 0.1:  # Minimum relevance threshold
                    # Determine stage based on discovery data
                    stage = await self._determine_entity_stage(entity_dir.name, profile_id)
                    
                    match_reasons = self._generate_match_reasons(entity_data, query, filters)
                    
                    results.append(AdvancedSearchResult(
                        entity_id=entity_dir.name,
                        entity_type="nonprofit",
                        relevance_score=relevance_score,
                        match_reasons=match_reasons,
                        entity_data=entity_data,
                        stage=stage
                    ))
                    
            except Exception as e:
                self.logger.warning(f"Error processing nonprofit {entity_dir.name}: {e}")
                continue
        
        return results
    
    async def _search_opportunities(self, query: str, filters: FilterSet, profile_id: Optional[str]) -> List[AdvancedSearchResult]:
        """Search opportunity entities."""
        results = []
        opportunities_path = self.data_path / "source_data" / "government" / "opportunities"
        
        if not opportunities_path.exists():
            return results
        
        for opp_dir in opportunities_path.iterdir():
            if not opp_dir.is_dir():
                continue
            
            for opp_file in opp_dir.glob("*.json"):
                try:
                    with open(opp_file, 'r') as f:
                        opp_data = json.load(f)
                    
                    # Apply filters
                    if not self._apply_opportunity_filters(opp_data, filters):
                        continue
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_opportunity_relevance(opp_data, query)
                    
                    if relevance_score > 0.1:
                        match_reasons = self._generate_opportunity_match_reasons(opp_data, query, filters)
                        
                        results.append(AdvancedSearchResult(
                            entity_id=opp_file.stem,
                            entity_type="government_opportunity",
                            relevance_score=relevance_score,
                            match_reasons=match_reasons,
                            entity_data=opp_data,
                            stage=WorkflowStage.OPPORTUNITIES  # Opportunities are always at opportunity stage
                        ))
                        
                except Exception as e:
                    self.logger.warning(f"Error processing opportunity {opp_file}: {e}")
                    continue
        
        return results
    
    async def _search_discovery_leads(self, query: str, filters: FilterSet, profile_id: str) -> List[AdvancedSearchResult]:
        """Search discovery leads for a specific profile."""
        results = []
        leads_path = self.data_path / "profiles" / "leads"
        
        if not leads_path.exists():
            return results
        
        for lead_file in leads_path.glob(f"*_{profile_id}_*.json"):
            try:
                with open(lead_file, 'r') as f:
                    lead_data = json.load(f)
                
                # Calculate relevance score
                relevance_score = self._calculate_lead_relevance(lead_data, query)
                
                if relevance_score > 0.1:
                    # Determine stage
                    stage_value = lead_data.get('funnel_stage', 'prospects')
                    try:
                        stage = WorkflowStage(stage_value)
                    except ValueError:
                        stage = WorkflowStage.PROSPECTS
                    
                    match_reasons = self._generate_lead_match_reasons(lead_data, query)
                    
                    results.append(AdvancedSearchResult(
                        entity_id=lead_file.stem,
                        entity_type="discovery_lead",
                        relevance_score=relevance_score,
                        match_reasons=match_reasons,
                        entity_data=lead_data,
                        stage=stage
                    ))
                    
            except Exception as e:
                self.logger.warning(f"Error processing lead {lead_file}: {e}")
                continue
        
        return results
    
    def _apply_filters(self, entity_data: Dict[str, Any], filters: FilterSet) -> bool:
        """Apply filters to entity data."""
        # Revenue filter
        revenue = entity_data.get('revenue') or entity_data.get('annual_revenue')
        if revenue:
            if filters.revenue_min and revenue < filters.revenue_min:
                return False
            if filters.revenue_max and revenue > filters.revenue_max:
                return False
        
        # State filter
        if filters.states:
            entity_state = entity_data.get('state')
            if entity_state and entity_state not in filters.states:
                return False
        
        # NTEE code filter
        if filters.ntee_codes:
            entity_ntee = entity_data.get('ntee_code')
            if entity_ntee:
                # Check if any NTEE code matches
                matches = any(code in entity_ntee for code in filters.ntee_codes)
                if not matches:
                    return False
        
        return True
    
    def _apply_opportunity_filters(self, opp_data: Dict[str, Any], filters: FilterSet) -> bool:
        """Apply filters to opportunity data."""
        # Funding amount filter
        if filters.revenue_min or filters.revenue_max:
            award_ceiling = opp_data.get('award_ceiling')
            if award_ceiling:
                if filters.revenue_min and award_ceiling < filters.revenue_min:
                    return False
                if filters.revenue_max and award_ceiling > filters.revenue_max:
                    return False
        
        # Deadline filter
        if filters.deadline_within_days:
            deadline = opp_data.get('close_date')
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    days_until = (deadline_date - datetime.now()).days
                    if days_until > filters.deadline_within_days:
                        return False
                except:
                    pass
        
        return True
    
    def _calculate_relevance(self, entity_data: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for an entity."""
        if not query:
            return 0.5
        
        query_lower = query.lower()
        score = 0.0
        
        # Check name
        name = entity_data.get('name', '').lower()
        if query_lower in name:
            score += 0.4
        
        # Check mission
        mission = entity_data.get('mission', '').lower()
        if query_lower in mission:
            score += 0.3
        
        # Check keywords
        keywords = entity_data.get('keywords', '').lower()
        if query_lower in keywords:
            score += 0.2
        
        # Check focus areas
        focus_areas = entity_data.get('focus_areas', [])
        for area in focus_areas:
            if query_lower in str(area).lower():
                score += 0.1
                break
        
        return min(1.0, score)
    
    def _calculate_opportunity_relevance(self, opp_data: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for an opportunity."""
        if not query:
            return 0.5
        
        query_lower = query.lower()
        score = 0.0
        
        # Check title
        title = opp_data.get('title', '').lower()
        if query_lower in title:
            score += 0.4
        
        # Check description
        description = opp_data.get('description', '').lower()
        if query_lower in description:
            score += 0.3
        
        # Check agency
        agency = opp_data.get('agency', '').lower()
        if query_lower in agency:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_lead_relevance(self, lead_data: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a discovery lead."""
        if not query:
            return 0.5
        
        query_lower = query.lower()
        score = 0.0
        
        # Check organization name
        org_name = lead_data.get('organization_name', '').lower()
        if query_lower in org_name:
            score += 0.4
        
        # Check source type
        source_type = lead_data.get('source_type', '').lower()
        if query_lower in source_type:
            score += 0.2
        
        # Check discovery source
        discovery_source = lead_data.get('discovery_source', '').lower()
        if query_lower in discovery_source:
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_match_reasons(self, entity_data: Dict[str, Any], query: str, filters: FilterSet) -> List[str]:
        """Generate reasons why an entity matches the search."""
        reasons = []
        
        if query:
            query_lower = query.lower()
            if query_lower in entity_data.get('name', '').lower():
                reasons.append(f"Name contains '{query}'")
            if query_lower in entity_data.get('mission', '').lower():
                reasons.append(f"Mission contains '{query}'")
        
        if filters.revenue_min or filters.revenue_max:
            revenue = entity_data.get('revenue') or entity_data.get('annual_revenue')
            if revenue:
                reasons.append(f"Revenue ${revenue:,.0f} meets criteria")
        
        if filters.states:
            state = entity_data.get('state')
            if state and state in filters.states:
                reasons.append(f"Located in {state}")
        
        return reasons
    
    def _generate_opportunity_match_reasons(self, opp_data: Dict[str, Any], query: str, filters: FilterSet) -> List[str]:
        """Generate reasons why an opportunity matches the search."""
        reasons = []
        
        if query:
            query_lower = query.lower()
            if query_lower in opp_data.get('title', '').lower():
                reasons.append(f"Title contains '{query}'")
            if query_lower in opp_data.get('description', '').lower():
                reasons.append(f"Description contains '{query}'")
        
        award_ceiling = opp_data.get('award_ceiling')
        if award_ceiling:
            reasons.append(f"Award up to ${award_ceiling:,.0f}")
        
        return reasons
    
    def _generate_lead_match_reasons(self, lead_data: Dict[str, Any], query: str) -> List[str]:
        """Generate reasons why a lead matches the search."""
        reasons = []
        
        if query:
            query_lower = query.lower()
            if query_lower in lead_data.get('organization_name', '').lower():
                reasons.append(f"Organization name contains '{query}'")
        
        score = lead_data.get('compatibility_score')
        if score:
            reasons.append(f"Match score: {score:.1%}")
        
        stage = lead_data.get('funnel_stage', 'prospects')
        reasons.append(f"Stage: {stage.replace('_', ' ').title()}")
        
        return reasons
    
    async def _determine_entity_stage(self, entity_id: str, profile_id: Optional[str]) -> WorkflowStage:
        """Determine the workflow stage for an entity."""
        if not profile_id:
            return WorkflowStage.PROSPECTS
        
        # Look for discovery leads that reference this entity
        leads_path = self.data_path / "profiles" / "leads"
        if leads_path.exists():
            for lead_file in leads_path.glob(f"*_{profile_id}_*.json"):
                try:
                    with open(lead_file, 'r') as f:
                        lead_data = json.load(f)
                    
                    # Check if this lead references our entity
                    if entity_id in lead_file.name or entity_id in str(lead_data):
                        stage_value = lead_data.get('funnel_stage', 'prospects')
                        try:
                            return WorkflowStage(stage_value)
                        except ValueError:
                            pass
                except:
                    continue
        
        return WorkflowStage.PROSPECTS
    
    async def _calculate_conversion_rates(self, profile_id: str) -> Dict[str, float]:
        """Calculate conversion rates between workflow stages."""
        rates = {}
        
        stage_counts = {}
        for stage in WorkflowStage:
            entities = await self._get_stage_entities(profile_id, stage)
            stage_counts[stage] = len(entities)
        
        # Calculate conversion rates
        stages = list(WorkflowStage)
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            current_count = stage_counts[current_stage]
            next_count = stage_counts[next_stage]
            
            if current_count > 0:
                rate = next_count / current_count
            else:
                rate = 0.0
            
            rates[f"{current_stage.value}_to_{next_stage.value}"] = rate
        
        return rates
    
    async def _calculate_average_scores(self, profile_id: str) -> Dict[str, float]:
        """Calculate average match scores by stage."""
        scores = {}
        
        for stage in WorkflowStage:
            entities = await self._get_stage_entities(profile_id, stage)
            
            if entities:
                stage_scores = [
                    e.get('compatibility_score', 0) for e in entities 
                    if e.get('compatibility_score') is not None
                ]
                
                if stage_scores:
                    scores[stage.value] = sum(stage_scores) / len(stage_scores)
                else:
                    scores[stage.value] = 0.0
            else:
                scores[stage.value] = 0.0
        
        return scores
    
    async def _calculate_processing_efficiency(self, profile_id: str) -> Dict[str, Any]:
        """Calculate processing efficiency metrics."""
        total_entities = 0
        recent_activity = 0
        
        for stage in WorkflowStage:
            entities = await self._get_stage_entities(profile_id, stage)
            total_entities += len(entities)
            
            # Count entities with recent activity (last 7 days)
            for entity in entities:
                try:
                    discovered_at = datetime.fromisoformat(entity.get('discovered_at', ''))
                    if (datetime.now() - discovered_at).days <= 7:
                        recent_activity += 1
                except:
                    continue
        
        return {
            'total_entities': total_entities,
            'recent_activity_rate': recent_activity / total_entities if total_entities > 0 else 0,
            'entities_per_stage': total_entities / len(WorkflowStage) if total_entities > 0 else 0
        }
    
    async def _analyze_trends(self, profile_id: str) -> Dict[str, Any]:
        """Analyze trends in workflow progression."""
        trends = {
            'discovery_rate': 0,
            'progression_rate': 0,
            'quality_trend': 'stable'
        }
        
        # Simple trend analysis based on recent activity
        total_entities = 0
        recent_entities = 0
        
        for stage in WorkflowStage:
            entities = await self._get_stage_entities(profile_id, stage)
            total_entities += len(entities)
            
            # Count entities discovered in last 14 days
            for entity in entities:
                try:
                    discovered_at = datetime.fromisoformat(entity.get('discovered_at', ''))
                    if (datetime.now() - discovered_at).days <= 14:
                        recent_entities += 1
                except:
                    continue
        
        if total_entities > 0:
            trends['discovery_rate'] = recent_entities / total_entities
        
        return trends
    
    def _calculate_batch_priority(self, entities: List[Dict[str, Any]]) -> float:
        """Calculate priority score for batch processing."""
        if not entities:
            return 0.0
        
        # Higher priority for entities with higher match scores
        scores = [e.get('compatibility_score', 0) for e in entities if e.get('compatibility_score')]
        if scores:
            return sum(scores) / len(scores)
        
        return 0.5
    
    async def _optimize_processing_order(self, batch_opportunities: List[Dict[str, Any]]) -> List[str]:
        """Optimize the order of batch processing."""
        # Sort by priority (highest first)
        sorted_batches = sorted(batch_opportunities, key=lambda x: x['priority'], reverse=True)
        
        return [batch['stage'] for batch in sorted_batches]


# Factory function for easy access
def get_workflow_optimizer(data_path: str = "data") -> WorkflowOptimizer:
    """Get a configured workflow optimizer instance."""
    return WorkflowOptimizer(data_path)
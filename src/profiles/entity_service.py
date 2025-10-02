#!/usr/bin/env python3
"""
Enhanced Profile Service with Entity-Based Architecture Integration
Extends the existing profile service with entity references and shared analytics.
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from .unified_service import UnifiedProfileService
from .models import (
    OrganizationProfile,
    OpportunityLead,
    ProfileSearchParams,
    ProfileStatus,
    PipelineStage,
    DiscoverySession
)
from ..core.entity_cache_manager import get_entity_cache_manager, EntityType, DataSourceType
from ..analytics.financial_analytics import get_financial_analytics, FinancialMetrics
from ..analytics.network_analytics import get_network_analytics, NetworkMetrics
from ..analysis.profile_matcher import get_profile_matcher, OpportunityMatch, ProfileMatchResults
from ..database.database_manager import DatabaseManager, Opportunity

logger = logging.getLogger(__name__)


class EntityProfileService(UnifiedProfileService):
    """
    Enhanced profile service that integrates with entity-based architecture.
    
    Extends the base ProfileService with:
    - Entity ID references (EINs, opportunity IDs)
    - Shared analytics integration
    - Profile-specific analysis
    - Entity-based opportunity discovery
    """
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize entity-enhanced profile service"""
        super().__init__(data_dir)
        
        # Initialize entity-based components
        self.entity_cache_manager = get_entity_cache_manager()
        self.financial_analytics = get_financial_analytics()
        self.network_analytics = get_network_analytics()
        self.profile_matcher = get_profile_matcher()
        self.database_service = DatabaseManager("data/catalynx.db")
        
        self.logger = logging.getLogger(__name__)
    
    # Enhanced Profile Operations with Entity Integration
    
    async def analyze_profile_entities(self, profile_id: str) -> Dict[str, Any]:
        """
        Analyze all entities associated with a profile using shared analytics.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Dictionary with comprehensive entity analysis
        """
        try:
            profile = self.get_profile(profile_id)
            if not profile:
                return {"error": "Profile not found"}
            
            analysis = {
                "profile_id": profile_id,
                "profile_name": profile.name,
                "analyzed_at": datetime.now().isoformat(),
                "entity_analysis": {},
                "opportunities_analysis": {},
                "summary_metrics": {}
            }
            
            # Get profile leads (existing opportunities)
            leads = self.get_profile_leads(profile_id)
            
            # Analyze organizations from leads using entity cache
            organization_analyses = []
            for lead in leads:
                if hasattr(lead, 'organization_ein') and lead.organization_ein:
                    org_analysis = await self._analyze_organization_entity(
                        lead.organization_ein, profile
                    )
                    if org_analysis:
                        organization_analyses.append(org_analysis)
            
            analysis["entity_analysis"]["organizations"] = organization_analyses
            
            # Get government opportunities from entity cache
            gov_opportunities = await self._get_government_opportunities()
            analysis["opportunities_analysis"]["government"] = len(gov_opportunities)
            
            # Generate profile-specific matches
            if organization_analyses and gov_opportunities:
                match_results = self._generate_profile_matches(
                    organization_analyses, gov_opportunities, profile
                )
                analysis["opportunities_analysis"]["matches"] = match_results
            
            # Calculate summary metrics
            analysis["summary_metrics"] = self._calculate_summary_metrics(
                organization_analyses, analysis.get("opportunities_analysis", {})
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing profile entities: {e}")
            return {"error": str(e)}
    
    async def _analyze_organization_entity(self, ein: str, profile: OrganizationProfile) -> Optional[Dict[str, Any]]:
        """Analyze a single organization entity using shared analytics"""
        try:
            # Get organization data from entity cache
            org_data = await self.entity_cache_manager.get_entity_data(
                entity_id=ein,
                entity_type=EntityType.NONPROFIT,
                data_source=DataSourceType.PROPUBLICA
            )
            
            if not org_data:
                self.logger.debug(f"No entity data found for EIN {ein}")
                return None
            
            # Use shared financial analytics
            financial_metrics = self.financial_analytics.analyze_organization_financials(
                filing_data=org_data,
                organization_name=org_data.get('organization', {}).get('name', 'Unknown'),
                ein=ein
            )
            
            # Use shared network analytics
            board_members = self.network_analytics.extract_board_members_from_data(
                filing_data=org_data,
                ein=ein,
                organization_name=financial_metrics.organization_name
            )
            
            # Use profile-specific analysis
            profile_analysis = self.profile_matcher.analyze_organization_for_profile(
                organization_data=org_data,
                profile_criteria=None  # Would use profile.funding_preferences if available
            )
            
            return {
                "ein": ein,
                "organization_name": financial_metrics.organization_name,
                "financial_metrics": {
                    "revenue": financial_metrics.revenue,
                    "assets": financial_metrics.assets,
                    "financial_stability_score": financial_metrics.financial_stability_score,
                    "revenue_trend": financial_metrics.revenue_trend
                },
                "network_metrics": {
                    "board_member_count": len(board_members),
                    "board_members": [m.original_name for m in board_members[:5]]  # Top 5
                },
                "profile_analysis": profile_analysis,
                "data_sources": org_data.get('data_sources', []),
                "last_updated": org_data.get('cached_at', datetime.now().isoformat())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing organization entity {ein}: {e}")
            return None
    
    async def _get_government_opportunities(self) -> List[Dict[str, Any]]:
        """Get government opportunities from entity cache"""
        try:
            # Get list of government opportunities
            opportunity_ids = await self.entity_cache_manager.list_entities(
                EntityType.GOVERNMENT_OPPORTUNITY
            )
            
            opportunities = []
            for opp_id in opportunity_ids[:20]:  # Limit to 20 for analysis
                opp_data = await self.entity_cache_manager.get_entity_data(
                    entity_id=opp_id,
                    entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
                    data_source=DataSourceType.GRANTS_GOV
                )
                if opp_data:
                    opportunities.append(opp_data)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting government opportunities: {e}")
            return []
    
    def _generate_profile_matches(self, 
                                 organization_analyses: List[Dict[str, Any]],
                                 opportunities: List[Dict[str, Any]],
                                 profile: OrganizationProfile) -> Dict[str, Any]:
        """Generate profile-specific opportunity matches"""
        try:
            # Convert analyses to format expected by profile matcher
            org_data_list = []
            for analysis in organization_analyses:
                # Reconstruct organization data format
                org_data = {
                    "organization": {
                        "ein": analysis["ein"],
                        "name": analysis["organization_name"]
                    }
                }
                org_data_list.append(org_data)
            
            # Generate matches using profile matcher
            match_results = self.profile_matcher.generate_profile_matches(
                organizations=org_data_list,
                opportunities=opportunities,
                profile_criteria=None,  # Would use profile criteria
                profile_name=profile.name
            )
            
            return {
                "total_matches": len(match_results.matches),
                "high_quality_matches": match_results.summary_stats.get("high_quality_matches", 0),
                "top_matches": [
                    {
                        "organization_name": match.organization_name,
                        "opportunity_title": match.opportunity_title,
                        "match_score": match.final_match_score,
                        "recommendation": match.recommendation
                    }
                    for match in match_results.top_matches[:5]  # Top 5
                ],
                "summary_stats": match_results.summary_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error generating profile matches: {e}")
            return {"error": str(e)}
    
    def _calculate_summary_metrics(self, 
                                 organization_analyses: List[Dict[str, Any]],
                                 opportunities_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary metrics for the profile"""
        try:
            if not organization_analyses:
                return {"total_organizations": 0}
            
            # Financial metrics
            revenues = [
                a["financial_metrics"]["revenue"] 
                for a in organization_analyses 
                if a["financial_metrics"]["revenue"]
            ]
            stability_scores = [
                a["financial_metrics"]["financial_stability_score"]
                for a in organization_analyses
                if a["financial_metrics"]["financial_stability_score"] is not None
            ]
            
            summary = {
                "total_organizations": len(organization_analyses),
                "organizations_with_financial_data": len(revenues),
                "average_revenue": sum(revenues) / len(revenues) if revenues else 0,
                "average_stability_score": sum(stability_scores) / len(stability_scores) if stability_scores else 0,
                "total_board_members": sum(
                    a["network_metrics"]["board_member_count"] 
                    for a in organization_analyses
                ),
                "organizations_with_positive_trend": len([
                    a for a in organization_analyses
                    if a["financial_metrics"]["revenue_trend"] and a["financial_metrics"]["revenue_trend"] > 0
                ])
            }
            
            # Add opportunity metrics
            matches_data = opportunities_analysis.get("matches", {})
            if matches_data and not isinstance(matches_data, dict) or "error" not in matches_data:
                summary.update({
                    "total_opportunity_matches": matches_data.get("total_matches", 0),
                    "high_quality_matches": matches_data.get("high_quality_matches", 0)
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error calculating summary metrics: {e}")
            return {"error": str(e)}
    
    # Enhanced Lead Management with Entity References
    
    async def add_entity_lead(self, 
                       profile_id: str, 
                       organization_ein: str,
                       opportunity_id: Optional[str] = None,
                       additional_data: Optional[Dict[str, Any]] = None) -> Optional[OpportunityLead]:
        """
        Add opportunity lead using entity references instead of just names.
        
        Args:
            profile_id: Profile identifier
            organization_ein: Organization EIN for entity reference
            opportunity_id: Optional opportunity ID for entity reference
            additional_data: Additional lead data
            
        Returns:
            Created OpportunityLead or None if failed
        """
        try:
            # Verify profile exists
            profile = self.get_profile(profile_id)
            if not profile:
                return None
            
            # Get organization data from entity cache
            org_data = await self.entity_cache_manager.get_entity_data(
                entity_id=organization_ein,
                entity_type=EntityType.NONPROFIT,
                data_source=DataSourceType.PROPUBLICA
            )
            
            if not org_data:
                self.logger.warning(f"No organization data found for EIN {organization_ein}")
                return None
            
            # Extract organization info
            org_info = org_data.get('organization', {})
            org_name = org_info.get('name', '[Organization Name Missing]')
            
            # Get opportunity data if provided
            opportunity_data = {}
            if opportunity_id:
                opp_data = await self.entity_cache_manager.get_entity_data(
                    entity_id=opportunity_id,
                    entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
                    data_source=DataSourceType.GRANTS_GOV
                )
                if opp_data:
                    opportunity_data = {
                        "opportunity_title": opp_data.get('funding_opportunity_title', 'Unknown Opportunity'),
                        "funding_amount": opp_data.get('award_ceiling', 0),
                        "agency": opp_data.get('agency_code', 'Unknown')
                    }
            
            # Generate enhanced lead data
            lead_data = {
                "organization_name": org_name,
                "organization_ein": organization_ein,  # Entity reference
                "opportunity_id": opportunity_id,       # Entity reference
                "funding_amount": opportunity_data.get("funding_amount", 0),
                "opportunity_title": opportunity_data.get("opportunity_title", "Unknown"),
                "pipeline_stage": PipelineStage.DISCOVERED,
                "discovery_method": "entity_analysis",
                "external_data": {
                    "entity_references": {
                        "organization_ein": organization_ein,
                        "opportunity_id": opportunity_id
                    },
                    "organization_data": org_info,
                    "opportunity_data": opportunity_data
                }
            }
            
            # Add any additional data
            if additional_data:
                lead_data.update(additional_data)
            
            # Create opportunity using DatabaseManager for consistency
            opportunity_id = f"entity_{uuid.uuid4().hex[:12]}"
            db_stage = lead_data.get("current_stage", "prospects")
            
            opportunity = Opportunity(
                id=opportunity_id,
                profile_id=profile_id,
                organization_name=lead_data.get("organization_name", ""),
                ein=lead_data.get("external_data", {}).get("ein"),
                current_stage=db_stage,
                scoring={"overall_score": lead_data.get("compatibility_score", 0.0)},
                analysis={"match_factors": lead_data.get("match_factors", {})},
                source="entity_service",
                opportunity_type=lead_data.get("opportunity_type", "entity"),
                description=lead_data.get("description"),
                funding_amount=lead_data.get("funding_amount"),
                program_name=lead_data.get("program_name"),
                discovered_at=datetime.now(),
                last_updated=datetime.now(),
                status="active"
            )
            
            success = self.database_service.create_opportunity(opportunity)
            if success:
                self.logger.info(f"Entity opportunity created via DatabaseManager: {opportunity_id}")
                return opportunity_id
            else:
                self.logger.error(f"Failed to create entity opportunity: {opportunity_id}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error adding entity lead: {e}")
            return None
    
    async def get_entity_lead_analysis(self, lead_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analysis for a lead using entity-based data.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Dictionary with comprehensive lead analysis
        """
        try:
            # Find the lead
            lead = None
            for profile_file in self.leads_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    temp_lead = OpportunityLead(**data)
                    if temp_lead.lead_id == lead_id:
                        lead = temp_lead
                        break
                except (json.JSONDecodeError, ValueError):
                    continue
            
            if not lead:
                return {"error": "Lead not found"}
            
            analysis = {
                "lead_id": lead_id,
                "organization_name": lead.organization_name,
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Get entity-based analysis if EIN is available
            if hasattr(lead, 'organization_ein') and lead.organization_ein:
                # Get fresh organization analysis
                org_analysis = await self._analyze_organization_entity(
                    lead.organization_ein, None  # Profile not needed for this analysis
                )
                if org_analysis:
                    analysis["entity_analysis"] = org_analysis
            
            # Add opportunity analysis if opportunity ID is available
            if hasattr(lead, 'opportunity_id') and lead.opportunity_id:
                opp_data = await self.entity_cache_manager.get_entity_data(
                    entity_id=lead.opportunity_id,
                    entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
                    data_source=DataSourceType.GRANTS_GOV
                )
                if opp_data:
                    analysis["opportunity_analysis"] = {
                        "opportunity_id": lead.opportunity_id,
                        "title": opp_data.get('funding_opportunity_title', 'Unknown'),
                        "agency": opp_data.get('agency_code', 'Unknown'),
                        "funding_amount": opp_data.get('award_ceiling', 0),
                        "category": opp_data.get('category_of_funding_activity', 'Unknown')
                    }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error getting entity lead analysis: {e}")
            return {"error": str(e)}
    
    # Discovery Session Enhancement
    
    def create_entity_discovery_session(self, 
                                      profile_id: str,
                                      entity_types: List[str] = None,
                                      filters: Optional[Dict[str, Any]] = None) -> Optional[DiscoverySession]:
        """
        Create discovery session that leverages entity-based data sources.
        
        Args:
            profile_id: Profile identifier
            entity_types: Types of entities to discover (nonprofits, opportunities, etc.)
            filters: Additional filters for discovery
            
        Returns:
            Created DiscoverySession or None if failed
        """
        try:
            profile = self.get_profile(profile_id)
            if not profile:
                return None
            
            # Default entity types
            if not entity_types:
                entity_types = ["nonprofits", "government_opportunities"]
            
            # Create session with entity-based tracks
            session_data = {
                "profile_id": profile_id,
                "tracks": entity_types,
                "parameters": {
                    "use_entity_cache": True,
                    "entity_types": entity_types,
                    "filters": filters or {},
                    "analysis_mode": "entity_based"
                }
            }
            
            return self.start_discovery_session(profile_id, entity_types)
            
        except Exception as e:
            self.logger.error(f"Error creating entity discovery session: {e}")
            return None


# Global service instance
_entity_profile_service: Optional[EntityProfileService] = None


def get_entity_profile_service() -> EntityProfileService:
    """Get or create global entity profile service instance"""
    global _entity_profile_service
    if _entity_profile_service is None:
        _entity_profile_service = EntityProfileService()
    return _entity_profile_service
"""
Integration layer between profile-driven search and existing workflow system
Bridges organization profiles with the current grant research pipeline
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import OrganizationProfile, ProfileSearchParams, FundingType, PipelineStage
from .search_engine import ProfileSearchEngine
from .unified_service import get_unified_profile_service, UnifiedProfileService
from src.discovery.unified_discovery_adapter import get_unified_discovery_adapter
from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.discovery.discovery_engine import discovery_engine
from src.pipeline.pipeline_engine import pipeline_engine, PipelineConfig, ProcessingPriority
from src.database.database_manager import DatabaseManager, Opportunity
import uuid


class ProfileWorkflowIntegrator:
    """Integrates profile-driven search with existing workflow system"""
    
    def __init__(self):
        self.search_engine = ProfileSearchEngine()
        self.profile_service = get_unified_profile_service()  # Use UnifiedProfileService instead
        self.unified_service = get_unified_profile_service()
        self.discovery_adapter = get_unified_discovery_adapter()
        self.workflow_engine = get_workflow_engine()
        self.database_service = DatabaseManager("data/catalynx.db")
    
    async def discover_opportunities_for_profile(
        self, 
        profile_id: str, 
        funding_types: Optional[List[FundingType]] = None,
        max_results_per_type: int = 100,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Discover opportunities for a specific profile using the new multi-track discovery engine
        
        Args:
            profile_id: Organization profile identifier
            funding_types: Types of funding to search for
            max_results_per_type: Maximum results per funding type
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with discovery results and metadata
        """
        # Get profile
        profile = self.profile_service.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        # Execute discovery using the new multi-track engine
        discovery_session = await discovery_engine.discover_opportunities(
            profile=profile,
            funding_types=funding_types,
            max_results_per_type=max_results_per_type,
            progress_callback=progress_callback
        )
        
        # Get session results
        session_results = discovery_engine.get_session_results(discovery_session.session_id)
        session_summary = discovery_engine.get_session_summary(discovery_session.session_id)
        
        # Convert discovery results to the expected format for backward compatibility
        discovery_results = {}
        
        # Group results by funding type
        for funding_type in discovery_session.funding_types:
            type_results = [r for r in session_results if r.source_type == funding_type]
            
            if discovery_session.errors_by_type.get(funding_type):
                discovery_results[funding_type.value] = {
                    "status": "error",
                    "error": discovery_session.errors_by_type[funding_type],
                    "message": f"Failed to discover {funding_type.value} opportunities"
                }
            else:
                # Convert DiscoveryResult objects to dictionary format
                opportunities = []
                for result in type_results:
                    opportunity = {
                        "organization_name": result.organization_name,
                        "opportunity_type": result.source_type.value,
                        "program_name": result.program_name,
                        "description": result.description,
                        "funding_amount": result.funding_amount,
                        "application_deadline": result.application_deadline,
                        "compatibility_score": result.compatibility_score,
                        "confidence_level": result.confidence_level,
                        "match_factors": result.match_factors,
                        "risk_factors": result.risk_factors,
                        "contact_info": result.contact_info,
                        "geographic_info": result.geographic_info,
                        "metadata": result.external_data,
                        "opportunity_id": result.opportunity_id,
                        "discovered_at": result.discovered_at.isoformat(),
                        "pipeline_stage": PipelineStage.DISCOVERY.value,
                        "funnel_stage": result.funnel_stage.value,
                        "is_schedule_i_grantee": result.is_schedule_i_grantee,
                        "schedule_i_match_data": result.schedule_i_match_data
                    }
                    opportunities.append(opportunity)
                
                discovery_results[funding_type.value] = {
                    "status": "completed",
                    "funding_type": funding_type.value,
                    "total_opportunities": len(opportunities),
                    "opportunities": opportunities,
                    "metadata": {
                        "discoverer_used": f"Multi-Track Discovery Engine",
                        "avg_compatibility_score": sum(r.compatibility_score for r in type_results) / len(type_results) if type_results else 0,
                        "top_matches": len([r for r in type_results if r.compatibility_score > 0.7]),
                    }
                }
        
        # Enhanced: Save raw results to unified service
        unified_integration_results = None
        try:
            # Get raw discovery results for unified service integration
            raw_session_results = discovery_engine.get_session_results(discovery_session.session_id)
            
            # Save to unified service using adapter
            unified_integration_results = await self.discovery_adapter.save_discovery_results(
                discovery_results=raw_session_results,
                profile_id=profile_id,
                session_id=discovery_session.session_id
            )
            
            # Update session analytics in unified profile
            session_analytics = await self.discovery_adapter.update_discovery_session_analytics(
                session=discovery_session,
                save_results=unified_integration_results,
                profile_id=profile_id
            )
            
        except Exception as e:
            # Log error but don't fail the entire discovery process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed unified service integration: {e}")
            unified_integration_results = {"error": str(e), "saved_count": 0}
        
        # Create enhanced summary using session data
        enhanced_summary = self._create_enhanced_discovery_summary(session_summary, profile)
        
        return {
            "profile_id": profile_id,
            "profile_name": profile.name,
            "discovery_timestamp": discovery_session.started_at.isoformat() if discovery_session.started_at else datetime.now().isoformat(),
            "session_id": discovery_session.session_id,
            "funding_types_searched": [ft.value for ft in discovery_session.funding_types],
            "results": discovery_results,
            "summary": enhanced_summary,
            "execution_time_seconds": discovery_session.execution_time_seconds,
            "api_calls_made": discovery_session.api_calls_made,
            "session_status": discovery_session.status.value,
            "unified_integration": {
                "enabled": True,
                "saved_to_unified": unified_integration_results.get("saved_count", 0) if unified_integration_results else 0,
                "failed_saves": unified_integration_results.get("failed_count", 0) if unified_integration_results else 0,
                "duplicates_skipped": unified_integration_results.get("duplicates_skipped", 0) if unified_integration_results else 0,
                "analytics_refreshed": unified_integration_results.get("analytics_refreshed", False) if unified_integration_results else False,
                "error": unified_integration_results.get("error") if unified_integration_results else None
            }
        }
    
    async def _discover_grant_opportunities(
        self, 
        profile: OrganizationProfile, 
        params: ProfileSearchParams
    ) -> Dict[str, Any]:
        """Discover nonprofit/foundation grant opportunities using existing workflow"""
        
        # Convert profile search params to workflow config
        workflow_config = self._profile_params_to_workflow_config(profile, params)
        
        try:
            # Execute existing workflow
            workflow_state = await self.workflow_engine.run_workflow(workflow_config)
            
            # Convert results to profile-centric format
            converted_results = self._convert_workflow_results_to_profile_format(
                workflow_state, profile, FundingType.GRANTS
            )
            
            return {
                "status": "completed",
                "funding_type": "grants",
                "total_opportunities": len(converted_results.get("opportunities", [])),
                "opportunities": converted_results.get("opportunities", []),
                "metadata": converted_results.get("metadata", {}),
                "search_parameters": params.dict()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to execute grant discovery workflow"
            }
    
    async def _discover_government_opportunities(
        self, 
        profile: OrganizationProfile, 
        params: ProfileSearchParams
    ) -> Dict[str, Any]:
        """Discover government grant opportunities (placeholder for Grants.gov integration)"""
        
        # Grants.gov API integration available via grants_gov_fetch processor
        # Current status: Operational with rate limiting and error handling
        # This would search federal grant opportunities based on profile parameters
        
        discovery_filters = params.discovery_filters
        
        # Placeholder implementation - would integrate with Grants.gov API
        mock_opportunities = self._generate_mock_government_opportunities(profile, discovery_filters)
        
        return {
            "status": "completed",
            "funding_type": "government",
            "total_opportunities": len(mock_opportunities),
            "opportunities": mock_opportunities,
            "metadata": {
                "search_agencies": discovery_filters.get("agencies", []),
                "eligibility_types": discovery_filters.get("eligibility_types", []),
                "funding_range": discovery_filters.get("funding_range", {}),
                "note": "Government opportunity discovery will integrate with Grants.gov API"
            },
            "search_parameters": params.dict()
        }
    
    async def _discover_commercial_opportunities(
        self, 
        profile: OrganizationProfile, 
        params: ProfileSearchParams
    ) -> Dict[str, Any]:
        """Discover commercial funding opportunities (placeholder for corporate databases)"""
        
        # Commercial opportunity integration available via foundation_directory_fetch processor
        # Current status: Foundation Directory API integrated with CSR analysis
        # This would search corporate giving programs, CSR initiatives, etc.
        
        discovery_filters = params.discovery_filters
        
        # Placeholder implementation
        mock_opportunities = self._generate_mock_commercial_opportunities(profile, discovery_filters)
        
        return {
            "status": "completed",
            "funding_type": "commercial",
            "total_opportunities": len(mock_opportunities),
            "opportunities": mock_opportunities,
            "metadata": {
                "target_industries": discovery_filters.get("industries", []),
                "company_sizes": discovery_filters.get("company_sizes", []),
                "funding_range": discovery_filters.get("funding_range", {}),
                "note": "Commercial opportunity discovery will integrate with corporate databases"
            },
            "search_parameters": params.dict()
        }
    
    def _profile_params_to_workflow_config(
        self, 
        profile: OrganizationProfile, 
        params: ProfileSearchParams
    ) -> WorkflowConfig:
        """Convert profile search parameters to existing workflow configuration"""
        
        discovery_filters = params.discovery_filters
        
        # Extract geographic parameters
        geo_scope = discovery_filters.get("geographic_scope", {})
        states = geo_scope.get("states", [])
        
        # Extract NTEE codes from discovery filters
        ntee_codes = discovery_filters.get("ntee_codes", [])
        
        # Extract funding range
        funding_range = discovery_filters.get("funding_range", {})
        min_revenue = funding_range.get("min_amount", None)  # No default filter
        
        # Create workflow configuration
        config = WorkflowConfig(
            workflow_id=f"profile_discovery_{profile.profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Profile Discovery: {profile.name}",
            target_ein=profile.ein,  # Use profile EIN if available
            states=states[:5] if states else ["VA"],  # Limit to 5 states, default to VA
            ntee_codes=ntee_codes[:10] if ntee_codes else ["E21", "E30", "F30"],  # Limit NTEE codes
            min_revenue=min_revenue,
            max_results=params.max_results_per_type,
            include_classified_organizations=True,  # Include intelligent classification
            classification_score_threshold=params.min_compatibility_threshold
        )
        
        return config
    
    def _convert_workflow_results_to_profile_format(
        self, 
        workflow_state, 
        profile: OrganizationProfile,
        funding_type: FundingType
    ) -> Dict[str, Any]:
        """Convert workflow results to profile-centric opportunity format"""
        
        opportunities = []
        
        # Extract results from workflow state
        raw_results = []
        if workflow_state.processor_results:
            for processor_name, processor_result in workflow_state.processor_results.items():
                if processor_result.success and processor_result.data:
                    if isinstance(processor_result.data, dict):
                        if 'organizations' in processor_result.data:
                            raw_results.extend(processor_result.data['organizations'])
                        elif 'results' in processor_result.data:
                            raw_results.extend(processor_result.data['results'])
        
        for result in raw_results:
            opportunity = {
                "organization_name": result.get("organization_name", "Unknown"),
                "ein": result.get("ein"),
                "opportunity_type": funding_type.value,
                "description": result.get("description", "Grant-making organization"),
                "funding_amount": result.get("total_revenue"),
                "compatibility_score": result.get("composite_score", 0.0),
                "match_factors": {
                    "ntee_match": result.get("ntee_code") in profile.focus_areas,
                    "geographic_match": result.get("state") in (profile.geographic_scope.states or []),
                    "financial_fit": self._assess_financial_fit(result, profile),
                    "program_alignment": self._assess_program_alignment(result, profile)
                },
                "contact_info": {
                    "address": result.get("address"),
                    "city": result.get("city"),
                    "state": result.get("state"),
                    "zip_code": result.get("zip_code")
                },
                "metadata": {
                    "ntee_code": result.get("ntee_code"),
                    "asset_amount": result.get("asset_amount"),
                    "revenue_amount": result.get("revenue_amount"),
                    "data_source": result.get("data_source", "ProPublica"),
                    "last_filing_year": result.get("filing_year")
                },
                "pipeline_stage": PipelineStage.DISCOVERY.value,
                "discovered_at": datetime.now().isoformat()
            }
            
            opportunities.append(opportunity)
        
        # Sort by compatibility score
        opportunities.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return {
            "opportunities": opportunities,
            "metadata": {
                "total_processed": len(raw_results),
                "avg_compatibility_score": sum(o["compatibility_score"] for o in opportunities) / len(opportunities) if opportunities else 0,
                "top_matches": len([o for o in opportunities if o["compatibility_score"] > 0.7]),
                "workflow_execution": workflow_results.get("execution_summary", {})
            }
        }
    
    def _assess_financial_fit(self, result: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Assess if organization's financial capacity fits profile needs"""
        org_revenue = result.get("revenue_amount", 0)
        profile_min = profile.funding_preferences.min_amount or 0
        profile_max = profile.funding_preferences.max_amount or float('inf')
        
        # Simple heuristic: org should have 10x the requested funding in revenue
        estimated_giving_capacity = org_revenue * 0.1 if org_revenue else 0
        
        return profile_min <= estimated_giving_capacity <= profile_max * 10
    
    def _assess_program_alignment(self, result: Dict[str, Any], profile: OrganizationProfile) -> bool:
        """Assess program alignment between funder and profile"""
        # Check NTEE code alignment
        result_ntee = result.get("ntee_code", "")
        
        # Map profile focus areas to NTEE categories
        focus_ntee_categories = []
        for focus in profile.focus_areas:
            if "health" in focus.lower():
                focus_ntee_categories.extend(["E", "F"])
            elif "education" in focus.lower():
                focus_ntee_categories.extend(["B"])
            elif "community" in focus.lower():
                focus_ntee_categories.extend(["S", "P"])
            elif "environment" in focus.lower():
                focus_ntee_categories.extend(["C"])
        
        # Check if NTEE code starts with any focus category
        return any(result_ntee.startswith(cat) for cat in focus_ntee_categories)
    
    def _create_discovery_summary(
        self, 
        discovery_results: Dict[str, Any], 
        profile: OrganizationProfile
    ) -> Dict[str, Any]:
        """Create summary of discovery results across all funding types"""
        
        total_opportunities = 0
        successful_searches = 0
        failed_searches = 0
        top_matches = []
        
        for funding_type, results in discovery_results.items():
            if results.get("status") == "completed":
                successful_searches += 1
                opportunities = results.get("opportunities", [])
                total_opportunities += len(opportunities)
                
                # Collect top matches from each funding type
                top_from_type = sorted(
                    opportunities, 
                    key=lambda x: x.get("compatibility_score", 0), 
                    reverse=True
                )[:3]
                
                for opp in top_from_type:
                    opp["funding_type"] = funding_type
                    top_matches.append(opp)
                    
            else:
                failed_searches += 1
        
        # Sort top matches across all funding types
        top_matches.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)
        top_matches = top_matches[:10]  # Keep top 10 overall
        
        return {
            "total_opportunities_found": total_opportunities,
            "funding_types_searched": len(discovery_results),
            "successful_searches": successful_searches,
            "failed_searches": failed_searches,
            "top_matches": top_matches,
            "search_effectiveness": successful_searches / len(discovery_results) if discovery_results else 0,
            "average_compatibility": sum(
                match.get("compatibility_score", 0) for match in top_matches
            ) / len(top_matches) if top_matches else 0,
            "recommendations": self._generate_discovery_recommendations(discovery_results, profile)
        }
    
    def _generate_discovery_recommendations(
        self, 
        discovery_results: Dict[str, Any], 
        profile: OrganizationProfile
    ) -> List[str]:
        """Generate strategic recommendations based on discovery results"""
        
        recommendations = []
        
        # Analyze results and provide strategic guidance
        grant_results = discovery_results.get("grants", {})
        if grant_results.get("status") == "completed":
            grant_count = grant_results.get("total_opportunities", 0)
            if grant_count > 50:
                recommendations.append("Strong foundation grant opportunities found. Focus on top 20 matches for best ROI.")
            elif grant_count > 10:
                recommendations.append("Moderate foundation opportunities. Consider expanding geographic scope.")
            else:
                recommendations.append("Limited foundation matches. Review focus area keywords and expand search criteria.")
        
        # Government recommendations
        gov_results = discovery_results.get("government", {})
        if gov_results.get("status") == "completed":
            recommendations.append("Government opportunities identified. Ensure compliance readiness before applying.")
        
        # Commercial recommendations  
        commercial_results = discovery_results.get("commercial", {})
        if commercial_results.get("status") == "completed":
            recommendations.append("Corporate funding opportunities available. Develop partnership proposals highlighting mutual benefits.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Consider refining profile focus areas and expanding geographic scope for better matches.")
        
        recommendations.append("Review top matches and prioritize based on funding capacity and alignment scores.")
        
        return recommendations
    
    def _create_enhanced_discovery_summary(
        self, 
        session_summary: Dict[str, Any], 
        profile: OrganizationProfile
    ) -> Dict[str, Any]:
        """Create enhanced discovery summary using session data"""
        
        return {
            "total_opportunities_found": session_summary.get("total_results", 0),
            "funding_types_searched": session_summary.get("funding_types_searched", []),
            "results_by_funding_type": session_summary.get("results_by_funding_type", {}),
            "avg_compatibility_scores": session_summary.get("avg_compatibility_scores", {}),
            "success_rates": session_summary.get("success_rates", {}),
            "top_matches": session_summary.get("top_opportunities", [])[:10],
            "execution_metrics": {
                "execution_time_seconds": session_summary.get("execution_time_seconds", 0),
                "api_calls_made": session_summary.get("api_calls_made", 0),
                "cache_hits": session_summary.get("cache_hits", 0)
            },
            "errors": session_summary.get("errors", {}),
            "search_effectiveness": sum(session_summary.get("success_rates", {}).values()) / len(session_summary.get("success_rates", {})) if session_summary.get("success_rates") else 0,
            "recommendations": self._generate_enhanced_recommendations(session_summary, profile)
        }
    
    def _generate_enhanced_recommendations(
        self, 
        session_summary: Dict[str, Any], 
        profile: OrganizationProfile
    ) -> List[str]:
        """Generate enhanced strategic recommendations based on session results"""
        
        recommendations = []
        
        total_results = session_summary.get("total_results", 0)
        results_by_type = session_summary.get("results_by_funding_type", {})
        avg_scores = session_summary.get("avg_compatibility_scores", {})
        
        # Overall discovery effectiveness
        if total_results > 100:
            recommendations.append("Excellent discovery results! Focus on top 20% of opportunities for maximum impact.")
        elif total_results > 50:
            recommendations.append("Good discovery results. Consider expanding search criteria for additional opportunities.")
        elif total_results > 10:
            recommendations.append("Moderate results found. Review and refine profile focus areas for better targeting.")
        else:
            recommendations.append("Limited opportunities found. Consider broadening geographic scope and focus areas.")
        
        # Funding type specific recommendations
        for funding_type, count in results_by_type.items():
            avg_score = avg_scores.get(funding_type, 0)
            
            if funding_type == "grants" and count > 0:
                if avg_score > 0.7:
                    recommendations.append(f"Strong foundation matches found ({count} opportunities). Prioritize highest compatibility scores.")
                elif avg_score > 0.5:
                    recommendations.append(f"Moderate foundation alignment ({count} opportunities). Review match factors for optimization.")
                else:
                    recommendations.append(f"Foundation opportunities available ({count}) but alignment could be improved.")
            
            elif funding_type == "government" and count > 0:
                recommendations.append(f"Government opportunities identified ({count}). Ensure compliance readiness and application capacity.")
            
            elif funding_type == "commercial" and count > 0:
                recommendations.append(f"Corporate partnerships available ({count}). Develop value propositions highlighting mutual benefits.")
        
        # Success rate analysis
        success_rates = session_summary.get("success_rates", {})
        failed_types = [ft for ft, rate in success_rates.items() if rate == 0.0]
        
        if failed_types:
            recommendations.append(f"Discovery failed for {', '.join(failed_types)}. Check profile completeness and search parameters.")
        
        # Performance recommendations
        execution_time = session_summary.get("execution_time_seconds", 0)
        if execution_time > 60:
            recommendations.append("Consider narrowing search scope for faster discovery in future searches.")
        
        return recommendations
    
    async def execute_full_pipeline(
        self,
        profile_id: str,
        funding_types: Optional[List[FundingType]] = None,
        priority: ProcessingPriority = ProcessingPriority.STANDARD,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute complete 4-stage pipeline: Discovery → Pre-scoring → Deep Analysis → Recommendations
        """
        
        # Get profile
        profile = self.profile_service.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        # Use profile funding preferences if not specified
        if not funding_types:
            funding_types = profile.funding_preferences.funding_types
        
        # Create pipeline configuration
        pipeline_config = PipelineConfig(
            profile_id=profile_id,
            funding_types=funding_types,
            priority=priority,
            discovery_limit=1000,
            pre_scoring_limit=200,
            deep_analysis_limit=50,
            final_recommendations=15,
            min_compatibility_score=0.3,
            pre_scoring_threshold=0.5,
            deep_analysis_threshold=0.7
        )
        
        # Execute pipeline
        pipeline_results = await pipeline_engine.execute_pipeline(
            profile=profile,
            config=pipeline_config,
            progress_callback=progress_callback
        )
        
        # Store final recommendations as opportunity leads
        if pipeline_results.get("final_recommendations"):
            for recommendation in pipeline_results["final_recommendations"]:
                lead_data = {
                    "organization_name": recommendation.organization_name,
                    "opportunity_type": recommendation.source_type.value,
                    "program_name": recommendation.program_name,
                    "description": recommendation.description,
                    "funding_amount": recommendation.funding_amount,
                    "compatibility_score": recommendation.compatibility_score,
                    "match_factors": recommendation.match_factors,
                    "external_data": recommendation.external_data
                }
                
                # Create opportunity using database service (migrated from ProfileService)
                try:
                    opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"
                    
                    # Map pipeline stage to business stage (aligned with filtering system)
                    db_stage = "opportunities" if recommendation.external_data.get("final_rank", 999) <= 5 else "candidates"
                    
                    opportunity = Opportunity(
                        id=opportunity_id,
                        profile_id=profile_id,
                        organization_name=lead_data.get("organization_name", ""),
                        ein=lead_data.get("external_data", {}).get("ein"),
                        current_stage=db_stage,
                        scoring={"overall_score": lead_data.get("compatibility_score", 0.0)},
                        analysis={"match_factors": lead_data.get("match_factors", {})},
                        source="workflow_integration",
                        opportunity_type=lead_data.get("opportunity_type", "grants"),
                        description=lead_data.get("description"),
                        funding_amount=lead_data.get("funding_amount"),
                        program_name=lead_data.get("program_name"),
                        discovered_at=datetime.now(),
                        last_updated=datetime.now(),
                        status="active"
                    )
                    
                    if not self.database_service.create_opportunity(opportunity):
                        print(f"Warning: Failed to save workflow opportunity {opportunity_id} to database")
                        
                except Exception as create_error:
                    print(f"Error creating workflow opportunity: {create_error}")
                    # Continue processing other opportunities
        
        return {
            "pipeline_id": pipeline_results["pipeline_id"],
            "profile_id": profile_id,
            "profile_name": profile.name,
            "pipeline_status": pipeline_results["status"],
            "stage_results": [
                {
                    "stage": result.stage.value,
                    "opportunities_in": result.opportunities_in,
                    "opportunities_out": result.opportunities_out,
                    "processing_time_seconds": result.processing_time_seconds,
                    "success": result.success,
                    "error": result.error
                }
                for result in pipeline_results["stage_results"]
            ],
            "final_recommendations": len(pipeline_results.get("final_recommendations", [])),
            "pipeline_metrics": pipeline_results.get("pipeline_metrics", {}),
            "total_processing_time": pipeline_results.get("total_processing_time", 0),
            "funding_types_processed": [ft.value for ft in funding_types]
        }
    
    # Mock data generators for placeholder implementations
    
    def _generate_mock_government_opportunities(
        self, 
        profile: OrganizationProfile, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate mock government opportunities for demonstration"""
        
        mock_opportunities = []
        agencies = filters.get("agencies", ["HHS", "ED", "EPA"])
        
        for i, agency in enumerate(agencies[:5]):  # Limit to 5 mock opportunities
            opportunity = {
                "organization_name": f"Department of {agency}",
                "program_name": f"{agency} Community Innovation Grant Program",
                "opportunity_type": "government",
                "description": f"Federal grant program supporting {', '.join(profile.focus_areas)} initiatives",
                "funding_amount": 500000,
                "application_deadline": "2024-03-15",
                "compatibility_score": 0.8 - (i * 0.1),
                "match_factors": {
                    "agency_alignment": True,
                    "eligibility_match": True,
                    "geographic_eligible": True,
                    "focus_alignment": True
                },
                "requirements": {
                    "eligibility": filters.get("eligibility_types", []),
                    "matching_funds": "25% match required",
                    "reporting": "Quarterly progress reports"
                },
                "contact_info": {
                    "agency": agency,
                    "program_officer": f"Program Officer {i+1}",
                    "email": f"grants@{agency.lower()}.gov"
                },
                "metadata": {
                    "cfda_number": f"93.{100+i:03d}",
                    "funding_source": "federal",
                    "award_type": "cooperative_agreement"
                },
                "pipeline_stage": PipelineStage.DISCOVERY.value,
                "discovered_at": datetime.now().isoformat()
            }
            
            mock_opportunities.append(opportunity)
        
        return mock_opportunities
    
    def _generate_mock_commercial_opportunities(
        self, 
        profile: OrganizationProfile, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate mock commercial opportunities for demonstration"""
        
        mock_companies = [
            {"name": "TechCorp Foundation", "industry": "technology", "size": "large"},
            {"name": "HealthCare Partners", "industry": "healthcare", "size": "large"},
            {"name": "Community Bank Giving", "industry": "financial", "size": "medium"},
            {"name": "GreenEnergy CSR Program", "industry": "energy", "size": "large"}
        ]
        
        mock_opportunities = []
        
        for i, company in enumerate(mock_companies):
            opportunity = {
                "organization_name": company["name"],
                "program_name": f"{company['name']} Community Impact Grant",
                "opportunity_type": "commercial",
                "description": f"Corporate giving program supporting {', '.join(profile.focus_areas)} in local communities",
                "funding_amount": 100000,
                "application_deadline": "Rolling basis",
                "compatibility_score": 0.7 - (i * 0.1),
                "match_factors": {
                    "industry_alignment": True,
                    "csr_focus_match": True,
                    "geographic_presence": True,
                    "partnership_potential": True
                },
                "requirements": {
                    "partnership_type": "Grant with recognition opportunities",
                    "reporting": "Annual impact report",
                    "branding": "Co-branding opportunities available"
                },
                "contact_info": {
                    "company": company["name"],
                    "contact_person": f"CSR Manager {i+1}",
                    "email": f"giving@{company['name'].lower().replace(' ', '')}.com"
                },
                "metadata": {
                    "industry": company["industry"],
                    "company_size": company["size"],
                    "funding_type": "corporate_giving"
                },
                "pipeline_stage": PipelineStage.DISCOVERY.value,
                "discovered_at": datetime.now().isoformat()
            }
            
            mock_opportunities.append(opportunity)
        
        return mock_opportunities
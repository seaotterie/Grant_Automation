"""
Unified Opportunity Service
Replaces the dual leads/opportunities system with a single unified architecture
"""

import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from .models import (
    UnifiedOpportunity, 
    OpportunityLead, 
    StageTransition, 
    ScoringResult, 
    StageAnalysis, 
    UserAssessment, 
    PromotionEvent,
    PipelineStage,
    FundingType
)

logger = logging.getLogger(__name__)


class UnifiedOpportunityService:
    """
    Unified service for managing opportunities with backward compatibility.
    Replaces the dual leads/opportunities architecture with a single format.
    """
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize the unified opportunity service"""
        self.data_dir = Path(data_dir)
        self.opportunities_dir = self.data_dir / "opportunities"
        self.leads_dir = self.data_dir / "leads"  # For migration compatibility
        
        # Create directories
        self.opportunities_dir.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # CORE OPPORTUNITY MANAGEMENT
    # ============================================================================
    
    def create_opportunity(self, profile_id: str, opportunity_data: Dict[str, Any]) -> Optional[UnifiedOpportunity]:
        """
        Create a new unified opportunity directly.
        This replaces add_opportunity_lead() with rich format from creation.
        """
        try:
            # Check for duplicates
            existing_opportunities = self.get_profile_opportunities(profile_id)
            org_name = opportunity_data.get("organization_name", "").strip().lower()
            
            for existing in existing_opportunities:
                if existing.organization_name.strip().lower() == org_name:
                    # Update existing if new has better score
                    new_score = opportunity_data.get("compatibility_score", 0.0)
                    existing_score = existing.scoring.overall_score if existing.scoring else 0.0
                    
                    if new_score > existing_score:
                        return self._update_opportunity_score(existing, opportunity_data)
                    return existing
            
            # Generate opportunity ID
            opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"
            
            # Create initial stage transition
            now = datetime.now().isoformat()
            stage = opportunity_data.get("pipeline_stage", "discovery")
            if hasattr(stage, 'value'):
                stage = stage.value
                
            stage_history = [StageTransition(
                stage=stage,
                entered_at=now,
                exited_at=None,
                duration_hours=None
            )]
            
            # Create initial analysis
            analysis = {
                stage: StageAnalysis(
                    match_factors=opportunity_data.get("match_factors", {}),
                    risk_factors=opportunity_data.get("risk_factors", {}),
                    recommendations=opportunity_data.get("recommendations", []),
                    network_insights=opportunity_data.get("network_insights", {}),
                    analyzed_at=now,
                    source=opportunity_data.get("source"),
                    opportunity_type=opportunity_data.get("opportunity_type", "grants")
                )
            }
            
            # Create scoring result
            scoring = ScoringResult(
                overall_score=opportunity_data.get("compatibility_score", 0.0),
                auto_promotion_eligible=False,
                promotion_recommended=False,
                dimension_scores={},
                confidence_level=None,
                scored_at=now,
                scorer_version="1.0.0"
            )
            
            # Create unified opportunity
            opportunity = UnifiedOpportunity(
                opportunity_id=opportunity_id,
                profile_id=profile_id,
                organization_name=opportunity_data.get("organization_name", ""),
                ein=opportunity_data.get("external_data", {}).get("ein"),
                current_stage=stage,
                stage_history=stage_history,
                scoring=scoring,
                analysis=analysis,
                user_assessment=None,
                promotion_history=[],
                source=opportunity_data.get("source"),
                opportunity_type=opportunity_data.get("opportunity_type", "grants"),
                discovered_at=now,
                last_updated=now,
                status="active",
                legacy_lead_id=opportunity_data.get("lead_id"),  # For migration
                description=opportunity_data.get("description"),
                funding_amount=opportunity_data.get("funding_amount"),
                program_name=opportunity_data.get("program_name")
            )
            
            # Save opportunity
            self._save_opportunity(opportunity)
            
            logger.info(f"Created unified opportunity {opportunity_id} for profile {profile_id}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to create opportunity for profile {profile_id}: {e}")
            return None
    
    def get_profile_opportunities(
        self, 
        profile_id: str, 
        stage: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> List[UnifiedOpportunity]:
        """Get all opportunities for a profile with optional filtering"""
        try:
            opportunities = []
            
            # Load opportunities from unified format
            for opp_file in self.opportunities_dir.glob(f"profile_{profile_id}_opportunity_*.json"):
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    opportunity = UnifiedOpportunity(**data)
                    
                    # Apply filters
                    if stage and opportunity.current_stage != stage:
                        continue
                    
                    if min_score and opportunity.scoring:
                        if opportunity.scoring.overall_score < min_score:
                            continue
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    logger.warning(f"Error loading opportunity file {opp_file}: {e}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to get opportunities for profile {profile_id}: {e}")
            return []
    
    def get_opportunity(self, opportunity_id: str, profile_id: str) -> Optional[UnifiedOpportunity]:
        """Get a specific opportunity"""
        try:
            opp_file = self.opportunities_dir / f"profile_{profile_id}_opportunity_{opportunity_id.replace('opp_', '')}.json"
            
            if not opp_file.exists():
                return None
            
            with open(opp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return UnifiedOpportunity(**data)
            
        except Exception as e:
            logger.error(f"Failed to get opportunity {opportunity_id}: {e}")
            return None
    
    def update_opportunity_stage(
        self, 
        opportunity_id: str, 
        profile_id: str, 
        new_stage: str,
        reason: str = "Manual stage update"
    ) -> bool:
        """Update opportunity stage with full audit trail"""
        try:
            opportunity = self.get_opportunity(opportunity_id, profile_id)
            if not opportunity:
                return False
            
            old_stage = opportunity.current_stage
            now = datetime.now().isoformat()
            
            # Close current stage
            if opportunity.stage_history:
                current_transition = opportunity.stage_history[-1]
                if not current_transition.exited_at:
                    current_transition.exited_at = now
                    if current_transition.entered_at:
                        entered = datetime.fromisoformat(current_transition.entered_at)
                        current = datetime.now()
                        current_transition.duration_hours = (current - entered).total_seconds() / 3600
            
            # Add new stage transition
            new_transition = StageTransition(
                stage=new_stage,
                entered_at=now,
                exited_at=None,
                duration_hours=None
            )
            opportunity.stage_history.append(new_transition)
            opportunity.current_stage = new_stage
            
            # Add promotion event
            promotion_event = PromotionEvent(
                from_stage=old_stage,
                to_stage=new_stage,
                decision_type="manual_promotion",
                score_at_promotion=opportunity.scoring.overall_score if opportunity.scoring else 0.0,
                reason=reason,
                promoted_at=now
            )
            opportunity.promotion_history.append(promotion_event)
            
            opportunity.last_updated = now
            
            # Save updated opportunity
            self._save_opportunity(opportunity)
            
            logger.info(f"Updated opportunity {opportunity_id} stage: {old_stage} → {new_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update opportunity stage {opportunity_id}: {e}")
            return False
    
    def delete_opportunity(self, opportunity_id: str, profile_id: str) -> bool:
        """Delete an opportunity"""
        try:
            opp_file = self.opportunities_dir / f"profile_{profile_id}_opportunity_{opportunity_id.replace('opp_', '')}.json"
            
            if opp_file.exists():
                opp_file.unlink()
                logger.info(f"Deleted opportunity {opportunity_id} for profile {profile_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete opportunity {opportunity_id}: {e}")
            return False
    
    # ============================================================================
    # BACKWARD COMPATIBILITY METHODS
    # ============================================================================
    
    def add_opportunity_lead(self, profile_id: str, lead_data: Dict[str, Any]) -> Optional[OpportunityLead]:
        """
        Backward compatibility method - creates unified opportunity but returns lead format
        """
        # Create unified opportunity
        opportunity = self.create_opportunity(profile_id, lead_data)
        
        if not opportunity:
            return None
        
        # Convert back to lead format for backward compatibility
        return self._opportunity_to_lead(opportunity)
    
    def get_profile_leads(
        self, 
        profile_id: str, 
        stage: Optional[PipelineStage] = None,
        min_score: Optional[float] = None
    ) -> List[OpportunityLead]:
        """
        Backward compatibility method - returns opportunities as leads
        """
        stage_str = stage.value if stage else None
        opportunities = self.get_profile_opportunities(profile_id, stage_str, min_score)
        
        return [self._opportunity_to_lead(opp) for opp in opportunities]
    
    def delete_lead(self, lead_id: str, profile_id: str) -> bool:
        """
        Backward compatibility method - deletes by lead ID
        """
        # Try to find opportunity by legacy_lead_id
        opportunities = self.get_profile_opportunities(profile_id)
        
        for opp in opportunities:
            if opp.legacy_lead_id == lead_id:
                return self.delete_opportunity(opp.opportunity_id, profile_id)
        
        return False
    
    # ============================================================================
    # MIGRATION UTILITIES
    # ============================================================================
    
    def migrate_lead_to_opportunity(self, lead_file: Path) -> Optional[UnifiedOpportunity]:
        """
        Migrate a lead file to unified opportunity format
        """
        try:
            with open(lead_file, 'r', encoding='utf-8') as f:
                lead_data = json.load(f)
            
            # Convert lead data to opportunity creation format
            opportunity_data = {
                "lead_id": lead_data.get("lead_id"),
                "organization_name": lead_data.get("organization_name", ""),
                "source": lead_data.get("source", ""),
                "opportunity_type": lead_data.get("opportunity_type", "grants"),
                "description": lead_data.get("description"),
                "funding_amount": lead_data.get("funding_amount"),
                "program_name": lead_data.get("program_name"),
                "pipeline_stage": lead_data.get("pipeline_stage", "discovery"),
                "compatibility_score": lead_data.get("compatibility_score", 0.0),
                "match_factors": lead_data.get("match_factors", {}),
                "risk_factors": lead_data.get("risk_factors", {}),
                "recommendations": lead_data.get("recommendations", []),
                "network_insights": lead_data.get("network_insights", {}),
                "external_data": lead_data.get("external_data", {})
            }
            
            profile_id = lead_data.get("profile_id")
            opportunity = self.create_opportunity(profile_id, opportunity_data)
            
            if opportunity:
                logger.info(f"Migrated lead {lead_data.get('lead_id')} to opportunity {opportunity.opportunity_id}")
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to migrate lead file {lead_file}: {e}")
            return None
    
    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================
    
    def _save_opportunity(self, opportunity: UnifiedOpportunity):
        """Save opportunity to file"""
        try:
            opp_file = self.opportunities_dir / f"profile_{opportunity.profile_id}_opportunity_{opportunity.opportunity_id.replace('opp_', '')}.json"
            logger.info(f"Attempting to save opportunity to: {opp_file}")
            
            # Ensure directory exists
            self.opportunities_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Opportunities directory confirmed: {self.opportunities_dir}")
            
            # Serialize opportunity data
            opportunity_data = opportunity.model_dump()
            logger.info(f"Successfully serialized opportunity data for {opportunity.organization_name}")
            
            # Write to file
            with open(opp_file, 'w', encoding='utf-8') as f:
                json.dump(opportunity_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved opportunity file: {opp_file}")
            
            # Verify file was created
            if opp_file.exists():
                file_size = opp_file.stat().st_size
                logger.info(f"Opportunity file verified: {file_size} bytes")
            else:
                logger.error(f"Opportunity file was not created: {opp_file}")
                
        except Exception as save_error:
            logger.error(f"Failed to save opportunity {opportunity.opportunity_id}: {save_error}")
            import traceback
            logger.error(f"Save opportunity traceback: {traceback.format_exc()}")
            raise
    
    def _update_opportunity_score(self, existing: UnifiedOpportunity, new_data: Dict[str, Any]) -> UnifiedOpportunity:
        """Update existing opportunity with better scoring data"""
        new_score = new_data.get("compatibility_score", 0.0)
        
        # Update scoring
        if existing.scoring:
            existing.scoring.overall_score = new_score
            existing.scoring.scored_at = datetime.now().isoformat()
        
        # Update analysis for current stage
        current_stage = existing.current_stage
        if current_stage in existing.analysis:
            stage_analysis = existing.analysis[current_stage]
            stage_analysis.match_factors.update(new_data.get("match_factors", {}))
            stage_analysis.analyzed_at = datetime.now().isoformat()
        
        existing.last_updated = datetime.now().isoformat()
        
        self._save_opportunity(existing)
        return existing
    
    def _opportunity_to_lead(self, opportunity: UnifiedOpportunity) -> OpportunityLead:
        """Convert UnifiedOpportunity to OpportunityLead for backward compatibility"""
        # Get the discovery stage analysis
        discovery_analysis = opportunity.analysis.get("discovery", StageAnalysis())
        
        # Convert pipeline stage
        pipeline_stage = PipelineStage.DISCOVERY
        try:
            pipeline_stage = PipelineStage(opportunity.current_stage)
        except ValueError:
            pass
        
        # Convert funding type
        funding_type = FundingType.GRANTS
        try:
            funding_type = FundingType(opportunity.opportunity_type)
        except ValueError:
            pass
        
        return OpportunityLead(
            lead_id=opportunity.legacy_lead_id or opportunity.opportunity_id,
            profile_id=opportunity.profile_id,
            source=opportunity.source or "Unknown",
            opportunity_type=funding_type,
            organization_name=opportunity.organization_name,
            program_name=opportunity.program_name,
            description=opportunity.description,
            funding_amount=opportunity.funding_amount,
            pipeline_stage=pipeline_stage,
            compatibility_score=opportunity.scoring.overall_score if opportunity.scoring else None,
            success_probability=None,
            match_factors=discovery_analysis.match_factors,
            risk_factors=discovery_analysis.risk_factors,
            recommendations=discovery_analysis.recommendations,
            board_connections=[],  # Not in unified format
            network_insights=discovery_analysis.network_insights,
            approach_strategy=None,  # Not in unified format
            discovered_at=datetime.fromisoformat(opportunity.discovered_at) if opportunity.discovered_at else datetime.now(),
            last_analyzed=datetime.fromisoformat(opportunity.last_updated) if opportunity.last_updated else None,
            status=opportunity.status,
            assigned_to=None,  # Not in unified format
            external_data={"ein": opportunity.ein} if opportunity.ein else {}
        )
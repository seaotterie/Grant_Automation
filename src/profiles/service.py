"""
Profile management service for CRUD operations and business logic
"""
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


from .models import (
    OrganizationProfile, 
    OpportunityLead, 
    UnifiedOpportunity,
    ProfileSearchParams,
    ProfileStatus,
    PipelineStage,
    DiscoverySession
)


class ProfileService:
    """Service for managing organization profiles"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize profile service with data directory"""
        self.data_dir = Path(data_dir)
        self.profiles_dir = self.data_dir / "profiles"
        self.leads_dir = self.data_dir / "leads"
        self.sessions_dir = self.data_dir / "sessions"
        
        # Create directories if they don't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.leads_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # Profile CRUD Operations
    
    def create_profile(self, profile_data: Dict[str, Any]) -> OrganizationProfile:
        """Create new organization profile"""
        # Generate unique profile ID
        profile_id = f"profile_{uuid.uuid4().hex[:12]}"
        
        # Create profile with generated ID
        profile_data['profile_id'] = profile_id
        profile = OrganizationProfile(**profile_data)
        
        # Save to storage
        self._save_profile(profile)
        
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[OrganizationProfile]:
        """Get profile by ID"""
        profile_file = self.profiles_dir / f"{profile_id}.json"
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return OrganizationProfile(**data)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def update_profile(self, profile_id: str, update_data: Dict[str, Any]) -> Optional[OrganizationProfile]:
        """Update existing profile"""
        profile = self.get_profile(profile_id)
        
        if not profile:
            return None
        
        # Update fields
        profile_dict = profile.model_dump()
        profile_dict.update(update_data)
        profile_dict['updated_at'] = datetime.now()
        
        # Validate updated profile
        updated_profile = OrganizationProfile(**profile_dict)
        
        # Save changes
        self._save_profile(updated_profile)
        
        return updated_profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete profile (marks as archived)"""
        profile = self.get_profile(profile_id)
        
        if not profile:
            return False
        
        # Archive instead of delete
        profile.status = ProfileStatus.ARCHIVED
        self._save_profile(profile)
        
        return True
    
    def list_profiles(
        self, 
        status: Optional[ProfileStatus] = None,
        organization_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[OrganizationProfile]:
        """List profiles with optional filtering"""
        profiles = []
        
        # Load all profile files
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                profile = OrganizationProfile(**data)
                
                # Apply filters
                if status and profile.status != status:
                    continue
                if organization_type and profile.organization_type != organization_type:
                    continue
                
                profiles.append(profile)
                
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by updated_at descending
        profiles.sort(key=lambda p: p.updated_at, reverse=True)
        
        # Apply pagination
        if offset > 0:
            profiles = profiles[offset:]
        if limit:
            profiles = profiles[:limit]
        
        return profiles
    
    # Profile Templates
    
    def create_template(self, template_data: Dict[str, Any], template_name: str) -> OrganizationProfile:
        """Create profile template"""
        template_id = f"template_{template_name.lower().replace(' ', '_')}"
        
        template_data.update({
            'profile_id': template_id,
            'name': f"Template: {template_name}",
            'status': ProfileStatus.TEMPLATE
        })
        
        template = OrganizationProfile(**template_data)
        self._save_profile(template)
        
        return template
    
    def create_from_template(self, template_id: str, profile_data: Dict[str, Any]) -> Optional[OrganizationProfile]:
        """Create new profile from template"""
        template = self.get_profile(template_id)
        
        if not template or template.status != ProfileStatus.TEMPLATE:
            return None
        
        # Start with template data
        new_profile_data = template.model_dump()
        
        # Override with provided data
        new_profile_data.update(profile_data)
        
        # Reset profile-specific fields
        new_profile_data['status'] = ProfileStatus.DRAFT
        new_profile_data['created_at'] = datetime.now()
        new_profile_data['updated_at'] = datetime.now()
        
        return self.create_profile(new_profile_data)
    
    # Opportunity Lead Management
    
    def add_opportunity_lead(self, profile_id: str, lead_data: Dict[str, Any]) -> Optional[OpportunityLead]:
        """Add opportunity lead to profile with deduplication"""
        # Verify profile exists
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Check for duplicate opportunities based on organization name and funding amount
        existing_leads = self.get_profile_leads(profile_id)
        org_name = lead_data.get("organization_name", "").strip().lower()
        funding_amount = lead_data.get("funding_amount", 0)
        
        for existing_lead in existing_leads:
            existing_org = existing_lead.organization_name.strip().lower()
            existing_amount = existing_lead.funding_amount or 0
            
            # Check for duplicate based on organization name and funding amount
            if existing_org == org_name and existing_amount == funding_amount:
                # Update the existing lead with new data if it has better score
                new_score = lead_data.get("compatibility_score", 0.0)
                if new_score > (existing_lead.compatibility_score or 0.0):
                    # Update existing lead with better data
                    existing_lead.compatibility_score = new_score
                    existing_lead.match_factors.update(lead_data.get("match_factors", {}))
                    existing_lead.external_data.update(lead_data.get("external_data", {}))
                    existing_lead.last_analyzed = datetime.now()
                    self._save_lead(existing_lead)
                return existing_lead
        
        # Generate lead ID
        lead_id = f"lead_{uuid.uuid4().hex[:12]}"
        
        lead_data.update({
            'lead_id': lead_id,
            'profile_id': profile_id
        })
        
        lead = OpportunityLead(**lead_data)
        
        # Save lead
        self._save_lead(lead)
        
        # Update profile opportunities count
        profile.opportunities_count = len(self.get_profile_leads(profile_id))
        if lead_id not in profile.associated_opportunities:
            profile.associated_opportunities.append(lead_id)
        profile.last_discovery_date = datetime.now()
        profile.discovery_status = "completed"
        
        # Save updated profile
        self.update_profile(profile_id, profile)
        
        return lead
    
    def get_profile_leads(
        self, 
        profile_id: str, 
        stage: Optional[PipelineStage] = None,
        min_score: Optional[float] = None
    ) -> List[OpportunityLead]:
        """Get all leads for a profile"""
        leads = []
        
        # Load all lead files for this profile
        for lead_file in self.leads_dir.glob(f"*_{profile_id}_*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                lead = OpportunityLead(**data)
                
                # Apply filters
                if stage and lead.pipeline_stage != stage:
                    continue
                if min_score and (not lead.compatibility_score or lead.compatibility_score < min_score):
                    continue
                
                leads.append(lead)
                
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by compatibility score descending
        leads.sort(key=lambda l: l.compatibility_score or 0, reverse=True)
        
        return leads
    
    def update_lead_stage(self, lead_id: str, new_stage: PipelineStage, analysis_data: Optional[Dict] = None) -> bool:
        """Update lead pipeline stage with optional analysis data"""
        lead = self._get_lead(lead_id)
        
        if not lead:
            return False
        
        lead.pipeline_stage = new_stage
        lead.last_analyzed = datetime.now()
        
        if analysis_data:
            lead.match_factors.update(analysis_data.get('match_factors', {}))
            lead.risk_factors.update(analysis_data.get('risk_factors', {}))
            lead.recommendations.extend(analysis_data.get('recommendations', []))
            lead.network_insights.update(analysis_data.get('network_insights', {}))
            
            if 'compatibility_score' in analysis_data:
                lead.compatibility_score = analysis_data['compatibility_score']
            if 'success_probability' in analysis_data:
                lead.success_probability = analysis_data['success_probability']
            if 'approach_strategy' in analysis_data:
                lead.approach_strategy = analysis_data['approach_strategy']
        
        self._save_lead(lead)
        return True
    
    # Analytics and Reporting
    
    def get_profile_analytics(self, profile_id: str) -> Dict[str, Any]:
        """Get analytics for a specific profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return {}
        
        leads = self.get_profile_leads(profile_id)
        
        # Calculate metrics
        total_leads = len(leads)
        stage_counts = {}
        avg_compatibility = 0
        
        for stage in PipelineStage:
            stage_leads = [l for l in leads if l.pipeline_stage == stage]
            stage_counts[stage.value] = len(stage_leads)
        
        if leads:
            scored_leads = [l for l in leads if l.compatibility_score is not None]
            if scored_leads:
                avg_compatibility = sum(l.compatibility_score for l in scored_leads) / len(scored_leads)
        
        return {
            'profile_id': profile_id,
            'profile_name': profile.name,
            'total_opportunities': total_leads,
            'pipeline_distribution': stage_counts,
            'average_compatibility_score': round(avg_compatibility, 3),
            'last_updated': profile.updated_at.isoformat(),
            'focus_areas': profile.focus_areas,
            'funding_types': [ft.value for ft in profile.funding_preferences.funding_types]
        }
    
    # Private helper methods
    
    def _save_profile(self, profile: OrganizationProfile):
        """Save profile to storage"""
        profile_file = self.profiles_dir / f"{profile.profile_id}.json"
        
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, indent=2, default=str, ensure_ascii=False)
    
    def _save_lead(self, lead: OpportunityLead):
        """Save lead to storage"""
        lead_file = self.leads_dir / f"{lead.lead_id}_{lead.profile_id}_{lead.pipeline_stage.value}.json"
        
        with open(lead_file, 'w', encoding='utf-8') as f:
            json.dump(lead.model_dump(), f, indent=2, default=str, ensure_ascii=False)
    
    def _get_lead(self, lead_id: str):
        """Get lead by ID - returns either OpportunityLead or UnifiedOpportunity"""
        # First try legacy lead files (pattern includes lead_id)
        for lead_file in self.leads_dir.glob(f"{lead_id}_*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return OpportunityLead(**data)
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Try new opportunity file format - check profile directories in parent
        profiles_root = self.data_dir  # data/profiles
        for profile_dir in profiles_root.iterdir():
            if profile_dir.is_dir() and profile_dir.name.startswith('profile_'):
                opportunities_dir = profile_dir / 'opportunities'
                if opportunities_dir.exists():
                    # Handle opportunity_id format (e.g. "opp_test_result_001" or "opp_lead_c721929257b6")
                    if lead_id.startswith('opp_lead_'):
                        # Remove "opp_lead_" prefix for legacy format
                        opportunity_id = lead_id[9:]  # Remove "opp_lead_" prefix
                        opportunity_file = opportunities_dir / f'opportunity_{opportunity_id}.json'
                    elif lead_id.startswith('opp_'):
                        # Remove "opp_" prefix for standard format
                        opportunity_id = lead_id[4:]  # Remove "opp_" prefix
                        opportunity_file = opportunities_dir / f'opportunity_{opportunity_id}.json'
                    else:
                        opportunity_file = opportunities_dir / f'opportunity_{lead_id}.json'
                    
                    if opportunity_file.exists():
                        try:
                            with open(opportunity_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            # Try UnifiedOpportunity first (new format)
                            return UnifiedOpportunity(**data)
                        except (json.JSONDecodeError, ValueError):
                            continue
                        except Exception:
                            # Fallback to OpportunityLead if UnifiedOpportunity fails
                            try:
                                with open(opportunity_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                return OpportunityLead(**data)
                            except:
                                continue
        
        return None
    
    def delete_lead(self, lead_id: str, profile_id: str) -> bool:
        """Delete a specific lead/opportunity"""
        try:
            # Get the lead first to verify it exists
            lead = self._get_lead(lead_id)
            if not lead:
                return False
            
            # Remove lead from profile's associated opportunities (if field exists)
            profile = self.get_profile(profile_id)
            if profile and hasattr(profile, 'associated_opportunities') and lead_id in profile.associated_opportunities:
                profile.associated_opportunities.remove(lead_id)
                self._save_profile(profile)
            
            # Remove legacy lead file(s)
            deleted_files = 0
            for lead_file in self.leads_dir.glob(f"{lead_id}_*.json"):
                try:
                    lead_file.unlink()
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"Failed to delete lead file {lead_file}: {e}")
            
            # Remove new opportunity file format
            profile_dir = self.data_dir / profile_id
            opportunities_dir = profile_dir / 'opportunities'
            if opportunities_dir.exists():
                # Handle opportunity_id format (e.g. "opp_test_result_001" or "opp_lead_c721929257b6")
                if lead_id.startswith('opp_lead_'):
                    # Remove "opp_lead_" prefix for legacy format
                    opportunity_id = lead_id[9:]  # Remove "opp_lead_" prefix
                    opportunity_file = opportunities_dir / f'opportunity_{opportunity_id}.json'
                elif lead_id.startswith('opp_'):
                    # Remove "opp_" prefix for standard format
                    opportunity_id = lead_id[4:]  # Remove "opp_" prefix
                    opportunity_file = opportunities_dir / f'opportunity_{opportunity_id}.json'
                else:
                    opportunity_file = opportunities_dir / f'opportunity_{lead_id}.json'
                
                if opportunity_file.exists():
                    try:
                        opportunity_file.unlink()
                        deleted_files += 1
                        logger.info(f"Deleted opportunity file: {opportunity_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete opportunity file {opportunity_file}: {e}")
            
            logger.info(f"Deleted lead {lead_id} for profile {profile_id}: {deleted_files} files removed")
            return deleted_files > 0
            
        except Exception as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            return False
    
    # Discovery Session Management
    
    def start_discovery_session(self, profile_id: str, tracks: List[str] = None) -> Optional[DiscoverySession]:
        """Start a new discovery session for a profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Generate session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        session = DiscoverySession(
            session_id=session_id,
            profile_id=profile_id,
            tracks_executed=tracks or []
        )
        
        # Update profile discovery status
        profile.discovery_status = "in_progress"
        self._save_profile(profile)
        
        # Save session
        self._save_session(session)
        
        return session
    
    def complete_discovery_session(
        self, 
        session_id: str, 
        opportunities_found: Dict[str, int] = None,
        total_opportunities: int = 0,
        execution_time: int = None,
        error_messages: List[str] = None
    ) -> bool:
        """Complete a discovery session and update profile"""
        session = self._get_session(session_id)
        if not session:
            return False
        
        # Update session
        session.completed_at = datetime.now()
        session.status = "completed"
        session.opportunities_found = opportunities_found or {}
        session.total_opportunities = total_opportunities
        session.execution_time_seconds = execution_time
        session.error_messages = error_messages or []
        
        # Update profile discovery tracking
        profile = self.get_profile(session.profile_id)
        if profile:
            profile.last_discovery_date = datetime.now()
            profile.discovery_count += 1
            profile.discovery_status = "completed"
            profile.opportunities_count = total_opportunities
            
            # Calculate next recommended discovery (30 days from now)
            from datetime import timedelta
            profile.next_recommended_discovery = datetime.now() + timedelta(days=30)
            
            self._save_profile(profile)
        
        self._save_session(session)
        return True
    
    def fail_discovery_session(self, session_id: str, error_messages: List[str]) -> bool:
        """Mark discovery session as failed"""
        session = self._get_session(session_id)
        if not session:
            return False
        
        session.completed_at = datetime.now()
        session.status = "failed"
        session.error_messages = error_messages
        
        # Update profile status
        profile = self.get_profile(session.profile_id)
        if profile:
            profile.discovery_status = "failed"
            self._save_profile(profile)
        
        self._save_session(session)
        return True
    
    def get_profile_sessions(self, profile_id: str, limit: Optional[int] = None) -> List[DiscoverySession]:
        """Get discovery sessions for a profile"""
        sessions = []
        
        # Load session files for this profile
        for session_file in self.sessions_dir.glob(f"*_{profile_id}_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                session = DiscoverySession(**data)
                sessions.append(session)
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by start time descending
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def get_discovery_analytics(self, profile_id: str) -> Dict[str, Any]:
        """Get discovery analytics for a profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return {}
        
        sessions = self.get_profile_sessions(profile_id)
        
        completed_sessions = [s for s in sessions if s.status == "completed"]
        total_opportunities = sum(s.total_opportunities for s in completed_sessions)
        avg_execution_time = 0
        
        if completed_sessions:
            execution_times = [s.execution_time_seconds for s in completed_sessions if s.execution_time_seconds]
            if execution_times:
                avg_execution_time = sum(execution_times) // len(execution_times)
        
        return {
            "profile_id": profile_id,
            "discovery_status": profile.discovery_status,
            "last_discovery": profile.last_discovery_date.isoformat() if profile.last_discovery_date else None,
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "failed_sessions": len([s for s in sessions if s.status == "failed"]),
            "total_opportunities_found": total_opportunities,
            "avg_execution_time_seconds": avg_execution_time,
            "next_recommended": profile.next_recommended_discovery.isoformat() if profile.next_recommended_discovery else None,
            "needs_update": profile.discovery_status == "needs_update" or (
                profile.next_recommended_discovery and 
                profile.next_recommended_discovery < datetime.now()
            )
        }
    
    def add_discovery_session(self, session: DiscoverySession) -> bool:
        """Add a completed discovery session to storage"""
        try:
            self._save_session(session)
            return True
        except Exception as e:
            logger.error(f"Error saving discovery session: {e}")
            return False
    
    # Private helper methods for sessions
    
    def _save_session(self, session: DiscoverySession):
        """Save discovery session to storage"""
        session_file = self.sessions_dir / f"{session.session_id}_{session.profile_id}_{session.started_at.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(), f, indent=2, default=str, ensure_ascii=False)
    
    def _get_session(self, session_id: str) -> Optional[DiscoverySession]:
        """Get session by ID"""
        for session_file in self.sessions_dir.glob(f"{session_id}_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return DiscoverySession(**data)
            except (json.JSONDecodeError, ValueError):
                continue
        
        return None


# Singleton instance
_profile_service = None

def get_profile_service() -> ProfileService:
    """Get singleton instance of profile service"""
    global _profile_service
    if _profile_service is None:
        _profile_service = ProfileService()
    return _profile_service
"""
Profile management service for CRUD operations and business logic
"""
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    OrganizationProfile, 
    OpportunityLead, 
    ProfileSearchParams,
    ProfileStatus,
    PipelineStage
)


class ProfileService:
    """Service for managing organization profiles"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize profile service with data directory"""
        self.data_dir = Path(data_dir)
        self.profiles_dir = self.data_dir / "profiles"
        self.leads_dir = self.data_dir / "leads"
        
        # Create directories if they don't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.leads_dir.mkdir(parents=True, exist_ok=True)
    
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
        profile_dict = profile.dict()
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
        new_profile_data = template.dict()
        
        # Override with provided data
        new_profile_data.update(profile_data)
        
        # Reset profile-specific fields
        new_profile_data['status'] = ProfileStatus.DRAFT
        new_profile_data['created_at'] = datetime.now()
        new_profile_data['updated_at'] = datetime.now()
        
        return self.create_profile(new_profile_data)
    
    # Opportunity Lead Management
    
    def add_opportunity_lead(self, profile_id: str, lead_data: Dict[str, Any]) -> Optional[OpportunityLead]:
        """Add opportunity lead to profile"""
        # Verify profile exists
        if not self.get_profile(profile_id):
            return None
        
        # Generate lead ID
        lead_id = f"lead_{uuid.uuid4().hex[:12]}"
        
        lead_data.update({
            'lead_id': lead_id,
            'profile_id': profile_id
        })
        
        lead = OpportunityLead(**lead_data)
        
        # Save lead
        self._save_lead(lead)
        
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
            json.dump(profile.dict(), f, indent=2, default=str, ensure_ascii=False)
    
    def _save_lead(self, lead: OpportunityLead):
        """Save lead to storage"""
        lead_file = self.leads_dir / f"{lead.lead_id}_{lead.profile_id}_{lead.pipeline_stage.value}.json"
        
        with open(lead_file, 'w', encoding='utf-8') as f:
            json.dump(lead.dict(), f, indent=2, default=str, ensure_ascii=False)
    
    def _get_lead(self, lead_id: str) -> Optional[OpportunityLead]:
        """Get lead by ID"""
        # Find lead file (pattern includes lead_id)
        for lead_file in self.leads_dir.glob(f"{lead_id}_*.json"):
            try:
                with open(lead_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return OpportunityLead(**data)
            except (json.JSONDecodeError, ValueError):
                continue
        
        return None
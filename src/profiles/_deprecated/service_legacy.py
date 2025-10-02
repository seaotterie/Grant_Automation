"""
Profile management service for CRUD operations and business logic
"""
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import time
import os
import threading
from contextlib import contextmanager

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
from .unified_opportunity_service import UnifiedOpportunityService


class ProfileService:
    """Service for managing organization profiles"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize profile service with data directory"""
        self.data_dir = Path(data_dir)
        self.profiles_dir = self.data_dir / "profiles"
        self.leads_dir = self.data_dir / "leads"
        self.sessions_dir = self.data_dir / "sessions"
        self.locks_dir = self.data_dir / "locks"
        
        # Create directories if they don't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.leads_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize unified opportunity service
        self.opportunity_service = UnifiedOpportunityService(str(self.data_dir))
        
        # Thread locks for in-process synchronization
        self._profile_locks = {}
        self._locks_lock = threading.Lock()
    
    # Session Locking Methods
    
    @contextmanager
    def _acquire_discovery_lock(self, profile_id: str, timeout: int = 30):
        """
        Acquire a discovery lock for a profile to prevent race conditions.
        Uses both file-based locking (for cross-process) and thread locks (for in-process).
        """
        lock_file = self.locks_dir / f"{profile_id}_discovery.lock"
        thread_lock = None
        file_lock = None
        
        try:
            # Get or create thread lock for this profile
            with self._locks_lock:
                if profile_id not in self._profile_locks:
                    self._profile_locks[profile_id] = threading.Lock()
                thread_lock = self._profile_locks[profile_id]
            
            # Acquire thread lock first (for in-process synchronization)
            if not thread_lock.acquire(timeout=timeout):
                raise TimeoutError(f"Failed to acquire thread lock for profile {profile_id} within {timeout} seconds")
            
            # Acquire file lock (for cross-process synchronization)
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Try to create lock file atomically
                    file_lock = open(lock_file, 'x')  # 'x' mode fails if file exists
                    # Replace colons with underscores for Windows filename compatibility
                    timestamp = datetime.now().isoformat().replace(':', '_')
                    file_lock.write(f"locked_by_pid:{os.getpid()}_time:{timestamp}\n")
                    file_lock.flush()
                    logger.info(f"Acquired discovery lock for profile {profile_id}")
                    break
                except FileExistsError:
                    # Lock file exists, check if it's stale
                    if self._is_stale_lock(lock_file):
                        logger.warning(f"Removing stale lock file: {lock_file}")
                        try:
                            lock_file.unlink()
                            continue
                        except FileNotFoundError:
                            continue  # Another process removed it
                    
                    # Wait a bit before retrying
                    time.sleep(0.1)
            else:
                thread_lock.release()
                raise TimeoutError(f"Failed to acquire file lock for profile {profile_id} within {timeout} seconds")
            
            yield
            
        finally:
            # Release file lock
            if file_lock:
                try:
                    file_lock.close()
                    lock_file.unlink()
                    logger.info(f"Released discovery lock for profile {profile_id}")
                except Exception as e:
                    logger.warning(f"Error releasing file lock for profile {profile_id}: {e}")
            
            # Release thread lock
            if thread_lock:
                thread_lock.release()
    
    def _is_stale_lock(self, lock_file: Path, max_age_minutes: int = 30) -> bool:
        """Check if a lock file is stale (older than max_age_minutes)"""
        try:
            if not lock_file.exists():
                return False
                
            # Check file age
            file_age = time.time() - lock_file.stat().st_mtime
            if file_age > max_age_minutes * 60:
                return True
            
            # Check if the PID in the lock file is still running (Unix-like systems)
            try:
                with open(lock_file, 'r') as f:
                    content = f.read().strip()
                if content.startswith("locked_by_pid:"):
                    pid_str = content.split("_time:")[0].split(":")[1]
                    pid = int(pid_str)
                    
                    # On Windows, this will raise an exception for non-existent PIDs
                    # On Unix, we can check /proc/{pid} but for simplicity, we'll rely on age
                    if os.name == 'nt':  # Windows
                        # For Windows, we mainly rely on file age
                        return file_age > 5 * 60  # 5 minutes for Windows
                    else:  # Unix-like
                        try:
                            os.kill(pid, 0)  # Check if process exists
                            return False  # Process exists, lock is not stale
                        except ProcessLookupError:
                            return True  # Process doesn't exist, lock is stale
                        except PermissionError:
                            return False  # Process exists but we can't signal it
                            
            except (ValueError, IndexError, FileNotFoundError):
                # If we can't parse the lock file, consider it stale if it's old enough
                return file_age > max_age_minutes * 60
                
        except Exception as e:
            logger.warning(f"Error checking if lock file is stale: {e}")
            return False
        
        return False
    
    def is_discovery_in_progress(self, profile_id: str) -> bool:
        """Check if discovery is currently in progress for a profile"""
        lock_file = self.locks_dir / f"{profile_id}_discovery.lock"
        
        # Check for file lock first
        if lock_file.exists() and not self._is_stale_lock(lock_file):
            logger.debug(f"Discovery in progress due to active lock file: {lock_file}")
            return True
        
        # Check for active sessions (this is the most reliable indicator)
        active_sessions = [s for s in self.get_profile_sessions(profile_id, limit=10) 
                         if s.status == "in_progress"]
        
        if active_sessions:
            logger.debug(f"Discovery in progress due to {len(active_sessions)} active sessions")
            return True
        
        # Check profile status only as final fallback
        profile = self.get_profile(profile_id)
        if profile and profile.discovery_status == "in_progress":
            # Profile says in progress but no active sessions - this is likely stale
            logger.warning(f"Profile {profile_id} shows discovery_status='in_progress' but no active sessions found - likely stale")
            # Reset the status since we have no active sessions
            profile.discovery_status = "completed"
            self._save_profile(profile)
            return False
        
        return False
    
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
        """
        Add opportunity lead to profile with deduplication (uses unified opportunity service)
        DEPRECATED: Main endpoints now use DatabaseManager directly. Consider migrating legacy code.
        """
        # Verify profile exists
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Use unified opportunity service (returns lead format for backward compatibility)
        lead = self.opportunity_service.add_opportunity_lead(profile_id, lead_data)
        
        if lead:
            # Update profile opportunities count and metadata
            profile.opportunities_count = len(self.get_profile_leads(profile_id))
            if lead.lead_id not in profile.associated_opportunities:
                profile.associated_opportunities.append(lead.lead_id)
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
        """Get all leads for a profile (uses unified opportunity service)"""
        # Use unified opportunity service with backward compatibility
        leads = self.opportunity_service.get_profile_leads(profile_id, stage, min_score)
        
        # Sort by compatibility score descending
        leads.sort(key=lambda l: l.compatibility_score or 0, reverse=True)
        
        return leads
    
    def update_lead_stage(self, lead_id: str, new_stage: PipelineStage, analysis_data: Optional[Dict] = None) -> bool:
        """Update lead pipeline stage with optional analysis data (uses unified opportunity service)"""
        # Find the profile ID for this lead (required for unified service)
        profile_id = None
        for profile in self.list_profiles():
            if lead_id in getattr(profile, 'associated_opportunities', []):
                profile_id = profile.profile_id
                break
        
        if not profile_id:
            return False
        
        stage_str = new_stage.value if hasattr(new_stage, 'value') else str(new_stage)
        reason = "Stage updated via ProfileService"
        if analysis_data:
            reason = f"Stage updated with analysis data: {', '.join(analysis_data.keys())}"
        
        # Use unified opportunity service
        return self.opportunity_service.update_opportunity_stage(
            lead_id, profile_id, stage_str, reason
        )
    
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
    
    def save_profile(self, profile: OrganizationProfile):
        """Public method to save profile to storage"""
        return self._save_profile(profile)
    
    # Private helper methods
    
    def _save_profile(self, profile: OrganizationProfile):
        """Save profile to storage"""
        profile_file = self.profiles_dir / f"{profile.profile_id}.json"
        
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, indent=2, default=str, ensure_ascii=False)
    
    # Legacy _save_lead method removed - now handled by UnifiedOpportunityService
    
    # Legacy _get_lead method removed - now handled by UnifiedOpportunityService
    
    def delete_lead(self, lead_id: str, profile_id: str) -> bool:
        """Delete a specific lead/opportunity (uses unified opportunity service)"""
        try:
            # Remove lead from profile's associated opportunities
            profile = self.get_profile(profile_id)
            if profile and hasattr(profile, 'associated_opportunities') and lead_id in profile.associated_opportunities:
                profile.associated_opportunities.remove(lead_id)
                self._save_profile(profile)
            
            # Use unified opportunity service for deletion
            success = self.opportunity_service.delete_lead(lead_id, profile_id)
            
            if success:
                logger.info(f"Deleted lead {lead_id} for profile {profile_id} via unified service")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            return False
    
    # Discovery Session Management
    
    def start_discovery_session(self, profile_id: str, tracks: List[str] = None) -> Optional[DiscoverySession]:
        """Start a new discovery session for a profile with locking to prevent race conditions"""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        try:
            # Acquire discovery lock to prevent race conditions
            with self._acquire_discovery_lock(profile_id, timeout=10):
                # Double-check that no discovery is in progress after acquiring lock
                # Note: we skip lock file check since we just created the lock file ourselves
                active_sessions = [s for s in self.get_profile_sessions(profile_id, limit=10) 
                                 if s.status == "in_progress"]
                
                # Mark any existing in-progress sessions as failed (these should be rare/abandoned)
                for session in active_sessions:
                    logger.warning(f"Marking abandoned session {session.session_id} as failed")
                    self.fail_discovery_session(session.session_id, 
                                               ["Session abandoned - new session started"])
                
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
                
                logger.info(f"Started discovery session {session_id} for profile {profile_id}")
                return session
                
        except TimeoutError as e:
            logger.error(f"Failed to acquire discovery lock for profile {profile_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error starting discovery session for profile {profile_id}: {e}")
            return None
    
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
            
            # Clean up any stale lock files after completion
            self._cleanup_stale_locks(session.profile_id)
        
        self._save_session(session)
        logger.info(f"Completed discovery session {session_id} for profile {session.profile_id}")
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
            
            # Clean up any stale lock files after failure
            self._cleanup_stale_locks(session.profile_id)
        
        self._save_session(session)
        logger.info(f"Failed discovery session {session_id} for profile {session.profile_id}")
        return True
    
    def _cleanup_stale_locks(self, profile_id: str):
        """Clean up stale lock files for a profile"""
        try:
            lock_file = self.locks_dir / f"{profile_id}_discovery.lock"
            if lock_file.exists() and self._is_stale_lock(lock_file, max_age_minutes=1):
                lock_file.unlink()
                logger.info(f"Cleaned up stale lock file for profile {profile_id}")
        except Exception as e:
            logger.warning(f"Error cleaning up stale lock for profile {profile_id}: {e}")
    
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
"""
Unified Profile Service for Simplified Architecture

Handles the new unified architecture with:
- Profile directories: data/profiles/profile_id/
- Single profile.json with embedded analytics
- Individual opportunity files in opportunities/ subdirectory
- Single source of truth per opportunity with complete lifecycle data
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    UnifiedProfile, UnifiedOpportunity, ProfileAnalytics,
    PipelineStage, ScoringResult, StageAnalysis, UserAssessment,
    PromotionEvent, StageTransition, RecentActivity, DiscoverySession
)
import uuid

logger = logging.getLogger(__name__)


class UnifiedProfileService:
    """Simplified profile service for unified architecture"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize with unified data directory structure"""
        self.data_dir = Path(data_dir)
        
        # Ensure base directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # PROFILE OPERATIONS
    # ============================================================================
    
    def get_profile(self, profile_id: str) -> Optional[UnifiedProfile]:
        """Get profile with real-time analytics (from database for backward compatibility)"""
        import sqlite3

        try:
            # Read from SQLite database (backward compatibility)
            # Use absolute path relative to project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "data", "catalynx.db")
            logger.info(f"[GET_PROFILE] Looking up profile_id={profile_id} in {db_path}")

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM profiles WHERE id = ?"
            logger.info(f"[GET_PROFILE] Executing query: {query} with params: {(profile_id,)}")

            cursor.execute(query, (profile_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"[GET_PROFILE] Profile {profile_id} not found in database")
                # Debug: List all profile IDs to help diagnose
                cursor.execute("SELECT id, name FROM profiles LIMIT 10")
                all_profiles = cursor.fetchall()
                logger.warning(f"[GET_PROFILE] Available profiles (first 10): {[(r['id'], r['name']) for r in all_profiles]}")
                conn.close()
                return None

            logger.info(f"[GET_PROFILE] Found profile: id={row['id']}, name={row['name']}")

            # Convert to UnifiedProfile model with mapped field names
            try:
                profile_data = {
                    'profile_id': row['id'],
                    'organization_name': row['name'],
                    'ein': row['ein'],
                    'website_url': row['website_url'],
                    'organization_type': row['organization_type'],
                    'ntee_codes': json.loads(row['ntee_codes']) if row['ntee_codes'] else [],
                    'ntee_code_990': row['ntee_code_990'],
                    'focus_areas': json.loads(row['focus_areas']) if row['focus_areas'] else [],
                    'geographic_scope': json.loads(row['geographic_scope']) if row['geographic_scope'] else {},
                    'government_criteria': json.loads(row['government_criteria']) if row['government_criteria'] else [],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'status': row['status'] or 'active',
                    'discovery_status': None,
                    'last_discovery_at': row['last_discovery_date'],
                    'analytics': {
                        'opportunity_count': row['opportunities_count'] or 0,
                        'stages_distribution': {},
                        'scoring_stats': {},
                        'discovery_stats': {},
                        'promotion_stats': {}
                    },
                    'recent_activity': [],
                    'tags': [],
                    'notes': None,
                    'web_enhanced_data': json.loads(row['web_enhanced_data']) if row['web_enhanced_data'] else None
                }

                logger.info(f"[GET_PROFILE] Profile data prepared: {list(profile_data.keys())}")
                unified_profile = UnifiedProfile(**profile_data)
                logger.info(f"[GET_PROFILE] UnifiedProfile created successfully for {profile_id}")

                conn.close()
                return unified_profile

            except Exception as conversion_error:
                logger.error(f"[GET_PROFILE] Error converting row to UnifiedProfile: {conversion_error}", exc_info=True)
                logger.error(f"[GET_PROFILE] Row keys: {list(row.keys())}")
                conn.close()
                raise

        except Exception as e:
            logger.error(f"[GET_PROFILE] Error loading profile {profile_id} from database: {e}", exc_info=True)
            return None
    
    def save_profile(self, profile: UnifiedProfile) -> bool:
        """Save profile to database (primary storage) with upsert logic"""
        try:
            from src.database.database_manager import DatabaseManager, Profile as DBProfile

            # Update timestamp
            profile.updated_at = datetime.now().isoformat()

            # Convert UnifiedProfile to DatabaseManager Profile model
            db_profile = DBProfile(
                id=profile.profile_id,
                name=profile.organization_name,
                organization_type=profile.organization_type,
                ein=profile.ein,
                website_url=getattr(profile, 'website_url', None),
                mission_statement=getattr(profile, 'mission_statement', None),
                status=profile.status or 'active',
                keywords=getattr(profile, 'keywords', None),
                focus_areas=profile.focus_areas,
                program_areas=getattr(profile, 'program_areas', None),
                target_populations=getattr(profile, 'target_populations', None),
                ntee_codes=profile.ntee_codes,
                ntee_code_990=getattr(profile, 'ntee_code_990', None),
                government_criteria=profile.government_criteria if isinstance(profile.government_criteria, list) else None,
                geographic_scope=profile.geographic_scope,
                service_areas=getattr(profile, 'service_areas', None),
                funding_preferences=getattr(profile, 'funding_preferences', None),
                annual_revenue=getattr(profile, 'annual_revenue', None),
                form_type=getattr(profile, 'form_type', None),
                foundation_grants=getattr(profile, 'foundation_grants', None),
                board_members=getattr(profile, 'board_members', None),
                discovery_count=getattr(profile, 'discovery_count', 0),
                opportunities_count=profile.analytics.opportunity_count if profile.analytics else 0,
                last_discovery_date=profile.last_discovery_at,
                performance_metrics=getattr(profile, 'performance_metrics', None),
                created_at=profile.created_at,
                updated_at=profile.updated_at,
                processing_history=getattr(profile, 'processing_history', None),
                verification_data=getattr(profile, 'verification_data', None),
                web_enhanced_data=getattr(profile, 'web_enhanced_data', None)
            )

            # Save to database with upsert logic
            db_manager = DatabaseManager("data/catalynx.db")

            # Check if profile exists
            existing = db_manager.get_profile(profile.profile_id)

            if existing:
                # Update existing profile
                success = db_manager.update_profile(db_profile)
                action = "updated"
            else:
                # Create new profile
                success = db_manager.create_profile(db_profile)
                action = "created"

            if success:
                logger.info(f"Profile {profile.profile_id} {action} in database successfully")
            else:
                logger.error(f"Failed to {action} profile {profile.profile_id} in database")

            return success

        except Exception as e:
            logger.error(f"Error saving profile {profile.profile_id}: {e}", exc_info=True)
            return False
    
    def list_profiles(self, limit: int = 50, offset: int = 0, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available profiles with pagination and search.

        Args:
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip
            search: Search term for name/EIN

        Returns:
            List of profile dictionaries
        """
        import sqlite3

        profiles = []

        try:
            # Read from SQLite database (backward compatibility)
            db_path = "data/catalynx.db"
            logger.info(f"[LIST_PROFILES] Reading from database: {db_path}")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()

            # Build query with optional search
            query = "SELECT * FROM profiles WHERE status != 'deleted'"
            params = []

            if search:
                query += " AND (name LIKE ? OR ein LIKE ? OR id LIKE ?)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            query += " ORDER BY name LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert to dictionaries with mapped field names
            for row in rows:
                profile = {
                    'profile_id': row['id'],
                    'name': row['name'],  # Backward compatibility with frontend
                    'organization_name': row['name'],
                    'ein': row['ein'],
                    'website_url': row['website_url'],
                    'organization_type': row['organization_type'],
                    'ntee_codes': json.loads(row['ntee_codes']) if row['ntee_codes'] else [],
                    'ntee_code_990': row['ntee_code_990'],
                    'focus_areas': json.loads(row['focus_areas']) if row['focus_areas'] else [],
                    'geographic_scope': json.loads(row['geographic_scope']) if row['geographic_scope'] else {},
                    'government_criteria': json.loads(row['government_criteria']) if row['government_criteria'] else [],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'status': row['status'] or 'active',
                    'discovery_status': None,
                    'last_discovery_at': row['last_discovery_date'],
                    'analytics': {
                        'opportunity_count': row['opportunities_count'] or 0,
                        'stages_distribution': {},
                        'scoring_stats': {},
                        'discovery_stats': {},
                        'promotion_stats': {}
                    },
                    'recent_activity': [],
                    'tags': [],
                    'notes': None
                }
                profiles.append(profile)

            conn.close()
            return profiles

        except Exception as e:
            logger.error(f"Error listing profiles from database: {e}")
            return []

    def create_profile(self, profile: UnifiedProfile) -> bool:
        """
        Create a new profile (alias for save_profile for API consistency).

        Args:
            profile: UnifiedProfile object to create

        Returns:
            True if successful, False otherwise
        """
        return self.save_profile(profile)

    def update_profile(self, profile: UnifiedProfile) -> bool:
        """
        Update an existing profile.

        Args:
            profile: UnifiedProfile object with updated data

        Returns:
            True if successful, False otherwise
        """
        # Check if profile exists
        existing = self.get_profile(profile.profile_id)
        if not existing:
            logger.warning(f"Cannot update non-existent profile {profile.profile_id}")
            return False

        # Update timestamp
        profile.updated_at = datetime.now().isoformat()

        return self.save_profile(profile)

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a profile from database (primary storage).

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            from src.database.database_manager import DatabaseManager

            # Delete from database
            db_manager = DatabaseManager("data/catalynx.db")
            success = db_manager.delete_profile(profile_id)

            if success:
                logger.info(f"Profile {profile_id} deleted from database successfully")
            else:
                logger.warning(f"Profile {profile_id} not found in database for deletion")

                # Debug: List existing profiles to help diagnose the issue
                try:
                    import sqlite3
                    conn = sqlite3.connect("data/catalynx.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name FROM profiles LIMIT 10")
                    existing_profiles = cursor.fetchall()
                    logger.warning(f"Existing profiles in database (first 10): {[(p[0], p[1]) for p in existing_profiles]}")
                    conn.close()
                except Exception as debug_error:
                    logger.error(f"Failed to list existing profiles for debugging: {debug_error}")

            return success

        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False

    def get_profile_analytics(self, profile_id: str) -> Dict[str, Any]:
        """
        Get consolidated analytics for a profile.

        Combines:
        - Profile metrics (opportunities by stage, success rates)
        - Funnel data (conversion rates, timeline)
        - Session information (discovery sessions, recent activity)

        Args:
            profile_id: Profile ID

        Returns:
            Dictionary with consolidated analytics
        """
        try:
            profile = self.get_profile(profile_id)
            if not profile:
                return {}

            # Get all opportunities for this profile
            opportunities = self.get_profile_opportunities(profile_id)

            # Calculate stage distribution
            stage_distribution = {}
            for opp in opportunities:
                stage = opp.current_stage or 'DISCOVER'
                stage_distribution[stage] = stage_distribution.get(stage, 0) + 1

            # Calculate conversion metrics
            total_opps = len(opportunities)
            approach_stage = sum(1 for o in opportunities if o.current_stage == 'APPROACH')
            conversion_rate = (approach_stage / total_opps * 100) if total_opps > 0 else 0

            # Get recent activity
            recent_updates = sorted(
                opportunities,
                key=lambda o: o.last_updated or '',
                reverse=True
            )[:10]

            return {
                "total_opportunities": total_opps,
                "stage_distribution": stage_distribution,
                "conversion_rate": conversion_rate,
                "recent_activity": [
                    {
                        "opportunity_id": o.opportunity_id,
                        "name": o.organization_name,
                        "stage": o.current_stage,
                        "last_updated": o.last_updated
                    }
                    for o in recent_updates
                ],
                "analytics": profile.analytics.model_dump() if profile.analytics else {},
                "created_at": profile.created_at,
                "updated_at": profile.updated_at
            }

        except Exception as e:
            logger.error(f"Error getting analytics for profile {profile_id}: {e}")
            return {}

    # ============================================================================
    # OPPORTUNITY OPERATIONS
    # ============================================================================
    
    def get_opportunity(self, profile_id: str, opportunity_id: str) -> Optional[UnifiedOpportunity]:
        """Get single opportunity by ID"""
        opportunities_dir = self.data_dir / profile_id / "opportunities"
        
        # Try different possible filename formats to handle legacy naming
        clean_id = opportunity_id.replace('opp_', '').replace('lead_', '')
        possible_files = [
            opportunities_dir / f"{opportunity_id}.json",
            opportunities_dir / f"opportunity_{opportunity_id}.json",
            opportunities_dir / f"opportunity_{clean_id}.json",
            opportunities_dir / f"{clean_id}.json"
        ]
        
        for opp_file in possible_files:
            if opp_file.exists():
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    return UnifiedOpportunity(**data)
                    
                except Exception as e:
                    logger.error(f"Error loading opportunity {opportunity_id}: {e}")
                    continue
        
        logger.warning(f"Opportunity {opportunity_id} not found for profile {profile_id}")
        return None
    
    def save_opportunity(self, profile_id: str, opportunity: UnifiedOpportunity) -> bool:
        """Save opportunity to storage"""
        try:
            opportunities_dir = self.data_dir / profile_id / "opportunities"
            opportunities_dir.mkdir(parents=True, exist_ok=True)
            
            # Use consistent filename format
            opp_file = opportunities_dir / f"opportunity_{opportunity.opportunity_id.replace('opp_', '').replace('lead_', '')}.json"
            
            # Update timestamp
            opportunity.last_updated = datetime.now().isoformat()
            
            # Save opportunity
            with open(opp_file, 'w', encoding='utf-8') as f:
                json.dump(opportunity.model_dump(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Opportunity {opportunity.opportunity_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving opportunity {opportunity.opportunity_id}: {e}")
            return False
    
    def get_profile_opportunities(self, profile_id: str, stage_filter: Optional[str] = None) -> List[UnifiedOpportunity]:
        """Get all opportunities for a profile, optionally filtered by stage"""
        opportunities_dir = self.data_dir / profile_id / "opportunities"
        
        if not opportunities_dir.exists():
            logger.info(f"No opportunities directory for profile {profile_id}")
            return []
        
        opportunities = []
        
        try:
            for opp_file in opportunities_dir.glob("opportunity_*.json"):
                try:
                    with open(opp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    opportunity = UnifiedOpportunity(**data)
                    
                    # Apply stage filter if specified
                    if stage_filter is None or opportunity.current_stage == stage_filter:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    logger.error(f"Error loading {opp_file}: {e}")
                    continue
            
            # Sort by discovery date (newest first)
            opportunities.sort(
                key=lambda x: x.discovered_at or "1900-01-01", 
                reverse=True
            )
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error getting opportunities for {profile_id}: {e}")
            return []

    # ============================================================================
    # DISCOVERY SESSION MANAGEMENT - NO LOCKING NEEDED
    # ============================================================================

    def start_discovery_session(
        self,
        profile_id: str,
        tracks: List[str] = None,
        session_params: Dict[str, Any] = None
    ) -> Optional[str]:
        """Start a new discovery session (no locking - single user app)"""
        try:
            # Check for active sessions (no locking needed)
            active_sessions = self.get_profile_sessions(profile_id, status_filter="in_progress")

            if active_sessions:
                logger.warning(f"Profile {profile_id} has {len(active_sessions)} active sessions")
                # Mark as failed (abandoned in single-user app)
                for session in active_sessions:
                    self.fail_discovery_session(
                        session.session_id,
                        errors=["Session abandoned - new session started"]
                    )

            # Create new session
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            now = datetime.now()

            session = DiscoverySession(
                session_id=session_id,
                profile_id=profile_id,
                started_at=now,
                status="in_progress",
                tracks_executed=tracks or []
            )

            # Save session
            sessions_dir = self.data_dir / profile_id / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            session_file = sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                # Use model_dump with mode='json' to serialize datetime
                json.dump(session.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

            # Update profile discovery status
            profile = self.get_profile(profile_id)
            if profile:
                profile.discovery_status = "in_progress"
                profile.last_discovery_at = now.isoformat()
                self.save_profile(profile)

            logger.info(f"Started discovery session {session_id} for profile {profile_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error starting discovery session: {e}")
            return None

    def complete_discovery_session(
        self,
        session_id: str,
        opportunities_found: Dict[str, int] = None,
        total_opportunities: int = 0
    ) -> bool:
        """Mark discovery session as completed"""
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False

            # Update session
            now = datetime.now()
            session.status = "completed"
            session.completed_at = now
            session.total_opportunities = total_opportunities
            if opportunities_found:
                session.opportunities_found = opportunities_found

            # Calculate duration
            if session.started_at:
                duration = (now - session.started_at).total_seconds()
                session.execution_time_seconds = int(duration)

            # Save session
            sessions_dir = self.data_dir / session.profile_id / "sessions"
            session_file = sessions_dir / f"{session_id}.json"

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

            # Update profile
            profile = self.get_profile(session.profile_id)
            if profile:
                profile.discovery_status = "completed"
                profile.last_discovery_at = now.isoformat()
                self.save_profile(profile)

            logger.info(f"Completed discovery session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error completing discovery session: {e}")
            return False

    def fail_discovery_session(
        self,
        session_id: str,
        errors: List[str] = None
    ) -> bool:
        """Mark discovery session as failed"""
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False

            # Update session
            now = datetime.now()
            session.status = "failed"
            session.completed_at = now
            session.error_messages = errors or []

            # Calculate duration
            if session.started_at:
                duration = (now - session.started_at).total_seconds()
                session.execution_time_seconds = int(duration)

            # Save session
            sessions_dir = self.data_dir / session.profile_id / "sessions"
            session_file = sessions_dir / f"{session_id}.json"

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

            # Update profile
            profile = self.get_profile(session.profile_id)
            if profile:
                profile.discovery_status = "failed"
                profile.last_discovery_at = now.isoformat()
                self.save_profile(profile)

            logger.info(f"Failed discovery session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error failing discovery session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[DiscoverySession]:
        """Get single discovery session by ID"""
        try:
            # Search all profiles for the session
            for profile_dir in self.data_dir.iterdir():
                if not profile_dir.is_dir():
                    continue

                sessions_dir = profile_dir / "sessions"
                if not sessions_dir.exists():
                    continue

                session_file = sessions_dir / f"{session_id}.json"
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return DiscoverySession(**data)

            return None

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    def get_profile_sessions(
        self,
        profile_id: str,
        status_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[DiscoverySession]:
        """Get discovery sessions for a profile"""
        try:
            sessions_dir = self.data_dir / profile_id / "sessions"
            if not sessions_dir.exists():
                return []

            sessions = []

            for session_file in sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    session = DiscoverySession(**data)

                    # Apply status filter
                    if status_filter is None or session.status == status_filter:
                        sessions.append(session)

                except Exception as e:
                    logger.error(f"Error loading session {session_file}: {e}")
                    continue

            # Sort by started_at (newest first)
            sessions.sort(
                key=lambda x: x.started_at or "1900-01-01",
                reverse=True
            )

            return sessions[:limit]

        except Exception as e:
            logger.error(f"Error getting sessions for profile {profile_id}: {e}")
            return []

    # ============================================================================
    # STAGE MANAGEMENT - SINGLE SOURCE OF TRUTH
    # ============================================================================
    
    def update_opportunity_stage(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        new_stage: str,
        reason: str = "Stage update",
        promoted_by: str = "system"
    ) -> bool:
        """Update opportunity stage - atomic operation with history tracking"""
        
        try:
            # Get current opportunity
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                logger.error(f"Opportunity {opportunity_id} not found for stage update")
                return False
            
            old_stage = opportunity.current_stage
            
            # Don't update if already in target stage
            if old_stage == new_stage:
                logger.info(f"Opportunity {opportunity_id} already in stage {new_stage}")
                return True
            
            # Update current stage
            opportunity.current_stage = new_stage
            
            # Add stage transition to history
            now = datetime.now().isoformat()
            
            # Close previous stage if exists
            if opportunity.stage_history:
                last_stage = opportunity.stage_history[-1]
                if not last_stage.exited_at:
                    last_stage.exited_at = now
                    
                    # Calculate duration
                    if last_stage.entered_at:
                        try:
                            entered = datetime.fromisoformat(last_stage.entered_at.replace('Z', '+00:00'))
                            exited = datetime.fromisoformat(now.replace('Z', '+00:00'))
                            last_stage.duration_hours = (exited - entered).total_seconds() / 3600
                        except:
                            pass
            
            # Add new stage transition
            new_transition = StageTransition(
                stage=new_stage,
                entered_at=now,
                exited_at=None,
                duration_hours=None
            )
            opportunity.stage_history.append(new_transition)
            
            # Add to promotion history
            promotion_event = PromotionEvent(
                from_stage=old_stage,
                to_stage=new_stage,
                decision_type="stage_update",
                score_at_promotion=opportunity.scoring.overall_score if opportunity.scoring else 0.0,
                reason=reason,
                promoted_at=now,
                promoted_by=promoted_by
            )
            opportunity.promotion_history.append(promotion_event)
            
            # Save updated opportunity
            success = self.save_opportunity(profile_id, opportunity)
            
            if success:
                # Refresh profile analytics
                self.refresh_profile_analytics(profile_id)
                logger.info(f"Updated opportunity {opportunity_id}: {old_stage} → {new_stage}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating opportunity stage: {e}")
            return False
    
    # ============================================================================
    # SCORING OPERATIONS
    # ============================================================================
    
    def update_opportunity_score(
        self, 
        profile_id: str, 
        opportunity_id: str, 
        scoring_result: Dict[str, Any],
        force_rescore: bool = False
    ) -> bool:
        """Update opportunity scoring - cached unless forced"""
        
        try:
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                return False
            
            # Check if re-scoring is needed
            if not force_rescore and opportunity.scoring:
                logger.info(f"Using cached score for {opportunity_id}")
                return True
            
            # Create/update scoring result
            scoring = ScoringResult(
                overall_score=scoring_result.get('overall_score', 0.0),
                auto_promotion_eligible=scoring_result.get('auto_promotion_eligible', False),
                promotion_recommended=scoring_result.get('promotion_recommended', False),
                dimension_scores=scoring_result.get('dimension_scores', {}),
                confidence_level=scoring_result.get('confidence_level'),
                scored_at=datetime.now().isoformat(),
                scorer_version=scoring_result.get('scorer_version', '1.0.0')
            )
            
            opportunity.scoring = scoring
            
            # Save updated opportunity
            success = self.save_opportunity(profile_id, opportunity)
            
            if success:
                # Refresh profile analytics
                self.refresh_profile_analytics(profile_id)
                logger.info(f"Updated scoring for {opportunity_id}: {scoring.overall_score:.3f}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating opportunity score: {e}")
            return False
    
    def update_user_assessment(
        self,
        profile_id: str,
        opportunity_id: str,
        assessment: Dict[str, Any]
    ) -> bool:
        """Update user assessment - persistent across sessions"""
        
        try:
            opportunity = self.get_opportunity(profile_id, opportunity_id)
            if not opportunity:
                return False
            
            # Create/update user assessment
            user_assessment = UserAssessment(
                user_rating=assessment.get('user_rating'),
                priority_level=assessment.get('priority_level'),
                assessment_notes=assessment.get('assessment_notes'),
                tags=assessment.get('tags', []),
                last_assessed_at=datetime.now().isoformat()
            )
            
            opportunity.user_assessment = user_assessment
            
            # Save updated opportunity
            return self.save_opportunity(profile_id, opportunity)
            
        except Exception as e:
            logger.error(f"Error updating user assessment: {e}")
            return False
    
    # ============================================================================
    # ANALYTICS OPERATIONS
    # ============================================================================
    
    def refresh_profile_analytics(self, profile_id: str) -> bool:
        """Recompute profile analytics from current opportunities"""
        
        try:
            # Get all opportunities
            opportunities = self.get_profile_opportunities(profile_id)
            
            # Compute analytics
            analytics = self._compute_analytics(opportunities)
            
            # Get and update profile
            profile = self.get_profile(profile_id)
            if not profile:
                logger.error(f"Profile {profile_id} not found for analytics refresh")
                return False
            
            profile.analytics = analytics
            profile.recent_activity = self._generate_recent_activity(opportunities)
            
            # Save updated profile
            return self.save_profile(profile)
            
        except Exception as e:
            logger.error(f"Error refreshing analytics for {profile_id}: {e}")
            return False
    
    def _compute_analytics(self, opportunities: List[UnifiedOpportunity]) -> ProfileAnalytics:
        """Compute analytics from opportunities"""
        
        if not opportunities:
            return ProfileAnalytics()
        
        # Stage distribution
        stages_dist = {}
        for opp in opportunities:
            stage = opp.current_stage
            stages_dist[stage] = stages_dist.get(stage, 0) + 1
        
        # Scoring statistics
        scores = [opp.scoring.overall_score for opp in opportunities if opp.scoring]
        high_potential_count = len([s for s in scores if s >= 0.80])
        auto_promotion_eligible = len([opp for opp in opportunities 
                                     if opp.scoring and opp.scoring.auto_promotion_eligible])
        
        scoring_stats = {
            'avg_score': round(sum(scores) / len(scores), 3) if scores else 0.0,
            'high_potential_count': high_potential_count,
            'auto_promotion_eligible': auto_promotion_eligible,
            'last_scored': max((opp.scoring.scored_at for opp in opportunities 
                               if opp.scoring and opp.scoring.scored_at), default=None)
        }
        
        # Discovery statistics  
        discovery_dates = set()
        for opp in opportunities:
            if opp.discovered_at:
                date = opp.discovered_at[:10]  # Just date part
                discovery_dates.add(date)
        
        last_discovery = max((opp.discovered_at for opp in opportunities if opp.discovered_at), default=None)
        last_session_results = len([opp for opp in opportunities 
                                   if opp.discovered_at and opp.discovered_at.startswith(last_discovery[:10])]) if last_discovery else 0
        
        discovery_stats = {
            'total_sessions': len(discovery_dates),
            'last_discovery': last_discovery,
            'last_session_results': last_session_results,
            'avg_results_per_session': len(opportunities) / max(len(discovery_dates), 1)
        }
        
        # Promotion statistics
        total_promotions = sum(len(opp.promotion_history) for opp in opportunities)
        auto_promotions = sum(1 for opp in opportunities for promo in opp.promotion_history 
                             if promo.decision_type == 'auto_promote')
        
        promotion_stats = {
            'total_promotions': total_promotions,
            'auto_promotions': auto_promotions,
            'manual_promotions': total_promotions - auto_promotions,
            'promotion_rate': round(total_promotions / len(opportunities), 2) if opportunities else 0.0
        }
        
        return ProfileAnalytics(
            opportunity_count=len(opportunities),
            stages_distribution=stages_dist,
            scoring_stats=scoring_stats,
            discovery_stats=discovery_stats,
            promotion_stats=promotion_stats
        )
    
    def _generate_recent_activity(self, opportunities: List[UnifiedOpportunity]) -> List[RecentActivity]:
        """Generate recent activity from opportunities"""
        
        activities = []
        
        # Add discovery sessions
        discovery_by_date = {}
        for opp in opportunities:
            if opp.discovered_at:
                date = opp.discovered_at[:10]
                if date not in discovery_by_date:
                    discovery_by_date[date] = 0
                discovery_by_date[date] += 1
        
        # Recent discovery sessions
        for date, count in sorted(discovery_by_date.items(), reverse=True)[:3]:
            activities.append(RecentActivity(
                type='discovery_session',
                date=f"{date}T12:00:00",
                results=count,
                source='Multiple Sources'
            ))
        
        # Recent promotions
        recent_promotions = []
        for opp in opportunities:
            for promo in opp.promotion_history[-2:]:  # Last 2 promotions per opportunity
                recent_promotions.append((promo, opp.organization_name))
        
        # Sort by date and take most recent
        recent_promotions.sort(key=lambda x: x[0].promoted_at or '', reverse=True)
        
        for promo, org_name in recent_promotions[:3]:
            activities.append(RecentActivity(
                type='auto_promotion' if promo.decision_type == 'auto_promote' else 'manual_promotion',
                date=promo.promoted_at,
                opportunity=org_name,
                from_stage=promo.from_stage,
                to_stage=promo.to_stage
            ))
        
        # Sort all activities by date
        activities.sort(key=lambda x: x.date or '', reverse=True)
        
        return activities[:5]  # Return top 5 recent activities


def get_unified_profile_service() -> UnifiedProfileService:
    """Get singleton instance of unified profile service"""
    if not hasattr(get_unified_profile_service, '_instance'):
        get_unified_profile_service._instance = UnifiedProfileService()
    return get_unified_profile_service._instance
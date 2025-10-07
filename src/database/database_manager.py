#!/usr/bin/env python3
"""
Database Manager for Catalynx Grant Research Platform
Single-user SQLite database operations and management

Handles:
- Database initialization and schema creation
- Profile and opportunity CRUD operations
- Search and filtering functionality
- Cost tracking and analytics
- Export and backup management
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import asyncio
import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class Profile:
    """Profile data model for database operations"""
    id: str
    name: str
    organization_type: str
    ein: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    mission_statement: Optional[str] = None
    status: str = 'active'
    keywords: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    program_areas: Optional[List[str]] = None
    target_populations: Optional[List[str]] = None
    ntee_codes: Optional[List[str]] = None
    government_criteria: Optional[List[str]] = None
    geographic_scope: Optional[Dict] = None
    service_areas: Optional[List[str]] = None
    funding_preferences: Optional[Dict] = None
    annual_revenue: Optional[int] = None
    form_type: Optional[str] = None
    foundation_grants: Optional[List] = None
    board_members: Optional[List] = None
    discovery_count: int = 0
    opportunities_count: int = 0
    last_discovery_date: Optional[datetime] = None
    performance_metrics: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processing_history: Optional[List] = None
    # Enhanced data fields for verified intelligence
    verification_data: Optional[Dict[str, Any]] = None
    web_enhanced_data: Optional[Dict[str, Any]] = None


@dataclass  
class Opportunity:
    """Opportunity data model for database operations"""
    id: str
    profile_id: str
    organization_name: str
    ein: Optional[str] = None
    current_stage: str = 'prospects'
    stage_history: Optional[List] = None
    overall_score: float = 0.0
    confidence_level: Optional[float] = None
    auto_promotion_eligible: bool = False
    promotion_recommended: bool = False
    scored_at: Optional[datetime] = None
    scorer_version: str = '1.0.0'
    analysis_discovery: Optional[Dict] = None
    analysis_plan: Optional[Dict] = None
    analysis_analyze: Optional[Dict] = None
    analysis_examine: Optional[Dict] = None
    analysis_approach: Optional[Dict] = None
    user_rating: Optional[int] = None
    priority_level: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    promotion_history: Optional[List] = None
    legacy_mappings: Optional[Dict] = None
    processing_status: str = 'pending'
    processing_errors: Optional[List] = None
    source: Optional[str] = None
    discovery_date: Optional[datetime] = None
    last_analysis_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DatabaseManager:
    """
    SQLite database manager for single-user grant research platform
    Optimized for 50 profiles with ~7,500 opportunities
    """
    
    def __init__(self, database_path: Optional[str] = None):
        import os
        # Use absolute path to ensure we always use the same database regardless of CWD
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if database_path:
            self.database_path = database_path
        else:
            # Default to project_root/data/catalynx.db (absolute path)
            self.database_path = os.path.join(project_root, "data", "catalynx.db")

        self.schema_path = os.path.join(project_root, "src", "database", "schema.sql")
        self.normalized_schema_path = os.path.join(project_root, "normalized_schema_design.sql")
        self._connection = None

        # Initialize data transformer for normalized storage
        self._data_transformer = None

        # Ensure database directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database on creation
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database with schema if it doesn't exist"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Check if database exists and has tables
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
                if not cursor.fetchone():
                    logger.info("Initializing new database with schema")
                    self._create_schema(conn)
                else:
                    logger.info("Database already exists, verifying schema")
                    self._verify_schema(conn)

                # Initialize normalized schema for analytical operations
                self._initialize_normalized_schema(conn)

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _initialize_normalized_schema(self, conn: sqlite3.Connection):
        """Initialize normalized schema for analytics"""
        try:
            # Check if normalized tables exist
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='people'")

            if not cursor.fetchone():
                logger.info("Creating normalized analytics schema")
                normalized_schema_file = Path(self.normalized_schema_path)
                if normalized_schema_file.exists():
                    with open(normalized_schema_file, 'r') as f:
                        normalized_sql = f.read()
                    conn.executescript(normalized_sql)
                    conn.commit()
                    logger.info("Normalized analytics schema created successfully")
                else:
                    logger.warning(f"Normalized schema file not found: {normalized_schema_file}")
            else:
                logger.info("Normalized analytics schema already exists")

        except Exception as e:
            logger.warning(f"Failed to initialize normalized schema: {e}")

    def _get_data_transformer(self):
        """Get or initialize data transformer"""
        if self._data_transformer is None:
            try:
                from src.data_transformation.main_service import CatalynxDataTransformer
                self._data_transformer = CatalynxDataTransformer(self)
                logger.info("Data transformer initialized successfully")
            except ImportError:
                logger.warning("Data transformation service not available")
                self._data_transformer = None
        return self._data_transformer
            
    def _create_schema(self, conn: sqlite3.Connection):
        """Create database schema from SQL file"""
        try:
            schema_file = Path(self.schema_path)
            if schema_file.exists():
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema created successfully")
            else:
                logger.error(f"Schema file not found: {schema_file}")
                raise FileNotFoundError(f"Schema file not found: {schema_file}")
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise

    def apply_migration(self, migration_file: str) -> bool:
        """Apply a database migration from SQL file"""
        try:
            migration_path = Path(migration_file)
            if not migration_path.exists():
                # Try relative to migrations directory
                migrations_dir = Path(self.schema_path).parent / "migrations"
                migration_path = migrations_dir / migration_file

            if not migration_path.exists():
                logger.error(f"Migration file not found: {migration_file}")
                return False

            with self.get_connection() as conn:
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                conn.executescript(migration_sql)
                conn.commit()
                logger.info(f"Successfully applied migration: {migration_path.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file}: {e}")
            return False

    def _verify_schema(self, conn: sqlite3.Connection):
        """Verify database schema version and structure"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                current_version = result[0]
                logger.info(f"Database schema version: {current_version}")
            else:
                logger.warning("No schema version found, database may be outdated")
        except Exception as e:
            logger.warning(f"Could not verify schema version: {e}")
            
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimized settings"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Optimize SQLite settings for single-user performance
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL") 
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn
        
    async def get_async_connection(self) -> aiosqlite.Connection:
        """Get async database connection for non-blocking operations"""
        conn = await aiosqlite.connect(self.database_path)
        conn.row_factory = aiosqlite.Row
        
        # Apply same optimizations
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.execute("PRAGMA synchronous = NORMAL")
        await conn.execute("PRAGMA cache_size = 10000")
        await conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn

    # =====================================================================================
    # PROFILE OPERATIONS
    # =====================================================================================
    
    def create_profile(self, profile: Profile) -> bool:
        """Create new profile in database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert complex fields to JSON
                focus_areas_json = json.dumps(profile.focus_areas) if profile.focus_areas else None
                program_areas_json = json.dumps(profile.program_areas) if profile.program_areas else None
                target_populations_json = json.dumps(profile.target_populations) if profile.target_populations else None
                ntee_codes_json = json.dumps(profile.ntee_codes) if profile.ntee_codes else None
                government_criteria_json = json.dumps(profile.government_criteria) if profile.government_criteria else None
                geographic_scope_json = json.dumps(profile.geographic_scope) if profile.geographic_scope else None
                service_areas_json = json.dumps(profile.service_areas) if profile.service_areas else None
                funding_preferences_json = json.dumps(profile.funding_preferences) if profile.funding_preferences else None
                foundation_grants_json = json.dumps(profile.foundation_grants) if profile.foundation_grants else None
                board_members_json = json.dumps(profile.board_members) if profile.board_members else None
                performance_metrics_json = json.dumps(profile.performance_metrics) if profile.performance_metrics else None
                processing_history_json = json.dumps(profile.processing_history) if profile.processing_history else None
                # Enhanced data fields
                verification_data_json = json.dumps(profile.verification_data) if profile.verification_data else None
                web_enhanced_data_json = json.dumps(profile.web_enhanced_data) if profile.web_enhanced_data else None

                cursor.execute("""
                    INSERT INTO profiles (
                        id, name, organization_type, ein, website_url, location,
                        mission_statement, status, keywords, focus_areas, program_areas,
                        target_populations, ntee_codes, government_criteria, geographic_scope,
                        service_areas, funding_preferences, annual_revenue, form_type,
                        foundation_grants, board_members, discovery_count, opportunities_count,
                        last_discovery_date, performance_metrics, processing_history,
                        verification_data, web_enhanced_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.id, profile.name, profile.organization_type, profile.ein,
                    profile.website_url, profile.location, profile.mission_statement, profile.status,
                    profile.keywords, focus_areas_json, program_areas_json, target_populations_json,
                    ntee_codes_json, government_criteria_json, geographic_scope_json,
                    service_areas_json, funding_preferences_json, profile.annual_revenue,
                    profile.form_type, foundation_grants_json, board_members_json,
                    profile.discovery_count, profile.opportunities_count,
                    profile.last_discovery_date, performance_metrics_json, processing_history_json,
                    verification_data_json, web_enhanced_data_json
                ))
                
                conn.commit()
                logger.info(f"Profile created: {profile.name} ({profile.id})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create profile {profile.id}: {e}")
            return False
            
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_profile(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get profile {profile_id}: {e}")
            return None

    def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get profile by ID and return as dictionary (for API compatibility)"""
        try:
            profile = self.get_profile(profile_id)
            if profile:
                # Convert Profile object to dictionary for API response
                return {
                    'id': profile.id,
                    'profile_id': profile.id,  # For frontend compatibility
                    'name': profile.name,
                    'organization_type': profile.organization_type,
                    'ein': profile.ein,
                    'website_url': profile.website_url,
                    'location': profile.location,
                    'mission_statement': profile.mission_statement,
                    'status': profile.status,
                    'keywords': profile.keywords,
                    'focus_areas': profile.focus_areas,
                    'program_areas': profile.program_areas,
                    'target_populations': profile.target_populations,
                    'ntee_codes': profile.ntee_codes,
                    'government_criteria': profile.government_criteria,
                    'geographic_scope': profile.geographic_scope,
                    'service_areas': profile.service_areas,
                    'funding_preferences': profile.funding_preferences,
                    'annual_revenue': profile.annual_revenue,
                    'form_type': profile.form_type,
                    'foundation_grants': profile.foundation_grants,
                    'board_members': profile.board_members,
                    'discovery_count': profile.discovery_count,
                    'opportunities_count': profile.opportunities_count,
                    'last_discovery_date': profile.last_discovery_date.isoformat() if profile.last_discovery_date else None,
                    'performance_metrics': profile.performance_metrics,
                    'verification_data': profile.verification_data,
                    'web_enhanced_data': profile.web_enhanced_data,
                    'created_at': profile.created_at.isoformat() if profile.created_at else None,
                    'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
                    'processing_history': profile.processing_history
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get profile by ID {profile_id}: {e}")
            return None
            
    def get_all_profiles(self) -> List[Profile]:
        """Get all profiles with summary information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM profile_summary 
                    ORDER BY last_discovery DESC, name ASC
                """)
                
                profiles = []
                for row in cursor.fetchall():
                    # Convert row to profile format
                    profile_dict = dict(row)
                    profiles.append(profile_dict)
                    
                return profiles
                
        except Exception as e:
            logger.error(f"Failed to get all profiles: {e}")
            return []
            
    def update_profile(self, profile: Profile) -> bool:
        """Update existing profile"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert complex fields to JSON
                focus_areas_json = json.dumps(profile.focus_areas) if profile.focus_areas else None
                program_areas_json = json.dumps(profile.program_areas) if profile.program_areas else None
                target_populations_json = json.dumps(profile.target_populations) if profile.target_populations else None
                ntee_codes_json = json.dumps(profile.ntee_codes) if profile.ntee_codes else None
                government_criteria_json = json.dumps(profile.government_criteria) if profile.government_criteria else None
                geographic_scope_json = json.dumps(profile.geographic_scope) if profile.geographic_scope else None
                service_areas_json = json.dumps(profile.service_areas) if profile.service_areas else None
                funding_preferences_json = json.dumps(profile.funding_preferences) if profile.funding_preferences else None
                foundation_grants_json = json.dumps(profile.foundation_grants) if profile.foundation_grants else None
                board_members_json = json.dumps(profile.board_members) if profile.board_members else None
                performance_metrics_json = json.dumps(profile.performance_metrics) if profile.performance_metrics else None
                processing_history_json = json.dumps(profile.processing_history) if profile.processing_history else None
                # Enhanced data fields
                verification_data_json = json.dumps(profile.verification_data) if profile.verification_data else None
                web_enhanced_data_json = json.dumps(profile.web_enhanced_data) if profile.web_enhanced_data else None

                # CRITICAL DEBUG: Log the exact values being passed to SQL
                logger.critical(f"DATABASE UPDATE DEBUG: profile.website_url='{profile.website_url}', profile.location='{profile.location}', profile.annual_revenue='{profile.annual_revenue}'")
                logger.critical(f"DATABASE UPDATE DEBUG: SQL params - website_url='{profile.website_url}', location='{profile.location}'")

                cursor.execute("""
                    UPDATE profiles SET
                        name = ?, organization_type = ?, ein = ?, website_url = ?, location = ?,
                        mission_statement = ?, status = ?, keywords = ?, focus_areas = ?,
                        program_areas = ?, target_populations = ?, ntee_codes = ?,
                        government_criteria = ?, geographic_scope = ?, service_areas = ?,
                        funding_preferences = ?, annual_revenue = ?, form_type = ?,
                        foundation_grants = ?, board_members = ?, discovery_count = ?,
                        opportunities_count = ?, last_discovery_date = ?, performance_metrics = ?,
                        processing_history = ?, verification_data = ?, web_enhanced_data = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    profile.name, profile.organization_type, profile.ein, profile.website_url, profile.location,
                    profile.mission_statement, profile.status, profile.keywords, focus_areas_json,
                    program_areas_json, target_populations_json, ntee_codes_json, government_criteria_json,
                    geographic_scope_json, service_areas_json, funding_preferences_json,
                    profile.annual_revenue, profile.form_type, foundation_grants_json,
                    board_members_json, profile.discovery_count, profile.opportunities_count,
                    profile.last_discovery_date, performance_metrics_json, processing_history_json,
                    verification_data_json, web_enhanced_data_json, profile.id
                ))

                conn.commit()

                # CRITICAL DEBUG: Verify the update was applied
                cursor.execute("SELECT website_url, location, annual_revenue FROM profiles WHERE id = ?", (profile.id,))
                row = cursor.fetchone()
                if row:
                    logger.critical(f"DATABASE VERIFICATION AFTER UPDATE: website_url='{row[0]}', location='{row[1]}', annual_revenue='{row[2]}'")
                else:
                    logger.critical(f"DATABASE VERIFICATION: No profile found with id {profile.id}")

                # Check if profile exists instead of relying on rowcount
                # SQLite rowcount can be 0 even if update succeeded when no values actually changed
                cursor.execute("SELECT COUNT(*) FROM profiles WHERE id = ?", (profile.id,))
                profile_exists = cursor.fetchone()[0] > 0

                if profile_exists:
                    logger.info(f"Profile updated: {profile.name} ({profile.id}) - rowcount: {cursor.rowcount}")
                    return True
                else:
                    logger.warning(f"Profile not found for update: {profile.id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update profile {profile.id}: {e}")
            return False

    def process_fetched_data(self, profile: Profile, web_scraping_results: Optional[Dict] = None,
                           board_members_json: Optional[str] = None) -> bool:
        """Process fetched data through the transformation pipeline and store normalized records"""
        try:
            transformer = self._get_data_transformer()
            if transformer:
                logger.info(f"Processing fetched data for profile {profile.id} through transformation pipeline")

                # Transform the data into normalized records
                result = transformer.transform_profile_data(
                    profile_id=profile.id,
                    web_scraping_results=web_scraping_results,
                    board_members_json=board_members_json
                )

                if result.success:
                    logger.info(f"Successfully processed fetched data: {result.stats.total_people_created} people, "
                              f"{result.stats.total_roles_created} roles, {result.stats.total_programs_created} programs")
                    return True
                else:
                    logger.warning(f"Data transformation completed with errors: {len(result.errors)} errors")
                    for error in result.errors:
                        logger.warning(f"Transformation error: {error.message}")
                    return False
            else:
                logger.warning("Data transformer not available, skipping normalized data processing")
                return True  # Don't fail the profile save if transformer unavailable

        except Exception as e:
            logger.error(f"Failed to process fetched data for profile {profile.id}: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """Delete profile and all associated opportunities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get opportunity count before deletion
                cursor.execute("SELECT COUNT(*) FROM opportunities WHERE profile_id = ?", (profile_id,))
                opp_count = cursor.fetchone()[0]
                
                # Delete profile (cascades to opportunities due to foreign key)
                cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Profile deleted: {profile_id} (with {opp_count} opportunities)")
                    return True
                else:
                    logger.warning(f"Profile not found for deletion: {profile_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            return False

    def _row_to_profile(self, row) -> Profile:
        """Convert database row to Profile object"""
        from datetime import datetime

        # Helper to parse timestamps (SQLite stores as strings)
        def parse_timestamp(ts):
            if not ts:
                return None
            if isinstance(ts, datetime):
                return ts
            try:
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                return None

        return Profile(
            id=row['id'],
            name=row['name'],
            organization_type=row['organization_type'],
            ein=row['ein'],
            mission_statement=row['mission_statement'],
            status=row['status'],
            keywords=row['keywords'],
            focus_areas=json.loads(row['focus_areas']) if row['focus_areas'] else None,
            program_areas=json.loads(row['program_areas']) if row['program_areas'] else None,
            target_populations=json.loads(row['target_populations']) if row['target_populations'] else None,
            ntee_codes=json.loads(row['ntee_codes']) if row['ntee_codes'] else None,
            government_criteria=json.loads(row['government_criteria']) if row['government_criteria'] else None,
            geographic_scope=json.loads(row['geographic_scope']) if row['geographic_scope'] else None,
            service_areas=json.loads(row['service_areas']) if row['service_areas'] else None,
            funding_preferences=json.loads(row['funding_preferences']) if row['funding_preferences'] else None,
            annual_revenue=row['annual_revenue'],
            form_type=row['form_type'],
            foundation_grants=json.loads(row['foundation_grants']) if row['foundation_grants'] else None,
            board_members=json.loads(row['board_members']) if row['board_members'] else None,
            discovery_count=row['discovery_count'],
            opportunities_count=row['opportunities_count'],
            last_discovery_date=parse_timestamp(row['last_discovery_date']),
            performance_metrics=json.loads(row['performance_metrics']) if row['performance_metrics'] else None,
            created_at=parse_timestamp(row['created_at']),
            updated_at=parse_timestamp(row['updated_at']),
            processing_history=json.loads(row['processing_history']) if row['processing_history'] else None,
            website_url=row['website_url'],
            location=row['location'],
            # Enhanced data fields
            verification_data=json.loads(row['verification_data']) if row['verification_data'] else None,
            web_enhanced_data=json.loads(row['web_enhanced_data']) if row['web_enhanced_data'] else None
        )

    # =====================================================================================
    # OPPORTUNITY OPERATIONS
    # =====================================================================================
    
    def create_opportunity(self, opportunity: Opportunity) -> bool:
        """Create new opportunity in database with performance monitoring"""
        import time
        start_time = time.time()
        
        try:
            # Validate opportunity stage before database insert
            valid_stages = ['prospects', 'qualified_prospects', 'candidates', 'targets', 'opportunities']
            if opportunity.current_stage not in valid_stages:
                logger.warning(f"Invalid opportunity stage '{opportunity.current_stage}', defaulting to 'prospects'")
                opportunity.current_stage = 'prospects'
                
                # Update stage history if it exists
                if opportunity.stage_history:
                    for stage_entry in opportunity.stage_history:
                        if stage_entry.get('stage') == 'discovery':
                            stage_entry['stage'] = 'prospects'
                            logger.info(f"Corrected stage history: discovery → prospects for {opportunity.id}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert complex fields to JSON
                stage_history_json = json.dumps(opportunity.stage_history) if opportunity.stage_history else None
                analysis_discovery_json = json.dumps(opportunity.analysis_discovery) if opportunity.analysis_discovery else None
                analysis_plan_json = json.dumps(opportunity.analysis_plan) if opportunity.analysis_plan else None
                analysis_analyze_json = json.dumps(opportunity.analysis_analyze) if opportunity.analysis_analyze else None
                analysis_examine_json = json.dumps(opportunity.analysis_examine) if opportunity.analysis_examine else None
                analysis_approach_json = json.dumps(opportunity.analysis_approach) if opportunity.analysis_approach else None
                tags_json = json.dumps(opportunity.tags) if opportunity.tags else None
                promotion_history_json = json.dumps(opportunity.promotion_history) if opportunity.promotion_history else None
                legacy_mappings_json = json.dumps(opportunity.legacy_mappings) if opportunity.legacy_mappings else None
                processing_errors_json = json.dumps(opportunity.processing_errors) if opportunity.processing_errors else None
                
                cursor.execute("""
                    INSERT INTO opportunities (
                        id, profile_id, organization_name, ein, current_stage, stage_history,
                        overall_score, confidence_level, auto_promotion_eligible, promotion_recommended,
                        scored_at, scorer_version, analysis_discovery, analysis_plan, analysis_analyze,
                        analysis_examine, analysis_approach, user_rating, priority_level, tags, notes,
                        promotion_history, legacy_mappings, processing_status, processing_errors,
                        source, discovery_date, last_analysis_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity.id, opportunity.profile_id, opportunity.organization_name, opportunity.ein,
                    opportunity.current_stage, stage_history_json, opportunity.overall_score,
                    opportunity.confidence_level, opportunity.auto_promotion_eligible, opportunity.promotion_recommended,
                    opportunity.scored_at, opportunity.scorer_version, analysis_discovery_json,
                    analysis_plan_json, analysis_analyze_json, analysis_examine_json, analysis_approach_json,
                    opportunity.user_rating, opportunity.priority_level, tags_json, opportunity.notes,
                    promotion_history_json, legacy_mappings_json, opportunity.processing_status,
                    processing_errors_json, opportunity.source, opportunity.discovery_date, opportunity.last_analysis_date
                ))
                
                conn.commit()
                
                # Update profile opportunities count
                try:
                    cursor.execute("""
                        UPDATE profiles 
                        SET opportunities_count = (
                            SELECT COUNT(*) FROM opportunities 
                            WHERE profile_id = ? AND status = 'active'
                        )
                        WHERE id = ?
                    """, (opportunity.profile_id, opportunity.profile_id))
                    conn.commit()
                    logger.info(f"Updated profile {opportunity.profile_id} opportunities count")
                except Exception as update_error:
                    logger.warning(f"Failed to update profile opportunities count: {update_error}")
                
                # Log performance metrics
                duration = time.time() - start_time
                logger.info(f"Opportunity created: {opportunity.organization_name} ({opportunity.id}) - Duration: {duration:.3f}s")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create opportunity {opportunity.id}: {e}")
            return False

    def get_opportunities_by_profile(self, profile_id: str, stage: Optional[str] = None, 
                                   limit: Optional[int] = None) -> List[Dict]:
        """Get opportunities for a profile, optionally filtered by stage"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = """
                    SELECT * FROM opportunities 
                    WHERE profile_id = ?
                """
                params = [profile_id]
                
                if stage:
                    base_query += " AND current_stage = ?"
                    params.append(stage)
                    
                base_query += " ORDER BY overall_score DESC, discovery_date DESC"
                
                if limit:
                    base_query += f" LIMIT {limit}"
                    
                cursor.execute(base_query, params)
                
                opportunities = []
                for row in cursor.fetchall():
                    opp_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['stage_history', 'analysis_discovery', 'analysis_plan', 
                                     'analysis_analyze', 'analysis_examine', 'analysis_approach',
                                     'tags', 'promotion_history', 'legacy_mappings', 'processing_errors']:
                        if opp_dict[json_field]:
                            opp_dict[json_field] = json.loads(opp_dict[json_field])
                    opportunities.append(opp_dict)
                    
                return opportunities
                
        except Exception as e:
            logger.error(f"Failed to get opportunities for profile {profile_id}: {e}")
            return []

    def get_opportunity(self, profile_id: str, opportunity_id: str) -> Optional[Dict]:
        """Get single opportunity by profile ID and opportunity ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM opportunities 
                    WHERE profile_id = ? AND id = ?
                """, (profile_id, opportunity_id))
                
                row = cursor.fetchone()
                if row:
                    opp_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['stage_history', 'analysis_discovery', 'analysis_plan', 
                                     'analysis_analyze', 'analysis_examine', 'analysis_approach',
                                     'tags', 'promotion_history', 'legacy_mappings', 'processing_errors']:
                        if opp_dict[json_field]:
                            opp_dict[json_field] = json.loads(opp_dict[json_field])
                    return opp_dict
                else:
                    logger.warning(f"Opportunity not found: {opportunity_id} for profile {profile_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get opportunity {opportunity_id} for profile {profile_id}: {e}")
            return None

    def update_opportunity_stage(self, profile_id: str, opportunity_id: str, new_stage: str, 
                               reason: str, promoted_by: str = 'system') -> bool:
        """Update opportunity stage with audit trail"""
        try:
            # Validate stage before update
            valid_stages = ['prospects', 'qualified_prospects', 'candidates', 'targets', 'opportunities']
            if new_stage not in valid_stages:
                logger.error(f"Invalid stage '{new_stage}' for opportunity {opportunity_id}. Valid stages: {valid_stages}")
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current opportunity data
                cursor.execute("""
                    SELECT current_stage, stage_history FROM opportunities 
                    WHERE profile_id = ? AND id = ?
                """, (profile_id, opportunity_id))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Opportunity not found for stage update: {opportunity_id}")
                    return False
                
                current_stage = row['current_stage']
                stage_history = json.loads(row['stage_history']) if row['stage_history'] else []
                
                # Add stage transition to history
                stage_transition = {
                    'from_stage': current_stage,
                    'to_stage': new_stage,
                    'reason': reason,
                    'promoted_by': promoted_by,
                    'timestamp': datetime.now().isoformat()
                }
                stage_history.append(stage_transition)
                
                # Update opportunity with new stage
                cursor.execute("""
                    UPDATE opportunities SET 
                        current_stage = ?,
                        stage_history = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE profile_id = ? AND id = ?
                """, (new_stage, json.dumps(stage_history), profile_id, opportunity_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Opportunity stage updated: {opportunity_id} from {current_stage} to {new_stage}")
                    return True
                else:
                    logger.warning(f"No rows updated for opportunity stage change: {opportunity_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update opportunity stage for {opportunity_id}: {e}")
            return False

    def search_opportunities(self, query: str, profile_id: Optional[str] = None,
                           stage: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Full-text search across opportunities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = """
                    SELECT o.*, p.name as profile_name
                    FROM opportunities_fts fts
                    JOIN opportunities o ON o.rowid = fts.rowid
                    JOIN profiles p ON o.profile_id = p.id
                    WHERE opportunities_fts MATCH ?
                """
                params = [query]
                
                if profile_id:
                    base_query += " AND o.profile_id = ?"
                    params.append(profile_id)
                    
                if stage:
                    base_query += " AND o.current_stage = ?"
                    params.append(stage)
                    
                base_query += " ORDER BY o.overall_score DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(base_query, params)
                
                opportunities = []
                for row in cursor.fetchall():
                    opp_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['stage_history', 'analysis_discovery', 'analysis_plan', 
                                     'analysis_analyze', 'analysis_examine', 'analysis_approach',
                                     'tags', 'promotion_history', 'legacy_mappings', 'processing_errors']:
                        if opp_dict[json_field]:
                            opp_dict[json_field] = json.loads(opp_dict[json_field])
                    opportunities.append(opp_dict)
                    
                return opportunities
                
        except Exception as e:
            logger.error(f"Failed to search opportunities with query '{query}': {e}")
            return []

    def get_stage_funnel_stats(self, profile_id: str) -> Dict:
        """Get funnel statistics for a profile"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stage_funnel WHERE profile_id = ?", (profile_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                else:
                    return {
                        'profile_id': profile_id,
                        'prospects': 0,
                        'qualified_prospects': 0, 
                        'candidates': 0,
                        'targets': 0,
                        'opportunities': 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get funnel stats for profile {profile_id}: {e}")
            return {}

    # =====================================================================================
    # COST TRACKING AND ANALYTICS
    # =====================================================================================
    
    def record_ai_processing_cost(self, opportunity_id: str, processor_type: str,
                                processing_stage: str, cost: float, processing_time: int,
                                token_usage: int, model_used: str,
                                input_data: Dict, output_data: Dict,
                                success: bool = True, error_details: Optional[Dict] = None) -> bool:
        """Record AI processing cost and results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert AI processing result
                cursor.execute("""
                    INSERT INTO ai_processing_results (
                        opportunity_id, processor_type, processing_stage, input_data, output_data,
                        processing_cost, processing_time, token_usage, model_used,
                        success_indicator, error_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity_id, processor_type, processing_stage,
                    json.dumps(input_data), json.dumps(output_data),
                    cost, processing_time, token_usage, model_used,
                    success, json.dumps(error_details) if error_details else None
                ))
                
                # Update daily cost tracking
                today = date.today()
                cursor.execute("""
                    INSERT INTO cost_tracking (date, total_cost, api_calls_count, tokens_used)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        total_cost = total_cost + excluded.total_cost,
                        api_calls_count = api_calls_count + 1,
                        tokens_used = tokens_used + excluded.tokens_used
                """, (today, cost, token_usage))
                
                # Update specific cost category
                cost_field = {
                    'ai_lite_unified': 'cost_ai_lite',
                    'ai_heavy_light': 'cost_ai_heavy_light', 
                    'ai_heavy_deep': 'cost_ai_heavy_deep',
                    'ai_heavy_implementation': 'cost_ai_heavy_impl'
                }.get(processor_type, 'cost_ai_lite')
                
                cursor.execute(f"""
                    UPDATE cost_tracking 
                    SET {cost_field} = {cost_field} + ?
                    WHERE date = ?
                """, (cost, today))
                
                conn.commit()
                logger.info(f"AI processing cost recorded: ${cost:.4f} for {processor_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record AI processing cost: {e}")
            return False

    def get_daily_cost_summary(self, days: int = 7) -> List[Dict]:
        """Get daily cost summary for the past N days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM cost_summary 
                    ORDER BY date DESC 
                    LIMIT ?
                """, (days,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get daily cost summary: {e}")
            return []

    def check_budget_alerts(self) -> Dict[str, bool]:
        """Check if budget alerts should be triggered"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                today = date.today()
                cursor.execute("""
                    SELECT total_cost, daily_budget, monthly_budget, budget_alert_sent,
                           (SELECT SUM(total_cost) FROM cost_tracking 
                            WHERE date BETWEEN date(?, '-29 days') AND ?) as monthly_total
                    FROM cost_tracking 
                    WHERE date = ?
                """, (today, today, today))
                row = cursor.fetchone()
                
                if not row:
                    return {'daily_alert': False, 'monthly_alert': False}
                
                daily_over = row['total_cost'] > row['daily_budget'] 
                monthly_over = row['monthly_total'] > row['monthly_budget']
                alert_sent = row['budget_alert_sent']
                
                alerts = {
                    'daily_alert': daily_over and not alert_sent,
                    'monthly_alert': monthly_over and not alert_sent,
                    'daily_usage': row['total_cost'] / row['daily_budget'] * 100,
                    'monthly_usage': row['monthly_total'] / row['monthly_budget'] * 100
                }
                
                # Mark alert as sent if needed
                if (daily_over or monthly_over) and not alert_sent:
                    cursor.execute("""
                        UPDATE cost_tracking SET budget_alert_sent = TRUE WHERE date = ?
                    """, (today,))
                    conn.commit()
                
                return alerts
                
        except Exception as e:
            logger.error(f"Failed to check budget alerts: {e}")
            return {'daily_alert': False, 'monthly_alert': False}

    # =====================================================================================
    # EXPORT AND BACKUP OPERATIONS
    # =====================================================================================
    
    def record_export(self, profile_id: str, export_type: str, export_format: str,
                     filename: str, file_path: str, file_size: int,
                     opportunities_count: int, export_config: Dict) -> bool:
        """Record export operation for tracking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO export_history (
                        profile_id, export_type, export_format, filename, file_path,
                        file_size, opportunities_count, export_config, export_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed')
                """, (
                    profile_id, export_type, export_format, filename, file_path,
                    file_size, opportunities_count, json.dumps(export_config)
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record export: {e}")
            return False

    def record_backup(self, backup_type: str, filename: str, file_path: str,
                     file_size: int, records_count: int) -> bool:
        """Record backup operation for tracking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO backup_history (
                        backup_type, backup_filename, backup_path, file_size, 
                        records_count, backup_status
                    ) VALUES (?, ?, ?, ?, ?, 'completed')
                """, (backup_type, filename, file_path, file_size, records_count))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to record backup: {e}")
            return False

    # =====================================================================================
    # SYSTEM METRICS AND PERFORMANCE
    # =====================================================================================
    
    def update_system_metrics(self):
        """Update daily system metrics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                today = date.today()
                
                # Get current counts
                cursor.execute("SELECT COUNT(*) FROM profiles WHERE status = 'active'")
                profile_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM opportunities")
                opportunity_count = cursor.fetchone()[0]
                
                # Get database size
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")  
                page_size = cursor.fetchone()[0]
                db_size = page_count * page_size
                
                # Update metrics
                cursor.execute("""
                    INSERT INTO system_metrics (
                        metric_date, database_size, total_profiles, total_opportunities
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(metric_date) DO UPDATE SET
                        database_size = excluded.database_size,
                        total_profiles = excluded.total_profiles,
                        total_opportunities = excluded.total_opportunities
                """, (today, db_size, profile_count, opportunity_count))
                
                conn.commit()
                logger.info(f"System metrics updated: {profile_count} profiles, {opportunity_count} opportunities")
                
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def get_performance_dashboard(self) -> List[Dict]:
        """Get performance dashboard data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM performance_dashboard")
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            return []

    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent system activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM recent_activity LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []

    # =====================================================================================
    # DATABASE MAINTENANCE
    # =====================================================================================
    
    def vacuum_database(self):
        """Optimize database storage and performance"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                logger.info("Database vacuum and analyze completed")
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")

    def backup_database(self, backup_path: str) -> bool:
        """Create full database backup"""
        try:
            import shutil
            
            # Simple file copy backup
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(self.database_path, backup_path)
            
            # Record backup
            file_size = Path(backup_path).stat().st_size
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM profiles")
                profile_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM opportunities") 
                opp_count = cursor.fetchone()[0]
                
            self.record_backup(
                'full_database', 
                backup_file.name,
                backup_path,
                file_size,
                profile_count + opp_count
            )
            
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False

    def __del__(self):
        """Cleanup database connection on destruction"""
        if self._connection:
            self._connection.close()


# =====================================================================================
# CONVENIENCE FUNCTIONS AND MIGRATION UTILITIES
# =====================================================================================

def migrate_json_data_to_database(json_data_path: str, db_manager: DatabaseManager):
    """Migrate existing JSON profile and opportunity data to database"""
    import os
    
    data_path = Path(json_data_path)
    profiles_migrated = 0
    opportunities_migrated = 0
    
    try:
        # Migrate profiles
        profiles_dir = data_path / "profiles" / "profiles"
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob("profile_*.json"):
                try:
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
                        
                    profile = Profile(
                        id=profile_data.get('profile_id'),
                        name=profile_data.get('name'),
                        organization_type=profile_data.get('organization_type', 'nonprofit'),
                        ein=profile_data.get('ein'),
                        mission_statement=profile_data.get('mission_statement'),
                        status=profile_data.get('status', 'active'),
                        keywords=profile_data.get('keywords'),
                        focus_areas=profile_data.get('focus_areas'),
                        program_areas=profile_data.get('program_areas'),
                        target_populations=profile_data.get('target_populations'),
                        ntee_codes=profile_data.get('ntee_codes'),
                        government_criteria=profile_data.get('government_criteria'),
                        geographic_scope=profile_data.get('geographic_scope'),
                        service_areas=profile_data.get('service_areas'),
                        funding_preferences=profile_data.get('funding_preferences'),
                        annual_revenue=profile_data.get('annual_revenue'),
                        form_type=profile_data.get('form_type'),
                        foundation_grants=profile_data.get('foundation_grants'),
                        board_members=profile_data.get('board_members')
                    )
                    
                    if db_manager.create_profile(profile):
                        profiles_migrated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to migrate profile {profile_file}: {e}")
        
        # Migrate opportunities  
        opportunities_dir = data_path / "profiles" / "opportunities"
        if opportunities_dir.exists():
            for opp_file in opportunities_dir.glob("profile_*_opportunity_*.json"):
                try:
                    with open(opp_file, 'r') as f:
                        opp_data = json.load(f)
                        
                    opportunity = Opportunity(
                        id=opp_data.get('opportunity_id'),
                        profile_id=opp_data.get('profile_id'),
                        organization_name=opp_data.get('organization_name'),
                        ein=opp_data.get('ein'),
                        current_stage=opp_data.get('current_stage', 'prospects'),
                        stage_history=opp_data.get('stage_history'),
                        overall_score=opp_data.get('scoring', {}).get('overall_score', 0.0),
                        confidence_level=opp_data.get('scoring', {}).get('confidence_level'),
                        auto_promotion_eligible=opp_data.get('scoring', {}).get('auto_promotion_eligible', False),
                        promotion_recommended=opp_data.get('scoring', {}).get('promotion_recommended', False),
                        analysis_discovery=opp_data.get('analysis', {}).get('discovery'),
                        source=opp_data.get('analysis', {}).get('discovery', {}).get('match_factors', {}).get('source_type'),
                        discovery_date=datetime.fromisoformat(opp_data.get('created_at', datetime.now().isoformat()))
                    )
                    
                    if db_manager.create_opportunity(opportunity):
                        opportunities_migrated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to migrate opportunity {opp_file}: {e}")
                    
        logger.info(f"Migration completed: {profiles_migrated} profiles, {opportunities_migrated} opportunities")
        return profiles_migrated, opportunities_migrated
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 0, 0


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    db = DatabaseManager("test_catalynx.db")
    
    # Test profile creation
    test_profile = Profile(
        id="test_profile_123",
        name="Test Organization",
        organization_type="nonprofit",
        ein="12-3456789",
        mission_statement="Test mission statement",
        focus_areas=["healthcare", "education"],
        ntee_codes=["P20", "B25"],
        government_criteria=["HHS", "ED"]
    )
    
    if db.create_profile(test_profile):
        print("✅ Profile created successfully")
        
        # Test opportunity creation
        test_opportunity = Opportunity(
            id="test_opp_456",
            profile_id="test_profile_123", 
            organization_name="Test Foundation",
            ein="98-7654321",
            current_stage="prospects",
            overall_score=0.75,
            analysis_discovery={"test": "data"}
        )
        
        if db.create_opportunity(test_opportunity):
            print("✅ Opportunity created successfully")
            
            # Test queries
            opportunities = db.get_opportunities_by_profile("test_profile_123")
            print(f"✅ Found {len(opportunities)} opportunities")
            
            # Test search
            search_results = db.search_opportunities("Test Foundation")
            print(f"✅ Search found {len(search_results)} results")
            
    # Test system metrics
    db.update_system_metrics()
    dashboard = db.get_performance_dashboard()
    print(f"✅ Performance dashboard: {len(dashboard)} metrics")
    
    print("Database manager testing completed successfully! 🎉")
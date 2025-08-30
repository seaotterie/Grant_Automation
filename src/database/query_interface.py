#!/usr/bin/env python3
"""
Enhanced Database Query Interface for Catalynx Grant Research Platform
Provides advanced filtering, sorting, and search capabilities
"""

from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json
import logging
from .database_manager import DatabaseManager, Profile, Opportunity

logger = logging.getLogger(__name__)


@dataclass
class QueryFilter:
    """Filter configuration for database queries"""
    profile_ids: Optional[List[str]] = None
    organization_types: Optional[List[str]] = None  # nonprofit, foundation, government
    stages: Optional[List[str]] = None  # discovery, prospects, etc.
    score_range: Optional[Tuple[float, float]] = None  # (min_score, max_score)
    date_range: Optional[Tuple[date, date]] = None  # (start_date, end_date)
    ein_list: Optional[List[str]] = None
    ntee_codes: Optional[List[str]] = None
    states: Optional[List[str]] = None
    revenue_range: Optional[Tuple[int, int]] = None  # (min_revenue, max_revenue)
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None
    priority_levels: Optional[List[str]] = None  # low, medium, high, urgent
    user_rating_range: Optional[Tuple[int, int]] = None  # (min_rating, max_rating)
    confidence_range: Optional[Tuple[float, float]] = None  # AI confidence range
    
    
@dataclass
class QuerySort:
    """Sorting configuration for database queries"""
    field: str = "updated_at"  # Field to sort by
    direction: str = "DESC"  # ASC or DESC
    secondary_field: Optional[str] = None  # Secondary sort field
    secondary_direction: str = "DESC"


class DatabaseQueryInterface:
    """
    Enhanced query interface with advanced filtering and search capabilities
    Built on top of DatabaseManager for the grant research platform
    """
    
    def __init__(self, database_path: Optional[str] = None):
        self.db = DatabaseManager(database_path)
        
    # =====================================================================================
    # PROFILE QUERIES
    # =====================================================================================
    
    def filter_profiles(self, filters: QueryFilter, sort: Optional[QuerySort] = None, 
                       limit: Optional[int] = None, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        Advanced profile filtering with multiple criteria
        Returns (filtered_profiles, total_count)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build base query
                base_query = "SELECT * FROM profiles WHERE 1=1"
                params = []
                count_params = []
                
                # Apply filters
                if filters.profile_ids:
                    placeholders = ','.join('?' * len(filters.profile_ids))
                    base_query += f" AND id IN ({placeholders})"
                    params.extend(filters.profile_ids)
                    count_params.extend(filters.profile_ids)
                    
                if filters.organization_types:
                    placeholders = ','.join('?' * len(filters.organization_types))
                    base_query += f" AND organization_type IN ({placeholders})"
                    params.extend(filters.organization_types)
                    count_params.extend(filters.organization_types)
                    
                if filters.states:
                    # Search in geographic_scope JSON field
                    state_conditions = []
                    for state in filters.states:
                        state_conditions.append("JSON_EXTRACT(geographic_scope, '$.states') LIKE ?")
                        params.append(f'%"{state}"%')
                        count_params.append(f'%"{state}"%')
                    base_query += f" AND ({' OR '.join(state_conditions)})"
                    
                if filters.ntee_codes:
                    # Search in ntee_codes JSON field
                    ntee_conditions = []
                    for code in filters.ntee_codes:
                        ntee_conditions.append("JSON_EXTRACT(ntee_codes, '$') LIKE ?")
                        params.append(f'%"{code}"%')
                        count_params.append(f'%"{code}"%')
                    base_query += f" AND ({' OR '.join(ntee_conditions)})"
                    
                if filters.revenue_range:
                    min_rev, max_rev = filters.revenue_range
                    if min_rev is not None:
                        base_query += " AND annual_revenue >= ?"
                        params.append(min_rev)
                        count_params.append(min_rev)
                    if max_rev is not None:
                        base_query += " AND annual_revenue <= ?"
                        params.append(max_rev)
                        count_params.append(max_rev)
                        
                if filters.search_text:
                    base_query += " AND (name LIKE ? OR mission_statement LIKE ? OR keywords LIKE ?)"
                    search_pattern = f"%{filters.search_text}%"
                    params.extend([search_pattern, search_pattern, search_pattern])
                    count_params.extend([search_pattern, search_pattern, search_pattern])
                    
                # Add status filter (only active by default)
                base_query += " AND status = 'active'"
                
                # Get total count
                count_query = base_query.replace("SELECT *", "SELECT COUNT(*)")
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
                
                # Apply sorting
                if sort:
                    base_query += f" ORDER BY {sort.field} {sort.direction}"
                    if sort.secondary_field:
                        base_query += f", {sort.secondary_field} {sort.secondary_direction}"
                else:
                    base_query += " ORDER BY updated_at DESC"
                    
                # Apply pagination
                if limit:
                    base_query += f" LIMIT {limit} OFFSET {offset}"
                    
                cursor.execute(base_query, params)
                profiles = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for profile in profiles:
                    self._parse_profile_json_fields(profile)
                    
                logger.info(f"Filtered profiles: {len(profiles)}/{total_count} with filters")
                return profiles, total_count
                
        except Exception as e:
            logger.error(f"Failed to filter profiles: {e}")
            return [], 0
            
    def search_profiles_full_text(self, query: str, limit: int = 50) -> List[Dict]:
        """Full-text search across all profile fields"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use comprehensive text search
                search_query = """
                    SELECT *, 
                           CASE 
                               WHEN name LIKE ? THEN 10
                               WHEN mission_statement LIKE ? THEN 5
                               WHEN keywords LIKE ? THEN 3
                               ELSE 1
                           END as relevance_score
                    FROM profiles 
                    WHERE status = 'active'
                      AND (name LIKE ? OR mission_statement LIKE ? OR keywords LIKE ? 
                           OR focus_areas LIKE ? OR program_areas LIKE ?)
                    ORDER BY relevance_score DESC, name ASC
                    LIMIT ?
                """
                
                search_pattern = f"%{query}%"
                params = [search_pattern] * 8 + [limit]
                
                cursor.execute(search_query, params)
                profiles = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for profile in profiles:
                    self._parse_profile_json_fields(profile)
                    
                logger.info(f"Full-text search found {len(profiles)} profiles for query: {query}")
                return profiles
                
        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            return []

    # =====================================================================================
    # OPPORTUNITY QUERIES  
    # =====================================================================================
    
    def filter_opportunities(self, filters: QueryFilter, sort: Optional[QuerySort] = None,
                           limit: Optional[int] = None, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        Advanced opportunity filtering with multiple criteria
        Returns (filtered_opportunities, total_count)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build base query with profile join
                base_query = """
                    SELECT o.*, p.name as profile_name, p.organization_type as profile_type
                    FROM opportunities o
                    JOIN profiles p ON o.profile_id = p.id
                    WHERE 1=1
                """
                params = []
                count_params = []
                
                # Apply filters
                if filters.profile_ids:
                    placeholders = ','.join('?' * len(filters.profile_ids))
                    base_query += f" AND o.profile_id IN ({placeholders})"
                    params.extend(filters.profile_ids)
                    count_params.extend(filters.profile_ids)
                    
                if filters.stages:
                    placeholders = ','.join('?' * len(filters.stages))
                    base_query += f" AND o.current_stage IN ({placeholders})"
                    params.extend(filters.stages)
                    count_params.extend(filters.stages)
                    
                if filters.score_range:
                    min_score, max_score = filters.score_range
                    if min_score is not None:
                        base_query += " AND o.overall_score >= ?"
                        params.append(min_score)
                        count_params.append(min_score)
                    if max_score is not None:
                        base_query += " AND o.overall_score <= ?"
                        params.append(max_score)
                        count_params.append(max_score)
                        
                if filters.confidence_range:
                    min_conf, max_conf = filters.confidence_range
                    if min_conf is not None:
                        base_query += " AND o.confidence_level >= ?"
                        params.append(min_conf)
                        count_params.append(min_conf)
                    if max_conf is not None:
                        base_query += " AND o.confidence_level <= ?"
                        params.append(max_conf)
                        count_params.append(max_conf)
                        
                if filters.user_rating_range:
                    min_rating, max_rating = filters.user_rating_range
                    if min_rating is not None:
                        base_query += " AND o.user_rating >= ?"
                        params.append(min_rating)
                        count_params.append(min_rating)
                    if max_rating is not None:
                        base_query += " AND o.user_rating <= ?"
                        params.append(max_rating)
                        count_params.append(max_rating)
                        
                if filters.priority_levels:
                    placeholders = ','.join('?' * len(filters.priority_levels))
                    base_query += f" AND o.priority_level IN ({placeholders})"
                    params.extend(filters.priority_levels)
                    count_params.extend(filters.priority_levels)
                    
                if filters.date_range:
                    start_date, end_date = filters.date_range
                    if start_date:
                        base_query += " AND DATE(o.discovery_date) >= ?"
                        params.append(start_date)
                        count_params.append(start_date)
                    if end_date:
                        base_query += " AND DATE(o.discovery_date) <= ?"
                        params.append(end_date)
                        count_params.append(end_date)
                        
                if filters.ein_list:
                    placeholders = ','.join('?' * len(filters.ein_list))
                    base_query += f" AND o.ein IN ({placeholders})"
                    params.extend(filters.ein_list)
                    count_params.extend(filters.ein_list)
                    
                if filters.search_text:
                    base_query += " AND (o.organization_name LIKE ? OR o.notes LIKE ? OR o.tags LIKE ?)"
                    search_pattern = f"%{filters.search_text}%"
                    params.extend([search_pattern, search_pattern, search_pattern])
                    count_params.extend([search_pattern, search_pattern, search_pattern])
                    
                # Get total count
                count_query = base_query.replace(
                    "SELECT o.*, p.name as profile_name, p.organization_type as profile_type", 
                    "SELECT COUNT(*)"
                )
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
                
                # Apply sorting
                if sort:
                    base_query += f" ORDER BY o.{sort.field} {sort.direction}"
                    if sort.secondary_field:
                        base_query += f", o.{sort.secondary_field} {sort.secondary_direction}"
                else:
                    base_query += " ORDER BY o.overall_score DESC, o.updated_at DESC"
                    
                # Apply pagination
                if limit:
                    base_query += f" LIMIT {limit} OFFSET {offset}"
                    
                cursor.execute(base_query, params)
                opportunities = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for opp in opportunities:
                    self._parse_opportunity_json_fields(opp)
                    
                logger.info(f"Filtered opportunities: {len(opportunities)}/{total_count} with filters")
                return opportunities, total_count
                
        except Exception as e:
            logger.error(f"Failed to filter opportunities: {e}")
            return [], 0

    def search_opportunities_advanced(self, query: str, filters: Optional[QueryFilter] = None, 
                                    limit: int = 100) -> List[Dict]:
        """Advanced full-text search with optional additional filters"""
        try:
            # Use the database's built-in full-text search
            if filters and filters.profile_ids:
                profile_id = filters.profile_ids[0] if len(filters.profile_ids) == 1 else None
                stage = filters.stages[0] if filters and filters.stages and len(filters.stages) == 1 else None
                
                return self.db.search_opportunities(query, profile_id=profile_id, stage=stage, limit=limit)
            else:
                return self.db.search_opportunities(query, limit=limit)
                
        except Exception as e:
            logger.error(f"Failed to search opportunities: {e}")
            return []

    # =====================================================================================
    # ANALYTICS AND REPORTING QUERIES
    # =====================================================================================
    
    def get_opportunity_analytics(self, profile_id: Optional[str] = None, 
                                date_range: Optional[Tuple[date, date]] = None) -> Dict:
        """Get comprehensive opportunity analytics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Base conditions
                conditions = ["1=1"]
                params = []
                
                if profile_id:
                    conditions.append("profile_id = ?")
                    params.append(profile_id)
                    
                if date_range:
                    start_date, end_date = date_range
                    if start_date:
                        conditions.append("DATE(discovery_date) >= ?")
                        params.append(start_date)
                    if end_date:
                        conditions.append("DATE(discovery_date) <= ?")
                        params.append(end_date)
                        
                where_clause = " AND ".join(conditions)
                
                analytics = {}
                
                # Stage distribution
                cursor.execute(f"""
                    SELECT current_stage, COUNT(*) as count
                    FROM opportunities 
                    WHERE {where_clause}
                    GROUP BY current_stage
                    ORDER BY count DESC
                """, params)
                analytics['stage_distribution'] = dict(cursor.fetchall())
                
                # Score distribution (bins)
                cursor.execute(f"""
                    SELECT 
                        CASE 
                            WHEN overall_score >= 0.8 THEN 'high'
                            WHEN overall_score >= 0.6 THEN 'medium'
                            WHEN overall_score >= 0.4 THEN 'low'
                            ELSE 'very_low'
                        END as score_bin,
                        COUNT(*) as count
                    FROM opportunities 
                    WHERE {where_clause}
                    GROUP BY score_bin
                """, params)
                analytics['score_distribution'] = dict(cursor.fetchall())
                
                # Top organizations by count
                cursor.execute(f"""
                    SELECT organization_name, COUNT(*) as count
                    FROM opportunities 
                    WHERE {where_clause}
                    GROUP BY organization_name
                    ORDER BY count DESC
                    LIMIT 10
                """, params)
                analytics['top_organizations'] = dict(cursor.fetchall())
                
                # Monthly discovery trend
                cursor.execute(f"""
                    SELECT 
                        strftime('%Y-%m', discovery_date) as month,
                        COUNT(*) as count
                    FROM opportunities 
                    WHERE {where_clause} AND discovery_date IS NOT NULL
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                """, params)
                analytics['monthly_trend'] = dict(cursor.fetchall())
                
                # Summary stats
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_opportunities,
                        AVG(overall_score) as avg_score,
                        MAX(overall_score) as max_score,
                        MIN(overall_score) as min_score,
                        COUNT(CASE WHEN user_rating IS NOT NULL THEN 1 END) as rated_count,
                        AVG(user_rating) as avg_user_rating
                    FROM opportunities 
                    WHERE {where_clause}
                """, params)
                row = cursor.fetchone()
                analytics['summary'] = dict(row) if row else {}
                
                logger.info(f"Generated analytics for {'profile ' + profile_id if profile_id else 'all profiles'}")
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to get opportunity analytics: {e}")
            return {}

    def get_profile_performance_metrics(self, profile_id: str) -> Dict:
        """Get detailed performance metrics for a specific profile"""
        try:
            metrics = {}
            
            # Get profile info
            profile = self.db.get_profile(profile_id)
            if not profile:
                return {}
                
            metrics['profile_info'] = {
                'name': profile.name,
                'organization_type': profile.organization_type,
                'created_at': profile.created_at,
                'discovery_count': profile.discovery_count,
                'opportunities_count': profile.opportunities_count,
                'last_discovery_date': profile.last_discovery_date
            }
            
            # Get stage funnel
            metrics['stage_funnel'] = self.db.get_stage_funnel_stats(profile_id)
            
            # Get opportunity analytics
            metrics['analytics'] = self.get_opportunity_analytics(profile_id)
            
            # Calculate conversion rates
            funnel = metrics['stage_funnel']
            if funnel.get('prospects', 0) > 0:
                metrics['conversion_rates'] = {
                    'prospects_to_qualified': funnel.get('qualified_prospects', 0) / funnel['prospects'],
                    'qualified_to_candidates': funnel.get('candidates', 0) / max(funnel.get('qualified_prospects', 1), 1),
                    'candidates_to_targets': funnel.get('targets', 0) / max(funnel.get('candidates', 1), 1),
                    'targets_to_opportunities': funnel.get('opportunities', 0) / max(funnel.get('targets', 1), 1),
                    'overall_conversion': funnel.get('opportunities', 0) / funnel['prospects']
                }
            
            logger.info(f"Generated performance metrics for profile: {profile.name}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get profile performance metrics: {e}")
            return {}
            
    # =====================================================================================
    # UTILITY METHODS
    # =====================================================================================
    
    def _parse_profile_json_fields(self, profile: Dict):
        """Parse JSON fields in profile dictionary"""
        json_fields = [
            'focus_areas', 'program_areas', 'target_populations', 'ntee_codes',
            'government_criteria', 'geographic_scope', 'service_areas', 
            'funding_preferences', 'foundation_grants', 'board_members',
            'performance_metrics', 'processing_history'
        ]
        
        for field in json_fields:
            if profile.get(field) and isinstance(profile[field], str):
                try:
                    profile[field] = json.loads(profile[field])
                except json.JSONDecodeError:
                    profile[field] = None
                    
    def _parse_opportunity_json_fields(self, opportunity: Dict):
        """Parse JSON fields in opportunity dictionary"""
        json_fields = [
            'stage_history', 'analysis_discovery', 'analysis_plan', 'analysis_analyze',
            'analysis_examine', 'analysis_approach', 'tags', 'promotion_history',
            'legacy_mappings', 'processing_errors'
        ]
        
        for field in json_fields:
            if opportunity.get(field) and isinstance(opportunity[field], str):
                try:
                    opportunity[field] = json.loads(opportunity[field])
                except json.JSONDecodeError:
                    opportunity[field] = None
    
    def get_filter_options(self) -> Dict:
        """Get available filter options for UI dropdowns"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                options = {}
                
                # Organization types
                cursor.execute("SELECT DISTINCT organization_type FROM profiles WHERE status = 'active'")
                options['organization_types'] = [row[0] for row in cursor.fetchall()]
                
                # Stages  
                cursor.execute("SELECT DISTINCT current_stage FROM opportunities")
                options['stages'] = [row[0] for row in cursor.fetchall()]
                
                # Priority levels
                cursor.execute("SELECT DISTINCT priority_level FROM opportunities WHERE priority_level IS NOT NULL")
                options['priority_levels'] = [row[0] for row in cursor.fetchall()]
                
                # States from geographic scope - simplified approach
                cursor.execute("""
                    SELECT geographic_scope FROM profiles 
                    WHERE geographic_scope IS NOT NULL 
                    AND geographic_scope != ''
                """)
                
                states = set()
                for row in cursor.fetchall():
                    try:
                        geo_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                        if geo_data and isinstance(geo_data, dict) and 'states' in geo_data:
                            if isinstance(geo_data['states'], list):
                                states.update(geo_data['states'])
                    except (json.JSONDecodeError, TypeError):
                        continue
                        
                options['states'] = sorted(list(states))
                
                return options
                
        except Exception as e:
            logger.error(f"Failed to get filter options: {e}")
            return {}


# =====================================================================================
# CONVENIENCE FUNCTIONS
# =====================================================================================

def create_basic_filter(**kwargs) -> QueryFilter:
    """Create a QueryFilter with common parameters"""
    return QueryFilter(**kwargs)

def create_score_filter(min_score: float = 0.7) -> QueryFilter:
    """Create a filter for high-scoring opportunities"""
    return QueryFilter(score_range=(min_score, 1.0))

def create_recent_filter(days: int = 30) -> QueryFilter:
    """Create a filter for recent opportunities"""
    start_date = date.today() - timedelta(days=days)
    return QueryFilter(date_range=(start_date, None))

def create_stage_filter(stages: List[str]) -> QueryFilter:
    """Create a filter for specific stages"""
    return QueryFilter(stages=stages)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize query interface
    qi = DatabaseQueryInterface("data/catalynx.db")
    
    # Test profile filtering
    print("=== Testing Profile Filtering ===")
    nonprofit_filter = create_basic_filter(organization_types=['nonprofit'])
    profiles, total = qi.filter_profiles(nonprofit_filter, limit=5)
    print(f"Found {len(profiles)}/{total} nonprofit profiles")
    
    # Test opportunity filtering
    print("\n=== Testing Opportunity Filtering ===")
    high_score_filter = create_score_filter(min_score=0.6)
    opportunities, total = qi.filter_opportunities(high_score_filter, limit=10)
    print(f"Found {len(opportunities)}/{total} high-scoring opportunities")
    
    # Test search
    print("\n=== Testing Search ===")
    search_results = qi.search_profiles_full_text("Health", limit=3)
    print(f"Found {len(search_results)} profiles matching 'Health'")
    
    # Test analytics
    print("\n=== Testing Analytics ===")
    if profiles:
        profile_id = profiles[0]['id']
        analytics = qi.get_opportunity_analytics(profile_id)
        print(f"Analytics for {profiles[0]['name']}: {analytics.get('summary', {})}")
    
    # Test filter options
    print("\n=== Testing Filter Options ===")
    options = qi.get_filter_options()
    print(f"Available filters: {list(options.keys())}")
    
    print("\nQuery interface testing completed successfully! 🎉")
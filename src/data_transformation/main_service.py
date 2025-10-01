#!/usr/bin/env python3
"""
Main Data Transformation Service for Catalynx
High-level orchestration service integrating all transformation components

Features:
- Simple API for profile data transformation
- Automatic error handling and recovery
- Performance monitoring and optimization
- Integration with existing profile workflow
- Comprehensive logging and debugging
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database.database_manager import DatabaseManager, Profile
from .models import (
    WebScrapingResults, DatabaseJSONFields, BoardMemberData,
    TransformationResult, TransformationConfig
)
from .transformation_service import DataTransformationService
from .database_integration import DataTransformationIntegrator

logger = logging.getLogger(__name__)


class CatalynxDataTransformer:
    """Main service for transforming Catalynx profile data"""
    
    def __init__(self, database_manager: DatabaseManager, 
                 config: Optional[TransformationConfig] = None):
        """Initialize the data transformer
        
        Args:
            database_manager: Existing database manager instance
            config: Optional transformation configuration
        """
        self.db_manager = database_manager
        self.config = config or TransformationConfig()
        
        # Initialize services
        self.transformation_service = DataTransformationService(self.config)
        self.integrator = DataTransformationIntegrator(database_manager)
        
        logger.info("CatalynxDataTransformer initialized")
    
    def transform_profile_data(self, profile_id: str, 
                             web_scraping_results: Optional[Dict[str, Any]] = None,
                             board_members_json: Optional[List[Dict[str, Any]]] = None,
                             verification_data: Optional[Dict[str, Any]] = None) -> TransformationResult:
        """Transform profile data from various sources
        
        Args:
            profile_id: ID of the profile to transform
            web_scraping_results: Web scraping results in frontend format
            board_members_json: Board member data from profile JSON field
            verification_data: Tax filing verification data
            
        Returns:
            TransformationResult with success status and transformed data
        """
        try:
            logger.info(f"Starting data transformation for profile {profile_id}")
            
            # Get profile information
            profile = self.db_manager.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
                
            # Prepare input data
            json_data = self._prepare_json_data(
                profile, web_scraping_results, board_members_json, verification_data
            )
            
            # Perform transformation
            result = self.transformation_service.transform_profile_data(
                profile_id=profile_id,
                ein=profile.ein or "",
                json_data=json_data
            )
            
            # Save results to database if successful
            if result.success and result.statistics.successful_transformations > 0:
                integration_success = self.integrator.process_profile_transformation(
                    profile, result
                )
                
                if not integration_success:
                    logger.warning(f"Data transformation succeeded but database integration failed for {profile_id}")
                    # Don't mark as failed if transformation worked but integration had issues
            
            logger.info(f"Transformation completed for {profile_id}: "
                       f"Success={result.success}, Records={result.statistics.total_records_processed}")
            
            return result
            
        except Exception as e:
            logger.error(f"Transformation failed for profile {profile_id}: {e}")
            return TransformationResult(
                success=False,
                transformation_id="failed",
                profile_id=profile_id,
                validation_errors=[{
                    "field": "system",
                    "error_type": "transformation_error",
                    "message": str(e),
                    "severity": "critical"
                }]
            )
    
    def transform_profile_from_database(self, profile_id: str) -> TransformationResult:
        """Transform profile using existing data in database
        
        Args:
            profile_id: ID of the profile to transform
            
        Returns:
            TransformationResult with success status and transformed data
        """
        try:
            # Get profile with existing JSON data
            profile = self.db_manager.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
                
            # Extract data from profile JSON fields
            web_data = None
            if profile.web_enhanced_data:
                try:
                    if isinstance(profile.web_enhanced_data, str):
                        web_data = json.loads(profile.web_enhanced_data)
                    else:
                        web_data = profile.web_enhanced_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse web_enhanced_data for {profile_id}: {e}")
                    
            board_data = None
            if profile.board_members:
                try:
                    if isinstance(profile.board_members, str):
                        board_data = json.loads(profile.board_members)
                    else:
                        board_data = profile.board_members
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse board_members for {profile_id}: {e}")
                    
            verification_data = None
            if profile.verification_data:
                try:
                    if isinstance(profile.verification_data, str):
                        verification_data = json.loads(profile.verification_data)
                    else:
                        verification_data = profile.verification_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse verification_data for {profile_id}: {e}")
            
            # Transform the data
            return self.transform_profile_data(
                profile_id=profile_id,
                web_scraping_results=web_data,
                board_members_json=board_data,
                verification_data=verification_data
            )
            
        except Exception as e:
            logger.error(f"Database transformation failed for profile {profile_id}: {e}")
            return TransformationResult(
                success=False,
                transformation_id="failed",
                profile_id=profile_id,
                validation_errors=[{
                    "field": "database_extraction",
                    "error_type": "data_access_error",
                    "message": str(e),
                    "severity": "critical"
                }]
            )
    
    def get_transformation_summary(self, profile_id: str) -> Dict[str, Any]:
        """Get transformation summary for a profile
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Dictionary with transformation history and current data quality
        """
        try:
            # Get profile information
            profile = self.db_manager.get_profile(profile_id)
            if not profile:
                return {'error': f'Profile not found: {profile_id}'}
                
            # Get enhanced profile data including normalized records
            enhanced_data = self.integrator.get_enhanced_profile_data(
                profile_id, profile.ein or ""
            )
            
            # Get transformation history
            transformation_history = self.integrator.normalized_db.get_transformation_history(profile_id)
            
            # Calculate summary statistics
            summary = {
                'profile_id': profile_id,
                'profile_name': profile.name,
                'ein': profile.ein,
                'last_transformation': None,
                'total_transformations': len(transformation_history),
                'data_quality': enhanced_data.get('data_quality_summary', {}),
                'normalized_records': {
                    'people': len(enhanced_data.get('normalized_data', {}).get('people', [])),
                    'programs': len(enhanced_data.get('normalized_data', {}).get('programs', [])),
                    'contacts': len(enhanced_data.get('normalized_data', {}).get('contacts', [])),
                    'connections': len(enhanced_data.get('normalized_data', {}).get('board_connections', []))
                },
                'recent_transformations': transformation_history[:5]  # Last 5 transformations
            }
            
            # Add last transformation info
            if transformation_history:
                latest = transformation_history[0]
                summary['last_transformation'] = {
                    'date': latest.get('created_at'),
                    'success': latest.get('success'),
                    'records_processed': latest.get('records_processed'),
                    'validation_errors': latest.get('validation_errors')
                }
                
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get transformation summary for {profile_id}: {e}")
            return {'error': str(e)}
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Get overall data quality report across all profiles
        
        Returns:
            Dictionary with system-wide data quality metrics
        """
        try:
            # Get quality metrics from normalized database
            quality_metrics = self.integrator.normalized_db.get_data_quality_metrics()
            
            # Get transformation statistics
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get transformation counts
                cursor.execute("""
                    SELECT COUNT(*) as total_transformations,
                           COUNT(CASE WHEN success THEN 1 END) as successful_transformations,
                           AVG(processing_time_seconds) as avg_processing_time,
                           SUM(records_processed) as total_records_processed
                    FROM transformation_history
                    WHERE created_at >= datetime('now', '-30 days')
                """)
                transformation_stats = cursor.fetchone()
                
                # Get profile coverage
                cursor.execute("""
                    SELECT COUNT(*) as total_profiles,
                           COUNT(CASE WHEN web_enhanced_data IS NOT NULL THEN 1 END) as profiles_with_web_data,
                           COUNT(CASE WHEN board_members IS NOT NULL THEN 1 END) as profiles_with_board_data
                    FROM profiles
                    WHERE status = 'active'
                """)
                profile_stats = cursor.fetchone()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'data_quality_metrics': quality_metrics,
                'transformation_statistics': {
                    'total_transformations_30_days': transformation_stats[0],
                    'successful_transformations_30_days': transformation_stats[1],
                    'success_rate_percent': round((transformation_stats[1] / max(transformation_stats[0], 1)) * 100, 1),
                    'avg_processing_time_seconds': round(transformation_stats[2] or 0, 2),
                    'total_records_processed_30_days': transformation_stats[3] or 0
                },
                'profile_coverage': {
                    'total_active_profiles': profile_stats[0],
                    'profiles_with_web_data': profile_stats[1],
                    'profiles_with_board_data': profile_stats[2],
                    'web_data_coverage_percent': round((profile_stats[1] / max(profile_stats[0], 1)) * 100, 1),
                    'board_data_coverage_percent': round((profile_stats[2] / max(profile_stats[0], 1)) * 100, 1)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate data quality report: {e}")
            return {'error': str(e), 'generated_at': datetime.now().isoformat()}
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old transformation data
        
        Args:
            days_old: Number of days old for data to be considered for cleanup
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cleanup_stats = {
                'transformation_records_deleted': 0,
                'errors': []
            }
            
            # Clean up old transformation history
            deleted_count = self.integrator.normalized_db.cleanup_old_transformations(days_old)
            cleanup_stats['transformation_records_deleted'] = deleted_count
            
            logger.info(f"Cleanup completed: {deleted_count} transformation records deleted")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {'transformation_records_deleted': 0, 'errors': [str(e)]}
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current transformation configuration
        
        Returns:
            Dictionary with validation results and recommendations
        """
        try:
            validation_results = {
                'config_valid': True,
                'warnings': [],
                'recommendations': [],
                'current_config': self.config.dict()
            }
            
            # Check name parsing configuration
            if self.config.name_parsing.min_name_length < 2:
                validation_results['warnings'].append(
                    "Minimum name length is very low (< 2), may accept invalid names"
                )
                
            # Check deduplication settings
            if self.config.deduplication.fuzzy_match_threshold > 0.95:
                validation_results['warnings'].append(
                    "Fuzzy match threshold is very high (> 0.95), may miss valid duplicates"
                )
            elif self.config.deduplication.fuzzy_match_threshold < 0.7:
                validation_results['warnings'].append(
                    "Fuzzy match threshold is low (< 0.7), may create false positive matches"
                )
                
            # Check performance settings
            if self.config.batch_size > 500:
                validation_results['recommendations'].append(
                    "Consider reducing batch size for better memory usage"
                )
                
            if self.config.max_processing_time < 60:
                validation_results['recommendations'].append(
                    "Processing timeout is very short, may interrupt large transformations"
                )
                
            # Check if auto-merge is enabled without sufficient safeguards
            if (self.config.auto_merge_duplicates and 
                self.config.deduplication.fuzzy_match_threshold < 0.9):
                validation_results['warnings'].append(
                    "Auto-merge is enabled with low fuzzy match threshold, may merge non-duplicates"
                )
                
            validation_results['config_valid'] = len(validation_results['warnings']) == 0
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return {
                'config_valid': False,
                'warnings': [f"Validation error: {e}"],
                'recommendations': [],
                'current_config': {}
            }
    
    def _prepare_json_data(self, profile: Profile, 
                         web_scraping_results: Optional[Dict[str, Any]],
                         board_members_json: Optional[List[Dict[str, Any]]],
                         verification_data: Optional[Dict[str, Any]]) -> DatabaseJSONFields:
        """Prepare and validate JSON data for transformation"""
        try:
            # Convert web scraping results to WebScrapingResults model
            web_data = None
            if web_scraping_results:
                try:
                    web_data = WebScrapingResults.parse_obj(web_scraping_results)
                except Exception as e:
                    logger.warning(f"Failed to parse web scraping results: {e}")
                    
            # Convert board members to BoardMemberData models
            board_data = None
            if board_members_json:
                try:
                    board_data = [BoardMemberData.parse_obj(member) for member in board_members_json]
                except Exception as e:
                    logger.warning(f"Failed to parse board members: {e}")
                    
            # Use existing profile data as fallback
            if not web_data and profile.web_enhanced_data:
                try:
                    if isinstance(profile.web_enhanced_data, str):
                        web_dict = json.loads(profile.web_enhanced_data)
                    else:
                        web_dict = profile.web_enhanced_data
                    web_data = WebScrapingResults.parse_obj(web_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse existing web data: {e}")
                    
            if not board_data and profile.board_members:
                try:
                    if isinstance(profile.board_members, str):
                        board_list = json.loads(profile.board_members)
                    else:
                        board_list = profile.board_members
                    board_data = [BoardMemberData.parse_obj(member) for member in board_list]
                except Exception as e:
                    logger.warning(f"Failed to parse existing board data: {e}")
                    
            if not verification_data and profile.verification_data:
                try:
                    if isinstance(profile.verification_data, str):
                        verification_data = json.loads(profile.verification_data)
                    else:
                        verification_data = profile.verification_data
                except Exception as e:
                    logger.warning(f"Failed to parse existing verification data: {e}")
            
            return DatabaseJSONFields(
                board_members=board_data,
                web_enhanced_data=web_data,
                verification_data=verification_data
            )
            
        except Exception as e:
            logger.error(f"Failed to prepare JSON data: {e}")
            raise

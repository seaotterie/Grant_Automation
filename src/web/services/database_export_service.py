#!/usr/bin/env python3
"""
Database Export Service
Extends the existing export capabilities to work with the new SQLite database
Integrates with the query interface for advanced filtering and export
"""

import json
import csv
import io
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import our database components
try:
    from src.database.query_interface import DatabaseQueryInterface, QueryFilter, QuerySort
    from src.core.ai_cost_tracker import get_cost_tracker
except ImportError:
    from database.query_interface import DatabaseQueryInterface, QueryFilter, QuerySort
    from core.ai_cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class DatabaseExportFormat(Enum):
    """Enhanced export formats for database exports"""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    ENHANCED_JSON = "enhanced_json"
    SUMMARY_JSON = "summary_json"


@dataclass
class ExportConfiguration:
    """Configuration for database export operations"""
    format: DatabaseExportFormat
    include_metadata: bool = True
    include_analytics: bool = True
    timestamp_format: str = "%Y-%m-%d_%H-%M-%S"
    max_records: Optional[int] = None
    filters: Optional[QueryFilter] = None
    sort: Optional[QuerySort] = None


class DatabaseExportService:
    """
    Enhanced export service that integrates with the new database system
    Extends existing export capabilities with database-driven functionality
    """
    
    def __init__(self, database_path: Optional[str] = None):
        self.qi = DatabaseQueryInterface(database_path or "data/catalynx.db")
        self.cost_tracker = get_cost_tracker()
        self.export_path = Path("data/consolidated/exports")
        self.export_path.mkdir(exist_ok=True)
        
        logger.info(f"Database Export Service initialized with database: {database_path or 'data/catalynx.db'}")
    
    def export_opportunities(
        self,
        config: ExportConfiguration,
        profile_id: Optional[str] = None,
        filename_prefix: str = "opportunities_export"
    ) -> Dict[str, Any]:
        """
        Export opportunities from database with advanced filtering
        
        Args:
            config: Export configuration
            profile_id: Specific profile to export (optional)
            filename_prefix: Prefix for generated filename
            
        Returns:
            Dict with export results and metadata
        """
        try:
            # Apply profile filter if specified
            if profile_id and config.filters:
                if not config.filters.profile_ids:
                    config.filters.profile_ids = [profile_id]
                elif profile_id not in config.filters.profile_ids:
                    config.filters.profile_ids.append(profile_id)
            elif profile_id:
                config.filters = QueryFilter(profile_ids=[profile_id])
            
            # Query opportunities from database
            filters = config.filters or QueryFilter()  # Use empty filter if none provided
            opportunities, total_count = self.qi.filter_opportunities(
                filters=filters,
                sort=config.sort,
                limit=config.max_records
            )
            
            logger.info(f"Retrieved {len(opportunities)} opportunities for export")
            
            if not opportunities:
                return {
                    "success": False,
                    "error": "No opportunities found matching the criteria",
                    "total_count": 0
                }
            
            # Generate export based on format
            result = self._generate_export(opportunities, total_count, config, filename_prefix)
            
            # Add cost tracking if enabled
            if config.include_metadata:
                cost_summary = self.cost_tracker.get_cost_analytics(days=7)
                result["cost_summary"] = cost_summary
            
            return result
            
        except Exception as e:
            logger.error(f"Export opportunities failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_count": 0
            }
    
    def export_profiles(
        self,
        config: ExportConfiguration,
        filename_prefix: str = "profiles_export"
    ) -> Dict[str, Any]:
        """Export profiles from database"""
        try:
            filters = config.filters or QueryFilter()  # Use empty filter if none provided
            profiles, total_count = self.qi.filter_profiles(
                filters=filters,
                sort=config.sort,
                limit=config.max_records
            )
            
            logger.info(f"Retrieved {len(profiles)} profiles for export")
            
            if not profiles:
                return {
                    "success": False,
                    "error": "No profiles found matching the criteria",
                    "total_count": 0
                }
            
            return self._generate_export(profiles, total_count, config, filename_prefix)
            
        except Exception as e:
            logger.error(f"Export profiles failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_count": 0
            }
    
    def export_analytics_report(
        self,
        profile_id: Optional[str] = None,
        days: int = 30,
        format: DatabaseExportFormat = DatabaseExportFormat.ENHANCED_JSON
    ) -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        try:
            # Get analytics data
            analytics = self.qi.get_opportunity_analytics(profile_id, 
                                                        date_range=None if days == 30 else 
                                                        (datetime.now().date() - timedelta(days=days), 
                                                         datetime.now().date()))
            
            # Get cost analytics
            cost_analytics = self.cost_tracker.get_cost_analytics(days=days)
            
            # Get system performance if available
            performance_data = {}
            try:
                from src.core.system_monitor import get_system_monitor
                monitor = get_system_monitor()
                performance_data = monitor.get_performance_report(hours=24)
            except Exception as e:
                logger.warning(f"Could not get performance data: {e}")
            
            # Combine analytics
            report_data = {
                "metadata": {
                    "report_type": "comprehensive_analytics",
                    "profile_id": profile_id,
                    "period_days": days,
                    "generated_at": datetime.now().isoformat(),
                    "database_source": "catalynx.db"
                },
                "opportunity_analytics": analytics,
                "cost_analytics": cost_analytics,
                "performance_data": performance_data
            }
            
            # Save to file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"analytics_report_{timestamp}.json"
            filepath = self.export_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return {
                "success": True,
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size,
                "format": format.value,
                "record_count": len(analytics.get('top_organizations', {})),
                "analytics_summary": {
                    "total_opportunities": analytics.get('summary', {}).get('total_opportunities', 0),
                    "avg_score": analytics.get('summary', {}).get('avg_score', 0),
                    "total_cost": cost_analytics.get('total_cost', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Export analytics report failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_export(
        self,
        data: List[Dict],
        total_count: int,
        config: ExportConfiguration,
        filename_prefix: str
    ) -> Dict[str, Any]:
        """Generate export file in specified format"""
        timestamp = datetime.now().strftime(config.timestamp_format)
        
        try:
            if config.format == DatabaseExportFormat.JSON:
                return self._export_json(data, total_count, config, filename_prefix, timestamp)
            
            elif config.format == DatabaseExportFormat.ENHANCED_JSON:
                return self._export_enhanced_json(data, total_count, config, filename_prefix, timestamp)
            
            elif config.format == DatabaseExportFormat.CSV:
                return self._export_csv(data, total_count, config, filename_prefix, timestamp)
            
            elif config.format == DatabaseExportFormat.XLSX:
                return self._export_xlsx(data, total_count, config, filename_prefix, timestamp)
            
            elif config.format == DatabaseExportFormat.SUMMARY_JSON:
                return self._export_summary_json(data, total_count, config, filename_prefix, timestamp)
            
            else:
                raise ValueError(f"Unsupported export format: {config.format}")
                
        except Exception as e:
            logger.error(f"Export generation failed: {e}")
            raise
    
    def _export_json(self, data: List[Dict], total_count: int, config: ExportConfiguration, 
                    prefix: str, timestamp: str) -> Dict[str, Any]:
        """Export as standard JSON"""
        export_data = {
            "metadata": {
                "export_timestamp": timestamp,
                "total_records": len(data),
                "total_available": total_count,
                "format": "json"
            } if config.include_metadata else {},
            "data": data
        }
        
        filename = f"{prefix}_{timestamp}.json"
        filepath = self.export_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return {
            "success": True,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size,
            "format": "json",
            "record_count": len(data)
        }
    
    def _export_enhanced_json(self, data: List[Dict], total_count: int, config: ExportConfiguration,
                             prefix: str, timestamp: str) -> Dict[str, Any]:
        """Export as enhanced JSON with analytics"""
        # Calculate analytics if enabled
        analytics = {}
        if config.include_analytics and data:
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(data)
                
                # Calculate statistics for numeric columns
                numeric_columns = df.select_dtypes(include=['number']).columns
                for col in numeric_columns:
                    if col == 'overall_score':
                        analytics['score_statistics'] = df[col].describe().to_dict()
                    elif 'cost' in col.lower():
                        analytics['cost_statistics'] = df[col].describe().to_dict()
                
                # Calculate categorical distributions
                categorical_columns = df.select_dtypes(include=['object']).columns
                for col in categorical_columns:
                    if col in ['current_stage', 'organization_type']:
                        analytics[f'{col}_distribution'] = df[col].value_counts().to_dict()
        
        export_data = {
            "metadata": {
                "export_timestamp": timestamp,
                "total_records": len(data),
                "total_available": total_count,
                "format": "enhanced_json",
                "database_source": "catalynx.db",
                "pandas_available": PANDAS_AVAILABLE
            },
            "analytics": analytics,
            "data": data
        }
        
        filename = f"{prefix}_enhanced_{timestamp}.json"
        filepath = self.export_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return {
            "success": True,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size,
            "format": "enhanced_json",
            "record_count": len(data),
            "analytics_included": bool(analytics)
        }
    
    def _export_csv(self, data: List[Dict], total_count: int, config: ExportConfiguration,
                   prefix: str, timestamp: str) -> Dict[str, Any]:
        """Export as CSV"""
        filename = f"{prefix}_{timestamp}.csv"
        filepath = self.export_path / filename
        
        if data:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        return {
            "success": True,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size if filepath.exists() else 0,
            "format": "csv",
            "record_count": len(data)
        }
    
    def _export_xlsx(self, data: List[Dict], total_count: int, config: ExportConfiguration,
                    prefix: str, timestamp: str) -> Dict[str, Any]:
        """Export as Excel (requires pandas and openpyxl)"""
        if not PANDAS_AVAILABLE:
            raise ValueError("Pandas is required for Excel export")
        
        filename = f"{prefix}_{timestamp}.xlsx"
        filepath = self.export_path / filename
        
        df = pd.DataFrame(data)
        
        try:
            # Try with openpyxl engine
            df.to_excel(filepath, index=False, sheet_name='Data', engine='openpyxl')
        except ImportError:
            # Fallback to default engine
            df.to_excel(filepath, index=False, sheet_name='Data')
        
        return {
            "success": True,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size,
            "format": "xlsx",
            "record_count": len(data),
            "sheets": ["Data"]
        }
    
    def _export_summary_json(self, data: List[Dict], total_count: int, config: ExportConfiguration,
                           prefix: str, timestamp: str) -> Dict[str, Any]:
        """Export as summary JSON with key statistics only"""
        summary = {
            "export_summary": {
                "timestamp": timestamp,
                "total_records": len(data),
                "total_available": total_count,
                "format": "summary_json"
            }
        }
        
        # Add key statistics
        if data and PANDAS_AVAILABLE:
            df = pd.DataFrame(data)
            
            summary["key_statistics"] = {
                "total_opportunities": len(data),
                "unique_organizations": df['organization_name'].nunique() if 'organization_name' in df.columns else 0,
                "avg_score": df['overall_score'].mean() if 'overall_score' in df.columns else 0,
                "stage_distribution": df['current_stage'].value_counts().to_dict() if 'current_stage' in df.columns else {},
                "date_range": {
                    "earliest": df['discovery_date'].min() if 'discovery_date' in df.columns else None,
                    "latest": df['discovery_date'].max() if 'discovery_date' in df.columns else None
                }
            }
        
        filename = f"{prefix}_summary_{timestamp}.json"
        filepath = self.export_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return {
            "success": True,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size,
            "format": "summary_json",
            "record_count": len(data)
        }
    
    def get_available_formats(self) -> List[str]:
        """Get list of available export formats"""
        formats = [fmt.value for fmt in DatabaseExportFormat]
        
        # Check if optional formats are available
        if not PANDAS_AVAILABLE:
            formats = [fmt for fmt in formats if fmt != "xlsx"]
        
        return formats
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exports in the export directory"""
        try:
            export_files = list(self.export_path.glob("*"))
            
            stats = {
                "total_files": len(export_files),
                "total_size_bytes": sum(f.stat().st_size for f in export_files if f.is_file()),
                "formats": {},
                "recent_exports": []
            }
            
            # Group by format
            for file in export_files:
                if file.is_file():
                    suffix = file.suffix.lower()
                    if suffix not in stats["formats"]:
                        stats["formats"][suffix] = 0
                    stats["formats"][suffix] += 1
                    
                    # Add to recent exports
                    stats["recent_exports"].append({
                        "filename": file.name,
                        "size_bytes": file.stat().st_size,
                        "modified": file.stat().st_mtime
                    })
            
            # Sort recent exports by modification time
            stats["recent_exports"].sort(key=lambda x: x["modified"], reverse=True)
            stats["recent_exports"] = stats["recent_exports"][:10]  # Keep last 10
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
            return {"error": str(e)}


# Factory function for easy access
def get_database_export_service(database_path: Optional[str] = None) -> DatabaseExportService:
    """Get a configured database export service instance"""
    return DatabaseExportService(database_path)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    service = get_database_export_service()
    
    # Test enhanced export
    config = ExportConfiguration(
        format=DatabaseExportFormat.ENHANCED_JSON,
        include_metadata=True,
        include_analytics=True,
        max_records=10
    )
    
    result = service.export_opportunities(config)
    print(f"Export result: {result}")
    
    # Test export stats
    stats = service.get_export_stats()
    print(f"Export stats: {stats}")
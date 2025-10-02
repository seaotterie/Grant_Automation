"""
Advanced Search and Export Service

Provides comprehensive search capabilities across opportunities with flexible filtering,
sorting, and export functionality using the unified architecture.
"""

import json
import csv
import io
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import pandas as pd

from src.profiles.unified_service import get_unified_profile_service
from src.profiles.models import UnifiedOpportunity

logger = logging.getLogger(__name__)


class SearchOperator(Enum):
    """Search operators for advanced filtering"""
    EQUALS = "equals"
    CONTAINS = "contains" 
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    BETWEEN = "between"
    IN_LIST = "in"
    NOT_IN_LIST = "not_in"


class SortDirection(Enum):
    """Sort direction options"""
    ASC = "asc"
    DESC = "desc"


class ExportFormat(Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"  # For future implementation


@dataclass
class SearchFilter:
    """Individual search filter"""
    field: str
    operator: SearchOperator
    value: Any
    value2: Optional[Any] = None  # For BETWEEN operator


@dataclass
class SearchCriteria:
    """Complete search criteria"""
    filters: List[SearchFilter]
    sort_by: Optional[str] = None
    sort_direction: SortDirection = SortDirection.DESC
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class SearchResults:
    """Search results with metadata"""
    opportunities: List[UnifiedOpportunity]
    total_count: int
    filtered_count: int
    page_info: Dict[str, Any]
    search_metadata: Dict[str, Any]


class AdvancedSearchService:
    """Advanced search service for opportunities with unified architecture integration"""
    
    def __init__(self):
        self.unified_service = get_unified_profile_service()
        self.logger = logging.getLogger(__name__)
    
    def search_opportunities(
        self, 
        criteria: SearchCriteria,
        profile_id: Optional[str] = None
    ) -> SearchResults:
        """
        Perform advanced search across opportunities
        
        Args:
            criteria: Search criteria with filters and sorting
            profile_id: Optional profile ID to limit search scope
            
        Returns:
            SearchResults with matched opportunities and metadata
        """
        try:
            # Get opportunities to search
            if profile_id:
                opportunities = self.unified_service.get_profile_opportunities(profile_id)
                total_count = len(opportunities)
            else:
                # Search across all profiles
                opportunities = []
                all_profile_ids = self.unified_service.list_profiles()  # Returns list of profile_id strings
                for profile_id in all_profile_ids:
                    profile_opportunities = self.unified_service.get_profile_opportunities(profile_id)
                    opportunities.extend(profile_opportunities)
                total_count = len(opportunities)
            
            # Apply filters
            filtered_opportunities = self._apply_filters(opportunities, criteria.filters)
            filtered_count = len(filtered_opportunities)
            
            # Apply sorting
            if criteria.sort_by:
                filtered_opportunities = self._apply_sorting(
                    filtered_opportunities, 
                    criteria.sort_by, 
                    criteria.sort_direction
                )
            
            # Apply pagination
            paginated_opportunities, page_info = self._apply_pagination(
                filtered_opportunities,
                criteria.limit,
                criteria.offset
            )
            
            # Create search metadata
            search_metadata = {
                "search_timestamp": datetime.now().isoformat(),
                "filters_applied": len(criteria.filters),
                "sort_by": criteria.sort_by,
                "sort_direction": criteria.sort_direction.value if criteria.sort_direction else None,
                "profile_scope": "single" if profile_id else "global",
                "execution_time_ms": 0  # Would measure in real implementation
            }
            
            return SearchResults(
                opportunities=paginated_opportunities,
                total_count=total_count,
                filtered_count=filtered_count,
                page_info=page_info,
                search_metadata=search_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to search opportunities: {e}")
            raise
    
    def _apply_filters(
        self, 
        opportunities: List[UnifiedOpportunity], 
        filters: List[SearchFilter]
    ) -> List[UnifiedOpportunity]:
        """Apply search filters to opportunity list"""
        
        if not filters:
            return opportunities
        
        filtered = []
        for opp in opportunities:
            if self._opportunity_matches_filters(opp, filters):
                filtered.append(opp)
        
        return filtered
    
    def _opportunity_matches_filters(
        self, 
        opportunity: UnifiedOpportunity, 
        filters: List[SearchFilter]
    ) -> bool:
        """Check if opportunity matches all filters (AND logic)"""
        
        for filter_item in filters:
            if not self._evaluate_filter(opportunity, filter_item):
                return False
        
        return True
    
    def _evaluate_filter(
        self, 
        opportunity: UnifiedOpportunity, 
        filter_item: SearchFilter
    ) -> bool:
        """Evaluate a single filter against an opportunity"""
        
        field_value = self._get_field_value(opportunity, filter_item.field)
        
        if field_value is None:
            return False
        
        operator = filter_item.operator
        filter_value = filter_item.value
        
        try:
            if operator == SearchOperator.EQUALS:
                return field_value == filter_value
            elif operator == SearchOperator.CONTAINS:
                return str(filter_value).lower() in str(field_value).lower()
            elif operator == SearchOperator.STARTS_WITH:
                return str(field_value).lower().startswith(str(filter_value).lower())
            elif operator == SearchOperator.ENDS_WITH:
                return str(field_value).lower().endswith(str(filter_value).lower())
            elif operator == SearchOperator.GREATER_THAN:
                return float(field_value) > float(filter_value)
            elif operator == SearchOperator.LESS_THAN:
                return float(field_value) < float(filter_value)
            elif operator == SearchOperator.BETWEEN:
                value2 = filter_item.value2
                if value2 is not None:
                    return float(filter_value) <= float(field_value) <= float(value2)
            elif operator == SearchOperator.IN_LIST:
                return field_value in filter_value if isinstance(filter_value, list) else False
            elif operator == SearchOperator.NOT_IN_LIST:
                return field_value not in filter_value if isinstance(filter_value, list) else True
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Filter evaluation error for field {filter_item.field}: {e}")
            return False
        
        return False
    
    def _get_field_value(self, opportunity: UnifiedOpportunity, field_path: str) -> Any:
        """Get field value from opportunity using dot notation (e.g., 'scoring.overall_score')"""
        
        try:
            obj = opportunity
            
            # Handle nested fields
            for field_part in field_path.split('.'):
                if hasattr(obj, field_part):
                    obj = getattr(obj, field_part)
                elif isinstance(obj, dict) and field_part in obj:
                    obj = obj[field_part]
                else:
                    return None
            
            return obj
            
        except Exception:
            return None
    
    def _apply_sorting(
        self,
        opportunities: List[UnifiedOpportunity],
        sort_by: str,
        sort_direction: SortDirection
    ) -> List[UnifiedOpportunity]:
        """Apply sorting to opportunity list"""
        
        try:
            reverse = sort_direction == SortDirection.DESC
            
            def sort_key(opp):
                value = self._get_field_value(opp, sort_by)
                # Handle None values by putting them at the end
                if value is None:
                    return float('inf') if not reverse else float('-inf')
                # Convert to string for consistent comparison if not numeric
                if not isinstance(value, (int, float)):
                    return str(value).lower()
                return value
            
            return sorted(opportunities, key=sort_key, reverse=reverse)
            
        except Exception as e:
            self.logger.warning(f"Failed to sort by {sort_by}: {e}")
            return opportunities
    
    def _apply_pagination(
        self,
        opportunities: List[UnifiedOpportunity],
        limit: Optional[int],
        offset: int
    ) -> Tuple[List[UnifiedOpportunity], Dict[str, Any]]:
        """Apply pagination to opportunity list"""
        
        total_items = len(opportunities)
        
        # Apply offset
        start_index = max(0, offset)
        
        # Apply limit
        if limit:
            end_index = start_index + limit
            paginated = opportunities[start_index:end_index]
        else:
            paginated = opportunities[start_index:]
            end_index = len(opportunities)
        
        # Calculate page info
        page_info = {
            "total_items": total_items,
            "items_on_page": len(paginated),
            "offset": offset,
            "limit": limit,
            "has_next": end_index < total_items,
            "has_previous": start_index > 0,
            "next_offset": end_index if end_index < total_items else None,
            "previous_offset": max(0, start_index - (limit or 20)) if start_index > 0 else None
        }
        
        return paginated, page_info
    
    def export_opportunities(
        self,
        opportunities: List[UnifiedOpportunity],
        format: ExportFormat,
        include_analytics: bool = True
    ) -> bytes:
        """Export opportunities to specified format"""
        
        try:
            if format == ExportFormat.JSON:
                return self._export_json(opportunities, include_analytics)
            elif format == ExportFormat.CSV:
                return self._export_csv(opportunities, include_analytics)
            elif format == ExportFormat.XLSX:
                return self._export_xlsx(opportunities, include_analytics)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export opportunities: {e}")
            raise
    
    def _export_json(self, opportunities: List[UnifiedOpportunity], include_analytics: bool) -> bytes:
        """Export opportunities as JSON"""
        
        export_data = {
            "export_metadata": {
                "format": "json",
                "exported_at": datetime.now().isoformat(),
                "total_opportunities": len(opportunities),
                "include_analytics": include_analytics
            },
            "opportunities": []
        }
        
        for opp in opportunities:
            opp_data = opp.model_dump()
            if not include_analytics:
                # Remove analytics fields
                opp_data.pop('analysis', None)
                opp_data.pop('promotion_history', None)
                opp_data.pop('stage_history', None)
            
            export_data["opportunities"].append(opp_data)
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_csv(self, opportunities: List[UnifiedOpportunity], include_analytics: bool) -> bytes:
        """Export opportunities as CSV"""
        
        if not opportunities:
            return b""
        
        output = io.StringIO()
        
        # Define CSV columns
        basic_columns = [
            'opportunity_id', 'organization_name', 'ein', 'current_stage',
            'opportunity_type', 'funding_amount', 'program_name', 'description',
            'discovered_at', 'last_updated', 'status'
        ]
        
        analytics_columns = [
            'overall_score', 'confidence_level', 'auto_promotion_eligible',
            'promotion_recommended', 'total_promotions', 'last_scored'
        ] if include_analytics else []
        
        all_columns = basic_columns + analytics_columns
        writer = csv.DictWriter(output, fieldnames=all_columns)
        writer.writeheader()
        
        for opp in opportunities:
            row = {
                'opportunity_id': opp.opportunity_id,
                'organization_name': opp.organization_name,
                'ein': opp.ein,
                'current_stage': opp.current_stage,
                'opportunity_type': opp.opportunity_type,
                'funding_amount': opp.funding_amount,
                'program_name': opp.program_name,
                'description': opp.description,
                'discovered_at': opp.discovered_at,
                'last_updated': opp.last_updated,
                'status': opp.status
            }
            
            if include_analytics and opp.scoring:
                row.update({
                    'overall_score': opp.scoring.overall_score,
                    'confidence_level': opp.scoring.confidence_level,
                    'auto_promotion_eligible': opp.scoring.auto_promotion_eligible,
                    'promotion_recommended': opp.scoring.promotion_recommended,
                    'total_promotions': len(opp.promotion_history),
                    'last_scored': opp.scoring.scored_at
                })
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')
    
    def _export_xlsx(self, opportunities: List[UnifiedOpportunity], include_analytics: bool) -> bytes:
        """Export opportunities as Excel file"""
        
        if not opportunities:
            return b""
        
        # Convert to DataFrame
        data = []
        for opp in opportunities:
            row = {
                'Opportunity ID': opp.opportunity_id,
                'Organization Name': opp.organization_name,
                'EIN': opp.ein,
                'Current Stage': opp.current_stage,
                'Opportunity Type': opp.opportunity_type,
                'Funding Amount': opp.funding_amount,
                'Program Name': opp.program_name,
                'Description': opp.description[:100] + '...' if opp.description and len(opp.description) > 100 else opp.description,
                'Discovered At': opp.discovered_at,
                'Last Updated': opp.last_updated,
                'Status': opp.status
            }
            
            if include_analytics and opp.scoring:
                row.update({
                    'Overall Score': opp.scoring.overall_score,
                    'Confidence Level': opp.scoring.confidence_level,
                    'Auto Promotion Eligible': opp.scoring.auto_promotion_eligible,
                    'Promotion Recommended': opp.scoring.promotion_recommended,
                    'Total Promotions': len(opp.promotion_history),
                    'Last Scored': opp.scoring.scored_at
                })
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Opportunities', index=False)
            
            # Add metadata sheet
            metadata_df = pd.DataFrame({
                'Export Information': [
                    'Export Format',
                    'Exported At',
                    'Total Opportunities',
                    'Analytics Included'
                ],
                'Value': [
                    'xlsx',
                    datetime.now().isoformat(),
                    len(opportunities),
                    include_analytics
                ]
            })
            metadata_df.to_excel(writer, sheet_name='Export Metadata', index=False)
        
        excel_buffer.seek(0)
        return excel_buffer.read()


# Singleton instance
_search_service = None

def get_search_export_service() -> AdvancedSearchService:
    """Get singleton search and export service instance"""
    global _search_service
    if _search_service is None:
        _search_service = AdvancedSearchService()
    return _search_service
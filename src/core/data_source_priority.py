#!/usr/bin/env python3
"""
Data Source Priority and Conflict Resolution System

Manages conflicts between multiple data sources (ProPublica, BMF, web scraping)
with priority-based resolution and data quality scoring.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source types with inherent priority order"""
    USER_PROVIDED = "user_provided"          # Priority 1: User knows the organization
    TAX_FILING_990 = "990_tax_filing"        # Priority 2: Official IRS data
    BMF_DATABASE = "bmf_database"            # Priority 3: IRS Business Master File
    PROPUBLICA_990 = "propublica_990"        # Priority 4: ProPublica 990 data
    WEB_SCRAPING = "web_scraping"            # Priority 5: Web scraped data
    GPT_PREDICTION = "gpt_prediction"        # Priority 6: AI-generated predictions
    ENHANCED_990 = "enhanced_990_supplemental" # Priority 7: Secondary 990 analysis


@dataclass
class DataSourceEntry:
    """Single data entry with source attribution"""
    value: Any
    source: DataSource
    confidence_score: float  # 0.0 - 1.0
    timestamp: Optional[str] = None
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class DataPriorityResolver:
    """Resolves conflicts between multiple data sources using priority and quality scoring"""

    # Source priority mapping (lower number = higher priority)
    SOURCE_PRIORITY = {
        DataSource.USER_PROVIDED: 1,
        DataSource.TAX_FILING_990: 2,
        DataSource.BMF_DATABASE: 3,
        DataSource.PROPUBLICA_990: 4,
        DataSource.WEB_SCRAPING: 5,
        DataSource.GPT_PREDICTION: 6,
        DataSource.ENHANCED_990: 7
    }

    # Base confidence scores by source type
    BASE_CONFIDENCE = {
        DataSource.USER_PROVIDED: 0.95,
        DataSource.TAX_FILING_990: 0.90,
        DataSource.BMF_DATABASE: 0.85,
        DataSource.PROPUBLICA_990: 0.80,
        DataSource.WEB_SCRAPING: 0.70,
        DataSource.GPT_PREDICTION: 0.60,
        DataSource.ENHANCED_990: 0.65
    }

    def __init__(self):
        self.resolution_stats = {
            'total_conflicts': 0,
            'priority_resolutions': 0,
            'confidence_resolutions': 0,
            'merge_resolutions': 0
        }

    def resolve_field_conflict(
        self,
        field_name: str,
        data_entries: List[DataSourceEntry]
    ) -> Tuple[DataSourceEntry, Dict[str, Any]]:
        """
        Resolve conflict for a single field with multiple data sources.

        Args:
            field_name: Name of the field being resolved
            data_entries: List of data entries from different sources

        Returns:
            Tuple of (selected_entry, resolution_metadata)
        """
        if not data_entries:
            raise ValueError("No data entries provided")

        if len(data_entries) == 1:
            return data_entries[0], {'resolution_type': 'no_conflict'}

        self.resolution_stats['total_conflicts'] += 1

        # Filter out None/empty values
        valid_entries = [entry for entry in data_entries if self._is_valid_value(entry.value)]

        if not valid_entries:
            # Return first entry even if invalid
            return data_entries[0], {'resolution_type': 'no_valid_data'}

        if len(valid_entries) == 1:
            return valid_entries[0], {'resolution_type': 'single_valid'}

        # Check for exact matches (no conflict)
        unique_values = set(str(entry.value).strip().lower() for entry in valid_entries)
        if len(unique_values) == 1:
            # All values are the same, return highest priority source
            best_entry = min(valid_entries, key=lambda x: self.SOURCE_PRIORITY[x.source])
            return best_entry, {'resolution_type': 'identical_values'}

        # Resolve using priority and confidence
        return self._resolve_by_priority_and_confidence(field_name, valid_entries)

    def _resolve_by_priority_and_confidence(
        self,
        field_name: str,
        entries: List[DataSourceEntry]
    ) -> Tuple[DataSourceEntry, Dict[str, Any]]:
        """Resolve using source priority and confidence scores"""

        # Group by priority level
        priority_groups = {}
        for entry in entries:
            priority = self.SOURCE_PRIORITY[entry.source]
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(entry)

        # Start with highest priority group
        for priority in sorted(priority_groups.keys()):
            group_entries = priority_groups[priority]

            if len(group_entries) == 1:
                self.resolution_stats['priority_resolutions'] += 1
                return group_entries[0], {
                    'resolution_type': 'priority_based',
                    'winning_priority': priority,
                    'rejected_sources': [e.source.value for e in entries if e not in group_entries]
                }

            # Multiple entries at same priority - use confidence score
            best_entry = max(group_entries, key=lambda x: x.confidence_score)
            self.resolution_stats['confidence_resolutions'] += 1
            return best_entry, {
                'resolution_type': 'confidence_based',
                'winning_confidence': best_entry.confidence_score,
                'rejected_sources': [e.source.value for e in entries if e != best_entry]
            }

        # Fallback (shouldn't reach here)
        return entries[0], {'resolution_type': 'fallback'}

    def resolve_list_conflict(
        self,
        field_name: str,
        data_entries: List[DataSourceEntry]
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Resolve conflicts for list fields by merging unique values.

        Args:
            field_name: Name of the list field
            data_entries: List of data entries containing lists

        Returns:
            Tuple of (merged_list, resolution_metadata)
        """
        if not data_entries:
            return [], {'resolution_type': 'no_data'}

        # Collect all unique values with source attribution
        merged_items = []
        sources_used = []

        for entry in data_entries:
            if not self._is_valid_value(entry.value):
                continue

            entry_list = entry.value if isinstance(entry.value, list) else [entry.value]
            sources_used.append(entry.source.value)

            for item in entry_list:
                if item and item not in merged_items:
                    merged_items.append(item)

        self.resolution_stats['merge_resolutions'] += 1
        return merged_items, {
            'resolution_type': 'list_merge',
            'sources_used': sources_used,
            'total_items': len(merged_items)
        }

    def calculate_composite_confidence(self, entries: List[DataSourceEntry]) -> float:
        """Calculate composite confidence score across multiple sources"""
        if not entries:
            return 0.0

        # Weight by source priority and individual confidence
        total_weight = 0.0
        weighted_confidence = 0.0

        for entry in entries:
            if not self._is_valid_value(entry.value):
                continue

            priority_weight = 1.0 / self.SOURCE_PRIORITY[entry.source]  # Higher priority = higher weight
            confidence_weight = entry.confidence_score
            combined_weight = priority_weight * confidence_weight

            weighted_confidence += combined_weight
            total_weight += priority_weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _is_valid_value(self, value: Any) -> bool:
        """Check if a value is valid (not None, empty string, etc.)"""
        if value is None:
            return False
        if isinstance(value, str) and value.strip().lower() in ['', 'none', 'null', 'n/a', 'unknown']:
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        return True

    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get statistics about conflict resolutions"""
        total = self.resolution_stats['total_conflicts']
        return {
            **self.resolution_stats,
            'resolution_rate': (total - self.resolution_stats.get('fallback', 0)) / total if total > 0 else 0.0
        }


# Global resolver instance
_resolver_instance = None

def get_data_priority_resolver() -> DataPriorityResolver:
    """Get singleton data priority resolver"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = DataPriorityResolver()
    return _resolver_instance
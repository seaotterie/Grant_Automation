#!/usr/bin/env python3
"""
Entity Extraction Utilities

Analyzes current cache files to identify entity types and extract
identifiers for organizing into the new entity-based structure.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging


class EntityType(str, Enum):
    NONPROFIT = "nonprofit"
    FOUNDATION = "foundation" 
    CORPORATION = "corporation"
    GOVERNMENT_FEDERAL = "government_federal"
    GOVERNMENT_STATE = "government_state"
    UNKNOWN = "unknown"


@dataclass
class EntityIdentification:
    """Results of entity identification from cache file"""
    entity_type: EntityType
    entity_id: str
    confidence: float
    source_indicators: List[str]
    additional_metadata: Dict[str, Any]


class EntityExtractor:
    """
    Analyzes cache files to identify entity types and extract identifiers
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for efficiency
        self.ein_pattern = re.compile(r'\b(\d{2}-?\d{7})\b')
        self.opportunity_id_pattern = re.compile(r'\b([A-Z]{2,}-\d{4,}-[A-Z0-9\-]+)\b')
        self.foundation_id_pattern = re.compile(r'\b(FND-\d+|FOUND-\d+)\b')
        
    def analyze_cache_file(self, cache_file_path: Path) -> EntityIdentification:
        """
        Analyze a cache file to determine entity type and extract identifier
        """
        try:
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content) if content.strip() else {}
            
            # Analyze content to determine entity type
            return self._identify_entity_from_content(data, content, cache_file_path.name)
            
        except Exception as e:
            self.logger.error(f"Error analyzing cache file {cache_file_path}: {e}")
            return EntityIdentification(
                entity_type=EntityType.UNKNOWN,
                entity_id="unknown",
                confidence=0.0,
                source_indicators=[f"error: {str(e)}"],
                additional_metadata={}
            )
    
    def _identify_entity_from_content(self, data: Dict, content: str, filename: str) -> EntityIdentification:
        """
        Identify entity type from file content and structure
        """
        source_indicators = []
        additional_metadata = {}
        
        # Check for nonprofit indicators
        nonprofit_score = self._score_nonprofit_indicators(data, content, source_indicators)
        
        # Check for government indicators  
        government_score = self._score_government_indicators(data, content, source_indicators)
        
        # Check for foundation indicators
        foundation_score = self._score_foundation_indicators(data, content, source_indicators)
        
        # Check for corporation indicators
        corporation_score = self._score_corporation_indicators(data, content, source_indicators)
        
        # Determine best match
        scores = [
            (EntityType.NONPROFIT, nonprofit_score),
            (EntityType.GOVERNMENT_FEDERAL, government_score),
            (EntityType.FOUNDATION, foundation_score),
            (EntityType.CORPORATION, corporation_score)
        ]
        
        entity_type, confidence = max(scores, key=lambda x: x[1])
        
        # Extract entity ID based on type
        entity_id = self._extract_entity_id(entity_type, data, content, filename)
        
        return EntityIdentification(
            entity_type=entity_type,
            entity_id=entity_id,
            confidence=confidence,
            source_indicators=source_indicators,
            additional_metadata=additional_metadata
        )
    
    def _score_nonprofit_indicators(self, data: Dict, content: str, indicators: List[str]) -> float:
        """Score likelihood this is nonprofit data"""
        score = 0.0
        
        # EIN patterns (strongest indicator)
        ein_matches = self.ein_pattern.findall(content)
        if ein_matches:
            score += 0.4
            indicators.append(f"EIN found: {ein_matches[0]}")
        
        # Nonprofit-specific fields in data
        nonprofit_fields = ['ein', 'ntee_code', 'ruling_date', 'tax_exempt_status', 'subsection_code']
        found_fields = [field for field in nonprofit_fields if self._has_field(data, field)]
        if found_fields:
            score += 0.3
            indicators.append(f"Nonprofit fields: {found_fields}")
        
        # IRS/ProPublica API indicators
        irs_indicators = ['irs.gov', 'propublica', 'business_master_file', 'form_990']
        for indicator in irs_indicators:
            if indicator.lower() in content.lower():
                score += 0.1
                indicators.append(f"IRS/ProPublica: {indicator}")
        
        # NTEE codes
        if 'ntee' in content.lower() or self._contains_ntee_codes(content):
            score += 0.2
            indicators.append("NTEE codes found")
        
        return min(score, 1.0)
    
    def _score_government_indicators(self, data: Dict, content: str, indicators: List[str]) -> float:
        """Score likelihood this is government funding data"""
        score = 0.0
        
        # Government opportunity ID patterns
        opp_matches = self.opportunity_id_pattern.findall(content)
        if opp_matches:
            score += 0.5
            indicators.append(f"Opportunity ID: {opp_matches[0]}")
        
        # Government-specific fields
        gov_fields = ['funding_instrument', 'agency_code', 'cfda_number', 'award_id', 'recipient_duns']
        found_fields = [field for field in gov_fields if self._has_field(data, field)]
        if found_fields:
            score += 0.3
            indicators.append(f"Government fields: {found_fields}")
        
        # Government API indicators
        gov_apis = ['grants.gov', 'usaspending.gov', 'sam.gov']
        for api in gov_apis:
            if api.lower() in content.lower():
                score += 0.2
                indicators.append(f"Government API: {api}")
        
        # CFDA numbers (Catalog of Federal Domestic Assistance)
        if re.search(r'\b\d{2}\.\d{3}\b', content):
            score += 0.2
            indicators.append("CFDA number found")
        
        return min(score, 1.0)
    
    def _score_foundation_indicators(self, data: Dict, content: str, indicators: List[str]) -> float:
        """Score likelihood this is foundation data"""
        score = 0.0
        
        # Foundation ID patterns
        found_id = self.foundation_id_pattern.findall(content)
        if found_id:
            score += 0.4
            indicators.append(f"Foundation ID: {found_id[0]}")
        
        # Foundation-specific fields
        foundation_fields = ['foundation_type', 'total_giving', 'asset_amount', 'grants_list', 'board_members']
        found_fields = [field for field in foundation_fields if self._has_field(data, field)]
        if found_fields:
            score += 0.3
            indicators.append(f"Foundation fields: {found_fields}")
        
        # Foundation keywords
        foundation_keywords = ['foundation directory', 'candid', 'guidestar', 'grantmaking', 'private foundation']
        for keyword in foundation_keywords:
            if keyword.lower() in content.lower():
                score += 0.1
                indicators.append(f"Foundation keyword: {keyword}")
        
        # 990-PF form indicators
        if '990-pf' in content.lower() or '990pf' in content.lower():
            score += 0.3
            indicators.append("990-PF form found")
        
        return min(score, 1.0)
    
    def _score_corporation_indicators(self, data: Dict, content: str, indicators: List[str]) -> float:
        """Score likelihood this is corporate data"""
        score = 0.0
        
        # Corporate fields
        corp_fields = ['ticker_symbol', 'csr_programs', 'corporate_foundation', 'employee_count']
        found_fields = [field for field in corp_fields if self._has_field(data, field)]
        if found_fields:
            score += 0.3
            indicators.append(f"Corporate fields: {found_fields}")
        
        # Corporate keywords
        corp_keywords = ['corporate social responsibility', 'csr', 'corporate foundation', 'employee giving']
        for keyword in corp_keywords:
            if keyword.lower() in content.lower():
                score += 0.2
                indicators.append(f"Corporate keyword: {keyword}")
        
        return min(score, 1.0)
    
    def _extract_entity_id(self, entity_type: EntityType, data: Dict, content: str, filename: str) -> str:
        """Extract appropriate entity ID based on type"""
        
        if entity_type == EntityType.NONPROFIT:
            # Try to extract EIN
            ein_matches = self.ein_pattern.findall(content)
            if ein_matches:
                ein = ein_matches[0].replace('-', '')  # Normalize EIN format
                return ein
            
            # Try to find EIN in data structure
            ein_fields = ['ein', 'EIN', 'employer_id', 'tax_id']
            for field in ein_fields:
                value = self._get_nested_value(data, field)
                if value and isinstance(value, str) and re.match(r'\d{9}', value.replace('-', '')):
                    return value.replace('-', '')
        
        elif entity_type == EntityType.GOVERNMENT_FEDERAL:
            # Try to extract opportunity ID
            opp_matches = self.opportunity_id_pattern.findall(content)
            if opp_matches:
                return opp_matches[0]
            
            # Try other government ID patterns
            for field in ['opportunity_id', 'award_id', 'funding_opportunity_number']:
                value = self._get_nested_value(data, field)
                if value:
                    return str(value)
        
        elif entity_type == EntityType.FOUNDATION:
            # Try to extract foundation ID
            found_id = self.foundation_id_pattern.findall(content)
            if found_id:
                return found_id[0]
            
            # Try foundation-specific fields
            for field in ['foundation_id', 'org_id', 'foundation_ein']:
                value = self._get_nested_value(data, field)
                if value:
                    return str(value)
        
        # Fallback: use filename hash
        return f"cache_{filename.replace('.cache', '').replace('.json', '')}"
    
    def _has_field(self, data: Dict, field_name: str) -> bool:
        """Check if data structure contains a field (case-insensitive)"""
        return self._get_nested_value(data, field_name) is not None
    
    def _get_nested_value(self, data: Dict, field_name: str) -> Any:
        """Get value from nested dictionary structure (case-insensitive)"""
        if not isinstance(data, dict):
            return None
        
        # Direct key match (case-insensitive)
        for key, value in data.items():
            if key.lower() == field_name.lower():
                return value
        
        # Search nested dictionaries
        for key, value in data.items():
            if isinstance(value, dict):
                nested_result = self._get_nested_value(value, field_name)
                if nested_result is not None:
                    return nested_result
            elif isinstance(value, list) and value:
                # Search in list of dictionaries
                for item in value:
                    if isinstance(item, dict):
                        nested_result = self._get_nested_value(item, field_name)
                        if nested_result is not None:
                            return nested_result
        
        return None
    
    def _contains_ntee_codes(self, content: str) -> bool:
        """Check if content contains NTEE codes (e.g., A01, B20, etc.)"""
        ntee_pattern = re.compile(r'\b[A-Z]\d{2}\b')
        return bool(ntee_pattern.search(content))
    
    def analyze_cache_directory(self, cache_dir: Path) -> Dict[str, EntityIdentification]:
        """
        Analyze all cache files in directory and return entity identifications
        """
        results = {}
        
        if not cache_dir.exists():
            self.logger.error(f"Cache directory does not exist: {cache_dir}")
            return results
        
        cache_files = list(cache_dir.glob("*.cache")) + list(cache_dir.glob("*.json"))
        self.logger.info(f"Analyzing {len(cache_files)} cache files...")
        
        for cache_file in cache_files:
            try:
                identification = self.analyze_cache_file(cache_file)
                results[str(cache_file)] = identification
                
                if identification.confidence > 0.5:
                    self.logger.info(
                        f"Identified {identification.entity_type} "
                        f"(ID: {identification.entity_id}, "
                        f"Confidence: {identification.confidence:.2f}) "
                        f"in {cache_file.name}"
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing {cache_file}: {e}")
        
        return results
    
    def generate_migration_report(self, identifications: Dict[str, EntityIdentification]) -> Dict[str, Any]:
        """
        Generate summary report of entity identification results
        """
        report = {
            'total_files': len(identifications),
            'by_entity_type': {},
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'unknown': 0
        }
        
        for identification in identifications.values():
            # Count by entity type
            entity_type = identification.entity_type
            if entity_type not in report['by_entity_type']:
                report['by_entity_type'][entity_type] = 0
            report['by_entity_type'][entity_type] += 1
            
            # Count by confidence level
            if identification.confidence >= 0.8:
                report['high_confidence'] += 1
            elif identification.confidence >= 0.5:
                report['medium_confidence'] += 1
            elif identification.confidence > 0.0:
                report['low_confidence'] += 1
            else:
                report['unknown'] += 1
        
        return report


if __name__ == "__main__":
    # Example usage
    extractor = EntityExtractor()
    cache_dir = Path("data/cache/api_response")
    
    if cache_dir.exists():
        identifications = extractor.analyze_cache_directory(cache_dir)
        report = extractor.generate_migration_report(identifications)
        
        print(f"Migration Analysis Report:")
        print(f"Total files: {report['total_files']}")
        print(f"By entity type: {report['by_entity_type']}")
        print(f"High confidence: {report['high_confidence']}")
        print(f"Medium confidence: {report['medium_confidence']}")
        print(f"Low confidence: {report['low_confidence']}")
        print(f"Unknown: {report['unknown']}")
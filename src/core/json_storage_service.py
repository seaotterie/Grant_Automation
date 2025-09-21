#!/usr/bin/env python3
"""
JSON Storage Service for Web Scraping Data
Manages JSON-based storage of raw web scraping results with confidence scoring
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ScrapingMetadata:
    """Metadata for a scraping session"""
    ein: str
    timestamp: str
    urls_scraped: List[str]
    total_content_length: int
    processing_time_seconds: float
    extraction_method: str = 'adaptive_html'
    confidence_level: str = 'low'  # low, medium, high
    data_source: str = 'web_scraping'
    
@dataclass
class RawScrapingResult:
    """Complete raw scraping result with all context"""
    url: str
    html_content: str
    extracted_text: str
    page_type: Optional[str]  # 'homepage', 'leadership', 'about', etc.
    content_length: int
    scrape_timestamp: str
    success: bool
    error_message: Optional[str] = None
    
@dataclass
class ExtractedIntelligence:
    """Structured intelligence extracted from raw content"""
    leadership_candidates: List[Dict[str, Any]]  # Potential names with confidence scores
    program_candidates: List[Dict[str, Any]]
    contact_candidates: Dict[str, Any]
    mission_candidates: List[str]
    extraction_confidence: float  # 0.0 - 1.0
    extraction_method: str
    validation_notes: List[str]

@dataclass
class ComprehensiveScrapingData:
    """Complete scraping session data"""
    metadata: ScrapingMetadata
    raw_results: List[RawScrapingResult]
    extracted_intelligence: ExtractedIntelligence
    quality_assessment: Dict[str, Any]

class JSONStorageService:
    """Service for managing JSON-based web scraping data storage"""
    
    def __init__(self, base_path: str = "data/web_scraping"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_ein_directory(self, ein: str) -> Path:
        """Get or create directory for specific EIN"""
        ein_dir = self.base_path / ein
        ein_dir.mkdir(parents=True, exist_ok=True)
        return ein_dir
        
    def _generate_filename(self, ein: str, timestamp: datetime = None) -> str:
        """Generate filename for scraping results"""
        if timestamp is None:
            timestamp = datetime.now()
        
        formatted_time = timestamp.strftime("%Y_%m_%d_%H_%M_%S")
        return f"scraping_results_{formatted_time}.json"
    
    def save_scraping_session(self, scraping_data: ComprehensiveScrapingData) -> str:
        """Save complete scraping session to JSON file"""
        try:
            ein_dir = self._get_ein_directory(scraping_data.metadata.ein)
            filename = self._generate_filename(scraping_data.metadata.ein)
            filepath = ein_dir / filename
            
            # Convert to JSON-serializable format
            json_data = {
                "metadata": asdict(scraping_data.metadata),
                "raw_results": [asdict(result) for result in scraping_data.raw_results],
                "extracted_intelligence": asdict(scraping_data.extracted_intelligence),
                "quality_assessment": scraping_data.quality_assessment,
                "storage_version": "1.0",
                "created_at": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved scraping session for EIN {scraping_data.metadata.ein} to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving scraping session: {e}")
            raise
    
    def load_latest_scraping_session(self, ein: str) -> Optional[ComprehensiveScrapingData]:
        """Load the most recent scraping session for an EIN"""
        try:
            ein_dir = self._get_ein_directory(ein)
            
            # Find most recent JSON file
            json_files = list(ein_dir.glob("scraping_results_*.json"))
            if not json_files:
                return None
                
            latest_file = max(json_files, key=os.path.getmtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convert back to dataclass objects
            metadata = ScrapingMetadata(**json_data["metadata"])
            raw_results = [RawScrapingResult(**result) for result in json_data["raw_results"]]
            extracted_intelligence = ExtractedIntelligence(**json_data["extracted_intelligence"])
            quality_assessment = json_data["quality_assessment"]
            
            return ComprehensiveScrapingData(
                metadata=metadata,
                raw_results=raw_results,
                extracted_intelligence=extracted_intelligence,
                quality_assessment=quality_assessment
            )
            
        except Exception as e:
            logger.error(f"Error loading scraping session for EIN {ein}: {e}")
            return None
    
    def get_scraping_history(self, ein: str) -> List[str]:
        """Get list of all scraping session timestamps for an EIN"""
        try:
            ein_dir = self._get_ein_directory(ein)
            json_files = list(ein_dir.glob("scraping_results_*.json"))
            
            timestamps = []
            for file in json_files:
                # Extract timestamp from filename
                filename = file.stem
                timestamp_part = filename.replace("scraping_results_", "")
                timestamps.append(timestamp_part)
            
            return sorted(timestamps, reverse=True)  # Most recent first
            
        except Exception as e:
            logger.error(f"Error getting scraping history for EIN {ein}: {e}")
            return []
    
    def get_validated_data_candidates(self, ein: str) -> Optional[Dict[str, Any]]:
        """Get data candidates that meet validation criteria for database storage"""
        scraping_data = self.load_latest_scraping_session(ein)
        if not scraping_data:
            return None
        
        intelligence = scraping_data.extracted_intelligence
        
        # Filter candidates by quality thresholds
        validated_candidates = {
            "leadership": [],
            "programs": [],
            "contact_info": {},
            "mission_statements": [],
            "metadata": {
                "confidence_score": intelligence.extraction_confidence,
                "extraction_method": intelligence.extraction_method,
                "validation_notes": intelligence.validation_notes,
                "source_timestamp": scraping_data.metadata.timestamp,
                "urls_scraped": scraping_data.metadata.urls_scraped
            }
        }
        
        # Validate leadership candidates
        for candidate in intelligence.leadership_candidates:
            confidence = candidate.get('confidence', 0.0)
            name = candidate.get('name', '')
            
            # Only include high-confidence, complete names
            if confidence >= 0.7 and len(name) > 5 and ' ' in name:
                validated_candidates["leadership"].append(candidate)
        
        # Validate other data types similarly
        for candidate in intelligence.program_candidates:
            if candidate.get('confidence', 0.0) >= 0.6:
                validated_candidates["programs"].append(candidate)
        
        # Contact info validation
        for field, value in intelligence.contact_candidates.items():
            if isinstance(value, str) and len(value) > 5:
                # Basic validation for contact info
                if '@' in value or '(' in value or 'http' in value:
                    validated_candidates["contact_info"][field] = value
        
        # Mission statements
        for mission in intelligence.mission_candidates:
            if len(mission) >= 50:  # Reasonable mission length
                validated_candidates["mission_statements"].append(mission)
        
        return validated_candidates if any([
            validated_candidates["leadership"],
            validated_candidates["programs"], 
            validated_candidates["contact_info"],
            validated_candidates["mission_statements"]
        ]) else None
    
    def cleanup_old_sessions(self, ein: str, keep_count: int = 5):
        """Keep only the most recent N scraping sessions for an EIN"""
        try:
            ein_dir = self._get_ein_directory(ein)
            json_files = list(ein_dir.glob("scraping_results_*.json"))
            
            if len(json_files) <= keep_count:
                return
                
            # Sort by modification time, keep most recent
            json_files.sort(key=os.path.getmtime, reverse=True)
            
            for old_file in json_files[keep_count:]:
                old_file.unlink()
                logger.info(f"Cleaned up old scraping session: {old_file}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old sessions for EIN {ein}: {e}")
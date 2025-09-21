#!/usr/bin/env python3
"""
Data Validation Pipeline
Processes JSON scraping data and promotes validated results to database
"""
import logging
from typing import Dict, List, Optional, Any
from .json_storage_service import JSONStorageService
import re

logger = logging.getLogger(__name__)

class DataValidationPipeline:
    """Pipeline for validating and promoting JSON scraping data to database"""
    
    def __init__(self, json_storage: JSONStorageService = None):
        self.json_storage = json_storage or JSONStorageService()
        
    def validate_leadership_data(self, leadership_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate leadership data and return only high-quality entries"""
        validated_leaders = []
        
        for candidate in leadership_candidates:
            name = candidate.get('name', '').strip()
            title = candidate.get('title', '').strip()
            confidence = candidate.get('confidence', 0.0)
            
            # Validation criteria
            validation_passed = True
            validation_notes = []
            
            # Name validation
            if not self._is_valid_person_name(name):
                validation_passed = False
                validation_notes.append(f"Invalid name format: '{name}'")
            
            # Fragment detection (from the old system)
            if self._is_name_fragment(name):
                validation_passed = False
                validation_notes.append(f"Detected name fragment: '{name}'")
            
            # Confidence threshold
            if confidence < 0.7:
                validation_passed = False
                validation_notes.append(f"Low confidence score: {confidence}")
            
            # Title validation
            if self._is_title_fragment(title):
                validation_passed = False
                validation_notes.append(f"Detected title fragment: '{title}'")
            
            if validation_passed:
                validated_candidate = candidate.copy()
                validated_candidate['validation_status'] = 'passed'
                validated_candidate['validation_notes'] = []
                validated_leaders.append(validated_candidate)
            else:
                logger.debug(f"Rejected leadership candidate '{name}': {', '.join(validation_notes)}")
        
        return validated_leaders
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Check if string looks like a valid person name"""
        if not name or len(name) < 3:
            return False
        
        # Must have at least first and last name
        name_parts = name.split()
        if len(name_parts) < 2:
            return False
        
        # Check for proper capitalization
        for part in name_parts[:2]:  # Check first two parts
            if not part[0].isupper() or not part[1:].islower():
                return False
        
        # Must not contain obvious non-name patterns
        non_name_patterns = ['@', 'http', '.com', 'phone', 'email']
        name_lower = name.lower()
        if any(pattern in name_lower for pattern in non_name_patterns):
            return False
            
        return True
    
    def _is_name_fragment(self, name: str) -> bool:
        """Detect if name is a fragment from the old extraction system"""
        name_lower = name.lower().strip()
        
        # Known fragment patterns from the problematic system
        fragment_patterns = [
            'board of', 'serving as', 'was appointed', 'executive vice',
            'been the', 'serves as', 'on the', 'at colliers', 'ramps to',
            'director', 'president', 'secretary', 'treasurer', 'chair',
            'member', 'committee', 'executive', 'vice'
        ]
        
        # Exact matches or very short fragments
        if name_lower in fragment_patterns:
            return True
        
        # Names that are too short and match patterns
        if len(name_lower) < 8 and any(pattern in name_lower for pattern in fragment_patterns):
            return True
            
        return False
    
    def _is_title_fragment(self, title: str) -> bool:
        """Detect if title is a fragment"""
        if not title:
            return False
            
        title_lower = title.lower().strip()
        
        # Titles that are actually name fragments
        name_fragment_patterns = [
            'board of', 'serving as', 'was appointed', 'executive vice',
            'been the', 'serves as', 'on the', 'at colliers', 'ramps to'
        ]
        
        return any(pattern in title_lower for pattern in name_fragment_patterns)
    
    def validate_program_data(self, program_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate program data"""
        validated_programs = []
        
        for candidate in program_candidates:
            name = candidate.get('name', '').strip()
            description = candidate.get('description', '').strip()
            confidence = candidate.get('confidence', 0.0)
            
            # Basic validation
            if len(name) < 3 or len(name) > 100:
                continue
                
            if confidence < 0.6:
                continue
            
            # Avoid obvious fragments
            if len(description) < 20 and any(word in description.lower() for word in ['contact', 'phone', 'email']):
                continue
            
            validated_candidate = candidate.copy()
            validated_candidate['validation_status'] = 'passed'
            validated_programs.append(validated_candidate)
        
        return validated_programs
    
    def validate_contact_data(self, contact_candidates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate contact information"""
        validated_contact = {}
        
        for field, value in contact_candidates.items():
            if not isinstance(value, str):
                continue
                
            value = value.strip()
            
            # Skip generic labels
            generic_labels = ['email', 'phone', 'address', 'contact', 'website']
            if value.lower() in generic_labels:
                continue
            
            # Basic validation by field type
            if field.lower() in ['email', 'email_address']:
                if '@' in value and '.' in value and len(value) > 5:
                    validated_contact[field] = value
            elif field.lower() in ['phone', 'phone_number', 'telephone']:
                if any(char.isdigit() for char in value) and len(value) >= 10:
                    validated_contact[field] = value
            elif field.lower() in ['address', 'mailing_address']:
                if len(value) > 10:  # Reasonable address length
                    validated_contact[field] = value
            elif field.lower() in ['website', 'url']:
                if 'http' in value.lower() or '.org' in value.lower() or '.com' in value.lower():
                    validated_contact[field] = value
            else:
                # Generic field, use basic validation
                if len(value) > 3:
                    validated_contact[field] = value
        
        return validated_contact
    
    def validate_mission_data(self, mission_candidates: List[str]) -> List[str]:
        """Validate mission statements"""
        validated_missions = []
        
        for mission in mission_candidates:
            mission = mission.strip()
            
            # Basic length validation
            if len(mission) < 30 or len(mission) > 1000:
                continue
            
            # Must contain meaningful content
            if any(word in mission.lower() for word in ['our mission', 'we serve', 'dedicated to', 'committed to']):
                validated_missions.append(mission)
            elif len(mission) > 50:  # Long enough to be meaningful
                validated_missions.append(mission)
        
        return validated_missions[:3]  # Limit to 3 best missions
    
    def process_ein_data(self, ein: str) -> Optional[Dict[str, Any]]:
        """Process JSON data for an EIN and return validated results"""
        try:
            # Normalize EIN (remove hyphens, spaces) to match storage format
            normalized_ein = ein.replace('-', '').replace(' ', '').strip()
            logger.debug(f"Processing EIN {ein} -> normalized: {normalized_ein}")
            
            # Load latest scraping session
            scraping_data = self.json_storage.load_latest_scraping_session(normalized_ein)
            if not scraping_data:
                logger.info(f"No JSON scraping data found for EIN {ein}")
                return None
            
            intelligence = scraping_data.extracted_intelligence
            
            # Validate each data type
            validated_leadership = self.validate_leadership_data(intelligence.leadership_candidates)
            validated_programs = self.validate_program_data(intelligence.program_candidates)
            validated_contact = self.validate_contact_data(intelligence.contact_candidates)
            validated_missions = self.validate_mission_data(intelligence.mission_candidates)
            
            # Calculate overall quality score
            quality_indicators = [
                len(validated_leadership) > 0,
                len(validated_programs) > 0,
                len(validated_contact) > 0,
                len(validated_missions) > 0
            ]
            
            quality_score = sum(quality_indicators) / len(quality_indicators)
            
            # Only return data if it meets minimum quality threshold
            if quality_score < 0.25:  # At least 1 out of 4 categories must have data
                logger.info(f"EIN {ein} data quality too low: {quality_score}")
                return None
            
            validated_data = {
                "ein": normalized_ein,
                "leadership": validated_leadership,
                "programs": validated_programs,
                "contact_info": validated_contact,
                "mission_statements": validated_missions,
                "metadata": {
                    "data_source": "json_validated",
                    "confidence_score": intelligence.extraction_confidence,
                    "quality_score": quality_score,
                    "extraction_method": intelligence.extraction_method,
                    "source_timestamp": scraping_data.metadata.timestamp,
                    "urls_scraped": scraping_data.metadata.urls_scraped,
                    "validation_notes": intelligence.validation_notes
                }
            }
            
            logger.info(f"Validated data for EIN {ein}: {len(validated_leadership)} leaders, {len(validated_programs)} programs")
            return validated_data
            
        except Exception as e:
            logger.error(f"Error processing data for EIN {ein}: {e}")
            return None
    
    def get_database_ready_format(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert validated data to database-ready format"""
        if not validated_data:
            return None
        
        # Format leadership data for database
        leadership_formatted = []
        for leader in validated_data["leadership"]:
            leadership_formatted.append({
                "name": leader.get("name", ""),
                "title": leader.get("title", ""),
                "bio": leader.get("bio", "")
            })
        
        # Format program data
        programs_formatted = []
        for program in validated_data["programs"]:
            programs_formatted.append({
                "name": program.get("name", ""),
                "description": program.get("description", "")
            })
        
        # Database ready format
        db_format = {
            "extracted_info": {
                "leadership": leadership_formatted,
                "programs": programs_formatted,
                "contact_info": validated_data["contact_info"],
                "mission_statements": validated_data["mission_statements"]
            },
            "intelligence_quality_score": int(validated_data["metadata"]["quality_score"] * 100),
            "data_source": validated_data["metadata"]["data_source"],
            "last_updated": validated_data["metadata"]["source_timestamp"]
        }
        
        return db_format
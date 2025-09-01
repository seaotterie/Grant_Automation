"""
Opportunity Type Detection System

Automatically detects opportunity type (government, nonprofit, corporate) to route
to appropriate fact extraction prompts and scoring algorithms.

Purpose: Enable opportunity-type aware fact extraction and scoring for improved
repeatability and appropriate analysis depth based on information availability patterns.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class OpportunityType(str, Enum):
    """Opportunity types with different information availability patterns"""
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit" 
    CORPORATE = "corporate"
    UNKNOWN = "unknown"

@dataclass
class OpportunityTypeIndicators:
    """Indicators used for opportunity type detection"""
    government_keywords: List[str]
    nonprofit_keywords: List[str]
    corporate_keywords: List[str]
    url_patterns: Dict[str, List[str]]
    organization_patterns: Dict[str, List[str]]

class OpportunityTypeDetectionResult(BaseModel):
    """Result of opportunity type detection with confidence scoring"""
    detected_type: OpportunityType
    confidence_score: float
    detection_evidence: List[str]
    alternative_types: Dict[OpportunityType, float]
    expected_data_completeness: float
    recommended_extraction_approach: str

class OpportunityTypeDetector:
    """
    Detects opportunity type to enable appropriate fact extraction and scoring
    
    Government: 85-95% data completeness expected, detailed compliance scoring
    Nonprofit: 40-70% data completeness expected, mission alignment focus  
    Corporate: 20-50% data completeness expected, relationship-centric scoring
    """
    
    def __init__(self):
        self.indicators = self._initialize_detection_indicators()
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6, 
            "low": 0.4
        }
        
        # Expected data completeness by opportunity type
        self.expected_completeness = {
            OpportunityType.GOVERNMENT: 0.90,
            OpportunityType.NONPROFIT: 0.55,
            OpportunityType.CORPORATE: 0.35,
            OpportunityType.UNKNOWN: 0.30
        }
    
    def _initialize_detection_indicators(self) -> OpportunityTypeIndicators:
        """Initialize keyword and pattern indicators for opportunity type detection"""
        
        return OpportunityTypeIndicators(
            government_keywords=[
                # Federal agencies
                "department of", "agency", "administration", "bureau", "commission",
                "federal", "national", "usda", "hhs", "doe", "nsf", "nih", "cdc",
                "hrsa", "samhsa", "cms", "fema", "epa", "dod", "va", "treasury",
                
                # Government document types
                "rfp", "rfi", "nofo", "funding opportunity", "solicitation",
                "cooperative agreement", "federal register", "cfr", "cfda",
                
                # Government processes
                "grants.gov", "sam.gov", "federal award", "appropriation",
                "congressional", "legislative", "regulatory", "compliance",
                
                # Government-specific terms
                "federal funding", "taxpayer", "public funds", "government contract",
                "federal grant", "stimulus", "infrastructure", "homeland security"
            ],
            
            nonprofit_keywords=[
                # Foundation types
                "foundation", "trust", "endowment", "charitable", "philanthropy",
                "community foundation", "private foundation", "family foundation",
                "corporate foundation", "giving program", "donor advised",
                
                # Nonprofit terminology
                "501c3", "501(c)(3)", "nonprofit", "non-profit", "charity",
                "charitable organization", "public charity", "tax exempt",
                
                # Foundation processes  
                "grant making", "grantmaking", "letter of inquiry", "loi",
                "proposal guidelines", "application deadline", "board meeting",
                "site visit", "capacity building", "general operating",
                
                # Foundation language
                "mission alignment", "strategic initiative", "program area",
                "geographic focus", "impact measurement", "social change"
            ],
            
            corporate_keywords=[
                # Corporate entities
                "corporation", "company", "inc", "llc", "ltd", "corp",
                "corporate social responsibility", "csr", "corporate giving",
                "community investment", "corporate philanthropy",
                
                # Corporate programs
                "employee giving", "matching gifts", "volunteer program",
                "sponsorship", "partnership", "community partnership",
                "corporate partner", "business alliance", "strategic partnership",
                
                # Corporate focus areas
                "brand alignment", "marketing opportunity", "visibility",
                "corporate values", "stakeholder engagement", "social impact",
                "sustainability", "environmental responsibility",
                
                # Corporate processes
                "business case", "roi", "brand exposure", "media coverage",
                "corporate communications", "public relations", "community relations"
            ],
            
            url_patterns={
                "government": [
                    r"\.gov$", r"grants\.gov", r"sam\.gov", r"usaspending\.gov",
                    r"federal", r"state\..*\.us", r"agency", r"department"
                ],
                "nonprofit": [
                    r"foundation", r"trust", r"charity", r"philanthropic",
                    r"giving", r"grants", r"nonprofit", r"501c3"
                ],
                "corporate": [
                    r"\.com$", r"corporate", r"company", r"inc", r"corp",
                    r"csr", r"community", r"social-responsibility"
                ]
            },
            
            organization_patterns={
                "government": [
                    r"Department of \w+", r"\w+ Agency", r"\w+ Administration",
                    r"\w+ Bureau", r"\w+ Commission", r"National \w+",
                    r"Federal \w+", r"U\.S\. \w+", r"United States \w+"
                ],
                "nonprofit": [
                    r"\w+ Foundation", r"\w+ Trust", r"\w+ Fund", r"\w+ Endowment",
                    r"Community Foundation of \w+", r"\w+ Charitable \w+",
                    r"\w+ Family Foundation", r"\w+ Corporate Foundation"
                ],
                "corporate": [
                    r"\w+ Corporation", r"\w+ Inc", r"\w+ LLC", r"\w+ Company",
                    r"\w+ Corp", r"\w+ Ltd", r"\w+ Group", r"\w+ Holdings"
                ]
            }
        )
    
    def detect_opportunity_type(self, opportunity_data: Dict) -> OpportunityTypeDetectionResult:
        """
        Detect opportunity type based on available data
        
        Args:
            opportunity_data: Dictionary with fields like title, description, 
                            organization_name, website, etc.
                            
        Returns:
            OpportunityTypeDetectionResult with detected type and confidence
        """
        logger.info(f"Detecting opportunity type for: {opportunity_data.get('title', 'Unknown')}")
        
        # Extract text content for analysis
        text_content = self._extract_text_content(opportunity_data)
        
        # Calculate scores for each opportunity type
        type_scores = {
            OpportunityType.GOVERNMENT: self._calculate_government_score(text_content, opportunity_data),
            OpportunityType.NONPROFIT: self._calculate_nonprofit_score(text_content, opportunity_data),
            OpportunityType.CORPORATE: self._calculate_corporate_score(text_content, opportunity_data)
        }
        
        # Determine best match
        detected_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        confidence_score = type_scores[detected_type]
        
        # Handle low confidence cases
        if confidence_score < self.confidence_thresholds["low"]:
            detected_type = OpportunityType.UNKNOWN
            confidence_score = 0.3  # Default low confidence for unknown types
        
        # Gather detection evidence
        detection_evidence = self._gather_detection_evidence(text_content, opportunity_data, detected_type)
        
        # Create result
        result = OpportunityTypeDetectionResult(
            detected_type=detected_type,
            confidence_score=confidence_score,
            detection_evidence=detection_evidence,
            alternative_types={k: v for k, v in type_scores.items() if k != detected_type},
            expected_data_completeness=self.expected_completeness[detected_type],
            recommended_extraction_approach=self._get_extraction_approach(detected_type, confidence_score)
        )
        
        logger.info(f"Detected type: {detected_type.value} (confidence: {confidence_score:.2f})")
        return result
    
    def _extract_text_content(self, opportunity_data: Dict) -> str:
        """Extract all text content for analysis"""
        text_parts = []
        
        # Standard fields to analyze
        text_fields = ['title', 'description', 'organization_name', 'agency', 
                      'program_name', 'category', 'focus_area', 'website']
        
        for field in text_fields:
            if field in opportunity_data and opportunity_data[field]:
                text_parts.append(str(opportunity_data[field]).lower())
        
        return " ".join(text_parts)
    
    def _calculate_government_score(self, text_content: str, opportunity_data: Dict) -> float:
        """Calculate government opportunity type score"""
        score = 0.0
        
        # Keyword matching
        gov_keyword_matches = sum(1 for keyword in self.indicators.government_keywords 
                                 if keyword.lower() in text_content)
        keyword_score = min(0.5, gov_keyword_matches / 20)  # Cap at 0.5
        score += keyword_score
        
        # URL pattern matching
        website = opportunity_data.get('website', '')
        if website:
            for pattern in self.indicators.url_patterns['government']:
                if re.search(pattern, website.lower()):
                    score += 0.3
                    break
        
        # Organization name pattern matching
        org_name = opportunity_data.get('organization_name', '') or opportunity_data.get('agency', '')
        if org_name:
            for pattern in self.indicators.organization_patterns['government']:
                if re.search(pattern, org_name, re.IGNORECASE):
                    score += 0.3
                    break
        
        # Government-specific indicators
        if any(term in text_content for term in ['rfp', 'nofo', 'grants.gov', 'federal']):
            score += 0.2
            
        return min(1.0, score)
    
    def _calculate_nonprofit_score(self, text_content: str, opportunity_data: Dict) -> float:
        """Calculate nonprofit/foundation opportunity type score"""
        score = 0.0
        
        # Keyword matching
        nonprofit_keyword_matches = sum(1 for keyword in self.indicators.nonprofit_keywords 
                                       if keyword.lower() in text_content)
        keyword_score = min(0.5, nonprofit_keyword_matches / 15)  # Cap at 0.5
        score += keyword_score
        
        # URL pattern matching
        website = opportunity_data.get('website', '')
        if website:
            for pattern in self.indicators.url_patterns['nonprofit']:
                if re.search(pattern, website.lower()):
                    score += 0.3
                    break
        
        # Organization name pattern matching
        org_name = opportunity_data.get('organization_name', '')
        if org_name:
            for pattern in self.indicators.organization_patterns['nonprofit']:
                if re.search(pattern, org_name, re.IGNORECASE):
                    score += 0.3
                    break
        
        # Foundation-specific indicators
        if any(term in text_content for term in ['foundation', '501c3', 'charitable', 'philanthropy']):
            score += 0.2
            
        return min(1.0, score)
    
    def _calculate_corporate_score(self, text_content: str, opportunity_data: Dict) -> float:
        """Calculate corporate opportunity type score"""
        score = 0.0
        
        # Keyword matching
        corporate_keyword_matches = sum(1 for keyword in self.indicators.corporate_keywords 
                                       if keyword.lower() in text_content)
        keyword_score = min(0.5, corporate_keyword_matches / 12)  # Cap at 0.5
        score += keyword_score
        
        # URL pattern matching
        website = opportunity_data.get('website', '')
        if website:
            for pattern in self.indicators.url_patterns['corporate']:
                if re.search(pattern, website.lower()):
                    score += 0.3
                    break
        
        # Organization name pattern matching
        org_name = opportunity_data.get('organization_name', '')
        if org_name:
            for pattern in self.indicators.organization_patterns['corporate']:
                if re.search(pattern, org_name, re.IGNORECASE):
                    score += 0.3
                    break
        
        # Corporate-specific indicators
        if any(term in text_content for term in ['csr', 'corporate', 'partnership', 'sponsorship']):
            score += 0.2
            
        return min(1.0, score)
    
    def _gather_detection_evidence(self, text_content: str, opportunity_data: Dict, 
                                 detected_type: OpportunityType) -> List[str]:
        """Gather evidence for the detection decision"""
        evidence = []
        
        if detected_type == OpportunityType.GOVERNMENT:
            keywords_found = [kw for kw in self.indicators.government_keywords[:10] 
                            if kw.lower() in text_content]
            if keywords_found:
                evidence.append(f"Government keywords found: {', '.join(keywords_found[:5])}")
                
        elif detected_type == OpportunityType.NONPROFIT:
            keywords_found = [kw for kw in self.indicators.nonprofit_keywords[:10] 
                            if kw.lower() in text_content]
            if keywords_found:
                evidence.append(f"Nonprofit keywords found: {', '.join(keywords_found[:5])}")
                
        elif detected_type == OpportunityType.CORPORATE:
            keywords_found = [kw for kw in self.indicators.corporate_keywords[:10] 
                            if kw.lower() in text_content]
            if keywords_found:
                evidence.append(f"Corporate keywords found: {', '.join(keywords_found[:5])}")
        
        # Organization name evidence
        org_name = opportunity_data.get('organization_name', '') or opportunity_data.get('agency', '')
        if org_name:
            evidence.append(f"Organization name: {org_name}")
        
        # Website evidence
        website = opportunity_data.get('website', '')
        if website:
            evidence.append(f"Website domain: {website}")
            
        return evidence[:5]  # Limit to top 5 pieces of evidence
    
    def _get_extraction_approach(self, detected_type: OpportunityType, confidence: float) -> str:
        """Get recommended fact extraction approach based on type and confidence"""
        
        if confidence >= self.confidence_thresholds["high"]:
            confidence_level = "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        approaches = {
            OpportunityType.GOVERNMENT: {
                "high": "detailed_government_extraction",
                "medium": "standard_government_extraction", 
                "low": "basic_government_extraction"
            },
            OpportunityType.NONPROFIT: {
                "high": "comprehensive_nonprofit_extraction",
                "medium": "standard_nonprofit_extraction",
                "low": "minimal_nonprofit_extraction"
            },
            OpportunityType.CORPORATE: {
                "high": "relationship_focused_extraction",
                "medium": "standard_corporate_extraction",
                "low": "basic_corporate_extraction"
            },
            OpportunityType.UNKNOWN: {
                "high": "general_extraction",
                "medium": "general_extraction",
                "low": "minimal_extraction"
            }
        }
        
        return approaches[detected_type][confidence_level]
    
    def get_expected_data_patterns(self, opportunity_type: OpportunityType) -> Dict:
        """Get expected data availability patterns for opportunity type"""
        
        patterns = {
            OpportunityType.GOVERNMENT: {
                "expected_completeness": 0.90,
                "high_availability_fields": [
                    "eligibility_requirements", "funding_amount", "deadline", 
                    "application_process", "evaluation_criteria", "program_officer"
                ],
                "variable_availability_fields": ["matching_requirements", "site_visits"],
                "low_availability_fields": ["informal_contacts", "relationship_factors"]
            },
            OpportunityType.NONPROFIT: {
                "expected_completeness": 0.55,
                "high_availability_fields": ["mission_statement", "focus_areas", "website"],
                "variable_availability_fields": [
                    "funding_range", "application_process", "geographic_preferences",
                    "deadlines", "contact_information"
                ],
                "low_availability_fields": [
                    "specific_amounts", "detailed_requirements", "evaluation_criteria"
                ]
            },
            OpportunityType.CORPORATE: {
                "expected_completeness": 0.35,
                "high_availability_fields": ["company_name", "csr_focus_general", "website"],
                "variable_availability_fields": [
                    "partnership_criteria", "contact_methods", "application_process"
                ],
                "low_availability_fields": [
                    "funding_amounts", "specific_deadlines", "detailed_requirements",
                    "evaluation_criteria", "program_officers"
                ]
            }
        }
        
        return patterns.get(opportunity_type, patterns[OpportunityType.CORPORATE])
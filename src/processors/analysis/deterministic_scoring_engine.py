"""
Deterministic Scoring Engine

Processes extracted facts using mathematical algorithms to generate consistent,
repeatable scores. Separates fact extraction (AI) from scoring logic (deterministic)
for improved reliability and auditability.

Architecture: AI Extracts Facts → Local Algorithms Calculate Scores → Intelligence Synthesis
"""

import json
import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel
from datetime import datetime, date

from .opportunity_type_detector import OpportunityType

logger = logging.getLogger(__name__)

class ScoreConfidenceLevel(str, Enum):
    """Score confidence levels based on data availability"""
    HIGH = "high"      # 0.8+ confidence
    MEDIUM = "medium"  # 0.6-0.8 confidence  
    LOW = "low"        # 0.4-0.6 confidence
    VERY_LOW = "very_low"  # <0.4 confidence

@dataclass
class ScoringWeights:
    """Scoring weights optimized by opportunity type"""
    base_compatibility: float
    strategic_alignment: float
    geographic_advantage: float
    financial_fit: float
    eligibility_compliance: float
    
    # Government-specific weights (compliance-heavy)
    @classmethod
    def government_weights(cls):
        return cls(
            base_compatibility=0.30,  # Eligibility compliance priority
            strategic_alignment=0.20,  # Program alignment
            geographic_advantage=0.20,  # Location benefits
            financial_fit=0.15,       # Award size compatibility
            eligibility_compliance=0.15  # Additional compliance factors
        )
    
    # Nonprofit-specific weights (mission-focused)
    @classmethod
    def nonprofit_weights(cls):
        return cls(
            base_compatibility=0.25,  # Basic compatibility
            strategic_alignment=0.35,  # Mission alignment priority
            geographic_advantage=0.15,  # Less geographic restriction
            financial_fit=0.15,       # Funding level fit
            eligibility_compliance=0.10  # Simpler eligibility
        )
    
    # Corporate-specific weights (relationship-focused)
    @classmethod
    def corporate_weights(cls):
        return cls(
            base_compatibility=0.20,  # Basic fit
            strategic_alignment=0.40,  # Partnership alignment priority
            geographic_advantage=0.10,  # Less geographic importance
            financial_fit=0.15,       # Value alignment
            eligibility_compliance=0.15  # Partnership criteria
        )

class ExtractedFacts(BaseModel):
    """Container for facts extracted by AI processors"""
    opportunity_type: OpportunityType
    extraction_template: str
    raw_facts: Dict[str, Any]
    data_completeness: float
    extraction_confidence: float
    missing_fields: List[str] = field(default_factory=list)
    extraction_timestamp: datetime

class ProfileData(BaseModel):
    """Organization profile data for scoring"""
    organization_name: str
    ein: str
    annual_revenue: Optional[float] = None
    ntee_codes: List[str] = []
    state: str = 'VA'
    focus_areas: List[str] = []
    mission_statement: Optional[str] = None
    board_size: Optional[int] = None
    staff_count: Optional[int] = None
    years_in_operation: Optional[int] = None

class ScoringResult(BaseModel):
    """Result of deterministic scoring calculation"""
    final_score: float
    confidence_level: ScoreConfidenceLevel
    component_scores: Dict[str, float]
    score_rationale: List[str]
    data_gaps_impact: List[str]
    calculation_details: Dict[str, Any]
    scoring_timestamp: datetime

class DeterministicScoringEngine:
    """
    Processes extracted facts using deterministic mathematical algorithms
    
    Key Benefits:
    - Identical inputs always produce identical scores
    - Clear audit trail from facts to final scores
    - Opportunity-type aware scoring logic
    - Confidence scoring based on actual data availability
    """
    
    def __init__(self):
        self.scoring_weights = self._initialize_scoring_weights()
        self.confidence_thresholds = {
            ScoreConfidenceLevel.HIGH: 0.8,
            ScoreConfidenceLevel.MEDIUM: 0.6,
            ScoreConfidenceLevel.LOW: 0.4,
            ScoreConfidenceLevel.VERY_LOW: 0.0
        }
        
        # Data completeness requirements by opportunity type
        self.completeness_requirements = {
            OpportunityType.GOVERNMENT: {
                'critical_fields': ['eligibility_requirements', 'funding_details', 'deadline'],
                'important_fields': ['application_process', 'evaluation_criteria'],
                'optional_fields': ['contacts', 'compliance_reporting']
            },
            OpportunityType.NONPROFIT: {
                'critical_fields': ['mission_focus', 'contact_method'],
                'important_fields': ['funding_areas', 'geographic_scope'],
                'optional_fields': ['application_process', 'recent_grants']
            },
            OpportunityType.CORPORATE: {
                'critical_fields': ['company_name', 'contact_method'],
                'important_fields': ['csr_focus', 'partnership_types'],
                'optional_fields': ['geographic_focus', 'organization_types']
            }
        }
    
    def _initialize_scoring_weights(self) -> Dict[OpportunityType, ScoringWeights]:
        """Initialize opportunity-type specific scoring weights"""
        return {
            OpportunityType.GOVERNMENT: ScoringWeights.government_weights(),
            OpportunityType.NONPROFIT: ScoringWeights.nonprofit_weights(),
            OpportunityType.CORPORATE: ScoringWeights.corporate_weights()
        }
    
    def calculate_opportunity_score(self, extracted_facts: ExtractedFacts, 
                                  profile_data: ProfileData) -> ScoringResult:
        """
        Calculate deterministic opportunity score based on extracted facts
        
        Args:
            extracted_facts: Facts extracted by AI processors
            profile_data: Organization profile information
            
        Returns:
            ScoringResult with final score and detailed breakdown
        """
        logger.info(f"Calculating score for {profile_data.organization_name} - "
                   f"{extracted_facts.opportunity_type.value} opportunity")
        
        start_time = datetime.now()
        
        # Get opportunity-type specific weights
        weights = self.scoring_weights.get(
            extracted_facts.opportunity_type, 
            self.scoring_weights[OpportunityType.CORPORATE]  # Default fallback
        )
        
        # Calculate component scores
        component_scores = {}
        score_rationale = []
        data_gaps_impact = []
        calculation_details = {}
        
        # Base Compatibility Score
        base_score, base_rationale, base_details = self._calculate_base_compatibility(
            extracted_facts, profile_data
        )
        component_scores['base_compatibility'] = base_score
        score_rationale.extend(base_rationale)
        calculation_details['base_compatibility'] = base_details
        
        # Strategic Alignment Score  
        strategic_score, strategic_rationale, strategic_details = self._calculate_strategic_alignment(
            extracted_facts, profile_data
        )
        component_scores['strategic_alignment'] = strategic_score
        score_rationale.extend(strategic_rationale)
        calculation_details['strategic_alignment'] = strategic_details
        
        # Geographic Advantage Score
        geo_score, geo_rationale, geo_details = self._calculate_geographic_advantage(
            extracted_facts, profile_data
        )
        component_scores['geographic_advantage'] = geo_score
        score_rationale.extend(geo_rationale)
        calculation_details['geographic_advantage'] = geo_details
        
        # Financial Fit Score
        financial_score, financial_rationale, financial_details = self._calculate_financial_fit(
            extracted_facts, profile_data
        )
        component_scores['financial_fit'] = financial_score
        score_rationale.extend(financial_rationale)
        calculation_details['financial_fit'] = financial_details
        
        # Eligibility Compliance Score
        eligibility_score, eligibility_rationale, eligibility_details = self._calculate_eligibility_compliance(
            extracted_facts, profile_data
        )
        component_scores['eligibility_compliance'] = eligibility_score
        score_rationale.extend(eligibility_rationale)
        calculation_details['eligibility_compliance'] = eligibility_details
        
        # Calculate weighted final score
        final_score = (
            base_score * weights.base_compatibility +
            strategic_score * weights.strategic_alignment +
            geo_score * weights.geographic_advantage +
            financial_score * weights.financial_fit +
            eligibility_score * weights.eligibility_compliance
        )
        
        # Calculate confidence level based on data availability
        confidence_level, confidence_rationale = self._calculate_confidence_level(
            extracted_facts, component_scores
        )
        data_gaps_impact.extend(confidence_rationale)
        
        # Create result
        result = ScoringResult(
            final_score=round(final_score, 3),
            confidence_level=confidence_level,
            component_scores=component_scores,
            score_rationale=score_rationale,
            data_gaps_impact=data_gaps_impact,
            calculation_details=calculation_details,
            scoring_timestamp=start_time
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Score calculation completed: {final_score:.3f} "
                   f"(confidence: {confidence_level.value}) in {processing_time:.2f}s")
        
        return result
    
    def _calculate_base_compatibility(self, facts: ExtractedFacts, 
                                    profile: ProfileData) -> Tuple[float, List[str], Dict]:
        """Calculate base compatibility score using deterministic logic"""
        score = 0.5  # Base score
        rationale = []
        details = {}
        
        if facts.opportunity_type == OpportunityType.GOVERNMENT:
            # Government base compatibility focuses on eligibility compliance
            eligibility_data = self._extract_nested_value(facts.raw_facts, 
                                                         ['eligibility_requirements', 'eligibility'])
            if eligibility_data and eligibility_data != "Information not available":
                # Check organizational type requirements
                if any(org_type in eligibility_data.lower() 
                      for org_type in ['501c3', '501(c)(3)', 'nonprofit', 'non-profit']):
                    score += 0.3
                    rationale.append("Nonprofit eligibility confirmed in requirements")
                
                # Check geographic compatibility
                if profile.state.lower() in eligibility_data.lower():
                    score += 0.2
                    rationale.append(f"Geographic eligibility confirmed for {profile.state}")
            else:
                rationale.append("Eligibility requirements not available - using base compatibility")
                
        elif facts.opportunity_type == OpportunityType.NONPROFIT:
            # Nonprofit compatibility focuses on mission alignment and NTEE matching
            mission_data = self._extract_nested_value(facts.raw_facts, 
                                                     ['foundation_essentials', 'mission_focus', 'focus_areas'])
            if mission_data and mission_data != "Information not available":
                # Basic mission keyword matching
                alignment_score = self._calculate_mission_alignment(mission_data, profile.focus_areas)
                score += alignment_score * 0.4
                rationale.append(f"Mission alignment calculated: {alignment_score:.2f}")
                
        elif facts.opportunity_type == OpportunityType.CORPORATE:
            # Corporate compatibility focuses on CSR alignment and partnership fit
            csr_data = self._extract_nested_value(facts.raw_facts, 
                                                 ['csr_program', 'focus_areas', 'community_focus'])
            if csr_data and csr_data != "Information not available":
                partnership_score = self._calculate_partnership_alignment(csr_data, profile.focus_areas)
                score += partnership_score * 0.4
                rationale.append(f"Partnership alignment calculated: {partnership_score:.2f}")
        
        details = {
            'base_score': 0.5,
            'compatibility_bonus': score - 0.5,
            'opportunity_type': facts.opportunity_type.value,
            'calculation_method': 'deterministic_compatibility_algorithm'
        }
        
        return min(1.0, score), rationale, details
    
    def _calculate_strategic_alignment(self, facts: ExtractedFacts, 
                                     profile: ProfileData) -> Tuple[float, List[str], Dict]:
        """Calculate strategic alignment using semantic matching"""
        score = 0.5
        rationale = []
        details = {}
        
        # Extract relevant alignment text based on opportunity type
        alignment_text = ""
        if facts.opportunity_type == OpportunityType.GOVERNMENT:
            program_goals = self._extract_nested_value(facts.raw_facts, ['program_specifics', 'program_goals'])
            priority_areas = self._extract_nested_value(facts.raw_facts, ['program_specifics', 'priority_areas'])
            alignment_text = f"{program_goals or ''} {priority_areas or ''}"
            
        elif facts.opportunity_type == OpportunityType.NONPROFIT:
            funding_areas = self._extract_nested_value(facts.raw_facts, ['grant_information', 'funding_areas'])
            mission_focus = self._extract_nested_value(facts.raw_facts, ['foundation_essentials', 'mission_focus'])
            alignment_text = f"{funding_areas or ''} {mission_focus or ''}"
            
        elif facts.opportunity_type == OpportunityType.CORPORATE:
            focus_areas = self._extract_nested_value(facts.raw_facts, ['csr_program', 'focus_areas'])
            program_interests = self._extract_nested_value(facts.raw_facts, ['partnership_criteria', 'program_interests'])
            alignment_text = f"{focus_areas or ''} {program_interests or ''}"
        
        if alignment_text and alignment_text.strip() != "Information not available":
            # Perform keyword-based semantic alignment
            alignment_score = self._calculate_keyword_alignment(alignment_text, profile.focus_areas, profile.mission_statement)
            score += alignment_score * 0.4
            rationale.append(f"Strategic alignment score: {alignment_score:.2f}")
            details['alignment_text_analyzed'] = alignment_text[:200]  # First 200 chars for debugging
        else:
            rationale.append("Strategic alignment data not available")
            details['alignment_data_missing'] = True
        
        details.update({
            'base_score': 0.5,
            'alignment_bonus': score - 0.5,
            'calculation_method': 'keyword_semantic_alignment'
        })
        
        return min(1.0, score), rationale, details
    
    def _calculate_geographic_advantage(self, facts: ExtractedFacts, 
                                      profile: ProfileData) -> Tuple[float, List[str], Dict]:
        """Calculate geographic advantage based on location preferences"""
        score = 0.5  # Base score
        rationale = []
        details = {}
        
        # Extract geographic information based on opportunity type
        geographic_data = ""
        if facts.opportunity_type == OpportunityType.GOVERNMENT:
            geo_restrictions = self._extract_nested_value(facts.raw_facts, ['eligibility_requirements', 'geographic_restrictions'])
            geographic_data = geo_restrictions or ""
            
        elif facts.opportunity_type == OpportunityType.NONPROFIT:
            geo_preferences = self._extract_nested_value(facts.raw_facts, ['grant_program', 'geographic_preferences'])
            geo_scope = self._extract_nested_value(facts.raw_facts, ['foundation_essentials', 'geographic_scope'])
            geographic_data = f"{geo_preferences or ''} {geo_scope or ''}"
            
        elif facts.opportunity_type == OpportunityType.CORPORATE:
            geo_focus = self._extract_nested_value(facts.raw_facts, ['partnership_info', 'geographic_focus'])
            geo_preferences = self._extract_nested_value(facts.raw_facts, ['partnership_criteria', 'geographic_preferences'])
            geographic_data = f"{geo_focus or ''} {geo_preferences or ''}"
        
        if geographic_data and geographic_data != "Information not available":
            # Check for state-specific advantages
            if profile.state.lower() in geographic_data.lower():
                score += 0.3
                rationale.append(f"State match found: {profile.state}")
                
            # Check for regional advantages  
            regional_matches = self._check_regional_matches(geographic_data, profile.state)
            if regional_matches:
                score += 0.2
                rationale.append(f"Regional advantage: {regional_matches}")
                
            # Check for national scope (neutral advantage)
            if any(term in geographic_data.lower() for term in ['national', 'nationwide', 'all states']):
                score += 0.1
                rationale.append("National scope opportunity")
                
        else:
            rationale.append("Geographic information not available")
            # Use Virginia concentration optimization (from existing system)
            if profile.state.upper() == 'VA':
                score += 0.15  # 78% Virginia concentration benefit
                rationale.append("Virginia geographic advantage applied (data-driven optimization)")
        
        details = {
            'base_score': 0.5,
            'geographic_bonus': score - 0.5,
            'state': profile.state,
            'geographic_data_available': bool(geographic_data),
            'calculation_method': 'geographic_matching_algorithm'
        }
        
        return min(1.0, score), rationale, details
    
    def _calculate_financial_fit(self, facts: ExtractedFacts, 
                               profile: ProfileData) -> Tuple[float, List[str], Dict]:
        """Calculate financial fit based on funding amounts and organizational capacity"""
        score = 0.5
        rationale = []
        details = {}
        
        # Extract funding information
        funding_data = ""
        if facts.opportunity_type == OpportunityType.GOVERNMENT:
            award_amount = self._extract_nested_value(facts.raw_facts, ['funding_details', 'award_amount_range'])
            funding_data = award_amount or ""
            
        elif facts.opportunity_type == OpportunityType.NONPROFIT:
            typical_amounts = self._extract_nested_value(facts.raw_facts, ['grant_information', 'typical_amounts'])
            grant_size = self._extract_nested_value(facts.raw_facts, ['grant_program', 'typical_grant_size'])
            funding_data = f"{typical_amounts or ''} {grant_size or ''}"
            
        elif facts.opportunity_type == OpportunityType.CORPORATE:
            # Corporate opportunities rarely specify amounts - focus on organizational fit
            support_types = self._extract_nested_value(facts.raw_facts, ['value_recognition', 'support_types'])
            funding_data = support_types or ""
        
        if funding_data and funding_data != "Information not available":
            # Parse funding amounts and compare to organizational capacity
            funding_range = self._parse_funding_amounts(funding_data)
            if funding_range and profile.annual_revenue:
                fit_score = self._calculate_funding_capacity_fit(funding_range, profile.annual_revenue)
                score += fit_score * 0.4
                rationale.append(f"Financial capacity fit: {fit_score:.2f}")
                details['funding_range_parsed'] = funding_range
                details['org_revenue'] = profile.annual_revenue
            else:
                rationale.append("Funding amounts mentioned but not parseable")
        else:
            rationale.append("Funding amount information not available")
        
        details.update({
            'base_score': 0.5,
            'financial_bonus': score - 0.5,
            'calculation_method': 'funding_capacity_analysis'
        })
        
        return min(1.0, score), rationale, details
    
    def _calculate_eligibility_compliance(self, facts: ExtractedFacts, 
                                        profile: ProfileData) -> Tuple[float, List[str], Dict]:
        """Calculate eligibility compliance score"""
        score = 0.5
        rationale = []
        details = {}
        
        # Different compliance factors by opportunity type
        if facts.opportunity_type == OpportunityType.GOVERNMENT:
            # Government eligibility is typically detailed and specific
            eligibility_reqs = self._extract_nested_dict(facts.raw_facts, ['eligibility_requirements'])
            if eligibility_reqs:
                compliance_score = self._check_government_eligibility_compliance(eligibility_reqs, profile)
                score += compliance_score * 0.4
                rationale.append(f"Government eligibility compliance: {compliance_score:.2f}")
                
        elif facts.opportunity_type == OpportunityType.NONPROFIT:
            # Nonprofit eligibility often focuses on organizational type and mission
            eligibility_data = self._extract_nested_dict(facts.raw_facts, ['eligibility'])
            if eligibility_data:
                compliance_score = self._check_nonprofit_eligibility_compliance(eligibility_data, profile)
                score += compliance_score * 0.4
                rationale.append(f"Nonprofit eligibility compliance: {compliance_score:.2f}")
                
        elif facts.opportunity_type == OpportunityType.CORPORATE:
            # Corporate partnerships focus on strategic fit and partnership criteria
            criteria_data = self._extract_nested_dict(facts.raw_facts, ['partnership_criteria'])
            if criteria_data:
                compliance_score = self._check_corporate_partnership_compliance(criteria_data, profile)
                score += compliance_score * 0.4
                rationale.append(f"Partnership criteria compliance: {compliance_score:.2f}")
        
        details = {
            'base_score': 0.5,
            'compliance_bonus': score - 0.5,
            'opportunity_type': facts.opportunity_type.value,
            'calculation_method': 'eligibility_compliance_analysis'
        }
        
        return min(1.0, score), rationale, details
    
    def _calculate_confidence_level(self, facts: ExtractedFacts, 
                                  component_scores: Dict[str, float]) -> Tuple[ScoreConfidenceLevel, List[str]]:
        """Calculate confidence level based on data availability and score consistency"""
        rationale = []
        
        # Base confidence from extraction quality
        base_confidence = facts.extraction_confidence * facts.data_completeness
        
        # Adjust confidence based on opportunity type expectations
        expected_completeness = {
            OpportunityType.GOVERNMENT: 0.85,
            OpportunityType.NONPROFIT: 0.55,
            OpportunityType.CORPORATE: 0.35
        }.get(facts.opportunity_type, 0.30)
        
        # Confidence penalty if data is below expectations
        completeness_ratio = facts.data_completeness / expected_completeness
        if completeness_ratio < 0.8:
            base_confidence *= completeness_ratio
            rationale.append(f"Confidence reduced due to low data completeness: {facts.data_completeness:.2f} vs expected {expected_completeness:.2f}")
        
        # Score consistency check
        score_variance = self._calculate_score_variance(component_scores)
        if score_variance > 0.3:  # High variance indicates inconsistent signals
            base_confidence *= 0.8
            rationale.append(f"Confidence reduced due to inconsistent component scores (variance: {score_variance:.2f})")
        
        # Data gaps impact
        critical_gaps = len([field for field in facts.missing_fields 
                           if field in self.completeness_requirements.get(facts.opportunity_type, {}).get('critical_fields', [])])
        if critical_gaps > 0:
            base_confidence *= (1 - critical_gaps * 0.2)
            rationale.append(f"Confidence reduced due to {critical_gaps} missing critical fields")
        
        # Determine confidence level
        if base_confidence >= self.confidence_thresholds[ScoreConfidenceLevel.HIGH]:
            return ScoreConfidenceLevel.HIGH, rationale
        elif base_confidence >= self.confidence_thresholds[ScoreConfidenceLevel.MEDIUM]:
            return ScoreConfidenceLevel.MEDIUM, rationale
        elif base_confidence >= self.confidence_thresholds[ScoreConfidenceLevel.LOW]:
            return ScoreConfidenceLevel.LOW, rationale
        else:
            return ScoreConfidenceLevel.VERY_LOW, rationale
    
    # Helper Methods
    
    def _extract_nested_value(self, data: Dict, path_options: List[str]) -> Optional[str]:
        """Extract value from nested dictionary using multiple path options"""
        for path in path_options:
            current = data
            keys = path.split('.')
            try:
                for key in keys:
                    current = current[key]
                if current and current != "Information not available":
                    return str(current)
            except (KeyError, TypeError):
                continue
        return None
    
    def _extract_nested_dict(self, data: Dict, path_options: List[str]) -> Dict:
        """Extract dictionary value from nested dictionary using multiple path options"""
        for path in path_options:
            current = data
            keys = path.split('.')
            try:
                for key in keys:
                    current = current[key]
                if current and isinstance(current, dict) and current != "Information not available":
                    return current
            except (KeyError, TypeError):
                continue
        return {}
    
    def _calculate_mission_alignment(self, mission_text: str, focus_areas: List[str]) -> float:
        """Calculate mission alignment using keyword matching"""
        if not focus_areas or not mission_text:
            return 0.0
            
        mission_lower = mission_text.lower()
        matches = sum(1 for area in focus_areas if area.lower() in mission_lower)
        return min(1.0, matches / len(focus_areas))
    
    def _calculate_partnership_alignment(self, csr_text: str, focus_areas: List[str]) -> float:
        """Calculate CSR partnership alignment"""
        return self._calculate_mission_alignment(csr_text, focus_areas)  # Same logic
    
    def _calculate_keyword_alignment(self, text: str, focus_areas: List[str], mission: Optional[str]) -> float:
        """Calculate alignment based on keyword matching"""
        if not text or not focus_areas:
            return 0.0
            
        text_lower = text.lower()
        focus_matches = sum(1 for area in focus_areas if area.lower() in text_lower)
        
        # Add mission keyword matching if available
        mission_bonus = 0.0
        if mission:
            mission_words = [word.strip() for word in mission.lower().split() if len(word) > 3]
            mission_matches = sum(1 for word in mission_words if word in text_lower)
            mission_bonus = min(0.2, mission_matches / max(len(mission_words), 1))
        
        base_score = min(0.8, focus_matches / max(len(focus_areas), 1))
        return base_score + mission_bonus
    
    def _check_regional_matches(self, geographic_text: str, state: str) -> str:
        """Check for regional geographic matches"""
        regional_mappings = {
            'VA': ['mid-atlantic', 'southeastern', 'east coast'],
            'NY': ['northeastern', 'mid-atlantic', 'east coast'],
            'CA': ['western', 'west coast', 'pacific'],
            'TX': ['southwestern', 'south central'],
            'FL': ['southeastern', 'south', 'east coast']
        }
        
        regions = regional_mappings.get(state, [])
        for region in regions:
            if region in geographic_text.lower():
                return region
        return ""
    
    def _parse_funding_amounts(self, funding_text: str) -> Optional[Tuple[int, int]]:
        """Parse funding amounts from text"""
        import re
        
        # Look for patterns like "$50,000 - $100,000" or "$75K to $150K"
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)\s*[-to]+\s*\$(\d{1,3}(?:,\d{3})*)',
            r'\$(\d+)[kK]\s*[-to]+\s*\$(\d+)[kK]',
            r'(\d{1,3}(?:,\d{3})*)\s*[-to]+\s*(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, funding_text)
            if match:
                try:
                    low = int(match.group(1).replace(',', ''))
                    high = int(match.group(2).replace(',', ''))
                    
                    # Handle K notation
                    if 'k' in pattern.lower():
                        low *= 1000
                        high *= 1000
                    
                    return (low, high)
                except ValueError:
                    continue
        
        return None
    
    def _calculate_funding_capacity_fit(self, funding_range: Tuple[int, int], org_revenue: float) -> float:
        """Calculate how well funding range fits organizational capacity"""
        low, high = funding_range
        avg_funding = (low + high) / 2
        
        # Optimal grant size is typically 5-20% of annual revenue
        optimal_low = org_revenue * 0.05
        optimal_high = org_revenue * 0.20
        
        if optimal_low <= avg_funding <= optimal_high:
            return 1.0  # Perfect fit
        elif avg_funding < optimal_low:
            # Too small - diminishing returns
            return 0.6 + 0.4 * (avg_funding / optimal_low)
        else:
            # Too large - capacity concerns
            capacity_ratio = optimal_high / avg_funding
            return max(0.2, capacity_ratio)
    
    def _check_government_eligibility_compliance(self, eligibility_data: Dict, profile: ProfileData) -> float:
        """Check government eligibility compliance"""
        compliance_score = 0.0
        
        # Basic organizational type check
        org_type = eligibility_data.get('organizational_type', '')
        if any(term in org_type.lower() for term in ['501c3', 'nonprofit', 'charitable']):
            compliance_score += 0.4
        
        # Geographic compliance
        geo_restrictions = eligibility_data.get('geographic_restrictions', '')
        if not geo_restrictions or profile.state.lower() in geo_restrictions.lower():
            compliance_score += 0.3
        
        # Financial capacity
        financial_reqs = eligibility_data.get('financial_capacity', '')
        if financial_reqs and profile.annual_revenue:
            # Simple check - if we have revenue data, assume basic compliance
            compliance_score += 0.3
        
        return min(1.0, compliance_score)
    
    def _check_nonprofit_eligibility_compliance(self, eligibility_data: Dict, profile: ProfileData) -> float:
        """Check nonprofit eligibility compliance"""
        # Simpler compliance for nonprofits
        compliance_score = 0.5  # Base compliance
        
        org_types = eligibility_data.get('organization_types', '')
        if any(term in org_types.lower() for term in ['501c3', 'nonprofit', 'charitable']):
            compliance_score += 0.5
        
        return min(1.0, compliance_score)
    
    def _check_corporate_partnership_compliance(self, criteria_data: Dict, profile: ProfileData) -> float:
        """Check corporate partnership criteria compliance"""
        compliance_score = 0.5  # Base partnership potential
        
        # Organization type fit
        org_types = criteria_data.get('organization_types', '')
        if any(term in org_types.lower() for term in ['nonprofit', '501c3', 'charitable']):
            compliance_score += 0.3
        
        # Program interest alignment
        program_interests = criteria_data.get('program_interests', '')
        if program_interests and profile.focus_areas:
            alignment = self._calculate_keyword_alignment(program_interests, profile.focus_areas, None)
            compliance_score += alignment * 0.2
        
        return min(1.0, compliance_score)
    
    def _calculate_score_variance(self, component_scores: Dict[str, float]) -> float:
        """Calculate variance in component scores"""
        scores = list(component_scores.values())
        if len(scores) < 2:
            return 0.0
        
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        return math.sqrt(variance)  # Standard deviation
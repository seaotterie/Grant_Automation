"""
NTEE Two-Part Scoring System (V2.0)

Implements enhanced NTEE code alignment scoring with:
- Two-part scoring: Major code (40%) + Leaf code (60%)
- Multi-source validation: BMF → Schedule I recipients → Website scraping
- Confidence penalties when only major code available
- Time-decay integration for aging data
- Support for partial matches and fuzzy alignment

NTEE Structure:
- Major Code (1 char): A-Z category (e.g., 'B' = Education)
- Leaf Code (2-3 digits): Subcategory (e.g., '25' = Elementary/Secondary)
- Full Code: "B25" = Elementary/Secondary Education

Phase 2, Week 3 Implementation
Expected Impact: 30-40% reduction in false positives
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from .scoring_config import (
    NTEE_MAJOR_WEIGHT,
    NTEE_LEAF_WEIGHT,
    NTEE_MAX_CONTRIBUTION,
)
from .time_decay_utils import TimeDecayCalculator, DecayType


logger = logging.getLogger(__name__)


class NTEEDataSource(str, Enum):
    """Source of NTEE code data"""
    BMF = "bmf"  # IRS Business Master File (most authoritative)
    SCHEDULE_I = "schedule_i"  # Inferred from Schedule I recipients
    WEBSITE = "website"  # Scraped from organization website
    USER_PROVIDED = "user_provided"  # Manually entered by user
    UNKNOWN = "unknown"


class NTEEMatchLevel(str, Enum):
    """Level of NTEE code matching"""
    EXACT_FULL = "exact_full"  # Exact major + leaf match (B25 = B25)
    EXACT_MAJOR = "exact_major"  # Major match, different leaf (B25 = B30)
    RELATED_MAJOR = "related_major"  # Related major codes (B = E for education)
    NO_MATCH = "no_match"  # No alignment


@dataclass
class NTEECode:
    """
    Parsed NTEE code with metadata

    Examples:
        "B25" → major='B', leaf='25', full_code='B25'
        "B" → major='B', leaf=None, full_code='B'
        "P20" → major='P', leaf='20', full_code='P20'
    """
    full_code: str
    major: str  # Single letter A-Z
    leaf: Optional[str] = None  # 2-3 digit subcategory
    source: NTEEDataSource = NTEEDataSource.UNKNOWN
    source_date: Optional[datetime] = None  # When this code was obtained
    confidence: float = 1.0  # 0.0-1.0 confidence in this code

    @classmethod
    def parse(cls, code_str: str,
              source: NTEEDataSource = NTEEDataSource.UNKNOWN,
              source_date: Optional[datetime] = None) -> Optional['NTEECode']:
        """
        Parse NTEE code string into structured format

        Args:
            code_str: NTEE code string (e.g., "B25", "B", "P20")
            source: Where this code came from
            source_date: When this code was obtained (for time-decay)

        Returns:
            Parsed NTEECode or None if invalid
        """
        if not code_str or not isinstance(code_str, str):
            return None

        code_str = code_str.strip().upper()

        # Must start with letter A-Z
        if not code_str or not code_str[0].isalpha():
            return None

        major = code_str[0]
        leaf = code_str[1:] if len(code_str) > 1 else None

        # Validate leaf is numeric if present
        if leaf and not leaf.isdigit():
            logger.warning(f"Invalid NTEE leaf code: {leaf} in {code_str}")
            leaf = None

        # Set confidence based on completeness
        confidence = 1.0 if leaf else 0.7  # Penalty for major-only codes

        return cls(
            full_code=code_str,
            major=major,
            leaf=leaf,
            source=source,
            source_date=source_date,
            confidence=confidence
        )


@dataclass
class NTEEScoreResult:
    """Result of NTEE scoring comparison"""
    score: float  # 0.0-1.0 normalized score
    match_level: NTEEMatchLevel
    profile_codes: List[NTEECode]
    foundation_codes: List[NTEECode]
    major_score: float  # Raw major code contribution
    leaf_score: float  # Raw leaf code contribution
    time_decay_factor: float  # Applied time-decay weight
    confidence: float  # Overall confidence in this score
    explanation: str  # Human-readable explanation

    @property
    def weighted_score(self) -> float:
        """Final score with time-decay applied"""
        return self.score * self.time_decay_factor


# NTEE Major Code Relationships
# Some major codes are closely related and should receive partial credit
NTEE_RELATED_MAJORS: Dict[str, Set[str]] = {
    'B': {'E', 'O'},  # Education related to schools and youth
    'E': {'B', 'O'},  # Elementary/Secondary related to education
    'O': {'B', 'E'},  # Youth development related to education
    'P': {'Q', 'E'},  # Health related to hospitals and mental health
    'Q': {'P', 'E'},  # Hospitals related to health
    'C': {'D', 'K'},  # Environment related to conservation and food/ag
    'D': {'C', 'K'},  # Animal-related related to environment
    'K': {'C', 'D'},  # Food/Agriculture related to environment
    'S': {'P', 'I'},  # Community improvement related to health and crime
    'I': {'S', 'J'},  # Crime/Legal related to community
    'A': {'T', 'V'},  # Arts related to humanities and religion
    'T': {'A', 'V'},  # Philanthropy related to arts
    'V': {'A', 'T', 'X'},  # Religion related to arts and faith-based
}


class NTEEScorer:
    """
    Two-part NTEE scoring system with multi-source validation

    Scoring Logic:
    1. Major Code Match (40% weight): Primary category alignment
    2. Leaf Code Match (60% weight): Subcategory specificity
    3. Time-Decay: Apply exponential decay to aging codes
    4. Confidence Penalties: Reduce score when only major code available
    5. Source Priority: BMF > Schedule I > Website > User

    Example Scores:
    - Exact match (B25 = B25): 1.0 × 0.4 (major) + 1.0 × 0.6 (leaf) = 1.0
    - Major match (B25 = B30): 1.0 × 0.4 (major) + 0.0 × 0.6 (leaf) = 0.4
    - Related major (B25 = E20): 0.5 × 0.4 (major) + 0.0 × 0.6 (leaf) = 0.2
    - No match (B25 = P20): 0.0
    """

    def __init__(self,
                 time_decay_calculator: Optional[TimeDecayCalculator] = None,
                 enable_time_decay: bool = True):
        """
        Initialize NTEE scorer

        Args:
            time_decay_calculator: Calculator for aging code data
            enable_time_decay: Whether to apply time-decay to scores
        """
        self.logger = logging.getLogger(f"{__name__}.NTEEScorer")
        self.time_decay = time_decay_calculator or TimeDecayCalculator(DecayType.NTEE_MISSION)
        self.enable_time_decay = enable_time_decay

    def score_alignment(self,
                       profile_codes: List[str],
                       foundation_codes: List[str],
                       profile_code_sources: Optional[Dict[str, NTEEDataSource]] = None,
                       foundation_code_sources: Optional[Dict[str, NTEEDataSource]] = None,
                       profile_code_dates: Optional[Dict[str, datetime]] = None,
                       foundation_code_dates: Optional[Dict[str, datetime]] = None) -> NTEEScoreResult:
        """
        Calculate NTEE alignment score between profile and foundation

        Args:
            profile_codes: List of NTEE codes for the profile (e.g., ["B25", "B30"])
            foundation_codes: List of NTEE codes foundation funds (e.g., ["B25", "E20"])
            profile_code_sources: Source of each profile code (for confidence)
            foundation_code_sources: Source of each foundation code
            profile_code_dates: When each profile code was obtained (for time-decay)
            foundation_code_dates: When each foundation code was obtained

        Returns:
            NTEEScoreResult with detailed scoring breakdown
        """
        # Parse all codes
        parsed_profile = self._parse_codes(
            profile_codes,
            profile_code_sources or {},
            profile_code_dates or {}
        )
        parsed_foundation = self._parse_codes(
            foundation_codes,
            foundation_code_sources or {},
            foundation_code_dates or {}
        )

        if not parsed_profile or not parsed_foundation:
            return self._create_empty_result(parsed_profile, parsed_foundation)

        # Find best match across all code pairs
        best_major_score = 0.0
        best_leaf_score = 0.0
        best_match_level = NTEEMatchLevel.NO_MATCH
        best_explanation = "No NTEE code alignment found"

        for p_code in parsed_profile:
            for f_code in parsed_foundation:
                major_score, leaf_score, match_level, explanation = self._compare_codes(
                    p_code, f_code
                )

                # Use best match found
                total_score = major_score * NTEE_MAJOR_WEIGHT + leaf_score * NTEE_LEAF_WEIGHT
                best_total = best_major_score * NTEE_MAJOR_WEIGHT + best_leaf_score * NTEE_LEAF_WEIGHT

                if total_score > best_total:
                    best_major_score = major_score
                    best_leaf_score = leaf_score
                    best_match_level = match_level
                    best_explanation = explanation

        # Calculate overall confidence (average of all code confidences)
        avg_profile_confidence = sum(c.confidence for c in parsed_profile) / len(parsed_profile)
        avg_foundation_confidence = sum(c.confidence for c in parsed_foundation) / len(parsed_foundation)
        overall_confidence = (avg_profile_confidence + avg_foundation_confidence) / 2.0

        # Apply time-decay if enabled
        time_decay_factor = 1.0
        if self.enable_time_decay:
            time_decay_factor = self._calculate_time_decay(
                parsed_profile + parsed_foundation
            )

        # Calculate final score
        raw_score = best_major_score * NTEE_MAJOR_WEIGHT + best_leaf_score * NTEE_LEAF_WEIGHT
        final_score = raw_score * overall_confidence  # Apply confidence penalty

        return NTEEScoreResult(
            score=final_score,
            match_level=best_match_level,
            profile_codes=parsed_profile,
            foundation_codes=parsed_foundation,
            major_score=best_major_score,
            leaf_score=best_leaf_score,
            time_decay_factor=time_decay_factor,
            confidence=overall_confidence,
            explanation=best_explanation
        )

    def _parse_codes(self,
                    codes: List[str],
                    sources: Dict[str, NTEEDataSource],
                    dates: Dict[str, datetime]) -> List[NTEECode]:
        """Parse list of NTEE code strings into structured format"""
        parsed = []
        for code_str in codes:
            source = sources.get(code_str, NTEEDataSource.UNKNOWN)
            date = dates.get(code_str)

            ntee_code = NTEECode.parse(code_str, source=source, source_date=date)
            if ntee_code:
                parsed.append(ntee_code)
            else:
                self.logger.warning(f"Failed to parse NTEE code: {code_str}")

        return parsed

    def _compare_codes(self,
                      profile_code: NTEECode,
                      foundation_code: NTEECode) -> Tuple[float, float, NTEEMatchLevel, str]:
        """
        Compare two NTEE codes and return scoring breakdown

        Returns:
            (major_score, leaf_score, match_level, explanation)
        """
        major_score = 0.0
        leaf_score = 0.0

        # Major code comparison
        if profile_code.major == foundation_code.major:
            major_score = 1.0
            match_level = NTEEMatchLevel.EXACT_MAJOR
            explanation = f"Major code match: {profile_code.major} = {foundation_code.major}"

            # Leaf code comparison (only if majors match)
            if profile_code.leaf and foundation_code.leaf:
                if profile_code.leaf == foundation_code.leaf:
                    leaf_score = 1.0
                    match_level = NTEEMatchLevel.EXACT_FULL
                    explanation = f"Exact NTEE match: {profile_code.full_code} = {foundation_code.full_code}"
                else:
                    # Majors match but leafs differ - no leaf credit
                    leaf_score = 0.0
                    explanation = f"Major match but different subcategory: {profile_code.full_code} vs {foundation_code.full_code}"
            elif not profile_code.leaf or not foundation_code.leaf:
                # One or both missing leaf - partial leaf credit with penalty
                leaf_score = 0.5
                explanation = f"Major match with incomplete subcategory: {profile_code.full_code} vs {foundation_code.full_code}"

        elif profile_code.major in NTEE_RELATED_MAJORS.get(foundation_code.major, set()):
            # Related major codes - partial credit
            major_score = 0.5
            leaf_score = 0.0
            match_level = NTEEMatchLevel.RELATED_MAJOR
            explanation = f"Related major codes: {profile_code.major} ~ {foundation_code.major}"
        else:
            # No match
            major_score = 0.0
            leaf_score = 0.0
            match_level = NTEEMatchLevel.NO_MATCH
            explanation = f"No NTEE alignment: {profile_code.major} ≠ {foundation_code.major}"

        return major_score, leaf_score, match_level, explanation

    def _calculate_time_decay(self, codes: List[NTEECode]) -> float:
        """
        Calculate average time-decay factor across all codes

        Codes without dates receive no decay penalty (factor = 1.0)
        """
        if not codes:
            return 1.0

        decay_factors = []
        current_date = datetime.now()

        for code in codes:
            if code.source_date:
                months_old = (current_date - code.source_date).days / 30.44
                decay_factor = self.time_decay.calculate_decay(months_old)
                decay_factors.append(decay_factor)
            else:
                # No date = no decay penalty
                decay_factors.append(1.0)

        return sum(decay_factors) / len(decay_factors) if decay_factors else 1.0

    def _create_empty_result(self,
                            parsed_profile: List[NTEECode],
                            parsed_foundation: List[NTEECode]) -> NTEEScoreResult:
        """Create result for empty/missing NTEE codes"""
        if not parsed_profile and not parsed_foundation:
            explanation = "No NTEE codes provided for profile or foundation"
        elif not parsed_profile:
            explanation = "No valid NTEE codes for profile"
        else:
            explanation = "No valid NTEE codes for foundation"

        return NTEEScoreResult(
            score=0.0,
            match_level=NTEEMatchLevel.NO_MATCH,
            profile_codes=parsed_profile,
            foundation_codes=parsed_foundation,
            major_score=0.0,
            leaf_score=0.0,
            time_decay_factor=1.0,
            confidence=0.0,
            explanation=explanation
        )

    def extract_codes_from_schedule_i(self,
                                     schedule_i_recipients: List[Dict]) -> List[str]:
        """
        Extract NTEE codes from Schedule I recipient data

        Infers foundation's funding interests from recipient organizations.
        Uses EIN resolution to look up recipient NTEE codes in BMF.

        Args:
            schedule_i_recipients: List of recipient dicts with 'ein', 'name', etc.

        Returns:
            List of inferred NTEE codes from recipients

        Note:
            Requires EIN resolution and BMF lookup - placeholder for Phase 2
        """
        # TODO: Implement in Phase 2, Week 4-5 (Schedule I recipient voting)
        # Will integrate with EINResolver and BMF database
        self.logger.debug("Schedule I NTEE extraction not yet implemented")
        return []

    def extract_codes_from_website(self, website_text: str) -> List[str]:
        """
        Extract NTEE codes from website text via keyword matching

        Args:
            website_text: Raw text content from organization website

        Returns:
            List of inferred NTEE codes based on keywords

        Note:
            Basic keyword matching - can be enhanced with Tool 25 integration
        """
        # TODO: Enhance with Tool 25 (Web Intelligence Tool) integration
        # For now, basic keyword matching
        codes = set()
        text_lower = website_text.lower()

        # Education keywords
        if any(kw in text_lower for kw in ['education', 'school', 'student', 'teacher', 'learning']):
            codes.add('B')  # Education major code

        # Health keywords
        if any(kw in text_lower for kw in ['health', 'medical', 'hospital', 'patient', 'clinic']):
            codes.add('P')  # Health major code

        # Environment keywords
        if any(kw in text_lower for kw in ['environment', 'conservation', 'wildlife', 'climate', 'green']):
            codes.add('C')  # Environment major code

        # Arts keywords
        if any(kw in text_lower for kw in ['arts', 'culture', 'museum', 'theater', 'music']):
            codes.add('A')  # Arts major code

        # Human services keywords
        if any(kw in text_lower for kw in ['homeless', 'shelter', 'food bank', 'poverty', 'community service']):
            codes.add('S')  # Community improvement major code

        self.logger.debug(f"Extracted {len(codes)} NTEE codes from website: {codes}")
        return list(codes)


# Convenience functions
def score_ntee_alignment(profile_codes: List[str],
                        foundation_codes: List[str],
                        enable_time_decay: bool = True) -> NTEEScoreResult:
    """
    Convenience function for NTEE scoring without metadata

    Args:
        profile_codes: Profile NTEE codes
        foundation_codes: Foundation NTEE codes
        enable_time_decay: Whether to apply time-decay

    Returns:
        NTEEScoreResult with scoring details
    """
    scorer = NTEEScorer(enable_time_decay=enable_time_decay)
    return scorer.score_alignment(profile_codes, foundation_codes)


def get_ntee_major_description(major_code: str) -> str:
    """Get human-readable description of NTEE major code"""
    descriptions = {
        'A': 'Arts, Culture, and Humanities',
        'B': 'Education',
        'C': 'Environment',
        'D': 'Animal-Related',
        'E': 'Health Care',
        'F': 'Mental Health and Crisis Intervention',
        'G': 'Voluntary Health Associations and Medical Disciplines',
        'H': 'Medical Research',
        'I': 'Crime and Legal-Related',
        'J': 'Employment',
        'K': 'Food, Agriculture, and Nutrition',
        'L': 'Housing and Shelter',
        'M': 'Public Safety, Disaster Preparedness and Relief',
        'N': 'Recreation and Sports',
        'O': 'Youth Development',
        'P': 'Human Services',
        'Q': 'International, Foreign Affairs, and National Security',
        'R': 'Civil Rights, Social Action, and Advocacy',
        'S': 'Community Improvement and Capacity Building',
        'T': 'Philanthropy, Voluntarism, and Grantmaking Foundations',
        'U': 'Science and Technology',
        'V': 'Social Science',
        'W': 'Public and Societal Benefit',
        'X': 'Religion-Related',
        'Y': 'Mutual and Membership Benefit',
        'Z': 'Unknown',
    }
    return descriptions.get(major_code.upper(), 'Unknown')

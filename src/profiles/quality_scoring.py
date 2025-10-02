"""
Data Quality Scoring System

Task 18: Comprehensive data quality scoring across profile sources.

This module provides quality scoring for:
1. Profile data sources (BMF, Form 990, Tool 25, Tool 2)
2. Funding opportunities (foundations with 990-PF)
3. Networking opportunities (peer nonprofits with 990)

Quality scores are calculated based on:
- Data completeness (required vs optional fields)
- Data accuracy (validation rules)
- Confidence levels (from AI/scraping tools)

Scoring Formula (from PROFILE_ENHANCEMENT_DATA_FLOW.md):
- Profile Quality = BMF(20%) + 990(35%) + Tool25(25%) + Tool2(20%)
- Funding Opportunity = Mission(30%) + Geography(20%) + GrantSize(25%) + Recipients(15%) + Feasibility(10%)
- Networking Opportunity = Mission(25%) + Board(25%) + Funders(30%) + Collaboration(20%)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class QualityRating(Enum):
    """Quality rating categories."""
    EXCELLENT = "EXCELLENT"  # >=0.85 for profiles, >=0.80 for funding, >=0.70 for networking
    GOOD = "GOOD"  # 0.70-0.84 for profiles, 0.65-0.79 for funding
    FAIR = "FAIR"  # 0.50-0.69 for profiles, 0.50-0.64 for funding
    POOR = "POOR"  # <0.50 for profiles, <0.50 for funding
    HIGH = "HIGH"  # >=0.70 for networking
    MEDIUM = "MEDIUM"  # 0.50-0.69 for networking
    LOW = "LOW"  # <0.50 for networking


@dataclass
class QualityScore:
    """Detailed quality score with breakdown."""
    overall_score: float  # 0.0-1.0
    rating: QualityRating
    component_scores: Dict[str, float] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    confidence_level: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)


class ProfileQualityScorer:
    """
    Calculate quality scores for profile data sources.

    Implements the scoring methodology from PROFILE_ENHANCEMENT_DATA_FLOW.md.
    """

    # Required and optional fields for each source
    BMF_REQUIRED = ['ein', 'name', 'state']
    BMF_OPTIONAL = ['ntee_code', 'city', 'address']

    FORM_990_CRITICAL = ['totrevenue', 'totfuncexpns', 'totassetsend']
    FORM_990_IMPORTANT = ['totliabend', 'totnetassetend', 'tax_year']
    FORM_990_OPTIONAL = ['topempcompexpens', 'numemps', 'numvols']

    TOOL25_CRITICAL = ['mission_statement', 'contact_info']
    TOOL25_IMPORTANT = ['leadership', 'programs']
    TOOL25_OPTIONAL = ['achievements', 'initiatives', 'partnerships']

    def score_bmf_data(self, bmf_data: Dict[str, Any]) -> QualityScore:
        """
        Score BMF (Business Master File) data quality.

        BMF contributes 20% to overall profile quality.

        Args:
            bmf_data: Organization data from BMF

        Returns:
            QualityScore with breakdown
        """
        missing = []
        errors = []
        recommendations = []

        # Check required fields
        required_present = 0
        for field in self.BMF_REQUIRED:
            if bmf_data.get(field):
                required_present += 1
            else:
                missing.append(field)
                errors.append(f"Missing required BMF field: {field}")

        required_score = required_present / len(self.BMF_REQUIRED)

        # Check optional fields (bonus points)
        optional_present = 0
        for field in self.BMF_OPTIONAL:
            if bmf_data.get(field):
                optional_present += 1
            else:
                missing.append(f"{field} (optional)")

        optional_score = optional_present / len(self.BMF_OPTIONAL)

        # Overall BMF score: 80% weight on required, 20% on optional
        overall = (required_score * 0.80) + (optional_score * 0.20)

        # Determine rating
        if overall >= 0.90:
            rating = QualityRating.EXCELLENT
        elif overall >= 0.75:
            rating = QualityRating.GOOD
        elif overall >= 0.50:
            rating = QualityRating.FAIR
        else:
            rating = QualityRating.POOR
            recommendations.append("BMF data incomplete - verify organization EIN")

        # NTEE code specific recommendation
        if not bmf_data.get('ntee_code'):
            recommendations.append("NTEE code missing - limits opportunity matching accuracy")

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores={
                'required_fields': required_score,
                'optional_fields': optional_score
            },
            missing_fields=missing,
            validation_errors=errors,
            recommendations=recommendations
        )

    def score_form_990(self, form_990: Dict[str, Any]) -> QualityScore:
        """
        Score Form 990 data quality.

        Form 990 contributes 35% to overall profile quality.

        Args:
            form_990: Financial data from Form 990

        Returns:
            QualityScore with breakdown
        """
        missing = []
        errors = []
        recommendations = []

        # Critical fields (must have)
        critical_present = 0
        for field in self.FORM_990_CRITICAL:
            value = form_990.get(field)
            if value is not None and value > 0:
                critical_present += 1
            else:
                missing.append(field)
                errors.append(f"Missing or invalid 990 field: {field}")

        critical_score = critical_present / len(self.FORM_990_CRITICAL)

        # Important fields
        important_present = 0
        for field in self.FORM_990_IMPORTANT:
            if form_990.get(field) is not None:
                important_present += 1
            else:
                missing.append(f"{field} (important)")

        important_score = important_present / len(self.FORM_990_IMPORTANT)

        # Optional fields
        optional_present = 0
        for field in self.FORM_990_OPTIONAL:
            if form_990.get(field) is not None:
                optional_present += 1
            else:
                missing.append(f"{field} (optional)")

        optional_score = optional_present / len(self.FORM_990_OPTIONAL)

        # Overall 990 score: 50% critical, 35% important, 15% optional
        overall = (critical_score * 0.50) + (important_score * 0.35) + (optional_score * 0.15)

        # Determine rating
        if overall >= 0.90:
            rating = QualityRating.EXCELLENT
        elif overall >= 0.75:
            rating = QualityRating.GOOD
        elif overall >= 0.50:
            rating = QualityRating.FAIR
        else:
            rating = QualityRating.POOR
            recommendations.append("Form 990 data incomplete - may limit financial analysis")

        # Financial health checks
        if critical_score >= 1.0:
            revenue = form_990.get('totrevenue', 0)
            expenses = form_990.get('totfuncexpns', 0)
            if revenue > 0 and expenses > 0:
                margin = (revenue - expenses) / revenue
                if margin < 0:
                    recommendations.append("Negative operating margin - review financial health")
                elif margin < 0.05:
                    recommendations.append("Low operating margin (<5%) - financial sustainability concern")

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores={
                'critical_fields': critical_score,
                'important_fields': important_score,
                'optional_fields': optional_score
            },
            missing_fields=missing,
            validation_errors=errors,
            recommendations=recommendations
        )

    def score_tool25_data(self, tool25_data: Dict[str, Any]) -> QualityScore:
        """
        Score Tool 25 (web intelligence) data quality.

        Tool 25 contributes 25% to overall profile quality.

        Args:
            tool25_data: Web-scraped data from Tool 25

        Returns:
            QualityScore with breakdown
        """
        missing = []
        errors = []
        recommendations = []
        confidence_scores = []

        if not tool25_data:
            return QualityScore(
                overall_score=0.0,
                rating=QualityRating.POOR,
                validation_errors=["No Tool 25 data available"],
                recommendations=["Run Tool 25 to gather web intelligence"]
            )

        # Extract confidence scores
        critical_present = 0
        for field in self.TOOL25_CRITICAL:
            if field in tool25_data:
                data = tool25_data[field]
                if isinstance(data, dict) and 'confidence' in data:
                    confidence = data['confidence']
                    confidence_scores.append(confidence)
                    if confidence >= 0.60:
                        critical_present += 1
                    else:
                        errors.append(f"Low confidence for {field}: {confidence:.2f}")
                elif data:  # Has data but no confidence score
                    critical_present += 1
                    confidence_scores.append(0.75)  # Assume medium confidence
            else:
                missing.append(field)

        critical_score = critical_present / len(self.TOOL25_CRITICAL)

        # Important fields
        important_present = 0
        for field in self.TOOL25_IMPORTANT:
            if field in tool25_data:
                data = tool25_data[field]
                if isinstance(data, dict) and 'confidence' in data:
                    confidence = data['confidence']
                    confidence_scores.append(confidence)
                    if confidence >= 0.50:
                        important_present += 1
                elif data:
                    important_present += 1
                    confidence_scores.append(0.70)
            else:
                missing.append(f"{field} (important)")

        important_score = important_present / len(self.TOOL25_IMPORTANT)

        # Optional fields
        optional_present = 0
        for field in self.TOOL25_OPTIONAL:
            if field in tool25_data and tool25_data[field]:
                optional_present += 1
                if isinstance(tool25_data[field], dict) and 'confidence' in tool25_data[field]:
                    confidence_scores.append(tool25_data[field]['confidence'])
            else:
                missing.append(f"{field} (optional)")

        optional_score = optional_present / len(self.TOOL25_OPTIONAL)

        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Overall Tool 25 score: 45% critical, 35% important, 20% optional
        overall = (critical_score * 0.45) + (important_score * 0.35) + (optional_score * 0.20)

        # Determine rating based on both completeness and confidence
        if overall >= 0.85 and avg_confidence >= 0.75:
            rating = QualityRating.EXCELLENT
        elif overall >= 0.70 and avg_confidence >= 0.60:
            rating = QualityRating.GOOD
        elif overall >= 0.50 and avg_confidence >= 0.50:
            rating = QualityRating.FAIR
        else:
            rating = QualityRating.POOR
            recommendations.append("Tool 25 data quality low - consider re-scraping")

        if avg_confidence < 0.60:
            recommendations.append(f"Low average confidence ({avg_confidence:.2f}) - verify web data manually")

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores={
                'critical_fields': critical_score,
                'important_fields': important_score,
                'optional_fields': optional_score
            },
            missing_fields=missing,
            validation_errors=errors,
            confidence_level=avg_confidence,
            recommendations=recommendations
        )

    def score_tool2_data(self, tool2_data: Optional[Dict[str, Any]]) -> QualityScore:
        """
        Score Tool 2 (AI analysis) data quality.

        Tool 2 contributes 20% to overall profile quality.

        Args:
            tool2_data: AI analysis data from Tool 2 (optional)

        Returns:
            QualityScore with breakdown
        """
        if not tool2_data:
            # Tool 2 is optional - no penalty for missing
            return QualityScore(
                overall_score=0.0,
                rating=QualityRating.FAIR,
                recommendations=["Tool 2 AI analysis not performed - optional enhancement"]
            )

        # Check for expected AI analysis components
        expected_components = [
            'strategic_positioning',
            'competitive_advantages',
            'organizational_strengths',
            'grant_readiness',
            'recommendations'
        ]

        present = 0
        missing = []
        for component in expected_components:
            if component in tool2_data and tool2_data[component]:
                present += 1
            else:
                missing.append(component)

        completeness = present / len(expected_components)

        # Tool 2 is binary: either it ran successfully (1.0) or not (0.0)
        overall = 1.0 if completeness >= 0.60 else completeness

        if overall >= 0.80:
            rating = QualityRating.EXCELLENT
        elif overall >= 0.60:
            rating = QualityRating.GOOD
        elif overall >= 0.40:
            rating = QualityRating.FAIR
        else:
            rating = QualityRating.POOR

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores={'completeness': completeness},
            missing_fields=missing,
            recommendations=[] if overall >= 0.80 else ["Tool 2 analysis incomplete"]
        )

    def calculate_profile_quality(
        self,
        bmf_data: Dict[str, Any],
        form_990: Optional[Dict[str, Any]] = None,
        tool25_data: Optional[Dict[str, Any]] = None,
        tool2_data: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Calculate overall profile quality from all sources.

        Formula: Profile Quality = BMF(20%) + 990(35%) + Tool25(25%) + Tool2(20%)

        Args:
            bmf_data: BMF organization data (required)
            form_990: Form 990 financial data (optional)
            tool25_data: Tool 25 web intelligence (optional)
            tool2_data: Tool 2 AI analysis (optional)

        Returns:
            Overall QualityScore with component breakdown
        """
        # Score each component
        bmf_score = self.score_bmf_data(bmf_data)
        form_990_score = self.score_form_990(form_990) if form_990 else QualityScore(
            overall_score=0.0,
            rating=QualityRating.POOR,
            validation_errors=["Form 990 data not available"]
        )
        tool25_score = self.score_tool25_data(tool25_data) if tool25_data else QualityScore(
            overall_score=0.0,
            rating=QualityRating.FAIR,
            recommendations=["Tool 25 not executed"]
        )
        tool2_score = self.score_tool2_data(tool2_data)

        # Calculate weighted overall score
        overall = (
            (bmf_score.overall_score * 0.20) +
            (form_990_score.overall_score * 0.35) +
            (tool25_score.overall_score * 0.25) +
            (tool2_score.overall_score * 0.20)
        )

        # Determine overall rating
        if overall >= 0.85:
            rating = QualityRating.EXCELLENT
            rating_msg = "Excellent - Profile complete with high-quality data"
        elif overall >= 0.70:
            rating = QualityRating.GOOD
            rating_msg = "Good - Profile mostly complete with reliable data"
        elif overall >= 0.50:
            rating = QualityRating.FAIR
            rating_msg = "Fair - Profile has basic data but missing enhancements"
        else:
            rating = QualityRating.POOR
            rating_msg = "Poor - Profile incomplete, additional data needed"

        # Aggregate all recommendations
        recommendations = []
        if bmf_score.recommendations:
            recommendations.extend(bmf_score.recommendations)
        if form_990_score.recommendations:
            recommendations.extend(form_990_score.recommendations)
        if tool25_score.recommendations:
            recommendations.extend(tool25_score.recommendations)
        if tool2_score.recommendations:
            recommendations.extend(tool2_score.recommendations)

        recommendations.append(rating_msg)

        # Aggregate all errors
        errors = []
        errors.extend(bmf_score.validation_errors)
        errors.extend(form_990_score.validation_errors)
        errors.extend(tool25_score.validation_errors)

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores={
                'bmf': bmf_score.overall_score,
                'form_990': form_990_score.overall_score,
                'tool_25': tool25_score.overall_score,
                'tool_2': tool2_score.overall_score
            },
            validation_errors=errors,
            recommendations=recommendations
        )


class OpportunityQualityScorer:
    """
    Calculate quality scores for opportunity matching.

    Implements scoring for:
    1. Funding opportunities (foundations with 990-PF)
    2. Networking opportunities (peer nonprofits with 990)
    """

    def score_funding_opportunity(
        self,
        profile: Dict[str, Any],
        foundation: Dict[str, Any]
    ) -> QualityScore:
        """
        Score a funding opportunity based on profile fit.

        Formula: Score = Mission(30%) + Geography(20%) + GrantSize(25%) +
                        Recipients(15%) + Feasibility(10%)

        Args:
            profile: Profile data (YOUR organization)
            foundation: Foundation data from BMF + 990-PF

        Returns:
            QualityScore for funding opportunity
        """
        scores = {}
        recommendations = []

        # Mission alignment (0.0-1.0) - 30% weight
        profile_ntee = set(profile.get('ntee_codes', []))
        foundation_ntee = set(foundation.get('funded_ntee_codes', []))

        if profile_ntee and foundation_ntee:
            ntee_overlap = len(profile_ntee & foundation_ntee)
            mission_score = min(ntee_overlap / len(profile_ntee), 1.0)
        else:
            mission_score = 0.5  # Unknown, assume moderate fit
            recommendations.append("NTEE codes missing - mission alignment uncertain")

        scores['mission_alignment'] = mission_score

        # Geographic fit (0.0-1.0) - 20% weight
        profile_states = set(profile.get('geographic_scope', {}).get('states', []))
        foundation_state = foundation.get('state', '')
        foundation_nationwide = foundation.get('nationwide_scope', False)

        if foundation_nationwide or foundation_state in profile_states:
            geo_score = 1.0
        elif profile_states and foundation_state:
            geo_score = 0.5  # Different state but still possible
            recommendations.append(f"Foundation in {foundation_state}, you in {profile_states} - may limit eligibility")
        else:
            geo_score = 0.3
            recommendations.append("Geographic alignment uncertain")

        scores['geographic_fit'] = geo_score

        # Grant size fit (0.0-1.0) - 25% weight
        profile_budget = profile.get('annual_budget', 0)
        avg_grant = foundation.get('avg_grant_size', 0)

        if profile_budget > 0 and avg_grant > 0:
            # Ideal grant is 10-30% of annual budget
            ideal_min = profile_budget * 0.10
            ideal_max = profile_budget * 0.30

            if ideal_min <= avg_grant <= ideal_max:
                grant_score = 1.0
            elif avg_grant < ideal_min:
                grant_score = 0.7  # Grant too small but still valuable
                recommendations.append(f"Grant size (${avg_grant:,}) small for budget (${profile_budget:,})")
            else:
                grant_score = 0.5  # Grant too large, may be harder to win
                recommendations.append(f"Grant size (${avg_grant:,}) large for budget (${profile_budget:,})")
        else:
            grant_score = 0.5  # Unknown
            recommendations.append("Budget or grant size data missing")

        scores['grant_size_fit'] = grant_score

        # Past recipients similarity (0.0-1.0) - 15% weight
        similar_recipients = foundation.get('similar_recipient_count', 0)
        recipient_score = min(similar_recipients / 10, 1.0)
        scores['past_recipients'] = recipient_score

        if recipient_score < 0.3:
            recommendations.append("Foundation rarely funds similar organizations - research fit carefully")

        # Application feasibility (0.0-1.0) - 10% weight
        has_open_application = foundation.get('accepts_applications', True)
        application_deadline = foundation.get('next_deadline', None)

        if has_open_application and application_deadline:
            feasibility_score = 1.0
        elif has_open_application:
            feasibility_score = 0.8
            recommendations.append("Application process open but no deadline published")
        else:
            feasibility_score = 0.3
            recommendations.append("Foundation may not accept unsolicited applications - verify")

        scores['application_feasibility'] = feasibility_score

        # Calculate overall score
        overall = (
            (mission_score * 0.30) +
            (geo_score * 0.20) +
            (grant_score * 0.25) +
            (recipient_score * 0.15) +
            (feasibility_score * 0.10)
        )

        # Determine rating
        if overall >= 0.80:
            rating = QualityRating.EXCELLENT
            recommendations.append("Excellent fit - Top priority for application")
        elif overall >= 0.65:
            rating = QualityRating.GOOD
            recommendations.append("Good fit - High priority for application")
        elif overall >= 0.50:
            rating = QualityRating.FAIR
            recommendations.append("Fair fit - Worth exploring further")
        else:
            rating = QualityRating.POOR
            recommendations.append("Poor fit - Low priority")

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores=scores,
            recommendations=recommendations
        )

    def score_networking_opportunity(
        self,
        profile: Dict[str, Any],
        peer_org: Dict[str, Any]
    ) -> QualityScore:
        """
        Score a networking opportunity based on strategic value.

        Formula: Score = Mission(25%) + Board(25%) + Funders(30%) + Collaboration(20%)

        Args:
            profile: Profile data (YOUR organization)
            peer_org: Peer nonprofit from BMF + 990

        Returns:
            QualityScore for networking opportunity
        """
        scores = {}
        recommendations = []

        # Mission similarity (0.0-1.0) - 25% weight
        profile_ntee = set(profile.get('ntee_codes', []))
        peer_ntee = set(peer_org.get('ntee_codes', []))

        if profile_ntee and peer_ntee:
            ntee_overlap = len(profile_ntee & peer_ntee)
            mission_score = min(ntee_overlap / len(profile_ntee), 1.0)
        else:
            mission_score = 0.5
            recommendations.append("NTEE codes missing - mission similarity uncertain")

        scores['mission_similarity'] = mission_score

        # Board connections (0.0-1.0) - 25% weight
        shared_board = peer_org.get('shared_board_members', 0)
        board_score = min(shared_board / 5, 1.0)  # 5+ shared members = perfect score
        scores['board_connections'] = board_score

        if shared_board > 0:
            recommendations.append(f"{shared_board} shared board members - strong connection potential")
        else:
            recommendations.append("No known board connections - explore relationship opportunities")

        # Funder overlap (0.0-1.0) - 30% weight (HIGHEST)
        shared_funders = peer_org.get('shared_funders', 0)
        funder_score = min(shared_funders / 10, 1.0)  # 10+ shared funders = perfect score
        scores['funder_overlap'] = funder_score

        if shared_funders >= 5:
            recommendations.append(f"{shared_funders} shared funders - strong partnership potential")
        elif shared_funders > 0:
            recommendations.append(f"{shared_funders} shared funders - possible collaboration")
        else:
            recommendations.append("No known shared funders - limited strategic value")

        # Collaboration potential (0.0-1.0) - 20% weight
        # Based on size, capacity, complementary programs
        profile_budget = profile.get('annual_budget', 0)
        peer_budget = peer_org.get('annual_budget', 0)

        if profile_budget > 0 and peer_budget > 0:
            # Similar-sized organizations often collaborate well
            size_ratio = min(profile_budget, peer_budget) / max(profile_budget, peer_budget)
            collab_score = size_ratio  # Closer to 1.0 = more similar sizes
        else:
            collab_score = 0.5
            recommendations.append("Budget data missing - collaboration potential uncertain")

        scores['collaboration_potential'] = collab_score

        # Calculate overall score
        overall = (
            (mission_score * 0.25) +
            (board_score * 0.25) +
            (funder_score * 0.30) +
            (collab_score * 0.20)
        )

        # Determine rating
        if overall >= 0.70:
            rating = QualityRating.HIGH
            recommendations.append("High value - Strong networking opportunity")
        elif overall >= 0.50:
            rating = QualityRating.MEDIUM
            recommendations.append("Medium value - Moderate networking potential")
        else:
            rating = QualityRating.LOW
            recommendations.append("Low value - Limited strategic benefit")

        return QualityScore(
            overall_score=overall,
            rating=rating,
            component_scores=scores,
            recommendations=recommendations
        )


class DataCompletenessValidator:
    """
    Validate data completeness across all sources.

    Provides detailed completeness metrics for quality assessment.
    """

    def validate_profile_completeness(
        self,
        bmf_data: Optional[Dict[str, Any]],
        form_990: Optional[Dict[str, Any]],
        tool25_data: Optional[Dict[str, Any]],
        tool2_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate overall profile data completeness.

        Returns:
            Dictionary with completeness metrics and recommendations
        """
        results = {
            'sources_present': [],
            'sources_missing': [],
            'overall_completeness': 0.0,
            'field_counts': {},
            'recommendations': []
        }

        # Check which sources are present
        if bmf_data:
            results['sources_present'].append('bmf')
            results['field_counts']['bmf'] = len([v for v in bmf_data.values() if v])
        else:
            results['sources_missing'].append('bmf')
            results['recommendations'].append("CRITICAL: BMF data missing - cannot proceed")

        if form_990:
            results['sources_present'].append('form_990')
            results['field_counts']['form_990'] = len([v for v in form_990.values() if v])
        else:
            results['sources_missing'].append('form_990')
            results['recommendations'].append("HIGH PRIORITY: Form 990 data missing - limits financial analysis")

        if tool25_data:
            results['sources_present'].append('tool_25')
            results['field_counts']['tool_25'] = len([v for v in tool25_data.values() if v])
        else:
            results['sources_missing'].append('tool_25')
            results['recommendations'].append("MEDIUM PRIORITY: Tool 25 data missing - run web scraping")

        if tool2_data:
            results['sources_present'].append('tool_2')
            results['field_counts']['tool_2'] = len([v for v in tool2_data.values() if v])
        else:
            results['sources_missing'].append('tool_2')
            results['recommendations'].append("OPTIONAL: Tool 2 AI analysis not performed")

        # Calculate overall completeness (weighted)
        source_weights = {'bmf': 0.20, 'form_990': 0.35, 'tool_25': 0.25, 'tool_2': 0.20}
        completeness = sum(source_weights[s] for s in results['sources_present'])
        results['overall_completeness'] = completeness

        # Add summary recommendation
        if completeness >= 0.85:
            results['recommendations'].append("Profile data complete - ready for high-quality matching")
        elif completeness >= 0.70:
            results['recommendations'].append("Profile data mostly complete - good quality matching possible")
        elif completeness >= 0.50:
            results['recommendations'].append("Profile data partial - basic matching possible but limited")
        else:
            results['recommendations'].append("Profile data insufficient - gather more data before matching")

        return results

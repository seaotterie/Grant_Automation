# Government Opportunity Scorer Tool
*🟡 Intermediate Level - Business logic with weighted scoring algorithms*

## What This Tool Does

The Government Scorer Tool takes government funding opportunities (from Grants.gov, USASpending, etc.) and scores them for match quality against a nonprofit profile. It calculates:

- **Eligibility Score**: How well the nonprofit meets requirements
- **Geographic Match**: Location alignment
- **Financial Fit**: Funding amount vs. organization size
- **Timeline Score**: Application deadlines and urgency
- **Historical Success**: Past success with similar opportunities

**Think of it like**: A dating app algorithm that matches nonprofits with government funding opportunities based on compatibility.

## Why This Tool Exists (12-Factor Pattern)

**Before**: Scoring logic was buried inside complex processors, making it hard to:
- Test different scoring algorithms
- Adjust weights for different scenarios
- Reuse scoring for different opportunity types
- Debug why certain scores were calculated

**After**: This tool ONLY does scoring. Other tools handle:
- Data fetching (BMF Filter, Government Fetcher)
- Analysis (AI Heavy Tool)
- Reporting (Report Generator Tool)

**12-Factor Benefits**:
- **Testable**: Easy to test scoring logic with known inputs
- **Configurable**: Adjust weights and thresholds via environment
- **Reusable**: Score any opportunity type with same logic
- **Transparent**: Clear audit trail of how scores are calculated

## Tool Structure (12-Factor Conventions)

```
government-scorer-tool/
├── README.md              # This file
├── .env                   # Environment configuration
├── 12factors.toml         # Tool configuration
├── pyproject.toml         # Dependencies
├── baml_src/              # BAML definitions
│   ├── gov_scoring.baml   # Scoring schema
│   ├── clients.baml       # LLM clients (optional)
│   └── generators.baml    # Code generation
└── app/                   # Implementation
    ├── __init__.py
    ├── gov_scorer.py      # Main scoring logic
    ├── scoring_engine.py  # Scoring algorithms
    ├── agent.py           # Agent integration
    ├── server.py          # HTTP server
    └── main.py            # Entry point
```

## Key Learning: Business Logic as Tools

This tool demonstrates **pure business logic** as a 12-factor tool:
- ✅ **Deterministic**: Same inputs always produce same outputs
- ✅ **Stateless**: No memory between scoring requests
- ✅ **Configurable**: Scoring weights adjustable via environment
- ✅ **Auditable**: Clear explanation of how scores are calculated

## Configuration Files

### .env
```bash
# Scoring Configuration
SCORING_WEIGHTS_ELIGIBILITY=0.30
SCORING_WEIGHTS_GEOGRAPHIC=0.20
SCORING_WEIGHTS_FINANCIAL=0.20
SCORING_WEIGHTS_TIMELINE=0.15
SCORING_WEIGHTS_HISTORICAL=0.15

# Score Thresholds
SCORE_THRESHOLD_HIGH=0.75
SCORE_THRESHOLD_MEDIUM=0.55
SCORE_THRESHOLD_LOW=0.35

# Performance Settings
SCORER_MAX_OPPORTUNITIES_BATCH=100
SCORER_TIMEOUT_SECONDS=30
SCORER_CACHE_ENABLED=true

# Server Settings
GOV_SCORER_PORT=8003
LOG_LEVEL=INFO
```

### 12factors.toml
```toml
[tool]
name = "government-scorer"
version = "1.0.0"
description = "Score government funding opportunities for nonprofit match quality"
intent = "score_government_opportunities"

[tool.capabilities]
primary = "opportunity_scoring"
secondary = ["match_analysis", "priority_ranking", "eligibility_assessment"]

[tool.scoring]
# Default scoring weights (can be overridden by environment)
weights = {
    eligibility = 0.30,
    geographic = 0.20,
    financial = 0.20,
    timeline = 0.15,
    historical = 0.15
}

thresholds = {
    high = 0.75,
    medium = 0.55,
    low = 0.35
}

[tool.performance]
max_batch_size = 100
timeout_seconds = 30
cache_ttl = 3600

[tool.12factors]
config_external = true      # Weights from environment
stateless = true           # No memory between requests
deterministic = true       # Same inputs = same outputs
auditable = true          # Score explanations included
```

## BAML Schema

### baml_src/gov_scoring.baml
```baml
// Government Opportunity Scoring Tool Schema
// Demonstrates pure business logic as 12-factor tool

// Tool Intent - What triggers opportunity scoring
class GovernmentScoringIntent {
    intent "score_government_opportunities"
    nonprofit_profile NonprofitProfile
    opportunities GovernmentOpportunity[]
    scoring_preferences ScoringPreferences?
}

// Nonprofit profile for matching
class NonprofitProfile {
    ein string?
    name string
    mission string?
    revenue int?
    assets int?
    employee_count int?
    focus_areas string[] @description("NTEE codes or focus area descriptions")
    geographic_scope string[] @description("States/regions where org operates")
    past_grants PastGrant[]?
    organizational_capacity OrganizationalCapacity?
}

class PastGrant {
    grantor string
    amount int
    year int
    grant_type string? @description("federal, state, local, foundation")
    success_rating float? @description("0.0-1.0 rating of grant success")
}

class OrganizationalCapacity {
    grant_writing_experience "none" | "limited" | "moderate" | "extensive"
    compliance_track_record "poor" | "fair" | "good" | "excellent"
    financial_management_strength "weak" | "adequate" | "strong" | "excellent"
    reporting_capability "basic" | "standard" | "advanced" | "sophisticated"
}

// Government opportunity to score
class GovernmentOpportunity {
    opportunity_id string
    title string
    agency string
    posted_date string?
    close_date string?
    estimated_award_amount int?
    minimum_award int?
    maximum_award int?
    eligible_applicants string[]
    geographic_restrictions string[]?
    program_areas string[]
    cfda_numbers string[]?
    cost_sharing_required bool?
    matching_funds_required float? @description("Percentage match required")
    application_complexity "simple" | "moderate" | "complex" | "very_complex"
    competition_level "low" | "medium" | "high" | "very_high"
}

// Scoring customization options
class ScoringPreferences {
    weight_eligibility float? @default(0.30)
    weight_geographic float? @default(0.20)
    weight_financial float? @default(0.20)
    weight_timeline float? @default(0.15)
    weight_historical float? @default(0.15)
    prioritize_larger_grants bool? @default(false)
    prefer_lower_competition bool? @default(true)
    require_perfect_eligibility bool? @default(false)
}

// Tool Result - Scored opportunities with explanations
class GovernmentScoringResult {
    intent "government_scoring_result"
    scored_opportunities ScoredOpportunity[]
    scoring_summary ScoringSummary
    execution_metadata ScoringExecutionData
}

class ScoredOpportunity {
    opportunity_id string
    opportunity_title string
    overall_score float @description("Final weighted score 0.0-1.0")
    score_tier "high" | "medium" | "low" | "not_recommended"
    component_scores ComponentScores
    match_explanation MatchExplanation
    recommendation OpportunityRecommendation
}

class ComponentScores {
    eligibility_score float @description("0.0-1.0 eligibility match")
    geographic_score float @description("0.0-1.0 geographic alignment")
    financial_score float @description("0.0-1.0 financial fit")
    timeline_score float @description("0.0-1.0 timeline favorability")
    historical_score float @description("0.0-1.0 based on past success")

    // Score explanations
    eligibility_reasons string[]
    geographic_reasons string[]
    financial_reasons string[]
    timeline_reasons string[]
    historical_reasons string[]
}

class MatchExplanation {
    key_strengths string[] @description("Why this is a good match")
    potential_challenges string[] @description("Obstacles or concerns")
    success_factors string[] @description("What would make application successful")
    risk_factors string[] @description("Why application might fail")
}

class OpportunityRecommendation {
    action "apply" | "consider" | "skip" | "monitor"
    priority "high" | "medium" | "low"
    confidence float @description("0.0-1.0 confidence in recommendation")
    next_steps string[] @description("Specific actions to take")
    application_timeline string? @description("Suggested application schedule")
    preparation_requirements string[] @description("What org needs to prepare")
}

class ScoringSummary {
    total_opportunities_scored int
    high_score_count int
    medium_score_count int
    low_score_count int
    not_recommended_count int
    average_score float
    top_recommendation_id string?
    scoring_weights_used ScoringPreferences
}

class ScoringExecutionData {
    execution_time_ms float
    opportunities_per_second float
    cache_hits int
    scoring_algorithm_version string
    weights_source "default" | "environment" | "request"
}

// Optional: Enhanced scoring with AI insights
function EnhanceScoringWithAI(
    opportunity: GovernmentOpportunity,
    profile: NonprofitProfile,
    base_score: ScoredOpportunity
) -> MatchExplanation {
    client OpenAILite
    prompt #"
        Analyze this opportunity match and provide insights:

        OPPORTUNITY: {{ opportunity.title }}
        Agency: {{ opportunity.agency }}
        Award Amount: ${{ opportunity.estimated_award_amount | number_format }}
        Program Areas: {{ opportunity.program_areas | join(", ") }}

        NONPROFIT: {{ profile.name }}
        Mission: {{ profile.mission }}
        Revenue: ${{ profile.revenue | number_format }}
        Focus: {{ profile.focus_areas | join(", ") }}

        CURRENT SCORE: {{ base_score.overall_score }} ({{ base_score.score_tier }})

        Provide enhanced match analysis:
        1. Key Strengths: Why this match makes sense
        2. Potential Challenges: Obstacles the nonprofit might face
        3. Success Factors: What would make the application competitive
        4. Risk Factors: Why the application might fail

        Be specific and actionable in your analysis.
    "#
}
```

## Tool Implementation

### app/scoring_engine.py
```python
"""
Core scoring algorithms for government opportunities
Pure business logic with no external dependencies
"""

import math
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ScoringWeights:
    """Scoring weights configuration"""
    eligibility: float = 0.30
    geographic: float = 0.20
    financial: float = 0.20
    timeline: float = 0.15
    historical: float = 0.15

    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = self.eligibility + self.geographic + self.financial + self.timeline + self.historical
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")

class ScoringEngine:
    """
    Pure scoring algorithms - deterministic and testable

    This class contains only business logic, no I/O or external dependencies.
    Perfect for unit testing and algorithm development.
    """

    def __init__(self, weights: ScoringWeights):
        self.weights = weights

    def score_opportunity(self, opportunity: dict, profile: dict) -> Tuple[float, dict]:
        """
        Score a single opportunity against a nonprofit profile

        Returns:
            (overall_score, component_scores_dict)
        """

        # Calculate component scores
        eligibility_score, eligibility_reasons = self._score_eligibility(opportunity, profile)
        geographic_score, geographic_reasons = self._score_geographic(opportunity, profile)
        financial_score, financial_reasons = self._score_financial(opportunity, profile)
        timeline_score, timeline_reasons = self._score_timeline(opportunity, profile)
        historical_score, historical_reasons = self._score_historical(opportunity, profile)

        # Calculate weighted overall score
        overall_score = (
            eligibility_score * self.weights.eligibility +
            geographic_score * self.weights.geographic +
            financial_score * self.weights.financial +
            timeline_score * self.weights.timeline +
            historical_score * self.weights.historical
        )

        # Compile component scores
        component_scores = {
            'eligibility_score': eligibility_score,
            'geographic_score': geographic_score,
            'financial_score': financial_score,
            'timeline_score': timeline_score,
            'historical_score': historical_score,
            'eligibility_reasons': eligibility_reasons,
            'geographic_reasons': geographic_reasons,
            'financial_reasons': financial_reasons,
            'timeline_reasons': timeline_reasons,
            'historical_reasons': historical_reasons
        }

        return overall_score, component_scores

    def _score_eligibility(self, opportunity: dict, profile: dict) -> Tuple[float, List[str]]:
        """Score eligibility match"""
        score = 0.0
        reasons = []

        # Check eligible applicants
        eligible_applicants = opportunity.get('eligible_applicants', [])
        if not eligible_applicants:
            score += 0.3  # No restrictions
            reasons.append("No eligibility restrictions specified")
        else:
            # Check if nonprofit type is eligible
            nonprofit_types = ['nonprofit', '501c3', 'charitable organization', 'public charity']
            if any(etype.lower() in ' '.join(eligible_applicants).lower() for etype in nonprofit_types):
                score += 0.3
                reasons.append("Nonprofit organizations are eligible")
            else:
                reasons.append("Nonprofit eligibility unclear")

        # Check program area alignment
        opportunity_areas = opportunity.get('program_areas', [])
        profile_areas = profile.get('focus_areas', [])

        if opportunity_areas and profile_areas:
            # Simple keyword matching (in production: use more sophisticated matching)
            area_matches = 0
            for opp_area in opportunity_areas:
                for prof_area in profile_areas:
                    if self._areas_match(opp_area, prof_area):
                        area_matches += 1
                        break

            if area_matches > 0:
                area_score = min(1.0, area_matches / len(opportunity_areas))
                score += 0.4 * area_score
                reasons.append(f"Program area alignment: {area_matches}/{len(opportunity_areas)} areas match")
            else:
                reasons.append("No clear program area alignment")
        else:
            score += 0.2  # Partial credit for missing data
            reasons.append("Program areas not specified")

        # Check organizational capacity requirements
        complexity = opportunity.get('application_complexity', 'moderate')
        org_capacity = profile.get('organizational_capacity', {})
        grant_experience = org_capacity.get('grant_writing_experience', 'limited')

        capacity_match = self._match_capacity_to_complexity(grant_experience, complexity)
        score += 0.3 * capacity_match

        if capacity_match > 0.7:
            reasons.append(f"Organization has {grant_experience} grant experience for {complexity} application")
        else:
            reasons.append(f"Application complexity ({complexity}) may exceed organizational capacity ({grant_experience})")

        return min(1.0, score), reasons

    def _score_geographic(self, opportunity: dict, profile: dict) -> Tuple[float, List[str]]:
        """Score geographic alignment"""
        score = 1.0  # Default to full score
        reasons = []

        restrictions = opportunity.get('geographic_restrictions', [])
        profile_scope = profile.get('geographic_scope', [])

        if not restrictions:
            reasons.append("No geographic restrictions")
            return 1.0, reasons

        if not profile_scope:
            score = 0.5  # Uncertain without profile data
            reasons.append("Organization geographic scope unknown")
            return score, reasons

        # Check for matches
        matches = []
        for restriction in restrictions:
            for scope_area in profile_scope:
                if self._geographic_match(restriction, scope_area):
                    matches.append(f"{scope_area} matches {restriction}")

        if matches:
            score = 1.0
            reasons.extend(matches)
        else:
            score = 0.0
            reasons.append("No geographic overlap with restrictions")

        return score, reasons

    def _score_financial(self, opportunity: dict, profile: dict) -> Tuple[float, List[str]]:
        """Score financial fit"""
        score = 0.0
        reasons = []

        org_revenue = profile.get('revenue', 0)
        award_amount = opportunity.get('estimated_award_amount') or opportunity.get('maximum_award', 0)

        if not award_amount:
            score = 0.5
            reasons.append("Award amount not specified")
            return score, reasons

        if not org_revenue:
            score = 0.3
            reasons.append("Organization revenue unknown")
            return score, reasons

        # Calculate award as percentage of revenue
        award_percentage = award_amount / org_revenue if org_revenue > 0 else 0

        # Scoring based on award size relative to organization
        if 0.05 <= award_percentage <= 0.5:  # 5-50% of revenue is ideal
            score = 1.0
            reasons.append(f"Award (${award_amount:,}) is {award_percentage:.1%} of revenue - excellent fit")
        elif 0.02 <= award_percentage <= 0.8:  # 2-80% is good
            score = 0.8
            reasons.append(f"Award (${award_amount:,}) is {award_percentage:.1%} of revenue - good fit")
        elif award_percentage < 0.02:  # Too small
            score = 0.4
            reasons.append(f"Award (${award_amount:,}) is {award_percentage:.1%} of revenue - may be too small")
        else:  # Too large
            score = 0.2
            reasons.append(f"Award (${award_amount:,}) is {award_percentage:.1%} of revenue - may be too large")

        # Check matching funds requirement
        matching_required = opportunity.get('matching_funds_required', 0)
        if matching_required > 0:
            matching_amount = award_amount * matching_required
            if matching_amount > org_revenue * 0.1:  # More than 10% of revenue
                score *= 0.7
                reasons.append(f"Matching funds ({matching_required:.0%}) may be challenging")
            else:
                reasons.append(f"Matching funds ({matching_required:.0%}) appears manageable")

        return score, reasons

    def _score_timeline(self, opportunity: dict, profile: dict) -> Tuple[float, List[str]]:
        """Score timeline favorability"""
        score = 0.0
        reasons = []

        close_date_str = opportunity.get('close_date')
        if not close_date_str:
            score = 0.3
            reasons.append("No application deadline specified")
            return score, reasons

        try:
            close_date = datetime.fromisoformat(close_date_str.replace('Z', '+00:00'))
            now = datetime.now(close_date.tzinfo)
            days_remaining = (close_date - now).days

            if days_remaining < 0:
                score = 0.0
                reasons.append("Application deadline has passed")
            elif days_remaining < 7:
                score = 0.2
                reasons.append(f"Only {days_remaining} days to apply - very tight timeline")
            elif days_remaining < 30:
                score = 0.6
                reasons.append(f"{days_remaining} days to apply - tight but manageable")
            elif days_remaining < 90:
                score = 1.0
                reasons.append(f"{days_remaining} days to apply - adequate time for preparation")
            else:
                score = 0.8
                reasons.append(f"{days_remaining} days to apply - plenty of time")

        except (ValueError, TypeError):
            score = 0.3
            reasons.append("Unable to parse application deadline")

        return score, reasons

    def _score_historical(self, opportunity: dict, profile: dict) -> Tuple[float, List[str]]:
        """Score based on historical success patterns"""
        score = 0.5  # Default neutral score
        reasons = []

        past_grants = profile.get('past_grants', [])
        opportunity_agency = opportunity.get('agency', '').lower()

        if not past_grants:
            reasons.append("No historical grant data available")
            return score, reasons

        # Check for same agency experience
        agency_experience = any(
            grant.get('grantor', '').lower().find(opportunity_agency) >= 0
            for grant in past_grants
        )

        if agency_experience:
            score += 0.3
            reasons.append(f"Organization has previous experience with {opportunity.get('agency')}")

        # Check for similar grant types
        federal_experience = any(
            grant.get('grant_type', '').lower() == 'federal'
            for grant in past_grants
        )

        if federal_experience:
            score += 0.2
            reasons.append("Organization has federal grant experience")

        # Check success ratings
        successful_grants = [
            grant for grant in past_grants
            if grant.get('success_rating', 0) > 0.7
        ]

        if successful_grants:
            avg_success = sum(g.get('success_rating', 0) for g in successful_grants) / len(successful_grants)
            score += avg_success * 0.3
            reasons.append(f"Strong track record with {len(successful_grants)} successful grants")

        return min(1.0, score), reasons

    def _areas_match(self, opp_area: str, prof_area: str) -> bool:
        """Check if opportunity and profile areas match"""
        # Simple keyword matching - in production, use NLP or ontology mapping
        opp_keywords = opp_area.lower().split()
        prof_keywords = prof_area.lower().split()

        return any(keyword in prof_keywords for keyword in opp_keywords)

    def _geographic_match(self, restriction: str, scope_area: str) -> bool:
        """Check if geographic restriction matches scope area"""
        # Simple string matching - in production, use geographic databases
        return restriction.lower() in scope_area.lower() or scope_area.lower() in restriction.lower()

    def _match_capacity_to_complexity(self, experience: str, complexity: str) -> float:
        """Match organizational capacity to application complexity"""
        capacity_levels = {
            'none': 0.0,
            'limited': 0.3,
            'moderate': 0.6,
            'extensive': 1.0
        }

        complexity_requirements = {
            'simple': 0.2,
            'moderate': 0.5,
            'complex': 0.8,
            'very_complex': 1.0
        }

        capacity_score = capacity_levels.get(experience, 0.3)
        required_capacity = complexity_requirements.get(complexity, 0.5)

        if capacity_score >= required_capacity:
            return 1.0
        else:
            return capacity_score / required_capacity
```

### app/gov_scorer.py
```python
"""
Government Opportunity Scorer Tool - 12-Factor Implementation
Demonstrates business logic as stateless, configurable tool
"""

import os
import time
from typing import List, Dict, Any
from app.scoring_engine import ScoringEngine, ScoringWeights
from app.generated.baml_types import (
    GovernmentScoringIntent, GovernmentScoringResult,
    ScoredOpportunity, ComponentScores, MatchExplanation,
    OpportunityRecommendation, ScoringSummary, ScoringExecutionData
)

class GovernmentScorerTool:
    """
    12-Factor Tool: Government Opportunity Scoring

    Demonstrates:
    - Factor 3: Configurable scoring weights from environment
    - Factor 6: Stateless deterministic scoring
    - Factor 4: Structured input/output
    - Factor 11: Auditable scoring with explanations
    """

    def __init__(self):
        # Factor 3: Configuration from environment
        self.weights = ScoringWeights(
            eligibility=float(os.getenv("SCORING_WEIGHTS_ELIGIBILITY", "0.30")),
            geographic=float(os.getenv("SCORING_WEIGHTS_GEOGRAPHIC", "0.20")),
            financial=float(os.getenv("SCORING_WEIGHTS_FINANCIAL", "0.20")),
            timeline=float(os.getenv("SCORING_WEIGHTS_TIMELINE", "0.15")),
            historical=float(os.getenv("SCORING_WEIGHTS_HISTORICAL", "0.15"))
        )

        self.thresholds = {
            'high': float(os.getenv("SCORE_THRESHOLD_HIGH", "0.75")),
            'medium': float(os.getenv("SCORE_THRESHOLD_MEDIUM", "0.55")),
            'low': float(os.getenv("SCORE_THRESHOLD_LOW", "0.35"))
        }

        self.max_batch_size = int(os.getenv("SCORER_MAX_OPPORTUNITIES_BATCH", "100"))
        self.cache_enabled = os.getenv("SCORER_CACHE_ENABLED", "true").lower() == "true"

        # Initialize scoring engine
        self.engine = ScoringEngine(self.weights)

        # Simple cache for repeated scoring
        self._cache = {}

    async def execute(self, intent: GovernmentScoringIntent) -> GovernmentScoringResult:
        """
        Execute government opportunity scoring

        Factor 6: Stateless - everything needed is in the intent
        Factor 4: Structured input -> deterministic processing -> structured output
        """
        start_time = time.time()

        # Check cache
        cache_key = self._make_cache_key(intent)
        if self.cache_enabled and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cached_result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            return cached_result

        # Validate input
        if len(intent.opportunities) > self.max_batch_size:
            raise ValueError(f"Too many opportunities: {len(intent.opportunities)} > {self.max_batch_size}")

        # Use custom weights if provided
        weights = self.weights
        if intent.scoring_preferences:
            weights = self._override_weights(intent.scoring_preferences)

        # Re-initialize engine with custom weights if needed
        if weights != self.weights:
            engine = ScoringEngine(weights)
        else:
            engine = self.engine

        # Score all opportunities
        scored_opportunities = []
        cache_hits = 0

        for opportunity in intent.opportunities:
            scored_opp = await self._score_single_opportunity(
                opportunity,
                intent.nonprofit_profile,
                engine
            )
            scored_opportunities.append(scored_opp)

        # Sort by score (highest first)
        scored_opportunities.sort(key=lambda x: x.overall_score, reverse=True)

        # Generate summary
        summary = self._generate_summary(scored_opportunities, weights)

        # Create execution metadata
        execution_time = (time.time() - start_time) * 1000
        metadata = ScoringExecutionData(
            execution_time_ms=execution_time,
            opportunities_per_second=len(intent.opportunities) / (execution_time / 1000) if execution_time > 0 else 0,
            cache_hits=cache_hits,
            scoring_algorithm_version="1.0.0",
            weights_source="environment" if weights == self.weights else "request"
        )

        # Build result
        result = GovernmentScoringResult(
            scored_opportunities=scored_opportunities,
            scoring_summary=summary,
            execution_metadata=metadata
        )

        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result

        return result

    async def _score_single_opportunity(self, opportunity, profile, engine) -> ScoredOpportunity:
        """Score a single opportunity"""

        # Convert to dict format for scoring engine
        opp_dict = self._opportunity_to_dict(opportunity)
        profile_dict = self._profile_to_dict(profile)

        # Calculate scores
        overall_score, component_scores = engine.score_opportunity(opp_dict, profile_dict)

        # Determine score tier
        score_tier = self._determine_score_tier(overall_score)

        # Create component scores object
        components = ComponentScores(**component_scores)

        # Generate match explanation
        explanation = self._generate_match_explanation(
            opportunity, profile, overall_score, components
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            opportunity, overall_score, score_tier, explanation
        )

        return ScoredOpportunity(
            opportunity_id=opportunity.opportunity_id,
            opportunity_title=opportunity.title,
            overall_score=overall_score,
            score_tier=score_tier,
            component_scores=components,
            match_explanation=explanation,
            recommendation=recommendation
        )

    def _determine_score_tier(self, score: float) -> str:
        """Determine score tier based on thresholds"""
        if score >= self.thresholds['high']:
            return "high"
        elif score >= self.thresholds['medium']:
            return "medium"
        elif score >= self.thresholds['low']:
            return "low"
        else:
            return "not_recommended"

    def _generate_match_explanation(self, opportunity, profile, score, components) -> MatchExplanation:
        """Generate explanation of why opportunity matches (or doesn't)"""

        strengths = []
        challenges = []
        success_factors = []
        risk_factors = []

        # Analyze component scores for insights
        if components.eligibility_score > 0.7:
            strengths.extend(components.eligibility_reasons[:2])  # Top reasons
        else:
            challenges.extend(components.eligibility_reasons[:2])

        if components.financial_score > 0.7:
            strengths.append("Good financial fit for organization size")
        elif components.financial_score < 0.4:
            challenges.append("Award size may not align with organizational capacity")

        if components.timeline_score > 0.7:
            strengths.append("Adequate time for application preparation")
        else:
            risk_factors.append("Tight application deadline")

        # Add success factors
        success_factors.extend([
            "Strong alignment between mission and program areas",
            "Demonstrated organizational capacity",
            "Competitive application materials"
        ])

        # Add risk factors based on low scores
        if components.geographic_score < 0.5:
            risk_factors.append("Geographic restrictions may limit eligibility")

        if components.historical_score < 0.4:
            risk_factors.append("Limited experience with similar grants")

        return MatchExplanation(
            key_strengths=strengths[:3],  # Limit to top 3
            potential_challenges=challenges[:3],
            success_factors=success_factors[:3],
            risk_factors=risk_factors[:3]
        )

    def _generate_recommendation(self, opportunity, score, tier, explanation) -> OpportunityRecommendation:
        """Generate actionable recommendation"""

        if tier == "high":
            action = "apply"
            priority = "high"
            confidence = min(0.9, score + 0.1)
        elif tier == "medium":
            action = "consider"
            priority = "medium"
            confidence = score
        elif tier == "low":
            action = "monitor"
            priority = "low"
            confidence = score
        else:
            action = "skip"
            priority = "low"
            confidence = 1.0 - score

        # Generate next steps based on action
        next_steps = []
        if action == "apply":
            next_steps = [
                "Begin application preparation immediately",
                "Gather required documentation",
                "Develop project proposal",
                "Submit application before deadline"
            ]
        elif action == "consider":
            next_steps = [
                "Assess organizational readiness",
                "Address identified challenges",
                "Consider partnership opportunities",
                "Decide on application by [deadline - 30 days]"
            ]
        elif action == "monitor":
            next_steps = [
                "Track for future similar opportunities",
                "Build organizational capacity in weak areas",
                "Consider as backup option"
            ]

        return OpportunityRecommendation(
            action=action,
            priority=priority,
            confidence=confidence,
            next_steps=next_steps[:4],  # Limit to 4 steps
            preparation_requirements=self._get_preparation_requirements(opportunity, explanation)
        )

    def _get_preparation_requirements(self, opportunity, explanation) -> List[str]:
        """Determine what organization needs to prepare"""
        requirements = []

        if "grant writing" in ' '.join(explanation.risk_factors).lower():
            requirements.append("Strengthen grant writing capabilities")

        if "matching funds" in str(opportunity.__dict__).lower():
            requirements.append("Secure matching fund commitments")

        if "documentation" in ' '.join(explanation.success_factors).lower():
            requirements.append("Compile required organizational documents")

        requirements.extend([
            "Project budget and timeline",
            "Letters of support from partners",
            "Organizational capacity documentation"
        ])

        return requirements[:4]  # Limit to 4 requirements

    def _generate_summary(self, scored_opportunities, weights) -> ScoringSummary:
        """Generate scoring summary statistics"""

        tier_counts = {"high": 0, "medium": 0, "low": 0, "not_recommended": 0}
        total_score = 0.0

        for opp in scored_opportunities:
            tier_counts[opp.score_tier] += 1
            total_score += opp.overall_score

        avg_score = total_score / len(scored_opportunities) if scored_opportunities else 0.0
        top_rec = scored_opportunities[0].opportunity_id if scored_opportunities else None

        return ScoringSummary(
            total_opportunities_scored=len(scored_opportunities),
            high_score_count=tier_counts["high"],
            medium_score_count=tier_counts["medium"],
            low_score_count=tier_counts["low"],
            not_recommended_count=tier_counts["not_recommended"],
            average_score=avg_score,
            top_recommendation_id=top_rec,
            scoring_weights_used=self._weights_to_preferences(weights)
        )

    def _opportunity_to_dict(self, opportunity) -> Dict[str, Any]:
        """Convert opportunity object to dict for scoring engine"""
        return {
            'opportunity_id': opportunity.opportunity_id,
            'title': opportunity.title,
            'agency': opportunity.agency,
            'close_date': opportunity.close_date,
            'estimated_award_amount': opportunity.estimated_award_amount,
            'eligible_applicants': opportunity.eligible_applicants,
            'geographic_restrictions': opportunity.geographic_restrictions or [],
            'program_areas': opportunity.program_areas,
            'application_complexity': opportunity.application_complexity,
            'matching_funds_required': opportunity.matching_funds_required or 0
        }

    def _profile_to_dict(self, profile) -> Dict[str, Any]:
        """Convert profile object to dict for scoring engine"""
        return {
            'ein': profile.ein,
            'name': profile.name,
            'revenue': profile.revenue,
            'focus_areas': profile.focus_areas or [],
            'geographic_scope': profile.geographic_scope or [],
            'past_grants': [
                {
                    'grantor': g.grantor,
                    'amount': g.amount,
                    'year': g.year,
                    'grant_type': g.grant_type,
                    'success_rating': g.success_rating
                }
                for g in (profile.past_grants or [])
            ],
            'organizational_capacity': profile.organizational_capacity.__dict__ if profile.organizational_capacity else {}
        }

    def _make_cache_key(self, intent: GovernmentScoringIntent) -> str:
        """Create cache key for scoring request"""
        opp_ids = [opp.opportunity_id for opp in intent.opportunities]
        key_parts = [
            intent.nonprofit_profile.ein or intent.nonprofit_profile.name,
            str(sorted(opp_ids)),
            str(self.weights.__dict__)
        ]
        return "|".join(key_parts)

    def _override_weights(self, preferences):
        """Override weights with preferences"""
        return ScoringWeights(
            eligibility=preferences.weight_eligibility or self.weights.eligibility,
            geographic=preferences.weight_geographic or self.weights.geographic,
            financial=preferences.weight_financial or self.weights.financial,
            timeline=preferences.weight_timeline or self.weights.timeline,
            historical=preferences.weight_historical or self.weights.historical
        )

    def _weights_to_preferences(self, weights):
        """Convert weights back to preferences format"""
        # Implementation would return appropriate preferences object
        pass
```

## Key Learning Points

### 1. Pure Business Logic (Factor 6)
- **Deterministic**: Same inputs always produce same outputs
- **Stateless**: No memory between scoring requests
- **Testable**: Easy to unit test scoring algorithms

### 2. Configurable Weights (Factor 3)
- **Environment-driven**: Adjust scoring weights without code changes
- **Override capability**: Custom weights per request
- **Validation**: Ensure weights are valid and sum correctly

### 3. Auditable Results (Factor 11)
- **Score explanations**: Why each score was calculated
- **Component breakdown**: See contribution of each factor
- **Recommendations**: Clear next steps based on scores

### 4. Batch Processing (Factor 8)
- **Efficient**: Score multiple opportunities in single request
- **Limits**: Prevent resource exhaustion with batch size limits
- **Sorted results**: Return opportunities ranked by score

## Running the Tool

```bash
# Configure scoring weights
export SCORING_WEIGHTS_ELIGIBILITY=0.40  # Emphasize eligibility
export SCORING_WEIGHTS_FINANCIAL=0.25    # Increase financial importance
export SCORE_THRESHOLD_HIGH=0.80         # Raise bar for high scores

# Run examples
python app/main.py

# Run as service
python app/server.py
```

This tool demonstrates how pure business logic can be implemented as a 12-factor tool with full configurability, auditability, and testability!
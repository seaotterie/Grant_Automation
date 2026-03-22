#!/usr/bin/env python3
"""
Profile Extras Router
Additional profile routes extracted from main.py during Phase 9 monolith decomposition.
Includes web intelligence, verified intelligence, funnel metrics, scoring rationale, and leads.
"""

import sqlite3
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException

from src.profiles.unified_service import get_unified_profile_service
from src.profiles.metrics_tracker import get_metrics_tracker
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profiles-extras"])

# Module-level service instances
profile_service = get_unified_profile_service()
metrics_tracker = get_metrics_tracker()


# =====================================================================================
# Helper functions
# =====================================================================================

async def _save_web_intelligence_data(ein: str, url: str, intelligence_data, organization_name: str = "") -> bool:
    """
    Save web intelligence data directly to database.
    Clean approach - no EIN extraction from URL needed.
    """
    try:
        # Extract intelligence information
        programs = intelligence_data.program_data if hasattr(intelligence_data, 'program_data') else []
        leadership = intelligence_data.leadership_data if hasattr(intelligence_data, 'leadership_data') else []
        contact_data = intelligence_data.contact_data if hasattr(intelligence_data, 'contact_data') else []
        mission_data = intelligence_data.mission_data if hasattr(intelligence_data, 'mission_data') else []
        intelligence_score = intelligence_data.intelligence_score if hasattr(intelligence_data, 'intelligence_score') else 0
        pages_scraped = len(intelligence_data.pages_scraped) if hasattr(intelligence_data, 'pages_scraped') else 0
        total_content_length = intelligence_data.total_content_length if hasattr(intelligence_data, 'total_content_length') else 0

        # Save to database
        with sqlite3.connect("data/catalynx.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO web_intelligence (
                    ein, url, scrape_date, intelligence_quality_score,
                    content_richness_score, pages_scraped, total_content_length,
                    leadership_data, leadership_count, program_data, program_count,
                    contact_data, mission_statements, mission_count,
                    processing_duration_ms, website_structure_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ein,
                url,
                datetime.now().isoformat(),
                intelligence_score,
                min(intelligence_score / 100.0 * 0.9, 1.0),
                pages_scraped,
                total_content_length,
                json.dumps(leadership),
                len(leadership),
                json.dumps(programs),
                len(programs),
                json.dumps(contact_data),
                json.dumps(mission_data),
                len(mission_data),
                int((intelligence_data.processing_time if hasattr(intelligence_data, 'processing_time') else 1.0) * 1000),
                "Good" if intelligence_score > 50 else "Fair"
            ))
            conn.commit()

        logger.info(f"Successfully saved web intelligence for EIN {ein}: {len(programs)} programs, {len(leadership)} leadership")
        return True

    except Exception as e:
        logger.error(f"Failed to save web intelligence data for EIN {ein}: {e}")
        return False


def _score_scraped_content(content: str, organization_data: Dict) -> float:
    """
    Score scraped content for relevance to the organization.
    Returns score between 0.0 and 1.0.
    """
    score = 0.0
    content_lower = content.lower()
    org_name_lower = organization_data.get('organization_name', '').lower()

    if org_name_lower and org_name_lower in content_lower:
        score += 0.4

    nonprofit_indicators = ['nonprofit', 'non-profit', 'charity', 'foundation', 'mission', 'donate', 'volunteer']
    indicator_count = sum(1 for indicator in nonprofit_indicators if indicator in content_lower)
    score += min(indicator_count * 0.1, 0.3)

    city = organization_data.get('city', '').lower()
    state = organization_data.get('state', '').lower()
    if city and city in content_lower:
        score += 0.2
    if state and state in content_lower:
        score += 0.1

    return min(score, 1.0)


def _extract_organization_info_simple(content: str, extracted_info: Dict):
    """Simple extraction of organization information from content."""
    lines = [line.strip() for line in content.split('\n') if line.strip()]

    mission_keywords = ["mission", "purpose", "vision", "goal", "about"]
    contact_keywords = ["contact", "email", "phone", "address"]
    program_keywords = ["program", "service", "initiative", "project"]
    leadership_keywords = ["board", "director", "ceo", "president", "staff"]

    for line in lines:
        line_lower = line.lower()

        if len(line) < 20 or len(line) > 300:
            continue

        if any(keyword in line_lower for keyword in mission_keywords):
            if line not in extracted_info["mission_statements"]:
                extracted_info["mission_statements"].append(line)

        elif any(keyword in line_lower for keyword in contact_keywords):
            if "@" in line or "phone" in line_lower:
                if line not in extracted_info["contact_info"]:
                    extracted_info["contact_info"].append(line)

        elif any(keyword in line_lower for keyword in program_keywords):
            if line not in extracted_info["programs"]:
                extracted_info["programs"].append(line)

        elif any(keyword in line_lower for keyword in leadership_keywords):
            if line not in extracted_info["leadership"]:
                extracted_info["leadership"].append(line)

    for key in extracted_info:
        extracted_info[key] = extracted_info[key][:5]


def _validate_cached_intelligence_quality(stored_intelligence: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the quality of cached intelligence data to prevent serving fake data."""
    validation_result = {
        'is_high_quality': True,
        'quality_score': 1.0,
        'issues': []
    }

    extracted_info = stored_intelligence.get("extracted_info", {})

    # Check leadership data for fake indicators
    leadership_data = extracted_info.get("leadership", [])
    if leadership_data:
        fake_patterns = [
            'board of', 'serving as', 'was appointed', 'executive vice',
            'been the', 'serves as', 'on the', 'at colliers', 'ramps to'
        ]

        fake_count = 0
        for leader_info in leadership_data:
            if isinstance(leader_info, str):
                leader_text = leader_info.lower()
                if any(pattern in leader_text for pattern in fake_patterns):
                    fake_count += 1
            elif isinstance(leader_info, dict):
                name = leader_info.get('name', '').lower()
                if any(pattern in name for pattern in fake_patterns):
                    fake_count += 1

        fake_percentage = fake_count / len(leadership_data) if leadership_data else 0
        if fake_percentage > 0.5:
            validation_result['is_high_quality'] = False
            validation_result['quality_score'] *= 0.3
            validation_result['issues'].append(f"High fake leadership data: {fake_percentage:.1%}")

    # Check for generic contact info
    contact_info = extracted_info.get("contact_info", [])
    if contact_info:
        generic_patterns = ['email', 'phone', 'address', 'contact']
        generic_count = sum(1 for item in contact_info if isinstance(item, str) and item.lower() in generic_patterns)
        if generic_count == len(contact_info):
            validation_result['quality_score'] *= 0.7
            validation_result['issues'].append("All contact info is generic labels")

    # Check data freshness
    scrape_date = stored_intelligence.get("scrape_date", "")
    if scrape_date:
        from datetime import timedelta
        try:
            cached_date = datetime.fromisoformat(scrape_date.replace('Z', '+00:00'))
            age_days = (datetime.now() - cached_date).days
            if age_days > 7:
                validation_result['quality_score'] *= 0.9
                validation_result['issues'].append(f"Data is {age_days} days old")
        except Exception:
            pass

    if validation_result['quality_score'] < 0.6:
        validation_result['is_high_quality'] = False

    return validation_result


async def _get_stored_intelligence_data(ein: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored intelligence data from the database by EIN."""
    try:
        database_path = "data/catalynx.db"
        if not Path(database_path).exists():
            logger.warning(f"Intelligence database not found at {database_path}")
            return None

        with sqlite3.connect(database_path) as conn:
            ein_with_dash = f"{ein[:2]}-{ein[2:]}" if len(ein) >= 9 and '-' not in ein else ein
            cursor = conn.execute("""
                SELECT wi.leadership_data, wi.program_data, wi.contact_data,
                       wi.mission_statements, wi.intelligence_quality_score,
                       wi.leadership_count, wi.program_count, wi.mission_count,
                       wi.url, wi.updated_at
                FROM web_intelligence wi
                WHERE wi.ein = ? OR wi.ein = ?
                ORDER BY wi.updated_at DESC
                LIMIT 1
            """, (ein, ein_with_dash))

            row = cursor.fetchone()
            if not row:
                logger.info(f"No stored intelligence found for EIN {ein} in web_intelligence table")
                return None

            leadership_data, program_data, contact_data, mission_data, quality_score, leadership_count, program_count, mission_count, url, last_updated = row

            extracted_info = {}

            try:
                extracted_info["leadership"] = json.loads(leadership_data) if leadership_data else []
                extracted_info["programs"] = json.loads(program_data) if program_data else []
                extracted_info["mission_statements"] = json.loads(mission_data) if mission_data else []
                extracted_info["contact_info"] = json.loads(contact_data) if contact_data else []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data for EIN {ein}: {e}")
                return None

            if not any([extracted_info["leadership"], extracted_info["programs"], extracted_info["mission_statements"]]):
                logger.info(f"No real extracted info found for EIN {ein} - returning None")
                return None

            intelligence_data = {
                "successful_scrapes": [{"url": url, "status": "success"}] if url else [],
                "extracted_info": extracted_info,
                "intelligence_quality_score": quality_score,
                "last_updated": last_updated,
                "data_source": "database"
            }

            logger.info(f"Retrieved stored intelligence for EIN {ein} with {len(intelligence_data['extracted_info']['programs'])} programs, {len(intelligence_data['extracted_info']['leadership'])} leadership entries")
            return intelligence_data

    except Exception as e:
        logger.error(f"Error retrieving stored intelligence for EIN {ein}: {e}")
        return None


async def _generate_scoring_rationale(profile, opportunity):
    """Generate comprehensive scoring rationale with pros/cons analysis."""
    score = opportunity.compatibility_score or 0.0

    scoring_dimensions = {
        "eligibility": _analyze_eligibility_fit(profile, opportunity),
        "geographic": _analyze_geographic_fit(profile, opportunity),
        "mission_alignment": _analyze_mission_alignment(profile, opportunity),
        "financial_fit": _analyze_financial_fit(profile, opportunity),
        "timing": _analyze_timing_factors(opportunity)
    }

    pros = []
    cons = []
    improvement_recommendations = []
    risk_factors = []

    for dimension, analysis in scoring_dimensions.items():
        if analysis["score"] >= 0.7:
            pros.extend(analysis["positive_factors"])
        elif analysis["score"] <= 0.4:
            cons.extend(analysis["negative_factors"])
            improvement_recommendations.extend(analysis["recommendations"])
        risk_factors.extend(analysis.get("risks", []))

    if score >= 0.8:
        overall_assessment = "Excellent match with strong alignment across multiple dimensions"
        recommendation = "High priority - proceed with application preparation"
    elif score >= 0.65:
        overall_assessment = "Good match with some areas for optimization"
        recommendation = "Medium priority - address identified gaps before proceeding"
    elif score >= 0.45:
        overall_assessment = "Moderate match requiring significant preparation"
        recommendation = "Low priority - substantial work needed to improve fit"
    else:
        overall_assessment = "Poor match with fundamental misalignment"
        recommendation = "Not recommended - consider alternative opportunities"

    return {
        "overall_assessment": overall_assessment,
        "recommendation": recommendation,
        "score_breakdown": scoring_dimensions,
        "strengths": pros[:5],
        "challenges": cons[:5],
        "improvement_recommendations": improvement_recommendations[:3],
        "risk_factors": risk_factors[:3],
        "strategic_insights": _generate_strategic_insights(profile, opportunity, score),
        "next_steps": _generate_next_steps(score, scoring_dimensions)
    }


def _analyze_eligibility_fit(profile, opportunity):
    """Analyze eligibility alignment between profile and opportunity."""
    match_factors = opportunity.match_factors or {}
    external_data = opportunity.external_data or {}

    positive_factors = []
    negative_factors = []
    recommendations = []
    risks = []

    profile_focus = getattr(profile, 'focus_areas', '') if hasattr(profile, 'focus_areas') else ''
    ntee_code = external_data.get('ntee_code', '')

    if ntee_code:
        ntee_focus_map = {
            'A': 'arts', 'B': 'education', 'C': 'environment', 'D': 'animals',
            'E': 'health', 'F': 'mental health', 'G': 'medical', 'H': 'medical research',
            'I': 'crime', 'J': 'employment', 'K': 'food', 'L': 'housing',
            'M': 'safety', 'N': 'recreation', 'O': 'youth', 'P': 'human services',
            'Q': 'international', 'R': 'civil rights', 'S': 'community', 'T': 'philanthropy'
        }
        primary_category = ntee_code[0] if ntee_code else ''
        mapped_focus = ntee_focus_map.get(primary_category, '')

        if mapped_focus and mapped_focus in profile_focus.lower():
            positive_factors.append(f"Strong NTEE alignment: {ntee_code} matches profile focus on {mapped_focus}")
        else:
            negative_factors.append(f"NTEE mismatch: {ntee_code} may not align with profile focus areas")

    source_type = match_factors.get('source_type', 'Unknown')
    if source_type == 'Nonprofit' and 'nonprofit' in profile_focus.lower():
        positive_factors.append("Organization type aligns with nonprofit focus")
    elif source_type in ['Foundation', 'Government']:
        positive_factors.append(f"{source_type} source provides credible funding opportunity")

    score = max(0.1, min(1.0, len(positive_factors) * 0.3 - len(negative_factors) * 0.2 + 0.5))

    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": risks
    }


def _analyze_geographic_fit(profile, opportunity):
    """Analyze geographic alignment."""
    match_factors = opportunity.match_factors or {}
    external_data = opportunity.external_data or {}

    positive_factors = []
    negative_factors = []
    recommendations = []

    org_state = match_factors.get('state', external_data.get('state', ''))
    profile_scope = getattr(profile, 'geographic_scope', '') if hasattr(profile, 'geographic_scope') else ''

    if org_state:
        if org_state in profile_scope or 'national' in profile_scope.lower():
            positive_factors.append(f"Geographic match: Organization in {org_state} aligns with profile scope")
        else:
            negative_factors.append(f"Geographic mismatch: {org_state} location may not align with target areas")
            recommendations.append("Consider if geographic expansion is strategic")

    score = 0.7 if positive_factors else 0.3

    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": []
    }


def _analyze_mission_alignment(profile, opportunity):
    """Analyze mission and program alignment."""
    positive_factors = []
    negative_factors = []

    org_name = opportunity.organization_name.lower()
    description = (opportunity.description or '').lower()
    profile_focus = getattr(profile, 'focus_areas', '').lower() if hasattr(profile, 'focus_areas') else ''

    focus_keywords = profile_focus.split(',') if profile_focus else []
    mission_matches = 0

    for keyword in focus_keywords:
        keyword = keyword.strip()
        if keyword and (keyword in org_name or keyword in description):
            positive_factors.append(f"Mission alignment: '{keyword}' appears in organization context")
            mission_matches += 1

    if mission_matches == 0:
        negative_factors.append("Limited mission alignment detected in available information")

    score = min(1.0, 0.4 + mission_matches * 0.2)

    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": [],
        "risks": []
    }


def _analyze_financial_fit(profile, opportunity):
    """Analyze financial capacity and funding alignment."""
    positive_factors = []
    negative_factors = []
    recommendations = []

    external_data = opportunity.external_data or {}
    description = opportunity.description or ''

    revenue_match = re.search(r'\$?([\d,]+(?:\.\d+)?)', description)
    if revenue_match:
        try:
            revenue_str = revenue_match.group(1).replace(',', '')
            revenue = float(revenue_str)

            if revenue > 1000000:
                positive_factors.append(f"Strong financial capacity: ${revenue:,.0f} annual revenue")
            elif revenue > 100000:
                positive_factors.append(f"Moderate financial capacity: ${revenue:,.0f} annual revenue")
            else:
                negative_factors.append(f"Limited financial capacity: ${revenue:,.0f} annual revenue")
                recommendations.append("Verify financial stability and grant management capacity")
        except Exception:
            pass

    funding_amount = opportunity.funding_amount
    if funding_amount:
        positive_factors.append(f"Specific funding amount available: ${funding_amount:,.0f}")

    score = 0.6 + len(positive_factors) * 0.15 - len(negative_factors) * 0.2
    score = max(0.1, min(1.0, score))

    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": recommendations,
        "risks": []
    }


def _analyze_timing_factors(opportunity):
    """Analyze timing and deadline factors."""
    positive_factors = []
    negative_factors = []
    risks = []

    match_factors = opportunity.match_factors or {}
    deadline = match_factors.get('deadline')

    if deadline:
        positive_factors.append("Clear application deadline provided")
    else:
        negative_factors.append("No clear deadline information available")
        risks.append("Risk of missing application windows without deadline clarity")

    discovered_at = opportunity.discovered_at
    if discovered_at:
        from datetime import timedelta
        try:
            discovered_date = datetime.fromisoformat(discovered_at.replace('Z', '+00:00'))
            days_since_discovery = (datetime.now().astimezone() - discovered_date).days

            if days_since_discovery <= 7:
                positive_factors.append("Recently discovered opportunity - information is current")
            elif days_since_discovery <= 30:
                positive_factors.append("Opportunity discovered within last month")
            else:
                negative_factors.append("Opportunity information may be outdated")
                risks.append("Risk of changed requirements or closed applications")
        except Exception:
            pass

    score = 0.5 + len(positive_factors) * 0.2 - len(negative_factors) * 0.15
    score = max(0.1, min(1.0, score))

    return {
        "score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "recommendations": [],
        "risks": risks
    }


def _generate_strategic_insights(profile, opportunity, score):
    """Generate strategic insights for the opportunity."""
    insights = []

    external_data = opportunity.external_data or {}
    org_name = opportunity.organization_name
    description = opportunity.description or ''

    if external_data.get('foundation_code') == '03':
        insights.append(f"{org_name} is a private foundation - may offer flexible funding terms")

    if 'million' in description.lower():
        insights.append("Large organization with potentially substantial grant-making capacity")

    ntee_code = external_data.get('ntee_code', '')
    if ntee_code and ntee_code.startswith('T'):
        insights.append("Philanthropy/voluntarism focus suggests potential for collaborative partnerships")

    if score >= 0.8:
        insights.append("High-scoring opportunity - prioritize for immediate action")
    elif score >= 0.6:
        insights.append("Solid opportunity - develop targeted approach based on strengths")
    else:
        insights.append("Challenging opportunity - consider if strategic investment is warranted")

    return insights[:3]


def _generate_next_steps(score, scoring_dimensions):
    """Generate actionable next steps based on scoring analysis."""
    next_steps = []

    if score >= 0.8:
        next_steps.extend([
            "Begin application preparation immediately",
            "Research organization's recent funding patterns",
            "Identify key contacts and decision makers"
        ])
    elif score >= 0.6:
        lowest_dimension = min(scoring_dimensions.items(), key=lambda x: x[1]["score"])
        next_steps.extend([
            f"Address {lowest_dimension[0]} alignment gaps first",
            "Gather additional information to strengthen application",
            "Consider strategic partnerships to enhance fit"
        ])
    else:
        next_steps.extend([
            "Reassess strategic fit before proceeding",
            "Explore alternative opportunities with better alignment",
            "Consider if significant changes could improve compatibility"
        ])

    next_steps.extend([
        "Review organization's 990 filings for deeper insights",
        "Analyze past grant recipients for pattern recognition"
    ])

    return next_steps[:5]


def _convert_lead_to_opportunity(lead):
    """Convert a lead object to opportunity dictionary format."""
    return {
        "id": lead.lead_id,
        "opportunity_id": lead.lead_id,
        "organization_name": lead.organization_name,
        "program_name": lead.program_name,
        "description": lead.description,
        "funding_amount": lead.funding_amount,
        "opportunity_type": lead.opportunity_type.value if hasattr(lead.opportunity_type, 'value') else str(lead.opportunity_type),
        "compatibility_score": lead.compatibility_score,
        "success_probability": lead.success_probability,
        "pipeline_stage": lead.pipeline_stage.value if hasattr(lead.pipeline_stage, 'value') else str(lead.pipeline_stage),
        "discovered_at": lead.discovered_at.isoformat() if lead.discovered_at else None,
        "last_analyzed": lead.last_analyzed.isoformat() if lead.last_analyzed else None,
        "match_factors": lead.match_factors,
        "recommendations": lead.recommendations,
        "approach_strategy": lead.approach_strategy,
        "external_data": lead.external_data,
        "source_type": lead.match_factors.get('source_type', 'Unknown') if lead.match_factors else 'Unknown',
        "discovery_source": lead.external_data.get('discovery_source', 'Unknown Source') if lead.external_data else 'Unknown Source',
        "application_status": lead.match_factors.get('application_status', None) if lead.match_factors else None,
        "is_schedule_i_grantee": lead.external_data.get('is_schedule_i_grantee', False) if lead.external_data else False
    }


# =====================================================================================
# Routes
# =====================================================================================

@router.get("/api/profiles/{ein}/web-intelligence")
async def get_web_intelligence(ein: str):
    """Get web intelligence data for Enhanced Data tab."""
    try:
        with sqlite3.connect("data/catalynx.db") as conn:
            cursor = conn.execute("""
                SELECT ein, url, scrape_date, intelligence_quality_score,
                       leadership_data, leadership_count, program_data, program_count,
                       contact_data, mission_statements, pages_scraped, total_content_length
                FROM web_intelligence
                WHERE ein = ?
                ORDER BY scrape_date DESC
                LIMIT 1
            """, (ein,))

            result = cursor.fetchone()

            if not result:
                return {
                    "success": False,
                    "message": f"No web intelligence data found for EIN {ein}",
                    "data": None
                }

            (db_ein, url, scrape_date, quality_score, leadership_json, leadership_count,
             program_json, program_count, contact_json, mission_json, pages_scraped, content_length) = result

            try:
                leadership_data = json.loads(leadership_json) if leadership_json else []
                program_data = json.loads(program_json) if program_json else []
                contact_data = json.loads(contact_json) if contact_json else []
                mission_data = json.loads(mission_json) if mission_json else []
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for EIN {ein}: {e}")
                leadership_data, program_data, contact_data, mission_data = [], [], [], []

            web_intelligence = {
                "successful_scrapes": [{
                    "url": url,
                    "content_length": content_length or 0,
                    "content_score": quality_score / 100.0 if quality_score else 0,
                    "timestamp": scrape_date
                }],
                "failed_scrapes": [],
                "extracted_info": {
                    "programs": [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in program_data],
                    "leadership": [f"{l.get('name', '')} - {l.get('title', '')}" if isinstance(l, dict) else str(l) for l in leadership_data],
                    "mission_statements": mission_data,
                    "contact_info": [str(c) for c in contact_data],
                    "financial_info": []
                },
                "intelligence_quality_score": quality_score or 0,
                "data_source": "database",
                "pages_scraped": pages_scraped or 0
            }

            return {
                "success": True,
                "data": {
                    "web_scraping_data": web_intelligence
                }
            }

    except Exception as e:
        logger.error(f"Failed to get web intelligence for EIN {ein}: {e}")
        return {
            "success": False,
            "message": "Error retrieving web intelligence",
            "data": None
        }


@router.get("/api/profiles/{profile_id}/verified-intelligence")
async def get_verified_intelligence(profile_id: str):
    """Get verified intelligence data using tax-data-first approach for Enhanced Data tab."""
    try:
        database_service = DatabaseManager()
        db_profile = database_service.get_profile(profile_id)

        if not db_profile:
            return {
                "success": False,
                "message": f"Profile not found in database: {profile_id}",
                "data": None
            }

        organization_name = db_profile.name
        verification_data = getattr(db_profile, 'verification_data', {}) or {}
        web_enhanced_data = getattr(db_profile, 'web_enhanced_data', {}) or {}

        logger.info(f"Getting verified intelligence for {organization_name}")

        leadership_list = []
        if web_enhanced_data.get('verified_leadership'):
            leadership_list = [
                f"{leader.get('name', 'Unknown')} - {leader.get('title', 'Unknown Title')} (Tax Filing, {leader.get('confidence_score', 0.9):.1%} confidence)"
                for leader in web_enhanced_data['verified_leadership']
                if leader.get('name')
            ]
        elif web_enhanced_data.get('leadership'):
            leadership_list = web_enhanced_data['leadership']

        programs_list = web_enhanced_data.get('programs', [])

        mission_statements = []
        if hasattr(db_profile, 'mission_statement') and db_profile.mission_statement:
            mission_statements = [db_profile.mission_statement]

        profile_website = getattr(db_profile, 'website_url', None) or getattr(db_profile, 'website', None)

        web_intelligence = {
            "successful_scrapes": [
                {
                    "url": profile_website or "No website available",
                    "content_length": len(str(web_enhanced_data)),
                    "content_score": verification_data.get('confidence_score', 0.8),
                    "timestamp": verification_data.get('fetched_at', datetime.now().isoformat())
                }
            ] if profile_website else [],
            "failed_scrapes": [],
            "extracted_info": {
                "leadership": leadership_list,
                "programs": programs_list,
                "mission_statements": mission_statements,
                "contact_info": [],
                "financial_info": []
            },
            "intelligence_quality_score": verification_data.get('confidence_score', 0.8),
            "data_source": "verified_tax_data_first",
            "pages_scraped": 1 if profile_website else 0,
            "verification_details": {
                "overall_confidence": verification_data.get('confidence_score', 0.8),
                "has_990_baseline": bool(verification_data.get('has_990_baseline', True)),
                "source_attribution": verification_data.get('source_attribution', 'Tax Filing + Web Verification'),
                "data_sources_used": verification_data.get('data_sources_used', ['Tax Filing', 'Web Scraping']),
                "verification_notes": verification_data.get('verification_notes', 'Data verified using tax-data-first approach'),
                "processing_time": verification_data.get('processing_time', 'N/A')
            }
        }

        verified_intelligence_compat = {
            "verified_website": profile_website,
            "verified_mission": mission_statements[0] if mission_statements else None,
            "verified_leadership": web_enhanced_data.get('verified_leadership', []),
            "verified_programs": programs_list,
            "overall_confidence": verification_data.get('confidence_score', 0.8),
            "data_quality_score": verification_data.get('confidence_score', 0.8),
            "intelligence_quality_score": verification_data.get('confidence_score', 0.8),
            "has_enhanced_data": bool(web_enhanced_data or verification_data),
            "fetched_at": verification_data.get('fetched_at', datetime.now().isoformat())
        }

        return {
            "success": True,
            "data": {
                "web_scraping_data": web_intelligence,
                "verified_intelligence": verified_intelligence_compat
            }
        }

    except Exception as e:
        logger.error(f"Failed to get verified intelligence for profile {profile_id}: {e}")
        return {
            "success": False,
            "message": "Error retrieving verified intelligence",
            "data": None
        }


@router.get("/api/profiles/{profile_id}/enhanced-intelligence")
async def get_enhanced_intelligence(profile_id: str):
    """Alias for verified intelligence - maintains compatibility with frontend calls."""
    return await get_verified_intelligence(profile_id)


@router.post("/api/profiles/{profile_id}/metrics/funnel")
async def update_funnel_metrics(profile_id: str, request: Dict[str, Any]):
    """Update funnel stage metrics for a profile."""
    try:
        stage = request.get("stage")
        count = request.get("count", 1)

        if not stage:
            raise HTTPException(status_code=400, detail="Stage is required")

        await metrics_tracker.update_funnel_stage(profile_id, stage, count)

        return {"success": True, "message": f"Updated {stage} metrics for profile {profile_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update funnel metrics for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/profiles/{profile_id}/metrics/session")
async def start_metrics_session(profile_id: str):
    """Start a new discovery session for metrics tracking."""
    try:
        await metrics_tracker.start_discovery_session(profile_id)

        return {
            "success": True,
            "message": f"Started new discovery session for profile {profile_id}",
            "session_started_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to start metrics session for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/profiles/{profile_id}/opportunities/{opportunity_id}/scoring-rationale")
async def get_scoring_rationale(profile_id: str, opportunity_id: str):
    """Get detailed scoring rationale and analysis for an opportunity."""
    try:
        profile = profile_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        leads = profile_service.get_profile_leads(profile_id=profile_id)
        opportunity = None
        for lead in leads:
            if lead.lead_id == opportunity_id:
                opportunity = lead
                break

        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        scoring_rationale = await _generate_scoring_rationale(profile, opportunity)

        return {
            "profile_id": profile_id,
            "opportunity_id": opportunity_id,
            "organization_name": opportunity.organization_name,
            "overall_score": opportunity.compatibility_score,
            "scoring_rationale": scoring_rationale,
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate scoring rationale for {opportunity_id} in profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/profiles/{profile_id}/leads")
async def get_profile_leads(profile_id: str, stage: Optional[str] = None, min_score: Optional[float] = None):
    """Get opportunity leads for a profile."""
    try:
        from src.profiles.models import PipelineStage

        pipeline_stage = None
        if stage:
            try:
                pipeline_stage = PipelineStage(stage)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

        leads = profile_service.get_profile_leads(
            profile_id=profile_id,
            stage=pipeline_stage,
            min_score=min_score
        )

        return {
            "profile_id": profile_id,
            "total_leads": len(leads),
            "leads": [lead.model_dump() for lead in leads],
            "filters_applied": {
                "stage": stage,
                "min_score": min_score
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get leads for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

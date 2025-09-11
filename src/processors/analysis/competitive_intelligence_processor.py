#!/usr/bin/env python3
"""
Competitive Intelligence Processor
Analyzes competitor organizations and funding landscapes using web intelligence.

This processor:
1. Identifies similar organizations in the same NTEE codes and geographic areas
2. Analyzes their web presence and strategic positioning
3. Compares funding patterns and grant success rates
4. Provides competitive insights and strategic recommendations
5. Monitors market trends and funding opportunities
"""

import asyncio
import time
import sqlite3
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile

try:
    from src.core.simple_mcp_client import SimpleMCPClient, DeepIntelligenceResult
except ImportError:
    SimpleMCPClient = None
    DeepIntelligenceResult = None


class CompetitorProfile:
    """Represents a competitor organization with intelligence data."""
    
    def __init__(self, ein: str, name: str, state: str, ntee_code: str):
        self.ein = ein
        self.name = name
        self.state = state
        self.ntee_code = ntee_code
        self.web_intelligence_score = 0
        self.funding_intelligence = {}
        self.strategic_positioning = {}
        self.competitive_threat_level = "Unknown"
        self.strengths = []
        self.weaknesses = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'ein': self.ein,
            'name': self.name,
            'state': self.state,
            'ntee_code': self.ntee_code,
            'web_intelligence_score': self.web_intelligence_score,
            'funding_intelligence': self.funding_intelligence,
            'strategic_positioning': self.strategic_positioning,
            'competitive_threat_level': self.competitive_threat_level,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses
        }


class CompetitiveIntelligenceProcessor(BaseProcessor):
    """Processor for competitive intelligence analysis using web intelligence."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="competitive_intelligence_processor",
            description="Analyze competitor organizations and funding landscapes with web intelligence",
            version="1.0.0",
            dependencies=["bmf_filter"],  # Run after BMF filtering to get competitor organizations
            estimated_duration=180,  # 3 minutes for comprehensive analysis
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Initialize MCP client for web intelligence
        self.mcp_client = SimpleMCPClient(timeout=25) if SimpleMCPClient else None
        self.database_path = "data/catalynx.db"
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute competitive intelligence analysis."""
        start_time = time.time()
        
        try:
            # Get target organizations from previous step
            target_organizations = await self._get_target_organizations(config, workflow_state)
            if not target_organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No target organizations found for competitive intelligence analysis"]
                )
            
            self.logger.info(f"Analyzing competitive landscape for {len(target_organizations)} target organizations")
            
            # Step 1: Discover competitor organizations
            competitors = await self._discover_competitors(target_organizations, config)
            self.logger.info(f"Discovered {len(competitors)} potential competitors")
            
            # Step 2: Analyze competitor web intelligence
            competitor_profiles = await self._analyze_competitor_intelligence(competitors, config)
            self.logger.info(f"Analyzed web intelligence for {len(competitor_profiles)} competitors")
            
            # Step 3: Compare funding landscapes
            funding_analysis = await self._analyze_funding_landscape(target_organizations, competitor_profiles, config)
            
            # Step 4: Generate competitive insights and recommendations
            competitive_insights = self._generate_competitive_insights(
                target_organizations, competitor_profiles, funding_analysis
            )
            
            # Step 5: Create strategic recommendations
            strategic_recommendations = self._create_strategic_recommendations(
                target_organizations, competitor_profiles, competitive_insights
            )
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "target_organizations": [org.dict() for org in target_organizations],
                "competitive_analysis": {
                    "total_competitors_discovered": len(competitors),
                    "competitors_with_intelligence": len(competitor_profiles),
                    "competitive_landscape_coverage": len(competitor_profiles) / max(len(competitors), 1) * 100,
                    "analysis_scope": {
                        "ntee_codes_analyzed": list(set(org.ntee_code for org in target_organizations if org.ntee_code)),
                        "states_analyzed": list(set(org.state for org in target_organizations if org.state)),
                        "intelligence_sources": ["web_scraping", "funding_data", "board_intelligence"]
                    }
                },
                "competitor_profiles": [profile.to_dict() for profile in competitor_profiles],
                "funding_landscape": funding_analysis,
                "competitive_insights": competitive_insights,
                "strategic_recommendations": strategic_recommendations
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "competitive_intelligence",
                    "data_sources": ["web_intelligence", "bmf_data", "funding_patterns"],
                    "competitor_threat_levels": self._summarize_threat_levels(competitor_profiles)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Competitive intelligence analysis failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Competitive intelligence analysis failed: {str(e)}"]
            )
    
    async def _get_target_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get target organizations from previous workflow step."""
        try:
            if workflow_state and workflow_state.has_processor_succeeded('bmf_filter'):
                org_dicts = workflow_state.get_organizations_from_processor('bmf_filter')
                if org_dicts:
                    organizations = []
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    return organizations[:5]  # Limit to 5 target orgs for performance
            
            # Fallback: create test target organizations
            self.logger.warning("No organizations from BMF filter - using test data")
            return self._create_test_target_organizations()
            
        except Exception as e:
            self.logger.error(f"Failed to get target organizations: {e}")
            return []
    
    def _create_test_target_organizations(self) -> List[OrganizationProfile]:
        """Create test target organizations for competitive analysis."""
        return [
            OrganizationProfile(
                ein="812827604",
                name="HEROS BRIDGE",
                state="VA",
                ntee_code="P20",
                address="123 Main St",
                city="Warrenton"
            ),
            OrganizationProfile(
                ein="541026365",
                name="VETERANS FOUNDATION",
                state="VA", 
                ntee_code="P23",
                address="456 Oak Ave",
                city="Richmond"
            )
        ]
    
    async def _discover_competitors(self, target_orgs: List[OrganizationProfile], config: ProcessorConfig) -> List[Dict[str, Any]]:
        """Discover competitor organizations using BMF database."""
        competitors = []
        
        try:
            # Get unique NTEE codes and states from target organizations
            ntee_codes = list(set(org.ntee_code for org in target_orgs if org.ntee_code))
            states = list(set(org.state for org in target_orgs if org.state))
            target_eins = set(org.ein for org in target_orgs)
            
            if not ntee_codes:
                self.logger.warning("No NTEE codes available for competitor discovery")
                return competitors
            
            # Query BMF database for similar organizations
            with sqlite3.connect("data/nonprofit_intelligence.db") as conn:
                # Build query for organizations in same NTEE codes and geographic areas
                ntee_placeholder = ','.join('?' * len(ntee_codes))
                state_placeholder = ','.join('?' * len(states)) if states else "'VA','MD','DC'"  # Default nearby states
                
                query = f"""
                    SELECT ein, name, state, ntee_code, classification
                    FROM bmf_organizations 
                    WHERE ntee_code IN ({ntee_placeholder})
                    AND state IN ({state_placeholder})
                    AND ein NOT IN ({','.join('?' * len(target_eins))})
                    ORDER BY name
                    LIMIT 20
                """
                
                params = ntee_codes + (states if states else ['VA', 'MD', 'DC']) + list(target_eins)
                cursor = conn.execute(query, params)
                
                for ein, name, state, ntee_code, classification in cursor.fetchall():
                    # Try to get financial data from form_990 table if available
                    asset_amount = 0
                    income_amount = 0
                    try:
                        financial_cursor = conn.execute("""
                            SELECT totassetsend, totrevenue 
                            FROM form_990 
                            WHERE ein = ? 
                            ORDER BY tax_year DESC 
                            LIMIT 1
                        """, (ein,))
                        financial_result = financial_cursor.fetchone()
                        if financial_result:
                            asset_amount = financial_result[0] or 0
                            income_amount = financial_result[1] or 0
                    except:
                        pass  # Financial data not available
                    
                    competitors.append({
                        'ein': ein,
                        'name': name,
                        'state': state,
                        'ntee_code': ntee_code,
                        'classification': classification,
                        'asset_amount': asset_amount,
                        'income_amount': income_amount
                    })
                    
        except Exception as e:
            self.logger.warning(f"Failed to discover competitors from BMF: {e}")
        
        return competitors
    
    async def _analyze_competitor_intelligence(self, competitors: List[Dict[str, Any]], config: ProcessorConfig) -> List[CompetitorProfile]:
        """Analyze web intelligence for competitor organizations."""
        competitor_profiles = []
        
        if not self.mcp_client:
            self.logger.warning("MCP client not available - skipping web intelligence analysis")
            return competitor_profiles
        
        # Limit analysis to top competitors by asset size
        top_competitors = sorted(competitors, key=lambda x: x.get('asset_amount', 0), reverse=True)[:10]
        
        for competitor in top_competitors:
            try:
                profile = CompetitorProfile(
                    ein=competitor['ein'],
                    name=competitor['name'],
                    state=competitor['state'],
                    ntee_code=competitor['ntee_code']
                )
                
                # Check for existing web intelligence
                web_intel = await self._get_existing_web_intelligence(competitor['ein'])
                if web_intel:
                    profile.web_intelligence_score = web_intel.get('intelligence_quality_score', 0)
                    profile.strategic_positioning = self._analyze_strategic_positioning(web_intel)
                    profile.strengths, profile.weaknesses = self._assess_competitive_strengths(web_intel)
                else:
                    # Attempt to gather new web intelligence
                    predicted_url = await self._predict_organization_url(competitor['name'], competitor['state'])
                    if predicted_url:
                        intel_result = await self.mcp_client.fetch_deep_intelligence(predicted_url)
                        if intel_result and intel_result.success:
                            profile.web_intelligence_score = intel_result.intelligence_score
                            profile.strategic_positioning = {
                                'mission_focus': intel_result.mission_data.get('mission_statement', ''),
                                'program_count': len(intel_result.program_data),
                                'leadership_depth': len(intel_result.leadership_data)
                            }
                            profile.strengths, profile.weaknesses = self._assess_competitive_strengths({
                                'program_data': json.dumps(intel_result.program_data),
                                'leadership_data': json.dumps(intel_result.leadership_data),
                                'intelligence_quality_score': intel_result.intelligence_score
                            })
                
                # Assess competitive threat level
                profile.competitive_threat_level = self._assess_threat_level(profile, competitor)
                
                competitor_profiles.append(profile)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze competitor {competitor['name']}: {e}")
                continue
        
        return competitor_profiles
    
    async def _get_existing_web_intelligence(self, ein: str) -> Optional[Dict[str, Any]]:
        """Get existing web intelligence data for an organization."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT intelligence_quality_score, leadership_data, program_data, 
                           contact_data, pages_scraped
                    FROM web_intelligence 
                    WHERE ein = ?
                """, (ein,))
                
                result = cursor.fetchone()
                if result:
                    quality_score, leadership_data, program_data, contact_data, pages_scraped = result
                    return {
                        'intelligence_quality_score': quality_score,
                        'leadership_data': leadership_data,
                        'program_data': program_data,
                        'contact_data': contact_data,
                        'pages_scraped': pages_scraped
                    }
        except Exception as e:
            self.logger.debug(f"No existing web intelligence for {ein}: {e}")
        
        return None
    
    async def _predict_organization_url(self, org_name: str, state: str) -> Optional[str]:
        """Predict organization URL using GPT."""
        # This would use the GPT URL discovery service similar to BMF Filter
        # For now, return a simple heuristic-based prediction
        base_name = re.sub(r'[^\w\s]', '', org_name.lower())
        base_name = re.sub(r'\s+', '', base_name)
        
        # Common URL patterns for nonprofits
        possible_urls = [
            f"https://www.{base_name}.org",
            f"https://{base_name}.org",
            f"https://www.{base_name}.com",
            f"https://{base_name}.net"
        ]
        
        return possible_urls[0] if possible_urls else None
    
    def _analyze_strategic_positioning(self, web_intel: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strategic positioning from web intelligence."""
        positioning = {
            'digital_presence_strength': min(web_intel.get('intelligence_quality_score', 0) / 100, 1.0),
            'program_diversity': 0,
            'leadership_visibility': 0,
            'community_engagement': 0
        }
        
        # Analyze program diversity
        try:
            program_data = json.loads(web_intel.get('program_data', '[]'))
            positioning['program_diversity'] = min(len(program_data) / 5.0, 1.0)  # Normalize to 0-1
        except:
            pass
        
        # Analyze leadership visibility
        try:
            leadership_data = json.loads(web_intel.get('leadership_data', '[]'))
            positioning['leadership_visibility'] = min(len(leadership_data) / 10.0, 1.0)  # Normalize to 0-1
        except:
            pass
        
        # Community engagement based on pages scraped
        pages_scraped = web_intel.get('pages_scraped', 0)
        positioning['community_engagement'] = min(pages_scraped / 10.0, 1.0)  # Normalize to 0-1
        
        return positioning
    
    def _assess_competitive_strengths(self, web_intel: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Assess competitive strengths and weaknesses from web intelligence."""
        strengths = []
        weaknesses = []
        
        quality_score = web_intel.get('intelligence_quality_score', 0)
        
        # Assess based on intelligence quality
        if quality_score >= 80:
            strengths.append("Strong digital presence and transparency")
        elif quality_score <= 40:
            weaknesses.append("Limited digital presence and public information")
        
        # Assess leadership depth
        try:
            leadership_data = json.loads(web_intel.get('leadership_data', '[]'))
            if len(leadership_data) >= 5:
                strengths.append("Deep leadership team with public visibility")
            elif len(leadership_data) <= 2:
                weaknesses.append("Limited leadership visibility")
        except:
            pass
        
        # Assess program diversity
        try:
            program_data = json.loads(web_intel.get('program_data', '[]'))
            if len(program_data) >= 3:
                strengths.append("Diverse program portfolio")
            elif len(program_data) <= 1:
                weaknesses.append("Limited program diversity")
        except:
            pass
        
        return strengths, weaknesses
    
    def _assess_threat_level(self, profile: CompetitorProfile, competitor_data: Dict[str, Any]) -> str:
        """Assess competitive threat level based on multiple factors."""
        threat_score = 0
        
        # Asset-based threat assessment
        asset_amount = competitor_data.get('asset_amount', 0)
        if asset_amount > 5000000:
            threat_score += 3
        elif asset_amount > 1000000:
            threat_score += 2
        elif asset_amount > 100000:
            threat_score += 1
        
        # Web intelligence-based threat assessment
        if profile.web_intelligence_score >= 80:
            threat_score += 2
        elif profile.web_intelligence_score >= 60:
            threat_score += 1
        
        # Strategic positioning threat assessment
        positioning_avg = sum(profile.strategic_positioning.values()) / max(len(profile.strategic_positioning), 1)
        if positioning_avg >= 0.8:
            threat_score += 2
        elif positioning_avg >= 0.6:
            threat_score += 1
        
        # Convert to threat level
        if threat_score >= 6:
            return "High"
        elif threat_score >= 4:
            return "Medium"
        elif threat_score >= 2:
            return "Low"
        else:
            return "Minimal"
    
    async def _analyze_funding_landscape(self, target_orgs: List[OrganizationProfile], 
                                       competitors: List[CompetitorProfile], 
                                       config: ProcessorConfig) -> Dict[str, Any]:
        """Analyze funding landscape and patterns."""
        funding_analysis = {
            "market_concentration": {},
            "funding_trends": {},
            "competitive_gaps": [],
            "opportunity_areas": []
        }
        
        try:
            # Analyze asset distribution across competitors
            competitor_assets = []
            total_assets = 0
            
            for competitor in competitors:
                # This would query funding data from 990 forms if available
                # For now, use placeholder analysis
                competitor_assets.append({
                    'name': competitor.name,
                    'estimated_assets': 1000000,  # Placeholder
                    'threat_level': competitor.competitive_threat_level
                })
                total_assets += 1000000
            
            # Market concentration analysis
            funding_analysis["market_concentration"] = {
                "total_market_assets": total_assets,
                "competitor_count": len(competitors),
                "average_competitor_assets": total_assets / max(len(competitors), 1),
                "high_threat_competitors": len([c for c in competitors if c.competitive_threat_level == "High"])
            }
            
            # Identify competitive gaps
            ntee_codes = list(set(org.ntee_code for org in target_orgs if org.ntee_code))
            for ntee in ntee_codes:
                competitors_in_ntee = [c for c in competitors if c.ntee_code == ntee]
                if len(competitors_in_ntee) < 3:
                    funding_analysis["competitive_gaps"].append(f"Limited competition in {ntee} sector")
            
            # Opportunity areas
            low_intel_competitors = [c for c in competitors if c.web_intelligence_score < 50]
            if len(low_intel_competitors) > len(competitors) * 0.5:
                funding_analysis["opportunity_areas"].append("Many competitors have weak digital presence")
                
        except Exception as e:
            self.logger.warning(f"Failed to analyze funding landscape: {e}")
        
        return funding_analysis
    
    def _generate_competitive_insights(self, target_orgs: List[OrganizationProfile],
                                     competitors: List[CompetitorProfile],
                                     funding_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate competitive insights and key findings."""
        insights = {
            "key_findings": [],
            "competitive_advantages": [],
            "market_position": {},
            "threat_assessment": []
        }
        
        # Market position analysis
        high_threat = len([c for c in competitors if c.competitive_threat_level == "High"])
        medium_threat = len([c for c in competitors if c.competitive_threat_level == "Medium"])
        
        insights["key_findings"].append(f"Identified {len(competitors)} competitors with {high_threat} high-threat organizations")
        
        # Intelligence score analysis
        avg_competitor_intelligence = sum(c.web_intelligence_score for c in competitors) / max(len(competitors), 1)
        insights["market_position"]["average_competitor_intelligence"] = avg_competitor_intelligence
        
        if avg_competitor_intelligence < 60:
            insights["competitive_advantages"].append("Market shows weak digital presence among competitors")
        
        # Geographic concentration
        states = list(set(c.state for c in competitors))
        insights["key_findings"].append(f"Competition spans {len(states)} states: {', '.join(states[:5])}")
        
        # Threat assessment
        if high_threat > 3:
            insights["threat_assessment"].append("High competitive threat environment - strong competitors present")
        elif high_threat == 0:
            insights["threat_assessment"].append("Low competitive threat - opportunity for market leadership")
        
        return insights
    
    def _create_strategic_recommendations(self, target_orgs: List[OrganizationProfile],
                                        competitors: List[CompetitorProfile],
                                        insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create strategic recommendations based on competitive analysis."""
        recommendations = []
        
        # Digital presence recommendations
        avg_intelligence = insights.get("market_position", {}).get("average_competitor_intelligence", 0)
        if avg_intelligence < 60:
            recommendations.append({
                "category": "Digital Strategy",
                "priority": "High",
                "recommendation": "Invest in strong digital presence to outperform competitors",
                "rationale": f"Average competitor intelligence score is only {avg_intelligence:.0f}/100"
            })
        
        # Geographic expansion recommendations
        high_threat_competitors = [c for c in competitors if c.competitive_threat_level == "High"]
        if len(high_threat_competitors) < 2:
            recommendations.append({
                "category": "Market Expansion",
                "priority": "Medium", 
                "recommendation": "Consider geographic expansion with limited high-threat competition",
                "rationale": f"Only {len(high_threat_competitors)} high-threat competitors identified"
            })
        
        # Partnership opportunities
        weak_competitors = [c for c in competitors if c.web_intelligence_score < 40]
        if len(weak_competitors) > 0:
            recommendations.append({
                "category": "Strategic Partnerships",
                "priority": "Medium",
                "recommendation": f"Explore partnerships with {len(weak_competitors)} competitors showing weak digital presence",
                "rationale": "Potential for collaboration rather than direct competition"
            })
        
        # Differentiation strategy
        common_strengths = []
        for competitor in competitors:
            common_strengths.extend(competitor.strengths)
        
        strength_counts = Counter(common_strengths)
        if strength_counts:
            most_common_strength = strength_counts.most_common(1)[0]
            recommendations.append({
                "category": "Differentiation",
                "priority": "High",
                "recommendation": f"Differentiate beyond common competitor strength: {most_common_strength[0]}",
                "rationale": f"Found in {most_common_strength[1]} competitors - avoid commodity positioning"
            })
        
        return recommendations
    
    def _summarize_threat_levels(self, competitors: List[CompetitorProfile]) -> Dict[str, int]:
        """Summarize threat levels across all competitors."""
        threat_counts = Counter(c.competitive_threat_level for c in competitors)
        return dict(threat_counts)
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for competitive intelligence analysis."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return CompetitiveIntelligenceProcessor()
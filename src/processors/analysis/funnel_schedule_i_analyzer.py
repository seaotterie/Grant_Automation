"""
Funnel-Aware Schedule I Network Analysis
Enhanced Schedule I analysis integrated with the Grant Opportunity Funnel system.

This processor enhances the Schedule I analysis by:
1. Analyzing Profile's own grants received (Schedule I as recipient)
2. Finding funders that supported the Profile
3. Researching other grantees of those funders
4. Creating network connections and lead generation
5. Integrating with funnel stages for intelligent progression
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.discovery.base_discoverer import DiscoveryResult, FunnelStage
from src.discovery.funnel_manager import funnel_manager
from src.profiles.service import ProfileService
from src.profiles.models import OpportunityLead, FundingType


class FunnelScheduleIAnalyzer(BaseProcessor):
    """Enhanced Schedule I analysis integrated with funnel stages."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="funnel_schedule_i_analyzer",
            description="Funnel-integrated Schedule I network analysis and lead generation",
            version="2.0.0",
            dependencies=["xml_downloader", "propublica_fetch"],
            estimated_duration=600,  # 10 minutes for comprehensive analysis
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        self.profile_service = ProfileService()
        
        # Analysis configuration
        self.max_network_depth = 2  # How deep to trace funding networks
        self.min_grant_amount = 5000  # Focus on substantial grants
        self.max_leads_per_funder = 20  # Limit leads per funding organization
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute funnel-aware Schedule I analysis."""
        start_time = time.time()
        
        try:
            # Get target profile for analysis
            target_profile = await self._get_target_profile(config)
            if not target_profile:
                return self._error_result("Target profile not found", start_time)
            
            self.logger.info(f"Starting Schedule I network analysis for profile: {target_profile.name}")
            
            # Step 1: Analyze Profile's grants received (if available)
            profile_funding_history = await self._analyze_profile_grants_received(target_profile)
            
            # Step 2: Research funders who supported the Profile
            profile_funders = await self._identify_profile_funders(target_profile, profile_funding_history)
            
            # Step 3: Find other grantees of those funders (peer organizations)
            peer_networks = await self._discover_peer_organizations(profile_funders)
            
            # Step 4: Generate opportunity leads from network analysis
            opportunity_leads = await self._generate_network_opportunities(
                target_profile, profile_funders, peer_networks
            )
            
            # Step 5: Apply funnel intelligence for stage assignment
            staged_opportunities = await self._assign_funnel_stages(opportunity_leads, target_profile)
            
            # Step 6: Add opportunities to funnel manager
            if staged_opportunities:
                funnel_manager.add_opportunities(target_profile.profile_id, staged_opportunities)
            
            execution_time = time.time() - start_time
            
            # Prepare comprehensive results
            result_data = {
                "target_profile": target_profile.dict(),
                "network_analysis": {
                    "profile_funding_history": profile_funding_history,
                    "identified_funders": len(profile_funders),
                    "peer_organizations": len(peer_networks),
                    "network_opportunities": len(opportunity_leads),
                    "funnel_staged_opportunities": len(staged_opportunities)
                },
                "opportunities": [opp.__dict__ for opp in staged_opportunities],
                "funnel_distribution": self._calculate_funnel_distribution(staged_opportunities),
                "network_insights": await self._generate_network_insights(
                    target_profile, profile_funders, peer_networks
                )
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "funnel_schedule_i_network",
                    "network_depth": self.max_network_depth,
                    "min_grant_amount": self.min_grant_amount
                }
            )
            
        except Exception as e:
            self.logger.error(f"Funnel Schedule I analysis failed: {e}", exc_info=True)
            return self._error_result(f"Analysis failed: {str(e)}", start_time)
    
    async def _get_target_profile(self, config: ProcessorConfig) -> Optional[OrganizationProfile]:
        """Get the target profile for analysis."""
        try:
            profile_id = config.get_config("profile_id") or config.workflow_config.target_ein
            if profile_id:
                return await self.profile_service.get_profile(profile_id)
        except Exception as e:
            self.logger.warning(f"Could not retrieve target profile: {e}")
        return None
    
    async def _analyze_profile_grants_received(self, profile: OrganizationProfile) -> Dict[str, Any]:
        """Analyze grants the Profile has received (reverse Schedule I analysis)."""
        try:
            funding_history = {
                "total_grants_received": 0,
                "total_funding_amount": 0,
                "funding_sources": [],
                "funding_patterns": {},
                "recent_funders": []
            }
            
            # Check if profile has funding history data
            if hasattr(profile, 'financial_history') and profile.financial_history:
                for year_data in profile.financial_history:
                    if 'grants_received' in year_data:
                        grants = year_data['grants_received']
                        funding_history["total_grants_received"] += len(grants)
                        
                        for grant in grants:
                            funder_name = grant.get('funder_name', 'Unknown')
                            amount = grant.get('amount', 0)
                            year = grant.get('year', year_data.get('year'))
                            
                            funding_history["total_funding_amount"] += amount
                            funding_history["funding_sources"].append({
                                "funder": funder_name,
                                "amount": amount,
                                "year": year
                            })
                            
                            # Track recent funders (last 3 years)
                            if year and year >= datetime.now().year - 3:
                                funding_history["recent_funders"].append(funder_name)
            
            # Analyze funding patterns
            if funding_history["funding_sources"]:
                funder_amounts = defaultdict(int)
                for source in funding_history["funding_sources"]:
                    funder_amounts[source["funder"]] += source["amount"]
                
                funding_history["funding_patterns"] = {
                    "top_funders": dict(sorted(funder_amounts.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "funding_diversity": len(set(source["funder"] for source in funding_history["funding_sources"])),
                    "average_grant_size": funding_history["total_funding_amount"] / max(funding_history["total_grants_received"], 1)
                }
            
            return funding_history
            
        except Exception as e:
            self.logger.error(f"Failed to analyze profile funding history: {e}")
            return {"error": str(e)}
    
    async def _identify_profile_funders(self, profile: OrganizationProfile, funding_history: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify organizations that have funded the Profile."""
        funders = []
        
        try:
            # Extract funders from funding history
            if "funding_sources" in funding_history:
                funder_data = defaultdict(lambda: {"total_amount": 0, "grant_count": 0, "years": []})
                
                for source in funding_history["funding_sources"]:
                    funder_name = source["funder"]
                    amount = source["amount"]
                    year = source["year"]
                    
                    funder_data[funder_name]["total_amount"] += amount
                    funder_data[funder_name]["grant_count"] += 1
                    if year:
                        funder_data[funder_name]["years"].append(year)
                
                # Convert to structured funder list
                for funder_name, data in funder_data.items():
                    funders.append({
                        "name": funder_name,
                        "total_amount_to_profile": data["total_amount"],
                        "grants_to_profile": data["grant_count"],
                        "funding_years": sorted(data["years"]),
                        "relationship_strength": self._calculate_relationship_strength(data),
                        "potential_for_repeat_funding": self._assess_repeat_potential(data)
                    })
            
            # Sort by relationship strength
            funders.sort(key=lambda x: x["relationship_strength"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to identify profile funders: {e}")
        
        return funders
    
    async def _discover_peer_organizations(self, profile_funders: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Discover other organizations funded by the same funders (peer analysis)."""
        peer_networks = {}
        
        try:
            for funder in profile_funders[:10]:  # Focus on top 10 funders
                funder_name = funder["name"]
                
                # Find other grantees of this funder
                peer_orgs = await self._find_funder_grantees(funder_name)
                
                if peer_orgs:
                    peer_networks[funder_name] = peer_orgs
                    self.logger.info(f"Found {len(peer_orgs)} peer organizations for funder: {funder_name}")
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        except Exception as e:
            self.logger.error(f"Failed to discover peer organizations: {e}")
        
        return peer_networks
    
    async def _find_funder_grantees(self, funder_name: str) -> List[Dict[str, Any]]:
        """Find organizations that have received grants from a specific funder."""
        grantees = []
        
        try:
            # This would ideally query a database of Schedule I data or use APIs
            # For now, we'll simulate the process with a placeholder
            
            # In a real implementation, this would:
            # 1. Search ProPublica API for organizations matching funder name
            # 2. Download their 990 Schedule I data
            # 3. Extract grant recipient information
            # 4. Cross-reference with known organizations
            
            # Placeholder implementation
            grantees = [
                {
                    "organization_name": f"Peer Organization A (funded by {funder_name})",
                    "ein": "123456789",
                    "grant_amount": 50000,
                    "grant_year": 2023,
                    "mission_alignment_potential": 0.8
                }
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to find grantees for funder {funder_name}: {e}")
        
        return grantees
    
    async def _generate_network_opportunities(
        self,
        target_profile: OrganizationProfile,
        profile_funders: List[Dict[str, Any]],
        peer_networks: Dict[str, List[Dict[str, Any]]]
    ) -> List[DiscoveryResult]:
        """Generate opportunity leads from network analysis."""
        opportunities = []
        
        try:
            # Opportunity Type 1: Re-engagement with past funders
            for funder in profile_funders:
                if funder["potential_for_repeat_funding"] > 0.6:
                    opp = self._create_re_engagement_opportunity(target_profile, funder)
                    opportunities.append(opp)
            
            # Opportunity Type 2: Peer funder opportunities
            for funder_name, peer_orgs in peer_networks.items():
                for peer in peer_orgs:
                    if peer.get("mission_alignment_potential", 0) > 0.7:
                        opp = self._create_peer_network_opportunity(target_profile, funder_name, peer)
                        opportunities.append(opp)
            
            # Opportunity Type 3: Network expansion opportunities
            network_expansion_opps = await self._identify_network_expansion_opportunities(
                target_profile, profile_funders, peer_networks
            )
            opportunities.extend(network_expansion_opps)
            
        except Exception as e:
            self.logger.error(f"Failed to generate network opportunities: {e}")
        
        return opportunities
    
    async def _assign_funnel_stages(
        self,
        opportunities: List[DiscoveryResult],
        target_profile: OrganizationProfile
    ) -> List[DiscoveryResult]:
        """Assign appropriate funnel stages based on network intelligence."""
        
        for opp in opportunities:
            # Determine stage based on relationship strength and data quality
            network_strength = opp.external_data.get("network_strength", 0.0)
            data_completeness = opp.external_data.get("data_completeness", 0.0)
            
            if network_strength > 0.8 and data_completeness > 0.8:
                # Strong network connection with good data → TARGETS
                opp.set_stage(FunnelStage.TARGETS, "Strong network connection identified")
            elif network_strength > 0.6:
                # Good network connection → CANDIDATES
                opp.set_stage(FunnelStage.CANDIDATES, "Network connection established")
            elif data_completeness > 0.7:
                # Good data available → QUALIFIED_PROSPECTS
                opp.set_stage(FunnelStage.QUALIFIED_PROSPECTS, "Comprehensive data available")
            else:
                # Basic network lead → PROSPECTS
                opp.set_stage(FunnelStage.PROSPECTS, "Network lead identified")
        
        return opportunities
    
    def _create_re_engagement_opportunity(
        self,
        target_profile: OrganizationProfile,
        funder: Dict[str, Any]
    ) -> DiscoveryResult:
        """Create re-engagement opportunity with past funder."""
        
        return DiscoveryResult(
            organization_name=funder["name"],
            source_type=FundingType.GRANTS,
            discovery_source="Schedule I Network Analysis",
            opportunity_id=f"reengagement_{target_profile.profile_id}_{funder['name'].replace(' ', '_')}",
            program_name=f"Re-engagement with {funder['name']}",
            description=f"Past funder relationship - {funder['grants_to_profile']} grants totaling ${funder['total_amount_to_profile']:,}",
            funding_amount=int(funder["total_amount_to_profile"] / max(funder["grants_to_profile"], 1)),
            raw_score=funder["relationship_strength"],
            compatibility_score=funder["potential_for_repeat_funding"],
            confidence_level=0.9,  # High confidence due to past relationship
            match_factors={
                "past_relationship": True,
                "funding_history": funder["grants_to_profile"],
                "total_past_funding": funder["total_amount_to_profile"],
                "relationship_strength": funder["relationship_strength"]
            },
            external_data={
                "network_strength": funder["relationship_strength"],
                "data_completeness": 0.9,
                "opportunity_type": "re_engagement",
                "funding_years": funder["funding_years"]
            }
        )
    
    def _create_peer_network_opportunity(
        self,
        target_profile: OrganizationProfile,
        funder_name: str,
        peer: Dict[str, Any]
    ) -> DiscoveryResult:
        """Create opportunity from peer network analysis."""
        
        return DiscoveryResult(
            organization_name=peer["organization_name"],
            source_type=FundingType.GRANTS,
            discovery_source="Schedule I Peer Network Analysis",
            opportunity_id=f"peer_{target_profile.profile_id}_{peer['ein']}",
            program_name=f"Peer Network Opportunity via {funder_name}",
            description=f"Organization funded by {funder_name} - potential for similar support",
            funding_amount=peer.get("grant_amount"),
            raw_score=peer.get("mission_alignment_potential", 0.5),
            compatibility_score=peer.get("mission_alignment_potential", 0.5),
            confidence_level=0.7,
            match_factors={
                "shared_funder": funder_name,
                "peer_relationship": True,
                "mission_alignment": peer.get("mission_alignment_potential", 0.5)
            },
            external_data={
                "network_strength": 0.6,
                "data_completeness": 0.7,
                "opportunity_type": "peer_network",
                "shared_funder": funder_name
            }
        )
    
    async def _identify_network_expansion_opportunities(
        self,
        target_profile: OrganizationProfile,
        profile_funders: List[Dict[str, Any]],
        peer_networks: Dict[str, List[Dict[str, Any]]]
    ) -> List[DiscoveryResult]:
        """Identify opportunities for expanding the funding network."""
        expansion_opportunities = []
        
        # Look for patterns in funder types and identify gaps
        funder_types = self._analyze_funder_types(profile_funders)
        
        # Generate opportunities for underrepresented funder types
        for funder_type, potential in funder_types.items():
            if potential > 0.6:  # Good potential for this type
                opp = DiscoveryResult(
                    organization_name=f"{funder_type.title()} Funders Network",
                    source_type=FundingType.GRANTS,
                    discovery_source="Schedule I Network Expansion Analysis",
                    opportunity_id=f"expansion_{target_profile.profile_id}_{funder_type}",
                    program_name=f"Network Expansion: {funder_type.title()} Funding",
                    description=f"Expand funding network into {funder_type} sector based on profile analysis",
                    raw_score=potential,
                    compatibility_score=potential,
                    confidence_level=0.6,
                    external_data={
                        "network_strength": 0.4,
                        "data_completeness": 0.5,
                        "opportunity_type": "network_expansion"
                    }
                )
                expansion_opportunities.append(opp)
        
        return expansion_opportunities
    
    def _calculate_relationship_strength(self, funder_data: Dict[str, Any]) -> float:
        """Calculate relationship strength with a funder."""
        # Factors: total amount, grant count, consistency over time
        amount_score = min(funder_data["total_amount"] / 100000, 1.0)  # Normalize to $100k max
        count_score = min(funder_data["grant_count"] / 5, 1.0)  # Normalize to 5 grants max
        
        # Consistency score based on years funded
        years = funder_data.get("years", [])
        consistency_score = len(set(years)) / 5 if years else 0  # Normalize to 5 years max
        
        return (amount_score * 0.4 + count_score * 0.4 + consistency_score * 0.2)
    
    def _assess_repeat_potential(self, funder_data: Dict[str, Any]) -> float:
        """Assess potential for repeat funding."""
        # Recent activity increases repeat potential
        years = funder_data.get("years", [])
        if not years:
            return 0.2
        
        recent_years = [y for y in years if y >= datetime.now().year - 3]
        recent_activity = len(recent_years) / len(years)
        
        # Multiple grants indicate ongoing relationship
        grant_frequency = min(funder_data["grant_count"] / 3, 1.0)
        
        return (recent_activity * 0.6 + grant_frequency * 0.4)
    
    def _analyze_funder_types(self, profile_funders: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze types of funders and identify expansion opportunities."""
        # Placeholder implementation - would analyze funder categories
        return {
            "corporate_foundations": 0.7,
            "private_foundations": 0.8,
            "government_agencies": 0.6,
            "community_foundations": 0.5
        }
    
    def _calculate_funnel_distribution(self, opportunities: List[DiscoveryResult]) -> Dict[str, int]:
        """Calculate distribution of opportunities across funnel stages."""
        distribution = Counter(opp.funnel_stage.value for opp in opportunities)
        return dict(distribution)
    
    async def _generate_network_insights(
        self,
        target_profile: OrganizationProfile,
        profile_funders: List[Dict[str, Any]],
        peer_networks: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Generate strategic insights from network analysis."""
        
        return {
            "funding_network_strength": len(profile_funders) / 10,  # Normalize
            "network_diversity": len(peer_networks),
            "re_engagement_opportunities": len([f for f in profile_funders if f["potential_for_repeat_funding"] > 0.6]),
            "peer_network_size": sum(len(peers) for peers in peer_networks.values()),
            "strategic_recommendations": [
                "Prioritize re-engagement with past funders showing high repeat potential",
                "Leverage peer networks for warm introductions",
                "Focus on network expansion in underrepresented sectors"
            ]
        }
    
    def _error_result(self, error_message: str, start_time: float) -> ProcessorResult:
        """Create error result."""
        return ProcessorResult(
            success=False,
            processor_name=self.metadata.name,
            execution_time=time.time() - start_time,
            errors=[error_message]
        )
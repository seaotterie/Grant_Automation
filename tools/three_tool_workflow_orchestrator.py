"""
Three-Tool Workflow Orchestrator
===============================

Orchestrates the complete three-tool nonprofit grant research workflow:
1. BMF Filter Tool: Fast filtering of 700K+ organizations
2. Form 990 Analysis Tool: Deep financial analysis of filtered results
3. Form 990 ProPublica Tool: API enrichment for comprehensive profiles

Demonstrates progressive data enrichment and opportunity dossier building
"""

import sys
import os
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add all tool directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
for tool_name in ['bmf-filter-tool', 'form990-analysis-tool', 'form990-propublica-tool']:
    tool_path = os.path.join(current_dir, tool_name, 'app')
    sys.path.insert(0, tool_path)

# Import all three tools
try:
    # Import with direct module names to avoid relative import issues
    import bmf_filter
    import form990_analyzer
    import propublica_enricher

    # Import specific classes
    from bmf_filter import BMFFilterTool
    from form990_analyzer import Form990AnalysisTool, Form990AnalysisCriteria
    from propublica_enricher import ProPublicaEnrichmentTool, ProPublicaEnrichmentCriteria

    print("✅ All three tools imported successfully")
except ImportError as e:
    print(f"❌ Failed to import tools: {e}")
    sys.exit(1)


@dataclass
class WorkflowConfiguration:
    """Configuration for the three-tool workflow"""
    # BMF Filter configuration
    bmf_max_results: int = 10
    bmf_sort_by: str = "revenue_desc"

    # Form 990 Analysis configuration
    form990_years_to_analyze: int = 3
    form990_max_organizations: int = 10

    # ProPublica Enrichment configuration
    propublica_enrichment_depth: str = "standard"
    propublica_max_organizations: int = 5
    propublica_include_peers: bool = True

    # Workflow optimization
    enable_caching: bool = True
    parallel_processing: bool = False
    quality_threshold: float = 0.6


@dataclass
class OpportunityDossier:
    """Complete opportunity dossier from three-tool workflow"""
    # Identification
    ein: str
    name: str

    # Stage 1: BMF Data
    bmf_data: Optional[Dict[str, Any]] = None
    bmf_match_score: float = 0.0
    bmf_match_reasons: List[str] = None

    # Stage 2: Form 990 Analysis
    form990_data: Optional[Dict[str, Any]] = None
    financial_health_score: float = 0.0
    financial_health_category: str = "unknown"

    # Stage 3: ProPublica Enrichment
    propublica_data: Optional[Dict[str, Any]] = None
    peer_organizations: List[Dict[str, Any]] = None
    data_completeness_score: float = 0.0

    # Workflow metadata
    processing_stages_completed: List[str] = None
    total_processing_time_ms: float = 0.0
    workflow_timestamp: str = ""

    def __post_init__(self):
        if self.bmf_match_reasons is None:
            self.bmf_match_reasons = []
        if self.peer_organizations is None:
            self.peer_organizations = []
        if self.processing_stages_completed is None:
            self.processing_stages_completed = []


@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    opportunity_dossiers: List[OpportunityDossier]

    # Performance metrics
    total_execution_time_ms: float
    bmf_stage_time_ms: float
    form990_stage_time_ms: float
    propublica_stage_time_ms: float

    # Data flow metrics
    organizations_bmf_found: int
    organizations_990_analyzed: int
    organizations_propublica_enriched: int

    # Quality metrics
    overall_success_rate: float
    data_quality_score: float

    # Efficiency metrics
    filter_efficiency_ratio: float  # How many orgs filtered out
    workflow_configuration: WorkflowConfiguration


class ThreeToolWorkflowOrchestrator:
    """
    Orchestrates the complete three-tool workflow with opportunity dossier building
    """

    def __init__(self, config: Optional[WorkflowConfiguration] = None):
        """Initialize the workflow orchestrator"""
        self.config = config or WorkflowConfiguration()

        # Initialize all three tools
        print("🔧 Initializing three-tool workflow...")
        self.bmf_tool = BMFFilterTool()
        self.form990_tool = Form990AnalysisTool()
        self.propublica_tool = ProPublicaEnrichmentTool()
        print("✅ All tools initialized successfully")

    async def execute_workflow(self, search_description: str, search_criteria: Dict[str, Any]) -> WorkflowResult:
        """
        Execute the complete three-tool workflow

        Args:
            search_description: Human-readable description of what we're looking for
            search_criteria: Dictionary containing search parameters

        Returns:
            WorkflowResult: Complete workflow results with opportunity dossiers
        """
        print(f"🚀 Starting Three-Tool Workflow: {search_description}")
        print("=" * 80)

        workflow_start = time.time()

        # Stage 1: BMF Filter - Organization Discovery
        print("📊 STAGE 1: BMF Organization Discovery")
        print("-" * 50)

        bmf_start = time.time()
        bmf_result = await self._execute_bmf_stage(search_criteria)
        bmf_time = (time.time() - bmf_start) * 1000

        print(f"✅ BMF Stage Results:")
        print(f"   Organizations found: {len(bmf_result.organizations)}")
        print(f"   Database records scanned: {bmf_result.summary.total_in_database:,}")
        print(f"   Stage time: {bmf_time:.1f}ms")

        if bmf_result.organizations:
            print(f"   Top organizations:")
            for i, org in enumerate(bmf_result.organizations[:3], 1):
                revenue = org.revenue or 0
                print(f"     {i}. {org.name} (EIN: {org.ein}) - ${revenue:,}")

        # Stage 2: Form 990 Analysis - Financial Intelligence
        print(f"\n💰 STAGE 2: Form 990 Financial Analysis")
        print("-" * 50)

        form990_start = time.time()
        form990_result = await self._execute_form990_stage(bmf_result.organizations)
        form990_time = (time.time() - form990_start) * 1000

        print(f"✅ Form 990 Stage Results:")
        print(f"   Organizations analyzed: {form990_result.total_organizations_analyzed}")
        print(f"   Stage time: {form990_time:.1f}ms")

        if form990_result.organizations:
            print(f"   Financial health summary:")
            for i, org in enumerate(form990_result.organizations[:3], 1):
                health = org.financial_health
                print(f"     {i}. {org.name}: {health.health_category.upper()} (Score: {health.overall_score:.1f})")

        # Stage 3: ProPublica Enrichment - Comprehensive Profiles
        print(f"\n🌐 STAGE 3: ProPublica API Enrichment")
        print("-" * 50)

        propublica_start = time.time()
        propublica_result = await self._execute_propublica_stage(form990_result.organizations)
        propublica_time = (time.time() - propublica_start) * 1000

        print(f"✅ ProPublica Stage Results:")
        print(f"   Organizations enriched: {propublica_result.organizations_processed}")
        print(f"   API calls made: {propublica_result.api_calls_made}")
        print(f"   Stage time: {propublica_time:.1f}ms")

        # Build Opportunity Dossiers
        print(f"\n📋 DOSSIER BUILDING: Combining All Data Sources")
        print("-" * 50)

        dossier_start = time.time()
        opportunity_dossiers = self._build_opportunity_dossiers(
            bmf_result.organizations,
            form990_result.organizations,
            propublica_result.enriched_organizations
        )
        dossier_time = (time.time() - dossier_start) * 1000

        print(f"✅ Dossier Building Results:")
        print(f"   Complete dossiers created: {len(opportunity_dossiers)}")
        print(f"   Dossier building time: {dossier_time:.1f}ms")

        # Calculate final metrics
        total_time = (time.time() - workflow_start) * 1000
        filter_efficiency = bmf_result.summary.total_in_database / len(bmf_result.organizations) if bmf_result.organizations else 0

        # Create workflow result
        result = WorkflowResult(
            opportunity_dossiers=opportunity_dossiers,
            total_execution_time_ms=total_time,
            bmf_stage_time_ms=bmf_time,
            form990_stage_time_ms=form990_time,
            propublica_stage_time_ms=propublica_time,
            organizations_bmf_found=len(bmf_result.organizations),
            organizations_990_analyzed=form990_result.total_organizations_analyzed,
            organizations_propublica_enriched=propublica_result.organizations_processed,
            overall_success_rate=len(opportunity_dossiers) / len(bmf_result.organizations) if bmf_result.organizations else 0,
            data_quality_score=self._calculate_overall_quality(opportunity_dossiers),
            filter_efficiency_ratio=filter_efficiency,
            workflow_configuration=self.config
        )

        # Final summary
        print(f"\n🎯 WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"Total execution time: {total_time:.1f}ms")
        print(f"Stage breakdown:")
        print(f"  BMF Filter: {bmf_time:.1f}ms ({bmf_time/total_time*100:.1f}%)")
        print(f"  990 Analysis: {form990_time:.1f}ms ({form990_time/total_time*100:.1f}%)")
        print(f"  ProPublica: {propublica_time:.1f}ms ({propublica_time/total_time*100:.1f}%)")
        print(f"Data flow: {bmf_result.summary.total_in_database:,} → {len(bmf_result.organizations)} → {form990_result.total_organizations_analyzed} → {propublica_result.organizations_processed}")
        print(f"Filter efficiency: {filter_efficiency:,.0f}:1 reduction")
        print(f"Complete dossiers: {len(opportunity_dossiers)}")
        print(f"Overall data quality: {result.data_quality_score:.2f}")

        print(f"\n🎉 Three-tool workflow completed successfully!")

        return result

    async def _execute_bmf_stage(self, search_criteria: Dict[str, Any]):
        """Execute BMF filter stage"""
        # Convert search criteria to BMF format
        try:
            # Import BMF types (simplified version for demo)
            @dataclass
            class SimpleBMFCriteria:
                states: List[str] = None
                ntee_codes: List[str] = None
                revenue_min: Optional[int] = None
                revenue_max: Optional[int] = None
                limit: int = 10
                sort_by: str = "revenue_desc"

            @dataclass
            class SimpleBMFIntent:
                what_youre_looking_for: str = ""
                criteria: SimpleBMFCriteria = None

            bmf_criteria = SimpleBMFCriteria(
                states=search_criteria.get('states', ['VA', 'MD']),
                ntee_codes=search_criteria.get('ntee_codes', ['P20', 'B25']),
                revenue_min=search_criteria.get('revenue_min', 500000),
                limit=self.config.bmf_max_results,
                sort_by=self.config.bmf_sort_by
            )

            bmf_intent = SimpleBMFIntent(
                what_youre_looking_for=search_criteria.get('description', 'Organizations matching criteria'),
                criteria=bmf_criteria
            )

            return await self.bmf_tool.execute(bmf_intent)
        except Exception as e:
            print(f"❌ BMF stage failed: {e}")
            # Return mock result for demonstration
            @dataclass
            class MockBMFResult:
                organizations: List = None
                summary: Any = None

                def __post_init__(self):
                    if self.organizations is None:
                        self.organizations = []
                    if self.summary is None:
                        @dataclass
                        class MockSummary:
                            total_in_database: int = 700000
                        self.summary = MockSummary()

            return MockBMFResult()

    async def _execute_form990_stage(self, bmf_organizations: List):
        """Execute Form 990 analysis stage"""
        if not bmf_organizations:
            # Return empty result
            return form990_analyzer.Form990AnalysisResult(
                organizations=[],
                execution_time_ms=0,
                total_organizations_analyzed=0,
                analysis_period="2022-2024"
            )

        # Extract EINs from BMF results
        target_eins = []
        for org in bmf_organizations[:self.config.form990_max_organizations]:
            if hasattr(org, 'ein'):
                target_eins.append(org.ein)

        if not target_eins:
            print("⚠️ No EINs found in BMF results for 990 analysis")
            return form990_analyzer.Form990AnalysisResult(
                organizations=[],
                execution_time_ms=0,
                total_organizations_analyzed=0,
                analysis_period="2022-2024"
            )

        criteria = Form990AnalysisCriteria(
            target_eins=target_eins,
            years_to_analyze=self.config.form990_years_to_analyze,
            financial_health_analysis=True,
            grant_capacity_analysis=True
        )

        return await self.form990_tool.execute(criteria)

    async def _execute_propublica_stage(self, form990_organizations: List):
        """Execute ProPublica enrichment stage"""
        if not form990_organizations:
            return propublica_enricher.ProPublicaEnrichmentResult(
                enriched_organizations=[],
                execution_time_ms=0,
                api_calls_made=0,
                cache_hit_rate=0.0,
                organizations_processed=0,
                enrichment_success_rate=0.0
            )

        # Select highest-scoring organizations for ProPublica enrichment
        scored_orgs = []
        for org in form990_organizations:
            if hasattr(org, 'financial_health') and hasattr(org.financial_health, 'overall_score'):
                if org.financial_health.overall_score >= self.config.quality_threshold * 100:
                    scored_orgs.append(org)

        # Take top organizations
        target_eins = [org.ein for org in scored_orgs[:self.config.propublica_max_organizations]]

        if not target_eins:
            print("⚠️ No organizations meet quality threshold for ProPublica enrichment")
            return propublica_enricher.ProPublicaEnrichmentResult(
                enriched_organizations=[],
                execution_time_ms=0,
                api_calls_made=0,
                cache_hit_rate=0.0,
                organizations_processed=0,
                enrichment_success_rate=0.0
            )

        criteria = ProPublicaEnrichmentCriteria(
            target_eins=target_eins,
            enrichment_depth=self.config.propublica_enrichment_depth,
            include_filing_history=True,
            include_peer_analysis=self.config.propublica_include_peers,
            include_leadership_details=True
        )

        return await self.propublica_tool.execute(criteria)

    def _build_opportunity_dossiers(self, bmf_orgs: List, form990_orgs: List, propublica_orgs: List) -> List[OpportunityDossier]:
        """Build complete opportunity dossiers combining all three data sources"""
        dossiers = []

        # Create mapping by EIN for easy lookup
        form990_map = {org.ein: org for org in form990_orgs if hasattr(org, 'ein')}
        propublica_map = {org.ein: org for org in propublica_orgs if hasattr(org, 'ein')}

        for bmf_org in bmf_orgs:
            if not hasattr(bmf_org, 'ein'):
                continue

            ein = bmf_org.ein
            stages_completed = ['bmf']

            # Get Form 990 data if available
            form990_data = None
            financial_health_score = 0.0
            financial_health_category = "unknown"

            if ein in form990_map:
                stages_completed.append('form990')
                form990_org = form990_map[ein]
                form990_data = {
                    'latest_year': getattr(form990_org, 'latest_year', None),
                    'financial_years': len(getattr(form990_org, 'financial_years', [])),
                    'data_quality_score': getattr(form990_org, 'data_quality_score', 0.0)
                }

                if hasattr(form990_org, 'financial_health'):
                    financial_health_score = form990_org.financial_health.overall_score
                    financial_health_category = form990_org.financial_health.health_category

            # Get ProPublica data if available
            propublica_data = None
            peer_organizations = []
            data_completeness_score = 0.0

            if ein in propublica_map:
                stages_completed.append('propublica')
                propublica_org = propublica_map[ein]
                propublica_data = {
                    'organization_type': getattr(propublica_org, 'organization_type', 'unknown'),
                    'filing_records': len(getattr(propublica_org, 'filing_records', [])),
                    'leadership_members': len(getattr(propublica_org, 'leadership_members', []))
                }

                peer_organizations = [
                    {
                        'ein': peer.ein,
                        'name': peer.name,
                        'similarity_score': peer.similarity_score
                    }
                    for peer in getattr(propublica_org, 'peer_organizations', [])
                ]

                data_completeness_score = getattr(propublica_org, 'data_completeness_score', 0.0)

            # Create dossier
            dossier = OpportunityDossier(
                ein=ein,
                name=getattr(bmf_org, 'name', f'Organization-{ein}'),
                bmf_data={
                    'state': getattr(bmf_org, 'state', ''),
                    'ntee_code': getattr(bmf_org, 'ntee_code', ''),
                    'revenue': getattr(bmf_org, 'revenue', 0)
                },
                bmf_match_score=getattr(bmf_org, 'match_score', 0.0),
                bmf_match_reasons=getattr(bmf_org, 'match_reasons', []),
                form990_data=form990_data,
                financial_health_score=financial_health_score,
                financial_health_category=financial_health_category,
                propublica_data=propublica_data,
                peer_organizations=peer_organizations,
                data_completeness_score=data_completeness_score,
                processing_stages_completed=stages_completed,
                workflow_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

            dossiers.append(dossier)

        return dossiers

    def _calculate_overall_quality(self, dossiers: List[OpportunityDossier]) -> float:
        """Calculate overall data quality score across all dossiers"""
        if not dossiers:
            return 0.0

        total_quality = 0.0
        for dossier in dossiers:
            # Quality based on stages completed and data completeness
            stage_score = len(dossier.processing_stages_completed) / 3.0  # 3 total stages
            completeness_score = dossier.data_completeness_score
            dossier_quality = (stage_score + completeness_score) / 2.0
            total_quality += dossier_quality

        return total_quality / len(dossiers)


# Example usage and testing
async def test_three_tool_workflow():
    """Test the complete three-tool workflow"""

    print("🧪 Testing Three-Tool Workflow Orchestrator")
    print("=" * 80)

    # Create workflow configuration
    config = WorkflowConfiguration(
        bmf_max_results=5,
        form990_max_organizations=5,
        propublica_max_organizations=3,
        quality_threshold=0.5
    )

    # Initialize orchestrator
    orchestrator = ThreeToolWorkflowOrchestrator(config)

    # Define search criteria
    search_description = "Large healthcare and education organizations in Virginia and Maryland"
    search_criteria = {
        'description': search_description,
        'states': ['VA', 'MD'],
        'ntee_codes': ['P20', 'B25'],  # Education and Health
        'revenue_min': 1000000  # $1M+ organizations
    }

    # Execute workflow
    result = await orchestrator.execute_workflow(search_description, search_criteria)

    # Display detailed results
    print(f"\n📊 DETAILED RESULTS")
    print("=" * 80)

    for i, dossier in enumerate(result.opportunity_dossiers, 1):
        print(f"\n{i}. {dossier.name} (EIN: {dossier.ein})")
        print(f"   Stages completed: {' → '.join(dossier.processing_stages_completed)}")
        print(f"   Financial health: {dossier.financial_health_category} (Score: {dossier.financial_health_score:.1f})")
        print(f"   Data completeness: {dossier.data_completeness_score:.2f}")

        if dossier.bmf_data:
            bmf = dossier.bmf_data
            print(f"   BMF: {bmf['state']}, {bmf['ntee_code']}, Revenue: ${bmf['revenue']:,}")

        if dossier.peer_organizations:
            print(f"   Peers found: {len(dossier.peer_organizations)}")

    print(f"\n✅ Three-tool workflow test completed successfully!")
    return result


if __name__ == "__main__":
    asyncio.run(test_three_tool_workflow())
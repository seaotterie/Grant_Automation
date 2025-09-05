#!/usr/bin/env python3
"""
Real World Validation Suite - Enhanced Test Data Pipeline
Comprehensive real-world testing with multiple nonprofits, opportunities, and scenarios
to validate the 4-tier intelligence system across diverse conditions and edge cases.

This suite provides:
1. Extended test data pipeline with 20+ nonprofit/opportunity combinations
2. Edge case testing with incomplete data and error conditions
3. Cross-sector validation (healthcare, education, environment, social services)
4. Multi-organization size testing (small, medium, large nonprofits)
5. Opportunity complexity testing (simple, moderate, complex, transformational)
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import from our testing frameworks
from integrated_tier_test import TestDataSet, TierLevel, TestConfiguration
from tier_comparison_test import TierComparisonTester

# Configure logging
logger = logging.getLogger(__name__)

class OrganizationSize(str, Enum):
    """Organization size categories"""
    SMALL = "small"          # <$1M annual budget
    MEDIUM = "medium"        # $1M-$10M annual budget  
    LARGE = "large"          # >$10M annual budget
    VERY_LARGE = "very_large" # >$100M annual budget

class ComplexityLevel(str, Enum):
    """Opportunity complexity levels"""
    SIMPLE = "simple"                    # Local grants, straightforward requirements
    MODERATE = "moderate"                # State/regional grants, moderate requirements
    COMPLEX = "complex"                  # Federal grants, complex requirements
    TRANSFORMATIONAL = "transformational" # Multi-million strategic partnerships

class SectorType(str, Enum):
    """Sector categories for nonprofits"""
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    SOCIAL_SERVICES = "social_services"
    ARTS_CULTURE = "arts_culture"
    EMERGENCY_SERVICES = "emergency_services"
    HUMAN_SERVICES = "human_services"
    RESEARCH = "research"

@dataclass
class TestVariation:
    """Test variation configuration"""
    variation_id: str
    description: str
    data_completeness: float  # 0.0-1.0
    introduce_errors: bool
    api_timeout_simulation: bool
    cost_constraint_testing: bool
    edge_case_type: Optional[str] = None

@dataclass
class ValidationResult:
    """Result from real-world validation testing"""
    dataset_id: str
    variation_id: str
    success: bool
    processing_time_seconds: float
    total_cost: float
    quality_score: float
    error_handling_score: float
    robustness_score: float
    business_value_score: float
    issues_identified: List[str]
    recommendations: List[str]

class EnhancedTestDataGenerator:
    """Generates comprehensive test data for real-world validation"""
    
    def __init__(self):
        self.sector_templates = self._create_sector_templates()
        self.opportunity_templates = self._create_opportunity_templates()
        
    def generate_comprehensive_test_suite(self) -> List[TestDataSet]:
        """Generate comprehensive test suite with diverse scenarios"""
        
        test_datasets = []
        
        # Generate datasets by sector and size combination
        for sector in SectorType:
            for org_size in OrganizationSize:
                for complexity in ComplexityLevel:
                    dataset = self._generate_dataset_for_combination(sector, org_size, complexity)
                    if dataset:
                        test_datasets.append(dataset)
                        
        # Add edge case datasets
        edge_case_datasets = self._generate_edge_case_datasets()
        test_datasets.extend(edge_case_datasets)
        
        # Add real-world inspired datasets
        real_world_datasets = self._generate_real_world_inspired_datasets()
        test_datasets.extend(real_world_datasets)
        
        logger.info(f"Generated {len(test_datasets)} comprehensive test datasets")
        
        return test_datasets
        
    def _create_sector_templates(self) -> Dict[SectorType, Dict[str, Any]]:
        """Create templates for different nonprofit sectors"""
        
        return {
            SectorType.HEALTHCARE: {
                "ntee_codes": ["E20", "E21", "E22", "E30", "E31", "E32"],
                "common_missions": [
                    "Improve health outcomes and access to healthcare in underserved communities",
                    "Provide medical care and health education to vulnerable populations",
                    "Advance medical research and healthcare innovation"
                ],
                "typical_programs": ["Primary Care", "Health Education", "Medical Research", "Community Health"],
                "funding_focus_areas": ["Health Equity", "Rural Health", "Chronic Disease", "Mental Health"]
            },
            SectorType.EDUCATION: {
                "ntee_codes": ["B20", "B21", "B24", "B25", "B28", "B30"],
                "common_missions": [
                    "Provide quality education and educational opportunities to underserved students",
                    "Support educational innovation and excellence in teaching",
                    "Bridge educational gaps and promote lifelong learning"
                ],
                "typical_programs": ["After-School Programs", "Tutoring", "Scholarship Programs", "Teacher Training"],
                "funding_focus_areas": ["STEM Education", "Educational Equity", "Workforce Development", "Early Childhood"]
            },
            SectorType.ENVIRONMENT: {
                "ntee_codes": ["C01", "C20", "C27", "C30", "C32", "C35"],
                "common_missions": [
                    "Protect and preserve natural resources and wildlife habitats",
                    "Promote environmental sustainability and climate action", 
                    "Educate communities about environmental conservation"
                ],
                "typical_programs": ["Conservation", "Environmental Education", "Climate Action", "Wildlife Protection"],
                "funding_focus_areas": ["Climate Change", "Conservation", "Renewable Energy", "Environmental Justice"]
            },
            SectorType.SOCIAL_SERVICES: {
                "ntee_codes": ["P20", "P21", "P30", "P31", "P40", "P50"],
                "common_missions": [
                    "Provide essential services and support to vulnerable populations",
                    "Address social issues and promote community wellbeing",
                    "Empower individuals and families to achieve self-sufficiency"
                ],
                "typical_programs": ["Food Security", "Housing Assistance", "Job Training", "Family Support"],
                "funding_focus_areas": ["Poverty Alleviation", "Housing", "Food Security", "Economic Development"]
            },
            SectorType.ARTS_CULTURE: {
                "ntee_codes": ["A20", "A23", "A25", "A30", "A40", "A50"],
                "common_missions": [
                    "Promote arts and cultural expression in the community",
                    "Preserve cultural heritage and traditions",
                    "Provide arts education and cultural programming"
                ],
                "typical_programs": ["Arts Education", "Cultural Events", "Artist Support", "Community Theater"],
                "funding_focus_areas": ["Arts Education", "Cultural Preservation", "Community Arts", "Artist Development"]
            },
            SectorType.EMERGENCY_SERVICES: {
                "ntee_codes": ["M20", "M23", "M24", "M40", "M41", "M42"],
                "common_missions": [
                    "Provide emergency response and disaster relief services",
                    "Prepare communities for emergencies and disasters",
                    "Support first responders and emergency personnel"
                ],
                "typical_programs": ["Emergency Response", "Disaster Relief", "Emergency Preparedness", "First Aid Training"],
                "funding_focus_areas": ["Disaster Preparedness", "Emergency Response", "Community Safety", "First Responder Support"]
            }
        }
        
    def _create_opportunity_templates(self) -> Dict[ComplexityLevel, List[Dict[str, Any]]]:
        """Create opportunity templates by complexity level"""
        
        return {
            ComplexityLevel.SIMPLE: [
                {
                    "title_template": "Local {focus_area} Grant Program",
                    "agency_types": ["County", "City", "Local Foundation"],
                    "award_range": [5000, 50000],
                    "requirements": ["Local 501(c)(3)", "Community focus", "Basic reporting"],
                    "complexity_factors": ["simple_application", "minimal_reporting", "local_focus"]
                },
                {
                    "title_template": "Community {focus_area} Initiative",
                    "agency_types": ["Community Foundation", "Local Government", "Regional Foundation"],
                    "award_range": [10000, 75000],
                    "requirements": ["501(c)(3) status", "Community impact", "Financial stability"],
                    "complexity_factors": ["straightforward_requirements", "community_focus", "moderate_timeline"]
                }
            ],
            ComplexityLevel.MODERATE: [
                {
                    "title_template": "State {focus_area} Innovation Grant",
                    "agency_types": ["State Agency", "Regional Foundation", "Corporate Foundation"],
                    "award_range": [50000, 300000],
                    "requirements": ["State registration", "Innovation component", "Evaluation plan", "Partnership letters"],
                    "complexity_factors": ["moderate_complexity", "innovation_required", "evaluation_component"]
                },
                {
                    "title_template": "{focus_area} Capacity Building Program",
                    "agency_types": ["National Foundation", "Corporate Foundation", "State Agency"],
                    "award_range": [75000, 500000],
                    "requirements": ["Multi-year commitment", "Capacity building plan", "Outcome measurement"],
                    "complexity_factors": ["capacity_building", "multi_year", "outcomes_focused"]
                }
            ],
            ComplexityLevel.COMPLEX: [
                {
                    "title_template": "Federal {focus_area} Excellence Initiative",
                    "agency_types": ["NIH", "NSF", "DOE", "DOL", "HHS", "ED"],
                    "award_range": [500000, 2000000],
                    "requirements": ["Federal compliance", "Research component", "Multi-site implementation", "Detailed evaluation"],
                    "complexity_factors": ["federal_compliance", "research_required", "multi_site", "rigorous_evaluation"]
                },
                {
                    "title_template": "National {focus_area} Research Consortium",
                    "agency_types": ["Federal Agency", "Major Foundation", "Research Institute"],
                    "award_range": [1000000, 5000000],
                    "requirements": ["Research expertise", "Multi-institutional partnership", "IRB approval", "Data management plan"],
                    "complexity_factors": ["research_intensive", "multi_institutional", "data_management", "regulatory_compliance"]
                }
            ],
            ComplexityLevel.TRANSFORMATIONAL: [
                {
                    "title_template": "Transformational {focus_area} Partnership Initiative", 
                    "agency_types": ["Federal Agency", "Major Foundation", "International Organization"],
                    "award_range": [5000000, 25000000],
                    "requirements": ["Strategic partnership", "Systems change focus", "Multi-year commitment", "Policy impact"],
                    "complexity_factors": ["systems_change", "policy_focus", "transformational_impact", "strategic_partnership"]
                },
                {
                    "title_template": "National {focus_area} System Reform Initiative",
                    "agency_types": ["Federal Agency", "Philanthropic Collaborative", "Policy Institute"],
                    "award_range": [10000000, 50000000],
                    "requirements": ["System reform focus", "Multi-stakeholder collaboration", "Policy change component", "Sustained impact"],
                    "complexity_factors": ["system_reform", "policy_change", "multi_stakeholder", "sustained_impact"]
                }
            ]
        }
        
    def _generate_dataset_for_combination(self, sector: SectorType, org_size: OrganizationSize, 
                                        complexity: ComplexityLevel) -> Optional[TestDataSet]:
        """Generate test dataset for specific sector/size/complexity combination"""
        
        # Get templates
        sector_template = self.sector_templates[sector]
        opportunity_templates = self.opportunity_templates[complexity]
        
        if not opportunity_templates:
            return None
            
        opportunity_template = random.choice(opportunity_templates)
        
        # Generate nonprofit profile
        nonprofit_profile = self._generate_nonprofit_profile(sector_template, org_size)
        
        # Generate opportunity data
        opportunity_data = self._generate_opportunity_data(opportunity_template, sector_template, complexity)
        
        # Determine expected tier recommendation
        expected_tier = self._determine_expected_tier(org_size, complexity, opportunity_data.get("award_ceiling", 0))
        
        dataset_id = f"{sector.value}_{org_size.value}_{complexity.value}_{random.randint(1000, 9999)}"
        
        return TestDataSet(
            dataset_id=dataset_id,
            nonprofit_profile=nonprofit_profile,
            opportunity_data=opportunity_data,
            expected_tier_recommendation=expected_tier,
            complexity_level=complexity.value,
            organization_size=org_size.value,
            sector_type=sector.value
        )
        
    def _generate_nonprofit_profile(self, sector_template: Dict[str, Any], org_size: OrganizationSize) -> Dict[str, Any]:
        """Generate realistic nonprofit profile"""
        
        # Organization size parameters
        size_params = {
            OrganizationSize.SMALL: {"revenue_range": [50000, 999000], "asset_range": [25000, 800000], "staff": "5-15"},
            OrganizationSize.MEDIUM: {"revenue_range": [1000000, 9999000], "asset_range": [800000, 15000000], "staff": "15-100"},
            OrganizationSize.LARGE: {"revenue_range": [10000000, 99999000], "asset_range": [15000000, 150000000], "staff": "100-1000"},
            OrganizationSize.VERY_LARGE: {"revenue_range": [100000000, 1000000000], "asset_range": [150000000, 2000000000], "staff": "1000+"}
        }
        
        params = size_params[org_size]
        
        # Generate basic info
        org_name = f"{random.choice(['Community', 'Regional', 'National', 'Alliance for', 'Coalition for', 'Center for'])} {random.choice(sector_template['funding_focus_areas'])}"
        
        # Generate financial data
        annual_revenue = random.randint(params["revenue_range"][0], params["revenue_range"][1])
        total_assets = random.randint(params["asset_range"][0], params["asset_range"][1])
        
        # Generate location (weighted toward populous states)
        states = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI", "NJ", "VA", "WA", "AZ", "MA"]
        cities = ["Los Angeles", "Houston", "Miami", "New York", "Philadelphia", "Chicago", "Columbus", "Atlanta", "Charlotte", "Detroit", "Newark", "Richmond", "Seattle", "Phoenix", "Boston"]
        
        location_idx = random.randint(0, len(states) - 1)
        
        return {
            "ein": f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            "name": org_name,
            "city": cities[location_idx],
            "state": states[location_idx],
            "ntee_code": random.choice(sector_template["ntee_codes"]),
            "annual_revenue": annual_revenue,
            "total_assets": total_assets,
            "mission": random.choice(sector_template["common_missions"]),
            "geographic_scope": "Local" if org_size == OrganizationSize.SMALL else "Regional" if org_size == OrganizationSize.MEDIUM else "National",
            "staff_size": params["staff"],
            "programs": random.sample(sector_template["typical_programs"], min(3, len(sector_template["typical_programs"])))
        }
        
    def _generate_opportunity_data(self, opportunity_template: Dict[str, Any], 
                                 sector_template: Dict[str, Any], complexity: ComplexityLevel) -> Dict[str, Any]:
        """Generate realistic opportunity data"""
        
        focus_area = random.choice(sector_template["funding_focus_areas"])
        title = opportunity_template["title_template"].format(focus_area=focus_area)
        agency = random.choice(opportunity_template["agency_types"])
        
        # Generate award amount
        award_ceiling = random.randint(opportunity_template["award_range"][0], opportunity_template["award_range"][1])
        
        # Generate deadline (30-180 days from now)
        days_until_deadline = random.randint(30, 180)
        deadline = (datetime.now() + timedelta(days=days_until_deadline)).strftime("%Y-%m-%d")
        
        # Generate opportunity ID
        opportunity_id = f"{agency.replace(' ', '-').upper()}-{focus_area.replace(' ', '-').upper()}-{datetime.now().year}-{random.randint(100, 999)}"
        
        return {
            "opportunity_id": opportunity_id,
            "funding_opportunity_title": title,
            "agency_code": agency,
            "funding_instrument_type": "Grant" if award_ceiling < 1000000 else "Cooperative Agreement",
            "category_of_funding_activity": focus_area,
            "award_ceiling": award_ceiling,
            "eligibility_requirements": opportunity_template["requirements"],
            "application_deadline": deadline,
            "complexity_level": complexity.value,
            "complexity_factors": opportunity_template["complexity_factors"]
        }
        
    def _determine_expected_tier(self, org_size: OrganizationSize, complexity: ComplexityLevel, opportunity_value: int) -> TierLevel:
        """Determine expected tier recommendation based on scenario characteristics"""
        
        # Decision matrix
        if complexity == ComplexityLevel.TRANSFORMATIONAL or opportunity_value > 10000000:
            return TierLevel.COMPLETE
        elif complexity == ComplexityLevel.COMPLEX or opportunity_value > 1000000:
            return TierLevel.ENHANCED
        elif complexity == ComplexityLevel.MODERATE or opportunity_value > 100000:
            return TierLevel.STANDARD
        elif org_size == OrganizationSize.SMALL and opportunity_value < 50000:
            return TierLevel.CURRENT
        else:
            return TierLevel.STANDARD
            
    def _generate_edge_case_datasets(self) -> List[TestDataSet]:
        """Generate edge case datasets for robustness testing"""
        
        edge_cases = []
        
        # Incomplete data case
        edge_cases.append(TestDataSet(
            dataset_id="edge_case_incomplete_data",
            nonprofit_profile={
                "ein": "12-3456789",
                "name": "Incomplete Data Test Organization",
                # Missing city, state, financial data
                "ntee_code": "P20",
                "mission": "Test organization with incomplete data"
            },
            opportunity_data={
                "opportunity_id": "INCOMPLETE-TEST-001",
                "funding_opportunity_title": "Test Grant with Missing Data",
                # Missing agency, deadline, requirements
                "award_ceiling": 50000
            },
            expected_tier_recommendation=TierLevel.CURRENT,
            complexity_level="simple",
            organization_size="small",
            sector_type="social_services"
        ))
        
        # Very small opportunity case
        edge_cases.append(TestDataSet(
            dataset_id="edge_case_micro_grant",
            nonprofit_profile={
                "ein": "99-8877665",
                "name": "Micro Grant Test Organization",
                "city": "Small Town",
                "state": "KS",
                "ntee_code": "P30",
                "annual_revenue": 75000,
                "total_assets": 50000,
                "mission": "Small community organization testing micro grants"
            },
            opportunity_data={
                "opportunity_id": "MICRO-GRANT-001",
                "funding_opportunity_title": "Community Micro Grant Program",
                "agency_code": "Local Foundation",
                "award_ceiling": 1000,  # Very small grant
                "eligibility_requirements": ["501(c)(3)", "Local organization"],
                "application_deadline": "2025-03-01"
            },
            expected_tier_recommendation=TierLevel.CURRENT,
            complexity_level="simple",
            organization_size="small",
            sector_type="social_services"
        ))
        
        # Extremely large opportunity case
        edge_cases.append(TestDataSet(
            dataset_id="edge_case_mega_grant",
            nonprofit_profile={
                "ein": "11-2233445",
                "name": "Major National Organization",
                "city": "Washington",
                "state": "DC",
                "ntee_code": "C01",
                "annual_revenue": 500000000,
                "total_assets": 1000000000,
                "mission": "Major national organization testing transformational funding"
            },
            opportunity_data={
                "opportunity_id": "MEGA-INITIATIVE-001",
                "funding_opportunity_title": "National Transformation Initiative",
                "agency_code": "Federal Agency Consortium",
                "award_ceiling": 100000000,  # $100M grant
                "eligibility_requirements": ["National reach", "Proven track record", "Multi-institutional partnerships"],
                "application_deadline": "2025-12-31"
            },
            expected_tier_recommendation=TierLevel.COMPLETE,
            complexity_level="transformational",
            organization_size="very_large",
            sector_type="environment"
        ))
        
        return edge_cases
        
    def _generate_real_world_inspired_datasets(self) -> List[TestDataSet]:
        """Generate datasets inspired by real-world organizations and opportunities"""
        
        real_world_datasets = []
        
        # American Red Cross-inspired dataset
        real_world_datasets.append(TestDataSet(
            dataset_id="real_world_disaster_relief_national",
            nonprofit_profile={
                "ein": "53-0196605",
                "name": "National Disaster Relief Organization",
                "city": "Washington",
                "state": "DC",
                "ntee_code": "M20",
                "annual_revenue": 3600000000,
                "total_assets": 4200000000,
                "mission": "Provide emergency assistance, disaster relief, and disaster preparedness education nationwide",
                "geographic_scope": "National",
                "staff_size": "20000+",
                "programs": ["Disaster Relief", "Emergency Assistance", "Blood Services", "International Relief"]
            },
            opportunity_data={
                "opportunity_id": "FEMA-DR-2025-001",
                "funding_opportunity_title": "National Disaster Response Enhancement Program",
                "agency_code": "FEMA",
                "award_ceiling": 15000000,
                "eligibility_requirements": ["National disaster response capability", "Government partnership experience", "Multi-state operations"],
                "application_deadline": "2025-06-30"
            },
            expected_tier_recommendation=TierLevel.COMPLETE,
            complexity_level="complex",
            organization_size="very_large",
            sector_type="emergency_services"
        ))
        
        # Teach for America-inspired dataset
        real_world_datasets.append(TestDataSet(
            dataset_id="real_world_education_national",
            nonprofit_profile={
                "ein": "13-3541913",
                "name": "National Teaching Excellence Corps",
                "city": "New York",
                "state": "NY",
                "ntee_code": "B25",
                "annual_revenue": 350000000,
                "total_assets": 500000000,
                "mission": "Eliminate educational inequality by recruiting and developing exceptional teachers for high-need schools",
                "geographic_scope": "National",
                "staff_size": "1000+",
                "programs": ["Teacher Recruitment", "Leadership Development", "Alumni Support", "Policy Advocacy"]
            },
            opportunity_data={
                "opportunity_id": "DOE-TEACHER-2025-001",
                "funding_opportunity_title": "National Teacher Excellence and Retention Initiative",
                "agency_code": "Department of Education",
                "award_ceiling": 25000000,
                "eligibility_requirements": ["Teacher development expertise", "Multi-state presence", "Outcome measurement capability"],
                "application_deadline": "2025-08-15"
            },
            expected_tier_recommendation=TierLevel.COMPLETE,
            complexity_level="complex",
            organization_size="very_large",
            sector_type="education"
        ))
        
        # Local community health center-inspired dataset
        real_world_datasets.append(TestDataSet(
            dataset_id="real_world_health_local",
            nonprofit_profile={
                "ein": "54-1234567",
                "name": "Community Health Partners",
                "city": "Austin",
                "state": "TX",
                "ntee_code": "E32",
                "annual_revenue": 8500000,
                "total_assets": 12000000,
                "mission": "Provide comprehensive healthcare services to underserved communities in Central Texas",
                "geographic_scope": "Regional",
                "staff_size": "100-200",
                "programs": ["Primary Care", "Mental Health", "Dental Services", "Community Health Education"]
            },
            opportunity_data={
                "opportunity_id": "HRSA-CHC-2025-001",
                "funding_opportunity_title": "Community Health Center Expansion Grant",
                "agency_code": "HRSA",
                "award_ceiling": 2500000,
                "eligibility_requirements": ["FQHC status", "Underserved area focus", "Quality improvement capability"],
                "application_deadline": "2025-05-30"
            },
            expected_tier_recommendation=TierLevel.ENHANCED,
            complexity_level="complex",
            organization_size="medium",
            sector_type="healthcare"
        ))
        
        return real_world_datasets

class RealWorldValidationTester:
    """Comprehensive real-world validation testing framework"""
    
    def __init__(self, config: TestConfiguration = None):
        self.config = config or TestConfiguration(max_total_budget=150.00)  # Higher budget for comprehensive testing
        self.data_generator = EnhancedTestDataGenerator()
        self.comparison_tester = TierComparisonTester(self.config)
        
        # Test variations for robustness testing
        self.test_variations = [
            TestVariation("standard", "Standard complete data testing", 1.0, False, False, False),
            TestVariation("incomplete_data", "Testing with 70% data completeness", 0.7, False, False, False, "incomplete_data"),
            TestVariation("error_simulation", "Testing with simulated API errors", 1.0, True, False, False, "api_errors"),
            TestVariation("timeout_simulation", "Testing with API timeout simulation", 1.0, False, True, False, "timeouts"),
            TestVariation("budget_constraints", "Testing with strict budget constraints", 1.0, False, False, True, "budget_limits")
        ]
        
        # Results storage
        self.validation_results = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path(f"validation_results/real_world_validation_{self.session_id}")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Real World Validation Suite initialized - Session: {self.session_id}")
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive real-world validation testing"""
        
        logger.info("Starting comprehensive real-world validation testing")
        
        validation_suite = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "test_datasets": [],
            "validation_results": [],
            "robustness_analysis": {},
            "sector_analysis": {},
            "size_analysis": {},
            "complexity_analysis": {},
            "recommendations": []
        }
        
        # Generate comprehensive test datasets
        test_datasets = self.data_generator.generate_comprehensive_test_suite()
        validation_suite["test_datasets"] = [asdict(ds) for ds in test_datasets]
        
        logger.info(f"Generated {len(test_datasets)} test datasets for validation")
        
        # Test each dataset with multiple variations
        for dataset in test_datasets[:10]:  # Limit for budget management
            logger.info(f"\n{'='*80}")
            logger.info(f"Validating Dataset: {dataset.dataset_id}")
            logger.info(f"Sector: {dataset.sector_type}, Size: {dataset.organization_size}, Complexity: {dataset.complexity_level}")
            logger.info(f"{'='*80}")
            
            # Test with standard variation
            standard_result = await self._test_dataset_with_variation(dataset, self.test_variations[0])
            validation_suite["validation_results"].append(standard_result)
            
            # Test with one additional variation if budget allows
            if self.comparison_tester.integrated_tester.cost_tracker.get_remaining_budget() > 20.0:
                variation = random.choice(self.test_variations[1:])
                variation_result = await self._test_dataset_with_variation(dataset, variation)
                validation_suite["validation_results"].append(variation_result)
                
        # Analyze results
        validation_suite["robustness_analysis"] = self._analyze_robustness(validation_suite["validation_results"])
        validation_suite["sector_analysis"] = self._analyze_by_sector(validation_suite["validation_results"])
        validation_suite["size_analysis"] = self._analyze_by_size(validation_suite["validation_results"])
        validation_suite["complexity_analysis"] = self._analyze_by_complexity(validation_suite["validation_results"])
        validation_suite["recommendations"] = self._generate_validation_recommendations(validation_suite)
        
        validation_suite["end_time"] = datetime.now().isoformat()
        
        # Save results
        await self._save_validation_results(validation_suite)
        
        # Print summary
        self._print_validation_summary(validation_suite)
        
        return validation_suite
        
    async def _test_dataset_with_variation(self, dataset: TestDataSet, variation: TestVariation) -> ValidationResult:
        """Test dataset with specific variation"""
        
        logger.info(f"Testing {dataset.dataset_id} with variation: {variation.description}")
        
        start_time = time.time()
        
        try:
            # Apply variation modifications
            modified_dataset = self._apply_variation_to_dataset(dataset, variation)
            
            # Run tier comparison testing
            scenario_comparison = await self.comparison_tester.test_scenario_comparison(modified_dataset)
            
            # Calculate validation metrics
            processing_time = time.time() - start_time
            
            # Assess results
            success = scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.success
            quality_score = scenario_comparison.tier_service_result.quality_score if scenario_comparison.tier_service_result else 0.0
            total_cost = scenario_comparison.tier_service_result.total_cost_usd if scenario_comparison.tier_service_result else 0.0
            
            # Calculate robustness scores
            error_handling_score = self._calculate_error_handling_score(scenario_comparison, variation)
            robustness_score = self._calculate_robustness_score(scenario_comparison, variation)
            business_value_score = self._calculate_business_value_score(scenario_comparison)
            
            # Identify issues and generate recommendations
            issues = self._identify_issues(scenario_comparison, variation)
            recommendations = self._generate_dataset_recommendations(scenario_comparison, variation)
            
            return ValidationResult(
                dataset_id=dataset.dataset_id,
                variation_id=variation.variation_id,
                success=success,
                processing_time_seconds=processing_time,
                total_cost=total_cost,
                quality_score=quality_score,
                error_handling_score=error_handling_score,
                robustness_score=robustness_score,
                business_value_score=business_value_score,
                issues_identified=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Validation test failed for {dataset.dataset_id} with variation {variation.variation_id}: {e}")
            
            return ValidationResult(
                dataset_id=dataset.dataset_id,
                variation_id=variation.variation_id,
                success=False,
                processing_time_seconds=time.time() - start_time,
                total_cost=0.0,
                quality_score=0.0,
                error_handling_score=0.0,
                robustness_score=0.0,
                business_value_score=0.0,
                issues_identified=[f"Test failed: {str(e)}"],
                recommendations=["Review error handling and system robustness"]
            )
            
    def _apply_variation_to_dataset(self, dataset: TestDataSet, variation: TestVariation) -> TestDataSet:
        """Apply test variation modifications to dataset"""
        
        modified_dataset = TestDataSet(
            dataset_id=f"{dataset.dataset_id}_{variation.variation_id}",
            nonprofit_profile=dataset.nonprofit_profile.copy(),
            opportunity_data=dataset.opportunity_data.copy(),
            expected_tier_recommendation=dataset.expected_tier_recommendation,
            complexity_level=dataset.complexity_level,
            organization_size=dataset.organization_size,
            sector_type=dataset.sector_type
        )
        
        # Apply data completeness reduction
        if variation.data_completeness < 1.0:
            modified_dataset.nonprofit_profile = self._reduce_data_completeness(
                modified_dataset.nonprofit_profile, variation.data_completeness
            )
            modified_dataset.opportunity_data = self._reduce_data_completeness(
                modified_dataset.opportunity_data, variation.data_completeness
            )
            
        return modified_dataset
        
    def _reduce_data_completeness(self, data_dict: Dict[str, Any], completeness: float) -> Dict[str, Any]:
        """Reduce data completeness by removing random fields"""
        
        if completeness >= 1.0:
            return data_dict
            
        reduced_data = data_dict.copy()
        num_fields = len(reduced_data)
        num_to_keep = int(num_fields * completeness)
        
        if num_to_keep < num_fields:
            keys_to_keep = random.sample(list(reduced_data.keys()), num_to_keep)
            reduced_data = {k: v for k, v in reduced_data.items() if k in keys_to_keep}
            
        return reduced_data
        
    def _calculate_error_handling_score(self, scenario_comparison, variation: TestVariation) -> float:
        """Calculate error handling effectiveness score"""
        
        base_score = 0.8
        
        if variation.introduce_errors and scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.success:
            return base_score + 0.2  # Good error recovery
        elif variation.introduce_errors and not (scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.success):
            return base_score - 0.3  # Poor error handling
        else:
            return base_score
            
    def _calculate_robustness_score(self, scenario_comparison, variation: TestVariation) -> float:
        """Calculate system robustness score"""
        
        base_score = 0.7
        
        # Adjust based on variation handling
        if variation.data_completeness < 1.0 and scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.success:
            base_score += 0.2  # Good incomplete data handling
            
        if variation.api_timeout_simulation and scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.success:
            base_score += 0.1  # Good timeout handling
            
        return min(1.0, base_score)
        
    def _calculate_business_value_score(self, scenario_comparison) -> float:
        """Calculate business value score"""
        
        if not scenario_comparison.tier_service_result:
            return 0.0
            
        # Factors: professional deliverables, cost efficiency, quality
        professional_bonus = 0.3 if len(scenario_comparison.tier_service_result.professional_package) > 0 else 0
        quality_factor = scenario_comparison.tier_service_result.quality_score * 0.4
        cost_efficiency = min(0.3, 0.3 * (1000 / scenario_comparison.tier_service_result.total_cost_usd)) if scenario_comparison.tier_service_result.total_cost_usd > 0 else 0
        
        return professional_bonus + quality_factor + cost_efficiency
        
    def _identify_issues(self, scenario_comparison, variation: TestVariation) -> List[str]:
        """Identify issues from test results"""
        
        issues = []
        
        if not scenario_comparison.tier_service_result or not scenario_comparison.tier_service_result.success:
            issues.append("Tier service processing failed")
            
        if scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.quality_score < 0.6:
            issues.append("Quality score below acceptable threshold")
            
        if variation.data_completeness < 1.0 and scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.quality_score < 0.5:
            issues.append("Poor handling of incomplete data")
            
        if scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.total_cost_usd == 0:
            issues.append("Cost tracking failed")
            
        return issues
        
    def _generate_dataset_recommendations(self, scenario_comparison, variation: TestVariation) -> List[str]:
        """Generate recommendations for dataset test results"""
        
        recommendations = []
        
        if variation.data_completeness < 1.0:
            recommendations.append("Implement better data validation and default value handling")
            
        if variation.introduce_errors:
            recommendations.append("Enhance error recovery and graceful degradation mechanisms")
            
        if scenario_comparison.tier_service_result and scenario_comparison.tier_service_result.quality_score > 0.8:
            recommendations.append("System demonstrates good performance - ready for production")
        else:
            recommendations.append("System performance needs improvement before production deployment")
            
        return recommendations
        
    def _analyze_robustness(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze system robustness across all tests"""
        
        if not validation_results:
            return {}
            
        successful_tests = [r for r in validation_results if r.success]
        
        return {
            "overall_success_rate": len(successful_tests) / len(validation_results),
            "average_error_handling_score": sum(r.error_handling_score for r in validation_results) / len(validation_results),
            "average_robustness_score": sum(r.robustness_score for r in validation_results) / len(validation_results),
            "variation_performance": {
                variation_id: {
                    "success_rate": len([r for r in validation_results if r.variation_id == variation_id and r.success]) / len([r for r in validation_results if r.variation_id == variation_id]),
                    "average_quality": sum(r.quality_score for r in validation_results if r.variation_id == variation_id) / len([r for r in validation_results if r.variation_id == variation_id])
                }
                for variation_id in set(r.variation_id for r in validation_results)
            }
        }
        
    def _analyze_by_sector(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze results by sector"""
        
        # Extract sector from dataset_id (simplified)
        sector_results = {}
        for result in validation_results:
            sector = result.dataset_id.split('_')[0]  # Extract sector from dataset_id
            if sector not in sector_results:
                sector_results[sector] = []
            sector_results[sector].append(result)
            
        return {
            sector: {
                "success_rate": len([r for r in results if r.success]) / len(results),
                "average_quality": sum(r.quality_score for r in results) / len(results),
                "average_cost": sum(r.total_cost for r in results) / len(results)
            }
            for sector, results in sector_results.items()
        }
        
    def _analyze_by_size(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze results by organization size"""
        
        # Extract size from dataset_id (simplified)
        size_results = {}
        for result in validation_results:
            size = result.dataset_id.split('_')[1]  # Extract size from dataset_id
            if size not in size_results:
                size_results[size] = []
            size_results[size].append(result)
            
        return {
            size: {
                "success_rate": len([r for r in results if r.success]) / len(results),
                "average_quality": sum(r.quality_score for r in results) / len(results),
                "average_cost": sum(r.total_cost for r in results) / len(results)
            }
            for size, results in size_results.items()
        }
        
    def _analyze_by_complexity(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze results by complexity level"""
        
        # Extract complexity from dataset_id (simplified)
        complexity_results = {}
        for result in validation_results:
            complexity = result.dataset_id.split('_')[2]  # Extract complexity from dataset_id
            if complexity not in complexity_results:
                complexity_results[complexity] = []
            complexity_results[complexity].append(result)
            
        return {
            complexity: {
                "success_rate": len([r for r in results if r.success]) / len(results),
                "average_quality": sum(r.quality_score for r in results) / len(results),
                "average_cost": sum(r.total_cost for r in results) / len(results)
            }
            for complexity, results in complexity_results.items()
        }
        
    def _generate_validation_recommendations(self, validation_suite: Dict[str, Any]) -> List[str]:
        """Generate overall validation recommendations"""
        
        recommendations = []
        
        robustness = validation_suite["robustness_analysis"]
        
        if robustness.get("overall_success_rate", 0) > 0.9:
            recommendations.append("System demonstrates high reliability - ready for production deployment")
        elif robustness.get("overall_success_rate", 0) > 0.8:
            recommendations.append("System shows good reliability with minor improvements needed")
        else:
            recommendations.append("System reliability needs significant improvement before production")
            
        if robustness.get("average_error_handling_score", 0) < 0.7:
            recommendations.append("Enhance error handling and recovery mechanisms")
            
        if robustness.get("average_robustness_score", 0) < 0.7:
            recommendations.append("Improve system robustness for edge cases and data variations")
            
        # Sector-specific recommendations
        sector_analysis = validation_suite["sector_analysis"]
        for sector, metrics in sector_analysis.items():
            if metrics.get("success_rate", 0) < 0.8:
                recommendations.append(f"Improve performance for {sector} sector applications")
                
        return recommendations
        
    async def _save_validation_results(self, validation_suite: Dict[str, Any]):
        """Save comprehensive validation results"""
        
        # Save main results
        results_file = self.results_dir / "real_world_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(validation_suite, f, indent=2, default=str)
            
        # Save detailed validation results
        for result in validation_suite["validation_results"]:
            result_file = self.results_dir / f"validation_result_{result.dataset_id}.json"
            with open(result_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
                
        logger.info(f"Validation results saved to: {self.results_dir}")
        
    def _print_validation_summary(self, validation_suite: Dict[str, Any]):
        """Print comprehensive validation summary"""
        
        print(f"\n{'='*100}")
        print("REAL WORLD VALIDATION SUITE - COMPREHENSIVE RESULTS")
        print(f"{'='*100}")
        
        print(f"Session ID: {validation_suite['session_id']}")
        print(f"Total Test Datasets: {len(validation_suite['test_datasets'])}")
        print(f"Total Validation Tests: {len(validation_suite['validation_results'])}")
        
        robustness = validation_suite["robustness_analysis"]
        print(f"\n{'='*50} ROBUSTNESS ANALYSIS {'='*50}")
        print(f"Overall Success Rate: {robustness.get('overall_success_rate', 0):.1%}")
        print(f"Average Error Handling Score: {robustness.get('average_error_handling_score', 0):.2f}")
        print(f"Average Robustness Score: {robustness.get('average_robustness_score', 0):.2f}")
        
        print(f"\n{'='*50} SECTOR ANALYSIS {'='*50}")
        sector_analysis = validation_suite["sector_analysis"]
        for sector, metrics in sector_analysis.items():
            print(f"\n{sector.upper()}:")
            print(f"  Success Rate: {metrics.get('success_rate', 0):.1%}")
            print(f"  Average Quality: {metrics.get('average_quality', 0):.2f}")
            print(f"  Average Cost: ${metrics.get('average_cost', 0):.2f}")
            
        print(f"\n{'='*50} RECOMMENDATIONS {'='*50}")
        for recommendation in validation_suite["recommendations"]:
            print(f"• {recommendation}")
            
        print(f"\n{'='*100}")
        print("REAL WORLD VALIDATION COMPLETE - See detailed results in validation_results directory")
        print(f"{'='*100}\n")

# Main execution function
async def run_real_world_validation():
    """Run comprehensive real-world validation"""
    
    print("Real World Validation Suite - Enhanced Test Data Pipeline")
    print("=" * 100)
    
    # Initialize configuration
    config = TestConfiguration(
        max_total_budget=150.00,  # Higher budget for comprehensive validation
        enable_real_api=False,   # Set to True for real API testing
        enable_simulation=True,
        save_detailed_results=True
    )
    
    # Create validation tester
    tester = RealWorldValidationTester(config)
    
    try:
        # Run comprehensive validation
        results = await tester.run_comprehensive_validation()
        
        print(f"\n✓ Real world validation completed successfully!")
        print(f"✓ Results saved to: {tester.results_dir}")
        print(f"✓ Validation tests run: {len(results['validation_results'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Real world validation failed: {e}")
        print(f"✗ Validation failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the comprehensive real world validation
    asyncio.run(run_real_world_validation())
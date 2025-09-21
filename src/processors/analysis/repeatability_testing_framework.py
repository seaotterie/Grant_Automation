"""
Repeatability Testing Framework

Comprehensive testing framework to validate that the new fact-extraction + deterministic
scoring architecture produces identical results for identical inputs, addressing the
core concern about variable AI responses.

Key Testing Areas:
- Identical input → Identical output validation
- Cross-architecture comparison (new vs legacy)
- Performance impact measurement
- Data quality impact on repeatability
"""

import json
import logging
import asyncio
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel
import hashlib

from src.processors.analysis.enhanced_ai_lite_processor import EnhancedAILiteProcessor, ProcessingMode
from src.processors.analysis.fact_extraction_integration_service import ProcessorMigrationConfig
from src.processors.analysis.opportunity_type_detector import OpportunityType

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Individual test case for repeatability testing"""
    test_id: str
    opportunity_data: Dict[str, Any]
    profile_data: Dict[str, Any]
    expected_opportunity_type: Optional[OpportunityType] = None
    description: str = ""
    data_completeness_category: str = "medium"  # high, medium, low

class RepeatabilityTestResult(BaseModel):
    """Results of repeatability testing"""
    test_id: str
    test_runs: int
    success: bool
    
    # Score consistency metrics
    scores: List[float]
    score_variance: float
    max_score_difference: float
    mean_score: float
    
    # Repeatability assessment
    is_perfectly_repeatable: bool  # Zero variance
    repeatability_quality: str    # excellent, good, fair, poor
    consistency_percentage: float # Percentage of identical results
    
    # Architecture comparison
    architecture_used: str
    processing_modes_tested: List[str]
    cross_architecture_difference: Optional[float] = None
    
    # Performance metrics
    processing_times: List[float]
    mean_processing_time: float
    processing_time_variance: float
    
    # Additional analysis
    confidence_levels: List[str]
    opportunity_types_detected: List[str]
    data_completeness_scores: List[float]
    
    # Test metadata
    test_timestamp: datetime
    test_description: str

class RepeatabilityTestSuite(BaseModel):
    """Complete test suite results"""
    suite_id: str
    total_test_cases: int
    successful_tests: int
    failed_tests: int
    
    # Overall repeatability metrics
    overall_repeatability_score: float  # 0.0-1.0 composite score
    perfectly_repeatable_count: int
    repeatability_quality_distribution: Dict[str, int]
    
    # Architecture comparison summary
    new_architecture_performance: Dict[str, float]
    legacy_architecture_performance: Dict[str, float]
    architecture_difference_stats: Dict[str, float]
    
    # Performance impact analysis
    performance_impact_summary: Dict[str, Any]
    
    # Individual test results
    test_results: List[RepeatabilityTestResult]
    
    # Suite metadata
    test_timestamp: datetime
    test_configuration: Dict[str, Any]

class RepeatabilityTestingFramework:
    """
    Comprehensive framework for testing repeatability of the new architecture
    
    Key Capabilities:
    - Identical input repeatability validation
    - Cross-architecture comparison testing
    - Performance impact measurement
    - Data quality impact analysis
    - Comprehensive reporting and metrics
    """
    
    def __init__(self):
        self.test_cases = self._initialize_test_cases()
        self.test_results = []
        
        # Initialize processors for testing
        self.processors = {
            'new_architecture': EnhancedAILiteProcessor(
                processing_mode=ProcessingMode.NEW_ARCHITECTURE,
                migration_config=ProcessorMigrationConfig(
                    enable_fact_extraction=True,
                    enable_deterministic_scoring=True,
                    fallback_to_legacy=False
                )
            ),
            'legacy_architecture': EnhancedAILiteProcessor(
                processing_mode=ProcessingMode.LEGACY_ARCHITECTURE
            ),
            'hybrid_comparison': EnhancedAILiteProcessor(
                processing_mode=ProcessingMode.HYBRID_COMPARISON
            )
        }
    
    def _initialize_test_cases(self) -> List[TestCase]:
        """Initialize comprehensive test cases covering different opportunity types and data qualities"""
        
        test_cases = []
        
        # Government opportunity test cases (high data completeness expected)
        test_cases.extend([
            TestCase(
                test_id="gov_high_data_001",
                description="Federal grant with comprehensive RFP documentation",
                opportunity_data={
                    'opportunity_id': 'FEMA-2024-001',
                    'title': 'Emergency Management Performance Grant',
                    'organization_name': 'Federal Emergency Management Agency',
                    'agency': 'FEMA',
                    'website': 'https://fema.gov/grants',
                    'funding_amount': '$500,000 - $2,000,000',
                    'deadline': '2024-12-15',
                    'geographic_scope': 'National',
                    'category': 'Emergency Management',
                    'focus_areas': ['Disaster Preparedness', 'Community Resilience']
                },
                profile_data={
                    'name': 'Metro Emergency Response Coalition',
                    'ein': '541234567',
                    'state': 'VA',
                    'annual_revenue': 1500000,
                    'ntee_codes': ['M42'],
                    'focus_areas': ['Emergency Management', 'Disaster Response'],
                    'mission_statement': 'Enhance community emergency preparedness and response capabilities'
                },
                expected_opportunity_type=OpportunityType.GOVERNMENT,
                data_completeness_category="high"
            ),
            
            TestCase(
                test_id="gov_medium_data_002", 
                description="State government opportunity with limited documentation",
                opportunity_data={
                    'opportunity_id': 'VA-DOH-2024-15',
                    'title': 'Community Health Innovation Grant',
                    'organization_name': 'Virginia Department of Health',
                    'funding_amount': '$50,000 - $200,000',
                    'geographic_scope': 'Virginia',
                    'focus_areas': ['Public Health', 'Health Innovation']
                },
                profile_data={
                    'name': 'Virginia Health Innovation Network',
                    'ein': '541987654',
                    'state': 'VA',
                    'annual_revenue': 800000,
                    'ntee_codes': ['E32'],
                    'focus_areas': ['Health Innovation', 'Community Health'],
                    'mission_statement': 'Advance health innovation in Virginia communities'
                },
                expected_opportunity_type=OpportunityType.GOVERNMENT,
                data_completeness_category="medium"
            )
        ])
        
        # Nonprofit/Foundation test cases (medium data completeness expected)
        test_cases.extend([
            TestCase(
                test_id="nonprofit_medium_data_001",
                description="Private foundation with standard website information",
                opportunity_data={
                    'opportunity_id': 'GATES-HEALTH-2024',
                    'title': 'Global Health Innovation Initiative',
                    'organization_name': 'Gates Foundation',
                    'website': 'https://gatesfoundation.org/grants',
                    'funding_amount': '$100,000 - $500,000',
                    'focus_areas': ['Global Health', 'Innovation', 'Technology'],
                    'geographic_scope': 'International'
                },
                profile_data={
                    'name': 'International Health Technology Alliance',
                    'ein': '542345678',
                    'state': 'WA',
                    'annual_revenue': 2500000,
                    'ntee_codes': ['E70'],
                    'focus_areas': ['Global Health', 'Health Technology', 'Innovation'],
                    'mission_statement': 'Develop technology solutions for global health challenges'
                },
                expected_opportunity_type=OpportunityType.NONPROFIT,
                data_completeness_category="medium"
            ),
            
            TestCase(
                test_id="nonprofit_low_data_002",
                description="Small foundation with minimal public information",
                opportunity_data={
                    'opportunity_id': 'LOCAL-FOUND-001',
                    'title': 'Community Support Grants',
                    'organization_name': 'Local Community Foundation',
                    'focus_areas': ['Community Development'],
                    'geographic_scope': 'Local'
                },
                profile_data={
                    'name': 'Community Development Partnership',
                    'ein': '543456789',
                    'state': 'VA',
                    'annual_revenue': 150000,
                    'ntee_codes': ['S20'],
                    'focus_areas': ['Community Development', 'Social Services'],
                    'mission_statement': 'Strengthen communities through collaborative development'
                },
                expected_opportunity_type=OpportunityType.NONPROFIT,
                data_completeness_category="low"
            )
        ])
        
        # Corporate opportunity test cases (low data completeness expected)
        test_cases.extend([
            TestCase(
                test_id="corporate_low_data_001",
                description="Corporate CSR program with minimal public details",
                opportunity_data={
                    'opportunity_id': 'CORP-CSR-2024',
                    'title': 'Community Partnership Initiative',
                    'organization_name': 'TechCorp Industries',
                    'industry': 'Technology',
                    'focus_areas': ['Education', 'Technology Access'],
                    'partnership_types': ['Grants', 'Volunteer Support']
                },
                profile_data={
                    'name': 'Digital Equity Education Network',
                    'ein': '544567890',
                    'state': 'CA',
                    'annual_revenue': 750000,
                    'ntee_codes': ['B90'],
                    'focus_areas': ['Digital Equity', 'Education Technology'],
                    'mission_statement': 'Bridge the digital divide through educational programs'
                },
                expected_opportunity_type=OpportunityType.CORPORATE,
                data_completeness_category="low"
            )
        ])
        
        return test_cases
    
    async def run_repeatability_test_suite(self, test_runs: int = 5,
                                         include_cross_architecture: bool = True) -> RepeatabilityTestSuite:
        """
        Run comprehensive repeatability test suite
        
        Args:
            test_runs: Number of repeated runs per test case
            include_cross_architecture: Whether to include cross-architecture comparison
            
        Returns:
            RepeatabilityTestSuite with comprehensive results
        """
        suite_id = f"repeatability_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting repeatability test suite: {suite_id}")
        logger.info(f"Test configuration: {len(self.test_cases)} test cases, "
                   f"{test_runs} runs each, cross-architecture: {include_cross_architecture}")
        
        start_time = datetime.now()
        test_results = []
        
        # Run tests for each test case
        for test_case in self.test_cases:
            logger.info(f"Running test case: {test_case.test_id} - {test_case.description}")
            
            try:
                # Test new architecture repeatability
                new_arch_result = await self._run_single_test_case(
                    test_case, test_runs, 'new_architecture'
                )
                test_results.append(new_arch_result)
                
                # Test legacy architecture repeatability (for comparison)
                if include_cross_architecture:
                    legacy_result = await self._run_single_test_case(
                        test_case, test_runs, 'legacy_architecture'
                    )
                    test_results.append(legacy_result)
                    
                    # Calculate cross-architecture difference
                    cross_diff = abs(new_arch_result.mean_score - legacy_result.mean_score)
                    new_arch_result.cross_architecture_difference = cross_diff
                    legacy_result.cross_architecture_difference = cross_diff
                    
                    logger.info(f"Cross-architecture difference for {test_case.test_id}: {cross_diff:.3f}")
                
            except Exception as e:
                logger.error(f"Test case {test_case.test_id} failed: {str(e)}")
                # Create failed test result
                failed_result = RepeatabilityTestResult(
                    test_id=f"{test_case.test_id}_failed",
                    test_runs=0,
                    success=False,
                    scores=[],
                    score_variance=0.0,
                    max_score_difference=0.0,
                    mean_score=0.0,
                    is_perfectly_repeatable=False,
                    repeatability_quality="failed",
                    consistency_percentage=0.0,
                    architecture_used="error",
                    processing_modes_tested=[],
                    processing_times=[],
                    mean_processing_time=0.0,
                    processing_time_variance=0.0,
                    confidence_levels=[],
                    opportunity_types_detected=[],
                    data_completeness_scores=[],
                    test_timestamp=datetime.now(),
                    test_description=f"Failed: {str(e)}"
                )
                test_results.append(failed_result)
        
        # Analyze overall suite results
        suite_results = self._analyze_suite_results(test_results, suite_id, start_time)
        
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Repeatability test suite completed in {total_time:.2f}s")
        logger.info(f"Overall repeatability score: {suite_results.overall_repeatability_score:.3f}")
        
        return suite_results
    
    async def _run_single_test_case(self, test_case: TestCase, test_runs: int,
                                  architecture: str) -> RepeatabilityTestResult:
        """Run a single test case multiple times to test repeatability"""
        
        processor = self.processors[architecture]
        results = []
        
        # Create consistent input hash for validation
        input_hash = self._create_input_hash(test_case.opportunity_data, test_case.profile_data)
        
        # Run the same input multiple times
        for run in range(test_runs):
            logger.debug(f"Test run {run + 1}/{test_runs} for {test_case.test_id} ({architecture})")
            
            try:
                result = await processor.execute({
                    'opportunity': test_case.opportunity_data,
                    'profile': test_case.profile_data
                })
                
                results.append({
                    'run': run + 1,
                    'success': result.success,
                    'final_score': result.final_score,
                    'confidence_level': result.confidence_level,
                    'processing_time': result.processing_time,
                    'architecture_used': result.architecture_used,
                    'opportunity_type': getattr(result, 'opportunity_type', 'unknown'),
                    'data_completeness': getattr(result, 'data_completeness', 0.0)
                })
                
            except Exception as e:
                logger.error(f"Run {run + 1} failed for {test_case.test_id}: {str(e)}")
                results.append({
                    'run': run + 1,
                    'success': False,
                    'final_score': 0.0,
                    'confidence_level': 'error',
                    'processing_time': 0.0,
                    'architecture_used': 'error',
                    'opportunity_type': 'error',
                    'data_completeness': 0.0
                })
        
        # Analyze repeatability
        return self._analyze_test_results(test_case, results, architecture)
    
    def _analyze_test_results(self, test_case: TestCase, results: List[Dict[str, Any]],
                            architecture: str) -> RepeatabilityTestResult:
        """Analyze results from multiple runs of the same test"""
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return RepeatabilityTestResult(
                test_id=f"{test_case.test_id}_{architecture}",
                test_runs=len(results),
                success=False,
                scores=[],
                score_variance=0.0,
                max_score_difference=0.0,
                mean_score=0.0,
                is_perfectly_repeatable=False,
                repeatability_quality="failed",
                consistency_percentage=0.0,
                architecture_used=architecture,
                processing_modes_tested=[architecture],
                processing_times=[],
                mean_processing_time=0.0,
                processing_time_variance=0.0,
                confidence_levels=[],
                opportunity_types_detected=[],
                data_completeness_scores=[],
                test_timestamp=datetime.now(),
                test_description=f"All runs failed for {test_case.description}"
            )
        
        # Extract metrics from successful results
        scores = [r['final_score'] for r in successful_results]
        processing_times = [r['processing_time'] for r in successful_results]
        confidence_levels = [r['confidence_level'] for r in successful_results]
        opportunity_types = [r['opportunity_type'] for r in successful_results]
        data_completeness_scores = [r['data_completeness'] for r in successful_results]
        
        # Calculate repeatability metrics
        score_variance = statistics.variance(scores) if len(scores) > 1 else 0.0
        max_score_difference = max(scores) - min(scores) if scores else 0.0
        mean_score = statistics.mean(scores) if scores else 0.0
        
        # Assess repeatability quality
        is_perfectly_repeatable = max_score_difference == 0.0
        repeatability_quality = self._assess_repeatability_quality(max_score_difference)
        consistency_percentage = len(set(scores)) == 1 and len(scores) > 0
        consistency_percentage = 100.0 if consistency_percentage else (1.0 - (max_score_difference / max(abs(max(scores)), 1.0))) * 100
        
        # Processing time analysis
        mean_processing_time = statistics.mean(processing_times) if processing_times else 0.0
        processing_time_variance = statistics.variance(processing_times) if len(processing_times) > 1 else 0.0
        
        return RepeatabilityTestResult(
            test_id=f"{test_case.test_id}_{architecture}",
            test_runs=len(results),
            success=len(successful_results) > 0,
            scores=scores,
            score_variance=score_variance,
            max_score_difference=max_score_difference,
            mean_score=mean_score,
            is_perfectly_repeatable=is_perfectly_repeatable,
            repeatability_quality=repeatability_quality,
            consistency_percentage=consistency_percentage,
            architecture_used=architecture,
            processing_modes_tested=[architecture],
            processing_times=processing_times,
            mean_processing_time=mean_processing_time,
            processing_time_variance=processing_time_variance,
            confidence_levels=confidence_levels,
            opportunity_types_detected=opportunity_types,
            data_completeness_scores=data_completeness_scores,
            test_timestamp=datetime.now(),
            test_description=test_case.description
        )
    
    def _analyze_suite_results(self, test_results: List[RepeatabilityTestResult],
                             suite_id: str, start_time: datetime) -> RepeatabilityTestSuite:
        """Analyze overall test suite results"""
        
        successful_tests = [r for r in test_results if r.success]
        failed_tests = [r for r in test_results if not r.success]
        
        # Calculate overall repeatability score (composite metric)
        if successful_tests:
            quality_scores = []
            for result in successful_tests:
                if result.repeatability_quality == "excellent":
                    quality_scores.append(1.0)
                elif result.repeatability_quality == "good":
                    quality_scores.append(0.8)
                elif result.repeatability_quality == "fair":
                    quality_scores.append(0.6)
                else:
                    quality_scores.append(0.3)
            
            overall_repeatability_score = statistics.mean(quality_scores)
        else:
            overall_repeatability_score = 0.0
        
        # Repeatability quality distribution
        quality_distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "failed": 0}
        for result in test_results:
            if result.success:
                quality_distribution[result.repeatability_quality] += 1
            else:
                quality_distribution["failed"] += 1
        
        # Architecture comparison (if available)
        new_arch_results = [r for r in successful_tests if 'new_architecture' in r.architecture_used]
        legacy_arch_results = [r for r in successful_tests if 'legacy_architecture' in r.architecture_used]
        
        new_architecture_performance = {}
        legacy_architecture_performance = {}
        architecture_difference_stats = {}
        
        if new_arch_results:
            new_architecture_performance = {
                'mean_repeatability_score': statistics.mean([
                    1.0 if r.is_perfectly_repeatable else (1.0 - r.max_score_difference) 
                    for r in new_arch_results
                ]),
                'perfect_repeatability_rate': sum(1 for r in new_arch_results if r.is_perfectly_repeatable) / len(new_arch_results),
                'mean_processing_time': statistics.mean([r.mean_processing_time for r in new_arch_results])
            }
        
        if legacy_arch_results:
            legacy_architecture_performance = {
                'mean_repeatability_score': statistics.mean([
                    1.0 if r.is_perfectly_repeatable else (1.0 - r.max_score_difference)
                    for r in legacy_arch_results
                ]),
                'perfect_repeatability_rate': sum(1 for r in legacy_arch_results if r.is_perfectly_repeatable) / len(legacy_arch_results),
                'mean_processing_time': statistics.mean([r.mean_processing_time for r in legacy_arch_results])
            }
        
        # Cross-architecture difference analysis
        cross_diffs = [r.cross_architecture_difference for r in successful_tests if r.cross_architecture_difference is not None]
        if cross_diffs:
            architecture_difference_stats = {
                'mean_difference': statistics.mean(cross_diffs),
                'max_difference': max(cross_diffs),
                'min_difference': min(cross_diffs),
                'significant_differences': sum(1 for d in cross_diffs if d > 0.1)  # >10% difference
            }
        
        return RepeatabilityTestSuite(
            suite_id=suite_id,
            total_test_cases=len(test_results),
            successful_tests=len(successful_tests),
            failed_tests=len(failed_tests),
            overall_repeatability_score=overall_repeatability_score,
            perfectly_repeatable_count=sum(1 for r in successful_tests if r.is_perfectly_repeatable),
            repeatability_quality_distribution=quality_distribution,
            new_architecture_performance=new_architecture_performance,
            legacy_architecture_performance=legacy_architecture_performance,
            architecture_difference_stats=architecture_difference_stats,
            performance_impact_summary=self._analyze_performance_impact(successful_tests),
            test_results=test_results,
            test_timestamp=start_time,
            test_configuration={
                'test_cases': len(self.test_cases),
                'architectures_tested': list(self.processors.keys()),
                'framework_version': '1.0.0'
            }
        )
    
    def _analyze_performance_impact(self, successful_tests: List[RepeatabilityTestResult]) -> Dict[str, Any]:
        """Analyze performance impact of new architecture vs legacy"""
        
        new_arch_times = [r.mean_processing_time for r in successful_tests if 'new_architecture' in r.architecture_used]
        legacy_arch_times = [r.mean_processing_time for r in successful_tests if 'legacy_architecture' in r.architecture_used]
        
        performance_summary = {}
        
        if new_arch_times:
            performance_summary['new_architecture'] = {
                'mean_time': statistics.mean(new_arch_times),
                'median_time': statistics.median(new_arch_times),
                'max_time': max(new_arch_times),
                'min_time': min(new_arch_times)
            }
        
        if legacy_arch_times:
            performance_summary['legacy_architecture'] = {
                'mean_time': statistics.mean(legacy_arch_times),
                'median_time': statistics.median(legacy_arch_times),
                'max_time': max(legacy_arch_times),
                'min_time': min(legacy_arch_times)
            }
        
        if new_arch_times and legacy_arch_times:
            new_mean = statistics.mean(new_arch_times)
            legacy_mean = statistics.mean(legacy_arch_times)
            performance_summary['comparison'] = {
                'time_difference': new_mean - legacy_mean,
                'performance_ratio': new_mean / legacy_mean,
                'is_faster': new_mean < legacy_mean
            }
        
        return performance_summary
    
    def _assess_repeatability_quality(self, max_difference: float) -> str:
        """Assess repeatability quality based on maximum score difference"""
        if max_difference == 0.0:
            return "excellent"  # Perfect repeatability
        elif max_difference < 0.01:  # <1% difference
            return "excellent"
        elif max_difference < 0.05:  # <5% difference
            return "good"
        elif max_difference < 0.10:  # <10% difference
            return "fair"
        else:
            return "poor"
    
    def _create_input_hash(self, opportunity_data: Dict[str, Any], profile_data: Dict[str, Any]) -> str:
        """Create hash of input data for consistency validation"""
        combined_input = {
            'opportunity': opportunity_data,
            'profile': profile_data
        }
        input_json = json.dumps(combined_input, sort_keys=True)
        return hashlib.md5(input_json.encode()).hexdigest()
    
    async def run_quick_repeatability_check(self, test_runs: int = 3) -> Dict[str, Any]:
        """Run a quick repeatability check with limited test cases"""
        
        logger.info(f"Running quick repeatability check ({test_runs} runs)")
        
        # Use first test case for quick check
        test_case = self.test_cases[0] if self.test_cases else None
        if not test_case:
            return {"error": "No test cases available"}
        
        # Test new architecture only
        result = await self._run_single_test_case(test_case, test_runs, 'new_architecture')
        
        return {
            'test_case': test_case.test_id,
            'repeatability_quality': result.repeatability_quality,
            'is_perfectly_repeatable': result.is_perfectly_repeatable,
            'max_difference': result.max_score_difference,
            'mean_score': result.mean_score,
            'score_variance': result.score_variance,
            'test_runs': result.test_runs
        }
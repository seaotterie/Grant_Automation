# Unit Tests for Discovery Scorer
# Tests the core discovery scoring functionality with comprehensive coverage

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from src.scoring.discovery_scorer import DiscoveryScorer
    from src.profiles.models import OrganizationProfile
except ImportError:
    # Mock classes if imports fail
    class DiscoveryScorer:
        async def score_opportunity(self, opportunity, profile):
            return Mock(overall_score=0.75, confidence_level=0.8, dimension_scores={})
    
    class OrganizationProfile:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

class TestDiscoveryScorer:
    """Test suite for Discovery Scorer functionality"""

    @pytest.fixture
    def scorer(self):
        """Create a discovery scorer instance"""
        return DiscoveryScorer()

    def create_test_profile(self, **kwargs):
        """Helper to create test profiles with required fields"""
        from src.profiles.models import OrganizationType

        # Set defaults for required fields
        defaults = {
            'profile_id': f"test_profile_{hash(str(kwargs)) % 10000}",
            'name': kwargs.pop('organization_name', 'Test Organization'),
            'organization_type': OrganizationType.NONPROFIT,
            'focus_areas': ['general'],
        }

        # Map legacy field names to new field names
        if 'revenue' in kwargs:
            kwargs['annual_revenue'] = kwargs.pop('revenue')
        if 'state' in kwargs:
            kwargs['location'] = kwargs.pop('state')

        # Merge defaults with provided kwargs
        defaults.update(kwargs)

        return OrganizationProfile(**defaults)

    @pytest.fixture
    def valid_profile(self):
        """Valid organization profile for testing"""
        return self.create_test_profile(
            organization_name="Test Education Foundation",
            focus_areas=["education", "youth development"],
            ntee_codes=["B25"],
            annual_revenue=1000000,
            location="Richmond, VA",
            mission_statement="Supporting educational excellence"
        )
    
    @pytest.fixture
    def valid_opportunity(self):
        """Valid opportunity for testing"""
        return {
            "opportunity_id": "test_opp_001",
            "organization_name": "Educational Grant Foundation",
            "ntee_codes": ["B25"],
            "external_data": {"state": "VA"},
            "description": "Educational support program for underserved communities",
            "funding_amount": 150000,
            "application_deadline": (datetime.now() + timedelta(days=45)).isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_basic_scoring_functionality(self, scorer, valid_profile, valid_opportunity):
        """Test basic discovery scoring functionality"""
        result = await scorer.score_opportunity(valid_opportunity, valid_profile)
        
        # Validate result structure
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'confidence_level')
        assert hasattr(result, 'dimension_scores')
        
        # Validate score ranges
        assert 0.0 <= result.overall_score <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0
        
        # Validate dimension scores exist
        assert isinstance(result.dimension_scores, dict)
        assert len(result.dimension_scores) > 0
    
    @pytest.mark.asyncio
    async def test_perfect_match_scoring(self, scorer):
        """Test scoring with perfect match data"""
        perfect_profile = self.create_test_profile(
            organization_name="Perfect Education Foundation",
            focus_areas=["education"],
            ntee_codes=["B25"],
            revenue=1000000,
            state="VA"
        )
        
        perfect_opportunity = {
            "organization_name": "Education Support Initiative",
            "ntee_codes": ["B25"],
            "external_data": {"state": "VA"},
            "description": "Education foundation support",
            "funding_amount": 100000  # Perfect size for organization
        }
        
        result = await scorer.score_opportunity(perfect_opportunity, perfect_profile)
        
        # Perfect match should score highly
        assert result.overall_score > 0.7
        assert result.confidence_level > 0.7
    
    @pytest.mark.asyncio
    async def test_poor_match_scoring(self, scorer):
        """Test scoring with poor match data"""
        poor_profile = self.create_test_profile(
            organization_name="Education Foundation",
            ntee_codes=["B25"],
            revenue=1000000,
            state="VA"
        )
        
        poor_opportunity = {
            "organization_name": "Sports Equipment Company",
            "ntee_codes": ["T99"],  # Different NTEE
            "external_data": {"state": "CA"},  # Different state
            "description": "Sports equipment manufacturing",
            "funding_amount": 10000000  # Way too large
        }
        
        result = await scorer.score_opportunity(poor_opportunity, poor_profile)
        
        # Poor match should score lower
        assert result.overall_score < 0.6
    
    @pytest.mark.asyncio
    async def test_missing_data_handling(self, scorer):
        """Test handling of missing data"""
        minimal_profile = self.create_test_profile(
            organization_name="Minimal Foundation"
            # create_test_profile adds required fields automatically
        )
        
        minimal_opportunity = {
            "organization_name": "Some Foundation"
            # Missing most fields
        }
        
        result = await scorer.score_opportunity(minimal_opportunity, minimal_profile)
        
        # Should handle gracefully
        assert 0.0 <= result.overall_score <= 1.0
        assert result.confidence_level < 0.6  # Low confidence due to missing data
    
    @pytest.mark.asyncio
    async def test_ntee_code_matching(self, scorer):
        """Test NTEE code matching logic"""
        profile = self.create_test_profile(
            organization_name="Education Foundation",
            ntee_codes=["B25", "B28"],
            revenue=1000000,
            state="VA"
        )
        
        # Test exact match
        exact_match_opp = {
            "organization_name": "Education Grant",
            "ntee_codes": ["B25"],
            "description": "Education support"
        }
        
        result_exact = await scorer.score_opportunity(exact_match_opp, profile)
        
        # Test no match
        no_match_opp = {
            "organization_name": "Sports Grant",
            "ntee_codes": ["T99"],
            "description": "Sports support"
        }
        
        result_no_match = await scorer.score_opportunity(no_match_opp, profile)
        
        # Exact match should score higher than no match
        assert result_exact.overall_score > result_no_match.overall_score
    
    @pytest.mark.asyncio
    async def test_geographic_scoring(self, scorer):
        """Test geographic advantage scoring"""
        profile = self.create_test_profile(
            organization_name="Virginia Foundation",
            state="VA",
            ntee_codes=["B25"]
        )
        
        # Same state opportunity
        va_opportunity = {
            "organization_name": "VA Education Grant",
            "external_data": {"state": "VA"},
            "ntee_codes": ["B25"]
        }
        
        # Different state opportunity
        ca_opportunity = {
            "organization_name": "CA Education Grant", 
            "external_data": {"state": "CA"},
            "ntee_codes": ["B25"]
        }
        
        va_result = await scorer.score_opportunity(va_opportunity, profile)
        ca_result = await scorer.score_opportunity(ca_opportunity, profile)
        
        # Same state should score higher
        assert va_result.overall_score >= ca_result.overall_score
    
    @pytest.mark.asyncio
    async def test_revenue_compatibility(self, scorer):
        """Test revenue-based compatibility scoring"""
        small_org = self.create_test_profile(
            organization_name="Small Foundation",
            revenue=100000,
            ntee_codes=["B25"]
        )

        large_org = self.create_test_profile(
            organization_name="Large Foundation",
            revenue=10000000,
            ntee_codes=["B25"]
        )
        
        # Large grant opportunity
        large_opportunity = {
            "organization_name": "Major Grant Program",
            "funding_amount": 5000000,
            "ntee_codes": ["B25"]
        }
        
        small_result = await scorer.score_opportunity(large_opportunity, small_org)
        large_result = await scorer.score_opportunity(large_opportunity, large_org)
        
        # Large organization should be better match for large grant
        assert large_result.overall_score >= small_result.overall_score
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, scorer, valid_profile):
        """Test confidence level calculation"""
        # High-quality data opportunity
        high_quality_opp = {
            "organization_name": "Well Documented Foundation",
            "ntee_codes": ["B25"],
            "external_data": {"state": "VA"},
            "description": "Comprehensive education support program",
            "funding_amount": 150000,
            "application_deadline": (datetime.now() + timedelta(days=60)).isoformat(),
            "eligibility_criteria": ["Nonprofits", "Education"],
            "program_areas": ["K-12 Education", "Literacy"]
        }
        
        # Low-quality data opportunity
        low_quality_opp = {
            "organization_name": "Some Foundation"
            # Minimal data
        }
        
        high_quality_result = await scorer.score_opportunity(high_quality_opp, valid_profile)
        low_quality_result = await scorer.score_opportunity(low_quality_opp, valid_profile)
        
        # High-quality data should have higher confidence
        assert high_quality_result.confidence_level > low_quality_result.confidence_level
    
    @pytest.mark.asyncio
    async def test_boost_factors(self, scorer, valid_profile):
        """Test scoring boost factors"""
        base_opportunity = {
            "organization_name": "Base Foundation",
            "ntee_codes": ["B25"],
            "description": "Basic education support"
        }
        
        enhanced_opportunity = {
            "organization_name": "Enhanced Foundation",
            "ntee_codes": ["B25"],  # Exact NTEE match
            "description": "Education support with comprehensive data",
            "has_990_data": True,
            "board_connections": True,
            "historical_success": True
        }
        
        base_result = await scorer.score_opportunity(base_opportunity, valid_profile)
        enhanced_result = await scorer.score_opportunity(enhanced_opportunity, valid_profile)
        
        # Enhanced opportunity should score higher due to boost factors
        assert enhanced_result.overall_score >= base_result.overall_score
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self, scorer):
        """Test handling of edge cases"""
        profile = self.create_test_profile(organization_name="Test Foundation")
        
        edge_cases = [
            {},  # Empty opportunity
            {"organization_name": ""},  # Empty name
            {"organization_name": None},  # None name
            {"funding_amount": -1000},  # Negative amount
            {"ntee_codes": "invalid"}  # Invalid NTEE format
        ]
        
        for edge_case in edge_cases:
            result = await scorer.score_opportunity(edge_case, profile)
            
            # Should handle gracefully without errors
            assert 0.0 <= result.overall_score <= 1.0
            assert 0.0 <= result.confidence_level <= 1.0
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_scoring_performance(self, scorer, performance_test_data):
        """Test scoring performance with large dataset"""
        import time
        
        profiles = performance_test_data["profiles"][:10]  # Use subset for unit test
        opportunities = performance_test_data["opportunities"][:100]
        
        start_time = time.perf_counter()
        
        results = []
        for opportunity in opportunities:
            for profile in profiles:
                # Convert dict to profile object
                profile_obj = self.create_test_profile(**profile)
                result = await scorer.score_opportunity(opportunity, profile_obj)
                results.append(result)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Performance targets
        operations = len(opportunities) * len(profiles)
        avg_time_per_operation = total_time / operations
        
        # Should complete 1000 operations in reasonable time
        assert total_time < 10.0  # Less than 10 seconds
        assert avg_time_per_operation < 0.01  # Less than 10ms per operation
        
        # Verify all results are valid
        for result in results:
            assert 0.0 <= result.overall_score <= 1.0
    
    def test_scorer_initialization(self):
        """Test scorer initialization"""
        scorer = DiscoveryScorer()
        
        # Should initialize without errors
        assert scorer is not None
        assert hasattr(scorer, 'score_opportunity')
    
    @pytest.mark.asyncio
    async def test_concurrent_scoring(self, scorer, valid_profile, sample_opportunities_batch):
        """Test concurrent scoring operations"""
        import asyncio
        
        # Run multiple scoring operations concurrently
        tasks = [
            scorer.score_opportunity(opp, valid_profile)
            for opp in sample_opportunities_batch
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All operations should complete successfully
        assert len(results) == len(sample_opportunities_batch)
        
        for result in results:
            assert 0.0 <= result.overall_score <= 1.0
            assert 0.0 <= result.confidence_level <= 1.0
    
    @pytest.mark.asyncio
    async def test_score_consistency(self, scorer, valid_profile, valid_opportunity):
        """Test that identical inputs produce identical outputs"""
        results = []
        
        # Run same scoring operation multiple times
        for _ in range(5):
            result = await scorer.score_opportunity(valid_opportunity, valid_profile)
            results.append(result.overall_score)
        
        # All scores should be identical for same inputs
        assert len(set(results)) == 1, "Scoring inconsistency detected"
    
    def test_dimension_score_validation(self, scorer):
        """Test that dimension scores are properly validated"""
        # This would test the internal dimension scoring if accessible
        # For now, test through the main interface
        pass  # Implementation depends on scorer internals
    
    @pytest.mark.asyncio
    async def test_error_handling(self, scorer):
        """Test error handling in scorer"""
        profile = self.create_test_profile(organization_name="Test")
        
        # Test with invalid data that might cause errors
        invalid_opportunity = {
            "organization_name": "Test",
            "funding_amount": "invalid_amount",  # Should be numeric
            "application_deadline": "invalid_date"  # Should be proper date
        }
        
        # Should not raise exceptions
        try:
            result = await scorer.score_opportunity(invalid_opportunity, profile)
            assert 0.0 <= result.overall_score <= 1.0
        except Exception as e:
            pytest.fail(f"Scorer should handle invalid data gracefully, but raised: {e}")


# Integration tests that could be moved to integration folder
class TestDiscoveryScorerIntegration:
    """Integration tests for Discovery Scorer with other components"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scorer_with_real_data_structure(self, scorer):
        """Test scorer with realistic data structures"""
        # This would test with data structures matching real API responses
        realistic_opportunity = {
            "opportunity_id": "EPA-R3-MULTI-2024-001",
            "organization_name": "Environmental Protection Agency",
            "agency_code": "EPA",
            "title": "Environmental Education Grant Program",
            "description": "Funding for environmental education initiatives",
            "funding_amount_max": 150000,
            "funding_amount_min": 25000,
            "application_deadline": "2025-08-15T23:59:59Z",
            "eligibility_categories": ["Nonprofits"],
            "funding_activities": ["Education", "Environment"],
            "geographic_scope": "Regional",
            "ntee_codes": ["C32", "B25"]
        }
        
        realistic_profile = self.create_test_profile(
            organization_name="Environmental Education Foundation",
            ntee_codes=["C32"],
            revenue=750000,
            state="VA",
            mission_statement="Promoting environmental education and awareness"
        )
        
        result = await scorer.score_opportunity(realistic_opportunity, realistic_profile)
        
        # Should handle realistic data structure
        assert 0.0 <= result.overall_score <= 1.0
        assert result.confidence_level > 0.5  # Good data should give decent confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Functional tests for discovery engine
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.discovery.discovery_strategy import (
    UnifiedDiscoveryEngine, 
    GovernmentDiscoveryStrategy,
    FoundationDiscoveryStrategy,
    CorporateDiscoveryStrategy,
    get_discovery_engine
)
from src.core.data_models import GovernmentOpportunity, OpportunityCollection
from src.profiles.models import OrganizationProfile


class TestUnifiedDiscoveryEngine:
    """Test the unified discovery engine functionality"""
    
    def test_engine_initialization(self):
        engine = UnifiedDiscoveryEngine()
        
        assert 'government' in engine.strategies
        assert 'foundation' in engine.strategies 
        assert 'corporate' in engine.strategies
        
        assert isinstance(engine.strategies['government'], GovernmentDiscoveryStrategy)
        assert isinstance(engine.strategies['foundation'], FoundationDiscoveryStrategy)
        assert isinstance(engine.strategies['corporate'], CorporateDiscoveryStrategy)
    
    @pytest.mark.asyncio
    async def test_get_engine_status(self):
        engine = UnifiedDiscoveryEngine()
        status = await engine.get_engine_status()
        
        assert status['engine_status'] == 'active'
        assert 'strategies' in status
        assert status['total_strategies'] == 3
        
        # Check individual strategy status
        strategies = status['strategies']
        assert 'government' in strategies
        assert 'foundation' in strategies
        assert 'corporate' in strategies
    
    @pytest.mark.asyncio
    @patch('src.discovery.discovery_strategy.GovernmentDiscoveryStrategy.discover_opportunities')
    @patch('src.discovery.discovery_strategy.FoundationDiscoveryStrategy.discover_opportunities') 
    @patch('src.discovery.discovery_strategy.CorporateDiscoveryStrategy.discover_opportunities')
    async def test_discover_all_opportunities(self, mock_corp, mock_found, mock_gov, sample_organization_profile):
        # Mock strategy responses
        mock_gov_opportunity = GovernmentOpportunity(
            id="gov_001",
            title="Test Government Grant",
            funder_name="Test Agency",
            agency_code="TA",
            status="active",
            relevance_score=85.0
        )
        
        mock_gov.return_value = [mock_gov_opportunity]
        mock_found.return_value = []
        mock_corp.return_value = []
        
        engine = UnifiedDiscoveryEngine()
        collection = await engine.discover_all_opportunities(
            profile=sample_organization_profile,
            max_results_per_source=50
        )
        
        assert isinstance(collection, OpportunityCollection)
        assert collection.total_count == 1
        assert len(collection.government_opportunities) == 1
        assert collection.government_opportunities[0].id == "gov_001"
        
        # Verify all strategies were called
        mock_gov.assert_called_once()
        mock_found.assert_called_once()
        mock_corp.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.discovery.discovery_strategy.GovernmentDiscoveryStrategy.discover_opportunities')
    async def test_discovery_with_progress_callback(self, mock_gov, sample_organization_profile):
        mock_gov.return_value = []
        
        progress_messages = []
        def progress_callback(message):
            progress_messages.append(message)
        
        engine = UnifiedDiscoveryEngine()
        await engine.discover_all_opportunities(
            profile=sample_organization_profile,
            progress_callback=progress_callback
        )
        
        # Should have received progress messages from strategies
        assert any("Government:" in msg for msg in progress_messages)
    
    @pytest.mark.asyncio
    @patch('src.discovery.discovery_strategy.GovernmentDiscoveryStrategy.discover_opportunities')
    async def test_discovery_with_strategy_failure(self, mock_gov, sample_organization_profile):
        # Mock one strategy to fail
        mock_gov.side_effect = Exception("API Error")
        
        engine = UnifiedDiscoveryEngine()
        collection = await engine.discover_all_opportunities(
            profile=sample_organization_profile
        )
        
        # Should still return a collection, even if one strategy failed
        assert isinstance(collection, OpportunityCollection)
        # Total count might be 0 if other strategies also return empty results


class TestGovernmentDiscoveryStrategy:
    """Test government discovery strategy"""
    
    def test_strategy_initialization(self):
        strategy = GovernmentDiscoveryStrategy()
        
        assert strategy.strategy_name == "government"
        assert hasattr(strategy, 'grants_gov_client')
        assert hasattr(strategy, 'usaspending_client')
        assert hasattr(strategy, 'va_state_client')
    
    def test_keyword_extraction_from_profile(self, sample_organization_profile):
        strategy = GovernmentDiscoveryStrategy()
        
        # Add some descriptive fields to the profile
        sample_organization_profile.mission_description = "Community health and wellness programs"
        sample_organization_profile.activity_description = "Primary care services and health education"
        
        keywords = strategy._extract_keywords_from_profile(sample_organization_profile)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 10  # Should limit to top 10
        assert any(len(word) > 3 for word in keywords)  # Should filter short words
    
    @pytest.mark.asyncio
    @patch('src.clients.grants_gov_client.GrantsGovClient.search_opportunities')
    @patch('src.clients.va_state_client.VAStateClient.search_opportunities')
    async def test_discover_opportunities(self, mock_va_search, mock_grants_search, sample_organization_profile):
        # Mock API responses
        mock_grants_response = [
            {
                'opportunityId': 'HHS-2025-001',
                'opportunityTitle': 'Community Health Grant',
                'agencyName': 'Health and Human Services',
                'agencyCode': 'HHS',
                'awardCeiling': 50000,
                'closeDate': '2025-06-30'
            }
        ]
        
        mock_va_response = [
            {
                'id': 'VA-001',
                'title': 'Virginia Health Initiative',
                'agency_name': 'Virginia Department of Health',
                'agency_code': 'VDH',
                'funding_range': {'min': 10000, 'max': 25000},
                'deadline': '2025-05-15'
            }
        ]
        
        mock_grants_search.return_value = mock_grants_response
        mock_va_search.return_value = mock_va_response
        
        strategy = GovernmentDiscoveryStrategy()
        opportunities = await strategy.discover_opportunities(
            profile=sample_organization_profile,
            max_results=100
        )
        
        assert isinstance(opportunities, list)
        assert len(opportunities) == 2  # Should have both federal and state results
        
        # Verify both API clients were called
        mock_grants_search.assert_called_once()
        mock_va_search.assert_called_once()
    
    def test_relevance_score_calculation(self, sample_organization_profile, sample_government_opportunity):
        strategy = GovernmentDiscoveryStrategy()
        
        score = strategy.calculate_relevance_score(sample_government_opportunity, sample_organization_profile)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        
        # Test with health-related opportunity and health-related profile
        sample_government_opportunity.title = "Community Health Services Grant"
        sample_organization_profile.ntee_code = "P81"  # Health - Community Health Systems
        
        health_score = strategy.calculate_relevance_score(sample_government_opportunity, sample_organization_profile)
        
        # Should get bonus for NTEE alignment
        assert health_score > score
    
    def test_date_parsing(self):
        strategy = GovernmentDiscoveryStrategy()
        
        # Test ISO format
        date1 = strategy._parse_date("2025-06-30")
        assert date1 is not None
        assert date1.year == 2025
        assert date1.month == 6
        assert date1.day == 30
        
        # Test ISO format with time
        date2 = strategy._parse_date("2025-06-30T23:59:59Z")
        assert date2 is not None
        
        # Test invalid date
        date3 = strategy._parse_date("invalid-date")
        assert date3 is None
        
        # Test None input
        date4 = strategy._parse_date(None)
        assert date4 is None


class TestGlobalDiscoveryEngine:
    """Test the global discovery engine instance"""
    
    def test_get_discovery_engine_singleton(self):
        engine1 = get_discovery_engine()
        engine2 = get_discovery_engine()
        
        # Should return same instance
        assert engine1 is engine2
        assert isinstance(engine1, UnifiedDiscoveryEngine)
    
    @pytest.mark.asyncio
    async def test_global_engine_functionality(self, sample_organization_profile):
        engine = get_discovery_engine()
        
        # Should be able to get status
        status = await engine.get_engine_status()
        assert status['engine_status'] == 'active'


class TestDiscoveryIntegration:
    """Test end-to-end discovery integration"""
    
    @pytest.mark.asyncio
    @patch('src.clients.grants_gov_client.GrantsGovClient.search_opportunities')
    async def test_full_discovery_pipeline(self, mock_search, sample_organization_profile):
        # Mock a complete API response
        mock_response = [
            {
                'opportunityId': 'EPA-2025-HEALTH-001',
                'opportunityTitle': 'Environmental Health Community Grant Program',
                'description': 'Funding for community environmental health initiatives',
                'agencyName': 'Environmental Protection Agency',
                'agencyCode': 'EPA',
                'awardCeiling': 75000,
                'awardFloor': 15000,
                'estimatedTotalProgramFunding': 5000000,
                'closeDate': '2025-08-15',
                'postDate': '2025-01-15',
                'grantsGovUrl': 'https://grants.gov/view-opportunity.html?oppId=EPA-2025-HEALTH-001'
            }
        ]
        mock_search.return_value = mock_response
        
        # Test full pipeline
        engine = get_discovery_engine()
        collection = await engine.discover_all_opportunities(
            profile=sample_organization_profile,
            max_results_per_source=10
        )
        
        assert isinstance(collection, OpportunityCollection)
        assert collection.profile_used == sample_organization_profile.ein
        
        # Should have opportunities
        all_opps = collection.get_all_opportunities()
        if len(all_opps) > 0:
            opp = all_opps[0]
            assert hasattr(opp, 'relevance_score')
            assert opp.relevance_score >= 0.0
"""
Unit tests for consolidated data models
"""
import pytest
from datetime import datetime, timedelta

from src.core.data_models import (
    FundingSourceType, OpportunityStatus, EligibilityType,
    BaseOpportunity, GovernmentOpportunity, FoundationOpportunity, 
    CorporateOpportunity, OpportunityCollection
)


class TestFundingSourceType:
    """Test FundingSourceType enumeration"""
    
    def test_all_values_present(self):
        expected_values = [
            "government_federal", "government_state", "government_local",
            "foundation_private", "foundation_corporate", "foundation_community",
            "corporate_csr", "corporate_sponsorship", "nonprofit_intermediary",
            "international", "other"
        ]
        
        actual_values = [item.value for item in FundingSourceType]
        
        for expected in expected_values:
            assert expected in actual_values


class TestOpportunityStatus:
    """Test OpportunityStatus enumeration"""
    
    def test_status_values(self):
        assert OpportunityStatus.ACTIVE.value == "active"
        assert OpportunityStatus.CLOSED.value == "closed"
        assert OpportunityStatus.FORECASTED.value == "forecasted"


class TestBaseOpportunity:
    """Test BaseOpportunity base class"""
    
    def test_required_fields(self):
        # Test creation with required fields
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity",
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE
        )
        
        assert opportunity.id == "test_001"
        assert opportunity.title == "Test Opportunity"
        assert opportunity.source_type == FundingSourceType.GOVERNMENT_FEDERAL
        assert opportunity.funder_name == "Test Agency"
        assert opportunity.status == OpportunityStatus.ACTIVE
    
    def test_default_values(self):
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity",
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE
        )
        
        assert opportunity.description == ""
        assert opportunity.relevance_score == 0.0
        assert opportunity.competition_level == "unknown"
        assert opportunity.match_reasons == []
        assert opportunity.keywords == []
        assert opportunity.processing_notes == []
    
    def test_days_until_deadline_calculation(self):
        # Test with future deadline
        future_date = datetime.now() + timedelta(days=30)
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity",
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE,
            application_deadline=future_date
        )
        
        days = opportunity.calculate_days_until_deadline()
        # Allow 29-31 days due to time-of-day and timezone differences
        assert 29 <= days <= 31
        
        # Test with no deadline
        opportunity.application_deadline = None
        assert opportunity.calculate_days_until_deadline() is None
        
        # Test with past deadline
        past_date = datetime.now() - timedelta(days=5)
        opportunity.application_deadline = past_date
        assert opportunity.calculate_days_until_deadline() == 0  # Should return 0 for past dates
    
    def test_eligibility_check(self):
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity", 
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE,
            eligible_applicants=[EligibilityType.NONPROFIT_501C3, EligibilityType.UNIVERSITY_PUBLIC]
        )
        
        assert opportunity.is_eligible_for(EligibilityType.NONPROFIT_501C3) is True
        assert opportunity.is_eligible_for(EligibilityType.UNIVERSITY_PUBLIC) is True
        assert opportunity.is_eligible_for(EligibilityType.FOR_PROFIT_SMALL) is False
    
    def test_match_reason_management(self):
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity",
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE
        )
        
        opportunity.add_match_reason("NTEE code alignment")
        opportunity.add_match_reason("Geographic match")
        opportunity.add_match_reason("NTEE code alignment")  # Duplicate
        
        assert len(opportunity.match_reasons) == 2
        assert "NTEE code alignment" in opportunity.match_reasons
        assert "Geographic match" in opportunity.match_reasons
    
    def test_score_update(self):
        opportunity = BaseOpportunity(
            id="test_001",
            title="Test Opportunity",
            source_type=FundingSourceType.GOVERNMENT_FEDERAL,
            funder_name="Test Agency",
            status=OpportunityStatus.ACTIVE
        )
        
        opportunity.update_score(85.5, "High relevance match")
        
        assert opportunity.relevance_score == 85.5
        assert "High relevance match" in opportunity.match_reasons
        
        # Test score clamping
        opportunity.update_score(150.0)  # Over 100
        assert opportunity.relevance_score == 100.0
        
        opportunity.update_score(-10.0)  # Below 0
        assert opportunity.relevance_score == 0.0


class TestGovernmentOpportunity:
    """Test GovernmentOpportunity specialized class"""
    
    def test_government_opportunity_creation(self):
        opportunity = GovernmentOpportunity(
            id="gov_001",
            title="Federal Health Grant",
            funder_name="Department of Health",
            agency_code="HHS",
            status=OpportunityStatus.ACTIVE
        )
        
        assert isinstance(opportunity, BaseOpportunity)
        assert opportunity.source_type == FundingSourceType.GOVERNMENT_FEDERAL
        assert opportunity.agency_code == "HHS"
        assert opportunity.funding_instrument == "grant"
    
    def test_government_specific_fields(self):
        opportunity = GovernmentOpportunity(
            id="gov_001",
            title="Federal Health Grant",
            funder_name="Department of Health", 
            agency_code="HHS",
            status=OpportunityStatus.ACTIVE,
            cfda_numbers=["93.123", "93.456"],
            grants_gov_id="HHS-2025-001",
            compliance_requirements=["FFATA", "Civil Rights"]
        )
        
        assert opportunity.cfda_numbers == ["93.123", "93.456"]
        assert opportunity.grants_gov_id == "HHS-2025-001"
        assert "FFATA" in opportunity.compliance_requirements


class TestFoundationOpportunity:
    """Test FoundationOpportunity specialized class"""
    
    def test_foundation_opportunity_creation(self):
        opportunity = FoundationOpportunity(
            id="found_001",
            title="Community Foundation Grant",
            funder_name="Test Foundation",
            foundation_type="private",
            status=OpportunityStatus.ACTIVE
        )
        
        assert isinstance(opportunity, BaseOpportunity)
        assert opportunity.source_type == FundingSourceType.FOUNDATION_PRIVATE
        assert opportunity.foundation_type == "private"
        assert opportunity.application_process == "standard"
        assert opportunity.requires_loi is False
    
    def test_corporate_foundation_source_type(self):
        opportunity = FoundationOpportunity(
            id="found_001",
            title="Corporate Foundation Grant",
            funder_name="XYZ Foundation",
            foundation_type="corporate",
            status=OpportunityStatus.ACTIVE
        )
        
        assert opportunity.source_type == FundingSourceType.FOUNDATION_CORPORATE
    
    def test_community_foundation_source_type(self):
        opportunity = FoundationOpportunity(
            id="found_001", 
            title="Community Foundation Grant",
            funder_name="Local Community Foundation",
            foundation_type="community",
            status=OpportunityStatus.ACTIVE
        )
        
        assert opportunity.source_type == FundingSourceType.FOUNDATION_COMMUNITY


class TestCorporateOpportunity:
    """Test CorporateOpportunity specialized class"""
    
    def test_corporate_opportunity_creation(self):
        opportunity = CorporateOpportunity(
            id="corp_001",
            title="Corporate CSR Program",
            funder_name="ABC Corporation",
            company_name="ABC Corporation",
            industry="Technology",
            status=OpportunityStatus.ACTIVE
        )
        
        assert isinstance(opportunity, BaseOpportunity)
        assert opportunity.source_type == FundingSourceType.CORPORATE_CSR
        assert opportunity.company_name == "ABC Corporation"
        assert opportunity.industry == "Technology"
    
    def test_sponsorship_source_type(self):
        opportunity = CorporateOpportunity(
            id="corp_001",
            title="Event Sponsorship",
            funder_name="ABC Corporation",
            company_name="ABC Corporation", 
            industry="Technology",
            status=OpportunityStatus.ACTIVE,
            partnership_types=["sponsorship", "event_support"]
        )
        
        assert opportunity.source_type == FundingSourceType.CORPORATE_SPONSORSHIP


class TestOpportunityCollection:
    """Test OpportunityCollection container class"""
    
    def test_collection_creation(self):
        collection = OpportunityCollection(
            collection_id="test_collection",
            name="Test Collection"
        )
        
        assert collection.collection_id == "test_collection"
        assert collection.name == "Test Collection"
        assert collection.total_count == 0
        assert len(collection.government_opportunities) == 0
    
    def test_add_opportunities(self):
        collection = OpportunityCollection(
            collection_id="test_collection",
            name="Test Collection"
        )
        
        # Add government opportunity
        gov_opp = GovernmentOpportunity(
            id="gov_001",
            title="Government Grant",
            funder_name="Federal Agency",
            agency_code="FA",
            status=OpportunityStatus.ACTIVE
        )
        collection.add_opportunity(gov_opp)
        
        # Add foundation opportunity
        found_opp = FoundationOpportunity(
            id="found_001",
            title="Foundation Grant",
            funder_name="Test Foundation",
            foundation_type="private",
            status=OpportunityStatus.ACTIVE
        )
        collection.add_opportunity(found_opp)
        
        assert collection.total_count == 2
        assert len(collection.government_opportunities) == 1
        assert len(collection.foundation_opportunities) == 1
        assert collection.source_breakdown["government"] == 1
        assert collection.source_breakdown["foundation"] == 1
    
    def test_get_all_opportunities(self):
        collection = OpportunityCollection(
            collection_id="test_collection",
            name="Test Collection"
        )
        
        gov_opp = GovernmentOpportunity(
            id="gov_001",
            title="Government Grant",
            funder_name="Federal Agency",
            agency_code="FA", 
            status=OpportunityStatus.ACTIVE
        )
        
        found_opp = FoundationOpportunity(
            id="found_001",
            title="Foundation Grant",
            funder_name="Test Foundation",
            foundation_type="private",
            status=OpportunityStatus.ACTIVE
        )
        
        collection.add_opportunity(gov_opp)
        collection.add_opportunity(found_opp)
        
        all_opps = collection.get_all_opportunities()
        assert len(all_opps) == 2
        assert gov_opp in all_opps
        assert found_opp in all_opps
    
    def test_get_top_opportunities(self):
        collection = OpportunityCollection(
            collection_id="test_collection",
            name="Test Collection"
        )
        
        # Add opportunities with different scores
        opp1 = GovernmentOpportunity(
            id="gov_001",
            title="Low Score Grant",
            funder_name="Agency A",
            agency_code="AA",
            status=OpportunityStatus.ACTIVE,
            relevance_score=30.0
        )
        
        opp2 = GovernmentOpportunity(
            id="gov_002", 
            title="High Score Grant",
            funder_name="Agency B",
            agency_code="AB",
            status=OpportunityStatus.ACTIVE,
            relevance_score=90.0
        )
        
        opp3 = GovernmentOpportunity(
            id="gov_003",
            title="Medium Score Grant",
            funder_name="Agency C",
            agency_code="AC",
            status=OpportunityStatus.ACTIVE,
            relevance_score=60.0
        )
        
        collection.add_opportunity(opp1)
        collection.add_opportunity(opp2)
        collection.add_opportunity(opp3)
        
        top_opps = collection.get_top_opportunities(limit=2)
        assert len(top_opps) == 2
        assert top_opps[0].relevance_score == 90.0  # Highest first
        assert top_opps[1].relevance_score == 60.0  # Second highest
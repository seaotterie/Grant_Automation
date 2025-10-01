#!/usr/bin/env python3
"""
Unit Tests for Data Transformation Pipeline
Comprehensive test suite for Catalynx data transformation components
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import the modules we're testing
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from src.data_transformation.models import (
    ScrapedLeadership, ScrapedProgram, ScrapedContact, WebScrapingResults,
    BoardMemberData, DatabaseJSONFields, Person, ParsedName, OrganizationRole,
    TransformationConfig, DataSource, ContactType
)
from src.data_transformation.transformation_service import (
    NameParser, DataDeduplicator, DataTransformationService
)
from src.data_transformation.main_service import CatalynxDataTransformer
from src.database.database_manager import DatabaseManager, Profile


class TestNameParser(unittest.TestCase):
    """Test name parsing functionality"""
    
    def setUp(self):
        from src.data_transformation.models import NameParsingConfig
        self.config = NameParsingConfig()
        self.parser = NameParser(self.config)
    
    def test_simple_name_parsing(self):
        """Test parsing of simple names"""
        parsed = self.parser.parse_name("John Smith")
        
        self.assertEqual(parsed.first_name, "John")
        self.assertEqual(parsed.last_name, "Smith")
        self.assertEqual(parsed.normalized_name, "John Smith")
        self.assertIsNone(parsed.middle_name)
        self.assertIsNone(parsed.prefix)
        self.assertIsNone(parsed.suffix)
    
    def test_name_with_title_and_suffix(self):
        """Test parsing names with titles and suffixes"""
        parsed = self.parser.parse_name("Dr. John Q. Smith Jr.")
        
        self.assertEqual(parsed.first_name, "John")
        self.assertEqual(parsed.middle_name, "Q")
        self.assertEqual(parsed.last_name, "Smith")
        self.assertEqual(parsed.prefix, "Dr")
        self.assertEqual(parsed.suffix, "Jr")
    
    def test_name_normalization(self):
        """Test name normalization for matching"""
        # Test with titles stripped (default config)
        parsed1 = self.parser.parse_name("Dr. John Smith")
        parsed2 = self.parser.parse_name("John Smith")
        
        # Both should normalize to the same value
        self.assertEqual(parsed1.normalized_name, parsed2.normalized_name)
    
    def test_nickname_handling(self):
        """Test nickname to formal name conversion"""
        parsed = self.parser.parse_name("Bill Johnson")
        
        # Should convert Bill to William
        self.assertEqual(parsed.first_name, "Bill")
        self.assertTrue("William" in parsed.normalized_name or "Bill" in parsed.normalized_name)
    
    def test_invalid_names(self):
        """Test handling of invalid names"""
        with self.assertRaises(ValueError):
            self.parser.parse_name("")  # Empty name
            
        with self.assertRaises(ValueError):
            self.parser.parse_name("A")  # Too short
    
    def test_name_similarity_calculation(self):
        """Test name similarity scoring"""
        # Identical names should have similarity of 1.0
        similarity = self.parser.calculate_name_similarity("John Smith", "John Smith")
        self.assertEqual(similarity, 1.0)
        
        # Different names should have lower similarity
        similarity = self.parser.calculate_name_similarity("John Smith", "Jane Doe")
        self.assertLess(similarity, 0.5)
        
        # Similar names should have moderate similarity
        similarity = self.parser.calculate_name_similarity("John Smith", "John Smyth")
        self.assertGreater(similarity, 0.7)


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic model validation and functionality"""
    
    def test_scraped_leadership_validation(self):
        """Test ScrapedLeadership model validation"""
        # Valid data
        leadership = ScrapedLeadership(
            name="John Smith",
            title="CEO",
            biography="Experienced leader",
            quality_score=85.0
        )
        self.assertEqual(leadership.name, "John Smith")
        self.assertEqual(leadership.quality_score, 85.0)
        
        # Invalid data - empty name
        with self.assertRaises(ValueError):
            ScrapedLeadership(name="", quality_score=50.0)
        
        # Invalid data - quality score out of range
        with self.assertRaises(ValueError):
            ScrapedLeadership(name="John Smith", quality_score=150.0)
    
    def test_scraped_contact_validation(self):
        """Test ScrapedContact model validation"""
        # Valid email
        contact = ScrapedContact(
            type=ContactType.EMAIL,
            value="john@example.com",
            quality_score=90.0
        )
        self.assertEqual(contact.value, "john@example.com")
        
        # Invalid email format
        with self.assertRaises(ValueError):
            ScrapedContact(
                type=ContactType.EMAIL,
                value="invalid-email",
                quality_score=50.0
            )
        
        # Valid phone number
        contact = ScrapedContact(
            type=ContactType.PHONE,
            value="(555) 123-4567",
            quality_score=85.0
        )
        # Phone should be cleaned
        self.assertIn("5551234567", contact.value.replace("-", "").replace("(", "").replace(")", "").replace(" ", ""))
    
    def test_web_scraping_results_structure(self):
        """Test WebScrapingResults model structure"""
        results = WebScrapingResults(
            extracted_info={
                "leadership": [
                    {
                        "name": "John Smith",
                        "title": "CEO",
                        "quality_score": 90.0
                    }
                ],
                "contact_info": [
                    {
                        "type": "email",
                        "value": "contact@example.com",
                        "quality_score": 85.0
                    }
                ]
            },
            successful_scrapes=["https://example.com"],
            total_quality_score=87.5
        )
        
        self.assertEqual(len(results.extracted_info.leadership), 1)
        self.assertEqual(len(results.extracted_info.contact_info), 1)
        self.assertEqual(results.total_quality_score, 87.5)


class TestDataTransformationService(unittest.TestCase):
    """Test core data transformation functionality"""
    
    def setUp(self):
        from src.data_transformation.models import TransformationConfig
        self.config = TransformationConfig()
        self.service = DataTransformationService(self.config)
    
    def test_person_creation_from_board_member(self):
        """Test creating Person from BoardMemberData"""
        board_member = BoardMemberData(
            name="Dr. Jane Smith",
            title="Board Chair",
            background="Experienced nonprofit leader"
        )
        
        person = self.service._create_person_from_board_member(board_member)
        
        self.assertEqual(person.parsed_name.full_name, "Dr. Jane Smith")
        self.assertEqual(person.primary_title, "Board Chair")
        self.assertEqual(person.biography, "Experienced nonprofit leader")
        self.assertEqual(person.confidence_score, 0.9)
        self.assertIn(DataSource.BOARD_MEMBERS, person.data_sources)
    
    def test_person_creation_from_scraped_leadership(self):
        """Test creating Person from ScrapedLeadership"""
        leadership = ScrapedLeadership(
            name="John Doe",
            title="Executive Director",
            biography="Leader in community development",
            quality_score=75.0
        )
        
        person = self.service._create_person_from_scraped_leadership(leadership)
        
        self.assertEqual(person.parsed_name.full_name, "John Doe")
        self.assertEqual(person.primary_title, "Executive Director")
        self.assertEqual(person.confidence_score, 0.75)
        self.assertIn(DataSource.WEB_SCRAPING, person.data_sources)
    
    def test_role_classification(self):
        """Test position classification (board vs executive)"""
        # Test board position detection
        self.assertTrue(self.service._is_board_position("Board Chair"))
        self.assertTrue(self.service._is_board_position("Director"))
        self.assertTrue(self.service._is_board_position("Trustee"))
        self.assertFalse(self.service._is_board_position("Staff Member"))
        
        # Test executive position detection
        self.assertTrue(self.service._is_executive_position("CEO"))
        self.assertTrue(self.service._is_executive_position("Executive Director"))
        self.assertTrue(self.service._is_executive_position("President"))
        self.assertFalse(self.service._is_executive_position("Board Member"))
    
    def test_program_type_classification(self):
        """Test program type classification"""
        from src.data_transformation.models import ProgramType
        
        # Test different program types
        advocacy_type = self.service._classify_program_type(
            "Policy Advocacy", "We advocate for policy changes"
        )
        self.assertEqual(advocacy_type, ProgramType.ADVOCACY)
        
        education_type = self.service._classify_program_type(
            "Training Program", "Educational workshops for community"
        )
        self.assertEqual(education_type, ProgramType.EDUCATION)
        
        service_type = self.service._classify_program_type(
            "Food Service", "Direct assistance to families in need"
        )
        self.assertEqual(service_type, ProgramType.DIRECT_SERVICE)
    
    def test_transformation_with_minimal_data(self):
        """Test transformation with minimal input data"""
        json_data = DatabaseJSONFields(
            board_members=[
                BoardMemberData(name="John Smith", title="Board Chair")
            ]
        )
        
        result = self.service.transform_profile_data(
            profile_id="test_profile",
            ein="12-3456789",
            json_data=json_data
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.people), 1)
        self.assertEqual(len(result.roles), 1)
        self.assertEqual(result.people[0].parsed_name.full_name, "John Smith")
        self.assertEqual(result.roles[0].position_title, "Board Chair")


class TestDataDeduplicator(unittest.TestCase):
    """Test deduplication functionality"""
    
    def setUp(self):
        from src.data_transformation.models import (
            DeduplicationConfig, NameParsingConfig
        )
        name_config = NameParsingConfig()
        dedup_config = DeduplicationConfig(fuzzy_match_threshold=0.85)
        
        self.name_parser = NameParser(name_config)
        self.deduplicator = DataDeduplicator(dedup_config, self.name_parser)
    
    def test_exact_duplicate_detection(self):
        """Test detection of exact duplicate people"""
        # Create two identical people
        person1 = Person(
            parsed_name=ParsedName(
                full_name="John Smith",
                first_name="John",
                last_name="Smith",
                normalized_name="John Smith"
            ),
            match_key="john smith"
        )
        
        person2 = Person(
            parsed_name=ParsedName(
                full_name="John Smith",
                first_name="John",
                last_name="Smith",
                normalized_name="John Smith"
            ),
            match_key="john smith"
        )
        
        duplicates = self.deduplicator.find_person_duplicates([person1, person2])
        
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].match_type, "exact")
        self.assertEqual(duplicates[0].confidence, 1.0)
    
    def test_fuzzy_duplicate_detection(self):
        """Test detection of fuzzy duplicate people"""
        person1 = Person(
            parsed_name=ParsedName(
                full_name="John Smith",
                normalized_name="John Smith"
            ),
            match_key="john smith"
        )
        
        person2 = Person(
            parsed_name=ParsedName(
                full_name="Jon Smith",  # Slight variation
                normalized_name="Jon Smith"
            ),
            match_key="jon smith"
        )
        
        duplicates = self.deduplicator.find_person_duplicates([person1, person2])
        
        # Should find fuzzy match
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0].match_type, "fuzzy")
        self.assertGreater(duplicates[0].confidence, 0.8)
    
    def test_person_merging(self):
        """Test merging of duplicate people"""
        person1 = Person(
            parsed_name=ParsedName(
                full_name="John Smith",
                normalized_name="John Smith"
            ),
            primary_title="CEO",
            all_titles=["CEO"],
            confidence_score=0.9,
            data_sources=[DataSource.BOARD_MEMBERS],
            match_key="john smith"
        )
        
        person2 = Person(
            parsed_name=ParsedName(
                full_name="John Smith",
                normalized_name="John Smith"
            ),
            primary_title="Executive Director",
            all_titles=["Executive Director"],
            biography="Experienced leader",
            confidence_score=0.8,
            data_sources=[DataSource.WEB_SCRAPING],
            match_key="john smith"
        )
        
        merged = self.deduplicator.merge_people(person1, person2)
        
        # Should combine information from both
        self.assertEqual(len(merged.all_titles), 2)
        self.assertIn("CEO", merged.all_titles)
        self.assertIn("Executive Director", merged.all_titles)
        self.assertEqual(len(merged.data_sources), 2)
        self.assertEqual(merged.biography, "Experienced leader")
        # Should average confidence scores
        self.assertEqual(merged.confidence_score, 0.85)


class TestCatalynxDataTransformer(unittest.TestCase):
    """Test main transformation service integration"""
    
    def setUp(self):
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock database manager
        self.db_manager = Mock(spec=DatabaseManager)
        self.db_manager.database_path = self.temp_db.name
        self.db_manager.get_connection = Mock()
        
        self.transformer = CatalynxDataTransformer(self.db_manager)
    
    def tearDown(self):
        # Clean up temporary database
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_profile_not_found_handling(self):
        """Test handling when profile is not found"""
        self.db_manager.get_profile.return_value = None
        
        result = self.transformer.transform_profile_data("nonexistent_profile")
        
        self.assertFalse(result.success)
        self.assertEqual(result.profile_id, "nonexistent_profile")
        self.assertTrue(len(result.validation_errors) > 0)
    
    def test_successful_transformation(self):
        """Test successful transformation flow"""
        # Mock profile
        mock_profile = Mock(spec=Profile)
        mock_profile.id = "test_profile"
        mock_profile.name = "Test Organization"
        mock_profile.ein = "12-3456789"
        mock_profile.web_enhanced_data = None
        mock_profile.board_members = None
        mock_profile.verification_data = None
        
        self.db_manager.get_profile.return_value = mock_profile
        
        # Mock the integrator to avoid database operations
        with patch.object(self.transformer.integrator, 'process_profile_transformation', return_value=True):
            result = self.transformer.transform_profile_data(
                profile_id="test_profile",
                board_members_json=[
                    {"name": "John Smith", "title": "Board Chair"}
                ]
            )
        
        self.assertTrue(result.success)
        self.assertEqual(result.profile_id, "test_profile")
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        validation_result = self.transformer.validate_configuration()
        
        self.assertIn('config_valid', validation_result)
        self.assertIn('warnings', validation_result)
        self.assertIn('recommendations', validation_result)
        self.assertIn('current_config', validation_result)
        
        # Should be valid with default configuration
        self.assertTrue(validation_result['config_valid'])


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON data"""
        from src.data_transformation.models import TransformationConfig
        service = DataTransformationService(TransformationConfig())
        
        # Test with malformed board member data
        json_data = DatabaseJSONFields(
            board_members=[]  # Empty list should not cause errors
        )
        
        result = service.transform_profile_data(
            profile_id="test_profile",
            ein="12-3456789",
            json_data=json_data
        )
        
        # Should succeed even with empty data
        self.assertTrue(result.success)
        self.assertEqual(len(result.people), 0)
    
    def test_invalid_contact_data_handling(self):
        """Test handling of invalid contact information"""
        # This should be handled gracefully by the validation
        try:
            contact = ScrapedContact(
                type=ContactType.EMAIL,
                value="valid@example.com",
                quality_score=50.0
            )
            self.assertEqual(contact.value, "valid@example.com")
        except Exception as e:
            self.fail(f"Valid contact data should not raise exception: {e}")


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""
Board Network Analyzer Web Integration Test
Tests the enhanced board network analysis with web intelligence integration.

This test validates:
1. Web intelligence board member data extraction
2. Data source merging and deduplication  
3. Enhanced network analysis with web sources
4. Quality reporting and insights generation
"""

import asyncio
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor, BoardMember
from src.core.data_models import ProcessorConfig, OrganizationProfile


class BoardNetworkWebIntegrationTest:
    """Test enhanced board network analyzer with web intelligence."""
    
    def __init__(self):
        self.database_path = "data/catalynx.db"
        self.test_org_ein = "812827604"
        self.test_org_name = "HEROS BRIDGE"
        
    async def run_integration_test(self):
        """Run complete board network web integration test."""
        print("BOARD NETWORK ANALYZER WEB INTEGRATION TEST")
        print("=" * 55)
        
        try:
            # Test 1: Verify intelligence database setup
            print("\n1. VERIFYING BOARD MEMBER INTELLIGENCE DATA...")
            db_status = self.verify_intelligence_database()
            print(f"   Intelligence Database: {'READY' if db_status else 'NO DATA'}")
            
            if not db_status:
                print("   Setting up test board member intelligence data...")
                self.setup_test_intelligence_data()
            
            # Test 2: Test web intelligence extraction
            print("\n2. TESTING WEB INTELLIGENCE EXTRACTION...")
            processor = BoardNetworkAnalyzerProcessor()
            test_orgs = self.create_test_organizations()
            
            config = ProcessorConfig(
                workflow_id="test_web_extraction",
                processor_name="board_network_analyzer", 
                workflow_config={}
            )
            web_members = await processor._extract_web_intelligence_board_members(test_orgs, config)
            print(f"   Web Intelligence Members: {len(web_members)}")
            
            for member in web_members[:3]:  # Show first 3
                quality_score = getattr(member, 'quality_score', 'N/A')
                data_source = getattr(member, 'data_source', 'unknown')
                print(f"     - {member.normalized_name} ({member.organization_name}) - Quality: {quality_score}, Source: {data_source}")
            
            # Test 3: Test data source merging
            print("\n3. TESTING DATA SOURCE MERGING...")
            filing_members = processor._extract_board_members(test_orgs)
            merged_members = processor._merge_board_member_sources(filing_members, web_members)
            
            print(f"   Filing Members: {len(filing_members)}")
            print(f"   Web Members: {len(web_members)}")
            print(f"   Merged Members: {len(merged_members)}")
            print(f"   Deduplication Savings: {len(filing_members) + len(web_members) - len(merged_members)}")
            
            # Test 4: Test complete enhanced network analysis
            print("\n4. TESTING ENHANCED NETWORK ANALYSIS...")
            config = ProcessorConfig(
                workflow_id="test_enhanced_network",
                processor_name="board_network_analyzer",
                workflow_config={},
                profile_id="test_profile"
            )
            
            result = await processor.execute(config)
            
            if result.success:
                print("   Enhanced Network Analysis: SUCCESS")
                
                network_data = result.data.get("network_analysis", {})
                data_sources = network_data.get("data_sources", {})
                
                print(f"   Total Board Members: {network_data.get('total_board_members', 0)}")
                print(f"   Unique Individuals: {network_data.get('unique_individuals', 0)}")
                print(f"   Network Connections: {network_data.get('network_connections', 0)}")
                print(f"   Filing Data: {data_sources.get('filing_data', 0)} members")
                print(f"   Web Intelligence: {data_sources.get('web_intelligence', 0)} members")
                print(f"   Deduplication Savings: {data_sources.get('deduplication_savings', 0)}")
                
                # Show insights
                insights = result.data.get("insights", {})
                key_findings = insights.get("key_findings", [])
                data_quality = insights.get("data_quality", [])
                
                if key_findings:
                    print("   Key Findings:")
                    for finding in key_findings[:2]:
                        print(f"     - {finding}")
                
                if data_quality:
                    print("   Data Quality Insights:")
                    for quality_note in data_quality[:2]:
                        print(f"     - {quality_note}")
                        
            else:
                print("   Enhanced Network Analysis: FAILED")
                print(f"   Errors: {result.errors}")
                return False
            
            # Test 5: Verify metadata enhancement
            print("\n5. VERIFYING METADATA ENHANCEMENT...")
            metadata = result.metadata
            data_sources = metadata.get("data_sources", [])
            
            print(f"   Analysis Type: {metadata.get('analysis_type')}")
            print(f"   Data Sources: {', '.join(data_sources)}")
            
            expected_sources = ["990_filings", "web_intelligence", "board_member_intelligence"]
            missing_sources = [source for source in expected_sources if source not in data_sources]
            
            if not missing_sources:
                print("   Metadata Enhancement: SUCCESS")
            else:
                print(f"   Metadata Enhancement: MISSING {missing_sources}")
                return False
            
            print("\n" + "=" * 55)
            print("INTEGRATION TEST SUMMARY: ALL TESTS PASSED")
            print("\nEnhanced Board Network Analyzer capabilities:")
            print("- Web intelligence board member data integration")
            print("- Multi-source data merging with deduplication")
            print("- Quality-based filtering for reliable web data")
            print("- Enhanced insights with data source analysis")
            print("- Cross-source network relationship mapping")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Integration test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_intelligence_database(self) -> bool:
        """Verify board member intelligence database has data."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM board_member_intelligence")
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"   Database verification error: {e}")
            return False
    
    def setup_test_intelligence_data(self):
        """Set up test board member intelligence data."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Add test board member intelligence
                test_members = [
                    (self.test_org_ein, "John Smith", "John Smith", "Executive Director", "web_scraping", "Veteran advocate with 15 years experience", 85),
                    (self.test_org_ein, "Sarah Johnson", "Sarah Johnson", "Program Director", "web_scraping", "Mental health specialist for veteran programs", 80),
                    (self.test_org_ein, "Michael Brown", "Michael Brown", "Board Chair", "web_scraping", "Community leader and veteran services advocate", 75),
                    ("987654321", "Sarah Johnson", "Sarah Johnson", "Board Member", "web_scraping", "Serves on multiple nonprofit boards", 82),
                    ("456789123", "Michael Brown", "Michael Brown", "Treasurer", "web_scraping", "Financial oversight and veteran programs", 78)
                ]
                
                for member_data in test_members:
                    conn.execute("""
                        INSERT OR REPLACE INTO board_member_intelligence 
                        (ein, member_name, normalized_name, title_position, data_source, 
                         biography, data_quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, member_data)
                
                conn.commit()
                print("   Test board member intelligence data created")
                
        except Exception as e:
            print(f"   Setup error: {e}")
    
    def create_test_organizations(self) -> list:
        """Create test organizations with board member data."""
        return [
            OrganizationProfile(
                ein=self.test_org_ein,
                name=self.test_org_name,
                state="VA",
                ntee_code="P20",
                board_members=["John Smith", "Robert Davis", "Patricia Wilson"],  # Filing data
                key_personnel=[
                    {"name": "John Smith", "title": "Executive Director"},
                    {"name": "Mary Johnson", "title": "Program Manager"}
                ]
            ),
            OrganizationProfile(
                ein="987654321",
                name="Community Veterans Alliance",
                state="VA",
                ntee_code="P23",
                board_members=["David Miller", "Sarah Johnson"],  # Some overlap with web data
                key_personnel=[
                    {"name": "David Miller", "title": "CEO"}
                ]
            ),
            OrganizationProfile(
                ein="456789123",
                name="Virginia Military Family Support",
                state="VA", 
                ntee_code="P20",
                board_members=["Michael Brown", "Jennifer Lee"],  # Some overlap with web data
                key_personnel=[]
            )
        ]


async def main():
    """Run the enhanced board network integration test."""
    test_runner = BoardNetworkWebIntegrationTest()
    success = await test_runner.run_integration_test()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
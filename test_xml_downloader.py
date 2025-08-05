#!/usr/bin/env python3
"""
Test XML Downloader with corrected ProPublica object_id method
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.data_models import WorkflowConfig, ProcessorConfig, OrganizationProfile
from src.processors import get_processor


async def test_xml_downloader():
    """Test XML downloader with ProPublica object_id method."""
    print("Testing XML Downloader with ProPublica Object ID Method")
    print("=" * 60)
    
    # Test EIN that should have XML available
    test_ein = "541669652"
    print(f"Testing EIN: {test_ein}")
    
    try:
        # Get XML downloader processor
        xml_processor = get_processor("xml_downloader")
        if not xml_processor:
            print("ERROR: XML downloader processor not found")
            return False
        
        print("XML downloader processor found!")
        
        # Create a mock organization with high score to trigger XML download
        test_org = OrganizationProfile(
            ein=test_ein,
            name="Test Organization",
            state="VA",
            composite_score=0.8,  # High score to trigger download
            revenue=1000000,
            filing_years=[2022, 2021, 2020]
        )
        
        # Create workflow config
        workflow_config = WorkflowConfig(
            workflow_id="test_xml_downloader",
            target_ein=test_ein,
            name="XML Downloader Test"
        )
        
        # Create processor config
        processor_config = ProcessorConfig(
            workflow_id=workflow_config.workflow_id,
            processor_name="xml_downloader",
            workflow_config=workflow_config
        )
        
        # Create mock previous step results (simulate financial scorer output)
        mock_financial_results = {
            "organizations": [test_org.dict()],
            "scoring_stats": {"total_scored": 1}
        }
        
        # For testing, we'll manually inject the mock data
        # In real workflow, this comes from the financial scorer
        print("Finding ProPublica object_id and downloading XML...")
        
        # Test the object_id finding specifically
        import aiohttp
        async with aiohttp.ClientSession() as session:
            object_id = await xml_processor._find_object_id(session, test_ein)
            if object_id:
                print(f"Found object_id: {object_id}")
                
                # Test the full download process
                xml_info = {
                    "ein": test_ein,
                    "name": "Test Organization",
                    "object_id": None,
                    "cache_path": None
                }
                
                download_result = await xml_processor._download_xml_file(xml_info)
                
                print(f"\nDownload Results:")
                print(f"Success: {download_result['success']}")
                print(f"Object ID: {download_result['object_id']}")
                print(f"File Path: {download_result['file_path']}")
                print(f"Cached: {download_result['cached']}")
                
                if download_result['error']:
                    print(f"Error: {download_result['error']}")
                
                if download_result['success']:
                    file_path = Path(download_result['file_path'])
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        print(f"File Size: {file_size:,} bytes")
                        
                        # Try to parse a bit of the XML to verify it's valid
                        try:
                            import xml.etree.ElementTree as ET
                            tree = ET.parse(file_path)
                            root = tree.getroot()
                            print(f"XML Root Tag: {root.tag}")
                            print("XML file appears to be valid!")
                        except ET.ParseError as e:
                            print(f"XML parsing error: {e}")
                
                return download_result['success']
            else:
                print("No object_id found - XML may not be available for this EIN")
                return False
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_xml_downloader())
    print(f"\nXML Downloader Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
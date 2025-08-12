#!/usr/bin/env python3
"""
Direct test of EIN lookup functionality without web server
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_ein_lookup_directly():
    """Test the EIN lookup processor directly"""
    
    print("Testing EIN Lookup Processor Directly")
    print("=" * 40)
    
    try:
        from src.processors.lookup.ein_lookup import EINLookupProcessor
        from src.utils.validators import validate_ein, normalize_ein
        from src.core.data_models import ProcessorConfig
        
        # Test EIN
        test_ein = "13-1628593"  # American Red Cross
        
        print(f"Testing EIN: {test_ein}")
        
        # Validate and normalize EIN
        normalized_ein = normalize_ein(test_ein)
        validate_ein(normalized_ein)
        print(f"Normalized EIN: {normalized_ein}")
        
        # Create processor config
        config = ProcessorConfig(
            workflow_config=type('WorkflowConfig', (), {
                'target_ein': normalized_ein,
                'research_parameters': {}
            })(),
            processor_config={}
        )
        
        # Test EIN lookup
        print("Running EIN lookup...")
        ein_processor = EINLookupProcessor()
        result = ein_processor.execute_sync(config)
        
        if result.success:
            print("SUCCESS!")
            org_data = result.data.get('organization_profile', {})
            print(f"Organization Name: {org_data.get('name', 'Unknown')}")
            print(f"State: {org_data.get('state', 'Unknown')}")
            print(f"Revenue: ${org_data.get('total_revenue', 0):,}" if org_data.get('total_revenue') else "Revenue: Unknown")
            print(f"NTEE Code: {org_data.get('ntee_code', 'Unknown')}")
            print(f"Address: {org_data.get('address', 'Unknown')}")
            print(f"Available fields: {list(org_data.keys())}")
            
            # Test profile creation logic
            print("\nTesting profile creation logic...")
            from src.profiles.service import ProfileService
            from src.profiles.models import OrganizationType, FundingType
            
            profile_data = {
                "name": org_data.get('name') or f"Organization {normalized_ein}",
                "organization_type": OrganizationType.NONPROFIT,
                "ein": normalized_ein,
                "mission_statement": org_data.get('mission') or "Mission statement to be updated",
                "focus_areas": org_data.get('ntee_description', '').split(', ') if org_data.get('ntee_description') else ["General charitable purposes"],
                "program_areas": org_data.get('program_areas', []) or [],
                "target_populations": [],
                "geographic_scope": {
                    "states": [org_data.get('state', 'VA')] if org_data.get('state') else ['VA'],
                    "nationwide": False,
                    "international": False
                },
                "funding_preferences": {
                    "min_amount": 10000,
                    "max_amount": 500000,
                    "funding_types": [FundingType.GRANTS]
                },
                "annual_revenue": org_data.get('total_revenue') or None,
                "auto_populated": True,
                "source": "ProPublica/IRS lookup"
            }
            
            profile_service = ProfileService()
            profile = profile_service.create_profile(profile_data)
            
            print(f"Profile created successfully!")
            print(f"Profile ID: {profile.profile_id}")
            print(f"Profile Name: {profile.name}")
            print(f"Revenue: ${profile.annual_revenue:,}" if profile.annual_revenue else "Revenue: Unknown")
            
            return True
            
        else:
            print(f"FAILED: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Direct EIN Functionality Test")
    print("Testing without web server dependency")
    print()
    
    success = test_ein_lookup_directly()
    
    print("\n" + "=" * 40)
    if success:
        print("EIN FUNCTIONALITY WORKING!")
        print("The processor and profile creation logic is functional.")
        print("Server restart may be needed to activate web endpoint.")
    else:
        print("Issues found with EIN functionality")
    
    print("\nNext: Refresh browser at http://localhost:8000")
    print("Try the 'Create from EIN' button in READIFIER -> Profiler")

if __name__ == "__main__":
    main()
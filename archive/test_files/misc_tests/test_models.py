#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.analysis.deterministic_scoring_engine import ExtractedFacts, ProfileData
from src.processors.analysis.opportunity_type_detector import OpportunityType
from datetime import datetime

# Test creating ExtractedFacts
print("Testing ExtractedFacts creation...")
facts = ExtractedFacts(
    opportunity_type=OpportunityType.GOVERNMENT,
    extraction_template='GOVERNMENT_COMPREHENSIVE', 
    raw_facts={'test': 'value'},
    data_completeness=0.8,
    extraction_confidence=0.7,
    missing_fields=[],
    extraction_timestamp=datetime.now()
)

print(f'ExtractedFacts created: {type(facts)}')
print(f'raw_facts attribute: {hasattr(facts, "raw_facts")}')
print(f'raw_facts type: {type(facts.raw_facts)}')
print(f'raw_facts value: {facts.raw_facts}')

# Test ProfileData
print("\nTesting ProfileData creation...")
profile = ProfileData(
    organization_name='Test Org',
    ein='123456789'
)

print(f'ProfileData created: {type(profile)}')
print("Models work correctly!")
# Tool 25 Integration Plan
## Web Intelligence Tool → Profile Creation Workflow

**Date**: 2025-10-01
**Phase**: Phase 8 - Profile Capability Transformation
**Objective**: Replace legacy VerificationEnhancedScraper with Tool 25 (Scrapy-powered Web Intelligence)

---

## Integration Overview

### What We're Replacing
**Legacy scraper**: `src/core/verification_enhanced_scraper.py` (VerificationEnhancedScraper)
- Mixed concerns (XML parsing + web scraping)
- No structured outputs
- Not 12-factor compliant
- Poor data quality scoring

**New Tool**: Tool 25 - Web Intelligence Tool (tools/web-intelligence-tool/)
- ✅ 12-factor compliant
- ✅ Scrapy-powered (professional framework)
- ✅ Structured outputs (BAML schemas)
- ✅ 990 verification pipeline
- ✅ Smart URL Resolution (User → 990 → GPT)
- ✅ Data quality scoring

---

## Integration Points

### 1. POST /api/profiles/fetch-ein
**Location**: `src/web/main.py` lines 1929-2200
**Current flow**:
```
1. EINLookupProcessor → Get 990 data
2. GPTURLDiscoveryProcessor → Predict URLs
3. VerificationEnhancedScraper → Scrape web data ❌ REPLACE THIS
4. Return response_data
```

**New flow**:
```
1. EINLookupProcessor → Get 990 data
2. Smart URL Resolution (User → 990 → GPT priority)
3. Tool 25 Profile Builder → Scrape with 990 verification ✅ NEW
4. Auto-populate profile fields from intelligence
5. Return enhanced response_data
```

---

## Implementation Steps

### Step 1: Import Tool 25 Classes
```python
# At top of main.py
import sys
from pathlib import Path

# Add tools directory to path
tools_dir = Path(__file__).parent.parent.parent / "tools" / "web-intelligence-tool"
sys.path.insert(0, str(tools_dir))

from app.web_intelligence_tool import (
    WebIntelligenceTool,
    WebIntelligenceRequest,
    UseCase
)
```

### Step 2: Replace VerificationEnhancedScraper Call

**Before** (lines 2043-2150):
```python
from src.core.verification_enhanced_scraper import VerificationEnhancedScraper

scraper = VerificationEnhancedScraper()
verification_result = await scraper.scrape_with_verification(
    ein=ein,
    organization_name=org_name,
    user_provided_url=predicted_urls[0] if predicted_urls else None
)
```

**After**:
```python
# Initialize Tool 25
web_intel_tool = WebIntelligenceTool()

# Create request for Profile Builder use case
web_intel_request = WebIntelligenceRequest(
    ein=ein,
    organization_name=org_name,
    use_case=UseCase.PROFILE_BUILDER,
    user_provided_url=request.get('user_provided_url'),  # User URL (highest priority)
    require_990_verification=True,
    min_confidence_score=0.7
)

# Execute Tool 25
web_intel_response = await web_intel_tool.execute(web_intel_request)
```

### Step 3: Map Intelligence Data to Response

**Extract data from OrganizationIntelligence**:
```python
if web_intel_response.success and web_intel_response.intelligence_data:
    intel_data = web_intel_response.intelligence_data

    # Auto-populate profile fields
    if intel_data.mission_statement and not response_data["mission_statement"]:
        response_data["mission_statement"] = intel_data.mission_statement

    if intel_data.verified_website and not response_data["website"]:
        response_data["website"] = intel_data.verified_website
        response_data["website_url"] = intel_data.verified_website

    # Add leadership data
    leadership_data = [
        {
            "name": leader.name,
            "title": leader.title,
            "confidence": leader.confidence_score,
            "source": leader.source_url
        }
        for leader in intel_data.leadership_info
    ]

    # Add program data
    program_data = [
        {
            "name": program.program_name,
            "description": program.program_description,
            "confidence": program.confidence_score
        }
        for program in intel_data.programs
    ]

    # Add contact data
    contact_data = [
        {
            "type": contact.contact_type,
            "value": contact.contact_value,
            "confidence": contact.confidence_score
        }
        for contact in intel_data.contact_information
    ]

    # Update response data
    response_data["web_scraping_data"] = {
        "leadership": leadership_data,
        "programs": program_data,
        "contacts": contact_data,
        "mission_statements": [
            {
                "text": intel_data.mission_statement,
                "source": intel_data.verified_website,
                "confidence": intel_data.scraping_metadata.verification_confidence
            }
        ] if intel_data.mission_statement else []
    }

    response_data["enhanced_with_web_data"] = True
    response_data["data_quality_score"] = web_intel_response.data_quality_score
    response_data["verification_confidence"] = web_intel_response.verification_confidence
    response_data["pages_scraped"] = web_intel_response.pages_scraped
```

### Step 4: Smart URL Resolution Implementation

**Priority Order**:
1. **User-provided URL** (if supplied in request) - Highest priority
2. **990 Website** (from tax filing) - Most reliable
3. **GPT-predicted URL** (if above don't exist) - AI fallback

```python
# Smart URL Resolution
user_url = request.get('user_provided_url')
filing_url = _extract_website_url_from_990(org_data)
gpt_url = predicted_urls[0] if predicted_urls else None

# Priority selection
resolved_url = user_url or filing_url or gpt_url

logger.info(
    f"Smart URL Resolution:\n"
    f"  User URL: {user_url or 'None'}\n"
    f"  990 Filing URL: {filing_url or 'None'}\n"
    f"  GPT Predicted URL: {gpt_url or 'None'}\n"
    f"  RESOLVED: {resolved_url or 'None (will search)'}"
)

# Pass resolved URL to Tool 25
web_intel_request = WebIntelligenceRequest(
    ein=ein,
    organization_name=org_name,
    use_case=UseCase.PROFILE_BUILDER,
    user_provided_url=resolved_url,  # Smart resolution result
    require_990_verification=True,
    min_confidence_score=0.7
)
```

---

## Auto-Population Rules

### Field Population Priority

**1. Mission Statement**:
- Tool 25 scraped mission (if verification_confidence >= 0.7)
- 990 tax filing mission
- Keep existing if neither available

**2. Website URL**:
- User-provided URL (if supplied)
- Tool 25 verified website (if verification_confidence >= 0.8)
- 990 tax filing website
- Keep existing if none available

**3. Leadership**:
- Tool 25 scraped leadership (confidence >= 0.7)
- 990 Officer/Director data
- Merge both sources (deduplicate by name)

**4. Programs**:
- Tool 25 scraped programs (confidence >= 0.6)
- 990 program descriptions
- Merge both sources

**5. Contact Information**:
- Tool 25 scraped contacts (confidence >= 0.7)
- 990 principal officer contact
- Merge both sources

**Confidence Thresholds**:
- High confidence: >= 0.8 (auto-populate, override existing)
- Medium confidence: >= 0.6 (auto-populate if empty)
- Low confidence: < 0.6 (do not auto-populate)

---

## Response Format

**Enhanced response_data structure**:
```json
{
  "name": "Organization Name",
  "ein": "12-3456789",
  "mission_statement": "Auto-populated from Tool 25 or 990",
  "website": "https://verified-url.org",
  "website_url": "https://verified-url.org",

  "web_scraping_data": {
    "leadership": [
      {
        "name": "John Doe",
        "title": "Executive Director",
        "confidence": 0.92,
        "source": "https://org.org/about"
      }
    ],
    "programs": [
      {
        "name": "Youth Development",
        "description": "...",
        "confidence": 0.85
      }
    ],
    "contacts": [
      {
        "type": "email",
        "value": "info@org.org",
        "confidence": 0.88
      }
    ],
    "mission_statements": [
      {
        "text": "Our mission is...",
        "source": "https://org.org",
        "confidence": 0.95
      }
    ]
  },

  "enhanced_with_web_data": true,
  "data_quality_score": 0.87,
  "verification_confidence": 0.92,
  "pages_scraped": 5,

  "tool_25_metadata": {
    "use_case": "PROFILE_BUILDER",
    "execution_time_seconds": 12.5,
    "url_resolution": {
      "user_url": null,
      "filing_url": "https://org.org",
      "gpt_url": "https://organization.org",
      "resolved_url": "https://org.org",
      "resolution_method": "990_filing"
    }
  }
}
```

---

## Error Handling

### Graceful Degradation

**If Tool 25 fails**:
1. Log warning (don't fail entire request)
2. Return 990 data only
3. Set `enhanced_with_web_data: false`
4. Set `tool_25_error: "<error message>"`

```python
try:
    web_intel_response = await web_intel_tool.execute(web_intel_request)

    if web_intel_response.success:
        # Process intelligence data
        ...
    else:
        logger.warning(f"Tool 25 failed: {web_intel_response.errors}")
        response_data["enhanced_with_web_data"] = False
        response_data["tool_25_error"] = "; ".join(web_intel_response.errors)

except Exception as e:
    logger.error(f"Tool 25 exception: {e}")
    response_data["enhanced_with_web_data"] = False
    response_data["tool_25_error"] = str(e)
```

---

## Testing Strategy

### Unit Tests
1. Test Smart URL Resolution priority
2. Test auto-population with various confidence scores
3. Test field merging (990 + web data)
4. Test error handling and graceful degradation

### Integration Tests
1. Test with real nonprofits (5-10 examples)
2. Verify 990 verification pipeline
3. Compare Tool 25 vs legacy scraper results
4. Test with user-provided URLs

### Test Cases
```python
# Test Case 1: User URL provided (highest priority)
{
    "ein": "54-1026365",
    "user_provided_url": "https://unitedway.org",
    "enable_web_scraping": True
}
# Expected: Use https://unitedway.org

# Test Case 2: 990 URL available (no user URL)
{
    "ein": "54-1026365",
    "enable_web_scraping": True
}
# Expected: Use 990 filing URL

# Test Case 3: GPT fallback (no user, no 990 URL)
{
    "ein": "12-3456789",  # Has no website in 990
    "enable_web_scraping": True
}
# Expected: Use GPT predicted URL

# Test Case 4: Tool 25 failure
{
    "ein": "99-9999999",  # Invalid EIN
    "enable_web_scraping": True
}
# Expected: Graceful degradation, 990 data only
```

---

## Migration Checklist

### Phase 1: Implementation (Day 1, Morning)
- [ ] Add Tool 25 import to main.py
- [ ] Implement Smart URL Resolution
- [ ] Replace VerificationEnhancedScraper with Tool 25
- [ ] Implement auto-population logic
- [ ] Add response mapping

### Phase 2: Testing (Day 1, Afternoon)
- [ ] Unit test Smart URL Resolution
- [ ] Integration test with 5 nonprofits
- [ ] Compare results vs legacy scraper
- [ ] Verify auto-population rules

### Phase 3: Cleanup (Day 2, Morning)
- [ ] Remove VerificationEnhancedScraper imports
- [ ] Update frontend to display Tool 25 metadata
- [ ] Add Tool 25 execution metrics to dashboard

### Phase 4: Documentation (Day 2, Afternoon)
- [ ] Document Tool 25 integration
- [ ] Update API documentation
- [ ] Create user guide for URL priority

---

## Success Criteria

### Functional Requirements ✅
- [ ] Smart URL Resolution working (User → 990 → GPT priority)
- [ ] Auto-population of profile fields from Tool 25
- [ ] 990 verification pipeline operational
- [ ] Graceful degradation on Tool 25 failure
- [ ] Data quality scoring accurate

### Performance Requirements ✅
- [ ] Tool 25 execution < 60 seconds
- [ ] Verification confidence >= 85%
- [ ] Data quality score >= 0.75
- [ ] Pages scraped >= 3 per organization

### Quality Requirements ✅
- [ ] No regressions in existing functionality
- [ ] All tests passing
- [ ] Clean error handling
- [ ] Comprehensive logging

---

## Next Steps

After Tool 25 integration:
1. ✅ Test with 5-10 real nonprofits (Task 9)
2. ✅ Verify NTEE code selection still functional (Task 10)
3. ✅ Continue with 990 intelligence pipeline testing (Task 13-15)

# Tool 25: Web Intelligence Tool

**Scrapy-powered web scraping for nonprofit grant research intelligence**

## Overview

Tool 25 is a 12-factor compliant web intelligence gathering tool that uses the Scrapy framework to extract structured data from nonprofit organization websites, grantmaking organizations, and private foundations.

### Three Strategic Use Cases

1. **Profile Builder** (Use Case 1)
   - **Purpose**: Auto-populate organization profiles from websites
   - **Targets**: Mission, programs, leadership, contact info, financials
   - **Integration**: `POST /api/profiles/fetch-ein`
   - **Cost**: $0.05-0.10 per organization

2. **Opportunity Research** (Use Case 2)
   - **Purpose**: Discover grant opportunities from grantmaking nonprofits
   - **Targets**: Grant programs, funding priorities, application requirements, deadlines
   - **Examples**: United Way chapters, community foundations, nonprofit grantmakers
   - **Integration**: Tool 2 (Deep Intelligence Tool)
   - **Cost**: $0.15-0.25 per organization

3. **Foundation Research** (Use Case 3)
   - **Purpose**: Discover grant opportunities and application details
   - **Targets**: Guidelines, deadlines, priorities, trustees, recent grants
   - **Integration**: Tool 13 (Schedule I Grant Analyzer Tool)
   - **Cost**: $0.10-0.20 per foundation

## Key Features

### ✅ Smart URL Resolution
- **Priority**: User-provided → 990-declared → GPT-predicted
- **Integration**: `SmartURLResolutionService` via `SmartURLMiddleware`
- **Confidence Scoring**: Every URL has source attribution and confidence score

### ✅ 990 Tax Filing Verification
- **Cross-Validation**: Scraped leadership verified against IRS 990 Part VII
- **Financial Verification**: Budget/revenue checked against 990 Part I
- **Confidence Metrics**: Overall verification confidence score (0.0-1.0)

### ✅ Respectful Scraping
- **Rate Limiting**: 2-second delay between requests (configurable)
- **Robots.txt Compliance**: Built-in
- **User Agent**: Clear identification as `CatalynxBot/1.0`
- **Depth Limiting**: Max 3 levels deep (configurable)

### ✅ Structured Outputs
- **BAML Schemas**: All outputs match BAML definitions
- **Pydantic Validation**: Type-safe structured data
- **Factor 4 Compliance**: Tools as Structured Outputs

### ✅ Intelligent Pipelines
1. **Smart URL Middleware**: Resolves best URL before scraping
2. **Rate Limit Middleware**: Ensures respectful crawling
3. **990 Validation Pipeline**: Verifies data against tax filings
4. **Deduplication Pipeline**: Removes duplicate entries (fuzzy matching)
5. **Structured Output Pipeline**: Converts to BAML models

## Architecture

```
tools/web-intelligence-tool/
├── 12factors.toml                          # Tool configuration
├── scrapy.cfg                              # Scrapy project config
├── README.md                               # This file
│
├── app/
│   ├── web_intelligence_tool.py            # Main tool entry point
│   ├── scrapy_settings.py                  # Scrapy settings
│   │
│   ├── scrapy_spiders/
│   │   ├── organization_profile_spider.py  # Use Case 1
│   │   ├── opportunity_research_spider.py  # Use Case 2 (TODO)
│   │   └── foundation_website_spider.py    # Use Case 3 (TODO)
│   │
│   ├── scrapy_middlewares/
│   │   ├── smart_url_middleware.py         # Integrates SmartURLResolutionService
│   │   └── rate_limit_middleware.py        # Additional rate limiting
│   │
│   └── scrapy_pipelines/
│       ├── validation_pipeline.py          # 990 verification
│       ├── deduplication_pipeline.py       # Duplicate removal
│       └── structured_output_pipeline.py   # BAML conversion
│
├── baml_src/
│   ├── web_intelligence_input.baml         # Input schema
│   ├── organization_intelligence.baml      # Output schema (Use Case 1)
│   ├── opportunity_intelligence.baml       # Output schema (Use Case 2)
│   └── foundation_intelligence.baml        # Output schema (Use Case 3)
│
└── tests/
    ├── test_profile_spider.py
    ├── test_opportunity_spider.py
    └── test_foundation_spider.py
```

## Usage

### Python API

```python
from tools.web_intelligence_tool.app.web_intelligence_tool import (
    WebIntelligenceTool,
    WebIntelligenceRequest,
    UseCase
)

# Create tool instance
tool = WebIntelligenceTool()

# Create request
request = WebIntelligenceRequest(
    ein="52-1693387",
    organization_name="American Red Cross",
    use_case=UseCase.PROFILE_BUILDER,
    user_provided_url="https://www.redcross.org"  # Optional
)

# Execute
response = await tool.execute(request)

# Access results
if response.success:
    intelligence = response.intelligence_data
    print(f"Mission: {intelligence.mission_statement}")
    print(f"Programs: {len(intelligence.programs)}")
    print(f"Leadership: {len(intelligence.leadership)}")
    print(f"Data Quality: {response.data_quality_score:.2%}")
    print(f"Verification Confidence: {response.verification_confidence:.2%}")
```

### Convenience Function

```python
from tools.web_intelligence_tool.app.web_intelligence_tool import scrape_organization_profile

# Simple profile scraping
response = await scrape_organization_profile(
    ein="52-1693387",
    organization_name="American Red Cross",
    user_provided_url="https://www.redcross.org"  # Optional
)
```

### Command-Line Interface (Testing)

```bash
python app/web_intelligence_tool.py \
    --ein "52-1693387" \
    --name "American Red Cross" \
    --url "https://www.redcross.org" \
    --use-case PROFILE_BUILDER
```

## Configuration

All configuration is managed through `12factors.toml`:

```toml
[tool.config]
max_depth = 3
concurrent_requests = 2
download_delay = 2.0  # Seconds between requests
user_agent = "CatalynxBot/1.0 (+https://catalynx.io/bot)"
respect_robots_txt = true
timeout = 30

[tool.config.use_case_1_profile_builder]
enabled = true
target_pages = ["about", "mission", "programs", "board", "staff", "contact"]
max_pages_per_site = 10
verification_required = true  # Must verify against 990

[tool.config.use_case_2_opportunity_research]
enabled = true
target_pages = ["grants", "funding", "apply", "giving", "how-to-apply"]
max_pages_per_site = 15
verification_required = true  # Verify against 990 Schedule I

[tool.config.use_case_3_foundation_research]
enabled = true
target_pages = ["apply", "guidelines", "grants", "priorities"]
max_pages_per_site = 12
verification_required = true  # Verify trustees against 990-PF
```

## Output Schemas (BAML)

### OrganizationIntelligence (Use Case 1)

```baml
class OrganizationIntelligence {
    ein string
    organization_name string
    website_url string
    mission_statement string?
    programs ProgramArea[]
    leadership LeadershipEntry[]          // With 990 verification
    contact_info ContactInformation?
    financial_info FinancialSummary?      // With 990 verification
    scraping_metadata ScrapingMetadata
}

class LeadershipEntry {
    name string
    title string
    verification_status VerificationStatus  // VERIFIED_990, WEB_ONLY, CONFLICTING
    matches_990 bool
    compensation_990 float?                 // From 990 if matched
}
```

### Data Quality Metrics

Every output includes comprehensive metadata:

- **Data Quality Score** (0.0-1.0): Overall quality of extracted data
- **Verification Confidence** (0.0-1.0): How well web data matches 990
- **URL Source**: Where the URL came from (user, 990, GPT)
- **URL Confidence**: Confidence in URL (0.0-1.0)
- **Extraction Flags**: What data was successfully extracted

## Integration Points

### 1. Profile Builder Integration

```python
# In POST /api/profiles/fetch-ein endpoint
from tools.web_intelligence_tool.app.web_intelligence_tool import scrape_organization_profile

# After fetching 990 data
intelligence_response = await scrape_organization_profile(
    ein=ein,
    organization_name=org_data['name'],
    user_provided_url=request.get('website_url')
)

if intelligence_response.success:
    # Auto-populate profile fields
    profile_data.update({
        'mission_statement': intelligence_response.intelligence_data.mission_statement,
        'website_url': intelligence_response.intelligence_data.website_url,
        'programs': [p.dict() for p in intelligence_response.intelligence_data.programs],
        # ...
    })
```

### 2. Deep Intelligence Integration (Tool 2)

```python
# In Deep Intelligence Tool - Enhanced depth mode
from tools.web_intelligence_tool.app.web_intelligence_tool import WebIntelligenceTool, UseCase

# For opportunity research (grantmaking nonprofits)
opportunity_tool = WebIntelligenceTool()
opportunity_request = WebIntelligenceRequest(
    ein=grantmaker_ein,
    organization_name=grantmaker_name,
    use_case=UseCase.OPPORTUNITY_RESEARCH
)
opportunity_intel = await opportunity_tool.execute(opportunity_request)
```

### 3. Foundation Analysis Integration (Tool 13)

```python
# In Schedule I Grant Analyzer Tool
foundation_tool = WebIntelligenceTool()
foundation_request = WebIntelligenceRequest(
    ein=foundation_ein,
    organization_name=foundation_name,
    use_case=UseCase.FOUNDATION_RESEARCH
)
foundation_intel = await foundation_tool.execute(foundation_request)
```

## 12-Factor Compliance

### Factor 1: Codebase
✅ Single codebase tracked in git

### Factor 3: Config
✅ All configuration in `12factors.toml`, no hardcoded values

### Factor 4: Structured Outputs
✅ All outputs use BAML schemas with Pydantic validation

### Factor 6: Stateless Processes
✅ Each spider run is independent, no persistent state

### Factor 10: Single Responsibility
✅ Focused solely on web intelligence gathering

### Factor 11: Autonomous Operation
✅ Self-contained with built-in URL resolution and 990 verification

## Performance & Costs

| Use Case | Pages Scraped | Execution Time | Cost Estimate |
|----------|--------------|----------------|---------------|
| Profile Builder | 2-10 | 10-30s | $0.05-0.10 |
| Opportunity Research | 5-15 | 30-60s | $0.15-0.25 |
| Foundation Research | 3-12 | 20-45s | $0.10-0.20 |

**Cost Breakdown:**
- Scrapy framework: $0.00 (open source)
- GPT URL discovery: $0.05-0.10 (if no user/990 URL)
- 990 verification: $0.00 (local data)
- Total: $0.05-0.25 per organization

## Testing

```bash
# Run spider tests
pytest tests/test_profile_spider.py -v

# Test with real organization
python app/web_intelligence_tool.py \
    --ein "52-1693387" \
    --name "American Red Cross" \
    --url "https://www.redcross.org"
```

## Development Status

- ✅ **Phase 1 Complete**: Foundation infrastructure
  - 12factors.toml configuration
  - BAML schemas (3 use cases)
  - Scrapy settings
  - Smart URL middleware
  - 990 validation pipeline
  - Deduplication pipeline
  - Structured output pipeline

- ✅ **Phase 2 Complete**: Use Case 1 (Profile Builder)
  - OrganizationProfileSpider implemented
  - Mission, programs, leadership extraction
  - Contact and financial data extraction
  - 990 verification integration

- ⏸️ **Phase 3 Pending**: Use Case 2 (Opportunity Research)
  - OpportunityResearchSpider (TODO)
  - Grant program extraction (TODO)
  - Application requirement parsing (TODO)

- ⏸️ **Phase 4 Pending**: Use Case 3 (Foundation Research)
  - FoundationWebsiteSpider (TODO)
  - Grant guidelines extraction (TODO)
  - Deadline detection and parsing (TODO)

## Future Enhancements

- [ ] JavaScript rendering support (Scrapy-Playwright)
- [ ] Image and PDF extraction
- [ ] Multi-language support
- [ ] Social media integration
- [ ] Advanced natural language processing
- [ ] Competitive intelligence scoring
- [ ] Grant matching algorithm

## License

Part of Catalynx Grant Research Intelligence Platform

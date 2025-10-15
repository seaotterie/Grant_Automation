# ProPublica API Enrichment Tool - 12-Factor Agents Implementation
*🟡 Intermediate Level - API Integration Following Human Layer Framework*

## What This Tool Does

The ProPublica API Enrichment Tool demonstrates **Factor 4: Tools as Structured Outputs** by providing organization enrichment using only the ProPublica Nonprofit Explorer API. This is the **third tool** in the five-tool nonprofit grant research architecture.

**Think of it like**: A research assistant that takes filtered organizations and enriches them with public API data - mission statements, filing summaries, and organization details from ProPublica.

## Integration with Five-Tool Architecture

This tool completes step 3 of the workflow:
1. **BMF Filter Tool**: 700K organizations → 10 filtered organizations
2. **Form990 Analysis Tool**: 10 organizations → deep financial analysis
3. **ProPublica API Enrichment Tool**: 10 organizations → comprehensive profiles ← **(This Tool)**
4. **XML Schedule Parser Tool**: Selected organizations → detailed schedule data
5. **Foundation Grant Intelligence Tool**: Foundation organizations → grant-making analysis

## 12-Factor Agents Principles (Human Layer Framework)

This tool implements the [Human Layer 12-Factor Agents Framework](https://github.com/humanlayer/12-factor-agents):

**Factor 1: Natural Language to Tool Calls** - Takes structured EINs from Form 990 tool, not natural language
**Factor 2: Own Your Prompts** - Complete control over ProPublica API integration and response processing
**Factor 3: Own Your Context Window** - Minimal context usage, ProPublica API provides data
**Factor 4: Tools as Structured Outputs** - Forces structured ProPublicaAPIResult with guaranteed format
**Factor 5: Unify Execution and Business State** - API enrichment unified with grant research workflows
**Factor 6: Launch/Pause/Resume with Simple APIs** - Single async execute() method with rate limiting
**Factor 7: Contact Humans with Tool Calls** - Provides human-readable organization profiles and descriptions
**Factor 8: Control Flow Management** - Explicit flow: EINs → API calls → structured enrichment
**Factor 9: Compact Error Handling** - API errors and rate limits integrated into result structure
**Factor 10: Small, Focused Agents** - Single responsibility: ProPublica API enrichment only
**Factor 11: Trigger from Anywhere** - Can be triggered from workflows, web UI, or standalone
**Factor 12: Stateless Reducer Model** - Pure function: ProPublicaAPIEnrichmentCriteria → ProPublicaAPIResult

### Key Innovation: Factor 4 Implementation

This tool demonstrates **Factor 4: Tools as Structured Outputs** for API enrichment:
- Takes structured EIN list from Form 990 Analysis Tool
- Executes controlled ProPublica API calls with rate limiting
- Returns structured `ProPublicaAPIResult` with guaranteed JSON format
- **Eliminates API response parsing errors** in production environments

## Single Responsibility Design

### **What This Tool Does:**
✅ ProPublica API organization lookups
✅ Basic filing summaries from API
✅ Mission and activity descriptions
✅ Organization classification and details
✅ Similar organization discovery (optional)
✅ Rate limiting and error handling

### **What This Tool Does NOT Do:**
❌ XML download or parsing (Tool 4 responsibility)
❌ Complex foundation analysis (Tool 5 responsibility)
❌ Financial health scoring (Tool 2 responsibility)
❌ BMF database filtering (Tool 1 responsibility)

## Features

### Core API Capabilities
- **Organization Profiles**: Complete organizational details from ProPublica API
- **Filing Summaries**: Basic financial data from recent 990 filings
- **Mission Intelligence**: Mission statements and activity descriptions
- **Classification Data**: NTEE codes, ruling dates, organization types
- **Similar Organizations**: Optional discovery of similar nonprofits

### Performance Features
- **Rate Limiting**: Intelligent delays to respect ProPublica API limits (0.2s between calls)
- **Error Handling**: Robust error handling with retry mechanisms
- **Structured Output**: Guaranteed JSON format regardless of API response variations
- **Quality Assessment**: Data completeness and freshness scoring

## Input/Output Contracts

### Input: ProPublicaAPIEnrichmentCriteria
```typescript
class ProPublicaAPIEnrichmentCriteria {
    target_eins: string[]                    // EINs to enrich (from previous tools)
    include_filing_history: boolean          // Include basic filing summaries
    years_to_include: int                    // Number of years of filing data
    include_mission_data: boolean            // Include mission and activity descriptions
    include_similar_orgs: boolean            // Find similar organizations (optional)
    max_similar_orgs: int                   // Maximum similar organizations to find
}
```

### Output: ProPublicaAPIResult
```typescript
class ProPublicaAPIResult {
    enriched_organizations: ProPublicaOrganizationProfile[]
    filing_summaries: FilingSummary[]
    similar_organizations: SimilarOrganization[]
    execution_metadata: APIExecutionMetadata
    quality_assessment: QualityAssessment
}
```

## Tool Usage

### Basic Usage
```python
from app.propublica_api_enricher import ProPublicaAPIEnrichmentTool, ProPublicaAPIEnrichmentCriteria

# Initialize tool
tool = ProPublicaAPIEnrichmentTool()

# Create enrichment criteria
criteria = ProPublicaAPIEnrichmentCriteria(
    target_eins=["123456789", "987654321"],
    include_filing_history=True,
    years_to_include=3,
    include_mission_data=True
)

# Execute enrichment
result = await tool.execute(criteria)
```

### Integration with Previous Tools
```python
# From BMF Filter Tool
bmf_result = await bmf_tool.execute(bmf_criteria)

# From Form 990 Analysis Tool
form990_result = await form990_tool.execute(form990_criteria)

# ProPublica API Enrichment (all analyzed organizations)
target_eins = [org.ein for org in form990_result.organizations]
api_result = await api_tool.execute(api_criteria)
```

## Environment Configuration

### Required Environment Variables
None - ProPublica API is public and requires no authentication

### Optional Environment Variables
```bash
# Performance Configuration
PROPUBLICA_RATE_LIMIT_DELAY=0.2
PROPUBLICA_MAX_ORGANIZATIONS=50
PROPUBLICA_TIMEOUT_SECONDS=30

# Caching and Logging
PROPUBLICA_CACHE_ENABLED=true
PROPUBLICA_LOG_PERFORMANCE=true
```

## Data Sources

### ProPublica Nonprofit Explorer API
- **Organization Search**: Name and EIN-based organization lookup
- **Organization Details**: Complete organizational profiles
- **Filing Summaries**: Basic financial data from 990 forms
- **Mission Data**: Mission statements and activity descriptions
- **Similar Organizations**: Related nonprofits discovery

### API Limitations and Handling
- **Rate Limiting**: 500 calls/hour with 0.2s delays
- **Data Coverage**: Not all organizations have complete API data
- **API Changes**: Tool handles API response variations gracefully
- **Error Handling**: Structured error reporting in result object

## Performance Characteristics

### API Efficiency
- **Response Time**: < 500ms per organization for standard enrichment
- **Rate Limiting**: Respects API limits with intelligent delays
- **Error Recovery**: Graceful handling of failed requests
- **Quality Scoring**: Data completeness assessment for each organization

### Integration Performance
- **Lightweight**: Focused on API-only enrichment
- **Structured Output**: Consistent JSON format regardless of API variations
- **Memory Efficient**: Minimal memory footprint (256MB limit)

## Error Handling

### Resilient API Integration
- **Connection Failures**: Automatic retry with exponential backoff
- **Rate Limit Exceeded**: Intelligent delay mechanisms
- **Data Not Found**: Graceful degradation with partial profiles
- **API Changes**: Version detection and compatibility handling

### Quality Assurance
- **Data Validation**: Schema validation for all API responses
- **Completeness Scoring**: Data quality metrics for each organization
- **Error Reporting**: Detailed error logging in structured results

## Architecture Benefits

### Five-Tool Separation
1. **BMF Filter**: Ultra-fast database filtering (99.99% reduction)
2. **Form 990 Analysis**: Financial intelligence on filtered subset
3. **ProPublica API Enrichment**: Organization profiles and mission data ← **(This Tool)**
4. **XML Schedule Parser**: Detailed schedule data from XML files
5. **Foundation Intelligence**: 990-PF grant-making analysis

### Performance Optimization
- **Stage 1**: 700K organizations → 10 organizations (database)
- **Stage 2**: 10 organizations → financial analysis (database)
- **Stage 3**: 10 organizations → API enrichment (ProPublica API) ← **(This Tool)**
- **Stage 4**: Selected organizations → XML schedules (XML parsing)
- **Stage 5**: Foundation organizations → grant intelligence (analysis)

### 12-Factor Compliance
- **Stateless Design**: No tool dependencies or persistent state
- **Structured Contracts**: BAML schemas for all interfaces
- **Environment Config**: Complete externalization of configuration
- **Single Responsibility**: API enrichment only, no other concerns

This tool provides essential organization profile enrichment while maintaining strict 12-factor compliance and clear separation of concerns within the five-tool architecture.
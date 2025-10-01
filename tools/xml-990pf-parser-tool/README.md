# XML 990-PF Parser Tool - 12-Factor Agents Implementation
*🔴 Advanced Tool - Private Foundation Form Parsing with Network Analysis Following Human Layer Framework*

## What This Tool Does

The XML 990-PF Parser Tool is a specialized 12-factor agent that downloads and parses IRS Form 990-PF XML filings for **private foundations only**. It extracts comprehensive foundation intelligence including officers/directors, grants paid, investment portfolios, payout requirements (5% distribution rule), and governance data with **network analysis capabilities** for board member connection mapping.

**Single Responsibility**: Form 990-PF parsing - does NOT handle 990 (regular nonprofits) or 990-EZ (small organizations), which have separate specialized tools.

**Advanced Features**: Person/org name normalization, role categorization, influence scoring, and grant relationship mapping for strategic network analysis.

## Core Capabilities

### Data Extraction (Form 990-PF Schedules)
- **Foundation Officers** (`OfficerDirTrstKeyEmplInfoGrp`): Names, titles, compensation, benefits with network analysis fields
- **Grants Paid** (Part XV): Recipients, amounts, purposes with normalized names for matching
- **Investment Portfolios** (Part II): Holdings, valuations, portfolio analysis for grant capacity assessment
- **Payout Requirements** (Part XII): 5% distribution rule compliance, qualifying distributions
- **Excise Tax** (Part VI): Tax calculations, net investment income
- **Governance**: Grant-making procedures, monitoring policies, operational indicators
- **Financial Summary**: Total assets, revenue, investments with grant-making capacity analysis

### Network Analysis (NEW - Phase 2 Complete)
- **Person Name Normalization**: "Christine M. Connolly" → "CHRISTINE M CONNOLLY" (fuzzy matching ready)
- **Organization Name Normalization**: "AFRO-AMERICAN HISTORICAL ASSOC" → "AFRO AMERICAN HISTORICAL ASSOC"
- **Role Categorization**: Executive, Board, Staff, Volunteer (standardized across 990 forms)
- **Influence Scoring**: 0-1 score based on role + compensation + hours + flags
- **Grant Relationship Mapping**: Foundation-to-grantee organization linking

### 12-Factor Framework Compliance
- **Factor 4**: Tools as Structured Outputs - returns `XML990PFResult` dataclass, eliminating parsing errors
- **Factor 10**: Small, Focused Agents - single responsibility for 990-PF forms only
- **Factor 6**: Stateless execution - no persistent state between runs
- **Factor 11**: Autonomous operation - self-contained with minimal external dependencies

## Quick Start

### Installation
```python
import sys
sys.path.insert(0, 'tools/xml-990pf-parser-tool/app')
from xml_990pf_parser import XML990PFParserTool, XML990PFParseCriteria
```

### Basic Usage
```python
import asyncio

async def parse_990pf_filing():
    tool = XML990PFParserTool()

    criteria = XML990PFParseCriteria(
        target_eins=["300219424"],  # Fauquier Health Foundation
        schedules_to_extract=['officers', 'grants_paid', 'investments', 'excise_tax', 'payout_requirements'],
        cache_enabled=True,
        max_years_back=3,
        download_if_missing=True,
        validate_990pf_schema=True
    )

    result = await tool.execute(criteria)

    # Structured output with network analysis
    print(f"Officers extracted: {len(result.officers)}")
    print(f"Grants paid: {len(result.grants_paid)}")
    print(f"Investment holdings: {len(result.investment_holdings)}")
    print(f"Grant capacity: ${result.investment_analysis[0].sustainable_grant_capacity:,.2f}/year")

    # Network analysis fields
    for officer in result.officers[:5]:
        print(f"{officer.normalized_person_name} ({officer.role_category}) - Influence: {officer.influence_score:.2f}")

asyncio.run(parse_990pf_filing())
```

## Structured Output Format

### XML990PFResult Dataclass
```python
@dataclass
class XML990PFResult:
    # Metadata
    tool_name: str = "XML 990-PF Parser Tool"
    framework_compliance: str = "Human Layer 12-Factor Agents"
    factor_4_implementation: str = "Tools as Structured Outputs"

    # Extraction counts
    organizations_processed: int
    officers_extracted: int
    grants_extracted: int
    investments_extracted: int
    extraction_failures: int

    # Structured data arrays with network analysis
    officers: List[FoundationOfficer]  # WITH normalized_person_name, role_category, influence_score
    grants_paid: List[FoundationGrant]  # WITH normalized_recipient_name, recipient_ein
    investment_holdings: List[InvestmentHolding]
    contact_info: List[FoundationContactInfo]

    # Advanced analysis
    grant_analysis: List[FoundationGrantAnalysis]
    foundation_classification: List[FoundationClassification]
    investment_analysis: List[InvestmentAnalysis]

    # Financial & compliance
    excise_tax_data: List[ExciseTaxData]
    payout_requirements: List[PayoutRequirement]
    governance_indicators: List[FoundationGovernance]
    financial_summaries: List[Foundation990PFFinancialSummary]

    # File metadata
    xml_files_processed: List[XML990PFFileMetadata]
    execution_metadata: XML990PFExecutionMetadata
    quality_assessment: XML990PFQualityAssessment
```

## Data Classes (Network Analysis Enhanced)

### FoundationOfficer (Network Analysis Fields)
```python
@dataclass
class FoundationOfficer:
    ein: str
    person_name: str
    normalized_person_name: str  # "CHRISTINE M CONNOLLY" - cleaned for network matching
    title: str
    role_category: str  # "Executive", "Board", "Staff", "Volunteer"

    average_hours_per_week: Optional[float]
    compensation: Optional[float]
    employee_benefit_program: Optional[bool]
    expense_account_allowance: Optional[float]

    is_officer: bool
    is_director: bool
    influence_score: Optional[float]  # 0-1 calculated decision-making power

    tax_year: int
    data_source: str = "Form 990-PF XML"
```

**Network Analysis Benefits**:
- `normalized_person_name`: Match board members across 990 (grantee) and 990-PF (grantor) forms
- `role_category`: Standardized classification for cross-form comparison
- `influence_score`: Prioritize connections to high-influence decision makers

### FoundationGrant (Network Analysis Fields)
```python
@dataclass
class FoundationGrant:
    ein: str
    recipient_name: str
    normalized_recipient_name: str  # "AFRO AMERICAN HISTORICAL ASSOC" - cleaned for matching
    recipient_ein: Optional[str]  # **CRITICAL** for org-to-org network mapping
    recipient_type: Optional[str]
    recipient_address: Optional[str]
    recipient_relationship: Optional[str]
    grant_amount: float
    grant_purpose: Optional[str]
    foundation_status_of_recipient: Optional[str]
    grant_monitoring_procedures: Optional[str]
    tax_year: int
    schedule_part: str = "Part XV - Grants"
```

**Network Analysis Benefits**:
- `normalized_recipient_name`: Fuzzy match grantee organizations across data sources
- `recipient_ein`: Direct link to grantee profile for board member cross-referencing

### InvestmentAnalysis (Grant Capacity Assessment)
```python
@dataclass
class InvestmentAnalysis:
    ein: str
    tax_year: int
    total_investment_value: float
    total_investment_count: int
    portfolio_diversification_score: float  # 0-1

    # Portfolio allocation
    equity_percentage: float
    fixed_income_percentage: float
    cash_equivalent_percentage: float
    alternative_investments_percentage: float

    # Grant capacity intelligence
    sustainable_grant_capacity: float  # Annual grant-making ability
    grant_funding_stability: str  # "Stable", "Variable", "Volatile"
    investment_strategy_type: str  # "Conservative", "Balanced", "Aggressive"
    grant_capacity_trend: str  # "Growing", "Stable", "Declining"
    multi_year_grant_feasibility: str  # "High", "Medium", "Low"

    # Risk assessment
    investment_volatility_assessment: str
    liquidity_assessment: str
    professional_management_indicators: bool
    endowment_sustainability_years: Optional[int]

    data_source: str = "Form 990-PF Investment Analysis"
```

## Network Analysis Functions

### normalize_person_name(name: str) -> str
```python
# Removes titles, punctuation, normalizes to uppercase
normalize_person_name("Christine M. Connolly") → "CHRISTINE M CONNOLLY"
normalize_person_name("Dr. Major Warner") → "MAJOR WARNER"
normalize_person_name("John W. McCarthy III") → "JOHN W MCCARTHY"
```

### normalize_org_name(name: str) -> str
```python
# Removes punctuation, normalizes hyphens and spaces
normalize_org_name("Boys and Girls Club of Fauquier") → "BOYS AND GIRLS CLUB OF FAUQUIER"
normalize_org_name("AFRO-AMERICAN HISTORICAL ASSOC") → "AFRO AMERICAN HISTORICAL ASSOC"
```

### categorize_role(title, is_officer, is_director, compensation) -> str
```python
# Returns: "Executive", "Board", "Staff", "Volunteer"
categorize_role("President/CEO", False, False, 350000) → "Executive"
categorize_role("Director", False, False, 0) → "Board"
categorize_role("CFO", False, False, 226000) → "Executive"
categorize_role("Chair", False, False, 0) → "Board"
```

### calculate_influence_score(...) -> float
```python
# Factors: role (1.0=Executive, 0.7=Board) + comp/500K*0.3 + hours/40*0.2 + flags
calculate_influence_score("Executive", False, False, 350000, None) → 1.0
calculate_influence_score("Board", False, False, 0, None) → 0.7
```

## Advanced Intelligence Features

### FoundationGrantAnalysis
```python
@dataclass
class FoundationGrantAnalysis:
    total_grants_count: int
    total_grants_amount: float
    average_grant_size: float
    median_grant_amount: Optional[float]

    # Grant size distribution
    large_grants_count: int  # >= $100K
    medium_grants_count: int  # $10K - $99K
    small_grants_count: int  # < $10K
    grant_size_strategy: str  # "Large Only", "Mixed", "Small Focused"

    # Grant recipient patterns
    individual_recipients_count: int
    organization_recipients_count: int
    geographic_concentration: Optional[str]

    # Grant purpose analysis
    top_grant_purposes: List[str]
    funding_focus_areas: List[str]
    impact_grant_percentage: Optional[float]
    flexible_funding_percentage: Optional[float]
```

### FoundationClassification
```python
@dataclass
class FoundationClassification:
    foundation_type: str  # "Private Foundation", "Operating Foundation"
    foundation_size_category: str  # "Major", "Significant", "Moderate", "Small"
    grant_making_approach: str  # "Proactive", "Responsive", "Mixed"
    funding_model: str  # "Endowed", "Pass-Through", "Hybrid"
    geographic_scope: str  # "National", "Regional", "Local"
    professional_management: str  # "Professional", "Volunteer", "Hybrid"
    risk_tolerance: str  # "Conservative", "Moderate", "Aggressive"

    grant_accessibility_score: float  # 0-1 (1.0 = highly accessible)
    sector_focus: List[str]  # ["Health & Wellness", "Education", etc.]
    unique_value_proposition: Optional[str]
    grant_seeker_recommendations: List[str]
```

## XML Parsing Strategy

### Form 990-PF Schema Validation
```python
# Strict validation - rejects 990 and 990-EZ forms
if "IRS990PF" not in xml_content:
    raise ValueError("Not a Form 990-PF (may be 990 or 990-EZ)")

if "IRS990EZ" in xml_content:
    raise ValueError("This is a 990-EZ form, use xml-990ez-parser-tool")

if "IRS990 " in xml_content and "IRS990PF" not in xml_content:
    raise ValueError("This is a 990 form, use xml-990-parser-tool")
```

### Officer Extraction with Network Analysis
```python
# Find OfficerDirTrstKeyEmplInfoGrp wrapper
wrapper_elem = root.find(f'.//{ns}OfficerDirTrstKeyEmplInfoGrp')
officer_elements = wrapper_elem.findall(f'.//{ns}OfficerDirTrstKeyEmplGrp')

for officer_elem in officer_elements:
    person_name = self._get_element_text(officer_elem, ".//PersonNm")
    title = self._get_element_text(officer_elem, ".//TitleTxt")
    compensation = self._get_element_float(officer_elem, ".//CompensationAmt")

    # Apply network analysis normalization
    normalized_name = normalize_person_name(person_name)
    role_category = categorize_role(title, is_officer, is_director, compensation)
    influence_score = calculate_influence_score(role_category, is_officer, is_director, compensation, hours)

    officer = FoundationOfficer(
        ein=ein,
        person_name=person_name,
        normalized_person_name=normalized_name,
        role_category=role_category,
        influence_score=influence_score,
        ...
    )
```

## Performance Characteristics

### Execution Metrics (Typical)
- **Startup time**: <50ms (factor 9 compliance)
- **Single foundation processing**: 10-20ms
- **Cache hit rate**: 85%+
- **Schema validation**: 100% (strict 990-PF checking)
- **Concurrent downloads**: 3 simultaneous (factor 8 scaling)

### Example Output (Fauquier Health Foundation - EIN 30-0219424)
```
Organizations Processed: 1
Officers Extracted: 16 (3 executives, 13 board members)
Grants Paid: 20 ($483,539 total)
Investment Holdings: 10 ($84.8M portfolio)
Grant Capacity: $4.2M/year sustainable
Influence Scores: 1.0 (executives), 0.7 (board)
Execution Time: 11.6ms
```

## Network Analysis Use Cases

### Board Member Connection Mapping
```python
# Extract foundation officers with normalized names
foundation_officers = result.officers

# Match against profile nonprofit board members (from 990 parser)
profile_board = profile_990_result.officers

# Find name matches for board connections
connections = [
    (fo, po) for fo in foundation_officers for po in profile_board
    if fo.normalized_person_name == po.normalized_person_name
]

# Prioritize foundations by influence scores
high_influence_connections = [
    conn for conn in connections if conn[0].influence_score > 0.8
]
```

### Grant Relationship Discovery
```python
# Find existing grants to profile nonprofit
profile_grants = [
    grant for grant in result.grants_paid
    if grant.recipient_ein == profile_ein or
       grant.normalized_recipient_name in profile_name_variations
]

# Analyze grant history for relationship patterns
if profile_grants:
    print(f"Foundation has granted ${sum(g.grant_amount for g in profile_grants):,.2f}")
    print(f"Grant history: {len(profile_grants)} grants over {years} years")
```

## Error Handling

### Graceful Degradation
- Missing schedules: Continues with available data
- Partial extraction: Returns what was successfully extracted
- Download failures: Falls back to cached data
- Schema validation failures: Raises clear errors with form type identification

### Quality Assessment
```python
@dataclass
class XML990PFQualityAssessment:
    overall_success_rate: float  # 0-1
    schema_validation_rate: float
    officer_data_completeness: float
    grant_data_completeness: float
    investment_data_completeness: float
    financial_data_completeness: float
    governance_data_completeness: float
    data_freshness_score: float
```

## Integration Patterns

### Multi-Tool Workflow with Network Analysis
```python
# Parse foundation 990-PF
foundation_result = await xml_990pf_tool.execute(pf_criteria)

# Parse profile nonprofit 990
profile_result = await xml_990_tool.execute(profile_criteria)

# Network analysis - match board members
board_connections = find_board_member_connections(
    foundation_officers=foundation_result.officers,
    profile_officers=profile_result.officers
)

# Prioritize grant opportunities
prioritized_foundations = rank_by_influence(board_connections)
```

## Configuration

### Network Analysis Settings
```toml
[tool.network_analysis]
enabled = true
person_name_normalization = true
org_name_normalization = true
role_categorization = true
influence_scoring = true
grant_relationship_mapping = true
```

### Cache Settings
```toml
[tool.caching]
cache_directory = "cache/xml_filings_990pf"
cache_enabled = true
cache_xml_files = true
```

## File Structure
```
xml-990pf-parser-tool/
├── 12factors.toml          # Framework compliance configuration
├── README.md               # This file
├── app/
│   └── xml_990pf_parser.py # Main parser with network analysis (2,310 lines)
└── baml_src/
    └── xml_990pf_parser.baml # BAML schema with network fields (16 classes)
```

## Related Tools

- **xml-990-parser-tool**: Regular nonprofit Form 990 parsing (network analysis pending)
- **xml-990ez-parser-tool**: Small organization Form 990-EZ parsing (network analysis pending)
- **docs/cross_990_field_standardization.md**: Cross-form network analysis strategy

## Testing

```bash
# Test with Fauquier Health Foundation (major private foundation)
python test_990pf_fauquier.py

# Expected output:
# - Officers: 16 (3 executives, 13 board) with normalized names
# - Grants: 20 with normalized recipient names
# - Investments: 10 holdings, $84.8M portfolio
# - Grant capacity: $4.2M/year
# - Influence scores: 1.0 (executives), 0.7 (board)
# - Network fields: Complete for all officers and grants
```

## Framework Compliance Summary

| Factor | Implementation | Status |
|--------|---------------|---------|
| Factor 1 | Git version control | ✅ |
| Factor 2 | Explicit dependencies (asyncio, aiohttp, lxml) | ✅ |
| Factor 3 | Environment config support | ✅ |
| **Factor 4** | **Structured outputs (XML990PFResult)** | ✅ **CORE** |
| Factor 5 | Separate build/run stages | ✅ |
| Factor 6 | Stateless execution | ✅ |
| Factor 7 | Not applicable (library, not service) | N/A |
| Factor 8 | Concurrent download scaling | ✅ |
| Factor 9 | Fast startup (<50ms) | ✅ |
| **Factor 10** | **Single responsibility (990-PF only)** | ✅ **CORE** |
| Factor 11 | Autonomous operation | ✅ |
| Factor 12 | API-first design | ✅ |

## Version History

- **v1.1.0** (2025-09-29): Network analysis enhancement (Phase 2 complete)
  - Added `normalized_person_name`, `role_category`, `influence_score` to officers
  - Added `normalized_recipient_name`, `recipient_ein` to grants
  - Network analysis helper functions (normalize, categorize, score)
  - Cross-990 field standardization documentation

- **v1.0.0** (2025-09-28): Initial implementation with full 12-factor compliance
  - Form 990-PF schema validation
  - Officer, grant, investment, payout, governance extraction
  - Foundation classification and grant analysis
  - Investment portfolio analysis for grant capacity assessment

---

*Part of the Human Layer 12-Factor Agents Framework for Catalynx Grant Research Intelligence Platform*
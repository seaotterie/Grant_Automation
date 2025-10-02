# Profile Enhancement Data Flow Documentation

**Task 16 - Phase 8 Nonprofit Workflow Solidification**
**Date**: 2025-10-02
**Status**: Documentation Complete

---

## Executive Summary

This document maps the complete data flow for profile enhancement and opportunity discovery in the Grant Automation system. The system follows a **one-to-many relationship** where:

- **One Profile** = YOUR organization seeking grants (the grant seeker)
- **Many Opportunities** = Potential funding sources and strategic relationships

### Key Architectural Principles

1. **Profile-Centric Design**: The Profile represents YOUR organization with complete data
2. **Two-Phase Workflow**: Profile Building → Opportunity Discovery
3. **Dual Opportunity Types**: Funding (foundations) + Networking (peer nonprofits)
4. **Quality-Driven**: Multi-source data aggregation with confidence scoring
5. **Tool Orchestration**: BMF → 990/990-PF → Tool 25 → Tool 2

---

## Part 1: Profile Building (YOUR Organization)

### Overview

The Profile represents **YOUR nonprofit organization** that is seeking grants. It's built by aggregating data from multiple sources to create a comprehensive picture for matching with opportunities.

### Data Sources

| Source | Purpose | Data Extracted | Priority |
|--------|---------|----------------|----------|
| **BMF (Business Master File)** | Organization validation | EIN, name, NTEE codes, state, classification | Required |
| **Form 990** | Financial & operational data | Revenue, expenses, assets, programs, governance | High |
| **Tool 25 (Web Intelligence)** | Website enrichment | Mission, programs, leadership, contact info | Medium |
| **Tool 2 (Deep AI Analysis)** | AI-powered insights | Strategic positioning, strengths, competitive analysis | Optional |

### Profile Data Flow

```
STEP 1: Organization Discovery (BMF)
┌─────────────────────────────────────────┐
│ Input: EIN or Organization Name         │
│ Source: BMF (data/nonprofit_intelligence.db) │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ BMF Organization Record                 │
│ - EIN: 541026365                        │
│ - Name: Example Nonprofit               │
│ - NTEE Code: P20 (Education)           │
│ - State: VA                             │
│ - Classification: Public Charity        │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 2: Financial Intelligence (Form 990)
┌─────────────────────────────────────────┐
│ Source: form_990 table                  │
│ - Total Revenue: $5,000,000             │
│ - Total Expenses: $4,800,000            │
│ - Total Assets: $2,000,000              │
│ - Programs: Education services          │
│ - Board Members: 15 trustees            │
│ - Operating Margin: 4.0%                │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 3: Web Intelligence (Tool 25)
┌─────────────────────────────────────────┐
│ Input: website URL (from 990 or GPT)   │
│ Scrapy Spider: organization_profile_spider │
│ - Mission Statement (confidence: 0.85)   │
│ - Leadership Team (confidence: 0.75)     │
│ - Contact Information (confidence: 0.90) │
│ - Program Descriptions (confidence: 0.70)│
│ - Achievements (confidence: 0.65)        │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 4: AI Enhancement (Tool 2) - OPTIONAL
┌─────────────────────────────────────────┐
│ Deep Intelligence Analysis              │
│ - Strategic Positioning                 │
│ - Competitive Advantages                │
│ - Organizational Strengths              │
│ - Grant Readiness Assessment            │
│ - Improvement Recommendations           │
└─────────────────┬───────────────────────┘
                  │
                  ▼

FINAL: Complete Profile
┌─────────────────────────────────────────┐
│ UnifiedProfile (data/profiles/)         │
│ - Core Identity (BMF)                   │
│ - Financial Health (990)                │
│ - Programs & Mission (Tool 25 + 990)    │
│ - Leadership & Governance (990 + Tool 25)│
│ - AI Insights (Tool 2)                  │
│ - Quality Score: 0.85                   │
└─────────────────────────────────────────┘
```

### Profile Quality Scoring

```python
def calculate_profile_quality(profile_data):
    """
    Calculate overall profile quality based on data completeness and confidence.

    Quality = (BMF_Score * 0.20) + (990_Score * 0.35) +
              (Tool25_Score * 0.25) + (Tool2_Score * 0.20)
    """

    # BMF Score (0.0-1.0)
    bmf_score = 1.0 if has_all_required_fields(bmf_data) else 0.0

    # 990 Score (0.0-1.0)
    financial_completeness = count_populated_fields(form_990) / total_fields

    # Tool 25 Score (0.0-1.0)
    web_intel_score = average_confidence(tool25_data)

    # Tool 2 Score (0.0-1.0) - OPTIONAL
    ai_score = 1.0 if has_ai_analysis else 0.0

    return (bmf_score * 0.20) + (financial_completeness * 0.35) +
           (web_intel_score * 0.25) + (ai_score * 0.20)
```

**Quality Thresholds**:
- **EXCELLENT** (≥0.85): All sources complete, high confidence
- **GOOD** (0.70-0.84): Most sources complete, medium confidence
- **FAIR** (0.50-0.69): Basic data complete, some gaps
- **POOR** (<0.50): Missing critical data, low confidence

---

## Part 2: Opportunity Discovery & Research

### Overview

Once the Profile is established, the system discovers and researches **opportunities** that match your organization's criteria. Opportunities come in two types:

1. **Funding Opportunities** (PRIMARY): Foundations that make grants
2. **Networking Opportunities** (SECONDARY): Peer nonprofits for partnerships

### Opportunity Type 1: Funding (Foundations with 990-PF)

**Priority**: HIGH - Direct funding sources

**Discovery Criteria**:
- Foundation code in BMF (foundation_code = 15 or 16)
- Geographic alignment (same state or national scope)
- NTEE code relevance (foundation supports your sector)
- Grant-making capacity (distribution amount > $0)

**Data Flow**:

```
STEP 1: Foundation Discovery (BMF)
┌─────────────────────────────────────────┐
│ Profile Criteria:                       │
│ - NTEE Codes: P20, B25                  │
│ - States: VA, MD, DC                    │
│ - Foundation Code: 15, 16               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ BMF Query Results                       │
│ SELECT * FROM bmf_organizations         │
│ WHERE foundation_code IN (15, 16)       │
│   AND state IN ('VA', 'MD', 'DC')       │
│                                          │
│ Results: 1,500 foundations found        │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 2: Foundation Intelligence (Form 990-PF)
┌─────────────────────────────────────────┐
│ For Each Foundation:                    │
│                                          │
│ Source: form_990pf table                │
│ - Total Assets: $40,798,643,857         │
│ - Distribution Amount: $1,607,157,925   │
│ - Grants Approved (Future): $55,575,526 │
│ - Investment Income: $1,915,656,584     │
│ - Investment Excise Tax: $26,385,610    │
│                                          │
│ Grant-Making Capacity: MAJOR            │
│ (Distributing $1.6B+ annually)          │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 3: Foundation Web Intelligence (Tool 25)
┌─────────────────────────────────────────┐
│ Use Case 3: Foundation Research         │
│ Scrapy Spider: foundation_profile_spider│
│                                          │
│ - Grant Application Process              │
│ - Funding Priorities                     │
│ - Recent Grant Awards                    │
│ - Application Deadlines                  │
│ - Contact Information                    │
│ - Board Members                          │
│                                          │
│ Cost: $0.10-0.20 per foundation         │
│ Confidence: 0.75-0.85                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 4: Foundation Match Analysis (Tool 2)
┌─────────────────────────────────────────┐
│ Deep Intelligence: Funding Fit Analysis │
│                                          │
│ Compare:                                 │
│ - Your Mission ↔ Foundation Priorities  │
│ - Your Programs ↔ Past Grant Recipients │
│ - Your Budget ↔ Typical Grant Sizes     │
│ - Your Geography ↔ Foundation Scope     │
│                                          │
│ Output:                                  │
│ - Match Score: 0.87 (EXCELLENT)         │
│ - Strategic Recommendations              │
│ - Application Approach                   │
│ - Risk Assessment                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼

FINAL: Ranked Funding Opportunity
┌─────────────────────────────────────────┐
│ Opportunity Record                      │
│ - Type: FUNDING                         │
│ - Foundation: Lilly Endowment Inc       │
│ - Grant Capacity: $1.6B/year            │
│ - Match Score: 0.87                     │
│ - Priority: HIGH                        │
│ - Next Steps: Application strategy      │
└─────────────────────────────────────────┘
```

### Opportunity Type 2: Networking (Peer Nonprofits with 990)

**Priority**: MEDIUM/LOW - Strategic relationships, indirect funding

**Discovery Criteria**:
- Similar NTEE codes (same sector)
- Geographic overlap (same service areas)
- Similar budget size (comparable scale)
- Complementary programs (collaboration potential)

**Data Flow**:

```
STEP 1: Peer Organization Discovery (BMF)
┌─────────────────────────────────────────┐
│ Profile Criteria:                       │
│ - NTEE Codes: P20 (Education)           │
│ - States: VA, MD, DC                    │
│ - NOT Foundation (foundation_code IS NULL)│
│ - Exclude YOUR EIN                       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ BMF Query Results                       │
│ SELECT * FROM bmf_organizations         │
│ WHERE ntee_code LIKE 'P%'               │
│   AND state IN ('VA', 'MD', 'DC')       │
│   AND foundation_code IS NULL           │
│   AND ein != YOUR_EIN                   │
│                                          │
│ Results: 4,220 peer nonprofits found    │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 2: Peer Financial & Operational Data (Form 990)
┌─────────────────────────────────────────┐
│ For Each Peer Organization:             │
│                                          │
│ Source: form_990 table                  │
│ - Total Revenue: $8,500,000             │
│ - Total Expenses: $8,200,000            │
│ - Programs: Similar education services   │
│ - Board Members: 12 trustees            │
│ - Operating Margin: 3.5%                │
│                                          │
│ Financial Health: STRONG                │
│ Program Overlap: HIGH                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 3: Network Analysis
┌─────────────────────────────────────────┐
│ Tool 12: Network Intelligence           │
│                                          │
│ Analyze:                                 │
│ - Board Member Overlap                   │
│ - Shared Funders (from 990 data)        │
│ - Geographic Proximity                   │
│ - Mission Similarity                     │
│                                          │
│ Potential:                               │
│ - Partnership Score: 0.72                │
│ - Board Connections: 2 shared trustees   │
│ - Funder Overlap: 3 common foundations  │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 4: Peer Web Intelligence (Tool 25) - OPTIONAL
┌─────────────────────────────────────────┐
│ Use Case 1: Profile Builder             │
│ Scrapy Spider: organization_profile_spider│
│                                          │
│ - Programs & Initiatives                 │
│ - Partnerships & Collaborations          │
│ - Success Stories                        │
│ - Contact Information                    │
│                                          │
│ Cost: $0.05-0.10 per organization       │
└─────────────────┬───────────────────────┘
                  │
                  ▼

STEP 5: Networking Potential Analysis (Tool 2) - OPTIONAL
┌─────────────────────────────────────────┐
│ Deep Intelligence: Partnership Analysis  │
│                                          │
│ Evaluate:                                │
│ - Collaboration Opportunities            │
│ - Shared Grant Applications              │
│ - Knowledge Transfer Potential           │
│ - Resource Sharing                       │
│                                          │
│ Output:                                  │
│ - Networking Score: 0.68                 │
│ - Collaboration Ideas                    │
│ - Introduction Strategy                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼

FINAL: Ranked Networking Opportunity
┌─────────────────────────────────────────┐
│ Opportunity Record                      │
│ - Type: NETWORKING                      │
│ - Organization: Similar Education Nonprofit│
│ - Partnership Score: 0.68               │
│ - Shared Connections: 2 board, 3 funders│
│ - Priority: MEDIUM                      │
│ - Next Steps: Introduction strategy     │
└─────────────────────────────────────────┘
```

### Opportunity Scoring

```python
def score_funding_opportunity(profile, foundation):
    """
    Score a foundation opportunity based on fit with profile.

    Score = (Mission_Match * 0.30) + (Geographic_Fit * 0.20) +
            (Grant_Size_Fit * 0.25) + (Past_Recipients * 0.15) +
            (Application_Feasibility * 0.10)
    """

    # Mission alignment (0.0-1.0)
    mission_score = calculate_ntee_similarity(profile.ntee_codes,
                                             foundation.funded_ntee_codes)

    # Geographic fit (0.0-1.0)
    geo_score = 1.0 if foundation.state in profile.states else 0.5

    # Grant size fit (0.0-1.0)
    typical_grant = foundation.avg_grant_size
    grant_size_score = 1.0 if (profile.budget * 0.1 <= typical_grant <=
                                profile.budget * 0.3) else 0.5

    # Similar recipients (0.0-1.0)
    recipient_score = count_similar_recipients(foundation.past_grants,
                                               profile) / 10

    # Application feasibility (0.0-1.0)
    feasibility = 1.0 if has_open_application() else 0.3

    return (mission_score * 0.30) + (geo_score * 0.20) +
           (grant_size_score * 0.25) + (recipient_score * 0.15) +
           (feasibility * 0.10)


def score_networking_opportunity(profile, peer_org):
    """
    Score a networking opportunity based on strategic value.

    Score = (Mission_Similarity * 0.25) + (Board_Connections * 0.25) +
            (Funder_Overlap * 0.30) + (Collaboration_Potential * 0.20)
    """

    # Mission similarity (0.0-1.0)
    mission_score = calculate_ntee_similarity(profile.ntee_codes,
                                             peer_org.ntee_codes)

    # Board connections (0.0-1.0)
    shared_board = count_shared_board_members(profile, peer_org)
    board_score = min(shared_board / 5, 1.0)

    # Funder overlap (0.0-1.0)
    shared_funders = count_shared_funders(profile, peer_org)
    funder_score = min(shared_funders / 10, 1.0)

    # Collaboration potential (0.0-1.0)
    collab_score = assess_collaboration_potential(profile, peer_org)

    return (mission_score * 0.25) + (board_score * 0.25) +
           (funder_score * 0.30) + (collab_score * 0.20)
```

**Scoring Thresholds**:

**Funding Opportunities**:
- **EXCELLENT** (≥0.80): Top priority, strong fit
- **GOOD** (0.65-0.79): High priority, good fit
- **FAIR** (0.50-0.64): Medium priority, worth exploring
- **POOR** (<0.50): Low priority, weak fit

**Networking Opportunities**:
- **HIGH** (≥0.70): Strong collaboration potential
- **MEDIUM** (0.50-0.69): Moderate networking value
- **LOW** (<0.50): Minimal strategic value

---

## Part 3: Data Quality & Validation

### Data Completeness Matrix

| Data Source | Critical Fields | Optional Fields | Quality Impact |
|-------------|----------------|-----------------|----------------|
| **BMF** | EIN, Name, NTEE, State | Address, City | 20% of profile score |
| **Form 990** | Revenue, Expenses, Assets | Programs, Board | 35% of profile score |
| **Form 990-PF** | Assets, Distribution Amount | Grants Approved, Investment Income | 30% of opportunity score |
| **Tool 25** | Mission Statement | Leadership, Programs, Contact | 25% of profile score |
| **Tool 2** | AI Analysis Complete | Recommendations | 20% of profile score |

### Validation Rules

```python
class ProfileValidator:
    """Validate profile data quality and completeness."""

    def validate_bmf_data(self, bmf_data):
        """Required: EIN, Name, NTEE Code, State."""
        required = ['ein', 'name', 'ntee_code', 'state']
        return all(bmf_data.get(field) for field in required)

    def validate_990_data(self, form_990):
        """Required: Revenue, Expenses, Assets."""
        required = ['totrevenue', 'totfuncexpns', 'totassetsend']
        return all(form_990.get(field) and form_990[field] > 0
                   for field in required)

    def validate_990pf_data(self, form_990pf):
        """Required: Assets, Distribution Amount."""
        return (form_990pf.get('totassetsend', 0) > 0 and
                form_990pf.get('distribamt', 0) >= 0)

    def validate_tool25_data(self, tool25_data):
        """Required: At least one high-confidence field."""
        return any(field.get('confidence', 0) >= 0.7
                   for field in tool25_data.values())
```

### Error Handling & Graceful Degradation

```python
class ProfileBuilder:
    """Build profile with graceful degradation."""

    def build_profile(self, ein):
        """Build profile with fallbacks for missing data."""

        profile = UnifiedProfile(ein=ein)
        errors = []

        # Step 1: BMF (REQUIRED)
        try:
            bmf_data = self.get_bmf_data(ein)
            profile.update_from_bmf(bmf_data)
        except Exception as e:
            errors.append(f"BMF lookup failed: {e}")
            return None  # Cannot proceed without BMF

        # Step 2: Form 990 (HIGH PRIORITY)
        try:
            form_990 = self.get_form_990(ein)
            profile.update_from_990(form_990)
        except Exception as e:
            errors.append(f"Form 990 lookup failed: {e}")
            # Continue with degraded profile

        # Step 3: Tool 25 (MEDIUM PRIORITY)
        try:
            web_data = self.run_tool25(ein, profile.website)
            profile.update_from_web(web_data)
        except Exception as e:
            errors.append(f"Web scraping failed: {e}")
            # Continue with degraded profile

        # Step 4: Tool 2 (OPTIONAL)
        try:
            ai_data = self.run_tool2(profile)
            profile.update_from_ai(ai_data)
        except Exception as e:
            errors.append(f"AI analysis failed: {e}")
            # Continue without AI insights

        profile.errors = errors
        profile.quality_score = self.calculate_quality(profile)

        return profile
```

---

## Part 4: Tool Integration & Orchestration

### Tool Execution Flow

```
Profile Building Workflow:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   BMF    │ -> │   990    │ -> │ Tool 25  │ -> │ Tool 2   │
│Discovery │    │Financial │    │   Web    │    │   AI     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
   REQUIRED      HIGH PRIORITY   MEDIUM PRIORITY   OPTIONAL

   $0.00         $0.00           $0.05-0.10        $0.75+
   < 1s          < 1s            10-60s            5-10min


Opportunity Discovery Workflow (Funding):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   BMF    │ -> │  990-PF  │ -> │ Tool 25  │ -> │ Tool 2   │
│Foundation│    │Foundation│    │Foundation│    │ Match    │
│Discovery │    │ Intel    │    │   Web    │    │ Analysis │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
   REQUIRED      HIGH PRIORITY   MEDIUM PRIORITY   OPTIONAL

   $0.00         $0.00           $0.10-0.20        $0.75+
   < 1s          < 1s            10-60s            5-10min


Opportunity Discovery Workflow (Networking):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   BMF    │ -> │   990    │ -> │ Network  │ -> │ Tool 2   │
│   Peer   │    │   Peer   │    │ Analysis │    │Partnership│
│Discovery │    │   Intel  │    │          │    │ Analysis │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
   REQUIRED      HIGH PRIORITY   MEDIUM PRIORITY   OPTIONAL

   $0.00         $0.00           $0.00             $0.75+
   < 1s          < 1s            < 1s              5-10min
```

### API Integration Points

```python
# Profile Building API
POST /api/profiles/create
{
  "ein": "541026365",
  "run_tool25": true,    # Enable web scraping
  "run_tool2": false,    # Skip AI analysis (optional)
  "quality_threshold": 0.70  # Minimum acceptable quality
}

# Opportunity Discovery API
POST /api/profiles/{profile_id}/discover
{
  "opportunity_types": ["funding", "networking"],
  "max_results": 100,
  "min_score": 0.50,
  "geographic_scope": ["VA", "MD", "DC"],
  "ntee_filters": ["P20", "B25"]
}

# Opportunity Research API
POST /api/opportunities/{opportunity_id}/research
{
  "depth": "standard",    # quick | standard | enhanced | complete
  "include_web": true,    # Run Tool 25
  "include_ai": true,     # Run Tool 2
  "match_analysis": true  # Compare with profile
}
```

### Orchestration Specification

```yaml
# Profile Building Workflow
name: profile_building
description: Build complete profile for grant-seeking organization

steps:
  - name: bmf_lookup
    tool: BMF Discovery (Tool 17)
    required: true
    timeout: 5s
    retry: 3
    error_handling: fail_workflow

  - name: financial_intelligence
    tool: Form 990 Query
    required: false
    timeout: 5s
    retry: 2
    error_handling: continue
    depends_on: [bmf_lookup]

  - name: web_intelligence
    tool: Web Intelligence (Tool 25)
    required: false
    timeout: 60s
    retry: 1
    error_handling: continue
    depends_on: [bmf_lookup]
    condition: profile.website is not None

  - name: ai_analysis
    tool: Deep Intelligence (Tool 2)
    required: false
    timeout: 600s
    retry: 0
    error_handling: continue
    depends_on: [bmf_lookup, financial_intelligence, web_intelligence]
    condition: user_requested AND quality >= 0.70

quality_gates:
  - stage: after_bmf_lookup
    minimum_quality: 0.20
    fail_below: true

  - stage: after_financial_intelligence
    minimum_quality: 0.55
    warn_below: true

  - stage: final
    minimum_quality: 0.70
    recommend_ai: true
```

---

## Part 5: Database Schema & Relationships

### Entity Relationship Diagram

```
┌─────────────────────────────────────┐
│        bmf_organizations            │
│  (700K+ organizations)              │
│  - ein (PK)                         │
│  - name                             │
│  - ntee_code                        │
│  - state                            │
│  - foundation_code                  │
└─────────────┬───────────────────────┘
              │
              │ 1:1
              ▼
┌─────────────────────────────────────┐
│         form_990                    │
│  (626K+ organizations)              │
│  - ein (PK)                         │
│  - tax_year (PK)                    │
│  - totrevenue                       │
│  - totfuncexpns                     │
│  - totassetsend                     │
└─────────────────────────────────────┘

              │ 1:1
              ▼
┌─────────────────────────────────────┐
│         form_990pf                  │
│  (220K+ foundations)                │
│  - ein (PK)                         │
│  - tax_year (PK)                    │
│  - totassetsend                     │
│  - distribamt                       │
│  - grntapprvfut                     │
└─────────────────────────────────────┘

              │
              │ Referenced by
              ▼
┌─────────────────────────────────────┐
│        UnifiedProfile               │
│  (YOUR organization)                │
│  - profile_id (PK)                  │
│  - ein                              │
│  - ntee_codes []                    │
│  - geographic_scope                 │
│  - discovery_status                 │
│  - quality_score                    │
└─────────────┬───────────────────────┘
              │
              │ 1:MANY
              ▼
┌─────────────────────────────────────┐
│      UnifiedOpportunity             │
│  (Potential funders/partners)       │
│  - opportunity_id (PK)              │
│  - profile_id (FK)                  │
│  - target_ein                       │
│  - opportunity_type (funding/networking) │
│  - match_score                      │
│  - priority                         │
└─────────────────────────────────────┘
```

### Key Database Queries

```sql
-- Profile Building: Get organization financial data
SELECT
    b.ein,
    b.name,
    b.ntee_code,
    b.state,
    f.totrevenue,
    f.totfuncexpns,
    f.totassetsend,
    f.tax_year
FROM bmf_organizations b
LEFT JOIN form_990 f ON b.ein = f.ein
WHERE b.ein = ?
ORDER BY f.tax_year DESC
LIMIT 1;

-- Funding Opportunity Discovery: Find foundations
SELECT
    b.ein,
    b.name,
    b.state,
    f.totassetsend,
    f.distribamt,
    f.grntapprvfut
FROM bmf_organizations b
INNER JOIN form_990pf f ON b.ein = f.ein
WHERE b.foundation_code IN (15, 16)
  AND b.state IN (?, ?, ?)
  AND f.distribamt > 0
ORDER BY f.distribamt DESC
LIMIT 100;

-- Networking Opportunity Discovery: Find peer nonprofits
SELECT
    b.ein,
    b.name,
    b.ntee_code,
    b.state,
    f.totrevenue,
    f.totfuncexpns
FROM bmf_organizations b
INNER JOIN form_990 f ON b.ein = f.ein
WHERE b.ntee_code LIKE ?
  AND b.state IN (?, ?, ?)
  AND b.foundation_code IS NULL
  AND b.ein != ?
  AND f.totrevenue BETWEEN ? AND ?
ORDER BY f.totrevenue DESC
LIMIT 100;
```

---

## Part 6: Cost & Performance Optimization

### Cost Analysis by Workflow

| Workflow | BMF | 990/990-PF | Tool 25 | Tool 2 | Total |
|----------|-----|------------|---------|--------|-------|
| **Profile Building** | $0.00 | $0.00 | $0.05-0.10 | $0.75+ | $0.80-0.85+ |
| **Funding Opp (per 100)** | $0.00 | $0.00 | $10-20 | $75+ | $85-95+ |
| **Networking Opp (per 100)** | $0.00 | $0.00 | Optional | $75+ | $75+ |

**Optimization Strategies**:

1. **Batch Processing**: Process multiple opportunities in parallel
2. **Caching**: Cache BMF and 990 data (never changes for past years)
3. **Selective Tool 25**: Only scrape high-priority opportunities
4. **Phased Tool 2**: Start with quick depth ($0.75), upgrade if promising
5. **Quality Gates**: Stop processing if quality falls below threshold

### Performance Benchmarks

| Operation | Target | Actual (Task 13) | Status |
|-----------|--------|------------------|--------|
| BMF Lookup | < 1s | ~0.5s | ✅ Excellent |
| 990 Query | < 1s | ~0.3s | ✅ Excellent |
| 990-PF Query | < 1s | ~0.3s | ✅ Excellent |
| Tool 25 Scrape | < 60s | 10-60s | ✅ Good |
| Tool 2 Quick | < 5min | N/A | ⏳ Pending |
| Profile Build (complete) | < 5min | N/A | ⏳ Pending |

---

## Part 7: Implementation Checklist

### Phase 1: Profile Building Implementation ✅

- [x] BMF Discovery integration (Task 11)
- [x] Form 990 query implementation (Task 13)
- [x] Tool 25 Profile Builder integration (Task 9)
- [x] Profile quality scoring methodology
- [ ] Tool 2 integration (quick depth)
- [ ] Profile validation rules
- [ ] Error handling & graceful degradation

### Phase 2: Opportunity Discovery Implementation

- [x] BMF Discovery with foundation filters (Task 12)
- [x] Form 990-PF foundation intelligence (Task 13)
- [ ] Networking opportunity discovery (990 peer matching)
- [ ] Opportunity scoring algorithms
- [ ] Priority ranking
- [ ] Down-selection workflow

### Phase 3: Opportunity Research Implementation

- [ ] Tool 25 Foundation Research (Use Case 3)
- [ ] Tool 25 Peer Research (Use Case 1)
- [ ] Tool 2 Match Analysis
- [ ] Network Analysis integration (Tool 12)
- [ ] Research result aggregation
- [ ] Comparison and ranking

### Phase 4: Orchestration & API

- [ ] Workflow orchestration engine
- [ ] Profile building API endpoints
- [ ] Opportunity discovery API endpoints
- [ ] Opportunity research API endpoints
- [ ] Quality gate enforcement
- [ ] Cost tracking and reporting

---

## Conclusion

This documentation provides a complete specification for the profile enhancement and opportunity discovery workflows. The key insights are:

1. **One-to-Many Relationship**: One Profile (YOUR org) → Many Opportunities (funders + partners)
2. **Dual Opportunity Types**: Funding (990-PF) high priority, Networking (990) medium/low priority
3. **Multi-Source Intelligence**: BMF → 990/990-PF → Tool 25 → Tool 2
4. **Quality-Driven**: Scoring methodology ensures data completeness and confidence
5. **Cost-Optimized**: Selective tool use based on priority and quality gates

**Next Steps**: Task 17 - Implement profile enhancement orchestration using this specification.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Author**: Grant Automation Project
**Status**: Complete - Ready for Implementation

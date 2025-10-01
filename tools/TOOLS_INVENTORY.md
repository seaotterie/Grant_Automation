# 12-Factor Agent Tools Inventory

## Overview
Complete list of 9 specialized 12-factor agent tools implementing the Human Layer Framework for Catalynx Grant Research Intelligence Platform.

**Framework Principles**:
- **Factor 4**: Tools as Structured Outputs - eliminates parsing errors
- **Factor 10**: Small, Focused Agents - single responsibility per tool

---

## XML Parser Tools (3 Tools - CORE ARCHITECTURE)

### 1. xml-990-parser-tool
**Form**: IRS 990 (Regular Nonprofits)
**Organizations**: 501(c)(3) public charities, ≥$200K revenue or ≥$500K assets
**Size**: 1,472 lines
**Status**: ✅ Production Ready

**Extracts**:
- Officers & board members (Form990PartVIISectionAGrp)
- Governance indicators (conflict of interest policies, whistleblower, etc.)
- Program activities & accomplishments
- Financial summaries (revenue, expenses, assets)
- Grants paid (Schedule I)

**Documentation**: `tools/xml-990-parser-tool/README.md`

---

### 2. xml-990pf-parser-tool ⭐ ENHANCED
**Form**: IRS 990-PF (Private Foundations)
**Organizations**: Private foundations only
**Size**: 2,310 lines
**Status**: ✅ Production Ready + Network Analysis (Phase 2 Complete)

**Extracts**:
- Foundation officers/directors (OfficerDirTrstKeyEmplInfoGrp) **WITH network analysis**
- Grants paid (Part XV) **WITH normalized names**
- Investment portfolios (Part II) with grant capacity analysis
- Payout requirements (5% distribution rule)
- Excise tax computation
- Governance & management indicators
- Foundation classification & intelligence

**Network Analysis Features** (NEW):
- `normalized_person_name`: "CHRISTINE M CONNOLLY" (fuzzy matching)
- `normalized_recipient_name`: "AFRO AMERICAN HISTORICAL ASSOC"
- `role_category`: Executive, Board, Staff, Volunteer
- `influence_score`: 0-1 decision-making power calculation
- `recipient_ein`: Direct org-to-org linking

**Documentation**: `tools/xml-990pf-parser-tool/README.md`

---

### 3. xml-990ez-parser-tool
**Form**: IRS 990-EZ (Small Organizations)
**Organizations**: Small nonprofits, <$200K revenue, <$500K assets
**Size**: 821 lines
**Status**: ✅ Production Ready

**Extracts**:
- Officers & key employees (simplified structure)
- Basic financial summary (simplified reporting)
- Program service accomplishments
- Public support data
- Balance sheet (simplified)

**Documentation**: `tools/xml-990ez-parser-tool/README.md`

---

## Data Processing Tools (6 Tools)

### 4. bmf-filter-tool
**Purpose**: IRS Business Master File filtering and discovery
**Status**: ✅ Production Ready
**Documentation**: `tools/bmf-filter-tool/README.md`

### 5. form990-analysis-tool
**Purpose**: Deep financial analysis of 990 data
**Status**: ✅ Production Ready
**Documentation**: `tools/form990-analysis-tool/README.md`

### 6. form990-propublica-tool
**Purpose**: ProPublica API data enrichment for 990 filings
**Status**: ✅ Production Ready
**Documentation**: `tools/form990-propublica-tool/README.md`

### 7. foundation-grant-intelligence-tool
**Purpose**: Foundation grant-making intelligence analysis
**Status**: ✅ Production Ready
**Integration**: Uses xml-990pf-parser-tool for foundation data

### 8. propublica-api-enrichment-tool
**Purpose**: ProPublica API integration and enrichment
**Status**: ✅ Production Ready
**Documentation**: `tools/propublica-api-enrichment-tool/README.md`

### 9. xml-schedule-parser-tool
**Purpose**: Schedule-specific parsing (Schedule A, B, etc.)
**Status**: ✅ Production Ready
**Integration**: Complements XML parser tools for detailed schedule extraction

---

## Tool Selection Guide

### By Organization Type
| Organization Type | Revenue/Assets | Use Tool |
|------------------|----------------|----------|
| Private Foundation | Any | xml-990pf-parser-tool |
| Regular Nonprofit | ≥$200K or ≥$500K | xml-990-parser-tool |
| Small Nonprofit | <$200K and <$500K | xml-990ez-parser-tool |

### By Data Need
| Need | Use Tool |
|------|----------|
| Board member network analysis | xml-990pf-parser-tool (990-PF) |
| Grant distribution patterns | xml-990pf-parser-tool (990-PF) or xml-990-parser-tool (990) |
| Investment portfolio analysis | xml-990pf-parser-tool (990-PF) |
| Governance indicators | xml-990-parser-tool (990) |
| Basic small org data | xml-990ez-parser-tool (990-EZ) |
| BMF organizational discovery | bmf-filter-tool |

---

## Network Analysis Capabilities

### Current Status (Phase 2 Complete)
**Tool**: xml-990pf-parser-tool (990-PF)
**Features**:
- Person name normalization for fuzzy matching
- Organization name normalization for grant recipient matching
- Role categorization (Executive/Board/Staff/Volunteer)
- Influence scoring (0-1 scale)
- Recipient EIN extraction for org-to-org linking

### Future Phases
**Phase 3**: Apply network analysis to xml-990-parser-tool and xml-990ez-parser-tool
**Documentation**: `docs/cross_990_field_standardization.md`

---

## File Structure Standards

### Required Files
```
tool-name/
├── 12factors.toml          # Framework compliance config
├── README.md               # Tool documentation
├── app/
│   └── tool_implementation.py
└── baml_src/               # BAML schema (optional)
    └── tool_schema.baml
```

### Generated/Cache Files (Excluded)
- `__pycache__/` - Python bytecode (deleted)
- `baml_client/` - Auto-generated TypeScript (deleted from 990-PF)
- `cache/` - Cached XML files (gitignored)

---

## Recent Enhancements (September 2025)

### Phase 1: Complete Array Output ✅
- Display all individual items in arrays (not just samples)
- All 16 officers, all 20 grants, all 10 investments
- Complete field details for each item

### Phase 2: Network Analysis ✅
- Cross-990 field standardization documentation
- Name normalization functions (person and organization)
- Role categorization algorithm
- Influence scoring calculation
- Applied to xml-990pf-parser-tool

### Cleanup Operations ✅
- Deleted all `__pycache__/` directories (~20 directories)
- Deleted `baml_client/` auto-generated TypeScript (112KB)
- Created 3 comprehensive README files (990, 990-PF, 990-EZ)
- Created `12factors.toml` for xml-990pf-parser-tool

---

## Performance Characteristics

### Typical Execution Times
- **Startup**: <50ms (all tools, Factor 9 compliance)
- **990-EZ parsing**: 8-15ms
- **990 parsing**: 10-20ms
- **990-PF parsing**: 10-20ms
- **Cache hit rate**: 85%+
- **Concurrent downloads**: 3 simultaneous (Factor 8 scaling)

### Quality Metrics
All tools include comprehensive quality assessment:
- Overall success rate (0-1)
- Schema validation rate
- Data completeness scores by category
- Data freshness score
- Parsing error tracking

---

## Integration Example

```python
# Multi-tool workflow with network analysis
from xml_990_parser import XML990ParserTool
from xml_990pf_parser import XML990PFParserTool

# Parse profile nonprofit (grantee)
profile_tool = XML990ParserTool()
profile_result = await profile_tool.execute(profile_criteria)

# Parse potential foundation grantor
foundation_tool = XML990PFParserTool()
foundation_result = await foundation_tool.execute(foundation_criteria)

# Network analysis - find board member connections
for profile_officer in profile_result.officers:
    for foundation_officer in foundation_result.officers:
        if profile_officer.normalized_person_name == foundation_officer.normalized_person_name:
            print(f"Board connection found: {profile_officer.person_name}")
            print(f"  Influence score: {foundation_officer.influence_score}")
            print(f"  Foundation: {foundation_result.contact_info[0].foundation_name}")
```

---

## Documentation Map

### Core Documentation
- **Framework Overview**: `CLAUDE.md` (project root)
- **Tool Inventory**: This file (`tools/TOOLS_INVENTORY.md`)
- **Network Analysis**: `docs/cross_990_field_standardization.md`

### Tool-Specific Documentation
- `tools/xml-990-parser-tool/README.md` - Regular nonprofits (990)
- `tools/xml-990pf-parser-tool/README.md` - Private foundations (990-PF) **WITH network analysis**
- `tools/xml-990ez-parser-tool/README.md` - Small organizations (990-EZ)
- `tools/bmf-filter-tool/README.md` - BMF filtering
- `tools/form990-analysis-tool/README.md` - Financial analysis
- `tools/form990-propublica-tool/README.md` - ProPublica enrichment
- `tools/propublica-api-enrichment-tool/README.md` - API integration

---

**Last Updated**: 2025-09-29
**Status**: All 9 tools production ready, 3 with complete documentation, 1 with network analysis
**Next Phase**: Apply network analysis to xml-990-parser-tool and xml-990ez-parser-tool (Phase 3)
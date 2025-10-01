# Catalynx Tier System Documentation

**Status**: LEGACY - Replaced by Tool 2 (Deep Intelligence Tool) with depth parameters
**Date**: 2025-09-30
**Version**: Consolidated from 3 separate tier documents

---

## Overview

The original tier system provided 4 business packages for grant intelligence analysis:
- **CURRENT** ($0.75): Quick 4-stage analysis
- **STANDARD** ($7.50): + Historical funding patterns
- **ENHANCED** ($22.00): + Document analysis and network intelligence
- **COMPLETE** ($42.00): + Policy analysis and strategic consulting

**Current Status**: This system has been modernized into **Tool 2: Deep Intelligence Tool** with configurable depth parameters.

---

## Modern Implementation (Tool 2)

### Depth Parameters
```python
# New 12-factor approach
from tools.deep_intelligence_tool import analyze_opportunity

result = await analyze_opportunity(
    opportunity_id="OPP-2025-001",
    depth="standard",  # quick | standard | enhanced | complete
    include_scoring=True,
    include_network=True
)
```

### Depth Mapping
- **quick**: $0.75, 5-10 min (replaces CURRENT tier)
- **standard**: $7.50, 15-20 min (replaces STANDARD tier)
- **enhanced**: $22.00, 30-45 min (replaces ENHANCED tier)
- **complete**: $42.00, 45-60 min (replaces COMPLETE tier)

---

## Legacy Tier System (DEPRECATED)

### Original Architecture

The tier system used 4 separate processors:
- `current_tier_processor.py`
- `standard_tier_processor.py`
- `enhanced_tier_processor.py`
- `complete_tier_processor.py`

Each processor duplicated significant code and AI logic, leading to:
- Maintenance overhead (4 separate files)
- Inconsistent behavior across tiers
- Difficulty adding new features
- Poor 12-factor compliance

### Migration to Tool 2

Tool 2 consolidates all tiers into a single tool with depth configuration:

**Benefits**:
- Single codebase (DRY principle)
- Consistent behavior across depths
- Easy feature additions
- 12-factor compliant
- Better testing and validation

**Processor Deprecation**:
- Original tier processors moved to `src/processors/_deprecated/`
- Scheduled for removal in Phase 8
- All functionality preserved in Tool 2

---

## Tier Features Breakdown

### CURRENT Tier ($0.75)
**Components**:
- PLAN tab analysis (opportunity screening)
- ANALYZE tab analysis (success scoring)
- EXAMINE tab analysis (basic intelligence)
- APPROACH tab analysis (strategic recommendations)

**Performance**: 5-10 minutes
**AI Cost**: ~$0.75 per opportunity

### STANDARD Tier ($7.50)
**Additional Components**:
- Historical funding analysis (USASpending.gov data)
- Geographic distribution patterns
- Temporal funding trends
- Success factor identification

**Performance**: 15-20 minutes
**AI Cost**: ~$7.50 per opportunity

### ENHANCED Tier ($22.00)
**Additional Components**:
- Document analysis (RFPs, guidelines, past awards)
- Network intelligence (board connections, relationships)
- Decision maker profiling
- Competitive landscape analysis

**Performance**: 30-45 minutes
**AI Cost**: ~$22.00 per opportunity

### COMPLETE Tier ($42.00)
**Additional Components**:
- Policy analysis and alignment
- Real-time monitoring setup
- 26+ page comprehensive reports
- Strategic consulting insights

**Performance**: 45-60 minutes
**AI Cost**: ~$42.00 per opportunity

---

## Tab Processors (4-Tab System)

The tier system internally used 4 tab processors:

1. **PLAN Tab** (`ai_lite_unified_processor.py`)
   - Fast opportunity screening
   - Basic eligibility check
   - Cost: $0.0004 per opportunity

2. **ANALYZE Tab** (`ai_heavy_light_analyzer.py`)
   - Success probability scoring
   - Competitive assessment
   - Cost: $0.02 per opportunity

3. **EXAMINE Tab** (`ai_heavy_deep_researcher.py`)
   - Deep intelligence gathering
   - Network analysis
   - Cost: $0.50-$2.00 per opportunity

4. **APPROACH Tab** (`ai_heavy_researcher.py`)
   - Strategic recommendations
   - Winning strategy development
   - Cost: $0.25-$1.00 per opportunity

**Migration**: Tab processors replaced by Tool 1 (Opportunity Screening) and Tool 2 (Deep Intelligence)

---

## Scoring Integration (NEW)

Tool 2 now integrates with **Tool 20: Multi-Dimensional Scorer** for sophisticated scoring:

### Stage-Specific Scoring
- DISCOVER stage: Mission alignment, geographic fit, financial match
- PLAN stage: Success probability, organizational capacity
- ANALYZE stage: Competitive position, strategic alignment
- EXAMINE stage: Deep intelligence quality, relationship pathways
- APPROACH stage: Overall viability, strategic value

### Boost Factors
Enhanced data availability increases relevant dimension scores:
- Financial data: +10%
- Network data: +15%
- Historical data: +12%
- Risk assessment: +8%

---

## Report Generation (NEW)

Tool 2 now integrates with **Tool 21: Report Generator** for professional output:

### Report Templates
1. **Comprehensive** (DOSSIER structure - 20+ sections)
2. **Executive** (2-page summary for decision makers)
3. **Risk** (Risk-focused assessment with matrices)
4. **Implementation** (Action plan and timeline)

### Output Quality
- Masters thesis-level comprehensive analysis
- Professional HTML formatting with responsive design
- Table of contents with smooth scrolling
- Metrics, tables, and visualization support

---

## API Integration

### Modern API (12-Factor)
```python
# Execute Tool 2 via API
POST /api/v1/tools/deep-intelligence-tool/execute
{
    "opportunity_id": "OPP-2025-001",
    "depth": "standard",
    "output_format": "comprehensive_report"
}
```

### Legacy API (DEPRECATED)
```python
# Old tier service API (still functional but deprecated)
POST /api/tiers/standard/analyze
{
    "opportunity_id": "OPP-2025-001"
}
```

---

## Historical Reference

For complete historical documentation, see archived files:
- `docs/archive/AI_INTELLIGENCE_TIER_SYSTEM.md`
- `docs/archive/TIER_SELECTION_GUIDE.md`
- `docs/archive/TIER_SERVICE_TECHNICAL_GUIDE.md`

---

## See Also

- [Two-Tool Architecture](TWO_TOOL_ARCHITECTURE.md) - Modern architecture overview
- [Migration History](MIGRATION_HISTORY.md) - Complete transformation timeline
- [Scoring Algorithms](../SCORING_ALGORITHMS.md) - Multi-dimensional scoring details
- [Tool 2 Documentation](../tools/deep-intelligence-tool/README.md) - Deep intelligence tool guide
- [Tool 20 Documentation](../tools/multi-dimensional-scorer-tool/README.md) - Scorer implementation
- [Tool 21 Documentation](../tools/report-generator-tool/README.md) - Report generation

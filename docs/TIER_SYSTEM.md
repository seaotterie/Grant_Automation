# Catalynx Tier System Documentation - TRUE COST MODEL

**Status**: ACTIVE - 2-Tier Value-Based Pricing (Network Intelligence Included)
**Date**: 2025-10-04
**Version**: 3.0 - True AI Cost Transparency + Network in Base Tier

---

## Overview

**Current System**: 2-tier value-based pricing with **network intelligence included** in base tier

- **ESSENTIALS** ($2.00): Complete analysis + network intelligence
- **PREMIUM** ($8.00): + Enhanced network pathways + policy analysis + strategic consulting

**Previous System** (DEPRECATED): 4 inflated tiers ($0.75 → $7.50 → $22 → $42)
- Pricing based on consultant rates, not actual AI costs
- Network analysis was $6.50 add-on
- Created decision paralysis with 4 tiers × 6 add-ons = 24 combinations

**Migration Rationale**: See [TIER_CONSOLIDATION_RATIONALE.md](TIER_CONSOLIDATION_RATIONALE.md) for complete analysis

---

## PRICING TRANSPARENCY: AI Costs vs User Pricing

### Actual AI API Costs (GPT-5 Models)

**GPT-5 Model Pricing**:
- `gpt-5-nano`: $0.25 per 1M input tokens, $2.00 per 1M output tokens
- `gpt-5-mini`: $0.50 per 1M input tokens, $4.00 per 1M output tokens
- `gpt-5`: $1.25 per 1M input tokens, $10.00 per 1M output tokens

**Typical Token Usage**:
- ESSENTIALS analysis: 5K input + 3K output (gpt-5-mini) = **$0.0145**
- Network intelligence: 4K input + 2K output (gpt-5-mini) = **$0.01**
- Premium enhancements: 7K input + 4K output (gpt-5) = **$0.055**
- Historical/Geographic: **$0** (algorithmic, no AI calls)

**True AI Costs**:
- **ESSENTIALS Tier**: $0.05 total AI cost
- **PREMIUM Tier**: $0.10 total AI cost

### User Pricing (40-80x Markup)

**ESSENTIALS**: $2.00 (40x markup from $0.05 AI cost)
**PREMIUM**: $8.00 (80x markup from $0.10 AI cost)

### Why the Markup? Platform Value Beyond AI 💡

**1. Data Infrastructure** ($X,XXX/month operating costs):
- IRS Business Master File (752K organizations)
- Form 990 database (671K filings)
- Form 990-PF database (235K foundations)
- USASpending.gov historical awards
- ProPublica API integration

**2. Tool Development & Maintenance**:
- 29 specialized 12-factor tools
- Continuous feature updates
- Bug fixes and support
- API infrastructure costs

**3. Strategic Intelligence Layer**:
- Multi-source data synthesis
- Pattern recognition algorithms
- Multi-dimensional scoring (Tool 20)
- Professional report generation (Tool 21)

**4. User Experience Platform**:
- Modern web interface (Alpine.js + Tailwind)
- Workflow orchestration engine
- Profile & opportunity management
- Export capabilities (PDF, Excel, PowerPoint)

**5. Opportunity Cost Savings**:
- **ESSENTIALS** replaces 4 hours consultant work ($200-400)
- **PREMIUM** replaces 12 hours consultant work ($600-1,200)
- Faster decision-making
- Higher quality analysis
- Scalable research

---

## Current 2-Tier System (Tool 2)

### Depth Parameters
```python
# 12-factor approach with true-cost pricing
from tools.deep_intelligence_tool import analyze_opportunity

result = await analyze_opportunity(
    opportunity_id="OPP-2025-001",
    depth="essentials",  # essentials | premium
    include_scoring=True,
    include_network=True  # Included in essentials!
)
```

### ESSENTIALS Tier ($2.00)

**AI Cost**: $0.05 | **User Price**: $2.00 | **Time**: 15-20 minutes

**Included Features**:
- ✅ Core 4-stage analysis (PLAN/ANALYZE/EXAMINE/APPROACH)
- ✅ Strategic fit assessment
- ✅ Financial viability analysis
- ✅ Operational readiness evaluation
- ✅ Risk assessment with mitigation strategies
- ✅ **Network intelligence & relationship mapping** 🆕
  - Board member profiling
  - Direct connection identification
  - Funder connection mapping
  - Top cultivation opportunities
- ✅ Historical funding intelligence (5-year patterns)
- ✅ Geographic distribution analysis
- ✅ Executive summary with action plan

**Network Intelligence in Base Tier** (Competitive Advantage):
- **AI Cost**: Only $0.01 (negligible)
- **Strategic Value**: High (70% of grants won through relationships)
- **Unique**: No competitor offers AI network analysis at $2

**Best For**:
- All opportunities (standard research)
- Relationship-driven funding
- Budget-conscious analysis
- Initial opportunity evaluation

### PREMIUM Tier ($8.00)

**AI Cost**: $0.10 | **User Price**: $8.00 | **Time**: 30-40 minutes

**Everything in ESSENTIALS +**:
- ✅ Enhanced network pathways (warm introduction mapping)
- ✅ Decision maker profiling & engagement strategies
- ✅ Network cluster analysis & relationship strength
- ✅ Policy context analysis & regulatory insights
- ✅ Strategic consulting recommendations
- ✅ Comprehensive 20+ page professional dossier

**Best For**:
- High-value opportunities ($100K+)
- Strategic partnerships
- Complex policy-driven funding
- Stakeholder presentations

---

## Legacy 4-Tier System (DEPRECATED - October 2025)

### Why 4 Tiers Failed

**Problems Identified**:
1. **Massive price jumps** created decision paralysis
   - $0.75 → $7.50 (10x jump)
   - $7.50 → $22 (3x jump)
   - $22 → $42 (2x jump)

2. **Pricing based on consultant rates**, not actual AI costs
   - QUICK $0.75 had $0.0047 AI cost (159x markup!)
   - COMPLETE $42 had $0.075 AI cost (560x markup!)

3. **Network analysis as $6.50 add-on** was confusing
   - Actual AI cost: $0.01
   - Users unsure if they needed it
   - Added decision complexity

4. **4 tiers × 6 add-ons = 24 combinations**
   - Decision fatigue
   - Support complexity
   - Lower conversions

### Original 4-Tier Pricing (Now Deprecated)

| Tier | Old Price | AI Cost | Markup | Status |
|------|-----------|---------|--------|--------|
| QUICK | $0.75 | $0.0047 | 159x | → ESSENTIALS |
| STANDARD | $7.50 | $0.0145 | 517x | → ESSENTIALS |
| ENHANCED | $22.00 | $0.02 | 1100x | → PREMIUM |
| COMPLETE | $42.00 | $0.075 | 560x | → PREMIUM |

### Migration Path (30-Day Deprecation)

**Automatic Mapping**:
```python
TIER_MIGRATION = {
    "quick": "essentials",      # $0.75 → $2.00
    "standard": "essentials",   # $7.50 → $2.00 (73% savings!)
    "enhanced": "premium",      # $22.00 → $8.00 (64% savings!)
    "complete": "premium"       # $42.00 → $8.00 (81% savings!)
}
```

**API Compatibility**:
- Old tier names supported for 30 days
- Auto-mapped to new tiers with deprecation warning
- Sunset date: November 4, 2025

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

# Human Gateway Specification
**Phase 4: Workflow Integration - Human-in-the-Loop Intelligence System**

## Overview

The Human Gateway is the critical interface between automated screening (Tool 1) and deep intelligence analysis (Tool 2). It enables human expertise to enhance AI-driven recommendations through manual review, web research, and strategic prioritization.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPPORTUNITY DISCOVERY                        │
│  (200+ opportunities from Grants.gov, Foundations, etc.)        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│               TOOL 1: OPPORTUNITY SCREENING                     │
│  - Fast Mode: 200 opps × $0.0004 = $0.08                       │
│  - Thorough Mode: 50 opps × $0.02 = $1.00                      │
│  - Output: 10-15 recommended opportunities (~$1-2 total)        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HUMAN GATEWAY (THIS LAYER)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Review screening results (scores, rationale)         │  │
│  │  2. Perform web scraping for additional context         │  │
│  │  3. Apply domain expertise and strategic judgment       │  │
│  │  4. Select 5-10 opportunities for deep analysis         │  │
│  │  5. Configure analysis depth per opportunity            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              TOOL 2: DEEP INTELLIGENCE ANALYSIS                 │
│  - Quick: 5 opps × $0.75 = $3.75                               │
│  - Standard: 3 opps × $7.50 = $22.50                           │
│  - Enhanced: 2 opps × $22.00 = $44.00                          │
│  - Complete: 1 opp × $42.00 = $42.00                           │
│  - Typical total: $50-100 for comprehensive intelligence       │
└─────────────────────────────────────────────────────────────────┘
```

## Human Gateway Features

### 1. Screening Results Dashboard

**Purpose**: Present AI screening results in a digestible, actionable format

**Features**:
- **Summary Statistics**:
  - Total opportunities screened
  - Passed threshold count
  - Recommended for deep analysis
  - Total cost and processing time

- **Opportunity List View**:
  - Sortable by: overall score, confidence, strategic fit, timing
  - Filterable by: score threshold, funder type, amount range
  - Quick view cards with key metrics

- **Individual Opportunity Cards**:
  ```
  ┌─────────────────────────────────────────────────────┐
  │ Community Health Initiative Grant                   │
  │ Health Foundation | $50K-$100K | Due: 2025-12-15   │
  ├─────────────────────────────────────────────────────┤
  │ Overall Score: 0.78 | Confidence: HIGH              │
  │                                                      │
  │ Strategic Fit:   ████████░░ 0.82                    │
  │ Eligibility:     ██████████ 0.95                    │
  │ Timing:          ████████░░ 0.75                    │
  │ Financial:       ███████░░░ 0.68                    │
  │ Competition:     ██████░░░░ 0.60                    │
  │                                                      │
  │ One-line: Excellent strategic alignment with         │
  │ strong eligibility match but moderate competition   │
  │                                                      │
  │ Strengths: Mission alignment, geographic fit        │
  │ Concerns: 60-day timeline, 15+ likely applicants    │
  │                                                      │
  │ [View Details] [Web Research] [Select for Analysis] │
  └─────────────────────────────────────────────────────┘
  ```

### 2. Web Research Enhancement

**Purpose**: Enable human researchers to augment AI analysis with web-scraped context

**Features**:
- **Quick Research Panel**:
  - Google search integration (opportunity + funder)
  - Funder website scraping
  - Past recipients research
  - News/press release monitoring

- **Research Notes**:
  - Rich text editor for notes
  - Attachment support (PDFs, links)
  - Tagging system (deadline, strategy, concern)

- **Context Enrichment**:
  - Add custom fields to opportunity record
  - Update funder relationship notes
  - Flag special considerations

**Example Workflow**:
```
1. User clicks "Web Research" on opportunity card
2. System opens research panel with:
   - Pre-populated Google search for funder
   - Funder website iframe
   - Notes editor
3. User adds findings:
   - "Funder prioritizes multi-year projects (website)"
   - "Last 3 grants went to orgs with <$2M budget"
   - "Board member connection: John Doe knows Jane Smith"
4. User saves research notes → attached to opportunity
5. Notes passed to deep intelligence tool for enhanced analysis
```

### 3. Strategic Selection Interface

**Purpose**: Apply human judgment to select opportunities for deep analysis

**Features**:
- **Selection Workflow**:
  - Drag-and-drop to priority order
  - Multi-select with batch actions
  - Quick filters (high confidence, urgent deadline)

- **Depth Configuration**:
  - Configure analysis depth per opportunity
  - Cost calculator showing total expected cost
  - Time estimate for batch processing

- **Batch Review**:
  ```
  Selected for Deep Analysis (8 opportunities)
  ┌─────────────────────────────────────────────────┐
  │ Priority  Opportunity              Depth   Cost │
  ├─────────────────────────────────────────────────┤
  │ 1         Community Health Init    STANDARD  $8 │
  │ 2         Youth Education Grant    QUICK    $1  │
  │ 3         Environmental Justice    ENHANCED $22 │
  │ 4         Arts & Culture Program   STANDARD  $8 │
  │ 5         STEM Education Fund      QUICK    $1  │
  │ 6         Community Development    COMPLETE $42 │
  │ 7         Public Health Research   STANDARD  $8 │
  │ 8         Workforce Development    QUICK    $1  │
  ├─────────────────────────────────────────────────┤
  │ TOTAL ESTIMATED COST:                     $91   │
  │ TOTAL PROCESSING TIME:                    3-5hr │
  │                                                  │
  │ [Adjust Selection] [Start Deep Analysis]        │
  └─────────────────────────────────────────────────┘
  ```

### 4. Decision Support Tools

**Purpose**: Help humans make informed selection decisions

**Features**:
- **Comparison View**:
  - Side-by-side opportunity comparison
  - Normalized score visualization
  - Pros/cons matrix

- **Risk Analysis**:
  - Timeline risk (days until deadline)
  - Capacity risk (resources required)
  - Competition risk (estimated applicants)

- **Portfolio View**:
  - Diversification analysis (funders, amounts, focus areas)
  - Timeline distribution (avoid clustering deadlines)
  - Total potential funding calculation

### 5. Workflow Execution Dashboard

**Purpose**: Monitor and manage deep intelligence workflow execution

**Features**:
- **Progress Tracking**:
  - Real-time workflow status per opportunity
  - Step-by-step execution log
  - Error handling and retry status

- **Results Management**:
  - Download intelligence reports (PDF/Excel/JSON)
  - View executive summaries
  - Access package outlines

- **Cost Tracking**:
  - Actual vs. estimated cost comparison
  - Cost breakdown by tool
  - Budget alerts

## Data Flow

### Input to Human Gateway (from Tool 1)
```json
{
  "screening_output": {
    "total_screened": 200,
    "passed_threshold": 15,
    "recommended_for_deep_analysis": ["OPP-001", "OPP-015", ...],
    "opportunity_scores": [
      {
        "opportunity_id": "OPP-001",
        "opportunity_title": "Community Health Initiative Grant",
        "overall_score": 0.78,
        "proceed_to_deep_analysis": true,
        "confidence_level": "high",
        "dimensional_scores": {...},
        "one_sentence_summary": "...",
        "key_strengths": [...],
        "key_concerns": [...],
        "recommended_actions": [...]
      }
    ],
    "screening_mode": "thorough",
    "processing_time_seconds": 145.2,
    "total_cost_usd": 1.08
  }
}
```

### Human Gateway Enhancement
```json
{
  "opportunity_id": "OPP-001",
  "human_research": {
    "web_research_notes": "Funder prioritizes multi-year projects...",
    "relationship_notes": "Board connection via John Doe",
    "strategic_notes": "Aligns with 2025-2027 strategic plan",
    "attachments": ["funder_guidelines.pdf", "board_roster.pdf"],
    "tags": ["high_priority", "board_connection", "multi_year"],
    "researcher_name": "Jane Smith",
    "research_date": "2025-09-30"
  },
  "selection_decision": {
    "selected_for_deep_analysis": true,
    "priority_rank": 1,
    "analysis_depth": "standard",
    "rationale": "High strategic fit with board connection",
    "estimated_cost": 7.50,
    "approved_by": "Grant Director"
  }
}
```

### Output from Human Gateway (to Tool 2)
```json
{
  "deep_intelligence_batch": [
    {
      "opportunity_id": "OPP-001",
      "opportunity_data": {...},
      "organization_context": {...},
      "analysis_config": {
        "depth": "standard",
        "focus_areas": ["board_networks", "historical_grants"],
        "user_notes": "Focus on multi-year sustainability",
        "export_format": "pdf"
      },
      "screening_score": 0.78,
      "human_research": {...}
    }
  ],
  "batch_metadata": {
    "batch_id": "BATCH-2025-001",
    "created_by": "Grant Director",
    "total_opportunities": 8,
    "estimated_total_cost": 91.00,
    "priority_order": true
  }
}
```

## Technical Implementation

### API Endpoints

```python
# Get screening results
GET /api/gateway/screening-results/{screening_batch_id}

# Add human research notes
POST /api/gateway/opportunities/{opportunity_id}/research
{
  "notes": "...",
  "attachments": [...],
  "tags": [...]
}

# Select opportunities for deep analysis
POST /api/gateway/select-for-analysis
{
  "opportunities": [
    {
      "opportunity_id": "OPP-001",
      "depth": "standard",
      "priority_rank": 1
    }
  ]
}

# Start deep intelligence workflow
POST /api/workflows/execute/deep-intelligence
{
  "opportunities": [...],
  "batch_metadata": {...}
}

# Monitor workflow progress
GET /api/workflows/status/{batch_id}

# Get completed intelligence reports
GET /api/workflows/results/{batch_id}
```

### Web Interface Components

**Frontend Stack**: Alpine.js + Tailwind CSS (existing)

**New Components**:
- `OpportunityCard.js` - Individual opportunity display
- `ResearchPanel.js` - Web research and notes interface
- `SelectionManager.js` - Batch selection and depth configuration
- `WorkflowMonitor.js` - Real-time workflow execution dashboard
- `ComparisonView.js` - Side-by-side opportunity comparison

**Existing Integration**:
- Reuse existing chart components for score visualization
- Leverage existing modal system for detailed views
- Extend existing export functionality for reports

## Success Metrics

**Efficiency**:
- 200 opportunities → 10-15 recommendations in <5 minutes (AI)
- Human review and selection: 30-60 minutes
- Deep analysis: 3-5 hours (automated)
- **Total time**: 4-6 hours vs. 40+ hours manual research

**Cost Effectiveness**:
- Stage 1 (Screening): $1-2
- Stage 2 (Deep Intelligence): $50-100
- **Total cost**: ~$50-100 vs. $2000+ consultant fees

**Quality**:
- AI identifies opportunities human might miss
- Human adds context AI cannot access
- Combined approach leverages strengths of both

## Phase 4 Deliverables

1. ✅ Workflow YAML definitions (opportunity_screening.yaml, deep_intelligence.yaml)
2. ⏳ Human Gateway Specification (this document)
3. ⏳ Tool loader implementation in workflow engine
4. ⏳ Web interface for human gateway
5. ⏳ API endpoints for workflow execution
6. ⏳ End-to-end testing and validation

---

**Status**: Phase 4 In Progress - Human Gateway Design Complete
**Next**: Implement tool loader and web interface

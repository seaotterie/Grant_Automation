# Tasks - <Grant_Automation>

## Today
- [ ] BUG-001

## Backlog

## Done


## Modifications
- Add a sorting carrot to the Headers in the scrollable tables to allow sorting to table place
- Add the ability for a non-profit to upload a list of Grantors, EINs Date, and Grant value.
- Fix the tabs TOP banners above the banner.  The Title and search bar area
- DISCOVER Nonprofits area, what is the IRS data refer to if not the 990 and 990-PF
- Tables
    - freeze headers
    - Filter & Sorting headers

## Comments
- While some non profits might not provide grants they may be of value from the BOD networking and Grantors Networking.



## New Features
Manual Inputs
- Websites like banks who manage foundations and trusts
- Donor lists similar to Schedule I but coming directly from the Profile and input manually
- Add a profile's grant package and docs outlining grant writing information, about us, past performance, metrics, non profit details to help with the APPROACH tab and grant writing
- Comments on View Details provided Promote and Demote reasoning
- Feedback loop where BOD and Grantor Networks feed back in to the DISCOVERY tab

## PLAN

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Ready to code?                                                                                                                  │
│                                                                                                                                 │
│ Here is Claude's plan:                                                                                                          │
│ ╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮ │
│ │ Proposed 5-Call Optimized Architecture                                                                                      │ │
│ │                                                                                                                             │ │
│ │ AI-Lite Stage: 2 Focused Calls                                                                                              │ │
│ │                                                                                                                             │ │
│ │ AI-Lite-1: Validation & Triage (~$0.0001/candidate, 50-100 tokens)                                                          │ │
│ │ - Primary: Confirm this is a real funding opportunity                                                                       │ │
│ │ - Secondary: Basic eligibility and geographic validation                                                                    │ │
│ │ - Output: Go/No-Go + Track assignment + Priority level                                                                      │ │
│ │ - Purpose: Filter out non-opportunities and mis-classified entries                                                          │ │
│ │                                                                                                                             │ │
│ │ AI-Lite-2: Strategic Scoring (~$0.0003/candidate, 150-200 tokens)                                                           │ │
│ │ - Primary: Mission alignment assessment (requires AI semantic matching)                                                     │ │
│ │ - Secondary: Strategic value judgment and priority ranking                                                                  │ │
│ │ - Output: Compatibility score + Strategic rationale + Action priority                                                       │ │
│ │ - Purpose: Strategic assessment for workflow continuation                                                                   │ │
│ │                                                                                                                             │ │
│ │ AI-Heavy Stage: 3 Specialized Calls                                                                                         │ │
│ │                                                                                                                             │ │
│ │ AI-Heavy-1: Research Bridge (~$0.05/candidate, 400-600 tokens) [NEW]                                                        │ │
│ │ - Website intelligence gathering (web scraping)                                                                             │ │
│ │ - Contact information extraction (web research)                                                                             │ │
│ │ - Basic fact extraction (document parsing)                                                                                  │ │
│ │ - Application process mapping (document analysis)                                                                           │ │
│ │ - Purpose: Data gathering and information extraction                                                                        │ │
│ │                                                                                                                             │ │
│ │ AI-Heavy-2: Analysis & Compliance (~$0.08/candidate, 600-800 tokens) [CURRENT HEAVY-A]                                      │ │
│ │ - 200-word executive summaries (complex writing)                                                                            │ │
│ │ - Eligibility deep dives (legal/compliance analysis)                                                                        │ │
│ │ - Detailed fact extraction (document parsing intensive)                                                                     │ │
│ │ - Requirements analysis (compliance assessment)                                                                             │ │
│ │ - Purpose: Detailed analysis and compliance evaluation                                                                      │ │
│ │                                                                                                                             │ │
│ │ AI-Heavy-3: Strategic Intelligence (~$0.12/candidate, 800+ tokens) [CURRENT HEAVY-B]                                        │ │
│ │ - Competitive analysis (market research complexity)                                                                         │ │
│ │ - Strategic dossier building (current functionality)                                                                        │ │
│ │ - Partnership assessment and positioning                                                                                    │ │
│ │ - Implementation planning and recommendations                                                                               │ │
│ │ - Purpose: Strategic intelligence and decision support                                                                      │ │
│ │                                                                                                                             │ │
│ │ Architecture Benefits:                                                                                                      │ │
│ │                                                                                                                             │ │
│ │ Cost Optimization:                                                                                                          │ │
│ │ - AI-Lite: Focuses on what AI does uniquely well (semantic reasoning)                                                       │ │
│ │ - Local Algorithms: Handle mathematical scoring (Government Scorer, Financial Scorer, Risk Assessor)                        │ │
│ │ - Progressive Investment: Expensive calls only for validated opportunities                                                  │ │
│ │                                                                                                                             │ │
│ │ Workflow Efficiency:                                                                                                        │ │
│ │ - Stage 1: Fast validation eliminates non-opportunities early                                                               │ │
│ │ - Stage 2: Strategic assessment guides resource allocation                                                                  │ │
│ │ - Stage 3: Research bridge gathers raw intelligence efficiently                                                             │ │
│ │ - Stage 4: Deep analysis provides compliance and requirement details                                                        │ │
│ │ - Stage 5: Strategic intelligence delivers implementation-ready insights                                                    │ │
│ │                                                                                                                             │ │
│ │ Specialization Benefits:                                                                                                    │ │
│ │ - Each call optimized for specific task types                                                                               │ │
│ │ - Reduces cognitive load on individual AI calls                                                                             │ │
│ │ - Enables parallel processing where appropriate                                                                             │ │
│ │ - Better error handling and retry strategies                                                                                │ │
│ │                                                                                                                             │ │
│ │ Integration Points:                                                                                                         │ │
│ │ - ANALYZE Tab: AI-Lite-1 + AI-Lite-2 + Local Scoring                                                                        │ │
│ │ - EXAMINE Tab: AI-Heavy-1 (Bridge) + AI-Heavy-2 (Analysis)                                                                  │ │
│ │ - APPROACH Tab: AI-Heavy-3 (Strategic Intelligence)                                                                         │ │
│ │                                                                                                                             │ │
│ │ Maximum 5 calls with clear specialization and progressive complexity                                                        │ │
│ ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ │
│   
│                   
## Phases
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Ready to code?                                                                                                                                  │
│                                                                                                                                                 │
│ Here is Claude's plan:                                                                                                                          │
│ ╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮ │
│ │ Catalynx Multi-Phase Rollout Plan: From Current to Enhanced Intelligence Platform                                                           │ │
│ │                                                                                                                                             │ │
│ │ PHASE 1: FOUNDATION INTEGRATION (Version 1.0)                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 2-3 Months | Budget: Low | ROI: High                                                                                              │ │
│ │ Focus: Activate Current AI-Lite & AI-Heavy Dual-Function Capabilities                                                                       │ │
│ │                                                                                                                                             │ │
│ │ AI-Lite Integration (ANALYZE Tab Enhancement)                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - Activate Research Mode: Implement website intelligence, document parsing, fact extraction                                                 │ │
│ │ - Research Report Generation: Enable grant team ready reports with supporting evidence                                                      │ │
│ │ - Enhanced Batch Processing: Optimize cost-effective research across 10-15 opportunities                                                    │ │
│ │ - Risk Assessment Enhancement: Implement 9 risk categories with mitigation strategies                                                       │ │
│ │ - Evidence-Based Scoring: Integrate research findings with compatibility scoring                                                            │ │
│ │                                                                                                                                             │ │
│ │ AI-Heavy Integration (EXAMINE Tab Enhancement)                                                                                              │ │
│ │                                                                                                                                             │ │
│ │ - Dossier Builder Activation: Enable comprehensive grant team decision documents                                                            │ │
│ │ - Relationship Intelligence: Activate board connection analysis and introduction strategies                                                 │ │
│ │ - Grant Application Intelligence: Full implementation of eligibility analysis and effort estimation                                         │ │
│ │ - Strategic Categorization: Enable 6-category opportunity classification system                                                             │ │
│ │ - Implementation Blueprints: Generate detailed roadmaps with resource requirements                                                          │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - 50% reduction in manual research time                                                                                                     │ │
│ │ - 75% improvement in decision quality through comprehensive dossiers                                                                        │ │
│ │ - 90% reduction in grant team prep time with ready-to-use research documents                                                                │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ PHASE 2: HUMAN-INTELLIGENCE INTEGRATION (Version 2.0)                                                                                       │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 4-6 Months | Budget: Medium | ROI: Very High                                                                                      │ │
│ │ Target: $250K+ Grant Opportunities                                                                                                          │ │
│ │                                                                                                                                             │ │
│ │ Manual Intelligence Upload Systems                                                                                                          │ │
│ │                                                                                                                                             │ │
│ │ - Profile POC Intelligence Input: Donor lists, board connections, insider knowledge                                                         │ │
│ │ - Grant Writing Package Integration: About us, past performance, metrics library                                                            │ │
│ │ - Promote/Demote Feedback System: Reasoning capture with continuous learning                                                                │ │
│ │ - Relationship Intelligence Database: Board member deep profiles, introduction history                                                      │ │
│ │                                                                                                                                             │ │
│ │ Enhanced Network Intelligence                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - Multi-Degree Relationship Mapping: 1st, 2nd, 3rd degree connection analysis                                                               │ │
│ │ - Introduction Pathway Optimization: Best route to decision-makers                                                                          │ │
│ │ - Relationship Maintenance System: CRM integration for relationship tracking                                                                │ │
│ │ - Board Member Intelligence Enhancement: Cross-board analysis, influence scoring                                                            │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - 3x increase in successful introductions through optimized pathways                                                                        │ │
│ │ - 60% improvement in relationship-building efficiency                                                                                       │ │
│ │ - 40% increase in grant success rate through insider intelligence                                                                           │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ PHASE 3: AUTOMATED INTELLIGENCE EXPANSION (Version 3.0)                                                                                     │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 6-9 Months | Budget: Medium-High | ROI: High                                                                                      │ │
│ │ Target: $500K+ Grant Opportunities                                                                                                          │ │
│ │                                                                                                                                             │ │
│ │ AI-Lite Web Intelligence Engine                                                                                                             │ │
│ │                                                                                                                                             │ │
│ │ - Automated Web Crawling: Funder website monitoring, staff directory extraction                                                             │ │
│ │ - Social Media Intelligence: LinkedIn, Twitter monitoring for decision-makers                                                               │ │
│ │ - News & Media Monitoring: Real-time funding announcements, leadership quotes                                                               │ │
│ │ - Public Database Mining: Enhanced 990 analysis, government database correlation                                                            │ │
│ │                                                                                                                                             │ │
│ │ AI-Heavy Predictive Intelligence                                                                                                            │ │
│ │                                                                                                                                             │ │
│ │ - Success Probability Modeling: Monte Carlo simulation, Bayesian probability updates                                                        │ │
│ │ - Competitive Intelligence: Game theory application, competitor strategy modeling                                                           │ │
│ │ - Scenario Analysis Engine: Best/worst case planning, market change impact                                                                  │ │
│ │ - Relationship Psychology Profiling: Decision-maker communication style analysis                                                            │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - 80% reduction in manual web research                                                                                                      │ │
│ │ - 2x improvement in competitive positioning                                                                                                 │ │
│ │ - 50% increase in optimal timing decisions                                                                                                  │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ PHASE 4: ADVANCED DOCUMENT & CONTENT INTELLIGENCE (Version 4.0)                                                                             │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 9-12 Months | Budget: High | ROI: Very High                                                                                       │ │
│ │ Target: $1M+ Grant Opportunities                                                                                                            │ │
│ │                                                                                                                                             │ │
│ │ Advanced Document Processing                                                                                                                │ │
│ │                                                                                                                                             │ │
│ │ - PDF Deep Analysis: Complex RFP structure extraction, evaluation rubric analysis                                                           │ │
│ │ - Historical Proposal Analysis: Pattern recognition in successful proposals                                                                 │ │
│ │ - Competitive Proposal Intelligence: Competitor approach analysis (when available)                                                          │ │
│ │ - Content Generation Engine: AI-powered proposal section generation                                                                         │ │
│ │                                                                                                                                             │ │
│ │ Institutional Knowledge Capture                                                                                                             │ │
│ │                                                                                                                                             │ │
│ │ - Grant Writing Intelligence Archive: Standard language library, evaluation methodologies                                                   │ │
│ │ - Success Stories Bank: Organized by outcome type with data visualizations                                                                  │ │
│ │ - Budget Templates: Automated budget generation by grant type/size                                                                          │ │
│ │ - Letters of Support Templates: Relationship-based template generation                                                                      │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - 70% reduction in proposal writing time                                                                                                    │ │
│ │ - 90% improvement in proposal quality consistency                                                                                           │ │
│ │ - 3x faster application development cycle                                                                                                   │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ PHASE 5: REAL-TIME & PREDICTIVE INTELLIGENCE (Version 5.0)                                                                                  │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 12-18 Months | Budget: High | ROI: Very High                                                                                      │ │
│ │ Target: $2M+ Grant Opportunities & Strategic Partnerships                                                                                   │ │
│ │                                                                                                                                             │ │
│ │ Live Intelligence Monitoring                                                                                                                │ │
│ │                                                                                                                                             │ │
│ │ - Real-Time Website Change Detection: Automatic deadline, priority change alerts                                                            │ │
│ │ - Funding Cycle Prediction: Pattern recognition for optimal application timing                                                              │ │
│ │ - Market Intelligence: Funding landscape shifts, emerging opportunity detection                                                             │ │
│ │ - Competitive Landscape Monitoring: New players, changing dynamics tracking                                                                 │ │
│ │                                                                                                                                             │ │
│ │ Advanced Predictive Systems                                                                                                                 │ │
│ │                                                                                                                                             │ │
│ │ - Funding Priority Trend Analysis: ML-based emerging priority identification                                                                │ │
│ │ - Success Factor Evolution: How success factors change over time                                                                            │ │
│ │ - Optimal Ask Amount Modeling: Data-driven funding request optimization                                                                     │ │
│ │ - Relationship Success Pattern Learning: AI learns from relationship outcomes                                                               │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - 90% improvement in timing optimization                                                                                                    │ │
│ │ - 2x increase in funding amount optimization                                                                                                │ │
│ │ - 50% reduction in missed opportunities through early detection                                                                             │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ PHASE 6: COMPREHENSIVE INTELLIGENCE ECOSYSTEM (Version 6.0)                                                                                 │ │
│ │                                                                                                                                             │ │
│ │ Timeline: 18-24 Months | Budget: Very High | ROI: Exceptional                                                                               │ │
│ │ Target: $5M+ Strategic Partnerships & Institutional Relationships                                                                           │ │
│ │                                                                                                                                             │ │
│ │ Cross-System Integration                                                                                                                    │ │
│ │                                                                                                                                             │ │
│ │ - CRM Integration: Full donor intelligence integration with relationship tracking                                                           │ │
│ │ - Financial System Integration: Real-time organizational health monitoring                                                                  │ │
│ │ - External Intelligence APIs: LinkedIn, Foundation Directory, Guidestar deep integration                                                    │ │
│ │ - Workflow Optimization: End-to-end process automation with quality prediction                                                              │ │
│ │                                                                                                                                             │ │
│ │ Specialized Intelligence Channels                                                                                                           │ │
│ │                                                                                                                                             │ │
│ │ - Policy Change Impact Analysis: How regulatory changes affect funding landscapes                                                           │ │
│ │ - Corporate Intelligence: Earnings correlation with CSR funding patterns                                                                    │ │
│ │ - Foundation Investment Performance: Endowment performance impact on giving                                                                 │ │
│ │ - Electoral Cycle Analysis: Political cycle impact on government funding                                                                    │ │
│ │                                                                                                                                             │ │
│ │ Expected ROI:                                                                                                                               │ │
│ │                                                                                                                                             │ │
│ │ - Complete automation of routine intelligence gathering                                                                                     │ │
│ │ - 5x improvement in strategic partnership identification                                                                                    │ │
│ │ - Institutional-level relationship building capability                                                                                      │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ IMPLEMENTATION STRATEGY BY GRANT VALUE TIER                                                                                                 │ │
│ │                                                                                                                                             │ │
│ │ Tier 1: $50K-$250K Grants (Phase 1-2)                                                                                                       │ │
│ │                                                                                                                                             │ │
│ │ - Focus: Efficiency and basic intelligence                                                                                                  │ │
│ │ - Tools: Enhanced AI-Lite research, basic dossier building                                                                                  │ │
│ │ - ROI: Process efficiency and time savings                                                                                                  │ │
│ │                                                                                                                                             │ │
│ │ Tier 2: $250K-$1M Grants (Phase 2-4)                                                                                                        │ │
│ │                                                                                                                                             │ │
│ │ - Focus: Strategic intelligence and relationship building                                                                                   │ │
│ │ - Tools: Advanced research, relationship intelligence, content generation                                                                   │ │
│ │ - ROI: Success rate improvement and competitive advantage                                                                                   │ │
│ │                                                                                                                                             │ │
│ │ Tier 3: $1M-$5M Grants (Phase 4-6)                                                                                                          │ │
│ │                                                                                                                                             │ │
│ │ - Focus: Comprehensive intelligence and strategic partnerships                                                                              │ │
│ │ - Tools: Full intelligence ecosystem, predictive modeling, institutional relationships                                                      │ │
│ │ - ROI: Transformational funding and long-term partnership development                                                                       │ │
│ │                                                                                                                                             │ │
│ │ Tier 4: $5M+ Strategic Partnerships (Phase 6+)                                                                                              │ │
│ │                                                                                                                                             │ │
│ │ - Focus: Institutional-level intelligence and ecosystem mapping                                                                             │ │
│ │ - Tools: Complete intelligence platform with cross-system integration                                                                       │ │
│ │ - ROI: Institutional transformation and market leadership                                                                                   │ │
│ │                                                                                                                                             │ │
│ │ ---                                                                                                                                         │ │
│ │ BUDGET & RESOURCE ALLOCATION                                                                                                                │ │
│ │                                                                                                                                             │ │
│ │ Phase 1 (Foundation): $50K-$100K                                                                                                            │ │
│ │                                                                                                                                             │ │
│ │ - Development: 60% (activate existing capabilities)                                                                                         │ │
│ │ - Integration: 30% (system integration work)                                                                                                │ │
│ │ - Testing: 10% (user acceptance testing)                                                                                                    │ │
│ │                                                                                                                                             │ │
│ │ Phase 2-3 (Enhancement): $200K-$400K per phase                                                                                              │ │
│ │                                                                                                                                             │ │
│ │ - Development: 50% (new intelligence capabilities)                                                                                          │ │
│ │ - Data Sources: 20% (API integrations, data licensing)                                                                                      │ │
│ │ - Infrastructure: 20% (enhanced processing capabilities)                                                                                    │ │
│ │ - Testing/Training: 10%                                                                                                                     │ │
│ │                                                                                                                                             │ │
│ │ Phase 4-6 (Advanced): $500K-$1M per phase                                                                                                   │ │
│ │                                                                                                                                             │ │
│ │ - Development: 40% (sophisticated AI/ML development)                                                                                        │ │
│ │ - Data Sources: 30% (premium data sources, specialized APIs)                                                                                │ │
│ │ - Infrastructure: 20% (enterprise-grade systems)                                                                                            │ │
│ │ - Specialized Expertise: 10% (domain experts, consultants)                                                                                  │ │
│ │                                                                                                                                             │ │
│ │ This phased approach ensures continuous ROI improvement while building toward a comprehensive intelligence platform that transforms grant   │ │
│ │ research from a manual process into a sophisticated, AI-powered strategic advantage.                                                        │ │
│ ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ │

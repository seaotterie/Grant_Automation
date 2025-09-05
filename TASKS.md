# Tasks - <Grant_Automation>


## Modifications
- Add a sorting carrot to the Headers in the scrollable tables to allow sorting to table place
- Add the ability for a non-profit to upload a list of Grantors, EINs Date, and Grant value.
- Fix the tabs TOP banners above the banner.  The Title and search bar area
- DISCOVER Nonprofits area, what is the IRS data refer to if not the 990 and 990-PF
- Tables
    - freeze headers
    - Filter & Sorting headers

- Requests for Proposals (RFPs) – Philanthropy News Digest  https://philanthropynewsdigest.org/rfps
 
This page offers a free, regularly updated list of request-for-proposal notices and awarded grants published daily, focused on U.S.-based philanthropic opportunities. Let me know if you’d like help navigating or filtering listings by category or region!

## Comments
- While some non profits might not provide grants they may be of value from the BOD networking and Grantors Networking.



## New Features
Manual Inputs
- Websites like banks who manage foundations and trusts
- Donor lists similar to Schedule I but coming directly from the Profile and input manually
- Add a profile's grant package and docs outlining grant writing information, about us, past performance, metrics, non profit details to help with the APPROACH tab and grant writing
- Comments on View Details provided Promote and Demote reasoning
- Feedback loop where BOD and Grantor Networks feed back in to the DISCOVERY tab

## API Costs
 🤖 AI API Costs Per Tier

  | Tier              | Total Price | AI API Cost | Platform/Infrastructure | Development/Margin |
  |-------------------|-------------|-------------|-------------------------|--------------------|
  | Current ($0.75)   | $0.75       | $0.31       | $0.19                   | $0.25              |
  | Standard ($7.50)  | $7.50       | $0.94       | $2.50                   | $4.06              |
  | Enhanced ($22.00) | $22.00      | $4.19       | $2.50                   | $15.31             |
  | Complete ($42.00) | $42.00      | $7.44       | $4.50                   | $30.06             |

  📊 AI API Cost Breakdown Details

  Current Tier ($0.31 API cost)

  - Tab processor integration and business packaging
  - Basic 4-stage AI analysis pipeline

  Standard Tier ($0.94 API cost)

  - All Current tier capabilities
  - Enhanced historical funding intelligence
  - Geographic pattern analysis
  - Temporal intelligence validation

  Enhanced Tier ($4.19 API cost)

  - All Standard tier capabilities
  - Complete RFP/NOFO document analysis (+$1.75)
  - Network intelligence and relationship mapping (+$0.75)
  - Decision maker profiling (+$0.69)

  Complete Tier ($7.44 API cost)

  - All Enhanced tier capabilities (+$4.19)
  - Advanced network mapping (+$1.25)
  - Policy analysis and regulatory intelligence (+$0.75)
  - Real-time monitoring system (+$0.50)
  - Strategic consulting integration (+$0.75)

## PLAN
│ Here is Claude's plan:                                                                                                                                                                                     │
│ ╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮ │
│ │ COMPREHENSIVE CATALYNX TESTING STRATEGY - TEST EVERYTHING                                                                                                                                              │ │
│ │                                                                                                                                                                                                        │ │
│ │ CONFIGURATION REQUIREMENTS - GPT-5 MODELS ONLY ✅                                                                                                                                                       │ │
│ │                                                                                                                                                                                                        │ │
│ │ - MAINTAIN GPT-5 Models: Keep existing GPT-5 configuration in .env and openai_service.py                                                                                                               │ │
│ │ - GPT-5 Benefits: Newer, more cost-effective, and available                                                                                                                                            │ │
│ │ - No Model Changes: Stop switching between GPT-4/GPT-5 - GPT-5 models are the correct choice                                                                                                           │ │
│ │ - Fix Simulation Mode: Address fallback issues WITHOUT changing model configuration                                                                                                                    │ │
│ │                                                                                                                                                                                                        │ │
│ │ COMPLETE SYSTEM ARCHITECTURE TO TEST:                                                                                                                                                                  │ │
│ │                                                                                                                                                                                                        │ │
│ │ 4-Stage AI Processing Pipeline (GPT-5 APIs):                                                                                                                                                           │ │
│ │                                                                                                                                                                                                        │ │
│ │ - PLAN: AI-Lite Unified Processor (src/processors/analysis/ai_lite_unified_processor.py)                                                                                                               │ │
│ │ - ANALYZE: AI-Heavy Light Analyzer (src/processors/analysis/ai_heavy_light_analyzer.py)                                                                                                                │ │
│ │ - EXAMINE: AI-Heavy Deep Researcher (src/processors/analysis/ai_heavy_deep_researcher.py)                                                                                                              │ │
│ │ - APPROACH: AI-Heavy Researcher (src/processors/analysis/ai_heavy_researcher.py)                                                                                                                       │ │
│ │                                                                                                                                                                                                        │ │
│ │ 18+ Additional Processors:                                                                                                                                                                             │ │
│ │                                                                                                                                                                                                        │ │
│ │ - Data Collection (6): ProPublica, Grants.gov, USASpending, Foundation Directory, VA State, BMF Filter                                                                                                 │ │
│ │ - Analysis (12+): Government Scorer, Financial Scorer, Board Network, Success Scorer, Risk Assessor, etc.                                                                                              │ │
│ │                                                                                                                                                                                                        │ │
│ │ COMPREHENSIVE 4-TIER TESTING APPROACH:                                                                                                                                                                 │ │
│ │                                                                                                                                                                                                        │ │
│ │ 1. EXECUTE ALL 4 INTELLIGENCE TIERS                                                                                                                                                                    │ │
│ │                                                                                                                                                                                                        │ │
│ │ Run complete analysis using Heroes Bridge + Fauquier Foundation data:                                                                                                                                  │ │
│ │                                                                                                                                                                                                        │ │
│ │ CURRENT Tier ($0.75)                                                                                                                                                                                   │ │
│ │                                                                                                                                                                                                        │ │
│ │ - 4-stage AI analysis + scoring                                                                                                                                                                        │ │
│ │ - Processing time: 5-10 minutes                                                                                                                                                                        │ │
│ │ - Capture: Token usage, processing time, data depth, output quality                                                                                                                                    │ │
│ │                                                                                                                                                                                                        │ │
│ │ STANDARD Tier ($7.50)                                                                                                                                                                                  │ │
│ │                                                                                                                                                                                                        │ │
│ │ - CURRENT + Historical funding analysis                                                                                                                                                                │ │
│ │ - Processing time: 15-20 minutes                                                                                                                                                                       │ │
│ │ - Capture: Additional token usage, enhanced analysis depth                                                                                                                                             │ │
│ │                                                                                                                                                                                                        │ │
│ │ ENHANCED Tier ($22.00)                                                                                                                                                                                 │ │
│ │                                                                                                                                                                                                        │ │
│ │ - STANDARD + Network intelligence + RFP analysis                                                                                                                                                       │ │
│ │ - Processing time: 30-45 minutes                                                                                                                                                                       │ │
│ │ - Capture: Advanced processing metrics, comprehensive intelligence depth                                                                                                                               │ │
│ │                                                                                                                                                                                                        │ │
│ │ COMPLETE Tier ($42.00)                                                                                                                                                                                 │ │
│ │                                                                                                                                                                                                        │ │
│ │ - Masters thesis level with comprehensive analysis                                                                                                                                                     │ │
│ │ - Processing time: 45-60 minutes                                                                                                                                                                       │ │
│ │ - Capture: Maximum token usage, professional deliverable quality                                                                                                                                       │ │
│ │                                                                                                                                                                                                        │ │
│ │ 2. COMPREHENSIVE DATA COLLECTION                                                                                                                                                                       │ │
│ │                                                                                                                                                                                                        │ │
│ │ For each tier, document:                                                                                                                                                                               │ │
│ │ - Token Usage: Actual GPT-5 consumption per AI processor                                                                                                                                               │ │
│ │ - Processing Time: Real execution duration per tier                                                                                                                                                    │ │
│ │ - Data Depth: Level of analysis detail and comprehensiveness                                                                                                                                           │ │
│ │ - Cost Validation: Actual API costs vs estimated tier pricing                                                                                                                                          │ │
│ │ - Output Quality: Professional depth and intelligence value                                                                                                                                            │ │
│ │ - Processor Execution: All 18+ processors completion status                                                                                                                                            │ │
│ │                                                                                                                                                                                                        │ │
│ │ 3. REAL DATA VALIDATION REQUIREMENTS                                                                                                                                                                   │ │
│ │                                                                                                                                                                                                        │ │
│ │ - Data Source: ONLY real ProPublica 990/990-PF data                                                                                                                                                    │ │
│ │   - Heroes Bridge (EIN 81-2827604): $504,030 revenue, Warrenton VA                                                                                                                                     │ │
│ │   - Fauquier Health Foundation (EIN 30-0219424): $249.9M assets, $11.67M distributions                                                                                                                 │ │
│ │ - API Authentication: Real GPT-5 API calls (NO simulation mode)                                                                                                                                        │ │
│ │ - Processing Verification: All processors execute with real data                                                                                                                                       │ │
│ │                                                                                                                                                                                                        │ │
│ │ 4. MANDATORY SUCCESS VALIDATION CHECKLIST                                                                                                                                                              │ │
│ │                                                                                                                                                                                                        │ │
│ │ - OpenAI GPT-5 API connects successfully                                                                                                                                                               │ │
│ │ - PLAN Tab: AI-Lite shows GPT-5 token usage > 0                                                                                                                                                        │ │
│ │ - ANALYZE Tab: AI-Heavy Light shows GPT-5 token usage > 0                                                                                                                                              │ │
│ │ - EXAMINE Tab: AI-Heavy Deep shows GPT-5 token usage > 0                                                                                                                                               │ │
│ │ - APPROACH Tab: AI-Heavy Researcher shows GPT-5 token usage > 0                                                                                                                                        │ │
│ │ - All 18+ processors execute successfully                                                                                                                                                              │ │
│ │ - All 4 tiers (CURRENT/STANDARD/ENHANCED/COMPLETE) complete                                                                                                                                            │ │
│ │ - Real Heroes Bridge + Fauquier data used throughout                                                                                                                                                   │ │
│ │ - Actual cost tracking for each tier                                                                                                                                                                   │ │
│ │ - NO "simulation mode" messages in any output                                                                                                                                                          │ │
│ │                                                                                                                                                                                                        │ │
│ │ 5. FINAL DELIVERABLE REQUIREMENTS                                                                                                                                                                      │ │
│ │                                                                                                                                                                                                        │ │
│ │ - Masters Thesis Dossier: Use COMPLETE Tier results                                                                                                                                                    │ │
│ │ - Template: heroes_bridge_fauquier_complete_masters_dossier.html (5-section structure)                                                                                                                 │ │
│ │ - Section 4 Enhancement: Include comparative analysis of all 4 tiers                                                                                                                                   │ │
│ │ - Token Analysis: Document GPT-5 usage and data depth for each tier                                                                                                                                    │ │
│ │ - Professional Quality: Executive summary + comprehensive technical analysis                                                                                                                           │ │
│ │                                                                                                                                                                                                        │ │
│ │ 6. COMPARATIVE TIER ANALYSIS OUTPUT                                                                                                                                                                    │ │
│ │                                                                                                                                                                                                        │ │
│ │ Generate detailed comparison showing:                                                                                                                                                                  │ │
│ │ - Processing Progression: How analysis depth increases across tiers                                                                                                                                    │ │
│ │ - Token Utilization: GPT-5 usage scaling from CURRENT to COMPLETE                                                                                                                                      │ │
│ │ - Value Proposition: Cost vs intelligence depth for each tier                                                                                                                                          │ │
│ │ - Business Applications: When to use each tier based on requirements                                                                                                                                   │ │
│ │                                                                                                                                                                                                        │ │
│ │ This comprehensive strategy tests EVERYTHING - all processors, all AI stages, all intelligence tiers, using GPT-5 models with real data to produce the ultimate masters thesis dossier with complete   │ │
│ │ tier comparison analysis.    
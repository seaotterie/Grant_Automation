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
Comprehensive AI-Lite Integration Plan: Security + Cost Controls + Integration                                                                               │ │
│ │                                                                                                                                                              │ │
│ │ Overview                                                                                                                                                     │ │
│ │                                                                                                                                                              │ │
│ │ Complete implementation of the first AI-Lite integration with enhanced security features and advanced cost controls, incorporating ChatGPT's recommendations │ │
│ │  with the existing robust Catalynx infrastructure.                                                                                                           │ │
│ │                                                                                                                                                              │ │
│ │ Phase 1: Enhanced Security Setup (Priority 1)                                                                                                                │ │
│ │                                                                                                                                                              │ │
│ │ 1.1 Master Security Foundation                                                                                                                               │ │
│ │                                                                                                                                                              │ │
│ │ - Set up encrypted API key management via python setup_auth.py api-keys setup                                                                                │ │
│ │ - Add OpenAI API key securely with format validation (sk-*, 48+ chars)                                                                                       │ │
│ │ - Configure master password protection with PBKDF2 encryption (100K iterations)                                                                              │ │
│ │ - Verify secure storage at ~/.grant_research/api_keys.enc with 0o600 permissions                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ 1.2 Enhanced Security Features (ChatGPT Suggestions)                                                                                                         │ │
│ │                                                                                                                                                              │ │
│ │ - API Key Rotation System: Extend APIKeyManager with expiry tracking and 30-day rotation alerts                                                              │ │
│ │ - Audit Logging Enhancement: Add --audit flag to CostTracker for encrypted operation hashes                                                                  │ │
│ │ - Multiple Service Aliases: Expand AIService enum for Claude, Gemini, Groq with alias support                                                                │ │
│ │ - Security Monitoring: Enhanced logging of authentication attempts and key access patterns                                                                   │ │
│ │                                                                                                                                                              │ │
│ │ Phase 2: Advanced Cost Control System (Priority 1)                                                                                                           │ │
│ │                                                                                                                                                              │ │
│ │ 2.1 Enhanced Cost Infrastructure                                                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ - Model Granularity: Expand TOKEN_COSTS for GPT-4o-mini, GPT-4o, GPT-3.5-turbo variants                                                                      │ │
│ │ - Dynamic Pricing: Service-specific token costs with real-time rate updates                                                                                  │ │
│ │ - Tier-Based Budgeting: Category budgets by model performance tier (economy/standard/premium)                                                                │ │
│ │                                                                                                                                                              │ │
│ │ 2.2 Smart Cost Management (ChatGPT Suggestions)                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ - Scenario Planner: Dry-run cost estimates for "50 candidates GPT-3.5 vs GPT-4o comparison"                                                                  │ │
│ │ - Billing Export: JSON/CSV downloads with model, task type, batch ID breakdowns                                                                              │ │
│ │ - Cost Optimization: Automatic model selection based on budget constraints and requirements                                                                  │ │
│ │                                                                                                                                                              │ │
│ │ 2.3 Conservative Budget Configuration                                                                                                                        │ │
│ │                                                                                                                                                              │ │
│ │ - Initial Budget: $5.00 total with category allocation                                                                                                       │ │
│ │   - AI Analysis: $3.00 (60% for AI-Lite operations)                                                                                                          │ │
│ │   - Testing/Buffer: $2.00 (40% safety margin)                                                                                                                │ │
│ │ - Alert Thresholds: Warning 75% ($3.75), Critical 90% ($4.50)                                                                                                │ │
│ │ - Per-Operation Limits: $0.01 max per request, $1.00 daily limit                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ Phase 3: AI-Lite Core Integration (Priority 2)                                                                                                               │ │
│ │                                                                                                                                                              │ │
│ │ 3.1 API Endpoint Implementation                                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ - Register AI Processing Router in main FastAPI app (src/web/routers/ai_processing.py)                                                                       │ │
│ │ - Implement Missing Endpoint: /api/profiles/{profile_id}/analyze/ai-lite (currently returns 404)                                                             │ │
│ │ - Connect AI Service Manager: Use existing AILiteScorer and request transformation                                                                           │ │
│ │ - Enable WebSocket Progress: Real-time monitoring for AI operations                                                                                          │ │
│ │                                                                                                                                                              │ │
│ │ 3.2 ANALYZE Tab Frontend Integration                                                                                                                         │ │
│ │                                                                                                                                                              │ │
│ │ - Connect AI-Lite Button: Link frontend to functional backend endpoint                                                                                       │ │
│ │ - Data Flow Mapping: Profile data → AILiteRequest → AILiteBatchResult → UI display                                                                           │ │
│ │ - Result Display Enhancement: Format AI analysis results with research mode toggle                                                                           │ │
│ │ - Error Handling: User-friendly messages for budget limits and failures                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ 3.3 Dual-Mode Operation                                                                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ - Scoring Mode: Cost-effective compatibility analysis ($0.0001/candidate)                                                                                    │ │
│ │ - Research Mode: Comprehensive research reports ($0.0008/candidate)                                                                                          │ │
│ │ - Mode Selection: Dynamic switching based on budget and requirements                                                                                         │ │
│ │ - Quality Validation: Compare outputs between modes for value assessment                                                                                     │ │
│ │                                                                                                                                                              │ │
│ │ Phase 4: Testing & Validation (Priority 2)                                                                                                                   │ │
│ │                                                                                                                                                              │ │
│ │ 4.1 Security Testing                                                                                                                                         │ │
│ │                                                                                                                                                              │ │
│ │ - API Key Security: Verify encrypted storage and access controls                                                                                             │ │
│ │ - Audit Trail Validation: Test encrypted operation logging                                                                                                   │ │
│ │ - Multiple Service Support: Test service aliases and key management                                                                                          │ │
│ │ - Rotation Testing: Simulate key rotation and expiry scenarios                                                                                               │ │
│ │                                                                                                                                                              │ │
│ │ 4.2 Cost Control Validation                                                                                                                                  │ │
│ │                                                                                                                                                              │ │
│ │ - Budget Enforcement: Test automatic blocking when limits exceeded                                                                                           │ │
│ │ - Scenario Planning: Validate dry-run cost estimates for multiple models                                                                                     │ │
│ │ - Export Functionality: Test billing data downloads (JSON/CSV)                                                                                               │ │
│ │ - Alert System: Verify threshold warnings and critical alerts                                                                                                │ │
│ │                                                                                                                                                              │ │
│ │ 4.3 AI-Lite Integration Testing                                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ - Endpoint Functionality: Fix 404 errors, ensure 200 responses with analysis results                                                                         │ │
│ │ - End-to-End Workflow: DISCOVER → ANALYZE → AI-Lite → Results display                                                                                        │ │
│ │ - Performance Testing: Batch processing with 1, 5, 10, 20 candidates                                                                                         │ │
│ │ - Cost Accuracy: Compare estimated vs actual costs across models                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ Phase 5: Production Readiness (Priority 3)                                                                                                                   │ │
│ │                                                                                                                                                              │ │
│ │ 5.1 Advanced Features Activation                                                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ - Multi-Model Support: Enable GPT-3.5, GPT-4o-mini, GPT-4o selection                                                                                         │ │
│ │ - Research Mode Enhancement: Full website intelligence and competitive analysis                                                                              │ │
│ │ - Export Integration: Professional reports with AI analysis inclusion                                                                                        │ │
│ │ - Mobile Optimization: Ensure AI-Lite works on mobile interface                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ 5.2 Monitoring & Analytics                                                                                                                                   │ │
│ │                                                                                                                                                              │ │
│ │ - Cost Analytics Dashboard: Real-time budget utilization and spending patterns                                                                               │ │
│ │ - Performance Metrics: Response times, success rates, model comparison                                                                                       │ │
│ │ - Usage Analytics: Track which modes and models provide best value                                                                                           │ │
│ │ - Audit Reports: Monthly security and cost control summaries                                                                                                 │ │
│ │                                                                                                                                                              │ │
│ │ Implementation Timeline                                                                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ Week 1: Security & Cost Foundation (8-12 hours)                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ - Days 1-2: Enhanced security setup with audit logging                                                                                                       │ │
│ │ - Days 3-4: Advanced cost controls with scenario planning                                                                                                    │ │
│ │ - Day 5: Billing export and multi-model pricing                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ Week 2: AI-Lite Core Integration (12-16 hours)                                                                                                               │ │
│ │                                                                                                                                                              │ │
│ │ - Days 1-3: API endpoint implementation and router registration                                                                                              │ │
│ │ - Days 4-5: Frontend integration and WebSocket progress                                                                                                      │ │
│ │ - Weekend: Testing and bug fixes                                                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ Week 3: Testing & Production Ready (8-10 hours)                                                                                                              │ │
│ │                                                                                                                                                              │ │
│ │ - Days 1-2: Comprehensive testing across all components                                                                                                      │ │
│ │ - Days 3-4: Performance optimization and edge case handling                                                                                                  │ │
│ │ - Day 5: Documentation and deployment preparation                                                                                                            │ │
│ │                                                                                                                                                              │ │
│ │ Success Criteria                                                                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ ✅ Security Achievements                                                                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ - API keys encrypted with master password protection                                                                                                         │ │
│ │ - Audit logging operational with encrypted hashes                                                                                                            │ │
│ │ - Multi-service support with alias management                                                                                                                │ │
│ │ - 30-day key rotation alerts configured                                                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ ✅ Cost Control Achievements                                                                                                                                  │ │
│ │                                                                                                                                                              │ │
│ │ - Dynamic model pricing with scenario planning                                                                                                               │ │
│ │ - Budget enforcement preventing overruns                                                                                                                     │ │
│ │ - Billing exports (JSON/CSV) functional                                                                                                                      │ │
│ │ - Real-time cost tracking with variance analysis                                                                                                             │ │
│ │                                                                                                                                                              │ │
│ │ ✅ Integration Achievements                                                                                                                                   │ │
│ │                                                                                                                                                              │ │
│ │ - /api/profiles/{profile_id}/analyze/ai-lite returns 200 with results                                                                                        │ │
│ │ - ANALYZE tab AI-Lite button functional end-to-end                                                                                                           │ │
│ │ - Dual-mode operation (scoring + research) working                                                                                                           │ │
│ │ - WebSocket progress monitoring operational                                                                                                                  │ │
│ │                                                                                                                                                              │ │
│ │ Expected Costs (Conservative Estimates)                                                                                                                      │ │
│ │                                                                                                                                                              │ │
│ │ Testing Phase Budget: $2.00                                                                                                                                  │ │
│ │                                                                                                                                                              │ │
│ │ - Security Testing: $0.10 (key validation, audit logs)                                                                                                       │ │
│ │ - Cost Control Testing: $0.40 (scenario planning, export validation)                                                                                         │ │
│ │ - AI-Lite Testing: $1.50 (10-20 candidates across multiple models)                                                                                           │ │
│ │                                                                                                                                                              │ │
│ │ Production Usage Scenarios (Daily)                                                                                                                           │ │
│ │                                                                                                                                                              │ │
│ │ - Light Usage: 20 candidates = $0.002-0.016                                                                                                                  │ │
│ │ - Moderate Usage: 50 candidates = $0.005-0.040                                                                                                               │ │
│ │ - Heavy Usage: 100 candidates = $0.010-0.080                                                                                                                 │ │
│ │                                                                                                                                                              │ │
│ │ This comprehensive plan integrates ChatGPT's excellent security and cost enhancement suggestions with the robust existing Catalynx infrastructure,           │ │
│ │ delivering a production-ready AI-Lite system with enterprise-grade security and granular cost controls.                                                      │ │
│ ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ │
│ 
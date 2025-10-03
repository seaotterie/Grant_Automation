# START HERE V4 - Phase 9 Week 4+ Planning & Gap Analysis

**Date**: 2025-10-03
**Session**: Fresh Context Window #6
**Phase**: Phase 9 Weeks 2-3 COMPLETE - Week 4+ Planning
**Progress**: 100% Phase 8 | 40% Phase 9 (frontend core complete)

---

## EXECUTIVE SUMMARY

**Phase 9 Weeks 2-3 Achievements**:
- ✅ Modular architecture complete (5 modules, 1,920 lines)
- ✅ Navigation simplified (8 stages → 3 stages)
- ✅ All 3 stage UIs built and functional
- ✅ Module integration complete (pragmatic, additive approach)
- ✅ V2 API integration ready (profiles, discovery, tools)

**Current System State**:
- **Backend**: 23 tools operational, 6 v2 profile APIs, unified tool API
- **Frontend**: 3-stage modular architecture with event-driven communication
- **Database**: 626K+ Form 990, 220K+ Form 990-PF, 700K+ BMF organizations
- **Code Status**: 31,413 lines (10,163 HTML + 19,143 JS + modules)

**What's Ready**:
- Profile list view with search/sort/pagination
- Discovery execution with track selection
- Screening workflow with Tool 10 integration
- Intelligence analysis with Tool 2 (4 depths)
- Report/export/package actions

**What's Missing** (Gap Analysis Below):
- Modal forms (create/edit/delete profiles)
- Advanced BMF filter configuration
- Network visualization dashboards
- Detailed opportunity analysis views
- Report customization options
- Analytics dashboards
- Settings management UI
- Bulk operations interface
- Integration testing
- Legacy code cleanup

---

## COMPLETED WORK SUMMARY

### Phase 9 Week 2-3 Deliverables

#### 1. Five Modules Created (1,920 lines)

**state-module.js** (89 lines):
- Centralized navigation state (activeStage, previousStage)
- Profile state (selectedProfile, profiles list)
- Screening state (discoveryResults, screeningResults)
- Intelligence state (intelligenceResults)
- Event-driven stage switching ($dispatch)

**shared-module.js** (281 lines):
- Dark mode management with persistence
- Notification system (toast notifications)
- Formatting utilities (currency, date, number, percent, EIN)
- Validation functions (EIN, email, URL)
- Utilities (clipboard, download, debounce, clone, generateId)

**profiles-module.js** (465 lines):
- Complete V2 Profile API integration
- CRUD operations (create, read, update, delete)
- Pagination, search, sorting
- Modal management (create/edit/delete modals)
- Analytics and quality scoring
- Export functionality

**screening-module.js** (529 lines):
- V2 Discovery API integration
- Track-based discovery (nonprofit, federal, BMF)
- Tool 10 opportunity screening (fast/thorough modes)
- Selection workflow for intelligence
- Results management and filtering

**intelligence-module.js** (556 lines):
- Tool 2 deep intelligence (4 depth levels)
- Tool 21 report generation (4 templates)
- Tool 18 data export (JSON, CSV, Excel, PDF)
- Tool 19 grant package assembly
- Cost tracking and progress monitoring

#### 2. Navigation Simplified

**Before**: 8 Workflow Stages
1. WELCOME - Introduction and profile selection
2. PROFILER - Profile creation and editing
3. DISCOVER - Opportunity discovery (4 tracks)
4. PLAN - Fast screening (200 → 50)
5. ANALYZE - Thorough screening (50 → 10-15)
6. EXAMINE - Deep intelligence analysis
7. APPROACH - Report generation and packages
8. SETTINGS - System configuration

**After**: 3 Consolidated Stages
1. **PROFILES** - Replaces WELCOME, PROFILER, SETTINGS
2. **SCREENING** - Replaces DISCOVER, PLAN, ANALYZE
3. **INTELLIGENCE** - Replaces EXAMINE, APPROACH

**Benefits**:
- 62.5% reduction in navigation complexity
- Clearer user journey
- Better alignment with actual workflow
- Preserved legacy navigation for reference

#### 3. Stage UIs Built

**PROFILES Stage** (lines 469-568 in index.html):
- Profile list grid with search
- Sort by name/date/quality
- Pagination controls
- Loading/empty/error states
- "New Profile" button
- Integration with profilesModule()

**SCREENING Stage** (lines 570-720 in index.html):
- Discovery track selection (nonprofit/federal/BMF)
- Screening mode selection (fast/thorough)
- Execute discovery button
- Results display with pagination
- Screening results with scores
- Selection checkboxes
- "Proceed to Intelligence" button

**INTELLIGENCE Stage** (lines 722-845 in index.html):
- Analysis depth selection (4 tiers with pricing)
- Selected opportunities display
- "Analyze All" button with progress
- Results display with completion status
- Report/Export/Package action buttons
- Summary dashboard with total cost/time

#### 4. Module Integration (app.js)

**Pragmatic Approach** (lines 639-801):
- Added initModules() function (no code deletion)
- Module instance variables added
- Enhanced switchStage() function
- Backward compatibility maintained
- Zero breaking changes

**Integration Pattern**:
```javascript
// Initialize modules
this.stateModule = stateModule();
this.sharedModule = sharedModule();
this.profilesModule = profilesModule();
this.screeningModule = screeningModule();
this.intelligenceModule = intelligenceModule();

// Event-driven communication
this.$dispatch('stage-changed', { stage });
```

---

## GAP ANALYSIS: MISSING FEATURES

### Category 1: Modal Forms (HIGH PRIORITY)

**What's Missing**:
1. **Create Profile Modal**
   - EIN input with validation
   - Manual profile form fields
   - Tool 25 web scraping option
   - Organization name, mission, location
   - Submit/cancel buttons

2. **Edit Profile Modal**
   - Load existing profile data
   - Editable fields for all profile properties
   - Save changes with optimistic updates
   - Validation and error handling

3. **Delete Profile Modal**
   - Confirmation dialog
   - Warning about data loss
   - Cascade delete options (opportunities, reports)
   - Final delete action

4. **Advanced Filters Modal** (Discovery)
   - NTEE code multi-select (200+ codes)
   - Geographic filters (state, county, city, radius)
   - Financial thresholds (revenue, assets, grants)
   - Organization type filters
   - Save filter presets

**Legacy Reference**:
- `app.js` lines 18723-18874: Modal system references
- Modal management scattered across stages
- No centralized modal component

**Implementation Plan**:
- Create `modal-component.js` reusable modal system
- Add modal HTML templates to index.html
- Wire up to profiles/screening modules
- Use Alpine.js x-show for display

---

### Category 2: BMF Discovery Configuration (MEDIUM PRIORITY)

**What's Missing**:
1. **NTEE Code Selector**
   - Searchable multi-select dropdown
   - Category grouping (A-Z, 26 categories)
   - Common presets (education, health, human services)
   - Selected count display

2. **Geographic Configuration**
   - State multi-select
   - County selection (conditional)
   - City search and select
   - Radius-based search (ZIP + miles)
   - Map visualization (optional)

3. **Financial Filters**
   - Revenue range sliders
   - Asset range sliders
   - Grant amount filters
   - Year-over-year growth filters
   - Financial health indicators

4. **Organization Type Filters**
   - Nonprofit vs Foundation toggle
   - 501(c)(3) vs other classifications
   - Public charity vs private foundation
   - Exclude types (schools, churches, etc.)

**Legacy Reference**:
- `app.js` lines 11116-11280: BMF filter implementation
- `bmfFilterInProgress` state variable
- `executeBMFFilter()` function
- Quick filter vs advanced filter patterns

**Implementation Plan**:
- Enhance screening-module.js with filter config
- Create filter builder UI component
- Integrate with Tool 17 (BMF Discovery)
- Add filter preset save/load

---

### Category 3: Visualization & Analytics (MEDIUM PRIORITY)

**What's Missing**:
1. **Network Visualization** (from ANALYZE stage)
   - Board member network graphs
   - Shared connections display
   - Centrality metrics visualization
   - Interactive network exploration
   - Export network maps

2. **Scoring Visualizations**
   - Multi-dimensional scoring radar charts
   - Comparative bar charts (opportunities)
   - Quality score trends over time
   - Dimensional breakdown displays
   - Boost factor indicators

3. **Analytics Dashboards**
   - Processing volume charts
   - Success rate metrics
   - Cost tracking over time
   - Opportunity pipeline visualization
   - Profile quality distribution

4. **Financial Charts**
   - Revenue/expense trends
   - Grant distribution analysis
   - Asset allocation pie charts
   - Comparative financial metrics
   - Foundation payout ratios

**Legacy Reference**:
- `app.js` lines 9603-9652: Network visualization functions
- `toggleNetworkVisualizations()`, `initializeNetworkCharts()`
- `app.js` lines 2410-2412: Chart state variables
- `app.js` lines 7297: Scoring visualization functions
- Chart.js integration scattered throughout

**Implementation Plan**:
- Create `visualization-module.js`
- Integrate Chart.js library (already in index.html)
- Add dashboard components to intelligence stage
- Connect to Tool 12 (Network Intelligence) outputs
- Connect to Tool 20 (Multi-Dimensional Scorer) outputs

---

### Category 4: Detailed Analysis Views (MEDIUM PRIORITY)

**What's Missing**:
1. **Opportunity Detail View**
   - Full opportunity information display
   - Tabbed interface (overview, financials, network, risk)
   - Historical funding patterns
   - Related opportunities
   - Notes and annotations

2. **Profile Analytics View**
   - Quality score breakdown
   - Enhancement recommendations
   - Data completeness meters
   - Improvement suggestions
   - Historical changes tracking

3. **Comparative Analysis**
   - Side-by-side opportunity comparison
   - Scoring dimension comparisons
   - Financial metric comparisons
   - Risk assessment comparisons
   - Decision matrix display

4. **Intelligence Report Viewer**
   - In-app HTML report rendering
   - Interactive table of contents
   - Section navigation
   - Print/export options
   - Annotation capabilities

**Legacy Reference**:
- Detailed views scattered across EXAMINE and APPROACH stages
- No single detailed view component
- Information spread across multiple modals

**Implementation Plan**:
- Create detail view components
- Add tabbed interface patterns
- Integrate with intelligence-module.js
- Build comparison tools

---

### Category 5: Report & Export Customization (LOW PRIORITY)

**What's Missing**:
1. **Report Template Selection**
   - Visual template previews
   - Template customization options
   - Section inclusion toggles
   - Branding/logo upload
   - Header/footer customization

2. **Export Format Options**
   - Format-specific options (Excel sheets, PDF layout)
   - Field selection for CSV exports
   - Batch export configuration
   - Scheduled exports
   - Email delivery options

3. **Package Assembly Interface**
   - Document checklist builder
   - Attachment management
   - Cover letter generator
   - Submission timeline planner
   - Package status tracking

**Legacy Reference**:
- Basic export functionality exists
- No customization UI
- Template selection hard-coded

**Implementation Plan**:
- Enhance intelligence-module.js
- Add template configuration UI
- Connect to Tool 21 (Report Generator)
- Connect to Tool 18 (Data Export)
- Connect to Tool 19 (Grant Package Generator)

---

### Category 6: Settings & Configuration (LOW PRIORITY)

**What's Missing**:
1. **System Settings**
   - Dark mode toggle (exists in shared-module.js)
   - Notification preferences
   - Auto-save configuration
   - Default view settings
   - Keyboard shortcut customization

2. **API Configuration**
   - API key management (OpenAI, ProPublica)
   - Cost limits and budgets
   - Rate limiting settings
   - Webhook configuration
   - Integration settings

3. **User Preferences**
   - Default filters and presets
   - Favorite NTEE codes
   - Saved searches
   - Column visibility preferences
   - Sort preferences

**Legacy Reference**:
- SETTINGS stage (8th original stage)
- Scattered settings across app.js
- No centralized settings UI

**Implementation Plan**:
- Create settings-module.js
- Build settings UI (modal or dedicated stage)
- Integrate with shared-module.js
- Add persistence (localStorage)

---

### Category 7: Bulk Operations (LOW PRIORITY)

**What's Missing**:
1. **Bulk Profile Operations**
   - Multi-select profiles
   - Batch delete
   - Batch export
   - Batch quality scoring
   - Batch enhancement (Tool 25 + Tool 2)

2. **Bulk Opportunity Operations**
   - Multi-select opportunities
   - Batch screening
   - Batch intelligence analysis
   - Batch report generation
   - Batch package creation

3. **Batch Processing UI**
   - Progress indicators for batch operations
   - Cancel/pause controls
   - Error handling for partial failures
   - Results summary display
   - Retry failed items

**Legacy Reference**:
- `app.js` lines 17814: `addDesktopBulkSelection` function
- Bulk selection system exists
- Limited bulk operation UI

**Implementation Plan**:
- Enhance profiles-module.js with bulk operations
- Enhance screening-module.js with batch screening
- Enhance intelligence-module.js with batch analysis
- Add bulk operation controls to UIs

---

## REMAINING FEATURES INVENTORY

### High Priority (Week 4-5)
1. ✅ Modal forms (create/edit/delete profiles) - **ESSENTIAL**
2. ✅ Advanced BMF filter configuration - **ESSENTIAL**
3. ✅ Basic network visualization - **IMPORTANT**
4. ✅ Opportunity detail views - **IMPORTANT**

### Medium Priority (Week 6-7)
5. ⏳ Analytics dashboards (Chart.js integration)
6. ⏳ Scoring visualizations (radar charts, comparisons)
7. ⏳ Profile analytics view (quality breakdown)
8. ⏳ Financial charts (revenue/expense trends)

### Low Priority (Week 8+)
9. ⏳ Report template customization
10. ⏳ Export format options
11. ⏳ Settings management UI
12. ⏳ Bulk operations interface
13. ⏳ Package assembly interface

---

## INTEGRATION TESTING NEEDS

### Test Scenarios (Not Yet Implemented)

**Profile Workflow**:
1. Create profile via EIN (Tool 25 integration)
2. Create profile manually
3. Edit profile and save changes
4. Delete profile with confirmation
5. View profile analytics
6. Export profile data

**Discovery Workflow**:
1. Execute nonprofit discovery
2. Execute federal discovery
3. Execute BMF discovery with filters
4. Handle discovery errors
5. Filter and sort results
6. Paginate through results

**Screening Workflow**:
1. Fast screening mode (200 → 50)
2. Thorough screening mode (50 → 10-15)
3. Select opportunities for intelligence
4. Handle screening errors
5. View screening scores

**Intelligence Workflow**:
1. Quick depth analysis ($0.75)
2. Standard depth analysis ($7.50)
3. Enhanced depth analysis ($22.00)
4. Complete depth analysis ($42.00)
5. Generate reports (4 templates)
6. Export data (4 formats)
7. Create grant package

**End-to-End**:
1. Create profile → Discover → Screen → Analyze → Report
2. Multi-profile batch processing
3. Error recovery and retry
4. Cost tracking and budgeting

**Testing Tools**:
- Manual testing checklist
- Integration test suite (planned)
- Performance benchmarking
- Error scenario testing

---

## LEGACY CODE CLEANUP PLAN

### Phase 1: Identify Unused Code (Week 4)
**Current Status**: 31,413 lines total
- index.html: 10,163 lines (includes legacy 8-stage content)
- app.js: 19,143 lines (includes duplicated logic)
- modules: 1,920 lines (new, clean code)

**Cleanup Targets**:
1. **Legacy Stage HTML** (~3,000 lines in index.html)
   - Old WELCOME stage content
   - Old PROFILER stage forms
   - Old DISCOVER/PLAN/ANALYZE stages
   - Old EXAMINE/APPROACH stages
   - Old SETTINGS stage

2. **Duplicated Functions in app.js** (~8,000 lines)
   - Profile management functions (now in profiles-module.js)
   - Discovery functions (now in screening-module.js)
   - Screening functions (now in screening-module.js)
   - Intelligence functions (now in intelligence-module.js)
   - Duplicated formatting/validation (now in shared-module.js)

3. **Unused State Variables** (~500 lines)
   - Legacy navigation state
   - Duplicated profile state
   - Old discovery state
   - Unused UI state

**Safety Approach**:
- ✅ Keep original code commented (don't delete)
- ✅ Move deprecated code to `_deprecated/` sections
- ✅ Use feature flags for gradual migration
- ✅ Git tags at each cleanup step

### Phase 2: Module Migration (Week 5)
**Goal**: Fully migrate app.js to coordinator pattern

**Steps**:
1. Remove profile management logic (use profiles-module.js)
2. Remove discovery logic (use screening-module.js)
3. Remove screening logic (use screening-module.js)
4. Remove intelligence logic (use intelligence-module.js)
5. Remove formatting/validation (use shared-module.js)
6. Remove state management (use state-module.js)

**Target**: app.js 19,143 lines → ~500 lines (coordinator only)

### Phase 3: HTML Simplification (Week 6)
**Goal**: Remove legacy stage content

**Steps**:
1. Remove old stage HTML sections
2. Keep only 3 new stage sections
3. Remove legacy navigation HTML
4. Clean up unused CSS
5. Consolidate script imports

**Target**: index.html 10,163 lines → ~3,000 lines (70% reduction)

### Phase 4: Final Cleanup (Week 7)
**Total Code Reduction**:
- Before: 31,413 lines (HTML + JS + modules)
- After: ~6,000 lines (3,000 HTML + 500 JS + 2,500 modules)
- **Reduction**: 81% (25,000 lines removed)

---

## PHASE 9 DETAILED PLAN

### Week 4: Modal Forms & Advanced Filters (HIGH PRIORITY)

**Task 4.1: Create Modal Component System** (8 hours)
- Build reusable modal-component.js
- Alpine.js x-show/x-transition integration
- Modal state management
- Keyboard shortcuts (ESC to close)
- Backdrop click to close
- Focus management

**Task 4.2: Profile Modals** (12 hours)
- Create profile modal (EIN + manual modes)
- Edit profile modal (load + save)
- Delete profile modal (confirmation)
- Validation and error handling
- Integration with profiles-module.js

**Task 4.3: Advanced BMF Filters** (10 hours)
- NTEE code multi-select component
- Geographic filter builder
- Financial range sliders
- Organization type toggles
- Filter preset save/load
- Integration with screening-module.js

**Task 4.4: Testing & Polish** (6 hours)
- Test all modal workflows
- Test filter configurations
- Error handling validation
- UX improvements

**Deliverables**:
- modal-component.js (~300 lines)
- Profile modals in index.html (~400 lines)
- Advanced filters UI (~500 lines)
- Enhanced screening-module.js (~100 lines added)

---

### Week 5: Opportunity Details & Network Visualization (HIGH PRIORITY)

**Task 5.1: Opportunity Detail View** (10 hours)
- Tabbed detail interface (overview/financials/network/risk)
- Full opportunity data display
- Historical funding patterns
- Related opportunities
- Notes and annotations
- Integration with intelligence-module.js

**Task 5.2: Network Visualization** (12 hours)
- Chart.js network graph setup
- Board member network display
- Shared connections visualization
- Centrality metrics overlay
- Interactive exploration
- Integration with Tool 12 outputs

**Task 5.3: Profile Analytics View** (8 hours)
- Quality score breakdown display
- Enhancement recommendations
- Data completeness meters
- Improvement suggestions
- Integration with profiles-module.js

**Task 5.4: Testing & Polish** (6 hours)
- Test detail views
- Test visualizations
- Performance optimization
- UX improvements

**Deliverables**:
- Opportunity detail view (~400 lines HTML)
- Network visualization component (~300 lines JS)
- Profile analytics view (~250 lines HTML)
- Enhanced modules (~150 lines added)

---

### Week 6: Analytics Dashboards & Visualizations (MEDIUM PRIORITY)

**Task 6.1: Create Visualization Module** (8 hours)
- visualization-module.js structure
- Chart.js integration
- Reusable chart components
- Responsive chart layouts

**Task 6.2: Scoring Visualizations** (10 hours)
- Multi-dimensional scoring radar charts
- Comparative bar charts
- Quality score trends
- Dimensional breakdown displays
- Boost factor indicators

**Task 6.3: Analytics Dashboards** (12 hours)
- Processing volume charts
- Success rate metrics
- Cost tracking over time
- Opportunity pipeline visualization
- Profile quality distribution

**Task 6.4: Financial Charts** (6 hours)
- Revenue/expense trends
- Grant distribution analysis
- Asset allocation pie charts
- Foundation payout ratios

**Deliverables**:
- visualization-module.js (~400 lines)
- Dashboard HTML (~500 lines)
- Chart integrations (~200 lines)

---

### Week 7: Legacy Code Cleanup (ESSENTIAL)

**Task 7.1: Identify & Comment Unused Code** (8 hours)
- Scan app.js for duplicated functions
- Comment out legacy stage logic
- Mark deprecated state variables
- Document what's being removed

**Task 7.2: Remove Legacy Stages from HTML** (6 hours)
- Comment out old stage HTML
- Remove legacy navigation
- Clean up unused CSS
- Consolidate script imports

**Task 7.3: Refactor app.js to Coordinator** (12 hours)
- Remove profiles logic (use module)
- Remove screening logic (use module)
- Remove intelligence logic (use module)
- Remove utilities (use shared-module)
- Keep only coordination code

**Task 7.4: Testing & Validation** (10 hours)
- Full regression testing
- Performance validation
- Error scenario testing
- Code size verification (target: 81% reduction)

**Deliverables**:
- app.js: 19,143 → ~500 lines (97% reduction)
- index.html: 10,163 → ~3,000 lines (70% reduction)
- Total: 31,413 → ~6,000 lines (81% reduction)

---

### Week 8: Report Customization & Settings (LOW PRIORITY)

**Task 8.1: Report Template Customization** (8 hours)
- Visual template previews
- Template customization UI
- Section inclusion toggles
- Branding options
- Integration with Tool 21

**Task 8.2: Export Format Options** (6 hours)
- Format-specific configuration
- Field selection for CSV
- Batch export UI
- Scheduled exports

**Task 8.3: Settings Management** (10 hours)
- Create settings-module.js
- Build settings UI (modal)
- System preferences
- API configuration
- User preferences
- Persistence (localStorage)

**Task 8.4: Bulk Operations** (8 hours)
- Bulk selection enhancement
- Batch processing UI
- Progress indicators
- Error handling

**Deliverables**:
- settings-module.js (~350 lines)
- Settings UI (~400 lines)
- Enhanced bulk operations (~200 lines)

---

### Week 9: Integration Testing & Polish (ESSENTIAL)

**Task 9.1: End-to-End Testing** (12 hours)
- Full workflow testing
- Error scenario testing
- Performance benchmarking
- Cross-browser testing

**Task 9.2: UI/UX Polish** (8 hours)
- Animation improvements
- Loading state polish
- Error message refinement
- Accessibility improvements (WCAG 2.1 AA)

**Task 9.3: Documentation** (6 hours)
- User guide creation
- Feature documentation
- API integration guide
- Deployment guide

**Task 9.4: Production Preparation** (6 hours)
- Code minification
- Asset optimization
- Performance tuning
- Security audit

**Deliverables**:
- Test suite (comprehensive)
- Documentation (user + technical)
- Production-ready build

---

### Week 10-11: Government Tools & Final Production (FROM START_HERE_V3)

**From Original Phase 9 Plan**:
- Tool 23: Grants.gov Opportunity Discovery
- Tool 24: USASpending.gov Award Analysis
- Tool 26: State Grants Discovery (Virginia focus)
- Docker containerization
- Environment configuration
- Database migration scripts
- Backup and recovery procedures
- Monitoring and logging
- User documentation

---

## TECHNICAL ARCHITECTURE

### Current Module System

**5 Core Modules** (1,920 lines):
1. state-module.js (89 lines) - Navigation & state
2. shared-module.js (281 lines) - Utilities & formatting
3. profiles-module.js (465 lines) - Profile CRUD & analytics
4. screening-module.js (529 lines) - Discovery & screening
5. intelligence-module.js (556 lines) - Analysis & reporting

**Planned Additional Modules**:
6. modal-component.js (~300 lines) - Reusable modal system
7. visualization-module.js (~400 lines) - Charts & dashboards
8. settings-module.js (~350 lines) - Settings & configuration

**Total Modular Code**: ~3,000 lines (clean, maintainable)

### Event-Driven Communication

**Alpine.js $dispatch Events**:
- `stage-changed` - Stage navigation
- `profile-selected` - Profile selection
- `discovery-complete` - Discovery results ready
- `screening-complete` - Screening results ready
- `proceed-to-intelligence` - Move to intelligence stage
- `intelligence-complete` - Analysis complete

**Benefits**:
- Loose coupling between modules
- Easy to add new listeners
- Clear data flow
- Testable interactions

### API Integration Strategy

**V2 Profile API** (6 endpoints):
- POST /api/v2/profiles/build (with Tool 25)
- GET /api/v2/profiles (list with pagination)
- GET /api/v2/profiles/{id} (get one)
- PUT /api/v2/profiles/{id} (update)
- DELETE /api/v2/profiles/{id} (delete)
- GET /api/v2/profiles/{id}/quality (quality score)

**V2 Discovery API** (3 endpoints):
- POST /api/v2/discovery/execute (track-based)
- GET /api/v2/discovery/bmf (BMF filtering)
- POST /api/v2/discovery/search (unified search)

**Tool Execution API** (4 endpoints):
- GET /api/v1/tools/list (all tools)
- GET /api/v1/tools/{id} (tool metadata)
- POST /api/v1/tools/{id}/execute (execute tool)
- GET /api/v1/tools/health (health check)

**Helper Functions** (api-helpers.js):
- executeToolAPI(toolId, params)
- screenOpportunities(opportunities, mode)
- analyzeOpportunityDeep(opportunity, depth, profile)
- generateReport(analysis, template)
- exportData(data, format)

---

## SUCCESS METRICS

### Code Quality Metrics

**Current State**:
- Total lines: 31,413 (HTML + JS + modules)
- Functions: 350+ (scattered)
- Stages: 8 (legacy) + 3 (new)
- Maintainability: Low (monolithic)

**Target State (End of Week 9)**:
- Total lines: ~6,000 (81% reduction)
- Functions: ~100 (organized in modules)
- Stages: 3 (consolidated)
- Maintainability: High (modular)

### Feature Completeness

**Week 4-5** (High Priority):
- ✅ Modal forms (create/edit/delete)
- ✅ Advanced BMF filters
- ✅ Opportunity detail views
- ✅ Network visualization

**Week 6** (Medium Priority):
- ⏳ Analytics dashboards
- ⏳ Scoring visualizations
- ⏳ Financial charts

**Week 7** (Essential):
- ⏳ Legacy code cleanup
- ⏳ Code reduction (81%)
- ⏳ Refactor to coordinator pattern

**Week 8** (Low Priority):
- ⏳ Report customization
- ⏳ Settings management
- ⏳ Bulk operations

**Week 9** (Essential):
- ⏳ Integration testing
- ⏳ UI/UX polish
- ⏳ Documentation

**Week 10-11** (Production):
- ⏳ Government tools
- ⏳ Docker deployment
- ⏳ Production readiness

### Performance Targets

**Load Time**:
- Initial page load: <2s (currently ~3-4s)
- Module load: <500ms
- Stage transition: <100ms

**Runtime Performance**:
- Profile list rendering: <500ms (1000 profiles)
- Discovery execution: <3s (200 results)
- Screening: <5s (200 opportunities)
- Intelligence analysis: 5-60min (depth-dependent)

**Memory Usage**:
- Initial load: <50MB
- With 1000 profiles: <100MB
- Peak usage: <200MB

---

## RUNNING LIST OF ITEMS

### Essential (Must Have) ✅
1. ✅ Modal forms (create/edit/delete profiles)
2. ✅ Advanced BMF filter configuration
3. ✅ Opportunity detail views
4. ✅ Legacy code cleanup (81% reduction)
5. ✅ Integration testing
6. ✅ End-to-end workflows validated

### Important (Should Have) ⏳
7. ⏳ Network visualization (basic)
8. ⏳ Profile analytics view
9. ⏳ Scoring visualizations (radar charts)
10. ⏳ Analytics dashboards (basic)
11. ⏳ Settings management UI

### Nice to Have (Could Have) 🔮
12. 🔮 Advanced network visualization (interactive)
13. 🔮 Financial charts (comprehensive)
14. 🔮 Report template customization
15. 🔮 Export format options
16. 🔮 Bulk operations interface
17. 🔮 Package assembly interface
18. 🔮 Scheduled exports
19. 🔮 Email delivery
20. 🔮 Real-time collaboration

### Future Enhancements (Won't Have Now) 💡
21. 💡 Mobile app version
22. 💡 Multi-user support
23. 💡 Real-time WebSocket updates
24. 💡 Advanced AI features
25. 💡 Custom workflow builder

---

## QUICK START COMMANDS

### Development Server
```bash
# Start web server
launch_catalynx_web.bat

# Alternative
python src/web/main.py

# Server URL
http://localhost:8000
```

### Testing
```bash
# Comprehensive test suite
python tests/profiles/test_profile_suite.py

# Individual tests
python tests/profiles/test_unified_service.py
python tests/profiles/test_orchestration.py
python tests/intelligence/test_990_pipeline.py
python tests/api/test_profiles_v2_api.py
```

### Git Status
```bash
# Check current branch
git branch
# Current: feature/bmf-filter-tool-12factor

# Recent commits
git log --oneline -10
# Latest: 720dd95 Phase 9 Week 3 - All 3 Stage UIs Complete
```

### Database Queries
```bash
# BMF organizations
sqlite3 data/nonprofit_intelligence.db "SELECT COUNT(*) FROM bmf_organizations;"
# Expected: 700,488

# Form 990 records
sqlite3 data/nonprofit_intelligence.db "SELECT COUNT(*) FROM form_990;"
# Expected: 626,983

# Form 990-PF records
sqlite3 data/nonprofit_intelligence.db "SELECT COUNT(*) FROM form_990pf;"
# Expected: 219,871
```

---

## IMPLEMENTATION PRIORITIES

### This Week (Week 4): Modal Forms & Filters
**Focus**: Essential user interactions
- Create/edit/delete profile modals
- Advanced BMF filter configuration
- Basic testing and validation

**Why This Week**: Cannot fully use the system without these forms

### Next Week (Week 5): Detail Views & Visualization
**Focus**: Enhanced user experience
- Opportunity detail views
- Network visualization (basic)
- Profile analytics display

**Why This Week**: Provides value to completed workflows

### Week 6: Dashboards & Analytics
**Focus**: Data insights
- Scoring visualizations
- Analytics dashboards
- Financial charts

**Why This Week**: Builds on completed infrastructure

### Week 7: Legacy Cleanup (CRITICAL)
**Focus**: Code reduction and performance
- Remove duplicated code
- Refactor app.js to coordinator
- Simplify index.html

**Why This Week**: Must happen before production

### Week 8: Polish & Configuration
**Focus**: Production readiness
- Report customization
- Settings management
- Bulk operations

**Why This Week**: Final features before testing

### Week 9: Testing & Documentation
**Focus**: Quality assurance
- End-to-end testing
- UI/UX polish
- Documentation

**Why This Week**: Validate everything works

### Week 10-11: Government Tools & Production
**Focus**: Final deployment
- Tool 23, 24, 26
- Docker deployment
- Production launch

**Why These Weeks**: Complete the vision

---

## IMPORTANT NOTES

### Keep Original Code as Reference
- ✅ Don't delete legacy stages (comment or collapse)
- ✅ Don't delete old functions (move to _deprecated)
- ✅ Use feature flags for gradual migration
- ✅ Git tags at each major step

### Backward Compatibility Strategy
- ✅ Legacy 8-stage navigation still accessible
- ✅ All legacy APIs still operational
- ✅ Can toggle between old/new UI
- ✅ Gradual user migration

### Testing Philosophy
- Test each module independently
- Test workflows end-to-end
- Test error scenarios
- Performance benchmarking

### Code Organization Principles
- Single Responsibility per module
- DRY (Don't Repeat Yourself)
- Event-driven communication
- API-first architecture

---

## FILES TO REVIEW

### Core Implementation Files
1. `src/web/static/modules/state-module.js` (89 lines)
2. `src/web/static/modules/shared-module.js` (281 lines)
3. `src/web/static/modules/profiles-module.js` (465 lines)
4. `src/web/static/modules/screening-module.js` (529 lines)
5. `src/web/static/modules/intelligence-module.js` (556 lines)
6. `src/web/static/app.js` (19,143 lines - TO BE REFACTORED)
7. `src/web/static/index.html` (10,163 lines - CONTAINS BOTH OLD & NEW)

### Documentation Files
1. `PHASE_9_FRONTEND_WEEK2_PROGRESS.md` (Week 2-3 detailed progress)
2. `START_HERE_V3.md` (Phase 8 complete, Phase 9 prep)
3. `CLAUDE.md` (System overview, updated with Phase 8)
4. `docs/PROFILE_ENHANCEMENT_DATA_FLOW.md` (Architecture spec)
5. `docs/MIGRATION_HISTORY.md` (Transformation timeline)

### Backend API Files
1. `src/web/routers/profiles_v2.py` (680 lines - V2 Profile API)
2. `src/web/routers/discovery_v2.py` (V2 Discovery API)
3. `src/web/routers/tools.py` (Unified Tool Execution API)
4. `src/web/static/api-helpers.js` (API helper functions)

---

## FINAL STATUS

**Phase 8**: ✅ **COMPLETE** (100% - 20/20 tasks)
**Phase 9 Week 2-3**: ✅ **COMPLETE** (Modular architecture + Stage UIs)
**Phase 9 Week 4+**: ⏳ **PLANNED** (Modal forms → Testing → Production)

**System Status**: **FUNCTIONAL** but missing essential UI elements (modals, filters)
**Code Status**: **NEEDS CLEANUP** (31,413 lines → target 6,000 lines)
**Next Milestone**: Week 4-5 essential UI components, Week 7 code cleanup

**Well done on Weeks 2-3!** 🎉
**Focus for Week 4**: Modal forms and advanced filters (essential for usability)

---

*Last Updated: 2025-10-03*
*Session: Context Window #5 → #6 Handoff*
*Phase: 9 Weeks 2-3 Complete → Week 4+ Planning*
*Total Lines: 31,413 → Target 6,000 (81% reduction by Week 7)*

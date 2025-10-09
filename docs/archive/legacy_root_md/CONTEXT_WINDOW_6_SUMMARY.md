# Context Window 6 - Quick Start Summary

**Welcome to Context Window #6!** This is your quick reference guide to get started immediately.

---

## WHAT YOU NEED TO KNOW

### Current Status
- **Phase 8**: 100% Complete (20/20 tasks)
- **Phase 9 Weeks 2-3**: 100% Complete (modular architecture + stage UIs)
- **Phase 9 Week 4+**: Ready to Start (modal forms → production)

### What Works Right Now ✅
- Backend: 23 tools operational, 626K+ Form 990 records, 700K+ BMF organizations
- Frontend: 3-stage modular architecture (PROFILES, SCREENING, INTELLIGENCE)
- Modules: 5 clean modules (1,920 lines) with event-driven communication
- APIs: V2 Profile API (6 endpoints), V2 Discovery API, Unified Tool API

### What's Missing (Critical) ❌
- Modal forms (cannot create/edit/delete profiles)
- Advanced BMF filter configuration (limited discovery options)
- Opportunity detail views (limited information display)
- Network visualization (no charts yet)

---

## START HERE

### 1. Read These Files (In Order)
1. **START_HERE_V4.md** (975 lines) - Comprehensive plan for Phase 9 Week 4+
   - Gap analysis (9 categories, 40+ features)
   - Week-by-week plan (Weeks 4-11)
   - Running list of items
   - Implementation priorities

2. **PHASE_9_GAP_ANALYSIS.md** (520 lines) - Deep dive into missing features
   - Original Catalynx vs current implementation
   - Feature-by-feature analysis
   - Legacy code reference map
   - Impact assessment

3. **PHASE_9_FRONTEND_WEEK2_PROGRESS.md** - What was completed in Weeks 2-3

### 2. Understand the Architecture

**5 Core Modules** (All Complete):
- `state-module.js` (89 lines) - Navigation & state management
- `shared-module.js` (281 lines) - Utilities & formatting
- `profiles-module.js` (465 lines) - Profile CRUD & analytics
- `screening-module.js` (529 lines) - Discovery & screening
- `intelligence-module.js` (556 lines) - Analysis & reporting

**3-Stage UI** (All Built):
- **PROFILES** - Profile list, search, sort (replaces WELCOME, PROFILER, SETTINGS)
- **SCREENING** - Discovery, screening workflow (replaces DISCOVER, PLAN, ANALYZE)
- **INTELLIGENCE** - Analysis, reports, packages (replaces EXAMINE, APPROACH)

**Event-Driven Communication**:
- Uses Alpine.js $dispatch for inter-module communication
- Events: stage-changed, profile-selected, discovery-complete, etc.

### 3. Current Code Statistics

**Total Lines**: 31,413
- index.html: 10,163 lines (includes legacy + new 3-stage UI)
- app.js: 19,143 lines (needs refactoring, contains legacy code)
- modules: 1,920 lines (clean, modular, complete)

**Target by Week 7**: ~6,000 lines (81% reduction)
- index.html: ~3,000 lines (remove legacy stages)
- app.js: ~500 lines (coordinator pattern only)
- modules: ~2,500 lines (add modal, visualization, settings modules)

---

## WHAT TO DO NEXT (WEEK 4)

### Priority 1: Modal Forms (CRITICAL - 20-24 hours)
**Cannot use system without these**

Files to Create:
1. `src/web/static/modules/modal-component.js` (~300 lines)
   - Reusable modal system
   - Alpine.js x-show/x-transition integration
   - Keyboard shortcuts (ESC to close)
   - Focus management

2. Modal HTML in `index.html`:
   - Create profile modal (EIN + manual modes)
   - Edit profile modal (load + save)
   - Delete profile modal (confirmation)
   - Advanced filter modal

Files to Modify:
- `src/web/static/modules/profiles-module.js` - Add modal open/close logic
- `src/web/static/modules/screening-module.js` - Add filter modal logic

**Tasks**:
- [ ] Create modal-component.js
- [ ] Build create profile modal (EIN input, manual form)
- [ ] Build edit profile modal (load existing, save changes)
- [ ] Build delete profile modal (confirmation dialog)
- [ ] Wire modals to profiles-module.js
- [ ] Test all modal workflows

### Priority 2: Advanced BMF Filters (CRITICAL - 10-12 hours)
**Discovery incomplete without these**

Files to Create:
1. Filter UI components in `index.html`:
   - NTEE code multi-select (searchable, 200+ codes)
   - Geographic filter builder (state, county, city, radius)
   - Financial range sliders (revenue, assets, grants)
   - Organization type toggles

Files to Modify:
- `src/web/static/modules/screening-module.js` - Add filter configuration

**Tasks**:
- [ ] Build NTEE code multi-select component
- [ ] Build geographic filter builder
- [ ] Build financial range sliders
- [ ] Build organization type toggles
- [ ] Add filter preset save/load
- [ ] Wire filters to screening-module.js
- [ ] Test filter configurations

**Legacy Reference**:
- `app.js` lines 11116-11280 (original BMF filter implementation)
- Functions: `runQuickBMFFilter()`, `executeBMFFilter()`

---

## IMPLEMENTATION ROADMAP

### Week 4 (Current) - Modal Forms & Advanced Filters
- **Focus**: Essential user interactions
- **Effort**: 30-36 hours
- **Why**: Cannot use system without these
- **Deliverables**: modal-component.js, profile modals, advanced filters

### Week 5 - Detail Views & Network Visualization
- **Focus**: Enhanced user experience
- **Effort**: 30-34 hours
- **Why**: Completes core workflows
- **Deliverables**: Opportunity detail view, network charts, profile analytics

### Week 6 - Dashboards & Analytics
- **Focus**: Data insights
- **Effort**: 20-24 hours
- **Why**: Enhances decision-making
- **Deliverables**: Analytics dashboards, scoring visualizations, financial charts

### Week 7 - Legacy Code Cleanup (ESSENTIAL)
- **Focus**: Code reduction & performance
- **Effort**: 32-36 hours
- **Why**: Must happen before production
- **Target**: 31,413 → 6,000 lines (81% reduction)
- **Deliverables**: Refactored app.js (19K → 500 lines), simplified index.html (10K → 3K)

### Week 8 - Settings & Polish
- **Focus**: Configuration & bulk operations
- **Effort**: 26-32 hours
- **Deliverables**: Settings UI, bulk operations, report customization

### Week 9 - Testing & Documentation
- **Focus**: Quality assurance
- **Effort**: 32-36 hours
- **Deliverables**: End-to-end tests, UI polish, documentation

### Week 10-11 - Government Tools & Production
- **Focus**: Final deployment
- **Effort**: 40+ hours
- **Deliverables**: Tool 23/24/26, Docker deployment, production launch

---

## QUICK COMMANDS

### Development Server
```bash
# Start web server
launch_catalynx_web.bat
# OR
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
python tests/api/test_profiles_v2_api.py
```

### Git Status
```bash
git branch
# Current: feature/bmf-filter-tool-12factor

git log --oneline -5
# Latest commits:
# 72f60c3 Phase 9 Context Window Handoff - Comprehensive Planning & Gap Analysis
# 720dd95 Phase 9 Week 3 - All 3 Stage UIs Complete
# 698a105 Phase 9 Week 3 - PROFILES Stage UI Complete
```

### Database Queries
```bash
# BMF organizations (expected: 700,488)
sqlite3 data/nonprofit_intelligence.db "SELECT COUNT(*) FROM bmf_organizations;"

# Form 990 records (expected: 626,983)
sqlite3 data/nonprofit_intelligence.db "SELECT COUNT(*) FROM form_990;"
```

---

## KEY FILES

### Start Here Documents
1. `START_HERE_V4.md` - Comprehensive plan (THIS SESSION)
2. `PHASE_9_GAP_ANALYSIS.md` - Feature gap analysis (THIS SESSION)
3. `CONTEXT_WINDOW_6_SUMMARY.md` - Quick reference (THIS FILE)
4. `START_HERE_V3.md` - Phase 8 complete summary
5. `PHASE_9_FRONTEND_WEEK2_PROGRESS.md` - Weeks 2-3 progress

### Core Implementation
1. `src/web/static/modules/state-module.js` (89 lines)
2. `src/web/static/modules/shared-module.js` (281 lines)
3. `src/web/static/modules/profiles-module.js` (465 lines)
4. `src/web/static/modules/screening-module.js` (529 lines)
5. `src/web/static/modules/intelligence-module.js` (556 lines)
6. `src/web/static/app.js` (19,143 lines - TO BE REFACTORED)
7. `src/web/static/index.html` (10,163 lines - CONTAINS LEGACY + NEW)

### Documentation
1. `CLAUDE.md` - System overview
2. `docs/PROFILE_ENHANCEMENT_DATA_FLOW.md` - Architecture spec
3. `docs/MIGRATION_HISTORY.md` - Transformation timeline

---

## RUNNING LIST (FROM GAP ANALYSIS)

### Week 4 - Critical (Must Have) ✅
- [ ] Create profile modal (EIN + manual)
- [ ] Edit profile modal
- [ ] Delete profile modal
- [ ] Advanced BMF filter modal
- [ ] NTEE code multi-select
- [ ] Geographic filter builder
- [ ] Financial range sliders
- [ ] Filter preset save/load

### Week 5 - High Priority (Should Have) ⏳
- [ ] Opportunity detail view
- [ ] Network visualization (Chart.js)
- [ ] Profile analytics view
- [ ] Historical funding display

### Week 6 - Medium Priority (Nice to Have) ⏳
- [ ] Analytics dashboards
- [ ] Scoring radar charts
- [ ] Financial charts

### Week 7 - Essential (Must Do) ⏳
- [ ] Remove duplicated code from app.js
- [ ] Remove legacy stages from index.html
- [ ] Refactor app.js to coordinator (19K → 500 lines)
- [ ] Achieve 81% code reduction

### Week 8 - Low Priority (Could Have) ⏳
- [ ] Settings management UI
- [ ] Bulk operations interface
- [ ] Report customization

### Week 9 - Essential (Must Do) ⏳
- [ ] End-to-end testing
- [ ] UI/UX polish
- [ ] Documentation

---

## IMPORTANT NOTES

### Legacy Code Strategy
- ✅ **DO NOT DELETE** legacy code yet
- ✅ Keep original implementations as reference
- ✅ Comment or move to _deprecated sections
- ✅ Use feature flags for gradual migration
- ⏳ Full removal in Week 7 cleanup

### Backward Compatibility
- ✅ Legacy 8-stage navigation still accessible (collapsible)
- ✅ All legacy APIs still operational
- ✅ Can toggle between old/new UI
- ✅ Zero breaking changes approach

### Testing Philosophy
- Test each module independently
- Test workflows end-to-end
- Test error scenarios thoroughly
- Performance benchmark before/after

---

## SUCCESS CRITERIA

### Week 4 Success = All Modals Working
- ✅ Can create profiles via EIN lookup (Tool 25)
- ✅ Can create profiles manually
- ✅ Can edit existing profiles
- ✅ Can delete profiles with confirmation
- ✅ Can configure advanced BMF filters
- ✅ Discovery works with full filter options

### Phase 9 Success = Production Ready
- ✅ All essential features implemented
- ✅ 81% code reduction achieved (31K → 6K lines)
- ✅ End-to-end workflows tested
- ✅ Performance targets met (<2s load time)
- ✅ Documentation complete
- ✅ Ready for deployment

---

## DECISION TREE

**Question**: Where do I start?
**Answer**: Read START_HERE_V4.md → Review PHASE_9_GAP_ANALYSIS.md → Start Week 4 tasks

**Question**: What's the most critical work?
**Answer**: Modal forms (Week 4) - system unusable without them

**Question**: Can I skip to Week 5?
**Answer**: No - Week 4 modal forms are prerequisites for everything else

**Question**: When do we clean up legacy code?
**Answer**: Week 7 - after all new features are complete and tested

**Question**: How do I find original implementations?
**Answer**: See "Legacy Code Reference Map" in PHASE_9_GAP_ANALYSIS.md

**Question**: What if I break something?
**Answer**: Git tags at each step, feature flags for rollback, legacy code preserved

---

## FINAL CHECKLIST

Before you start coding:
- [ ] Read START_HERE_V4.md (comprehensive plan)
- [ ] Read PHASE_9_GAP_ANALYSIS.md (gap analysis)
- [ ] Understand modular architecture (5 modules)
- [ ] Understand 3-stage UI (PROFILES, SCREENING, INTELLIGENCE)
- [ ] Review legacy code reference map
- [ ] Start web server (http://localhost:8000)
- [ ] Test current system (see what's missing)

Ready to code:
- [ ] Create modal-component.js
- [ ] Build profile modals (create/edit/delete)
- [ ] Build advanced filter modal
- [ ] Test all modal workflows
- [ ] Commit progress with clear messages

---

## GET HELP

**Stuck on architecture?** → Read `CLAUDE.md`
**Stuck on APIs?** → Read `docs/PROFILE_ENHANCEMENT_DATA_FLOW.md`
**Stuck on legacy code?** → See reference map in `PHASE_9_GAP_ANALYSIS.md`
**Stuck on modules?** → Read `PHASE_9_FRONTEND_WEEK2_PROGRESS.md`

**Key Principle**: All backend functionality exists. All we need is frontend UI components. The hard work is done - we're just wiring it up!

---

**Welcome to Context Window #6!**
**Your Focus: Week 4 - Modal Forms & Advanced Filters (30-36 hours)**
**Your Goal: Make the system fully usable**

**Let's build! 🚀**

---

*Created: 2025-10-03*
*Context Window: #6*
*Phase: 9 Week 4 Start*
*Status: Ready to Code*

# START HERE V6 - Opportunity Modal Enhancement (In Progress)

**Date**: 2025-10-05
**Status**: ✅ **Phases 1-2 Complete** (2 of 5) | 🚧 **Phase 3-5 Pending**
**Context**: Comprehensive opportunity modal enhancement with Tool 25 integration

---

## 🎯 Current Session Goal

Enhance the opportunity detail modal to provide users with complete information for promotion/demotion decisions:
1. ✅ Rename terminology (stage_category → category_level, auto_qualified → qualified)
2. ✅ Integrate Tool 25 (Web Intelligence) for real Scrapy web scraping
3. ⏳ Enhance existing tabs with comprehensive 990/Scrapy data
4. ⏳ Add promotion/demotion system
5. ⏳ Add Notes tab with auto-save

---

## ✅ Completed Work (Phases 1-2)

### **Phase 1: Database & Terminology Updates** ✅

**Backend Changes** (`src/web/routers/profiles_v2.py`):
- Renamed `stage_category` → `category_level` throughout
- Renamed `auto_qualified` → `qualified` in all scoring logic
- Updated summary counts: `{"qualified": 0, "review": 0, "consider": 0, "low_priority": 0}`
- Updated database save logic to use `category_level`
- Updated `GET /api/v2/profiles/{profile_id}/opportunities` endpoint

**Frontend Changes**:
- `index.html`: Updated summary badges "🟢 Auto-Qualified" → "🟢 Qualified"
- `index.html`: Updated all color coding for `category_level` instead of `stage_category`
- `screening-module.js`: Updated state object and notifications

**Key Files Modified**:
- `src/web/routers/profiles_v2.py` (7 changes)
- `src/web/static/index.html` (3 changes)
- `src/web/static/modules/screening-module.js` (3 changes)

---

### **Phase 2: Tool 25 Web Intelligence Integration** ✅

**Backend Integration** (`src/web/routers/opportunities.py:199-309`):
- Integrated Tool 25 (Web Intelligence Tool) with full Scrapy support
- Replaced placeholder response with actual web scraping
- Converts `OrganizationIntelligence` model to web_data structure
- Saves results to database `analysis_discovery.web_data`
- Returns comprehensive response with execution stats

**Web Data Structure**:
```javascript
{
  "website": "https://example.org",
  "website_verified": true,  // 990 cross-validation
  "leadership": [
    {
      "name": "John Doe",
      "title": "Executive Director",
      "email": "john@example.org",
      "phone": "555-1234",
      "bio": "...",
      "matches_990": true  // Cross-validated with 990 Part VIII
    }
  ],
  "leadership_cross_validated": true,
  "contact": {
    "email": "info@example.org",
    "phone": "555-5678",
    "address": "123 Main St, City, ST 12345"
  },
  "social_media": {
    "linkedin": "https://linkedin.com/company/...",
    "twitter": "https://twitter.com/...",
    "facebook": "https://facebook.com/..."
  },
  "mission": "Mission statement from website",
  "programs": [...],
  "data_quality_score": 0.85,
  "pages_scraped": 5,
  "execution_time": 12.3
}
```

**Frontend Update** (`screening-module.js:676-720`):
- Enhanced `runWebResearch()` with Tool 25 integration
- Added smart notifications with execution stats
- Auto-switches to Website Data tab after completion
- Shows: "✅ Web research complete! Found 3 leadership members (5 pages in 12.3s)"

**Key Files Modified**:
- `src/web/routers/opportunities.py` (110 lines added)
- `src/web/static/modules/screening-module.js` (enhanced runWebResearch method)

---

## 🚧 Remaining Work (Phases 3-5)

### **Phase 3: Enhance Existing Tabs with 990/Scrapy Data** ⏳

**Tab 2: Organization Details** (Enhance after line 1051 in index.html):
- Add Mission & Programs section (from 990 Part III or web_data.mission)
- Add Tax-Exempt Status section (organization type, foundation code)
- Add Financial Health Indicators (net assets, operating margin, months of reserves)
- Add IRS Compliance info (filing status, tax year)

**Tab 3: Grant History** (Enhance after line 1087 for 990-PF):
- Add Top Recipients list (Schedule I grant data)
- Add Grant Distribution breakdown (geographic, program area)
- Add Grant Size Statistics (average, min, max grants)
- Add Grant-Making Patterns (seasonal cycles, payout requirements)

**Tab 5: Website Data** (Enhance lines 1149-1183):
- Add Grant Application URL (if detected)
- Add Leadership cross-validation indicator
- Add Social Media links (LinkedIn, Twitter, Facebook)
- Add Recent News section
- Add Website freshness indicator

**Estimated Time**: 45 minutes

---

### **Phase 4: Promotion/Demotion System** ⏳

**Backend API Endpoints** (Add to `opportunities.py`):

```python
@router.post("/{opportunity_id}/promote")
async def promote_category_level(opportunity_id: str):
    """
    Promote: low_priority → consider → review → qualified
    If already qualified → current_stage = 'intelligence'
    """
    # Implementation in plan

@router.post("/{opportunity_id}/demote")
async def demote_category_level(opportunity_id: str):
    """
    Demote: qualified → review → consider → low_priority
    Cannot demote below low_priority
    """
    # Implementation in plan
```

**Frontend Modal Footer** (Update lines 1197-1207 in index.html):
- Replace current footer with 3-section layout:
  - Left: Demote button (⬇️ disabled if low_priority)
  - Center: Current category level badge
  - Right: Close + Promote buttons (⬆️ Promote or 🚀 Move to Intelligence)

**Frontend Methods** (Add to screening-module.js):
- `async promoteOpportunity()` - Calls promote endpoint, shows notification
- `async demoteOpportunity()` - Calls demote endpoint, shows notification
- Auto-reloads opportunities after promotion/demotion

**Estimated Time**: 40 minutes

---

### **Phase 5: Add Notes Tab with Auto-Save** ⏳

**Tab 6: Notes** (Add after Website Data tab in index.html):
- User Notes section: Free-form textarea with character counter (0/2000)
- Auto-save with debouncing (saves 1 second after user stops typing)
- System Information section: Discovery date, last updated, workflow stage, processing status

**Backend Endpoint** (Add to `opportunities.py`):
```python
@router.patch("/{opportunity_id}/notes")
async def update_opportunity_notes(opportunity_id: str, request: Dict[str, Any]):
    """Update notes field in opportunities table"""
    # Validate max 2000 characters
    # Update database
    # Return success
```

**Frontend Auto-Save** (Add to screening-module.js):
```javascript
notesSaving: false,
notesSaved: false,
notesDebounceTimer: null,

async autoSaveNotes() {
    clearTimeout(this.notesDebounceTimer);
    this.notesDebounceTimer = setTimeout(async () => {
        await this.saveNotesToDatabase();
    }, 1000);
}
```

**Estimated Time**: 25 minutes

---

## 📂 Key Files Reference

**Backend**:
- `src/web/routers/profiles_v2.py` - Discovery endpoint, category_level logic
- `src/web/routers/opportunities.py` - Web research (Tool 25), promote/demote (pending)
- `tools/web-intelligence-tool/app/web_intelligence_tool.py` - Tool 25 implementation
- `tools/web-intelligence-tool/app/scrapy_pipelines/structured_output_pipeline.py` - OrganizationIntelligence model

**Frontend**:
- `src/web/static/index.html` - Opportunity modal (lines 875-1210)
- `src/web/static/modules/screening-module.js` - Discovery, web research, modal logic

**Database**:
- `current_stage`: discovery, screening, intelligence, approach (workflow stage)
- `category_level`: qualified, review, consider, low_priority (quality tier - promotable/demotable)
- `analysis_discovery.web_data`: Web Intelligence Tool 25 results
- `notes`: User notes field (to be added)

---

## 🧪 Testing Checklist

**Phase 1 Tests** (Terminology):
- [ ] Run discovery → Verify summary shows "🟢 Qualified" (not "Auto-Qualified")
- [ ] Check opportunity cards → Verify `category_level` colors display correctly
- [ ] Open modal → Verify score breakdown uses correct category colors

**Phase 2 Tests** (Tool 25 Web Research):
- [ ] Click "Run Web Research" button in modal Website Data tab
- [ ] Verify notification: "🕷️ Starting web research with Scrapy (Tool 25)..."
- [ ] Wait for completion (~10-60 seconds depending on website)
- [ ] Verify success: "✅ Web research complete! Found X leadership members (Y pages in Zs)"
- [ ] Verify modal auto-switches to Website Data tab
- [ ] Verify web_data displays: website URL, leadership list, contact info
- [ ] Verify cross-validation indicator if leadership matches 990 Part VIII

**Phase 3 Tests** (Enhanced Tabs - PENDING):
- [ ] Organization Details tab shows mission, tax status, financial health
- [ ] Grant History tab shows top recipients, grant statistics (990-PF only)
- [ ] Website Data tab shows social media, grant application URL

**Phase 4 Tests** (Promotion/Demotion - PENDING):
- [ ] Demote button disabled when category_level = "low_priority"
- [ ] Promote from low_priority → consider → review → qualified
- [ ] Promote from qualified → intelligence stage (workflow change)
- [ ] Verify opportunities list refreshes after promotion/demotion

**Phase 5 Tests** (Notes Tab - PENDING):
- [ ] Notes tab exists and displays
- [ ] Type notes → auto-saves after 1 second
- [ ] Character counter updates correctly (X/2000)
- [ ] System info shows discovery date, last updated, etc.

---

## 🚀 Next Session Plan

### **Immediate Actions** (Start here):

1. **Test Phase 1 & 2 Changes**:
   ```bash
   # Restart server to pick up changes
   python src/web/main.py
   ```
   - Navigate to http://localhost:8000
   - Select a profile (e.g., "Heroes Bridge")
   - Run discovery
   - Verify "Qualified" label (not "Auto-Qualified")
   - Open an opportunity modal
   - Click "Run Web Research" in Website Data tab
   - Verify Tool 25 executes and displays results

2. **If Tests Pass** → Continue with Phase 3 (Enhance existing tabs)

3. **If Tests Fail** → Debug and fix issues before proceeding

### **Phase 3 Implementation** (Next):
- Enhance Organization Details tab with 990 Part III data
- Enhance Grant History tab with Schedule I grant analysis
- Enhance Website Data tab with social media, news, grant application detection

### **Phases 4-5** (After Phase 3):
- Implement promotion/demotion system
- Add Notes tab with auto-save

---

## 📊 Progress Summary

**Total Estimated Time**: ~3.5 hours
**Completed**: ~1.5 hours (Phases 1-2)
**Remaining**: ~2 hours (Phases 3-5)

**Files Modified So Far**: 3 files
**Lines Changed**: ~200 lines

**Architecture Decisions**:
- ✅ `category_level` is now the promotable/demotable field
- ✅ `current_stage` remains for workflow tracking (discovery → screening → intelligence → approach)
- ✅ Tool 25 provides real web scraping (not placeholder)
- ✅ Web data persists in `analysis_discovery.web_data`

---

## 🐛 Known Issues / Notes

1. **Tool 25 Execution Time**: Web scraping takes 10-60 seconds depending on website size. Consider adding progress indicator in future enhancement.

2. **990-PF Schedule I Data**: Grant recipient details need to be parsed from 990-PF Schedule I. Current implementation has basic grant_history structure but not detailed recipient list.

3. **Grant Application URL Detection**: Requires custom Scrapy spider logic to detect grant application pages. Placeholder field exists but not yet implemented.

4. **News Extraction**: Recent news section requires additional spider or API integration (Google News, etc.). Placeholder exists.

5. **Database Notes Field**: Needs to be added to opportunities table schema if not already present. Check schema before implementing Phase 5.

---

## 💡 Key Insights

**Why 2-Tier Category System?**
- `category_level` (qualified/review/consider/low_priority) = User-controlled quality tiers
- `current_stage` (discovery/screening/intelligence/approach) = System workflow stages
- Separation allows promotion within discovery stage, then jump to intelligence

**Why Tool 25 Integration?**
- Real Scrapy web scraping provides authentic data vs placeholder
- 990 cross-validation increases confidence in leadership data
- Structured outputs (OrganizationIntelligence model) ensure consistency
- Users get measurable value (execution stats, data quality scores)

**Modal as Decision Center**:
- User sees ALL available data in one place
- Promotes/demotes based on comprehensive information
- Notes capture decision rationale
- Replaces need for external spreadsheets/documents

---

**Last Updated**: 2025-10-05
**Next Session**: Continue with Phase 3 (Enhance existing tabs with 990/Scrapy data)
**Session Duration**: Plan for 2-hour session to complete remaining phases

---

## 🔗 Related Documentation

- `docs/PHASE3C_COMPLETE.md` - Processor deprecation (76% reduction)
- `docs/TWO_TOOL_ARCHITECTURE.md` - 12-factor tool architecture
- `tools/web-intelligence-tool/README.md` - Tool 25 documentation
- `CLAUDE.md` - Main project overview

**Ready to Continue!** 🚀

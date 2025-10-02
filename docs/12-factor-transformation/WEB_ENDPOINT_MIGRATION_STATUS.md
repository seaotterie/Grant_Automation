# Web Endpoint Migration Status
## ProfileService → UnifiedProfileService

**Date**: 2025-10-01
**Phase**: Phase 8 - Profile Service Consolidation

---

## Migration Summary

### ✅ COMPLETED: Core Services
1. **search_export_service.py** - Migrated to UnifiedProfileService
   - Removed ProfileService import
   - Updated `list_profiles()` usage (now returns profile_id strings)
   - All search and export functionality working with unified architecture

### ⚠️ DEPRECATED: Legacy Services (Recommend Removal)

#### 1. scoring_service.py
**Status**: DEPRECATED - Uses legacy lead-based architecture

**Issues**:
- Imports `get_profile_service()` from legacy ProfileService (line 23)
- Uses deprecated `get_profile_leads()` method (line 347)
- Converts leads to opportunities (lines 348-372) - OBSOLETE
- Updates opportunity stages using PipelineStage enum (line 398)
- Entire service appears to be for LEGACY lead system

**Used By**:
- `src/web/routers/scoring.py` - Calls methods like `calculate_financial_score()`, `calculate_network_score()`, `calculate_government_score()`
- **BUT**: These methods DON'T EXIST in scoring_service.py!

**Recommendation**:
❌ **DELETE** - This appears to be broken/incomplete legacy code
- Methods being called don't exist in the service
- Uses deprecated lead-based architecture
- Replaced by Tool 20 (Multi-Dimensional Scorer Tool)

#### 2. automated_promotion_service.py
**Status**: NOT YET REVIEWED

**Next Steps**: Check if this also uses deprecated ProfileService

---

## Web Routers Review

### ✅ Already Migrated
- **profiles.py** - Comments indicate "ProfileService removed - now using DatabaseManager exclusively"
- **main.py** - Comments indicate "ProfileService removed - consolidated to DatabaseManager only"

### ⚠️ Needs Review
- **scoring.py** - Uses scoring_service which is deprecated
- **discovery.py** - May use ProfileService (not checked yet)
- **ai_processing.py** - May use ProfileService (not checked yet)
- **admin.py** - May use ProfileService (not checked yet)
- **export.py** - May use ProfileService (not checked yet)

---

## Architectural Analysis

### Current Architecture (Correct)
```
UnifiedProfileService (src/profiles/unified_service.py)
├── Directory-based storage: data/profiles/{profile_id}/
├── Opportunities: {profile_id}/opportunities/opportunity_{id}.json
├── No file locking (stateless)
└── Embedded analytics
```

### Legacy Architecture (DEPRECATED)
```
ProfileService (src/profiles/service.py)
├── Flat file storage: data/profiles/profiles/{id}.json
├── LEADS system (deprecated)
├── Complex file locking
└── Separate sessions directory
```

### What Replaced What

| Legacy Component | Replacement | Status |
|-----------------|-------------|--------|
| ProfileService.get_profile_leads() | UnifiedProfileService.get_profile_opportunities() | ✅ Migrated |
| Lead-based workflow | Opportunity-based workflow | ✅ Migrated |
| PipelineStage enum | Unified stage management | ✅ Migrated |
| discovery_scorer.py | Tool 20 (Multi-Dimensional Scorer) | ✅ Replaced |
| promotion_engine.py | Automated promotion in UnifiedProfileService | ⚠️ Check |

---

## Action Items

### Immediate Actions (Today)
1. ✅ **DONE**: Migrate search_export_service.py to UnifiedProfileService
2. ❌ **DELETE**: scoring_service.py (deprecated, broken, replaced by Tool 20)
3. ⚠️ **CHECK**: automated_promotion_service.py for ProfileService usage
4. ⚠️ **REVIEW**: scoring.py router - remove calls to non-existent scoring_service methods

### Verification Steps
1. Check if scoring.py router is actually functional
   - Methods called don't exist in scoring_service
   - May be completely broken legacy code
2. Identify all Tool replacements
   - Tool 20: Multi-Dimensional Scorer replaces discovery_scorer
   - Tool 10: Financial Intelligence replaces financial scorers
   - Tool 12: Network Intelligence replaces network scorers

### Migration Strategy Going Forward

**Option A: Delete Legacy Scoring** (RECOMMENDED)
- Remove scoring_service.py entirely
- Remove scoring.py router endpoints that call it
- Update frontend to use Tool API endpoints instead
- Benefit: Clean architecture, no legacy code

**Option B: Update Legacy Scoring** (NOT RECOMMENDED)
- Fix broken method calls
- Update to use UnifiedProfileService
- Update to use opportunity-based architecture
- Downside: Maintaining parallel systems

---

## Tool Architecture Integration

### Scoring is Now Tool-Based

**Old Way** (DEPRECATED):
```python
# Via scoring_service.py
scoring_service = get_scoring_service()
score = scoring_service.calculate_financial_score(profile, opportunity)
```

**New Way** (CURRENT):
```python
# Via Tool 20 (Multi-Dimensional Scorer Tool)
from src.tools.tool_20_scorer import MultiDimensionalScorer
scorer = MultiDimensionalScorer()
result = await scorer.execute(
    context=ToolExecutionContext(
        opportunity_data=opportunity,
        profile_data=profile,
        current_stage="ANALYZE"
    )
)
score = result.data.overall_score
```

**Best Way** (RECOMMENDED):
```python
# Via unified tool execution API
response = requests.post(
    "http://localhost:8000/api/v1/tools/tool_20_scorer/execute",
    json={
        "opportunity_data": opportunity,
        "profile_data": profile,
        "current_stage": "ANALYZE"
    }
)
score = response.json()["result"]["overall_score"]
```

---

## Conclusion

**Current Status**:
- ✅ Core services migrated (search_export_service)
- ⚠️ Legacy services identified (scoring_service - BROKEN)
- ⚠️ Router review needed (scoring.py using non-existent methods)

**Recommendation**:
1. DELETE scoring_service.py (deprecated, broken, replaced by tools)
2. REVIEW and UPDATE scoring.py to use Tool API
3. VERIFY automated_promotion_service.py
4. Complete migration to UnifiedProfileService across all remaining routers

**Next Steps**:
1. Check automated_promotion_service.py for ProfileService usage
2. Review remaining routers (discovery, ai_processing, admin, export)
3. Delete deprecated scoring_service.py
4. Update scoring.py to use Tool 20 API
5. Test all endpoints end-to-end

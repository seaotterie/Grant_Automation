# Profile Service Feature Audit

## Executive Summary

**Objective**: Compare ProfileService (legacy) vs UnifiedProfileService (target) to plan migration strategy.

**Recommendation**: Migrate to UnifiedProfileService with selective feature additions from ProfileService.

**Key Finding**: File-based locking complexity (100+ lines) is unnecessary for single-user desktop app. UnifiedProfileService provides cleaner architecture with embedded analytics and better separation of concerns.

---

## Architecture Comparison

### ProfileService (Legacy - src/profiles/service.py)
- **File Structure**: Flat files in multiple directories
  - `data/profiles/profiles/{id}.json` - Profile data
  - `data/profiles/leads/` - Deprecated lead storage
  - `data/profiles/sessions/` - Discovery session tracking
  - `data/profiles/locks/` - Lock files for synchronization
- **Locking**: Complex dual-layer locking (file + thread)
- **Lines of Code**: 687 lines
- **Complexity**: HIGH (locking logic ~100 lines)

### UnifiedProfileService (Target - src/profiles/unified_service.py)
- **File Structure**: Directory-based with embedded data
  - `data/profiles/{profile_id}/profile.json` - Profile with embedded analytics
  - `data/profiles/{profile_id}/opportunities/opportunity_{id}.json` - Individual opportunities
- **Locking**: NONE (stateless operations)
- **Lines of Code**: 502 lines
- **Complexity**: LOW (clean, focused operations)

---

## Feature Comparison Matrix

### ✅ Features Present in BOTH Services

| Feature | ProfileService | UnifiedProfileService | Notes |
|---------|---------------|----------------------|-------|
| Get Profile | ✅ Lines 164-178 | ✅ Lines 40-58 | Both load from JSON |
| Save Profile | ✅ Lines 180-207 | ✅ Lines 60-80 | UnifiedProfileService simpler |
| List Profiles | ✅ Lines 209-230 | ✅ Lines 82-97 | Different filtering logic |
| Get Opportunity | ✅ Via UnifiedOpportunityService | ✅ Lines 103-129 | UnifiedProfileService handles directly |
| Save Opportunity | ✅ Via UnifiedOpportunityService | ✅ Lines 131-152 | UnifiedProfileService handles directly |
| Get Profile Opportunities | ✅ Via UnifiedOpportunityService | ✅ Lines 154-190 | UnifiedProfileService with stage filter |

### 🔴 Features ONLY in ProfileService (Need Migration Decision)

| Feature | Location | Migration Decision |
|---------|----------|-------------------|
| **File-Based Locking** | Lines 56-120 | ❌ **REMOVE** - Unnecessary for single-user desktop app |
| **Thread Locking** | Lines 56-120 | ❌ **REMOVE** - Not needed without file locking |
| **Stale Lock Detection** | Lines 121-162 | ❌ **REMOVE** - No locks = no stale locks |
| **Discovery Session Management** | Lines 472-516, 518-565 | ✅ **MIGRATE** - Critical for tracking discovery runs |
| **Session History & Analytics** | Lines 567-687 | ✅ **MIGRATE** - Needed for discovery tracking |
| **Profile Search** | Lines 253-291 | ⚠️ **EVALUATE** - May be useful for UI search |
| **Discovery Status Management** | Lines 293-354 | ✅ **MIGRATE** - Part of session management |
| **Legacy Lead Migration** | Lines 379-470 | ❌ **REMOVE** - One-time migration complete |

### 🟢 Features ONLY in UnifiedProfileService (Enhancements)

| Feature | Location | Value |
|---------|----------|-------|
| **Stage Management** | Lines 196-274 | ✅ Complete lifecycle tracking with history |
| **Promotion History** | Lines 242-260 | ✅ Audit trail for stage transitions |
| **Stage Transition Tracking** | Lines 224-248 | ✅ Duration calculation, entry/exit timestamps |
| **Scoring Operations** | Lines 280-324 | ✅ Cached scoring with force rescore |
| **User Assessment** | Lines 326-355 | ✅ User ratings and priority levels |
| **Real-Time Analytics** | Lines 361-449 | ✅ Computed on-demand from opportunities |
| **Recent Activity Generation** | Lines 451-495 | ✅ Dashboard-ready activity feed |
| **Embedded Analytics** | Lines 387-449 | ✅ No separate analytics service needed |

---

## Critical Feature Gap Analysis

### 1. Discovery Session Management (HIGH PRIORITY)

**ProfileService Implementation**:
```python
def start_discovery_session(self, profile_id: str, tracks: List[str] = None):
    """Start a new discovery session with locking to prevent race conditions"""
    with self._acquire_discovery_lock(profile_id, timeout=10):
        # Check for active sessions
        active_sessions = [s for s in self.get_profile_sessions(profile_id, limit=10)
                         if s.status == "in_progress"]

        # Mark abandoned sessions as failed
        for session in active_sessions:
            logger.warning(f"Marking abandoned session {session.session_id} as failed")
            self.fail_discovery_session(session.session_id, ["Session abandoned"])

        # Create new session
        session = DiscoverySession(session_id=f"session_{uuid.uuid4().hex[:12]}", ...)

        # Update profile discovery status
        profile.discovery_status = "in_progress"
        self._save_profile(profile)
```

**UnifiedProfileService Status**: ❌ **MISSING** - No session management

**Migration Strategy**: Add simplified session management without locking:
- Store sessions in profile directory: `{profile_id}/sessions/{session_id}.json`
- Remove lock-based race condition handling (single-user app)
- Keep session tracking for history and analytics

### 2. Profile Search (MEDIUM PRIORITY)

**ProfileService Implementation**:
```python
def search_profiles(self, query: str, filters: Dict = None) -> List[OrganizationProfile]:
    """Search profiles by name, EIN, keywords"""
    # Search logic with filtering
```

**UnifiedProfileService Status**: ❌ **MISSING** - No search capability

**Migration Strategy**: Add search to UnifiedProfileService if UI requires it.

### 3. Discovery Status Management (HIGH PRIORITY)

**ProfileService Implementation**:
```python
def update_discovery_status(self, profile_id: str, status: str):
    """Update profile discovery status (in_progress, completed, failed)"""
```

**UnifiedProfileService Status**: ❌ **MISSING** - No discovery status field

**Migration Strategy**: Add `discovery_status` to UnifiedProfile model and implement status management.

---

## Locking Complexity Analysis

### Why ProfileService Has Locking

**Purpose**: Prevent race conditions when multiple processes/threads access same profile simultaneously

**Use Cases**:
1. Starting discovery session (check for active sessions)
2. Updating discovery status
3. Saving profile during concurrent operations

**Implementation Cost**: ~100 lines of complex code
- File-based locking for cross-process synchronization
- Thread locking for in-process synchronization
- Stale lock detection and cleanup
- Timeout handling and retry logic

### Why UnifiedProfileService Doesn't Need Locking

**Single-User Desktop App**:
- One user, one process, sequential operations
- No concurrent access from multiple processes
- Web server is single-threaded for profile operations

**Stateless Design**:
- Read → Modify → Write pattern
- No shared mutable state
- Each operation is atomic at file system level

**Recommendation**: ✅ **REMOVE ALL LOCKING** - Adds complexity without benefit for single-user app

---

## Data Migration Strategy

### File Structure Changes

**ProfileService Structure**:
```
data/profiles/
├── profiles/{id}.json          # Profile data
├── leads/{id}_{source}.json    # Deprecated
├── sessions/{id}_{session}.json
└── locks/{id}_discovery.lock
```

**UnifiedProfileService Structure**:
```
data/profiles/
└── {profile_id}/
    ├── profile.json                    # Profile with embedded analytics
    ├── opportunities/
    │   └── opportunity_{id}.json       # Individual opportunities
    └── sessions/                       # NEW - To be added
        └── {session_id}.json
```

### Migration Steps

1. **Profile Migration**:
   - Read: `data/profiles/profiles/{id}.json`
   - Transform: Add embedded analytics structure
   - Write: `data/profiles/{profile_id}/profile.json`

2. **Opportunity Migration**:
   - Already using UnifiedOpportunityService (no migration needed)

3. **Session Migration**:
   - Read: `data/profiles/sessions/{id}_{session}.json`
   - Write: `data/profiles/{profile_id}/sessions/{session_id}.json`

4. **Cleanup**:
   - Delete: `data/profiles/leads/` (deprecated)
   - Delete: `data/profiles/locks/` (no longer needed)
   - Archive: `data/profiles/profiles/` after migration

---

## Migration Plan Summary

### Phase 1: Add Missing Features to UnifiedProfileService ✅
- [ ] Add discovery session management (without locking)
- [ ] Add discovery status tracking
- [ ] Add profile search (if needed by UI)
- [ ] Add session history and analytics

### Phase 2: Update Web Endpoints ✅
- [ ] Update all profile API endpoints to use UnifiedProfileService
- [ ] Test CRUD operations
- [ ] Verify discovery workflow

### Phase 3: Data Migration ✅
- [ ] Create migration script
- [ ] Migrate existing profiles to new structure
- [ ] Migrate session history
- [ ] Archive legacy data

### Phase 4: Remove Legacy Code ✅
- [ ] Deprecate ProfileService
- [ ] Remove file-based locking code
- [ ] Clean up legacy directories
- [ ] Update imports across codebase

---

## Risk Assessment

### LOW RISK ✅
- Removing file-based locking (not needed for single-user app)
- Removing thread locking (stateless design)
- Removing stale lock detection (no locks)

### MEDIUM RISK ⚠️
- Session management migration (need to preserve history)
- Discovery status tracking (need to ensure continuity)
- Profile search feature (verify UI requirements)

### MITIGATION STRATEGIES
1. **Test Coverage**: Create comprehensive tests before migration
2. **Data Backup**: Archive all profiles before migration
3. **Rollback Plan**: Keep ProfileService available during transition
4. **Incremental Rollout**: Migrate endpoints one at a time

---

## Conclusion

**Recommendation**: Proceed with migration to UnifiedProfileService

**Key Benefits**:
- 🎯 **Simpler Architecture**: Remove 100+ lines of locking complexity
- 📊 **Better Analytics**: Real-time embedded analytics
- 🔄 **Better Lifecycle Tracking**: Stage history and promotion tracking
- 🗂️ **Cleaner File Structure**: Directory-based organization
- ⚡ **Same Performance**: No locking overhead

**Required Work**:
1. Add 3 missing features to UnifiedProfileService (sessions, status, search)
2. Update 5-10 web endpoints
3. Create data migration script
4. Test thoroughly before removing ProfileService

**Timeline**: 2-3 days (Week 9, Days 1-2 of Phase 8 plan)

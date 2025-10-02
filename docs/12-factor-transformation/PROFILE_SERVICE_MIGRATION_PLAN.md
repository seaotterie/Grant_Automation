# Profile Service Migration Plan
## ProfileService → UnifiedProfileService

**Phase 8 - Nonprofit Workflow Solidification**
**Timeline**: Week 9, Days 1-2 (2 days)
**Status**: Ready for Implementation

---

## Executive Summary

**Goal**: Migrate from ProfileService (legacy, 687 lines with complex locking) to UnifiedProfileService (target, 502 lines with embedded analytics).

**Key Changes**:
- ✅ Remove 100+ lines of file-based locking complexity (unnecessary for single-user app)
- ✅ Add discovery session management to UnifiedProfileService
- ✅ Migrate to directory-based file structure with embedded analytics
- ✅ Update web endpoints to use UnifiedProfileService
- ✅ Preserve all critical functionality (sessions, analytics, discovery tracking)

**Benefits**:
- 27% code reduction (687 → 502 lines base + ~100 lines for sessions = ~600 total)
- Simpler architecture (no locking overhead)
- Better analytics (real-time embedded computation)
- Cleaner file structure (directory-based organization)

---

## Implementation Plan

### STEP 1: Add Missing Features to UnifiedProfileService
**File**: `src/profiles/unified_service.py`
**Duration**: 3-4 hours

#### 1.1 Add Discovery Session Management

**Add Session Data Classes** (after line 21):
```python
from .models import DiscoverySession, DiscoveryResult, DiscoveryTrack
```

**Add Session Methods** (after line 190):
```python
# ============================================================================
# DISCOVERY SESSION MANAGEMENT - SINGLE SOURCE OF TRUTH
# ============================================================================

def start_discovery_session(
    self,
    profile_id: str,
    tracks: List[str] = None,
    session_params: Dict[str, Any] = None
) -> Optional[str]:
    """
    Start a new discovery session for a profile.
    Returns session_id if successful, None if failed.
    """
    try:
        # Check for active sessions (without locking - single user app)
        active_sessions = self.get_profile_sessions(profile_id, status_filter="in_progress")

        if active_sessions:
            logger.warning(f"Profile {profile_id} has {len(active_sessions)} active sessions")
            # Mark as failed (abandoned sessions in single-user app)
            for session in active_sessions:
                self.fail_discovery_session(
                    session.session_id,
                    errors=["Session abandoned - new session started"]
                )

        # Create new session
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        session = DiscoverySession(
            session_id=session_id,
            profile_id=profile_id,
            started_at=now,
            status="in_progress",
            tracks=tracks or [],
            parameters=session_params or {}
        )

        # Save session to profile directory
        sessions_dir = self.data_dir / profile_id / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = sessions_dir / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(), f, indent=2, ensure_ascii=False)

        # Update profile discovery status
        profile = self.get_profile(profile_id)
        if profile:
            profile.discovery_status = "in_progress"
            profile.last_discovery_at = now
            self.save_profile(profile)

        logger.info(f"Started discovery session {session_id} for profile {profile_id}")
        return session_id

    except Exception as e:
        logger.error(f"Error starting discovery session: {e}")
        return None

def complete_discovery_session(
    self,
    session_id: str,
    results: List[Dict[str, Any]] = None,
    summary: Dict[str, Any] = None
) -> bool:
    """Mark discovery session as completed with results"""
    try:
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        # Update session
        session.status = "completed"
        session.completed_at = datetime.now().isoformat()
        session.results = results or []
        session.summary = summary or {}

        # Calculate duration
        if session.started_at:
            started = datetime.fromisoformat(session.started_at.replace('Z', '+00:00'))
            completed = datetime.fromisoformat(session.completed_at.replace('Z', '+00:00'))
            session.duration_seconds = (completed - started).total_seconds()

        # Save session
        sessions_dir = self.data_dir / session.profile_id / "sessions"
        session_file = sessions_dir / f"{session_id}.json"

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(), f, indent=2, ensure_ascii=False)

        # Update profile discovery status
        profile = self.get_profile(session.profile_id)
        if profile:
            profile.discovery_status = "completed"
            profile.last_discovery_at = session.completed_at
            self.save_profile(profile)

        logger.info(f"Completed discovery session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error completing discovery session: {e}")
        return False

def fail_discovery_session(
    self,
    session_id: str,
    errors: List[str] = None
) -> bool:
    """Mark discovery session as failed with error details"""
    try:
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        # Update session
        session.status = "failed"
        session.completed_at = datetime.now().isoformat()
        session.errors = errors or []

        # Save session
        sessions_dir = self.data_dir / session.profile_id / "sessions"
        session_file = sessions_dir / f"{session_id}.json"

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(), f, indent=2, ensure_ascii=False)

        # Update profile discovery status
        profile = self.get_profile(session.profile_id)
        if profile:
            profile.discovery_status = "failed"
            profile.last_discovery_at = session.completed_at
            self.save_profile(profile)

        logger.info(f"Failed discovery session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error failing discovery session: {e}")
        return False

def get_session(self, session_id: str) -> Optional[DiscoverySession]:
    """Get single discovery session by ID"""
    try:
        # Extract profile_id from session_id pattern or search all profiles
        for profile_dir in self.data_dir.iterdir():
            if not profile_dir.is_dir():
                continue

            sessions_dir = profile_dir / "sessions"
            if not sessions_dir.exists():
                continue

            session_file = sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return DiscoverySession(**data)

        return None

    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return None

def get_profile_sessions(
    self,
    profile_id: str,
    status_filter: Optional[str] = None,
    limit: int = 10
) -> List[DiscoverySession]:
    """Get discovery sessions for a profile"""
    try:
        sessions_dir = self.data_dir / profile_id / "sessions"
        if not sessions_dir.exists():
            return []

        sessions = []

        for session_file in sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                session = DiscoverySession(**data)

                # Apply status filter
                if status_filter is None or session.status == status_filter:
                    sessions.append(session)

            except Exception as e:
                logger.error(f"Error loading session {session_file}: {e}")
                continue

        # Sort by started_at (newest first)
        sessions.sort(
            key=lambda x: x.started_at or "1900-01-01",
            reverse=True
        )

        return sessions[:limit]

    except Exception as e:
        logger.error(f"Error getting sessions for profile {profile_id}: {e}")
        return []

def get_session_analytics(self, profile_id: str) -> Dict[str, Any]:
    """Get discovery session analytics for a profile"""
    try:
        sessions = self.get_profile_sessions(profile_id, limit=100)

        if not sessions:
            return {
                'total_sessions': 0,
                'completed_sessions': 0,
                'failed_sessions': 0,
                'in_progress_sessions': 0,
                'total_results': 0,
                'avg_results_per_session': 0.0,
                'last_session': None
            }

        completed = len([s for s in sessions if s.status == "completed"])
        failed = len([s for s in sessions if s.status == "failed"])
        in_progress = len([s for s in sessions if s.status == "in_progress"])

        total_results = sum(len(s.results) for s in sessions if s.results)
        avg_results = total_results / max(completed, 1)

        last_session = sessions[0] if sessions else None

        return {
            'total_sessions': len(sessions),
            'completed_sessions': completed,
            'failed_sessions': failed,
            'in_progress_sessions': in_progress,
            'total_results': total_results,
            'avg_results_per_session': round(avg_results, 1),
            'last_session': {
                'session_id': last_session.session_id,
                'status': last_session.status,
                'started_at': last_session.started_at,
                'results_count': len(last_session.results) if last_session.results else 0
            } if last_session else None
        }

    except Exception as e:
        logger.error(f"Error getting session analytics: {e}")
        return {}
```

#### 1.2 Add Profile Search (Optional - if needed by UI)

**Add Search Method** (after session methods):
```python
# ============================================================================
# PROFILE SEARCH
# ============================================================================

def search_profiles(
    self,
    query: str = None,
    filters: Dict[str, Any] = None,
    limit: int = 50
) -> List[UnifiedProfile]:
    """Search profiles by name, EIN, or other criteria"""
    try:
        all_profiles = []

        for profile_id in self.list_profiles():
            profile = self.get_profile(profile_id)
            if profile:
                all_profiles.append(profile)

        # Apply filters
        results = all_profiles

        # Text search on name and EIN
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if (p.organization_name and query_lower in p.organization_name.lower()) or
                   (p.ein and query in p.ein) or
                   (p.profile_id and query_lower in p.profile_id.lower())
            ]

        # Additional filters
        if filters:
            if 'ntee_codes' in filters:
                ntee_filter = set(filters['ntee_codes'])
                results = [
                    p for p in results
                    if p.ntee_codes and any(code in ntee_filter for code in p.ntee_codes)
                ]

            if 'state' in filters:
                state = filters['state']
                results = [
                    p for p in results
                    if p.geographic_scope and p.geographic_scope.states and state in p.geographic_scope.states
                ]

            if 'discovery_status' in filters:
                status = filters['discovery_status']
                results = [p for p in results if p.discovery_status == status]

        # Sort by last updated (newest first)
        results.sort(
            key=lambda x: x.updated_at or x.created_at or "1900-01-01",
            reverse=True
        )

        return results[:limit]

    except Exception as e:
        logger.error(f"Error searching profiles: {e}")
        return []
```

#### 1.3 Add Discovery Status Fields to Profile Model

**Update Profile Model** (`src/profiles/models.py`):
```python
# Add to UnifiedProfile class (around line 50-60)
discovery_status: Optional[str] = Field(
    default=None,
    description="Discovery status: in_progress, completed, failed"
)
last_discovery_at: Optional[str] = Field(
    default=None,
    description="Timestamp of last discovery session"
)
```

---

### STEP 2: Update Web Endpoints
**Files**: `src/web/routers/profiles.py`, `src/web/routers/discovery.py`
**Duration**: 2-3 hours

#### 2.1 Identify All ProfileService Usage

**Find all imports**:
```bash
grep -r "from.*profiles.*service import ProfileService" src/web/
grep -r "ProfileService()" src/web/
```

**Expected locations**:
- `src/web/routers/profiles.py` - Profile CRUD endpoints
- `src/web/routers/discovery.py` - Discovery endpoints
- `src/web/main.py` - Service initialization

#### 2.2 Update Imports

**Before**:
```python
from src.profiles.service import ProfileService
```

**After**:
```python
from src.profiles.unified_service import get_unified_profile_service
```

#### 2.3 Update Service Instantiation

**Before**:
```python
profile_service = ProfileService()
```

**After**:
```python
profile_service = get_unified_profile_service()
```

#### 2.4 Update Method Calls (if needed)

Most methods have same signature, but verify:
- Session management methods (new in UnifiedProfileService)
- Opportunity methods (now direct instead of via UnifiedOpportunityService)

---

### STEP 3: Data Migration Script
**File**: `src/profiles/migrate_to_unified.py` (NEW)
**Duration**: 2 hours

```python
"""
Profile Data Migration Script
Migrates from ProfileService structure to UnifiedProfileService structure
"""
import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfileMigration:
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.legacy_profiles_dir = self.data_dir / "profiles"
        self.legacy_sessions_dir = self.data_dir / "sessions"
        self.archive_dir = self.data_dir / "_archive_legacy"

    def migrate_all(self):
        """Run complete migration"""
        logger.info("Starting profile migration...")

        # 1. Backup existing data
        self.backup_data()

        # 2. Migrate profiles
        profiles_migrated = self.migrate_profiles()

        # 3. Migrate sessions
        sessions_migrated = self.migrate_sessions()

        # 4. Archive legacy data
        self.archive_legacy_data()

        logger.info(f"Migration complete: {profiles_migrated} profiles, {sessions_migrated} sessions")

    def backup_data(self):
        """Create backup of all profile data"""
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.data_dir / f"_backup_{timestamp}"

        logger.info(f"Creating backup at {backup_dir}")
        shutil.copytree(self.legacy_profiles_dir, backup_dir / "profiles")

        if self.legacy_sessions_dir.exists():
            shutil.copytree(self.legacy_sessions_dir, backup_dir / "sessions")

    def migrate_profiles(self) -> int:
        """Migrate profile files to new structure"""
        count = 0

        for profile_file in self.legacy_profiles_dir.glob("*.json"):
            try:
                # Read legacy profile
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                profile_id = data.get('profile_id') or profile_file.stem

                # Create new directory structure
                new_profile_dir = self.data_dir / profile_id
                new_profile_dir.mkdir(parents=True, exist_ok=True)

                # Add discovery status fields if missing
                if 'discovery_status' not in data:
                    data['discovery_status'] = None
                if 'last_discovery_at' not in data:
                    data['last_discovery_at'] = None

                # Add embedded analytics structure if missing
                if 'analytics' not in data:
                    data['analytics'] = {
                        'opportunity_count': 0,
                        'stages_distribution': {},
                        'scoring_stats': {},
                        'discovery_stats': {},
                        'promotion_stats': {}
                    }

                # Write to new location
                new_profile_file = new_profile_dir / "profile.json"
                with open(new_profile_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                logger.info(f"Migrated profile: {profile_id}")
                count += 1

            except Exception as e:
                logger.error(f"Error migrating {profile_file}: {e}")

        return count

    def migrate_sessions(self) -> int:
        """Migrate session files to new structure"""
        count = 0

        if not self.legacy_sessions_dir.exists():
            logger.info("No sessions directory to migrate")
            return 0

        for session_file in self.legacy_sessions_dir.glob("*.json"):
            try:
                # Read legacy session
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                profile_id = data.get('profile_id')
                session_id = data.get('session_id') or session_file.stem

                if not profile_id:
                    logger.warning(f"Session {session_id} has no profile_id, skipping")
                    continue

                # Create sessions directory for profile
                sessions_dir = self.data_dir / profile_id / "sessions"
                sessions_dir.mkdir(parents=True, exist_ok=True)

                # Write to new location
                new_session_file = sessions_dir / f"{session_id}.json"
                with open(new_session_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                logger.info(f"Migrated session: {session_id} for profile {profile_id}")
                count += 1

            except Exception as e:
                logger.error(f"Error migrating {session_file}: {e}")

        return count

    def archive_legacy_data(self):
        """Move legacy data to archive"""
        import shutil

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Archive legacy profiles
        if self.legacy_profiles_dir.exists():
            archive_profiles = self.archive_dir / "profiles"
            if archive_profiles.exists():
                shutil.rmtree(archive_profiles)
            shutil.move(str(self.legacy_profiles_dir), str(archive_profiles))
            logger.info("Archived legacy profiles")

        # Archive legacy sessions
        if self.legacy_sessions_dir.exists():
            archive_sessions = self.archive_dir / "sessions"
            if archive_sessions.exists():
                shutil.rmtree(archive_sessions)
            shutil.move(str(self.legacy_sessions_dir), str(archive_sessions))
            logger.info("Archived legacy sessions")

        # Archive locks directory (no longer needed)
        locks_dir = self.data_dir / "locks"
        if locks_dir.exists():
            archive_locks = self.archive_dir / "locks"
            if archive_locks.exists():
                shutil.rmtree(archive_locks)
            shutil.move(str(locks_dir), str(archive_locks))
            logger.info("Archived lock files")

if __name__ == "__main__":
    migrator = ProfileMigration()
    migrator.migrate_all()
```

---

### STEP 4: Testing & Validation
**Duration**: 2-3 hours

#### 4.1 Unit Tests

**Create**: `tests/profiles/test_unified_service_migration.py`
```python
import pytest
from src.profiles.unified_service import UnifiedProfileService

def test_discovery_session_lifecycle():
    """Test complete session lifecycle without locking"""
    service = UnifiedProfileService()

    # Start session
    session_id = service.start_discovery_session(
        profile_id="test_profile",
        tracks=["bmf", "propublica"]
    )
    assert session_id is not None

    # Verify session exists
    session = service.get_session(session_id)
    assert session.status == "in_progress"

    # Complete session
    success = service.complete_discovery_session(
        session_id,
        results=[{"org": "Test Org"}],
        summary={"count": 1}
    )
    assert success

    # Verify completion
    session = service.get_session(session_id)
    assert session.status == "completed"
    assert len(session.results) == 1

def test_profile_search():
    """Test profile search functionality"""
    service = UnifiedProfileService()

    results = service.search_profiles(
        query="united way",
        filters={'ntee_codes': ['P20']}
    )
    assert isinstance(results, list)

def test_session_analytics():
    """Test session analytics computation"""
    service = UnifiedProfileService()

    analytics = service.get_session_analytics("test_profile")
    assert 'total_sessions' in analytics
    assert 'avg_results_per_session' in analytics
```

#### 4.2 Integration Tests

**Test Web Endpoints**:
```bash
# Start server
python src/web/main.py

# Test profile creation
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"ein": "541026365", "organization_name": "Test Org"}'

# Test discovery session
curl -X POST http://localhost:8000/api/profiles/{profile_id}/discover \
  -H "Content-Type: application/json" \
  -d '{"tracks": ["bmf"]}'

# Verify session created
curl http://localhost:8000/api/profiles/{profile_id}/sessions
```

#### 4.3 Data Migration Validation

**Run migration**:
```bash
python src/profiles/migrate_to_unified.py
```

**Verify migration**:
```bash
# Check new structure exists
ls -la data/profiles/profile_*/profile.json
ls -la data/profiles/profile_*/sessions/

# Check archive created
ls -la data/profiles/_archive_legacy/

# Verify profile count matches
python -c "
from pathlib import Path
legacy = len(list(Path('data/profiles/_archive_legacy/profiles').glob('*.json')))
migrated = len(list(Path('data/profiles').glob('profile_*/profile.json')))
print(f'Legacy: {legacy}, Migrated: {migrated}')
assert legacy == migrated
"
```

---

### STEP 5: Deprecate ProfileService
**Duration**: 1 hour

#### 5.1 Move to Deprecated

```bash
# Create deprecated directory
mkdir -p src/profiles/_deprecated

# Move ProfileService
git mv src/profiles/service.py src/profiles/_deprecated/service_legacy.py

# Update file with deprecation notice
```

**Add to top of `src/profiles/_deprecated/service_legacy.py`**:
```python
"""
DEPRECATED: This service is deprecated as of Phase 8.
Use UnifiedProfileService instead (src/profiles/unified_service.py).

This file is kept for reference only and will be removed in Phase 9.
"""
import warnings
warnings.warn(
    "ProfileService is deprecated. Use UnifiedProfileService instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### 5.2 Update All Imports

**Search and replace across codebase**:
```bash
# Find all imports
grep -r "from.*profiles.service import" src/

# Replace with unified service
# Manual updates or:
find src/ -type f -name "*.py" -exec sed -i \
  's/from src.profiles.service import ProfileService/from src.profiles.unified_service import get_unified_profile_service/g' {} +
```

---

## Rollout Strategy

### Phase A: Preparation (Day 1, Morning)
1. ✅ Create feature audit (COMPLETE)
2. ✅ Create migration plan (COMPLETE)
3. ⏳ Add missing features to UnifiedProfileService
4. ⏳ Create data migration script
5. ⏳ Create unit tests

### Phase B: Migration (Day 1, Afternoon)
1. ⏳ Run data migration script on backup
2. ⏳ Verify migration results
3. ⏳ Run data migration on production data
4. ⏳ Archive legacy data

### Phase C: Code Updates (Day 2, Morning)
1. ⏳ Update web endpoint imports
2. ⏳ Update service instantiation
3. ⏳ Run integration tests
4. ⏳ Fix any compatibility issues

### Phase D: Cleanup (Day 2, Afternoon)
1. ⏳ Deprecate ProfileService
2. ⏳ Update documentation
3. ⏳ Final validation
4. ⏳ Commit changes

---

## Rollback Plan

**If migration fails**:

1. **Stop services**: Kill web server and any running processes
2. **Restore from backup**:
   ```bash
   # Find latest backup
   ls -la data/profiles/_backup_*

   # Restore
   cp -r data/profiles/_backup_TIMESTAMP/profiles data/profiles/
   cp -r data/profiles/_backup_TIMESTAMP/sessions data/profiles/
   ```
3. **Revert code changes**:
   ```bash
   git checkout src/profiles/service.py
   git checkout src/web/routers/
   ```
4. **Restart with legacy ProfileService**

---

## Success Criteria

### Functional Requirements ✅
- [ ] All profile CRUD operations working
- [ ] Discovery session management functional
- [ ] Session history preserved
- [ ] Profile search operational (if needed)
- [ ] Analytics computation accurate
- [ ] No data loss during migration

### Performance Requirements ✅
- [ ] Profile load time < 100ms
- [ ] Session creation < 50ms
- [ ] No locking overhead
- [ ] Analytics refresh < 200ms

### Code Quality Requirements ✅
- [ ] No locking complexity (100+ lines removed)
- [ ] All tests passing
- [ ] No deprecation warnings in logs
- [ ] Clean file structure (directory-based)

---

## Timeline Summary

**Total Duration**: 2 days (Week 9, Days 1-2)

| Day | Phase | Tasks | Hours |
|-----|-------|-------|-------|
| Day 1 AM | Preparation | Add features, migration script, tests | 4h |
| Day 1 PM | Migration | Run migration, verify, archive | 3h |
| Day 2 AM | Code Updates | Update endpoints, integration tests | 3h |
| Day 2 PM | Cleanup | Deprecate, document, validate | 2h |

**Total**: ~12 hours over 2 days

---

## Next Steps

After migration complete:
1. ✅ Move to Task 6: Integrate Tool 25 Profile Builder
2. ✅ Implement auto-population from web scraping
3. ✅ Add Smart URL Resolution to profile workflow
4. ✅ Continue with Week 9 NTEE validation tasks

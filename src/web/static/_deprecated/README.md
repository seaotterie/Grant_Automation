# Deprecated Frontend Code

This folder contains legacy frontend code that has been replaced or is no longer in use.

## Files

### profiles-store.js (261 lines)
- **Date Deprecated**: 2025-10-18
- **Reason**: Orphaned Alpine.js store implementation not loaded by index.html
- **Replaced By**: `modules/profiles-module.js` (Module Pattern)
- **Notes**: Alpine.js store pattern abandoned in favor of module pattern for better encapsulation

### profile-management.js (412 lines)
- **Date Deprecated**: 2025-10-18
- **Reason**: Orphaned class-based module only used by modular_test.html (deprecated test file)
- **Replaced By**: `modules/profiles-module.js` (Module Pattern)
- **Notes**: Class-based approach replaced with simpler function-based module pattern

## Why These Were Deprecated

During Phase 8-9 of the 12-factor tool transformation, we identified significant code duplication across three profile management implementations:

1. ✅ **profiles-module.js** (Active) - Primary implementation using Module Pattern
2. ❌ **profiles-store.js** (Deprecated) - Unused Alpine.js store
3. ❌ **profile-management.js** (Deprecated) - Unused class-based module

**Code Duplication**: ~65% of profile CRUD operations were duplicated across these files.

**Decision**: Standardize on Module Pattern (profiles-module.js) for:
- Better encapsulation
- Event-driven architecture
- Alpine.js compatibility
- Testability

## Architecture Decision

**Chosen Pattern**: Module Pattern (Function-based)

```javascript
function profilesModule() {
    return {
        profiles: [],
        async loadProfiles() { /* ... */ },
        async createProfile() { /* ... */ }
        // ...
    };
}
```

**Why Not Alpine Stores?**
- Global state management complexity
- Harder to debug (shared mutable state)
- Not integrated with existing architecture
- Requires significant refactoring

**Why Not Class-based?**
- More boilerplate
- Less idiomatic for Alpine.js components
- Overkill for current complexity level

## If You Need to Restore

These files are preserved in git history. To restore:

```bash
git checkout HEAD~1 -- src/web/static/js/stores/profiles-store.js
git checkout HEAD~1 -- src/web/static/js/modules/profile-management.js
```

## Related Documentation

- Code review report: See chat logs from 2025-10-18 (code-reviewer agent analysis)
- Architecture decision: See `docs/ARCHITECTURE.md` (if exists)
- Migration guide: Phase 8-9 transformation documentation in `CLAUDE.md`

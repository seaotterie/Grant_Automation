# Deprecated Web Routers

This directory contains older versions of web routers that have been superseded by v2 implementations.

## Deprecated Routers

### Future Candidates (pending verification):
- `profiles.py` (v1) → Use `profiles_v2.py` instead
- `discovery.py` (v1) → Use `discovery_v2.py` instead
- `discovery_legacy.py` → Use `discovery_v2.py` instead

## Migration Status

**Status**: Deprecation directories created, routers still active pending v2 verification

**Next Steps**:
1. Verify v2 routers are fully functional
2. Update `main.py` to only import v2 routers
3. Move v1 routers to this directory
4. Remove 4-tier code from `intelligence.py` (migrate to 2-tier only)

## Removal Timeline

- **Target**: Q1 2026 (after 3 months of v2 stability)
- **Condition**: All v2 endpoints verified operational

## See Also

- `docs/API_DOCUMENTATION.md` - Current API reference

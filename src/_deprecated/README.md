# Deprecated Code Archive

This directory contains code that has been superseded by the 12-factor tool architecture but is preserved for reference.

## Directory Structure

### `processors/`
**Status**: Deprecated - Replaced by 24 12-factor tools in `tools/` directory
**Migration**: Phase 1-8 (September-November 2025)

Original processor-based architecture replaced by stateless, single-responsibility tools.
See: `docs/TOOL_ARCHITECTURE_MAPPING.md` for tool replacements.

### `analysis/`
**Status**: Under Review - May be deprecated
**Reason**: Functionality migrated to specialized tools (Tool 2, Tool 12, Tool 21, etc.)

Large analysis modules that overlap with tool functionality.

### `scoring/`
**Status**: Under Review - May be deprecated
**Reason**: Functionality migrated to Tool 20 (Multi-Dimensional Scorer)

Scoring logic consolidated into unified multi-dimensional scoring tool.

### `intelligence/`
**Status**: Deprecated - Replaced by Tool 22
**Reason**: Historical funding analysis now in Tool 22 (Historical Funding Analyzer)

## Timeline

- **Phase 1-2** (Sep 2025): Two-tool pipeline operational
- **Phase 3-4** (Oct 2025): Supporting tools complete
- **Phase 5-6** (Oct 2025): Scoring & reporting tools
- **Phase 7** (Nov 2025): Validation & compliance audit
- **Phase 8** (Nov 2025): Workflow solidification

## Migration Status

- ✅ Tool 1 (Opportunity Screening) → Replaces: ai_lite_unified, ai_heavy_light
- ✅ Tool 2 (Deep Intelligence) → Replaces: ai_heavy_deep, ai_heavy_researcher, 4 tier processors
- ✅ Tool 10-13 (Intelligence Tools) → Replaces: analysis modules
- ✅ Tool 20 (Multi-Dimensional Scorer) → Replaces: scoring modules
- ✅ Tool 22 (Historical Funding) → Replaces: intelligence/historical_funding_analyzer.py

## Preservation Rationale

Code is preserved rather than deleted for:
1. Historical reference
2. Algorithm verification
3. Potential edge case handling
4. Migration rollback capability (if needed)

## Removal Timeline

These directories are candidates for complete removal in:
- **Q1 2026**: After 6 months of tool architecture stability
- **Condition**: No critical issues identified with tool replacements

## See Also

- `docs/MIGRATION_HISTORY.md` - Complete transformation timeline
- `docs/TOOL_ARCHITECTURE_MAPPING.md` - Processor → Tool mapping
- `docs/12-FACTOR_COMPLIANCE_MATRIX.md` - Tool compliance details

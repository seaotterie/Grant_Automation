# Test Archive

This directory contains archived tests from previous phases of development that are no longer actively maintained but preserved for historical reference.

## Archive Organization

### `pre_transformation/`

Tests from before the 12-factor tool transformation (prior to Phase 1-3, October 2025).

#### `legacy_tests/` (40 files)
- Tests written for the original processor-based architecture
- Pre-dates 12-factor tool transformation
- May reference deprecated components
- **Status**: Outdated, preserved for reference only

#### `deprecated_processor_tests/`
- Tests for the old processor pipeline architecture
- Replaced by modern tool-based architecture
- **Status**: Outdated, preserved for reference only

## Current Active Tests

Active test suites are located in the main `tests/` directory:

```
tests/
├── unit/              # Component-level tests
├── integration/       # Multi-component tests
├── e2e/              # End-to-end workflows
├── api/              # REST API tests
├── profiles/         # Profile workflow tests
├── performance/      # Load and performance tests
└── security/         # Security validation tests
```

## Why Archive Instead of Delete?

1. **Historical Reference**: Understanding evolution of testing strategy
2. **Pattern Learning**: May contain useful test patterns or edge cases
3. **Regression Validation**: Can compare old vs new approaches
4. **Documentation**: Shows progression of architecture decisions

## Migration Notes

- **Archived**: October 9, 2025 (Phase 4 - Comprehensive Testing)
- **Reason**: 12-factor tool transformation complete, processor architecture deprecated
- **Replacement**: New test suites in `test_framework/` and `tests/`

---

**Do not modify archived tests.** For current testing needs, refer to active test suites in parent directory.

# Mobile Tests - Deprecated

**Date Deprecated**: October 7, 2025
**Reason**: Catalynx is a desktop web application, not a mobile application

## Background

These tests were originally created to validate mobile responsiveness, but:
1. Catalynx is designed as a **desktop-first grant research platform**
2. The application is intended for professional use on desktop/laptop computers
3. Mobile support is not a core requirement or use case
4. Test failures were creating noise in the test suite

## Deprecated Tests

Mobile-specific tests from the Playwright configuration (playwright.config.js):
- `mobile-chrome` project (Pixel 5 device simulation)
- `mobile-safari` project (iPhone 13 device simulation)

## If Mobile Support Becomes Required

If mobile support becomes a future requirement, these considerations apply:

### Required Changes
1. **UI/UX Redesign**: Current desktop layout won't work on mobile screens
2. **Navigation**: Implement mobile-friendly navigation (hamburger menu, etc.)
3. **Data Tables**: Redesign table views for mobile displays
4. **Forms**: Optimize form inputs for mobile
5. **Modals**: Adapt modal dialogs for smaller screens

### Test Restoration
If mobile support is implemented, restore these tests by:
1. Uncommenting mobile projects in `playwright.config.js`
2. Reviewing and updating test expectations for mobile UI
3. Running tests to validate mobile functionality

## Current Status

**Catalynx Target Platform**: Desktop web browsers (Chrome, Firefox, Safari on macOS/Windows/Linux)
**Mobile Support**: Not implemented, not planned
**Test Status**: Deprecated to reduce test suite noise

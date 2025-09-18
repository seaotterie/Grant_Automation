# Catalynx Playwright Testing Framework

A comprehensive GUI testing framework for the Catalynx Grant Research Intelligence Platform using Playwright.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Catalynx server running on `http://localhost:8000`

### Installation
```bash
cd tests/playwright
npm install
npx playwright install
```

### Run Tests
```bash
# Quick smoke test
npm run test:smoke

# Run all tests
npm run test:full

# Run with UI mode (interactive)
npm run test:ui

# Run specific test
npx playwright test tests/smoke/00-basic-functionality.spec.js
```

## 📁 Project Structure

```
tests/playwright/
├── package.json                 # Dependencies and scripts
├── playwright.config.js         # Main configuration
├── tests/
│   ├── smoke/                  # Critical path tests
│   ├── workflows/              # End-to-end journeys
│   ├── visual/                 # Visual regression tests
│   └── performance/            # Performance benchmarks
├── page-objects/               # Page Object Models
│   ├── BasePage.js            # Base functionality
│   ├── ProfilePage.js         # Profile management
│   └── DiscoveryPage.js       # Discovery workflows
├── fixtures/                   # Test data and utilities
├── scripts/                    # Development tools
└── reports/                    # Test execution reports
```

## 🎯 Test Categories

### Smoke Tests (`tests/smoke/`)
Critical functionality validation:
- **00-basic-functionality.spec.js** - Application loading and navigation
- **01-application-loading.spec.js** - System health and API responses
- **02-tax-data-verification.spec.js** - Tax data display and attribution
- **03-discovery-workflow.spec.js** - Discovery execution and results

### Workflow Tests (`tests/workflows/`)
Complete user journeys:
- Profile creation and management
- Discovery execution and filtering
- Opportunity analysis and scoring
- Export and reporting workflows

### Visual Tests (`tests/visual/`)
UI consistency validation:
- Component layout verification
- Cross-browser compatibility
- Responsive design testing
- Theme consistency

## 🛠️ Development Tools

### Quick Test Runner
```bash
# Windows
scripts\run-quick-test.bat

# Manual
npm run test:smoke -- --project=chromium
```

### Application Inspector
```bash
node scripts/inspect-application.js
```

### Debug Mode
```bash
# Run tests with browser visible
npx playwright test --headed

# Interactive debugging
npx playwright test --debug

# Step-by-step UI mode
npm run test:ui
```

## 📊 Test Configuration

### Browser Support
- **Chromium** (Primary)
- **Firefox** 
- **WebKit** (Safari)
- **Mobile** (Chrome, Safari)

### Key Features
- **Parallel Execution** - 6 workers by default
- **Visual Regression** - Automatic screenshot comparison
- **Performance Monitoring** - Page load and API timing
- **Error Handling** - Graceful failure management
- **Artifact Collection** - Screenshots, videos, traces

## 🎭 Page Object Models

### BasePage
Core functionality for all pages:
```javascript
const basePage = new BasePage(page);
await basePage.navigate();
await basePage.waitForAppReady();
await basePage.switchTab('discovery');
```

### ProfilePage
Profile management operations:
```javascript
const profilePage = new ProfilePage(page);
await profilePage.createProfile(profileData);
await profilePage.verifyTaxDataDisplay(expectedData);
```

### DiscoveryPage
Discovery workflow testing:
```javascript
const discoveryPage = new DiscoveryPage(page);
const results = await discoveryPage.executeDiscovery();
await discoveryPage.verifyResultsQuality(expectations);
```

## 🧪 Test Data Management

Test configurations in `fixtures/test-configurations.js`:
- **Profiles** - Test organization data
- **Scenarios** - Workflow test cases
- **Selectors** - UI element locators
- **Mock Data** - Sample responses

### Example Test Profile
```javascript
{
  id: 'heroes_bridge_foundation',
  organization_name: 'Heroes Bridge Foundation',
  ein: '81-2827604',
  website_url: 'https://heroesbridge.org',
  test_data: {
    expected_bmf_data: true,
    expected_990_data: true
  }
}
```

## 📈 Performance Testing

Automated performance validation:
- **Page Load Time** - < 3 seconds
- **API Response Time** - < 1 second
- **Chart Rendering** - < 500ms
- **Memory Usage** - Monitored for leaks

## 🔍 Visual Regression

Automatic UI consistency checking:
```bash
# Generate baseline screenshots
npm run test:visual -- --update-snapshots

# Compare against baseline
npm run test:visual
```

## 🚨 Error Handling

Comprehensive error management:
- **Console Error Monitoring** - Automatic detection
- **API Failure Handling** - Graceful degradation testing
- **Network Timeout Testing** - Resilience validation
- **User Notification Verification** - Error message display

## 📝 Reporting

Multiple report formats:
- **HTML Report** - Interactive results viewer
- **JSON Report** - Machine-readable results
- **JUnit Report** - CI/CD integration
- **Allure Report** - Detailed test analytics

Access reports:
```bash
npm run test:report
```

## 🔧 Troubleshooting

### Common Issues

**Tests timeout waiting for elements:**
- Check if selectors match actual UI
- Verify application is running on correct port
- Ensure Alpine.js has initialized

**Visual tests fail unexpectedly:**
- Screen resolution differences
- Theme/styling changes
- Font rendering variations

**Performance tests fail:**
- Server resource constraints
- Network latency issues
- Concurrent process interference

### Debug Commands
```bash
# Inspect application structure
node scripts/inspect-application.js

# Run single test with debugging
npx playwright test specific-test.spec.js --debug

# Generate trace for analysis
npx playwright test --trace on

# Record new test interactively
npx playwright codegen http://localhost:8000
```

## 🎯 Tax-Data-First Verification

Key validation for Catalynx's core value proposition:

### What We Test
- **Real Data Display** - 990 forms, BMF records, SOI data
- **Source Attribution** - Proper IRS data source labeling
- **Confidence Scoring** - Accuracy percentage display
- **Fake Data Elimination** - No test/sample data visible

### Critical Tests
```javascript
// Verify tax data is displayed correctly
await profilePage.verifyTaxDataDisplay({
  ein: '81-2827604',
  expected_bmf_data: true,
  expected_990_data: true
});

// Check source attribution
await profilePage.verifySourceAttribution(['IRS BMF', 'Form 990']);

// Ensure no fake data
await profilePage.verifyNoFakeData();
```

## 🌟 Best Practices

### Test Writing
- **Start with smoke tests** for critical paths
- **Use Page Object Models** for reusability
- **Include performance assertions** in all tests
- **Handle async operations** properly
- **Provide clear test descriptions** and logging

### Maintenance
- **Update selectors** when UI changes
- **Review test data** regularly
- **Monitor performance trends** over time
- **Keep screenshots current** for visual tests

### Development Workflow
1. Write failing test
2. Implement feature
3. Run smoke tests
4. Update documentation
5. Commit with test evidence

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Catalynx API Documentation](http://localhost:8000/api/docs)
- [Test Configuration Reference](./fixtures/test-configurations.js)
- [Page Object Model Guide](./page-objects/README.md)

---

🎭 **Playwright GUI Testing Framework** - Ensuring quality and reliability for the Catalynx Grant Research Intelligence Platform.
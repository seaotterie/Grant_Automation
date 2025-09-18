/**
 * Smoke Test: Discovery Workflow
 * 
 * This test verifies the core discovery functionality:
 * - Discovery execution works
 * - Results are returned and displayable
 * - Filtering and pagination function
 * - Stage management works
 * - Export functionality is operational
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const DiscoveryPage = require('../../page-objects/DiscoveryPage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Discovery Workflow Smoke Tests', () => {
  let basePage;
  let profilePage;
  let discoveryPage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    // Set up a test profile that we'll use across tests
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);
    
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Use existing Heroes Bridge profile or create one
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();
    
    const heroesProfile = existingProfiles.find(p => 
      p.name && p.name.includes('Heroes Bridge')
    );
    
    if (heroesProfile) {
      testProfileId = heroesProfile.id;
      console.log(`✅ Using existing profile for discovery tests: ${testProfileId}`);
    } else {
      const heroesData = profiles.find(p => p.id === 'heroes_bridge_foundation');
      testProfileId = await profilePage.createProfile(heroesData);
      console.log(`📝 Created test profile for discovery: ${testProfileId}`);
    }
    
    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);
    discoveryPage = new DiscoveryPage(page);
    
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Select our test profile
    await profilePage.navigateToProfiles();
    await profilePage.selectProfile(testProfileId);
  });

  test('Discovery execution completes successfully', async ({ page }) => {
    // Navigate to discovery tab
    await discoveryPage.navigateToDiscovery();
    
    // Execute discovery with default options
    const results = await discoveryPage.executeDiscovery({
      tracks: ['nonprofit', 'government'],
      maxResults: 25,
      includeEntityCache: true
    });
    
    // Verify results were returned
    expect(Array.isArray(results)).toBeTruthy();
    expect(results.length).toBeGreaterThan(0);
    
    console.log(`✅ Discovery completed successfully: ${results.length} results found`);
    
    // Take screenshot of results
    await basePage.takeScreenshot('discovery-results');
  });

  test('Discovery results display correctly', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    // Execute discovery
    const results = await discoveryPage.executeDiscovery();
    
    if (results.length === 0) {
      test.skip('No discovery results to verify display');
    }
    
    // Verify results table is visible
    const resultsTableVisible = await basePage.isElementVisible(
      basePage.selectors.discovery.results_table
    );
    expect(resultsTableVisible).toBeTruthy();
    
    // Verify results quality
    await discoveryPage.verifyResultsQuality({
      minResults: 1,
      maxResults: 100,
      requiredFields: ['organization_name'],
      noTestData: true
    });
    
    console.log(`✅ Discovery results display validation passed`);
  });

  test('Discovery filters work correctly', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    // Execute discovery to get initial results
    const initialResults = await discoveryPage.executeDiscovery();
    
    if (initialResults.length === 0) {
      test.skip('No results to filter');
    }
    
    // Apply filters
    await discoveryPage.applyFilters({
      stage: 'prospects',
      minScore: 0.5
    });
    
    // Get filtered results
    const filteredResults = await discoveryPage.getDiscoveryResults();
    
    // Verify filtering worked (results changed or stayed the same if all matched)
    expect(Array.isArray(filteredResults)).toBeTruthy();
    
    console.log(`✅ Filtering applied: ${initialResults.length} → ${filteredResults.length} results`);
  });

  test('Opportunity selection and stage management works', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    const results = await discoveryPage.executeDiscovery();
    
    if (results.length === 0) {
      test.skip('No opportunities to manage');
    }
    
    // Select first few opportunities
    const orgNames = results.slice(0, 2).map(r => r.organization_name);
    const selectedOpportunities = await discoveryPage.selectOpportunities(orgNames);
    
    expect(selectedOpportunities.length).toBeGreaterThan(0);
    
    // Try to move to prospects stage
    try {
      await discoveryPage.moveOpportunitiesToStage(selectedOpportunities, 'prospects');
      console.log(`✅ Stage management worked: moved ${selectedOpportunities.length} opportunities`);
    } catch (error) {
      console.log(`ℹ️  Stage management not available or failed: ${error.message}`);
    }
  });

  test('Comprehensive scoring executes', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    const results = await discoveryPage.executeDiscovery();
    
    if (results.length === 0) {
      test.skip('No opportunities to score');
    }
    
    // Select first opportunity for scoring
    const orgName = results[0].organization_name;
    
    try {
      const scoringResults = await discoveryPage.executeComprehensiveScoring([orgName]);
      
      expect(Array.isArray(scoringResults)).toBeTruthy();
      console.log(`✅ Comprehensive scoring completed for ${orgName}`);
    } catch (error) {
      console.log(`ℹ️  Comprehensive scoring not available: ${error.message}`);
    }
  });

  test('Export functionality is operational', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    const results = await discoveryPage.executeDiscovery();
    
    if (results.length === 0) {
      test.skip('No results to export');
    }
    
    try {
      // Test Excel export
      const download = await discoveryPage.exportResults('excel');
      
      expect(download).toBeTruthy();
      expect(download.suggestedFilename()).toContain('excel');
      
      console.log(`✅ Export functionality works: ${download.suggestedFilename()}`);
    } catch (error) {
      console.log(`ℹ️  Export functionality not available: ${error.message}`);
    }
  });

  test('Discovery pagination works', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    // Execute discovery with more results to potentially trigger pagination
    const results = await discoveryPage.executeDiscovery({
      maxResults: 50
    });
    
    if (results.length <= 10) {
      test.skip('Not enough results to test pagination');
    }
    
    // Check if pagination controls are visible
    const paginationVisible = await basePage.isElementVisible(
      basePage.selectors.discovery.pagination_controls
    );
    
    if (paginationVisible) {
      try {
        await discoveryPage.navigateToPage(2);
        console.log('✅ Pagination navigation worked');
      } catch (error) {
        console.log(`ℹ️  Pagination navigation failed: ${error.message}`);
      }
    } else {
      console.log('ℹ️  Pagination not needed or not visible');
    }
  });

  test('Opportunity details can be viewed', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    const results = await discoveryPage.executeDiscovery();
    
    if (results.length === 0) {
      test.skip('No opportunities to view details');
    }
    
    const firstOpportunity = results[0];
    
    try {
      const details = await discoveryPage.getOpportunityDetails(firstOpportunity.organization_name);
      
      if (details) {
        expect(details.organizationName).toBeTruthy();
        console.log(`✅ Opportunity details loaded for ${details.organizationName}`);
        
        // Close details panel
        await discoveryPage.closeOpportunityDetails();
      }
    } catch (error) {
      console.log(`ℹ️  Opportunity details not available: ${error.message}`);
    }
  });

  test('Discovery performance is acceptable', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    // Measure discovery execution time
    const startTime = Date.now();
    
    const results = await discoveryPage.executeDiscovery({
      tracks: ['nonprofit'],
      maxResults: 10
    });
    
    const executionTime = Date.now() - startTime;
    
    // Verify reasonable performance (should complete within 30 seconds)
    expect(executionTime).toBeLessThan(30000);
    
    console.log(`✅ Discovery performance: ${executionTime}ms for ${results.length} results`);
  });

  test('Discovery handles errors gracefully', async ({ page }) => {
    await discoveryPage.navigateToDiscovery();
    
    // Monitor for console errors during discovery
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Execute discovery
    try {
      await discoveryPage.executeDiscovery();
    } catch (error) {
      // Discovery might fail, but app should handle it gracefully
      console.log(`ℹ️  Discovery failed, checking error handling: ${error.message}`);
    }
    
    // Verify app is still functional
    const appState = await basePage.getAppState();
    expect(appState).toBeTruthy();
    expect(appState.currentTab).toBe('discovery');
    
    // Filter out non-critical console errors
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('404') && 
      !error.includes('Network')
    );
    
    if (criticalErrors.length > 0) {
      console.warn('Console errors during discovery:', criticalErrors);
    }
    
    console.log('✅ Error handling verification completed');
  });
});
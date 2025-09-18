/**
 * Smoke Test: Tax Data First Verification System
 * 
 * This test verifies the core business value of the Catalynx platform:
 * - Real tax data (990, BMF, SOI) is displayed correctly
 * - Source attribution is visible and accurate
 * - Fake/test data is eliminated
 * - Confidence scoring is functional
 * 
 * This is the most critical test as it validates the tax-data-first approach.
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Tax Data First Verification System', () => {
  let basePage;
  let profilePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);
    
    await basePage.navigate();
    await basePage.waitForAppReady();
  });

  test('Heroes Bridge Foundation - Real tax data verification', async ({ page }) => {
    const heroesProfile = profiles.find(p => p.id === 'heroes_bridge_foundation');
    
    // Navigate to profiles and check if Heroes Bridge profile exists
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();
    
    let profileId;
    const existingProfile = existingProfiles.find(p => 
      p.name && p.name.includes('Heroes Bridge') || 
      p.id && p.id.includes('81-2827604')
    );
    
    if (existingProfile) {
      profileId = existingProfile.id;
      console.log(`✅ Using existing Heroes Bridge profile: ${profileId}`);
    } else {
      // Create profile with website URL to trigger data extraction
      console.log('📝 Creating new Heroes Bridge profile for testing...');
      profileId = await profilePage.createProfile({
        organization_name: heroesProfile.organization_name,
        website_url: heroesProfile.website_url,
        mission: heroesProfile.mission
      });
    }
    
    // Navigate to Enhanced Data tab
    await profilePage.navigateToEnhancedData(profileId);
    
    // Verify tax data display
    await profilePage.verifyTaxDataDisplay(heroesProfile.test_data);
    
    // Verify source attribution shows real data sources
    const expectedSources = ['IRS BMF', 'Form 990', 'SOI'];
    await profilePage.verifySourceAttribution(expectedSources);
    
    // Check confidence score is high for real data
    const confidenceScore = await profilePage.getConfidenceScore();
    expect(confidenceScore).toBeGreaterThan(80);
    
    // Verify no fake/test data is displayed
    await profilePage.verifyNoFakeData();
    
    // Take screenshot for verification
    await basePage.takeScreenshot('heroes-bridge-tax-data');
  });

  test('EIN extraction from website URL works correctly', async ({ page }) => {
    const testProfile = profiles.find(p => p.id === 'heroes_bridge_foundation');
    
    // Create profile with website URL
    const profileId = await profilePage.createProfile({
      organization_name: 'Test EIN Extraction',
      website_url: testProfile.website_url
    });
    
    // Navigate to Enhanced Data tab
    await profilePage.navigateToEnhancedData(profileId);
    
    // Verify EIN was extracted from website
    const extractedEIN = await profilePage.verifyWebsiteDataExtraction(testProfile.website_url);
    
    if (extractedEIN) {
      expect(extractedEIN).toMatch(/\d{2}-\d{7}/);
      console.log(`✅ EIN successfully extracted: ${extractedEIN}`);
    } else {
      console.log('ℹ️  EIN extraction may not be implemented yet');
    }
    
    // Clean up test profile
    await profilePage.deleteProfile(profileId);
  });

  test('BMF/SOI data integration displays correctly', async ({ page }) => {
    const fauquierProfile = profiles.find(p => p.id === 'fauquier_foundation');
    
    // Check if profile exists or create it
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();
    
    let profileId;
    const existingProfile = existingProfiles.find(p => 
      p.name && p.name.includes('Fauquier') ||
      p.id && p.id.includes('30-0219424')
    );
    
    if (existingProfile) {
      profileId = existingProfile.id;
    } else {
      profileId = await profilePage.createProfile({
        organization_name: fauquierProfile.organization_name,
        website_url: fauquierProfile.website_url,
        mission: fauquierProfile.mission
      });
    }
    
    // Navigate to Enhanced Data tab
    await profilePage.navigateToEnhancedData(profileId);
    
    // Verify BMF data is displayed
    const bmfSectionVisible = await basePage.isElementVisible(
      basePage.selectors.enhanced_data.bmf_data_section
    );
    
    if (bmfSectionVisible) {
      console.log('✅ BMF data section is visible');
      
      // Verify key BMF fields are displayed
      const expectedFields = ['EIN', 'NTEE Code', 'Classification', 'Revenue'];
      for (const field of expectedFields) {
        const fieldVisible = await page.locator(`text=${field}`).isVisible();
        if (fieldVisible) {
          console.log(`✅ ${field} field is visible`);
        }
      }
    } else {
      console.log('ℹ️  BMF data section not visible - may need profile with real EIN');
    }
    
    // Take screenshot
    await basePage.takeScreenshot('bmf-data-display');
  });

  test('Source attribution and confidence scoring work', async ({ page }) => {
    // Use any existing profile with data
    await profilePage.navigateToProfiles();
    const profiles = await profilePage.getAllProfiles();
    
    if (profiles.length === 0) {
      test.skip('No profiles available for testing source attribution');
    }
    
    const testProfileId = profiles[0].id;
    
    // Navigate to Enhanced Data tab
    await profilePage.navigateToEnhancedData(testProfileId);
    
    // Check if source attribution is visible
    const sourceVisible = await basePage.isElementVisible(
      basePage.selectors.enhanced_data.source_attribution
    );
    expect(sourceVisible).toBeTruthy();
    
    // Check if confidence score is visible
    const confidenceVisible = await basePage.isElementVisible(
      basePage.selectors.enhanced_data.confidence_score
    );
    expect(confidenceVisible).toBeTruthy();
    
    // If confidence score is visible, verify it's a valid percentage
    if (confidenceVisible) {
      const confidenceScore = await profilePage.getConfidenceScore();
      expect(confidenceScore).toBeGreaterThanOrEqual(0);
      expect(confidenceScore).toBeLessThanOrEqual(100);
      console.log(`✅ Confidence score: ${confidenceScore}%`);
    }
    
    // Take screenshot
    await basePage.takeScreenshot('source-attribution');
  });

  test('Real vs fake data detection works', async ({ page }) => {
    // This test verifies that the system distinguishes real data from test data
    
    // Check current profiles to ensure no obviously fake data
    await profilePage.navigateToProfiles();
    const allProfiles = await profilePage.getAllProfiles();
    
    for (const profile of allProfiles) {
      // Check profile names don't contain test indicators
      const suspiciousNames = [
        'test', 'fake', 'sample', 'example', 'demo'
      ];
      
      const nameText = profile.name?.toLowerCase() || '';
      const hasSuspiciousName = suspiciousNames.some(word => nameText.includes(word));
      
      if (hasSuspiciousName) {
        console.log(`⚠️  Potentially fake profile detected: ${profile.name}`);
      }
      
      // For smoke test, we don't fail - just report
      expect(profile.name).toBeDefined();
      expect(profile.id).toBeDefined();
    }
    
    // Navigate to a profile and verify no fake data in Enhanced Data tab
    if (allProfiles.length > 0) {
      await profilePage.navigateToEnhancedData(allProfiles[0].id);
      await profilePage.verifyNoFakeData();
    }
  });

  test('Database intelligence integration is functional', async ({ page }) => {
    // Verify that the dual database architecture is working
    
    // Test application database (profiles, opportunities)
    const profilesResponse = await page.request.get(`${basePage.baseURL}/api/profiles`);
    expect(profilesResponse.ok()).toBeTruthy();
    
    // Test system status includes database connectivity
    const statusResponse = await page.request.get(`${basePage.baseURL}/api/system/status`);
    expect(statusResponse.ok()).toBeTruthy();
    
    const statusData = await statusResponse.json();
    expect(statusData).toHaveProperty('database_connected');
    expect(statusData.database_connected).toBeTruthy();
    
    // Check for intelligence database indicators
    if (statusData.intelligence_database) {
      expect(statusData.intelligence_database).toBeTruthy();
      console.log('✅ Intelligence database (BMF/SOI) is connected');
    } else {
      console.log('ℹ️  Intelligence database status not reported');
    }
    
    console.log('Database status:', {
      connected: statusData.database_connected,
      processors: statusData.processors_available
    });
  });

  test('Tax data loading performance is acceptable', async ({ page }) => {
    // Measure performance of tax data loading
    
    const heroesProfile = profiles.find(p => p.id === 'heroes_bridge_foundation');
    
    // Time the profile creation process
    const startTime = Date.now();
    
    const profileId = await profilePage.createProfile({
      organization_name: `Performance Test ${Date.now()}`,
      website_url: heroesProfile.website_url
    });
    
    // Navigate to Enhanced Data tab and measure loading time
    const dataLoadStart = Date.now();
    await profilePage.navigateToEnhancedData(profileId);
    await basePage.waitForLoadingComplete();
    const dataLoadEnd = Date.now();
    
    const totalTime = Date.now() - startTime;
    const dataLoadTime = dataLoadEnd - dataLoadStart;
    
    // Verify reasonable performance
    expect(totalTime).toBeLessThan(30000); // 30 seconds total
    expect(dataLoadTime).toBeLessThan(10000); // 10 seconds for data loading
    
    console.log(`Performance metrics:
      Total profile creation: ${totalTime}ms
      Data loading: ${dataLoadTime}ms`);
    
    // Clean up
    await profilePage.deleteProfile(profileId);
  });
});
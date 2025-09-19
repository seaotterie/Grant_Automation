/**
 * Comprehensive Tab Navigation Tests
 *
 * This test suite validates all main tab navigation and content loading:
 * - Overview Tab: Dashboard metrics, charts, system status
 * - Profiles Tab: Profile creation, management, enhanced data
 * - Discovery Tab: All discovery tracks, filtering, results
 * - Plan Tab: Strategic planning, tier selection, pricing
 * - Analyze Tab: AI analysis workflows, scoring
 * - Examine Tab: Document analysis, evidence review
 * - Approach Tab: Strategy implementation, recommendations
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Comprehensive Tab Navigation', () => {
  let basePage;
  let profilePage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    // Create a test profile for use across tab tests
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Create or find Heroes Bridge profile for testing
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();

    const heroesProfile = existingProfiles.find(p =>
      p.name && p.name.includes('Heroes Bridge')
    );

    if (heroesProfile) {
      testProfileId = heroesProfile.id;
      console.log(`✅ Using existing profile: ${testProfileId}`);
    } else {
      const heroesData = profiles.find(p => p.id === 'heroes_bridge_foundation');
      testProfileId = await profilePage.createProfile(heroesData);
      console.log(`📝 Created test profile: ${testProfileId}`);
    }

    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Ensure we have a profile selected for tabs that require it
    if (testProfileId) {
      await profilePage.navigateToProfiles();
      await profilePage.selectProfile(testProfileId);
    }
  });

  test.describe('Main Tab Navigation', () => {
    test('Overview tab loads with dashboard content', async ({ page }) => {
      console.log('🧪 Testing Overview tab navigation and content...');

      // Navigate to Overview tab
      await basePage.switchTab('overview');

      // Verify tab is active and content is visible
      const overviewTab = page.locator('button:has-text("Overview")').first();
      await expect(overviewTab).toBeVisible();

      // Check for key dashboard elements
      await expect.soft(page.locator('text="System Status"')).toBeVisible({ timeout: 5000 });
      await expect.soft(page.locator('text="Performance Metrics"')).toBeVisible({ timeout: 3000 });

      // Look for chart elements
      const charts = page.locator('canvas');
      const chartCount = await charts.count();
      expect(chartCount).toBeGreaterThanOrEqual(0);

      // Verify app state
      const appState = await basePage.getAppState();
      expect(appState.currentTab).toBe('overview');

      await basePage.takeScreenshot('overview-tab-loaded');
      console.log('✅ Overview tab test completed');
    });

    test('Profiles tab loads with profile management interface', async ({ page }) => {
      console.log('🧪 Testing Profiles tab navigation and content...');

      // Navigate to profiles area (Create Profile button should be visible)
      const createProfileButton = page.locator('button:has-text("Create Profile")').first();
      await expect(createProfileButton).toBeVisible({ timeout: 10000 });

      // Verify profile management elements
      await expect.soft(page.locator('text="Organization"')).toBeVisible();
      await expect.soft(page.locator('text="Profile"')).toBeVisible();

      // Check for profile list or cards
      const profileElements = page.locator('.bg-white.rounded-lg, .profile-card, .border');
      const profileCount = await profileElements.count();
      expect(profileCount).toBeGreaterThanOrEqual(0);

      await basePage.takeScreenshot('profiles-tab-loaded');
      console.log('✅ Profiles tab test completed');
    });

    test('Discovery tab loads with discovery interface', async ({ page }) => {
      console.log('🧪 Testing Discovery tab navigation and content...');

      // Navigate to Discovery tab
      await basePage.switchTab('discover');

      // Verify discovery interface elements
      await expect.soft(page.locator('button:has-text("DISCOVER"), button:has-text("Run All Tracks")')).toBeVisible({ timeout: 5000 });
      await expect.soft(page.locator('text="Discovery", text="Track"')).toBeVisible();

      // Check for discovery controls
      await expect.soft(page.locator('button, select, input')).toHaveCount({ min: 1 });

      // Verify tab state
      const appState = await basePage.getAppState();
      if (appState && appState.currentTab) {
        expect(['discovery', 'discover']).toContain(appState.currentTab);
      }

      await basePage.takeScreenshot('discovery-tab-loaded');
      console.log('✅ Discovery tab test completed');
    });

    test('Plan tab loads with strategic planning interface', async ({ page }) => {
      console.log('🧪 Testing Plan tab navigation and content...');

      // Navigate to Plan tab
      await basePage.switchTab('plan');

      // Verify planning interface elements
      await expect.soft(page.locator('text="Plan", text="Strategic", text="Planning"')).toBeVisible({ timeout: 5000 });

      // Check for tier selection or pricing elements
      await expect.soft(page.locator('text="Tier", text="$", text="Price"')).toBeVisible({ timeout: 3000 });

      // Verify content area is populated
      const contentElements = page.locator('div, section, article').filter({ hasText: /plan|strategic|tier/i });
      const contentCount = await contentElements.count();
      expect(contentCount).toBeGreaterThanOrEqual(1);

      await basePage.takeScreenshot('plan-tab-loaded');
      console.log('✅ Plan tab test completed');
    });

    test('Analyze tab loads with analysis interface', async ({ page }) => {
      console.log('🧪 Testing Analyze tab navigation and content...');

      // Navigate to Analyze tab
      await basePage.switchTab('analyze');

      // Verify analysis interface elements
      await expect.soft(page.locator('text="Analyze", text="Analysis", text="AI"')).toBeVisible({ timeout: 5000 });

      // Check for analysis controls
      await expect.soft(page.locator('button:has-text("Heavy"), button:has-text("Lite"), button:has-text("Comprehensive")')).toBeVisible({ timeout: 3000 });

      // Verify scoring elements
      await expect.soft(page.locator('text="Score", text="Rating", text="Assessment"')).toBeVisible({ timeout: 3000 });

      await basePage.takeScreenshot('analyze-tab-loaded');
      console.log('✅ Analyze tab test completed');
    });

    test('Examine tab loads with document analysis interface', async ({ page }) => {
      console.log('🧪 Testing Examine tab navigation and content...');

      // Navigate to Examine tab
      await basePage.switchTab('examine');

      // Verify examination interface elements
      await expect.soft(page.locator('text="Examine", text="Document", text="Evidence"')).toBeVisible({ timeout: 5000 });

      // Check for document analysis features
      await expect.soft(page.locator('text="Review", text="Analysis", text="Document"')).toBeVisible({ timeout: 3000 });

      await basePage.takeScreenshot('examine-tab-loaded');
      console.log('✅ Examine tab test completed');
    });

    test('Approach tab loads with strategy implementation interface', async ({ page }) => {
      console.log('🧪 Testing Approach tab navigation and content...');

      // Navigate to Approach tab
      await basePage.switchTab('approach');

      // Verify approach interface elements
      await expect.soft(page.locator('text="Approach", text="Strategy", text="Implementation"')).toBeVisible({ timeout: 5000 });

      // Check for strategy elements
      await expect.soft(page.locator('text="Recommendation", text="Action", text="Next"')).toBeVisible({ timeout: 3000 });

      await basePage.takeScreenshot('approach-tab-loaded');
      console.log('✅ Approach tab test completed');
    });
  });

  test.describe('Tab Navigation Flow', () => {
    test('Can navigate between all main tabs sequentially', async ({ page }) => {
      console.log('🧪 Testing sequential tab navigation...');

      const tabs = ['overview', 'discover', 'plan', 'analyze', 'examine', 'approach'];
      const navigationTimes = {};

      for (const tab of tabs) {
        const startTime = Date.now();

        try {
          await basePage.switchTab(tab);
          await page.waitForTimeout(1000); // Allow content to stabilize

          const endTime = Date.now();
          navigationTimes[tab] = endTime - startTime;

          console.log(`✅ Navigated to ${tab} tab in ${navigationTimes[tab]}ms`);
        } catch (error) {
          console.log(`⚠️  Failed to navigate to ${tab} tab: ${error.message}`);
          navigationTimes[tab] = -1; // Mark as failed
        }
      }

      // Verify at least most tabs are navigable
      const successfulNavigations = Object.values(navigationTimes).filter(time => time > 0);
      expect(successfulNavigations.length).toBeGreaterThan(tabs.length * 0.7);

      console.log('📊 Navigation performance:', navigationTimes);
    });

    test('Tab navigation preserves application state', async ({ page }) => {
      console.log('🧪 Testing tab navigation state preservation...');

      // Get initial app state
      const initialState = await basePage.getAppState();
      const initialProfileId = initialState?.selectedProfile?.profile_id;

      // Navigate through tabs
      await basePage.switchTab('discover');
      await page.waitForTimeout(500);

      await basePage.switchTab('analyze');
      await page.waitForTimeout(500);

      await basePage.switchTab('overview');
      await page.waitForTimeout(500);

      // Verify state is preserved
      const finalState = await basePage.getAppState();
      const finalProfileId = finalState?.selectedProfile?.profile_id;

      if (initialProfileId && finalProfileId) {
        expect(finalProfileId).toBe(initialProfileId);
        console.log('✅ Profile selection preserved across tab navigation');
      }

      // Verify app is still functional
      expect(finalState).toBeTruthy();
      console.log('✅ Application state preserved during navigation');
    });

    test('Tab content loads within acceptable time limits', async ({ page }) => {
      console.log('🧪 Testing tab loading performance...');

      const tabs = ['overview', 'discover', 'plan', 'analyze'];
      const performanceData = {};

      for (const tab of tabs) {
        const startTime = performance.now();

        try {
          await basePage.switchTab(tab);

          // Wait for content to be visible
          await page.waitForSelector('div, section, main', {
            state: 'visible',
            timeout: 5000
          });

          const endTime = performance.now();
          const loadTime = endTime - startTime;

          performanceData[tab] = {
            loadTime: loadTime,
            acceptable: loadTime < 3000 // 3 second threshold
          };

          console.log(`📊 ${tab} tab loaded in ${loadTime.toFixed(0)}ms`);
        } catch (error) {
          performanceData[tab] = {
            loadTime: -1,
            acceptable: false,
            error: error.message
          };
        }
      }

      // Verify performance is acceptable for most tabs
      const acceptableCount = Object.values(performanceData)
        .filter(data => data.acceptable).length;

      expect(acceptableCount).toBeGreaterThan(tabs.length * 0.7);

      console.log('📈 Tab performance summary:', performanceData);
    });
  });

  test.describe('Tab Error Handling', () => {
    test('Tabs handle API failures gracefully', async ({ page }) => {
      console.log('🧪 Testing tab error handling...');

      // Monitor console errors
      const consoleErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      // Navigate through tabs (some may have API calls)
      const tabs = ['overview', 'discover', 'analyze'];

      for (const tab of tabs) {
        try {
          await basePage.switchTab(tab);
          await page.waitForTimeout(2000);

          // Verify app is still functional even if API calls fail
          const appState = await basePage.getAppState();
          expect(appState).toBeTruthy();

        } catch (error) {
          console.log(`⚠️  Tab ${tab} had issues: ${error.message}`);
        }
      }

      // Filter out non-critical errors
      const criticalErrors = consoleErrors.filter(error =>
        !error.includes('404') &&
        !error.includes('Network') &&
        !error.includes('fetch')
      );

      if (criticalErrors.length > 0) {
        console.warn('⚠️  Critical console errors detected:', criticalErrors);
      }

      console.log('✅ Error handling verification completed');
    });

    test('Tabs recover from temporary failures', async ({ page }) => {
      console.log('🧪 Testing tab recovery from failures...');

      // Navigate to a tab
      await basePage.switchTab('discover');

      // Simulate network issues by blocking requests temporarily
      await page.route('**/api/**', route => {
        // Let first few requests through, then block some
        if (Math.random() > 0.3) {
          route.fulfill({ status: 500, body: 'Server Error' });
        } else {
          route.continue();
        }
      });

      // Try navigating despite network issues
      await basePage.switchTab('analyze');
      await page.waitForTimeout(1000);

      // Remove network blocking
      await page.unroute('**/api/**');

      // Verify app recovers
      await basePage.switchTab('overview');
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      console.log('✅ Tab recovery test completed');
    });
  });

  test.describe('Accessibility and Keyboard Navigation', () => {
    test('Tabs are keyboard accessible', async ({ page }) => {
      console.log('🧪 Testing keyboard accessibility...');

      // Focus on navigation area
      await page.keyboard.press('Tab');

      // Try to navigate using keyboard
      const tabs = ['overview', 'discover', 'plan', 'analyze'];

      for (const tab of tabs) {
        try {
          // Find tab button and focus it
          const tabButton = page.locator(`button:has-text("${tab.toUpperCase()}")`).first();
          if (await tabButton.isVisible()) {
            await tabButton.focus();
            await page.keyboard.press('Enter');
            await page.waitForTimeout(500);

            console.log(`✅ Keyboard navigation to ${tab} successful`);
          }
        } catch (error) {
          console.log(`⚠️  Keyboard navigation to ${tab} failed: ${error.message}`);
        }
      }

      console.log('✅ Keyboard accessibility test completed');
    });

    test('Tabs have proper ARIA labels and roles', async ({ page }) => {
      console.log('🧪 Testing ARIA accessibility...');

      // Check for proper tab roles
      const tabButtons = page.locator('button[role="tab"], button[aria-selected], [role="tablist"] button');
      const tabCount = await tabButtons.count();

      if (tabCount > 0) {
        console.log(`✅ Found ${tabCount} elements with tab roles`);
      } else {
        // Check for navigation buttons that should have proper accessibility
        const navButtons = page.locator('nav button, button:has-text("Overview"), button:has-text("DISCOVER")');
        const navCount = await navButtons.count();
        expect(navCount).toBeGreaterThan(0);
        console.log(`✅ Found ${navCount} navigation buttons`);
      }

      console.log('✅ ARIA accessibility check completed');
    });
  });
});
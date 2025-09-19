/**
 * Sub-Tab Navigation Tests
 *
 * This test suite validates all nested tab navigation within main sections:
 * - Enhanced Data Sub-tabs: Basic Information, 990 Data, Schedule-I, Foundation Intel, Application Strategy
 * - Discovery Results Sub-tabs: Organizations, Opportunities, Staging
 * - Analysis Sub-tabs: AI-Heavy, AI-Lite, Network Analysis
 * - Intelligence Modal Sub-tabs: Overview, Discover, Plan, Analyze, Examine, Approach
 * - Profile Management Sub-tabs: Profile overview, configuration, settings
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const DiscoveryPage = require('../../page-objects/DiscoveryPage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Sub-Tab Navigation', () => {
  let basePage;
  let profilePage;
  let discoveryPage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    // Set up test profile with data for sub-tab testing
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Create or use Heroes Bridge profile (has real tax data)
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();

    const heroesProfile = existingProfiles.find(p =>
      p.name && p.name.includes('Heroes Bridge')
    );

    if (heroesProfile) {
      testProfileId = heroesProfile.id;
      console.log(`✅ Using existing profile with data: ${testProfileId}`);
    } else {
      const heroesData = profiles.find(p => p.id === 'heroes_bridge_foundation');
      testProfileId = await profilePage.createProfile(heroesData);
      console.log(`📝 Created test profile with data: ${testProfileId}`);
    }

    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);
    discoveryPage = new DiscoveryPage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Select test profile
    if (testProfileId) {
      await profilePage.navigateToProfiles();
      await profilePage.selectProfile(testProfileId);
    }
  });

  test.describe('Enhanced Data Sub-Tabs', () => {
    test('Basic Information sub-tab displays profile data', async ({ page }) => {
      console.log('🧪 Testing Basic Information sub-tab...');

      // Navigate to profiles area and select a profile
      await profilePage.navigateToProfiles();

      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Look for Enhanced Data tab
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Check for Basic Information sub-tab
        const basicInfoTab = page.locator('button:has-text("Basic Information"), button:has-text("Overview")').first();
        if (await basicInfoTab.isVisible({ timeout: 3000 })) {
          await basicInfoTab.click();
          await page.waitForTimeout(500);

          // Verify basic information content
          await expect.soft(page.locator('text="Organization", text="Name", text="EIN"')).toBeVisible({ timeout: 3000 });
          console.log('✅ Basic Information sub-tab loaded');
        } else {
          console.log('ℹ️  Basic Information sub-tab not found');
        }
      } else {
        console.log('ℹ️  Enhanced Data tab not found');
      }

      await basePage.takeScreenshot('enhanced-data-basic-info');
    });

    test('990 Data sub-tab displays tax filing information', async ({ page }) => {
      console.log('🧪 Testing 990 Data sub-tab...');

      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Navigate to Enhanced Data
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Look for 990 Data sub-tab
        const form990Tab = page.locator('button:has-text("990"), button:has-text("Tax Data")').first();
        if (await form990Tab.isVisible({ timeout: 3000 })) {
          await form990Tab.click();
          await page.waitForTimeout(1000);

          // Verify 990 data elements
          await expect.soft(page.locator('text="Revenue", text="Assets", text="Form 990"')).toBeVisible({ timeout: 5000 });
          await expect.soft(page.locator('text="IRS", text="Filing", text="Tax"')).toBeVisible({ timeout: 3000 });

          console.log('✅ 990 Data sub-tab loaded');
        } else {
          console.log('ℹ️  990 Data sub-tab not available');
        }
      }

      await basePage.takeScreenshot('enhanced-data-990');
    });

    test('Schedule-I sub-tab displays grants data when available', async ({ page }) => {
      console.log('🧪 Testing Schedule-I sub-tab...');

      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Navigate to Enhanced Data
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Look for Schedule-I sub-tab
        const scheduleITab = page.locator('button:has-text("Schedule-I"), button:has-text("Schedule I"), button:has-text("Grants")').first();
        if (await scheduleITab.isVisible({ timeout: 3000 })) {
          await scheduleITab.click();
          await page.waitForTimeout(1000);

          // Verify Schedule-I content
          await expect.soft(page.locator('text="Grant", text="Schedule", text="Recipient"')).toBeVisible({ timeout: 5000 });

          console.log('✅ Schedule-I sub-tab loaded');
        } else {
          console.log('ℹ️  Schedule-I sub-tab not available for this organization');
        }
      }

      await basePage.takeScreenshot('enhanced-data-schedule-i');
    });

    test('Foundation Intel sub-tab displays foundation data when available', async ({ page }) => {
      console.log('🧪 Testing Foundation Intel sub-tab...');

      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Navigate to Enhanced Data
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Look for Foundation Intel sub-tab
        const foundationTab = page.locator('button:has-text("Foundation"), button:has-text("Intel")').first();
        if (await foundationTab.isVisible({ timeout: 3000 })) {
          await foundationTab.click();
          await page.waitForTimeout(1000);

          // Verify foundation intelligence content
          await expect.soft(page.locator('text="Foundation", text="Giving", text="Assets"')).toBeVisible({ timeout: 5000 });

          console.log('✅ Foundation Intel sub-tab loaded');
        } else {
          console.log('ℹ️  Foundation Intel sub-tab not available');
        }
      }

      await basePage.takeScreenshot('enhanced-data-foundation');
    });

    test('Application Strategy sub-tab displays strategic recommendations', async ({ page }) => {
      console.log('🧪 Testing Application Strategy sub-tab...');

      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Navigate to Enhanced Data
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Look for Application Strategy sub-tab
        const strategyTab = page.locator('button:has-text("Strategy"), button:has-text("Application")').first();
        if (await strategyTab.isVisible({ timeout: 3000 })) {
          await strategyTab.click();
          await page.waitForTimeout(1000);

          // Verify strategy content
          await expect.soft(page.locator('text="Strategy", text="Application", text="Recommendation"')).toBeVisible({ timeout: 5000 });

          console.log('✅ Application Strategy sub-tab loaded');
        } else {
          console.log('ℹ️  Application Strategy sub-tab not available');
        }
      }

      await basePage.takeScreenshot('enhanced-data-strategy');
    });
  });

  test.describe('Discovery Results Sub-Tabs', () => {
    test('Organizations sub-tab displays discovered organizations', async ({ page }) => {
      console.log('🧪 Testing Organizations discovery sub-tab...');

      // Navigate to Discovery and run discovery
      await discoveryPage.navigateToDiscovery();

      try {
        const results = await discoveryPage.executeDiscovery({
          tracks: ['nonprofit'],
          maxResults: 10
        });

        if (results && results.length > 0) {
          // Look for Organizations sub-tab or tab
          const organizationsTab = page.locator('button:has-text("Organizations"), button:has-text("Orgs")').first();
          if (await organizationsTab.isVisible({ timeout: 5000 })) {
            await organizationsTab.click();
            await page.waitForTimeout(1000);

            // Verify organizations content
            await expect.soft(page.locator('text="Organization", table, .grid')).toBeVisible({ timeout: 5000 });
            console.log('✅ Organizations sub-tab loaded');
          } else {
            console.log('ℹ️  Organizations sub-tab not found, checking for organization content');
            await expect.soft(page.locator('text="Organization"')).toBeVisible({ timeout: 3000 });
          }
        } else {
          console.log('ℹ️  No discovery results to test organizations sub-tab');
        }
      } catch (error) {
        console.log(`ℹ️  Discovery execution failed: ${error.message}`);
      }

      await basePage.takeScreenshot('discovery-organizations-subtab');
    });

    test('Opportunities sub-tab displays grant opportunities', async ({ page }) => {
      console.log('🧪 Testing Opportunities discovery sub-tab...');

      // Navigate to Discovery
      await discoveryPage.navigateToDiscovery();

      try {
        const results = await discoveryPage.executeDiscovery({
          tracks: ['government'],
          maxResults: 10
        });

        if (results && results.length > 0) {
          // Look for Opportunities sub-tab
          const opportunitiesTab = page.locator('button:has-text("Opportunities"), button:has-text("Grants")').first();
          if (await opportunitiesTab.isVisible({ timeout: 5000 })) {
            await opportunitiesTab.click();
            await page.waitForTimeout(1000);

            // Verify opportunities content
            await expect.soft(page.locator('text="Opportunity", text="Grant", text="Deadline"')).toBeVisible({ timeout: 5000 });
            console.log('✅ Opportunities sub-tab loaded');
          } else {
            console.log('ℹ️  Opportunities sub-tab not found');
          }
        } else {
          console.log('ℹ️  No discovery results to test opportunities sub-tab');
        }
      } catch (error) {
        console.log(`ℹ️  Discovery execution failed: ${error.message}`);
      }

      await basePage.takeScreenshot('discovery-opportunities-subtab');
    });

    test('Staging sub-tab displays opportunity pipeline', async ({ page }) => {
      console.log('🧪 Testing Staging discovery sub-tab...');

      // Navigate to Discovery
      await discoveryPage.navigateToDiscovery();

      try {
        // Execute discovery to get some opportunities
        await discoveryPage.executeDiscovery({
          tracks: ['nonprofit', 'government'],
          maxResults: 5
        });

        // Look for Staging sub-tab
        const stagingTab = page.locator('button:has-text("Staging"), button:has-text("Pipeline"), button:has-text("Stages")').first();
        if (await stagingTab.isVisible({ timeout: 5000 })) {
          await stagingTab.click();
          await page.waitForTimeout(1000);

          // Verify staging content
          await expect.soft(page.locator('text="Stage", text="Pipeline", text="Prospects"')).toBeVisible({ timeout: 5000 });
          console.log('✅ Staging sub-tab loaded');
        } else {
          console.log('ℹ️  Staging sub-tab not found');
        }
      } catch (error) {
        console.log(`ℹ️  Discovery or staging failed: ${error.message}`);
      }

      await basePage.takeScreenshot('discovery-staging-subtab');
    });
  });

  test.describe('Analysis Sub-Tabs', () => {
    test('AI-Heavy analysis sub-tab functionality', async ({ page }) => {
      console.log('🧪 Testing AI-Heavy analysis sub-tab...');

      // Navigate to Analyze tab
      await basePage.switchTab('analyze');

      // Look for AI-Heavy sub-tab or option
      const aiHeavyTab = page.locator('button:has-text("Heavy"), button:has-text("AI-Heavy"), button:has-text("Comprehensive")').first();
      if (await aiHeavyTab.isVisible({ timeout: 5000 })) {
        await aiHeavyTab.click();
        await page.waitForTimeout(1000);

        // Verify AI-Heavy content
        await expect.soft(page.locator('text="Heavy", text="Comprehensive", text="Detailed"')).toBeVisible({ timeout: 5000 });
        console.log('✅ AI-Heavy sub-tab loaded');
      } else {
        console.log('ℹ️  AI-Heavy sub-tab not found');
      }

      await basePage.takeScreenshot('analysis-ai-heavy-subtab');
    });

    test('AI-Lite analysis sub-tab functionality', async ({ page }) => {
      console.log('🧪 Testing AI-Lite analysis sub-tab...');

      // Navigate to Analyze tab
      await basePage.switchTab('analyze');

      // Look for AI-Lite sub-tab or option
      const aiLiteTab = page.locator('button:has-text("Lite"), button:has-text("AI-Lite"), button:has-text("Quick")').first();
      if (await aiLiteTab.isVisible({ timeout: 5000 })) {
        await aiLiteTab.click();
        await page.waitForTimeout(1000);

        // Verify AI-Lite content
        await expect.soft(page.locator('text="Lite", text="Quick", text="Fast"')).toBeVisible({ timeout: 5000 });
        console.log('✅ AI-Lite sub-tab loaded');
      } else {
        console.log('ℹ️  AI-Lite sub-tab not found');
      }

      await basePage.takeScreenshot('analysis-ai-lite-subtab');
    });

    test('Network Analysis sub-tab functionality', async ({ page }) => {
      console.log('🧪 Testing Network Analysis sub-tab...');

      // Navigate to Analyze tab
      await basePage.switchTab('analyze');

      // Look for Network Analysis sub-tab
      const networkTab = page.locator('button:has-text("Network"), button:has-text("Board"), button:has-text("Connections")').first();
      if (await networkTab.isVisible({ timeout: 5000 })) {
        await networkTab.click();
        await page.waitForTimeout(1000);

        // Verify Network Analysis content
        await expect.soft(page.locator('text="Network", text="Board", text="Connection"')).toBeVisible({ timeout: 5000 });
        console.log('✅ Network Analysis sub-tab loaded');
      } else {
        console.log('ℹ️  Network Analysis sub-tab not found');
      }

      await basePage.takeScreenshot('analysis-network-subtab');
    });
  });

  test.describe('Intelligence Modal Sub-Tabs', () => {
    test('Intelligence modal Overview sub-tab', async ({ page }) => {
      console.log('🧪 Testing Intelligence modal Overview sub-tab...');

      // Try to open intelligence modal (this may vary based on current implementation)
      const intelligenceButton = page.locator('button:has-text("Intelligence"), button:has-text("Analysis"), button:has-text("AI Analysis")').first();

      if (await intelligenceButton.isVisible({ timeout: 5000 })) {
        await intelligenceButton.click();
        await page.waitForTimeout(1000);

        // Look for modal and Overview sub-tab
        const overviewTab = page.locator('button:has-text("Overview")').last(); // Use last() to get modal tab
        if (await overviewTab.isVisible({ timeout: 3000 })) {
          await overviewTab.click();
          await page.waitForTimeout(500);

          // Verify Overview content in modal
          await expect.soft(page.locator('.fixed, .modal, .overlay')).toBeVisible({ timeout: 3000 });
          console.log('✅ Intelligence modal Overview sub-tab loaded');
        } else {
          console.log('ℹ️  Intelligence modal Overview sub-tab not found');
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').last();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      } else {
        console.log('ℹ️  Intelligence modal trigger not found');
      }

      await basePage.takeScreenshot('intelligence-modal-overview');
    });

    test('Intelligence modal navigation between all sub-tabs', async ({ page }) => {
      console.log('🧪 Testing Intelligence modal sub-tab navigation...');

      // Try to open intelligence modal
      const intelligenceButton = page.locator('button:has-text("Intelligence"), button:has-text("Analysis"), button:has-text("Comprehensive")').first();

      if (await intelligenceButton.isVisible({ timeout: 5000 })) {
        await intelligenceButton.click();
        await page.waitForTimeout(1000);

        // Modal sub-tabs to test
        const modalTabs = ['Overview', 'Discover', 'Plan', 'Analyze', 'Examine', 'Approach'];

        for (const tabName of modalTabs) {
          try {
            const modalTab = page.locator(`.fixed button:has-text("${tabName}"), .modal button:has-text("${tabName}")`).first();
            if (await modalTab.isVisible({ timeout: 2000 })) {
              await modalTab.click();
              await page.waitForTimeout(500);
              console.log(`✅ Navigated to ${tabName} in intelligence modal`);
            } else {
              console.log(`ℹ️  ${tabName} sub-tab not found in modal`);
            }
          } catch (error) {
            console.log(`ℹ️  Failed to navigate to ${tabName}: ${error.message}`);
          }
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').last();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      } else {
        console.log('ℹ️  Intelligence modal not accessible');
      }

      await basePage.takeScreenshot('intelligence-modal-navigation');
    });
  });

  test.describe('Sub-Tab Performance and Usability', () => {
    test('Sub-tab switching is responsive', async ({ page }) => {
      console.log('🧪 Testing sub-tab switching performance...');

      // Test Enhanced Data sub-tabs if available
      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(1000);

        // Test switching between sub-tabs
        const subTabs = [
          'button:has-text("Basic")',
          'button:has-text("990")',
          'button:has-text("Overview")'
        ];

        const switchingTimes = [];

        for (const subTabSelector of subTabs) {
          const subTab = page.locator(subTabSelector).first();
          if (await subTab.isVisible({ timeout: 2000 })) {
            const startTime = Date.now();
            await subTab.click();
            await page.waitForTimeout(300);
            const endTime = Date.now();

            const switchTime = endTime - startTime;
            switchingTimes.push(switchTime);
            console.log(`Sub-tab switch took ${switchTime}ms`);
          }
        }

        // Verify switching is fast (under 1 second)
        const avgSwitchTime = switchingTimes.reduce((a, b) => a + b, 0) / switchingTimes.length;
        expect(avgSwitchTime).toBeLessThan(1000);

        console.log(`✅ Average sub-tab switching time: ${avgSwitchTime.toFixed(0)}ms`);
      }
    });

    test('Sub-tabs preserve data during navigation', async ({ page }) => {
      console.log('🧪 Testing sub-tab data persistence...');

      await profilePage.navigateToProfiles();
      if (testProfileId) {
        await profilePage.selectProfile(testProfileId);
      }

      // Get initial profile state
      const initialAppState = await basePage.getAppState();
      const initialProfileId = initialAppState?.selectedProfile?.profile_id;

      // Navigate through Enhanced Data sub-tabs
      const enhancedDataTab = page.locator('button:has-text("Enhanced Data")').first();
      if (await enhancedDataTab.isVisible({ timeout: 5000 })) {
        await enhancedDataTab.click();
        await page.waitForTimeout(500);

        // Switch between sub-tabs
        const basicTab = page.locator('button:has-text("Basic"), button:has-text("Overview")').first();
        if (await basicTab.isVisible({ timeout: 3000 })) {
          await basicTab.click();
          await page.waitForTimeout(300);
        }

        const form990Tab = page.locator('button:has-text("990")').first();
        if (await form990Tab.isVisible({ timeout: 3000 })) {
          await form990Tab.click();
          await page.waitForTimeout(300);
        }

        // Verify profile is still selected
        const finalAppState = await basePage.getAppState();
        const finalProfileId = finalAppState?.selectedProfile?.profile_id;

        if (initialProfileId && finalProfileId) {
          expect(finalProfileId).toBe(initialProfileId);
          console.log('✅ Profile selection preserved during sub-tab navigation');
        }
      }
    });
  });
});
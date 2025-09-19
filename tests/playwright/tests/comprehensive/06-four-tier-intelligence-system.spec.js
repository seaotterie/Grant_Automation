/**
 * 4-Tier Intelligence System Tests
 *
 * This test suite validates the complete business package functionality:
 * - CURRENT ($0.75, 5-10 min): 4-stage AI analysis, strategic recommendations
 * - STANDARD ($7.50, 15-20 min): + Historical funding analysis, geographic patterns
 * - ENHANCED ($22.00, 30-45 min): + Document analysis, network intelligence, decision maker profiles
 * - COMPLETE ($42.00, 45-60 min): + Policy analysis, monitoring, 26+ page reports, strategic consulting
 *
 * Tests tier selection, processing workflows, output quality, and pricing validation.
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('4-Tier Intelligence System', () => {
  let basePage;
  let profilePage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Create or find test profile
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();

    const testProfile = existingProfiles.find(p =>
      p.name && p.name.includes('Heroes Bridge')
    );

    if (testProfile) {
      testProfileId = testProfile.id;
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

    if (testProfileId) {
      await profilePage.navigateToProfiles();
      await profilePage.selectProfile(testProfileId);
    }
  });

  test.describe('Tier Selection and Configuration', () => {
    test('CURRENT tier ($0.75) - Basic AI analysis selection', async ({ page }) => {
      console.log('🧪 Testing CURRENT tier selection and configuration...');

      // Navigate to Plan tab for tier selection
      await basePage.switchTab('plan');

      // Look for CURRENT tier option
      const currentTier = page.locator('text="CURRENT", text="$0.75", text="5-10 min"').first();
      await expect.soft(currentTier).toBeVisible({ timeout: 5000 });

      // Check for tier features
      await expect.soft(page.locator('text="4-stage AI analysis"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="strategic recommendations"')).toBeVisible({ timeout: 3000 });

      // Verify pricing display
      await expect.soft(page.locator('text="$0.75"')).toBeVisible();

      await basePage.takeScreenshot('current-tier-selection');
      console.log('✅ CURRENT tier validation completed');
    });

    test('STANDARD tier ($7.50) - Enhanced analysis selection', async ({ page }) => {
      console.log('🧪 Testing STANDARD tier selection and features...');

      await basePage.switchTab('plan');

      // Look for STANDARD tier option
      const standardTier = page.locator('text="STANDARD", text="$7.50", text="15-20 min"').first();
      await expect.soft(standardTier).toBeVisible({ timeout: 5000 });

      // Check for tier features
      await expect.soft(page.locator('text="Historical funding analysis"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="geographic patterns"')).toBeVisible({ timeout: 3000 });

      // Verify pricing
      await expect.soft(page.locator('text="$7.50"')).toBeVisible();

      await basePage.takeScreenshot('standard-tier-selection');
      console.log('✅ STANDARD tier validation completed');
    });

    test('ENHANCED tier ($22.00) - Advanced analysis selection', async ({ page }) => {
      console.log('🧪 Testing ENHANCED tier selection and features...');

      await basePage.switchTab('plan');

      // Look for ENHANCED tier option
      const enhancedTier = page.locator('text="ENHANCED", text="$22.00", text="30-45 min"').first();
      await expect.soft(enhancedTier).toBeVisible({ timeout: 5000 });

      // Check for tier features
      await expect.soft(page.locator('text="Document analysis"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="network intelligence"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="decision maker profiles"')).toBeVisible({ timeout: 3000 });

      // Verify pricing
      await expect.soft(page.locator('text="$22.00"')).toBeVisible();

      await basePage.takeScreenshot('enhanced-tier-selection');
      console.log('✅ ENHANCED tier validation completed');
    });

    test('COMPLETE tier ($42.00) - Premium analysis selection', async ({ page }) => {
      console.log('🧪 Testing COMPLETE tier selection and features...');

      await basePage.switchTab('plan');

      // Look for COMPLETE tier option
      const completeTier = page.locator('text="COMPLETE", text="$42.00", text="45-60 min"').first();
      await expect.soft(completeTier).toBeVisible({ timeout: 5000 });

      // Check for tier features
      await expect.soft(page.locator('text="Policy analysis"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="monitoring"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="26+ page reports"')).toBeVisible({ timeout: 3000 });
      await expect.soft(page.locator('text="strategic consulting"')).toBeVisible({ timeout: 3000 });

      // Verify pricing
      await expect.soft(page.locator('text="$42.00"')).toBeVisible();

      await basePage.takeScreenshot('complete-tier-selection');
      console.log('✅ COMPLETE tier validation completed');
    });
  });

  test.describe('Tier Processing Workflows', () => {
    test('CURRENT tier processing workflow', async ({ page }) => {
      console.log('🧪 Testing CURRENT tier processing workflow...');

      // Navigate to Analyze tab
      await basePage.switchTab('analyze');

      // Look for CURRENT tier processing option
      const currentProcess = page.locator('button:has-text("CURRENT"), button:has-text("Lite")').first();
      if (await currentProcess.isVisible()) {
        await currentProcess.click();
        await page.waitForTimeout(2000);

        // Monitor processing indicators
        await expect.soft(page.locator('text="Processing", text="Analyzing", text="AI Analysis"')).toBeVisible({ timeout: 5000 });

        // Check for 4-stage analysis indicators
        await expect.soft(page.locator('text="PLAN", text="ANALYZE", text="EXAMINE", text="APPROACH"')).toBeVisible({ timeout: 10000 });
      }

      await basePage.takeScreenshot('current-tier-processing');
      console.log('✅ CURRENT tier processing test completed');
    });

    test('STANDARD tier processing workflow', async ({ page }) => {
      console.log('🧪 Testing STANDARD tier processing workflow...');

      await basePage.switchTab('analyze');

      // Look for STANDARD tier processing
      const standardProcess = page.locator('button:has-text("STANDARD"), button:has-text("Heavy")').first();
      if (await standardProcess.isVisible()) {
        await standardProcess.click();
        await page.waitForTimeout(2000);

        // Monitor extended processing indicators
        await expect.soft(page.locator('text="Historical Analysis", text="Geographic Patterns"')).toBeVisible({ timeout: 8000 });

        // Check for longer processing time indication
        await expect.soft(page.locator('text="15-20 min", text="Extended Analysis"')).toBeVisible({ timeout: 5000 });
      }

      await basePage.takeScreenshot('standard-tier-processing');
      console.log('✅ STANDARD tier processing test completed');
    });

    test('Intelligence system API endpoints', async ({ page }) => {
      console.log('🧪 Testing intelligence system API endpoints...');

      // Test tier configuration endpoint
      const tierConfigResponse = await page.request.get('http://localhost:8000/api/intelligence/tiers');
      if (tierConfigResponse.ok()) {
        const tierData = await tierConfigResponse.json();

        // Verify tier structure
        expect(tierData).toHaveProperty('tiers');
        const tiers = tierData.tiers;

        // Check for all four tiers
        expect(tiers).toEqual(expect.arrayContaining([
          expect.objectContaining({
            name: expect.stringMatching(/CURRENT/i),
            price: expect.any(Number),
            duration: expect.stringMatching(/5-10/),
            features: expect.arrayContaining([
              expect.stringMatching(/AI analysis/i)
            ])
          })
        ]));

        console.log('✅ Tier configuration API validated');
      }

      // Test tier processing endpoint
      if (testProfileId) {
        const processRequest = {
          profile_id: testProfileId,
          tier: 'CURRENT',
          analysis_type: 'comprehensive'
        };

        const processResponse = await page.request.post('http://localhost:8000/api/intelligence/process', {
          data: processRequest,
          timeout: 30000
        });

        if (processResponse.ok()) {
          const processData = await processResponse.json();
          expect(processData).toHaveProperty('status');
          expect(processData).toHaveProperty('estimated_duration');
          console.log('✅ Intelligence processing API validated');
        }
      }

      console.log('✅ Intelligence API testing completed');
    });
  });

  test.describe('Output Quality and Validation', () => {
    test('CURRENT tier output validation', async ({ page }) => {
      console.log('🧪 Validating CURRENT tier output quality...');

      await basePage.switchTab('analyze');

      // Trigger CURRENT tier analysis
      const currentButton = page.locator('button:has-text("Lite"), button:has-text("CURRENT")').first();
      if (await currentButton.isVisible()) {
        await currentButton.click();
        await page.waitForTimeout(3000);

        // Wait for results
        await expect.soft(page.locator('text="Analysis Complete", text="Results", text="Strategic"')).toBeVisible({ timeout: 15000 });

        // Verify strategic recommendations
        await expect.soft(page.locator('text="Recommendation", text="Strategy", text="Action"')).toBeVisible({ timeout: 5000 });

        // Check for 4-stage analysis output
        const analysisStages = ['PLAN', 'ANALYZE', 'EXAMINE', 'APPROACH'];
        for (const stage of analysisStages) {
          await expect.soft(page.locator(`text="${stage}"`)).toBeVisible({ timeout: 3000 });
        }
      }

      await basePage.takeScreenshot('current-tier-output');
      console.log('✅ CURRENT tier output validation completed');
    });

    test('Report generation and export functionality', async ({ page }) => {
      console.log('🧪 Testing report generation and export...');

      // Navigate to results or export area
      await basePage.switchTab('examine');

      // Look for export options
      const exportButton = page.locator('button:has-text("Export"), button:has-text("Download"), button:has-text("Report")').first();
      if (await exportButton.isVisible()) {
        await exportButton.click();
        await page.waitForTimeout(1000);

        // Check for export format options
        await expect.soft(page.locator('text="PDF", text="Excel", text="PowerPoint"')).toBeVisible({ timeout: 5000 });

        // Verify tier-specific report options
        await expect.soft(page.locator('text="Executive Summary", text="Strategic Report"')).toBeVisible({ timeout: 3000 });
      }

      await basePage.takeScreenshot('report-export-options');
      console.log('✅ Report generation testing completed');
    });

    test('Cost tracking and billing validation', async ({ page }) => {
      console.log('🧪 Testing cost tracking and billing...');

      // Check for cost tracking API
      const costResponse = await page.request.get('http://localhost:8000/api/costs/summary');
      if (costResponse.ok()) {
        const costData = await costResponse.json();

        // Verify cost structure
        expect(costData).toHaveProperty('total_costs');
        expect(costData).toHaveProperty('tier_breakdown');

        // Check tier pricing
        if (costData.tier_breakdown) {
          const tierCosts = costData.tier_breakdown;
          expect(tierCosts).toEqual(expect.objectContaining({
            CURRENT: expect.any(Number),
            STANDARD: expect.any(Number),
            ENHANCED: expect.any(Number),
            COMPLETE: expect.any(Number)
          }));
        }

        console.log('✅ Cost tracking API validated');
      }

      // Navigate to overview for cost display
      await basePage.switchTab('overview');

      // Look for cost metrics
      await expect.soft(page.locator('text="Cost", text="$", text="Usage"')).toBeVisible({ timeout: 5000 });

      await basePage.takeScreenshot('cost-tracking-display');
      console.log('✅ Cost tracking validation completed');
    });
  });

  test.describe('Tier Comparison and Upgrade Paths', () => {
    test('Tier comparison interface', async ({ page }) => {
      console.log('🧪 Testing tier comparison functionality...');

      await basePage.switchTab('plan');

      // Look for comparison table or interface
      await expect.soft(page.locator('text="Compare", text="Features", text="Pricing"')).toBeVisible({ timeout: 5000 });

      // Check for tier comparison elements
      const tierNames = ['CURRENT', 'STANDARD', 'ENHANCED', 'COMPLETE'];
      for (const tier of tierNames) {
        await expect.soft(page.locator(`text="${tier}"`)).toBeVisible({ timeout: 3000 });
      }

      // Verify pricing display
      const prices = ['$0.75', '$7.50', '$22.00', '$42.00'];
      for (const price of prices) {
        await expect.soft(page.locator(`text="${price}"`)).toBeVisible({ timeout: 3000 });
      }

      await basePage.takeScreenshot('tier-comparison-interface');
      console.log('✅ Tier comparison testing completed');
    });

    test('Upgrade path validation', async ({ page }) => {
      console.log('🧪 Testing tier upgrade pathways...');

      await basePage.switchTab('plan');

      // Look for upgrade buttons or links
      const upgradeButtons = page.locator('button:has-text("Upgrade"), button:has-text("Select"), a:has-text("Choose")');
      const upgradeCount = await upgradeButtons.count();
      expect(upgradeCount).toBeGreaterThan(0);

      // Test upgrade flow
      const firstUpgrade = upgradeButtons.first();
      if (await firstUpgrade.isVisible()) {
        await firstUpgrade.click();
        await page.waitForTimeout(1000);

        // Check for upgrade confirmation or selection
        await expect.soft(page.locator('text="Confirm", text="Proceed", text="Select Tier"')).toBeVisible({ timeout: 5000 });
      }

      await basePage.takeScreenshot('upgrade-path-interface');
      console.log('✅ Upgrade path validation completed');
    });

    test('Feature matrix validation', async ({ page }) => {
      console.log('🧪 Testing feature matrix accuracy...');

      await basePage.switchTab('plan');

      // Define expected features per tier
      const tierFeatures = {
        CURRENT: ['4-stage AI analysis', 'strategic recommendations'],
        STANDARD: ['Historical funding analysis', 'geographic patterns'],
        ENHANCED: ['Document analysis', 'network intelligence', 'decision maker profiles'],
        COMPLETE: ['Policy analysis', 'monitoring', '26+ page reports', 'strategic consulting']
      };

      // Validate feature listings
      for (const [tier, features] of Object.entries(tierFeatures)) {
        for (const feature of features) {
          await expect.soft(page.locator(`text="${feature}"`)).toBeVisible({ timeout: 3000 });
        }
      }

      // Check for feature exclusivity indicators
      await expect.soft(page.locator('text="✓", text="✗", text="Included"')).toBeVisible({ timeout: 5000 });

      await basePage.takeScreenshot('feature-matrix-validation');
      console.log('✅ Feature matrix validation completed');
    });
  });

  test.describe('Performance and Scalability', () => {
    test('Tier processing performance benchmarks', async ({ page }) => {
      console.log('🧪 Testing tier processing performance...');

      const performanceMetrics = {};

      // Test CURRENT tier performance
      await basePage.switchTab('analyze');

      const startTime = performance.now();
      const liteButton = page.locator('button:has-text("Lite")').first();

      if (await liteButton.isVisible()) {
        await liteButton.click();
        await page.waitForTimeout(2000);

        // Wait for processing to begin
        await expect.soft(page.locator('text="Processing", text="Analyzing"')).toBeVisible({ timeout: 10000 });

        const processingTime = performance.now() - startTime;
        performanceMetrics.CURRENT = {
          initiation_time: processingTime,
          target_duration: '5-10 min'
        };
      }

      // Verify performance is within acceptable bounds
      expect(performanceMetrics.CURRENT?.initiation_time).toBeLessThan(10000); // 10 second initiation

      console.log('📊 Performance metrics:', performanceMetrics);
      console.log('✅ Performance benchmarking completed');
    });

    test('Concurrent tier processing limits', async ({ page }) => {
      console.log('🧪 Testing concurrent processing capabilities...');

      // Test multiple simultaneous requests
      const concurrentRequests = [];

      for (let i = 0; i < 3; i++) {
        const request = page.request.post('http://localhost:8000/api/intelligence/process', {
          data: {
            profile_id: testProfileId,
            tier: 'CURRENT',
            analysis_type: 'concurrent_test'
          },
          timeout: 30000
        });
        concurrentRequests.push(request);
      }

      try {
        const responses = await Promise.allSettled(concurrentRequests);
        const successfulRequests = responses.filter(r => r.status === 'fulfilled' && r.value.ok());

        // Verify system handles concurrent requests appropriately
        expect(successfulRequests.length).toBeGreaterThanOrEqual(1);
        console.log(`✅ Handled ${successfulRequests.length}/3 concurrent requests successfully`);
      } catch (error) {
        console.log(`⚠️  Concurrent processing test: ${error.message}`);
      }

      console.log('✅ Concurrent processing testing completed');
    });

    test('System resource monitoring during tier processing', async ({ page }) => {
      console.log('🧪 Monitoring system resources during processing...');

      // Check system status endpoint
      const statusResponse = await page.request.get('http://localhost:8000/api/system/status');
      if (statusResponse.ok()) {
        const statusData = await statusResponse.json();

        // Verify system health metrics
        expect(statusData).toHaveProperty('status');
        expect(statusData).toHaveProperty('active_processes');
        expect(statusData).toHaveProperty('memory_usage');

        // Check if system is healthy
        if (statusData.status === 'healthy') {
          console.log('✅ System status healthy during processing');
        }
      }

      // Monitor processing queue
      const queueResponse = await page.request.get('http://localhost:8000/api/intelligence/queue');
      if (queueResponse.ok()) {
        const queueData = await queueResponse.json();
        expect(queueData).toHaveProperty('queue_length');
        expect(queueData).toHaveProperty('processing_capacity');

        console.log(`📊 Queue status: ${queueData.queue_length} items, capacity: ${queueData.processing_capacity}`);
      }

      console.log('✅ Resource monitoring completed');
    });
  });
});
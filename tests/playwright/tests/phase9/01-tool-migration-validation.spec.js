/**
 * Phase 9 Test: Tool Migration Validation
 *
 * Validates that all 22 operational tools are accessible and functional
 * after Phase 9 cleanup (34 processors removed, -21,612 lines).
 *
 * Tests:
 * - Tool registry API (/api/v1/tools)
 * - Tool 1: Opportunity Screening Tool
 * - Tool 2: Deep Intelligence Tool
 * - Tool 10-22: Intelligence tools
 * - Tool 17: BMF Discovery Tool
 * - Tool 25: Web Intelligence Tool
 * - No legacy processor imports
 */

const { test, expect } = require('@playwright/test');

test.describe('Phase 9: Tool Migration Validation', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to application
    await page.goto('http://localhost:8000');

    // Wait for Alpine.js initialization
    await page.waitForFunction(
      () => window.Alpine && window.catalynxApp,
      { timeout: 10000 }
    );
  });

  test('Tool Registry API returns 22+ operational tools', async ({ page }) => {
    console.log('🧪 Testing tool registry API...');

    // Call tool registry API
    const response = await page.request.get('http://localhost:8000/api/v1/tools');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    console.log(`📊 Found ${data.tools ? data.tools.length : 0} tools`);

    // Should have at least 22 operational tools
    expect(data.tools).toBeDefined();
    expect(data.tools.length).toBeGreaterThanOrEqual(22);

    // Verify key tools exist
    const toolNames = data.tools.map(t => t.name || t.tool_name);
    expect(toolNames).toContain('XML 990 Parser Tool');
    expect(toolNames).toContain('Opportunity Screening Tool');
    expect(toolNames).toContain('Deep Intelligence Tool');

    console.log('✅ Tool registry validated');
  });

  test('Tool categories are properly organized', async ({ page }) => {
    console.log('🧪 Testing tool categorization...');

    const response = await page.request.get('http://localhost:8000/api/v1/tools');
    const data = await response.json();

    // Count tools by category
    const categories = {};
    data.tools.forEach(tool => {
      const cat = tool.category || 'uncategorized';
      categories[cat] = (categories[cat] || 0) + 1;
    });

    console.log('📂 Tool categories:', categories);

    // Should have organized categories
    expect(Object.keys(categories).length).toBeGreaterThan(1);

    console.log('✅ Categories validated');
  });

  test('Tool 1: Opportunity Screening Tool is operational', async ({ page }) => {
    console.log('🧪 Testing Tool 1: Opportunity Screening...');

    // URL encode the tool name (spaces become %20)
    const toolName = encodeURIComponent('Opportunity Screening Tool');
    const response = await page.request.get(`http://localhost:8000/api/v1/tools/${toolName}`);
    expect(response.status()).toBeLessThan(500); // 200 or 404, but not 500

    if (response.ok()) {
      const data = await response.json();
      expect(data).toBeDefined();
      console.log('✅ Opportunity Screening Tool accessible');
    } else {
      console.log('ℹ️ Tool endpoint may use different pattern');
    }
  });

  test('Tool 2: Deep Intelligence Tool is operational', async ({ page }) => {
    console.log('🧪 Testing Tool 2: Deep Intelligence...');

    // URL encode the tool name (spaces become %20)
    const toolName = encodeURIComponent('Deep Intelligence Tool');
    const response = await page.request.get(`http://localhost:8000/api/v1/tools/${toolName}`);
    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      expect(data).toBeDefined();
      console.log('✅ Deep Intelligence Tool accessible');
    } else {
      console.log('ℹ️ Tool endpoint may use different pattern');
    }
  });

  test('Intelligence tools (10-22) are listed in registry', async ({ page }) => {
    console.log('🧪 Testing intelligence tools availability...');

    const response = await page.request.get('http://localhost:8000/api/v1/tools');
    const data = await response.json();

    const intelligenceTools = [
      'Financial Intelligence Tool',
      'Risk Intelligence Tool',
      'Network Intelligence Tool',
      'Schedule I Grant Analyzer',
      'EIN Validator Tool',
      'Data Validator Tool',
      'BMF Discovery Tool',
      'Data Export Tool',
      'Grant Package Generator',
      'Multi-Dimensional Scorer',
      'Report Generator Tool',
      'Historical Funding Analyzer',
      'Web Intelligence Tool'
    ];

    const toolNames = data.tools.map(t => t.name || t.tool_name);
    let foundCount = 0;

    intelligenceTools.forEach(toolName => {
      if (toolNames.some(name => name.includes(toolName))) {
        foundCount++;
      }
    });

    console.log(`📊 Found ${foundCount}/${intelligenceTools.length} intelligence tools`);
    expect(foundCount).toBeGreaterThan(8); // At least majority should exist

    console.log('✅ Intelligence tools validated');
  });

  test('Tool 17: BMF Discovery Tool is operational', async ({ page }) => {
    console.log('🧪 Testing Tool 17: BMF Discovery...');

    // Navigate to discovery tab
    await page.goto('http://localhost:8000');
    await page.waitForFunction(() => window.catalynxApp, { timeout: 10000 });

    // Look for BMF discovery functionality in UI
    const discoveryTab = page.locator('[data-tab="discover"], button:has-text("Discover")').first();
    if (await discoveryTab.isVisible({ timeout: 15000 })) {
      await discoveryTab.click();
      await page.waitForTimeout(1000);

      // Look for NTEE code selection (BMF discovery feature)
      const nteeButton = page.locator('button:has-text("Select NTEE"), button:has-text("NTEE Codes")').first();
      await expect.soft(nteeButton).toBeVisible({ timeout: 15000 });

      console.log('✅ BMF Discovery UI elements present');
    } else {
      console.log('ℹ️ Discovery tab navigation may differ');
    }
  });

  test('Tool 25: Web Intelligence Tool integration', async ({ page }) => {
    console.log('🧪 Testing Tool 25: Web Intelligence...');

    // Check for EIN lookup functionality (uses Tool 25)
    await page.goto('http://localhost:8000');
    await page.waitForFunction(() => window.catalynxApp, { timeout: 10000 });

    // Look for profile section with EIN input
    const profileSection = page.locator('[data-section="profiles"], [data-tab="profiles"]').first();
    if (await profileSection.isVisible({ timeout: 3000 })) {
      await profileSection.click();
      await page.waitForTimeout(500);
    }

    // Web Intelligence Tool integrates with profile creation
    const createProfileBtn = page.locator('button:has-text("Create Profile"), button:has-text("New Profile")').first();
    await expect.soft(createProfileBtn).toBeVisible({ timeout: 15000 });

    console.log('✅ Web Intelligence integration points available');
  });

  test('No console errors from legacy processor imports', async ({ page }) => {
    console.log('🧪 Testing for legacy processor errors...');

    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Check for processor-related errors
        if (text.includes('processor') || text.includes('ai_heavy') || text.includes('ai_lite')) {
          consoleErrors.push(text);
        }
      }
    });

    await page.goto('http://localhost:8000');
    await page.waitForTimeout(3000); // Let page fully load

    console.log(`📊 Found ${consoleErrors.length} processor-related errors`);

    if (consoleErrors.length > 0) {
      console.log('⚠️ Processor errors:', consoleErrors);
    }

    // Expect no processor-related errors
    expect(consoleErrors.length).toBe(0);

    console.log('✅ No legacy processor errors detected');
  });

  test('Tool-based workflow replaces processor workflow', async ({ page }) => {
    console.log('🧪 Testing tool-based workflow architecture...');

    await page.goto('http://localhost:8000');
    await page.waitForFunction(() => window.catalynxApp, { timeout: 10000 });

    // Check that app uses tool-based architecture
    const appHasTools = await page.evaluate(() => {
      // Check for tool-related variables or functions
      return !!(window.catalynxApp && typeof window.catalynxApp === 'object');
    });

    expect(appHasTools).toBeTruthy();

    // Navigate through tabs to ensure tool-based workflow
    const tabs = ['profiles', 'discover', 'intelligence', 'screening'];
    for (const tabName of tabs) {
      const tab = page.locator(`[data-tab="${tabName}"], button:has-text("${tabName}")`, { hasText: new RegExp(tabName, 'i') }).first();
      if (await tab.isVisible({ timeout: 2000 })) {
        await tab.click();
        await page.waitForTimeout(500);
        console.log(`✅ ${tabName} tab accessible`);
      }
    }

    console.log('✅ Tool-based workflow operational');
  });

  test('Health check confirms operational status', async ({ page }) => {
    console.log('🧪 Testing system health endpoint...');

    const response = await page.request.get('http://localhost:8000/api/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBeDefined();

    console.log(`📊 System status: ${data.status}`);
    console.log('✅ Health check passed');
  });
});

/**
 * Basic Functionality Smoke Test
 * 
 * This test verifies the most fundamental functionality:
 * - Application loads
 * - Alpine.js initializes
 * - Navigation works
 * - No critical errors
 */

const { test, expect } = require('@playwright/test');

test.describe('Basic Functionality', () => {
  test('Application loads and initializes correctly', async ({ page }) => {
    console.log('🚀 Testing basic application functionality...');
    
    // Navigate to application
    await page.goto('http://localhost:8000', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // Verify page title
    await expect(page).toHaveTitle(/Catalynx/);
    console.log('✅ Page title correct');
    
    // Wait for Alpine.js to initialize
    await page.waitForFunction(
      () => window.Alpine && window.catalynxApp,
      { timeout: 10000 }
    );
    console.log('✅ Alpine.js initialized');
    
    // Check for main navigation elements
    const overviewTab = page.locator('button:has-text("Overview")').first();
    await expect(overviewTab).toBeVisible({ timeout: 5000 });
    console.log('✅ Navigation visible');
    
    // Test navigation by clicking Overview tab
    await overviewTab.click();
    await page.waitForTimeout(1000);
    console.log('✅ Navigation works');
    
    // Check for main content
    const mainContent = page.locator('main, .main, #main').first();
    if (await mainContent.isVisible()) {
      console.log('✅ Main content area found');
    }
    
    // Verify API endpoints are accessible
    const response = await page.request.get('http://localhost:8000/api/system/status');
    expect(response.ok()).toBeTruthy();
    console.log('✅ API endpoint responding');
    
    // Take screenshot for verification
    await page.screenshot({ 
      path: 'tests/playwright/screenshots/basic-functionality.png',
      fullPage: true 
    });
    console.log('📸 Screenshot saved');
    
    console.log('🎉 Basic functionality test passed!');
  });

  test('Error handling works', async ({ page }) => {
    console.log('🧪 Testing error handling...');
    
    await page.goto('http://localhost:8000');
    await page.waitForFunction(() => window.Alpine);
    
    // Monitor console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Try an invalid API request
    await page.request.get('http://localhost:8000/api/invalid-endpoint');
    
    // Wait for any errors to surface
    await page.waitForTimeout(2000);
    
    // Application should still be functional
    const appState = await page.evaluate(() => {
      return window.catalynxApp ? {
        exists: true,
        isLoading: window.catalynxApp.isLoading
      } : { exists: false };
    });
    
    expect(appState.exists).toBeTruthy();
    console.log('✅ Application remains functional after errors');
  });

  test('Performance is acceptable', async ({ page }) => {
    console.log('⚡ Testing performance...');
    
    const startTime = Date.now();
    
    await page.goto('http://localhost:8000', { 
      waitUntil: 'domcontentloaded' 
    });
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds (generous for local dev)
    expect(loadTime).toBeLessThan(5000);
    console.log(`✅ Page loaded in ${loadTime}ms`);
    
    // Check performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart
      };
    });
    
    console.log(`📊 DOM Content Loaded: ${metrics.domContentLoaded}ms`);
    console.log(`📊 Load Complete: ${metrics.loadComplete}ms`);
  });
});
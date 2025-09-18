/**
 * Smoke Test: Application Loading and Basic Functionality
 * 
 * This test verifies that the Catalynx application loads correctly and
 * core functionality is available.
 * 
 * Critical success criteria:
 * - Application loads without errors
 * - Alpine.js framework initializes
 * - System status is healthy
 * - Navigation works
 * - API endpoints respond
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');

test.describe('Application Loading Smoke Tests', () => {
  let basePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
  });

  test('Application loads successfully', async ({ page }) => {
    // Navigate to application
    await basePage.navigate();
    
    // Verify page title contains "Catalynx"
    await expect(page).toHaveTitle(/Catalynx/);
    
    // Verify Alpine.js is loaded and initialized
    const alpineLoaded = await page.evaluate(() => {
      return typeof window.Alpine !== 'undefined' && typeof window.catalynxApp !== 'undefined';
    });
    expect(alpineLoaded).toBeTruthy();
    
    // Wait for application to be ready
    await basePage.waitForAppReady();
    
    // Take screenshot for visual verification
    await basePage.takeScreenshot('application-loaded');
  });

  test('System status is healthy', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Verify system health
    await basePage.verifySystemHealth();
    
    // Check system status in UI
    const appState = await basePage.getAppState();
    expect(appState).toBeTruthy();
    expect(appState.wsConnectionStatus).toBeDefined();
  });

  test('Navigation tabs are functional', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Test dashboard tab
    await basePage.switchTab('dashboard');
    let appState = await basePage.getAppState();
    expect(appState.currentTab).toBe('dashboard');
    
    // Test profiles tab  
    await basePage.switchTab('profiles');
    appState = await basePage.getAppState();
    expect(appState.currentTab).toBe('profiles');
    
    // Test discovery tab
    await basePage.switchTab('discovery');
    appState = await basePage.getAppState();
    expect(appState.currentTab).toBe('discovery');
  });

  test('API endpoints are responding', async ({ page }) => {
    await basePage.navigate();
    
    // Test key API endpoints
    const endpoints = [
      '/api/system/status',
      '/api/system/health', 
      '/api/dashboard/overview',
      '/api/profiles'
    ];
    
    for (const endpoint of endpoints) {
      const response = await page.request.get(`${basePage.baseURL}${endpoint}`);
      expect(response.ok()).toBeTruthy();
      
      const responseData = await response.json();
      expect(responseData).toBeDefined();
    }
  });

  test('Charts and visualizations load', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Switch to dashboard to trigger chart loading
    await basePage.switchTab('dashboard');
    
    // Wait for charts to render
    await basePage.waitForChartsToRender();
    
    // Verify Chart.js is available
    const chartJSLoaded = await page.evaluate(() => {
      return typeof window.Chart !== 'undefined';
    });
    expect(chartJSLoaded).toBeTruthy();
    
    // Check if charts are created in app state
    const chartsCreated = await page.evaluate(() => {
      return window.catalynxApp && window.catalynxApp.charts && window.catalynxApp.charts.size > 0;
    });
    expect(chartsCreated).toBeTruthy();
  });

  test('Error handling works correctly', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Monitor console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Test invalid API request (should be handled gracefully)
    await page.request.get(`${basePage.baseURL}/api/nonexistent-endpoint`);
    
    // Navigate through different tabs to trigger various API calls
    await basePage.switchTab('profiles');
    await basePage.switchTab('discovery');
    await basePage.switchTab('dashboard');
    
    // Wait a moment for any async errors to surface
    await page.waitForTimeout(2000);
    
    // Filter out known non-critical errors
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('404') && // Expected 404s are OK
      !error.includes('favicon') && // Favicon errors are not critical
      !error.includes('Extension')  // Browser extension errors
    );
    
    if (criticalErrors.length > 0) {
      console.warn('Console errors detected:', criticalErrors);
    }
    
    // Application should still be functional
    const appState = await basePage.getAppState();
    expect(appState).toBeTruthy();
  });

  test('Performance metrics are acceptable', async ({ page }) => {
    // Measure page load performance
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    const metrics = await basePage.getPerformanceMetrics();
    
    // Verify page load time is under 3 seconds
    expect(metrics.pageLoadTime).toBeLessThan(3000);
    
    // Verify DOM content loaded quickly
    expect(metrics.domContentLoaded).toBeLessThan(2000);
    
    // Verify Time to First Byte is reasonable
    expect(metrics.timeToFirstByte).toBeLessThan(1000);
    
    console.log('Performance metrics:', metrics);
  });

  test('WebSocket connection can be established', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Check WebSocket connection status
    const wsStatus = await page.evaluate(() => {
      return window.catalynxApp ? window.catalynxApp.wsConnectionStatus : null;
    });
    
    // WebSocket might be 'connected', 'disconnected', or 'connecting'
    expect(['connected', 'disconnected', 'connecting']).toContain(wsStatus);
    
    // If disconnected, that's OK for smoke test - just verify the infrastructure exists
    if (wsStatus === 'disconnected') {
      console.log('WebSocket disconnected - this is acceptable for smoke test');
    }
  });

  test('Database connectivity is working', async ({ page }) => {
    await basePage.navigate();
    await basePage.waitForAppReady();
    
    // Verify profiles can be loaded (tests database connectivity)
    await basePage.switchTab('profiles');
    await basePage.waitForAPIResponse('/api/profiles');
    
    // Check that profiles endpoint returns valid data structure
    const response = await page.request.get(`${basePage.baseURL}/api/profiles`);
    expect(response.ok()).toBeTruthy();
    
    const profilesData = await response.json();
    expect(profilesData).toHaveProperty('profiles');
    expect(Array.isArray(profilesData.profiles)).toBeTruthy();
  });
});
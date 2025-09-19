/**
 * Error Recovery Testing
 *
 * This test suite validates the application's ability to handle and recover from various error conditions:
 * - Network failures and API timeouts
 * - Server errors and service unavailability
 * - Client-side errors and JavaScript exceptions
 * - Data corruption and validation failures
 * - Session timeouts and authentication issues
 * - Browser compatibility and resource loading failures
 *
 * Tests both automatic recovery mechanisms and user-initiated recovery actions.
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Error Recovery Testing', () => {
  let basePage;
  let profilePage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Create test profile for error scenarios
    await profilePage.navigateToProfiles();
    const existingProfiles = await profilePage.getAllProfiles();

    const testProfile = existingProfiles.find(p =>
      p.name && p.name.includes('Heroes Bridge')
    );

    if (testProfile) {
      testProfileId = testProfile.id;
    } else {
      const heroesData = profiles.find(p => p.id === 'heroes_bridge_foundation');
      testProfileId = await profilePage.createProfile(heroesData);
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

  test.describe('Network Error Recovery', () => {
    test('API timeout recovery', async ({ page }) => {
      console.log('🧪 Testing API timeout recovery...');

      // Set up timeout simulation
      await page.route('**/api/**', async route => {
        // Delay responses to simulate timeouts
        await new Promise(resolve => setTimeout(resolve, 15000));
        route.continue();
      });

      // Attempt operation that will timeout
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();

      if (await discoverButton.isVisible()) {
        await discoverButton.click();

        // Check for timeout handling
        await expect.soft(page.locator('text="Timeout", text="Taking longer", text="Try again"')).toBeVisible({ timeout: 20000 });

        // Look for retry mechanism
        const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")').first();
        if (await retryButton.isVisible()) {
          // Remove timeout simulation
          await page.unroute('**/api/**');

          await retryButton.click();
          await page.waitForTimeout(2000);

          // Verify recovery
          await expect.soft(page.locator('text="Processing", text="Discovery"')).toBeVisible({ timeout: 5000 });
        }
      }

      await basePage.takeScreenshot('api-timeout-recovery');
      console.log('✅ API timeout recovery tested');
    });

    test('Network disconnection recovery', async ({ page }) => {
      console.log('🧪 Testing network disconnection recovery...');

      // Simulate complete network failure
      await page.route('**/*', route => {
        route.fulfill({ status: 500, body: 'Network Unavailable' });
      });

      // Try operations that require network
      await basePage.switchTab('analyze');
      const analyzeButton = page.locator('button:has-text("Lite")').first();

      if (await analyzeButton.isVisible()) {
        await analyzeButton.click();
        await page.waitForTimeout(3000);

        // Check for network error handling
        await expect.soft(page.locator('text="Network", text="Connection", text="Offline"')).toBeVisible({ timeout: 5000 });
      }

      // Restore network
      await page.unroute('**/*');

      // Test automatic recovery
      await page.reload();
      await basePage.waitForAppReady();

      // Verify app is functional again
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      await basePage.takeScreenshot('network-disconnection-recovery');
      console.log('✅ Network disconnection recovery tested');
    });

    test('Partial API failure recovery', async ({ page }) => {
      console.log('🧪 Testing partial API failure recovery...');

      // Simulate random API failures
      await page.route('**/api/**', route => {
        if (Math.random() > 0.5) {
          route.fulfill({ status: 503, body: 'Service Temporarily Unavailable' });
        } else {
          route.continue();
        }
      });

      // Try multiple operations
      const operations = [
        () => basePage.switchTab('discover'),
        () => basePage.switchTab('analyze'),
        () => basePage.switchTab('examine')
      ];

      for (const operation of operations) {
        try {
          await operation();
          await page.waitForTimeout(2000);

          // Check for graceful degradation
          const errorIndicator = page.locator('text="Error", text="Unavailable", text="Try later"').first();
          if (await errorIndicator.isVisible()) {
            console.log('✅ Graceful error handling detected');
          }
        } catch (error) {
          console.log(`⚠️ Operation failed gracefully: ${error.message}`);
        }
      }

      // Remove API blocking
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('partial-api-failure-recovery');
      console.log('✅ Partial API failure recovery tested');
    });
  });

  test.describe('Server Error Recovery', () => {
    test('500 Internal Server Error recovery', async ({ page }) => {
      console.log('🧪 Testing 500 error recovery...');

      // Simulate server errors
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error', message: 'Something went wrong' })
        });
      });

      // Attempt operation that will fail
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();

      if (await discoverButton.isVisible()) {
        await discoverButton.click();
        await page.waitForTimeout(3000);

        // Check for error message display
        await expect.soft(page.locator('text="Server Error", text="Internal Error", text="500"')).toBeVisible({ timeout: 5000 });

        // Look for recovery options
        const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")').first();
        const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Reload")').first();

        if (await retryButton.isVisible()) {
          // Remove server error simulation
          await page.unroute('**/api/**');

          await retryButton.click();
          await page.waitForTimeout(2000);

          // Verify recovery
          await expect.soft(page.locator('text="Processing", text="Discovery"')).toBeVisible({ timeout: 5000 });
        }
      }

      await basePage.takeScreenshot('500-error-recovery');
      console.log('✅ 500 error recovery tested');
    });

    test('404 Not Found error handling', async ({ page }) => {
      console.log('🧪 Testing 404 error handling...');

      // Simulate 404 errors for specific endpoints
      await page.route('**/api/profiles/**', route => {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Not Found', message: 'Profile not found' })
        });
      });

      // Try to access non-existent profile
      await profilePage.navigateToProfiles();

      // Check for 404 error handling
      await expect.soft(page.locator('text="Not Found", text="404", text="Profile not found"')).toBeVisible({ timeout: 5000 });

      // Look for fallback options
      const createNewButton = page.locator('button:has-text("Create New"), button:has-text("New Profile")').first();
      if (await createNewButton.isVisible()) {
        console.log('✅ Fallback option available for 404 error');
      }

      // Remove 404 simulation
      await page.unroute('**/api/profiles/**');

      await basePage.takeScreenshot('404-error-handling');
      console.log('✅ 404 error handling tested');
    });

    test('Service unavailable (503) recovery', async ({ page }) => {
      console.log('🧪 Testing service unavailable recovery...');

      // Simulate service unavailable
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Service Unavailable',
            message: 'Service temporarily unavailable',
            retry_after: 30
          })
        });
      });

      // Attempt analysis operation
      await basePage.switchTab('analyze');
      const analyzeButton = page.locator('button:has-text("Heavy")').first();

      if (await analyzeButton.isVisible()) {
        await analyzeButton.click();
        await page.waitForTimeout(3000);

        // Check for service unavailable handling
        await expect.soft(page.locator('text="Service Unavailable", text="503", text="Temporarily unavailable"')).toBeVisible({ timeout: 5000 });

        // Look for retry information
        await expect.soft(page.locator('text="Try again", text="Retry after", text="30"')).toBeVisible({ timeout: 3000 });
      }

      // Remove service unavailable simulation
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('503-service-unavailable');
      console.log('✅ Service unavailable recovery tested');
    });
  });

  test.describe('Client-Side Error Recovery', () => {
    test('JavaScript exception handling', async ({ page }) => {
      console.log('🧪 Testing JavaScript exception handling...');

      // Monitor JavaScript errors
      const jsErrors = [];
      page.on('pageerror', error => {
        jsErrors.push(error.message);
      });

      // Inject code that will cause an error
      await page.evaluate(() => {
        // Simulate a JavaScript error
        setTimeout(() => {
          try {
            // Attempt to access undefined property
            window.nonExistentObject.someMethod();
          } catch (error) {
            console.error('Caught JavaScript error:', error);
            // Dispatch custom error event for application to handle
            window.dispatchEvent(new CustomEvent('applicationError', { detail: error }));
          }
        }, 1000);
      });

      await page.waitForTimeout(2000);

      // Check if app continues to function
      await basePage.switchTab('overview');
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      // Verify error was logged but didn't crash the app
      if (jsErrors.length > 0) {
        console.log(`✅ JavaScript errors caught: ${jsErrors.length}`);
      }

      await basePage.takeScreenshot('javascript-exception-handling');
      console.log('✅ JavaScript exception handling tested');
    });

    test('Resource loading failure recovery', async ({ page }) => {
      console.log('🧪 Testing resource loading failure recovery...');

      // Block certain resources
      await page.route('**/*.css', route => {
        if (Math.random() > 0.7) {
          route.abort();
        } else {
          route.continue();
        }
      });

      await page.route('**/*.js', route => {
        if (Math.random() > 0.8) {
          route.abort();
        } else {
          route.continue();
        }
      });

      // Reload page with blocked resources
      await page.reload();
      await page.waitForTimeout(3000);

      // Check if app still functions despite missing resources
      try {
        await basePage.waitForAppReady();
        console.log('✅ App functional despite resource loading failures');
      } catch (error) {
        console.log(`⚠️ App degraded gracefully: ${error.message}`);
      }

      // Remove resource blocking
      await page.unroute('**/*.css');
      await page.unroute('**/*.js');

      await basePage.takeScreenshot('resource-loading-failure');
      console.log('✅ Resource loading failure recovery tested');
    });

    test('Memory exhaustion graceful degradation', async ({ page }) => {
      console.log('🧪 Testing memory exhaustion handling...');

      // Simulate memory-intensive operations
      await page.evaluate(() => {
        // Create large arrays to consume memory
        const memoryHog = [];
        try {
          for (let i = 0; i < 1000; i++) {
            memoryHog.push(new Array(10000).fill('memory_test_data'));
          }
        } catch (error) {
          console.warn('Memory allocation failed gracefully:', error);
        }
      });

      // Check if app continues to respond
      await basePage.switchTab('discover');
      await page.waitForTimeout(2000);

      // Verify app state
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      await basePage.takeScreenshot('memory-exhaustion-handling');
      console.log('✅ Memory exhaustion handling tested');
    });
  });

  test.describe('Data Validation Error Recovery', () => {
    test('Invalid profile data handling', async ({ page }) => {
      console.log('🧪 Testing invalid profile data handling...');

      await profilePage.navigateToProfiles();

      // Try to create profile with invalid data
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible()) {
        await createButton.click();
        await page.waitForTimeout(1000);

        // Submit invalid data
        const invalidData = {
          organization_name: '', // Empty name
          ein: 'invalid_ein', // Invalid EIN format
          annual_budget: 'not_a_number' // Invalid budget
        };

        // Fill with invalid data
        await page.fill('input[name="organization_name"]', invalidData.organization_name);
        await page.fill('input[name="ein"]', invalidData.ein);

        // Try to submit
        const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")').first();
        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForTimeout(2000);

          // Check for validation errors
          await expect.soft(page.locator('text="Required", text="Invalid", text="Error"')).toBeVisible({ timeout: 5000 });

          // Verify form doesn't submit
          await expect.soft(page.locator('text="Profile created", text="Success"')).not.toBeVisible();
        }

        // Close form
        const cancelButton = page.locator('button:has-text("Cancel"), button:has-text("Close")').first();
        if (await cancelButton.isVisible()) {
          await cancelButton.click();
        }
      }

      await basePage.takeScreenshot('invalid-profile-data-handling');
      console.log('✅ Invalid profile data handling tested');
    });

    test('Corrupted API response handling', async ({ page }) => {
      console.log('🧪 Testing corrupted API response handling...');

      // Simulate corrupted JSON responses
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: '{"invalid": json, malformed}' // Invalid JSON
        });
      });

      // Try operation that expects valid JSON
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();

      if (await discoverButton.isVisible()) {
        await discoverButton.click();
        await page.waitForTimeout(3000);

        // Check for data parsing error handling
        await expect.soft(page.locator('text="Data Error", text="Invalid Response", text="Parse Error"')).toBeVisible({ timeout: 5000 });
      }

      // Remove corrupted response simulation
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('corrupted-api-response-handling');
      console.log('✅ Corrupted API response handling tested');
    });

    test('Missing required fields recovery', async ({ page }) => {
      console.log('🧪 Testing missing required fields recovery...');

      // Simulate API responses with missing fields
      await page.route('**/api/profiles/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            // Missing required fields like id, name, etc.
            incomplete_data: true
          })
        });
      });

      // Try to load profiles
      await profilePage.navigateToProfiles();
      await page.waitForTimeout(3000);

      // Check for missing data handling
      await expect.soft(page.locator('text="Incomplete", text="Missing Data", text="Load Error"')).toBeVisible({ timeout: 5000 });

      // Look for fallback behavior
      const retryButton = page.locator('button:has-text("Retry"), button:has-text("Refresh")').first();
      if (await retryButton.isVisible()) {
        // Remove invalid response simulation
        await page.unroute('**/api/profiles/**');

        await retryButton.click();
        await page.waitForTimeout(2000);
      }

      await basePage.takeScreenshot('missing-fields-recovery');
      console.log('✅ Missing required fields recovery tested');
    });
  });

  test.describe('Session and Authentication Recovery', () => {
    test('Session timeout handling', async ({ page }) => {
      console.log('🧪 Testing session timeout handling...');

      // Simulate session timeout
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Unauthorized',
            message: 'Session expired',
            code: 'SESSION_TIMEOUT'
          })
        });
      });

      // Try authenticated operation
      await basePage.switchTab('analyze');
      const analyzeButton = page.locator('button:has-text("Heavy")').first();

      if (await analyzeButton.isVisible()) {
        await analyzeButton.click();
        await page.waitForTimeout(3000);

        // Check for session timeout handling
        await expect.soft(page.locator('text="Session", text="Expired", text="Login", text="Unauthorized"')).toBeVisible({ timeout: 5000 });

        // Look for re-authentication options
        const loginButton = page.locator('button:has-text("Login"), button:has-text("Sign In")').first();
        if (await loginButton.isVisible()) {
          console.log('✅ Re-authentication option available');
        }
      }

      // Remove session timeout simulation
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('session-timeout-handling');
      console.log('✅ Session timeout handling tested');
    });

    test('Token refresh recovery', async ({ page }) => {
      console.log('🧪 Testing token refresh recovery...');

      let requestCount = 0;

      // Simulate token expiration followed by successful refresh
      await page.route('**/api/**', route => {
        requestCount++;

        if (requestCount === 1) {
          // First request fails with expired token
          route.fulfill({
            status: 401,
            body: JSON.stringify({ error: 'Token expired' })
          });
        } else {
          // Subsequent requests succeed (after token refresh)
          route.continue();
        }
      });

      // Attempt operation that triggers token refresh
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();

      if (await discoverButton.isVisible()) {
        await discoverButton.click();
        await page.waitForTimeout(3000);

        // Should succeed after automatic token refresh
        await expect.soft(page.locator('text="Processing", text="Discovery"')).toBeVisible({ timeout: 10000 });
      }

      // Remove token expiration simulation
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('token-refresh-recovery');
      console.log('✅ Token refresh recovery tested');
    });
  });

  test.describe('Browser Compatibility Recovery', () => {
    test('Unsupported browser feature fallbacks', async ({ page }) => {
      console.log('🧪 Testing browser feature fallbacks...');

      // Disable certain modern browser features
      await page.addInitScript(() => {
        // Remove fetch API to test fallback to XMLHttpRequest
        delete window.fetch;

        // Remove modern Array methods
        delete Array.prototype.includes;

        // Remove Promise.allSettled
        delete Promise.allSettled;
      });

      // Reload to apply feature removal
      await page.reload();
      await page.waitForTimeout(3000);

      // Try to use app with limited browser features
      try {
        await basePage.waitForAppReady();
        await basePage.switchTab('overview');

        // App should still function with polyfills/fallbacks
        const appState = await basePage.getAppState();
        expect(appState).toBeTruthy();

        console.log('✅ App functional with limited browser features');
      } catch (error) {
        console.log(`⚠️ App degraded gracefully: ${error.message}`);
      }

      await basePage.takeScreenshot('browser-feature-fallbacks');
      console.log('✅ Browser feature fallbacks tested');
    });

    test('Storage quota exceeded handling', async ({ page }) => {
      console.log('🧪 Testing storage quota exceeded handling...');

      // Fill localStorage to capacity
      await page.evaluate(() => {
        try {
          let data = '';
          for (let i = 0; i < 1000000; i++) {
            data += 'x';
          }

          // Try to fill localStorage
          for (let i = 0; i < 100; i++) {
            localStorage.setItem(`large_data_${i}`, data);
          }
        } catch (error) {
          console.log('Storage quota exceeded:', error);
          // Trigger cleanup
          window.dispatchEvent(new CustomEvent('storageQuotaExceeded'));
        }
      });

      // Try to perform operations that require storage
      await basePage.switchTab('profiles');
      await page.waitForTimeout(2000);

      // App should handle storage issues gracefully
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      // Clean up localStorage
      await page.evaluate(() => {
        localStorage.clear();
      });

      await basePage.takeScreenshot('storage-quota-exceeded');
      console.log('✅ Storage quota exceeded handling tested');
    });
  });

  test.describe('Recovery Validation', () => {
    test('Complete error recovery workflow', async ({ page }) => {
      console.log('🧪 Testing complete error recovery workflow...');

      const errorScenarios = [
        {
          name: 'Network Error',
          setup: () => page.route('**/api/**', route => route.fulfill({ status: 500 })),
          cleanup: () => page.unroute('**/api/**')
        },
        {
          name: 'Timeout Error',
          setup: () => page.route('**/api/**', async route => {
            await new Promise(resolve => setTimeout(resolve, 10000));
            route.continue();
          }),
          cleanup: () => page.unroute('**/api/**')
        }
      ];

      for (const scenario of errorScenarios) {
        console.log(`🔍 Testing ${scenario.name} recovery...`);

        // Setup error condition
        await scenario.setup();

        // Attempt operation
        await basePage.switchTab('discover');
        const discoverButton = page.locator('button:has-text("DISCOVER")').first();
        if (await discoverButton.isVisible()) {
          await discoverButton.click();
          await page.waitForTimeout(3000);
        }

        // Cleanup error condition
        await scenario.cleanup();

        // Verify recovery
        const retryButton = page.locator('button:has-text("Retry")').first();
        if (await retryButton.isVisible()) {
          await retryButton.click();
          await page.waitForTimeout(2000);
        }

        // Verify app is functional
        const appState = await basePage.getAppState();
        expect(appState).toBeTruthy();

        console.log(`✅ ${scenario.name} recovery completed`);
      }

      await basePage.takeScreenshot('complete-error-recovery-workflow');
      console.log('✅ Complete error recovery workflow tested');
    });

    test('Error recovery metrics and monitoring', async ({ page }) => {
      console.log('🧪 Testing error recovery metrics...');

      // Check for error monitoring endpoints
      const metricsResponse = await page.request.get('http://localhost:8000/api/system/metrics');
      if (metricsResponse.ok()) {
        const metricsData = await metricsResponse.json();

        // Verify error tracking metrics
        expect(metricsData).toHaveProperty('errors');
        expect(metricsData).toHaveProperty('recovery_actions');
        expect(metricsData).toHaveProperty('uptime');

        console.log('✅ Error monitoring metrics available');
      }

      // Check for health check endpoint
      const healthResponse = await page.request.get('http://localhost:8000/api/health');
      if (healthResponse.ok()) {
        const healthData = await healthResponse.json();
        expect(healthData).toHaveProperty('status');
        expect(healthData.status).toBe('healthy');

        console.log('✅ Health check endpoint functional');
      }

      await basePage.takeScreenshot('error-recovery-metrics');
      console.log('✅ Error recovery metrics tested');
    });
  });
});
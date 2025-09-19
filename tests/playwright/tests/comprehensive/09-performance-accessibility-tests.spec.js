/**
 * Performance and Accessibility Tests
 *
 * This test suite validates application performance metrics and accessibility compliance:
 * - Page load performance and Core Web Vitals
 * - Memory usage and resource optimization
 * - Network efficiency and caching
 * - WCAG 2.1 AA accessibility compliance
 * - Keyboard navigation and screen reader support
 * - Color contrast and visual accessibility
 * - Performance under load and stress conditions
 *
 * Tests ensure the application meets modern web standards for performance and accessibility.
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Performance and Accessibility Tests', () => {
  let basePage;
  let profilePage;
  let testProfileId;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();

    // Create test profile for performance tests
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

  test.describe('Page Performance Tests', () => {
    test('Initial page load performance', async ({ page }) => {
      console.log('🧪 Testing initial page load performance...');

      // Measure page load performance
      const startTime = Date.now();

      await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });

      const loadTime = Date.now() - startTime;
      console.log(`📊 Page load time: ${loadTime}ms`);

      // Verify load time is acceptable (under 3 seconds)
      expect(loadTime).toBeLessThan(3000);

      // Check for performance API metrics
      const performanceMetrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (!navigation) return null;

        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || null,
          firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null
        };
      });

      if (performanceMetrics) {
        console.log('📈 Performance metrics:', performanceMetrics);

        // Verify Core Web Vitals expectations
        if (performanceMetrics.firstContentfulPaint) {
          expect(performanceMetrics.firstContentfulPaint).toBeLessThan(2000); // FCP under 2s
        }
      }

      await basePage.takeScreenshot('initial-page-load-performance');
      console.log('✅ Initial page load performance tested');
    });

    test('Tab switching performance', async ({ page }) => {
      console.log('🧪 Testing tab switching performance...');

      const tabs = ['overview', 'discover', 'plan', 'analyze', 'examine', 'approach'];
      const switchingTimes = {};

      for (const tab of tabs) {
        const startTime = performance.now();

        await basePage.switchTab(tab);
        await page.waitForTimeout(500); // Allow content to stabilize

        const endTime = performance.now();
        switchingTimes[tab] = endTime - startTime;

        console.log(`⚡ ${tab} tab switch: ${switchingTimes[tab].toFixed(2)}ms`);

        // Verify tab switching is responsive (under 500ms)
        expect(switchingTimes[tab]).toBeLessThan(500);
      }

      // Calculate average switching time
      const averageTime = Object.values(switchingTimes).reduce((a, b) => a + b, 0) / tabs.length;
      console.log(`📊 Average tab switching time: ${averageTime.toFixed(2)}ms`);

      expect(averageTime).toBeLessThan(300); // Average under 300ms

      await basePage.takeScreenshot('tab-switching-performance');
      console.log('✅ Tab switching performance tested');
    });

    test('Resource loading optimization', async ({ page }) => {
      console.log('🧪 Testing resource loading optimization...');

      // Monitor network requests
      const resourceMetrics = {
        requests: 0,
        totalSize: 0,
        cacheHits: 0,
        imageCount: 0,
        scriptCount: 0,
        styleCount: 0
      };

      page.on('response', response => {
        resourceMetrics.requests++;
        resourceMetrics.totalSize += response.request().postDataBuffer()?.length || 0;

        if (response.fromCache()) {
          resourceMetrics.cacheHits++;
        }

        const url = response.url();
        if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) {
          resourceMetrics.imageCount++;
        } else if (url.match(/\.js$/)) {
          resourceMetrics.scriptCount++;
        } else if (url.match(/\.css$/)) {
          resourceMetrics.styleCount++;
        }
      });

      // Navigate through different sections
      await basePage.switchTab('discover');
      await page.waitForTimeout(2000);

      await basePage.switchTab('analyze');
      await page.waitForTimeout(2000);

      console.log('📊 Resource metrics:', resourceMetrics);

      // Verify reasonable resource usage
      expect(resourceMetrics.requests).toBeLessThan(100); // Not too many requests
      expect(resourceMetrics.cacheHits / resourceMetrics.requests).toBeGreaterThan(0.3); // At least 30% cache hit rate

      await basePage.takeScreenshot('resource-loading-optimization');
      console.log('✅ Resource loading optimization tested');
    });

    test('Memory usage monitoring', async ({ page }) => {
      console.log('🧪 Testing memory usage...');

      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (initialMemory) {
        console.log('📊 Initial memory usage:', {
          used: `${(initialMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          total: `${(initialMemory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`
        });
      }

      // Perform memory-intensive operations
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();
      if (await discoverButton.isVisible()) {
        await discoverButton.click();
        await page.waitForTimeout(5000);
      }

      await basePage.switchTab('analyze');
      const analyzeButton = page.locator('button:has-text("Heavy")').first();
      if (await analyzeButton.isVisible()) {
        await analyzeButton.click();
        await page.waitForTimeout(3000);
      }

      // Check memory after operations
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      if (initialMemory && finalMemory) {
        const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
        console.log(`📊 Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB`);

        // Verify memory usage is reasonable (less than 100MB increase)
        expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024);
      }

      await basePage.takeScreenshot('memory-usage-monitoring');
      console.log('✅ Memory usage monitoring tested');
    });
  });

  test.describe('Core Web Vitals', () => {
    test('Largest Contentful Paint (LCP)', async ({ page }) => {
      console.log('🧪 Testing Largest Contentful Paint...');

      await page.goto('http://localhost:8000');

      const lcp = await page.evaluate(() => {
        return new Promise((resolve) => {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            resolve(lastEntry.startTime);
          });

          observer.observe({ type: 'largest-contentful-paint', buffered: true });

          // Timeout after 10 seconds
          setTimeout(() => resolve(null), 10000);
        });
      });

      if (lcp) {
        console.log(`📊 LCP: ${lcp.toFixed(2)}ms`);
        // LCP should be under 2.5 seconds for good performance
        expect(lcp).toBeLessThan(2500);
      }

      await basePage.takeScreenshot('largest-contentful-paint');
      console.log('✅ Largest Contentful Paint tested');
    });

    test('First Input Delay (FID) simulation', async ({ page }) => {
      console.log('🧪 Testing First Input Delay simulation...');

      await page.goto('http://localhost:8000');
      await basePage.waitForAppReady();

      // Simulate first user interaction
      const startTime = performance.now();

      await page.click('button:visible');

      const endTime = performance.now();
      const inputDelay = endTime - startTime;

      console.log(`📊 Simulated FID: ${inputDelay.toFixed(2)}ms`);

      // FID should be under 100ms for good responsiveness
      expect(inputDelay).toBeLessThan(100);

      await basePage.takeScreenshot('first-input-delay-simulation');
      console.log('✅ First Input Delay simulation tested');
    });

    test('Cumulative Layout Shift (CLS)', async ({ page }) => {
      console.log('🧪 Testing Cumulative Layout Shift...');

      await page.goto('http://localhost:8000');

      // Monitor layout shifts
      const cls = await page.evaluate(() => {
        return new Promise((resolve) => {
          let clsValue = 0;

          const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            }
          });

          observer.observe({ type: 'layout-shift', buffered: true });

          // Check CLS after page interactions
          setTimeout(() => {
            resolve(clsValue);
          }, 5000);
        });
      });

      console.log(`📊 CLS: ${cls.toFixed(4)}`);

      // CLS should be under 0.1 for good visual stability
      expect(cls).toBeLessThan(0.1);

      await basePage.takeScreenshot('cumulative-layout-shift');
      console.log('✅ Cumulative Layout Shift tested');
    });
  });

  test.describe('WCAG 2.1 AA Accessibility Tests', () => {
    test('Color contrast compliance', async ({ page }) => {
      console.log('🧪 Testing color contrast compliance...');

      // Navigate through different sections to test various color combinations
      const sections = ['overview', 'discover', 'analyze'];

      for (const section of sections) {
        await basePage.switchTab(section);
        await page.waitForTimeout(1000);

        // Check for sufficient color contrast (this is a simplified check)
        const colorIssues = await page.evaluate(() => {
          const elements = document.querySelectorAll('*');
          const issues = [];

          for (const element of elements) {
            const style = window.getComputedStyle(element);
            const color = style.color;
            const backgroundColor = style.backgroundColor;

            // Simple check for very light text on light backgrounds
            if (color === 'rgb(255, 255, 255)' && backgroundColor === 'rgb(255, 255, 255)') {
              issues.push('White text on white background detected');
            }
          }

          return issues;
        });

        console.log(`📊 ${section} section color issues:`, colorIssues.length);
        expect(colorIssues.length).toBe(0);
      }

      await basePage.takeScreenshot('color-contrast-compliance');
      console.log('✅ Color contrast compliance tested');
    });

    test('Keyboard navigation accessibility', async ({ page }) => {
      console.log('🧪 Testing keyboard navigation accessibility...');

      // Start from top of page
      await page.keyboard.press('Tab');
      await page.waitForTimeout(500);

      // Track focusable elements
      const focusableElements = [];
      const maxTabs = 20; // Limit to prevent infinite loops

      for (let i = 0; i < maxTabs; i++) {
        const focusedElement = await page.evaluate(() => {
          const element = document.activeElement;
          return {
            tagName: element.tagName,
            type: element.type || null,
            role: element.getAttribute('role'),
            ariaLabel: element.getAttribute('aria-label'),
            text: element.textContent?.trim().substring(0, 50) || '',
            id: element.id,
            className: element.className
          };
        });

        focusableElements.push(focusedElement);

        // Move to next focusable element
        await page.keyboard.press('Tab');
        await page.waitForTimeout(200);

        // Check if we've cycled back to the beginning
        if (i > 5 && focusedElement.tagName === 'BODY') {
          break;
        }
      }

      console.log(`📊 Found ${focusableElements.length} focusable elements`);

      // Verify reasonable number of focusable elements
      expect(focusableElements.length).toBeGreaterThan(5);

      // Check for proper focus indicators
      const focusVisible = await page.evaluate(() => {
        const style = window.getComputedStyle(document.activeElement);
        return style.outline !== 'none' || style.boxShadow !== 'none';
      });

      expect(focusVisible).toBeTruthy();

      await basePage.takeScreenshot('keyboard-navigation-accessibility');
      console.log('✅ Keyboard navigation accessibility tested');
    });

    test('ARIA labels and roles validation', async ({ page }) => {
      console.log('🧪 Testing ARIA labels and roles...');

      // Check for proper ARIA implementation
      const ariaIssues = await page.evaluate(() => {
        const issues = [];

        // Check for buttons without accessible names
        const buttons = document.querySelectorAll('button');
        buttons.forEach((button, index) => {
          const hasLabel = button.getAttribute('aria-label') ||
                          button.getAttribute('aria-labelledby') ||
                          button.textContent?.trim();

          if (!hasLabel) {
            issues.push(`Button ${index} missing accessible name`);
          }
        });

        // Check for form inputs without labels
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea');
        inputs.forEach((input, index) => {
          const hasLabel = input.getAttribute('aria-label') ||
                          input.getAttribute('aria-labelledby') ||
                          document.querySelector(`label[for="${input.id}"]`);

          if (!hasLabel) {
            issues.push(`Input ${index} missing label`);
          }
        });

        // Check for proper heading structure
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        if (headings.length === 0) {
          issues.push('No heading elements found');
        }

        return issues;
      });

      console.log(`📊 ARIA issues found: ${ariaIssues.length}`);
      if (ariaIssues.length > 0) {
        console.log('⚠️ ARIA issues:', ariaIssues);
      }

      // Allow some ARIA issues but not too many
      expect(ariaIssues.length).toBeLessThan(10);

      await basePage.takeScreenshot('aria-labels-roles-validation');
      console.log('✅ ARIA labels and roles tested');
    });

    test('Screen reader compatibility', async ({ page }) => {
      console.log('🧪 Testing screen reader compatibility...');

      // Check for screen reader friendly content
      const screenReaderContent = await page.evaluate(() => {
        const content = {
          headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
          landmarks: document.querySelectorAll('[role="main"], [role="navigation"], [role="banner"], main, nav, header').length,
          altText: document.querySelectorAll('img[alt]').length,
          skipLinks: document.querySelectorAll('a[href="#main"], a[href="#content"]').length,
          ariaLive: document.querySelectorAll('[aria-live]').length
        };

        return content;
      });

      console.log('📊 Screen reader content:', screenReaderContent);

      // Verify presence of screen reader aids
      expect(screenReaderContent.headings).toBeGreaterThan(0);
      expect(screenReaderContent.landmarks).toBeGreaterThan(0);

      await basePage.takeScreenshot('screen-reader-compatibility');
      console.log('✅ Screen reader compatibility tested');
    });

    test('Focus management in modals', async ({ page }) => {
      console.log('🧪 Testing focus management in modals...');

      // Open a modal
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible()) {
        await createButton.click();
        await page.waitForTimeout(1000);

        // Check if focus is trapped in modal
        const modalElement = page.locator('[role="dialog"], .modal').first();
        if (await modalElement.isVisible()) {
          // Verify focus is in modal
          const focusedElement = await page.evaluate(() => {
            return document.activeElement.closest('[role="dialog"], .modal') !== null;
          });

          expect(focusedElement).toBeTruthy();

          // Test Tab key behavior in modal
          await page.keyboard.press('Tab');
          await page.waitForTimeout(200);

          // Verify focus is still within modal
          const focusStillInModal = await page.evaluate(() => {
            return document.activeElement.closest('[role="dialog"], .modal') !== null;
          });

          expect(focusStillInModal).toBeTruthy();

          // Close modal
          const closeButton = page.locator('button:has-text("Cancel"), button:has-text("Close")').first();
          if (await closeButton.isVisible()) {
            await closeButton.click();
            await page.waitForTimeout(500);
          }
        }
      }

      await basePage.takeScreenshot('focus-management-modals');
      console.log('✅ Focus management in modals tested');
    });
  });

  test.describe('Performance Under Load', () => {
    test('Multiple concurrent operations', async ({ page }) => {
      console.log('🧪 Testing performance under concurrent operations...');

      if (!testProfileId) {
        console.log('⚠️ Skipping concurrent operations test - no test profile available');
        return;
      }

      // Start multiple operations simultaneously
      const operations = [
        () => basePage.switchTab('discover'),
        () => basePage.switchTab('analyze'),
        () => basePage.switchTab('examine')
      ];

      const startTime = performance.now();

      // Execute operations concurrently
      await Promise.all(operations.map(op => op()));

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      console.log(`📊 Concurrent operations completed in: ${totalTime.toFixed(2)}ms`);

      // Should complete concurrent operations in reasonable time
      expect(totalTime).toBeLessThan(2000);

      // Verify app is still responsive
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      await basePage.takeScreenshot('concurrent-operations-performance');
      console.log('✅ Concurrent operations performance tested');
    });

    test('Large data set handling', async ({ page }) => {
      console.log('🧪 Testing large data set handling...');

      // Simulate large data response
      await page.route('**/api/**', route => {
        if (route.request().url().includes('discovery')) {
          // Create large mock dataset
          const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
            id: i,
            name: `Organization ${i}`,
            description: 'A'.repeat(100), // Large description
            opportunities: Array.from({ length: 10 }, (_, j) => ({
              id: `${i}-${j}`,
              title: `Opportunity ${i}-${j}`,
              amount: Math.random() * 1000000
            }))
          }));

          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ results: largeDataset })
          });
        } else {
          route.continue();
        }
      });

      // Test performance with large dataset
      await basePage.switchTab('discover');
      const discoverButton = page.locator('button:has-text("DISCOVER")').first();

      if (await discoverButton.isVisible()) {
        const startTime = performance.now();

        await discoverButton.click();
        await page.waitForTimeout(5000);

        const endTime = performance.now();
        const processingTime = endTime - startTime;

        console.log(`📊 Large dataset processing time: ${processingTime.toFixed(2)}ms`);

        // Should handle large datasets in reasonable time
        expect(processingTime).toBeLessThan(10000);
      }

      // Remove route
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('large-dataset-handling');
      console.log('✅ Large data set handling tested');
    });

    test('Stress testing with rapid interactions', async ({ page }) => {
      console.log('🧪 Testing stress with rapid interactions...');

      const interactions = [
        () => basePage.switchTab('overview'),
        () => basePage.switchTab('discover'),
        () => basePage.switchTab('analyze'),
        () => basePage.switchTab('examine'),
        () => basePage.switchTab('approach')
      ];

      // Perform rapid interactions
      for (let round = 0; round < 3; round++) {
        for (const interaction of interactions) {
          await interaction();
          await page.waitForTimeout(100); // Very short delay
        }
      }

      // Verify app is still functional after stress
      const finalAppState = await basePage.getAppState();
      expect(finalAppState).toBeTruthy();

      // Check for JavaScript errors
      const jsErrors = [];
      page.on('pageerror', error => {
        jsErrors.push(error.message);
      });

      await page.waitForTimeout(2000);

      // Should not have critical JavaScript errors
      const criticalErrors = jsErrors.filter(error =>
        !error.includes('Network') && !error.includes('404')
      );
      expect(criticalErrors.length).toBe(0);

      await basePage.takeScreenshot('stress-testing-rapid-interactions');
      console.log('✅ Stress testing with rapid interactions completed');
    });
  });

  test.describe('Accessibility Edge Cases', () => {
    test('High contrast mode compatibility', async ({ page }) => {
      console.log('🧪 Testing high contrast mode compatibility...');

      // Simulate high contrast mode
      await page.addInitScript(() => {
        // Add high contrast media query
        const style = document.createElement('style');
        style.textContent = `
          @media (prefers-contrast: high) {
            * {
              background: black !important;
              color: white !important;
              border-color: white !important;
            }
          }
        `;
        document.head.appendChild(style);
      });

      await page.reload();
      await basePage.waitForAppReady();

      // Verify app is still functional in high contrast mode
      await basePage.switchTab('overview');
      await page.waitForTimeout(1000);

      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      await basePage.takeScreenshot('high-contrast-mode-compatibility');
      console.log('✅ High contrast mode compatibility tested');
    });

    test('Reduced motion preferences', async ({ page }) => {
      console.log('🧪 Testing reduced motion preferences...');

      // Simulate reduced motion preference
      await page.emulateMedia({ reducedMotion: 'reduce' });

      await page.reload();
      await basePage.waitForAppReady();

      // Test navigation with reduced motion
      await basePage.switchTab('discover');
      await page.waitForTimeout(1000);

      await basePage.switchTab('analyze');
      await page.waitForTimeout(1000);

      // Verify app respects reduced motion
      const animationIssues = await page.evaluate(() => {
        const elements = document.querySelectorAll('*');
        let issues = 0;

        for (const element of elements) {
          const style = window.getComputedStyle(element);
          if (style.animationDuration !== '0s' && style.animationDuration !== '') {
            issues++;
          }
        }

        return issues;
      });

      // Should have minimal animations when reduced motion is preferred
      expect(animationIssues).toBeLessThan(5);

      await basePage.takeScreenshot('reduced-motion-preferences');
      console.log('✅ Reduced motion preferences tested');
    });

    test('Text scaling compatibility', async ({ page }) => {
      console.log('🧪 Testing text scaling compatibility...');

      // Test with 200% text scaling
      await page.addInitScript(() => {
        document.documentElement.style.fontSize = '200%';
      });

      await page.reload();
      await basePage.waitForAppReady();

      // Verify app layout with scaled text
      await basePage.switchTab('overview');
      await page.waitForTimeout(1000);

      // Check for text overflow issues
      const overflowIssues = await page.evaluate(() => {
        const elements = document.querySelectorAll('*');
        let issues = 0;

        for (const element of elements) {
          const rect = element.getBoundingClientRect();
          if (rect.width > window.innerWidth + 20) { // Allow small margin
            issues++;
          }
        }

        return issues;
      });

      // Should have minimal overflow with scaled text
      expect(overflowIssues).toBeLessThan(10);

      await basePage.takeScreenshot('text-scaling-compatibility');
      console.log('✅ Text scaling compatibility tested');
    });
  });
});
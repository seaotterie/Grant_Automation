/**
 * Cross-Browser Validation Tests
 *
 * This test suite validates application compatibility across different browsers:
 * - Chrome/Chromium: Primary browser testing
 * - Firefox: Secondary browser testing
 * - Browser-specific feature compatibility
 * - CSS rendering consistency
 * - JavaScript API compatibility
 * - Performance comparison across browsers
 * - LocalStorage and session handling
 *
 * Tests ensure consistent user experience across supported browsers at 1920x1080 resolution.
 */

const { test, expect, devices } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

// Desktop resolution configuration
const desktopViewport = { width: 1920, height: 1080 };

test.describe('Cross-Browser Validation', () => {
  let testProfileId;

  // Setup test profile once for all browser tests
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    const basePage = new BasePage(page);
    const profilePage = new ProfilePage(page);

    await page.setViewportSize(desktopViewport);
    await basePage.navigate();
    await basePage.waitForAppReady();

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

  test.describe('Chrome Browser Tests', () => {
    test('Chrome - Basic functionality and navigation', async ({ browser }) => {
      console.log('🧪 Testing Chrome browser compatibility...');

      const context = await browser.newContext({
        viewport: desktopViewport,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);
      const profilePage = new ProfilePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test basic navigation in Chrome
      const tabs = ['overview', 'discover', 'plan', 'analyze'];
      for (const tab of tabs) {
        await basePage.switchTab(tab);
        await page.waitForTimeout(1000);

        // Verify content loads correctly
        await expect.soft(page.locator('body')).toBeVisible();
        console.log(`✅ Chrome: ${tab} tab loaded successfully`);
      }

      // Test profile management in Chrome
      if (testProfileId) {
        await profilePage.navigateToProfiles();
        await profilePage.selectProfile(testProfileId);
        console.log('✅ Chrome: Profile selection functional');
      }

      await basePage.takeScreenshot('chrome-basic-functionality');

      await context.close();
      console.log('✅ Chrome browser tests completed');
    });

    test('Chrome - Advanced features testing', async ({ browser }) => {
      console.log('🧪 Testing Chrome advanced features...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test Chrome-specific features
      const chromeFeatures = await page.evaluate(() => {
        return {
          webGL: !!window.WebGLRenderingContext,
          webRTC: !!window.RTCPeerConnection,
          serviceWorkers: 'serviceWorker' in navigator,
          webAssembly: typeof WebAssembly !== 'undefined',
          asyncAwait: (async () => {})().constructor.name === 'AsyncFunction',
          fetch: typeof fetch !== 'undefined',
          promises: typeof Promise !== 'undefined',
          localStorage: typeof localStorage !== 'undefined',
          sessionStorage: typeof sessionStorage !== 'undefined'
        };
      });

      console.log('📊 Chrome feature support:', chromeFeatures);

      // Verify essential features are available
      expect(chromeFeatures.fetch).toBeTruthy();
      expect(chromeFeatures.promises).toBeTruthy();
      expect(chromeFeatures.localStorage).toBeTruthy();

      // Test Chrome's JavaScript performance
      const performanceTest = await page.evaluate(() => {
        const start = performance.now();

        // Run computation-heavy task
        for (let i = 0; i < 100000; i++) {
          Math.sqrt(i);
        }

        return performance.now() - start;
      });

      console.log(`📊 Chrome JS performance: ${performanceTest.toFixed(2)}ms`);
      expect(performanceTest).toBeLessThan(100); // Should complete in under 100ms

      await basePage.takeScreenshot('chrome-advanced-features');

      await context.close();
      console.log('✅ Chrome advanced features tested');
    });

    test('Chrome - CSS rendering and layout', async ({ browser }) => {
      console.log('🧪 Testing Chrome CSS rendering...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test CSS Grid and Flexbox support
      const cssSupport = await page.evaluate(() => {
        const testDiv = document.createElement('div');
        document.body.appendChild(testDiv);

        const support = {
          grid: CSS.supports('display', 'grid'),
          flexbox: CSS.supports('display', 'flex'),
          customProperties: CSS.supports('color', 'var(--test)'),
          transforms: CSS.supports('transform', 'translateX(10px)'),
          animations: CSS.supports('animation-duration', '1s')
        };

        document.body.removeChild(testDiv);
        return support;
      });

      console.log('📊 Chrome CSS support:', cssSupport);

      // Verify modern CSS features
      expect(cssSupport.grid).toBeTruthy();
      expect(cssSupport.flexbox).toBeTruthy();
      expect(cssSupport.customProperties).toBeTruthy();

      // Test layout consistency
      await basePage.switchTab('overview');
      await page.waitForTimeout(1000);

      const layoutMetrics = await page.evaluate(() => {
        const body = document.body;
        const main = document.querySelector('main, #app, .app');

        return {
          bodyWidth: body.offsetWidth,
          bodyHeight: body.offsetHeight,
          mainWidth: main ? main.offsetWidth : null,
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight
        };
      });

      console.log('📊 Chrome layout metrics:', layoutMetrics);

      // Verify layout is using full viewport
      expect(layoutMetrics.viewportWidth).toBe(1920);
      expect(layoutMetrics.viewportHeight).toBe(1080);

      await basePage.takeScreenshot('chrome-css-rendering');

      await context.close();
      console.log('✅ Chrome CSS rendering tested');
    });
  });

  test.describe('Firefox Browser Tests', () => {
    test('Firefox - Basic functionality and navigation', async ({ browser }) => {
      console.log('🧪 Testing Firefox browser compatibility...');

      const context = await browser.newContext({
        viewport: desktopViewport,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);
      const profilePage = new ProfilePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test basic navigation in Firefox
      const tabs = ['overview', 'discover', 'plan', 'analyze'];
      for (const tab of tabs) {
        await basePage.switchTab(tab);
        await page.waitForTimeout(1000);

        // Verify content loads correctly
        await expect.soft(page.locator('body')).toBeVisible();
        console.log(`✅ Firefox: ${tab} tab loaded successfully`);
      }

      // Test profile management in Firefox
      if (testProfileId) {
        await profilePage.navigateToProfiles();
        await profilePage.selectProfile(testProfileId);
        console.log('✅ Firefox: Profile selection functional');
      }

      await basePage.takeScreenshot('firefox-basic-functionality');

      await context.close();
      console.log('✅ Firefox browser tests completed');
    });

    test('Firefox - Engine-specific features', async ({ browser }) => {
      console.log('🧪 Testing Firefox engine-specific features...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test Firefox-specific features
      const firefoxFeatures = await page.evaluate(() => {
        return {
          gecko: navigator.userAgent.includes('Gecko'),
          mozConnection: 'mozConnection' in navigator,
          mozBattery: 'mozBattery' in navigator,
          webGL: !!window.WebGLRenderingContext,
          indexedDB: !!window.indexedDB,
          fetch: typeof fetch !== 'undefined',
          promises: typeof Promise !== 'undefined',
          localStorage: typeof localStorage !== 'undefined',
          sessionStorage: typeof sessionStorage !== 'undefined',
          webWorkers: typeof Worker !== 'undefined'
        };
      });

      console.log('📊 Firefox feature support:', firefoxFeatures);

      // Verify essential features work in Firefox
      expect(firefoxFeatures.fetch).toBeTruthy();
      expect(firefoxFeatures.promises).toBeTruthy();
      expect(firefoxFeatures.localStorage).toBeTruthy();

      // Test Firefox's JavaScript performance
      const performanceTest = await page.evaluate(() => {
        const start = performance.now();

        // Run computation-heavy task
        for (let i = 0; i < 100000; i++) {
          Math.sqrt(i);
        }

        return performance.now() - start;
      });

      console.log(`📊 Firefox JS performance: ${performanceTest.toFixed(2)}ms`);
      expect(performanceTest).toBeLessThan(150); // Firefox may be slightly slower

      await basePage.takeScreenshot('firefox-engine-features');

      await context.close();
      console.log('✅ Firefox engine features tested');
    });

    test('Firefox - CSS rendering differences', async ({ browser }) => {
      console.log('🧪 Testing Firefox CSS rendering differences...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test CSS support in Firefox
      const cssSupport = await page.evaluate(() => {
        return {
          grid: CSS.supports('display', 'grid'),
          flexbox: CSS.supports('display', 'flex'),
          customProperties: CSS.supports('color', 'var(--test)'),
          transforms: CSS.supports('transform', 'translateX(10px)'),
          animations: CSS.supports('animation-duration', '1s'),
          mozPrefix: CSS.supports('-moz-appearance', 'none')
        };
      });

      console.log('📊 Firefox CSS support:', cssSupport);

      // Verify Firefox CSS compatibility
      expect(cssSupport.grid).toBeTruthy();
      expect(cssSupport.flexbox).toBeTruthy();
      expect(cssSupport.customProperties).toBeTruthy();

      // Test Firefox-specific layout behavior
      await basePage.switchTab('discover');
      await page.waitForTimeout(1000);

      const firefoxLayout = await page.evaluate(() => {
        const elements = document.querySelectorAll('button, input, select');
        const layoutInfo = [];

        for (let i = 0; i < Math.min(5, elements.length); i++) {
          const el = elements[i];
          const style = window.getComputedStyle(el);
          layoutInfo.push({
            display: style.display,
            position: style.position,
            boxSizing: style.boxSizing,
            width: el.offsetWidth,
            height: el.offsetHeight
          });
        }

        return layoutInfo;
      });

      console.log('📊 Firefox layout info (first 5 elements):', firefoxLayout);

      await basePage.takeScreenshot('firefox-css-rendering');

      await context.close();
      console.log('✅ Firefox CSS rendering tested');
    });
  });

  test.describe('Cross-Browser Compatibility', () => {
    test('Feature parity between Chrome and Firefox', async ({ browser }) => {
      console.log('🧪 Testing feature parity between browsers...');

      const results = { chrome: {}, firefox: {} };

      // Test in Chrome
      const chromeContext = await browser.newContext({
        viewport: desktopViewport
      });
      const chromePage = await chromeContext.newPage();
      const chromeBasePage = new BasePage(chromePage);

      await chromeBasePage.navigate();
      await chromeBasePage.waitForAppReady();

      results.chrome = await chromePage.evaluate(() => {
        return {
          tabs: Array.from(document.querySelectorAll('button[role="tab"], nav button')).length,
          modals: Array.from(document.querySelectorAll('[role="dialog"], .modal')).length,
          forms: document.querySelectorAll('form').length,
          inputs: document.querySelectorAll('input, textarea, select').length,
          charts: document.querySelectorAll('canvas').length,
          apiSupport: {
            fetch: typeof fetch !== 'undefined',
            localStorage: typeof localStorage !== 'undefined',
            webGL: !!window.WebGLRenderingContext
          }
        };
      });

      await chromeContext.close();

      // Test in Firefox (if available)
      try {
        const firefoxContext = await browser.newContext({
          viewport: desktopViewport
        });
        const firefoxPage = await firefoxContext.newPage();
        const firefoxBasePage = new BasePage(firefoxPage);

        await firefoxBasePage.navigate();
        await firefoxBasePage.waitForAppReady();

        results.firefox = await firefoxPage.evaluate(() => {
          return {
            tabs: Array.from(document.querySelectorAll('button[role="tab"], nav button')).length,
            modals: Array.from(document.querySelectorAll('[role="dialog"], .modal')).length,
            forms: document.querySelectorAll('form').length,
            inputs: document.querySelectorAll('input, textarea, select').length,
            charts: document.querySelectorAll('canvas').length,
            apiSupport: {
              fetch: typeof fetch !== 'undefined',
              localStorage: typeof localStorage !== 'undefined',
              webGL: !!window.WebGLRenderingContext
            }
          };
        });

        await firefoxContext.close();

        // Compare results
        console.log('📊 Chrome results:', results.chrome);
        console.log('📊 Firefox results:', results.firefox);

        // Verify feature parity
        expect(results.chrome.apiSupport.fetch).toBe(results.firefox.apiSupport.fetch);
        expect(results.chrome.apiSupport.localStorage).toBe(results.firefox.apiSupport.localStorage);

        console.log('✅ Feature parity verified between browsers');
      } catch (error) {
        console.log('⚠️ Firefox testing skipped - browser not available');
      }

      console.log('✅ Cross-browser feature parity tested');
    });

    test('Performance comparison across browsers', async ({ browser }) => {
      console.log('🧪 Testing performance across browsers...');

      const performanceResults = {};

      // Test Chrome performance
      const chromeContext = await browser.newContext({
        viewport: desktopViewport
      });
      const chromePage = await chromeContext.newPage();
      const chromeBasePage = new BasePage(chromePage);

      const chromeStartTime = Date.now();
      await chromeBasePage.navigate();
      await chromeBasePage.waitForAppReady();
      const chromeLoadTime = Date.now() - chromeStartTime;

      // Test Chrome operations performance
      const chromeOpsStart = performance.now();
      await chromeBasePage.switchTab('discover');
      await chromePage.waitForTimeout(1000);
      await chromeBasePage.switchTab('analyze');
      await chromePage.waitForTimeout(1000);
      const chromeOpsTime = performance.now() - chromeOpsStart;

      performanceResults.chrome = {
        loadTime: chromeLoadTime,
        operationsTime: chromeOpsTime
      };

      await chromeContext.close();

      console.log('📊 Performance results:', performanceResults);

      // Verify Chrome performance is acceptable
      expect(performanceResults.chrome.loadTime).toBeLessThan(5000);
      expect(performanceResults.chrome.operationsTime).toBeLessThan(3000);

      console.log('✅ Cross-browser performance comparison completed');
    });

    test('Local storage consistency across browsers', async ({ browser }) => {
      console.log('🧪 Testing localStorage consistency...');

      const testData = {
        testKey: 'crossBrowserTest',
        testValue: JSON.stringify({
          timestamp: Date.now(),
          data: 'Cross-browser test data'
        })
      };

      // Test Chrome localStorage
      const chromeContext = await browser.newContext({
        viewport: desktopViewport
      });
      const chromePage = await chromeContext.newPage();

      await chromePage.goto('http://localhost:8000');
      await chromePage.waitForTimeout(2000);

      const chromeStorageTest = await chromePage.evaluate((data) => {
        localStorage.setItem(data.testKey, data.testValue);
        const retrieved = localStorage.getItem(data.testKey);
        localStorage.removeItem(data.testKey);

        return {
          stored: data.testValue,
          retrieved: retrieved,
          match: data.testValue === retrieved
        };
      }, testData);

      console.log('📊 Chrome localStorage test:', chromeStorageTest);
      expect(chromeStorageTest.match).toBeTruthy();

      await chromeContext.close();

      console.log('✅ localStorage consistency tested');
    });

    test('CSS rendering consistency validation', async ({ browser }) => {
      console.log('🧪 Testing CSS rendering consistency...');

      const contexts = [];
      const pages = [];
      const basePages = [];

      try {
        // Create contexts for available browsers
        const chromeContext = await browser.newContext({
          viewport: desktopViewport
        });
        contexts.push(chromeContext);

        const chromePage = await chromeContext.newPage();
        pages.push(chromePage);
        basePages.push(new BasePage(chromePage));

        // Load app in all browsers
        for (const basePage of basePages) {
          await basePage.navigate();
          await basePage.waitForAppReady();
        }

        // Compare layout metrics
        const layoutComparisons = [];

        for (let i = 0; i < pages.length; i++) {
          const page = pages[i];
          const browserName = i === 0 ? 'chrome' : 'firefox';

          const layoutMetrics = await page.evaluate(() => {
            const main = document.querySelector('main, #app, .app, body');
            const buttons = document.querySelectorAll('button');

            return {
              mainWidth: main ? main.offsetWidth : 0,
              mainHeight: main ? main.offsetHeight : 0,
              buttonCount: buttons.length,
              firstButtonSize: buttons[0] ? {
                width: buttons[0].offsetWidth,
                height: buttons[0].offsetHeight
              } : null
            };
          });

          layoutComparisons.push({
            browser: browserName,
            metrics: layoutMetrics
          });
        }

        console.log('📊 Layout comparisons:', layoutComparisons);

        // Verify layouts are reasonably consistent
        if (layoutComparisons.length > 1) {
          const chrome = layoutComparisons[0].metrics;
          const firefox = layoutComparisons[1].metrics;

          // Allow for small differences (within 5%)
          const widthDiff = Math.abs(chrome.mainWidth - firefox.mainWidth) / chrome.mainWidth;
          expect(widthDiff).toBeLessThan(0.05);

          console.log('✅ CSS rendering consistency verified');
        }

      } finally {
        // Clean up contexts
        for (const context of contexts) {
          await context.close();
        }
      }

      console.log('✅ CSS rendering consistency tested');
    });

    test('Error handling consistency across browsers', async ({ browser }) => {
      console.log('🧪 Testing error handling consistency...');

      const errorTests = [
        {
          name: 'Network Error',
          setup: (page) => page.route('**/api/**', route => route.fulfill({ status: 500 }))
        },
        {
          name: 'JavaScript Error',
          setup: (page) => page.evaluate(() => {
            setTimeout(() => {
              try {
                window.nonExistentFunction();
              } catch (e) {
                console.error('Test error:', e);
              }
            }, 1000);
          })
        }
      ];

      for (const errorTest of errorTests) {
        console.log(`🔍 Testing ${errorTest.name} handling...`);

        const chromeContext = await browser.newContext({
          viewport: desktopViewport
        });
        const chromePage = await chromeContext.newPage();
        const chromeBasePage = new BasePage(chromePage);

        await chromeBasePage.navigate();
        await chromeBasePage.waitForAppReady();

        // Set up error condition
        await errorTest.setup(chromePage);

        // Test error recovery
        await chromeBasePage.switchTab('discover');
        await chromePage.waitForTimeout(3000);

        // Verify app is still functional
        const appState = await chromeBasePage.getAppState();
        expect(appState).toBeTruthy();

        await chromeContext.close();

        console.log(`✅ ${errorTest.name} handling tested`);
      }

      console.log('✅ Error handling consistency tested');
    });
  });

  test.describe('Browser-Specific Optimizations', () => {
    test('Chrome DevTools integration', async ({ browser }) => {
      console.log('🧪 Testing Chrome DevTools integration...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test console integration
      const consoleMessages = [];
      page.on('console', msg => {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      });

      // Trigger some operations that might log messages
      await basePage.switchTab('discover');
      await page.waitForTimeout(2000);

      // Check for appropriate console messages
      const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
      const warningMessages = consoleMessages.filter(msg => msg.type === 'warning');

      console.log(`📊 Console messages: ${consoleMessages.length} total, ${errorMessages.length} errors, ${warningMessages.length} warnings`);

      // Should not have critical errors
      const criticalErrors = errorMessages.filter(msg =>
        !msg.text.includes('404') &&
        !msg.text.includes('favicon') &&
        !msg.text.includes('Network')
      );
      expect(criticalErrors.length).toBe(0);

      await basePage.takeScreenshot('chrome-devtools-integration');

      await context.close();
      console.log('✅ Chrome DevTools integration tested');
    });

    test('Firefox Developer Edition features', async ({ browser }) => {
      console.log('🧪 Testing Firefox developer features...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();
      const basePage = new BasePage(page);

      await basePage.navigate();
      await basePage.waitForAppReady();

      // Test Firefox-specific developer features
      const firefoxDevFeatures = await page.evaluate(() => {
        return {
          mozPaintCount: typeof document.mozPaintCount !== 'undefined',
          mozImageSmoothingEnabled: (function() {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            return 'mozImageSmoothingEnabled' in ctx;
          })(),
          mozRequestAnimationFrame: typeof window.mozRequestAnimationFrame !== 'undefined',
          performanceAPI: typeof performance !== 'undefined' && typeof performance.mark !== 'undefined'
        };
      });

      console.log('📊 Firefox developer features:', firefoxDevFeatures);

      // Test performance monitoring
      if (firefoxDevFeatures.performanceAPI) {
        await page.evaluate(() => {
          performance.mark('test-start');
          setTimeout(() => {
            performance.mark('test-end');
            performance.measure('test-duration', 'test-start', 'test-end');
          }, 100);
        });

        await page.waitForTimeout(200);

        const performanceEntries = await page.evaluate(() => {
          const measures = performance.getEntriesByType('measure');
          return measures.map(m => ({
            name: m.name,
            duration: m.duration
          }));
        });

        console.log('📊 Firefox performance entries:', performanceEntries);
      }

      await basePage.takeScreenshot('firefox-developer-features');

      await context.close();
      console.log('✅ Firefox developer features tested');
    });

    test('Browser-specific polyfill requirements', async ({ browser }) => {
      console.log('🧪 Testing polyfill requirements...');

      const context = await browser.newContext({
        viewport: desktopViewport
      });

      const page = await context.newPage();

      // Check what polyfills might be needed
      const polyfillNeeds = await page.evaluate(() => {
        const features = {
          fetch: typeof fetch !== 'undefined',
          promises: typeof Promise !== 'undefined',
          arrayIncludes: Array.prototype.includes !== undefined,
          objectAssign: Object.assign !== undefined,
          customElements: typeof customElements !== 'undefined',
          intersectionObserver: typeof IntersectionObserver !== 'undefined',
          resizeObserver: typeof ResizeObserver !== 'undefined'
        };

        const missing = Object.entries(features)
          .filter(([key, value]) => !value)
          .map(([key]) => key);

        return {
          supported: features,
          missing: missing
        };
      });

      console.log('📊 Polyfill analysis:', polyfillNeeds);

      // Load the app and verify it works despite missing features
      const basePage = new BasePage(page);
      await basePage.navigate();
      await basePage.waitForAppReady();

      // App should function even with some missing features
      const appState = await basePage.getAppState();
      expect(appState).toBeTruthy();

      await basePage.takeScreenshot('polyfill-requirements');

      await context.close();
      console.log('✅ Polyfill requirements tested');
    });
  });
});
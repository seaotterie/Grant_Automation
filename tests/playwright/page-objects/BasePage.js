/**
 * Base Page Object Model for Catalynx Application
 * 
 * This class provides common functionality for all page objects:
 * - Navigation methods
 * - Common UI interactions
 * - Utility methods
 * - Error handling
 */

const { expect } = require('@playwright/test');
const { selectors, timeouts, urls } = require('../fixtures/test-configurations');

class BasePage {
  constructor(page) {
    this.page = page;
    this.baseURL = urls.base;
    this.selectors = selectors;
    this.timeouts = timeouts;
  }

  /**
   * Navigate to the application base URL
   */
  async navigate() {
    await this.page.goto(this.baseURL, { 
      waitUntil: 'domcontentloaded',
      timeout: this.timeouts.navigation 
    });
    
    // Wait for Alpine.js to initialize
    await this.waitForAlpineJS();
  }

  /**
   * Wait for Alpine.js framework to initialize
   */
  async waitForAlpineJS() {
    await this.page.waitForFunction(
      () => window.Alpine && window.catalynxApp,
      { timeout: this.timeouts.navigation }
    );
  }

  /**
   * Wait for the application to be fully loaded
   */
  async waitForAppReady() {
    // Wait for Alpine.js to be ready
    await this.waitForAlpineJS();
    
    // Wait a moment for initial API calls to complete
    await this.page.waitForTimeout(2000);
    
    // Try to wait for key API responses, but don't fail if they don't come
    try {
      await this.page.waitForResponse(
        response => response.url().includes('/api/system/status') && response.ok(),
        { timeout: 5000 }
      );
    } catch (error) {
      console.log('Note: System status API response not captured, continuing...');
    }
    
    try {
      await this.page.waitForResponse(
        response => response.url().includes('/api/dashboard/overview') && response.ok(),
        { timeout: 5000 }
      );
    } catch (error) {
      console.log('Note: Dashboard API response not captured, continuing...');
    }
    
    // Wait for any loading to complete
    await this.waitForLoadingComplete();
  }

  /**
   * Switch to a specific tab in the application
   * @param {string} tabName - Name of the tab to switch to
   */
  async switchTab(tabName) {
    // Map common tab names to actual selectors
    const tabMapping = {
      'dashboard': this.selectors.navigation.overview_tab,
      'overview': this.selectors.navigation.overview_tab,
      'profiles': 'button:has-text("Create Profile")', // Profile management area
      'discovery': this.selectors.navigation.discover_tab,
      'discover': this.selectors.navigation.discover_tab,
      'plan': this.selectors.navigation.plan_tab,
      'analyze': this.selectors.navigation.analyze_tab,
      'examine': this.selectors.navigation.examine_tab,
      'approach': this.selectors.navigation.approach_tab
    };
    
    const tabSelector = tabMapping[tabName] || this.selectors.navigation[`${tabName}_tab`];
    if (!tabSelector) {
      console.warn(`Tab selector not found for: ${tabName}, trying generic approach`);
      // Try to find button with the tab name
      const genericSelector = `button:has-text("${tabName}")`;
      if (await this.isElementVisible(genericSelector)) {
        await this.clickElement(genericSelector);
        return;
      } else {
        throw new Error(`Tab not found: ${tabName}`);
      }
    }
    
    await this.clickElement(tabSelector);
    
    // Wait for tab content to load
    await this.page.waitForTimeout(1000);
  }

  /**
   * Wait for a loading state to complete
   */
  async waitForLoadingComplete() {
    // Wait for any loading spinners to disappear
    const loadingSelectors = [
      '.loading',
      '.spinner',
      '[data-loading="true"]',
      '.opacity-50' // Common loading state class in Tailwind
    ];
    
    for (const selector of loadingSelectors) {
      try {
        await this.page.waitForSelector(selector, { 
          state: 'detached', 
          timeout: 5000 
        });
      } catch (error) {
        // Loading element might not exist, which is fine
      }
    }
  }

  /**
   * Take a screenshot with a descriptive name
   * @param {string} name - Name for the screenshot
   */
  async takeScreenshot(name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}_${timestamp}.png`;
    
    await this.page.screenshot({
      path: `tests/playwright/screenshots/${filename}`,
      fullPage: true
    });
    
    return filename;
  }

  /**
   * Check if an element is visible on the page
   * @param {string} selector - CSS selector
   * @returns {boolean}
   */
  async isElementVisible(selector) {
    try {
      await this.page.waitForSelector(selector, { 
        state: 'visible', 
        timeout: 3000 
      });
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get text content from an element
   * @param {string} selector - CSS selector
   * @returns {string}
   */
  async getElementText(selector) {
    await this.page.waitForSelector(selector, { timeout: 5000 });
    return await this.page.textContent(selector);
  }

  /**
   * Fill an input field with error handling
   * @param {string} selector - CSS selector for the input
   * @param {string} value - Value to fill
   */
  async fillInput(selector, value) {
    await this.page.waitForSelector(selector, { timeout: 5000 });
    await this.page.fill(selector, value);
    
    // Verify the value was set
    const actualValue = await this.page.inputValue(selector);
    if (actualValue !== value) {
      throw new Error(`Failed to fill input ${selector}. Expected: ${value}, Actual: ${actualValue}`);
    }
  }

  /**
   * Click an element with retry logic
   * @param {string} selector - CSS selector
   * @param {Object} options - Click options
   */
  async clickElement(selector, options = {}) {
    await this.page.waitForSelector(selector, { 
      state: 'visible', 
      timeout: 5000 
    });
    
    // Ensure element is clickable
    await this.page.hover(selector);
    await this.page.click(selector, options);
  }

  /**
   * Wait for an API response matching a pattern
   * @param {string} urlPattern - URL pattern to match
   * @param {number} timeout - Timeout in milliseconds
   */
  async waitForAPIResponse(urlPattern, timeout = this.timeouts.api_response) {
    return await this.page.waitForResponse(
      response => response.url().includes(urlPattern) && response.ok(),
      { timeout }
    );
  }

  /**
   * Get current application state from Alpine.js
   */
  async getAppState() {
    return await this.page.evaluate(() => {
      if (window.catalynxApp) {
        return {
          currentTab: window.catalynxApp.currentTab,
          isLoading: window.catalynxApp.isLoading,
          selectedProfile: window.catalynxApp.selectedProfile,
          profilesCount: window.catalynxApp.profiles?.length || 0,
          wsConnectionStatus: window.catalynxApp.wsConnectionStatus
        };
      }
      return null;
    });
  }

  /**
   * Verify system is in a healthy state
   */
  async verifySystemHealth() {
    const response = await this.page.request.get(`${this.baseURL}/api/system/health`);
    expect(response.ok()).toBeTruthy();
    
    const healthData = await response.json();
    expect(healthData.status).toBe('healthy');
  }

  /**
   * Wait for charts to render
   */
  async waitForChartsToRender() {
    // Wait for Chart.js to be available
    await this.page.waitForFunction(
      () => window.Chart,
      { timeout: this.timeouts.chart_render }
    );
    
    // Wait for chart canvases to be visible
    const chartSelectors = Object.values(this.selectors.charts);
    for (const selector of chartSelectors) {
      try {
        await this.page.waitForSelector(selector, { 
          state: 'visible', 
          timeout: 3000 
        });
      } catch (error) {
        // Chart might not be present on this page
      }
    }
    
    // Give charts time to render
    await this.page.waitForTimeout(1000);
  }

  /**
   * Handle modal dialogs
   * @param {string} modalSelector - Selector for the modal
   * @param {boolean} expectVisible - Whether modal should be visible
   */
  async handleModal(modalSelector, expectVisible = true) {
    if (expectVisible) {
      await this.page.waitForSelector(modalSelector, { 
        state: 'visible',
        timeout: this.timeouts.modal_animation 
      });
    } else {
      await this.page.waitForSelector(modalSelector, { 
        state: 'hidden',
        timeout: this.timeouts.modal_animation 
      });
    }
  }

  /**
   * Scroll element into view
   * @param {string} selector - CSS selector
   */
  async scrollIntoView(selector) {
    await this.page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * Get performance metrics from the browser
   */
  async getPerformanceMetrics() {
    return await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        pageLoadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        timeToFirstByte: navigation.responseStart - navigation.requestStart,
        resourceLoadTime: navigation.loadEventEnd - navigation.fetchStart
      };
    });
  }
}

module.exports = BasePage;
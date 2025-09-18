/**
 * Visual Regression Test: UI Consistency
 * 
 * This test captures and compares screenshots to ensure UI consistency
 * across updates and different browsers.
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');

test.describe('Visual Regression Tests', () => {
  let basePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    await basePage.navigate();
    await basePage.waitForAppReady();
  });

  test('Homepage layout is consistent', async ({ page }) => {
    // Wait for page to fully render
    await page.waitForTimeout(2000);
    
    // Hide dynamic elements that might cause false positives
    await page.evaluate(() => {
      // Hide timestamps, counters, or other dynamic content
      const dynamicElements = document.querySelectorAll(
        '[data-timestamp], .timestamp, .counter, .live-update'
      );
      dynamicElements.forEach(el => el.style.visibility = 'hidden');
    });
    
    // Take full page screenshot
    await expect(page).toHaveScreenshot('homepage-layout.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Main navigation is visually consistent', async ({ page }) => {
    // Focus on navigation area
    const navArea = page.locator('nav, .navigation, .nav').first();
    
    if (await navArea.isVisible()) {
      await expect(navArea).toHaveScreenshot('navigation-area.png', {
        animations: 'disabled'
      });
    } else {
      // Fallback to top portion of page
      await expect(page.locator('body')).toHaveScreenshot('top-navigation.png', {
        clip: { x: 0, y: 0, width: 1280, height: 200 },
        animations: 'disabled'
      });
    }
  });

  test('Profile management interface is consistent', async ({ page }) => {
    // Look for profile-related content
    const createProfileBtn = page.locator('button:has-text("Create Profile")');
    
    if (await createProfileBtn.isVisible()) {
      await createProfileBtn.click();
      await page.waitForTimeout(1000);
      
      // Capture profile creation modal/form
      const modal = page.locator('.fixed.inset-0, .modal, .dialog').first();
      if (await modal.isVisible()) {
        await expect(modal).toHaveScreenshot('profile-creation-modal.png', {
          animations: 'disabled'
        });
        
        // Close modal
        const closeBtn = page.locator('button:has-text("×"), button:has-text("Close"), button:has-text("Cancel")');
        if (await closeBtn.first().isVisible()) {
          await closeBtn.first().click();
        }
      }
    }
  });

  test('Data display components are consistent', async ({ page }) => {
    // Look for data tables or cards
    const dataComponents = [
      'table',
      '.grid',
      '.card',
      '.data-display',
      '.results'
    ];
    
    for (const selector of dataComponents) {
      const element = page.locator(selector).first();
      if (await element.isVisible()) {
        await expect(element).toHaveScreenshot(`data-component-${selector.replace(/[^a-z0-9]/gi, '')}.png`, {
          animations: 'disabled'
        });
        break; // Only capture the first visible data component
      }
    }
  });

  test('Button and control styling is consistent', async ({ page }) => {
    // Capture a section with various buttons
    const buttonContainer = page.locator('div:has(button)').first();
    
    if (await buttonContainer.isVisible()) {
      await expect(buttonContainer).toHaveScreenshot('button-styles.png', {
        animations: 'disabled'
      });
    }
  });

  test('Color theme and typography are consistent', async ({ page }) => {
    // Test light theme
    await expect(page.locator('body')).toHaveScreenshot('light-theme-sample.png', {
      clip: { x: 0, y: 0, width: 800, height: 600 },
      animations: 'disabled'
    });
    
    // Try to switch to dark theme if toggle exists
    const darkModeToggle = page.locator('button:has-text("🌙"), button:has-text("☀️"), [data-theme-toggle]');
    
    if (await darkModeToggle.first().isVisible()) {
      await darkModeToggle.first().click();
      await page.waitForTimeout(1000);
      
      await expect(page.locator('body')).toHaveScreenshot('dark-theme-sample.png', {
        clip: { x: 0, y: 0, width: 800, height: 600 },
        animations: 'disabled'
      });
    }
  });

  test('Mobile responsive layout is consistent', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('mobile-layout.png', {
      fullPage: true,
      animations: 'disabled'
    });
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('tablet-layout.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Chart and visualization components are consistent', async ({ page }) => {
    // Look for chart canvases
    const charts = page.locator('canvas');
    const chartCount = await charts.count();
    
    if (chartCount > 0) {
      // Wait for charts to render
      await page.waitForTimeout(3000);
      
      for (let i = 0; i < Math.min(chartCount, 3); i++) {
        const chart = charts.nth(i);
        if (await chart.isVisible()) {
          await expect(chart).toHaveScreenshot(`chart-${i}.png`, {
            animations: 'disabled'
          });
        }
      }
    }
  });

  test('Loading states are visually consistent', async ({ page }) => {
    // Try to trigger a loading state
    const runButtons = page.locator('button:has-text("Run"), button:has-text("Execute"), button:has-text("Start")');
    
    if (await runButtons.first().isVisible()) {
      // Click to potentially trigger loading
      await runButtons.first().click();
      await page.waitForTimeout(500);
      
      // Look for loading indicators
      const loadingElements = page.locator('.loading, .spinner, .opacity-50, text="Loading"');
      
      if (await loadingElements.first().isVisible()) {
        await expect(page.locator('body')).toHaveScreenshot('loading-state.png', {
          clip: { x: 0, y: 0, width: 1280, height: 400 },
          animations: 'disabled'
        });
      }
    }
  });
});
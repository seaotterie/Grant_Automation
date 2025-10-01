/**
 * Profile Modal Button Visibility Test
 *
 * This test specifically validates the profile modal button visibility and layout issues
 * reported by the user:
 * 1. Cancel and Update Profile buttons should be visible at modal bottom
 * 2. Tax Filing tab should have purple highlight like other tabs
 * 3. All tabs should have consistent height and scrolling
 * 4. Basic Information tab should display correctly after HTML structure fix
 */

const { test, expect } = require('@playwright/test');

test.describe('Profile Modal Button Visibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8000');

    // Wait for the application to load
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('body', { timeout: 10000 });
  });

  test('Profile modal opens and buttons are visible', async ({ page }) => {
    console.log('🧪 Testing profile modal button visibility...');

    // Try to find and click the Create Profile button
    // Check multiple possible selectors
    const createButtons = [
      'button:has-text("Create Profile")',
      'button:has-text("Create Organization Profile")',
      'button:has-text("Add Profile")',
      '[data-testid="create-profile"]',
      '.create-profile-btn'
    ];

    let createButton = null;
    for (const selector of createButtons) {
      const button = page.locator(selector).first();
      if (await button.isVisible().catch(() => false)) {
        createButton = button;
        console.log(`✅ Found create button with selector: ${selector}`);
        break;
      }
    }

    if (!createButton) {
      // Try to take a screenshot to see what's on the page
      await page.screenshot({ path: 'test-results/page-state.png', fullPage: true });
      console.log('📸 Page screenshot saved to test-results/page-state.png');

      // Look for any button that might open the modal
      const allButtons = await page.locator('button').all();
      console.log(`Found ${allButtons.length} buttons on page`);

      for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
        const buttonText = await allButtons[i].textContent().catch(() => '');
        console.log(`Button ${i}: "${buttonText}"`);
      }

      throw new Error('Could not find Create Profile button');
    }

    // Click to open the modal
    await createButton.click();

    // Wait for modal to appear
    const modal = page.locator('.fixed.inset-0').first();
    await expect(modal).toBeVisible({ timeout: 5000 });

    console.log('✅ Modal opened successfully');

    // Take screenshot of the opened modal
    await page.screenshot({ path: 'test-results/modal-opened.png', fullPage: true });

    // Test 1: Check that Cancel and Update Profile buttons are visible
    const cancelButton = page.locator('button:has-text("Cancel")');
    const updateButton = page.locator('button:has-text("Update Profile"), button:has-text("Create Profile")');

    await expect(cancelButton).toBeVisible({ timeout: 3000 });
    await expect(updateButton).toBeVisible({ timeout: 3000 });

    console.log('✅ Cancel and Update buttons are visible');

    // Test 2: Check that buttons are at the bottom of the modal (not scrolled away)
    const cancelBox = await cancelButton.boundingBox();
    const updateBox = await updateButton.boundingBox();
    const modalBox = await modal.boundingBox();

    if (cancelBox && updateBox && modalBox) {
      // Buttons should be near the bottom of the modal
      const buttonDistanceFromBottom = modalBox.y + modalBox.height - cancelBox.y;
      expect(buttonDistanceFromBottom).toBeLessThan(100); // Within 100px of bottom
      console.log(`✅ Buttons positioned correctly: ${buttonDistanceFromBottom}px from modal bottom`);
    }

    // Test 3: Check all tabs are present and clickable
    const expectedTabs = [
      'Basic Information',
      'NTEE Codes',
      'Government Criteria',
      'Tax Filing Data',
      'Web Search Data'
    ];

    for (const tabName of expectedTabs) {
      const tab = page.locator(`button:has-text("${tabName}")`);
      await expect(tab).toBeVisible({ timeout: 2000 });
      console.log(`✅ Tab found: ${tabName}`);
    }

    // Test 4: Check Tax Filing tab color consistency
    const taxFilingTab = page.locator('button:has-text("Tax Filing Data")');
    await taxFilingTab.click();

    // Wait for tab to become active
    await page.waitForTimeout(500);

    // Check if the tab has purple highlight (same as other tabs)
    const taxFilingClass = await taxFilingTab.getAttribute('class');
    expect(taxFilingClass).toContain('purple'); // Should contain purple color classes
    console.log('✅ Tax Filing tab has correct purple styling');

    // Test 5: Check Basic Information tab structure
    const basicInfoTab = page.locator('button:has-text("Basic Information")');
    await basicInfoTab.click();
    await page.waitForTimeout(500);

    // Check that the content is properly displayed
    const organizationNameField = page.locator('input[placeholder*="organization name"], input[placeholder*="Organization name"]');
    await expect(organizationNameField).toBeVisible({ timeout: 3000 });
    console.log('✅ Basic Information tab displays correctly');

    // Test 6: Check scrolling works on all tabs
    for (const tabName of expectedTabs) {
      const tab = page.locator(`button:has-text("${tabName}")`);
      await tab.click();
      await page.waitForTimeout(300);

      // Check that the tab content area has overflow scrolling
      const tabContent = page.locator(`[x-show="profileModalActiveTab === '${tabName.toLowerCase().replace(/ /g, '-')}'"]:visible`);
      if (await tabContent.isVisible().catch(() => false)) {
        const hasOverflow = await tabContent.evaluate(el => {
          const style = window.getComputedStyle(el);
          return style.overflowY === 'auto' || style.overflowY === 'scroll';
        });
        expect(hasOverflow).toBe(true);
        console.log(`✅ Tab "${tabName}" has proper scrolling enabled`);
      }
    }

    // Test 7: Verify modal maintains consistent height across tabs
    const heights = [];
    for (const tabName of expectedTabs) {
      const tab = page.locator(`button:has-text("${tabName}")`);
      await tab.click();
      await page.waitForTimeout(300);

      const modalHeight = await modal.evaluate(el => el.offsetHeight);
      heights.push(modalHeight);
    }

    // All heights should be the same (or very close)
    const minHeight = Math.min(...heights);
    const maxHeight = Math.max(...heights);
    expect(maxHeight - minHeight).toBeLessThan(50); // Allow 50px variance
    console.log(`✅ Modal height consistency: ${minHeight}px - ${maxHeight}px`);

    // Final screenshot
    await page.screenshot({ path: 'test-results/modal-final-state.png', fullPage: true });
    console.log('📸 Final test screenshot saved');
  });

  test('Modal responsive behavior', async ({ page }) => {
    console.log('🧪 Testing modal responsive behavior...');

    // Test at different viewport sizes
    const viewports = [
      { width: 1280, height: 720 },   // Desktop
      { width: 768, height: 1024 },   // Tablet
      { width: 375, height: 667 }     // Mobile
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      console.log(`Testing at ${viewport.width}x${viewport.height}`);

      // Try to open modal (implementation varies by viewport)
      const createButton = page.locator('button:has-text("Create Profile"), button:has-text("Create Organization Profile")').first();
      if (await createButton.isVisible().catch(() => false)) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0').first();
        await expect(modal).toBeVisible({ timeout: 3000 });

        // Check buttons are still visible and accessible
        const cancelButton = page.locator('button:has-text("Cancel")');
        const updateButton = page.locator('button:has-text("Update Profile"), button:has-text("Create Profile")');

        await expect(cancelButton).toBeVisible({ timeout: 2000 });
        await expect(updateButton).toBeVisible({ timeout: 2000 });

        console.log(`✅ Buttons visible at ${viewport.width}x${viewport.height}`);

        // Close modal
        await cancelButton.click();
        await page.waitForTimeout(500);
      }
    }
  });
});
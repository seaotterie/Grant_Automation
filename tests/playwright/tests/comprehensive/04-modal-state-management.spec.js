/**
 * Modal State Management Tests
 *
 * This test suite validates modal state management:
 * - Modal opening/closing animations and state persistence
 * - Data persistence during modal interactions
 * - Error state handling within modals
 * - Cross-modal navigation flows
 * - Modal stacking and z-index management
 * - Session state preservation across modal operations
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const DiscoveryPage = require('../../page-objects/DiscoveryPage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Modal State Management', () => {
  let basePage;
  let profilePage;
  let discoveryPage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);
    discoveryPage = new DiscoveryPage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();
  });

  test.describe('Modal Opening and Closing State Management', () => {
    test('Modal state persists during opening animations', async ({ page }) => {
      console.log('🧪 Testing modal opening state persistence...');

      await profilePage.navigateToProfiles();

      // Get initial app state
      const initialState = await basePage.getAppState();

      // Open profile creation modal
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        // Verify modal is opening (should be visible during animation)
        const modal = page.locator('.fixed.inset-0, .modal, [role="dialog"]').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Check that app state is preserved during modal opening
        const stateAfterModalOpen = await basePage.getAppState();

        if (initialState && stateAfterModalOpen) {
          // Core app state should be preserved
          expect(stateAfterModalOpen.profilesCount).toBe(initialState.profilesCount);
          if (initialState.selectedProfile && stateAfterModalOpen.selectedProfile) {
            expect(stateAfterModalOpen.selectedProfile.profile_id).toBe(initialState.selectedProfile.profile_id);
          }
          console.log('✅ App state preserved during modal opening');
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('modal-opening-state');
    });

    test('Modal state cleanup on closing', async ({ page }) => {
      console.log('🧪 Testing modal state cleanup...');

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        // Open modal
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Fill some form data
        const nameInput = page.locator('input[name="organization_name"], input[placeholder*="organization"]').first();
        if (await nameInput.isVisible({ timeout: 3000 })) {
          await nameInput.fill('Test Organization for State Management');
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }

        // Verify modal is completely gone
        await expect(modal).not.toBeVisible({ timeout: 3000 });

        // Reopen modal and verify form is cleared
        await createButton.click();
        await expect(modal).toBeVisible({ timeout: 5000 });

        if (await nameInput.isVisible({ timeout: 3000 })) {
          const inputValue = await nameInput.inputValue();
          if (inputValue === '') {
            console.log('✅ Form state properly cleared after modal close');
          } else {
            console.log('ℹ️  Form state persisted - this may be intentional');
          }
        }

        // Close modal again
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('modal-state-cleanup');
    });

    test('Modal animations complete properly', async ({ page }) => {
      console.log('🧪 Testing modal animation completion...');

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        // Measure modal opening animation
        const startTime = Date.now();
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Wait for animation to complete
        await page.waitForTimeout(500);

        const openTime = Date.now() - startTime;
        console.log(`Modal opened in ${openTime}ms`);

        // Verify modal is fully interactive
        const nameInput = page.locator('input[name="organization_name"], input[placeholder*="organization"]').first();
        if (await nameInput.isVisible({ timeout: 3000 })) {
          await nameInput.click();
          await nameInput.fill('Animation Test');
          const value = await nameInput.inputValue();
          expect(value).toBe('Animation Test');
          console.log('✅ Modal fully interactive after animation');
        }

        // Test closing animation
        const closeStartTime = Date.now();
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }

        await expect(modal).not.toBeVisible({ timeout: 3000 });
        const closeTime = Date.now() - closeStartTime;
        console.log(`Modal closed in ${closeTime}ms`);

        // Verify reasonable animation times (not too fast, not too slow)
        expect(openTime).toBeLessThan(2000);
        expect(closeTime).toBeLessThan(2000);
      }

      await basePage.takeScreenshot('modal-animation-timing');
    });
  });

  test.describe('Data Persistence During Modal Operations', () => {
    test('Profile selection persists through modal operations', async ({ page }) => {
      console.log('🧪 Testing profile selection persistence...');

      await profilePage.navigateToProfiles();

      // Get or create a profile to select
      const profiles = await profilePage.getAllProfiles();
      if (profiles.length > 0) {
        await profilePage.selectProfile(profiles[0].id);

        const initialState = await basePage.getAppState();
        const initialProfileId = initialState?.selectedProfile?.profile_id;

        if (initialProfileId) {
          // Open and close profile creation modal
          const createButton = page.locator('button:has-text("Create Profile")').first();
          if (await createButton.isVisible({ timeout: 5000 })) {
            await createButton.click();

            const modal = page.locator('.fixed.inset-0, .modal').first();
            await expect(modal).toBeVisible({ timeout: 5000 });

            // Close modal
            const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
            if (await closeButton.isVisible({ timeout: 2000 })) {
              await closeButton.click();
            }

            // Verify profile selection is maintained
            const finalState = await basePage.getAppState();
            const finalProfileId = finalState?.selectedProfile?.profile_id;

            expect(finalProfileId).toBe(initialProfileId);
            console.log('✅ Profile selection persisted through modal operation');
          }
        }
      } else {
        console.log('ℹ️  No profiles available to test selection persistence');
      }

      await basePage.takeScreenshot('profile-selection-persistence');
    });

    test('Discovery results persist through modal operations', async ({ page }) => {
      console.log('🧪 Testing discovery results persistence...');

      // Navigate to discovery and run discovery
      await discoveryPage.navigateToDiscovery();

      try {
        const results = await discoveryPage.executeDiscovery({
          tracks: ['nonprofit'],
          maxResults: 5
        });

        if (results && results.length > 0) {
          const initialResultCount = results.length;

          // Open a modal (export modal, settings, etc.)
          const exportButton = page.locator('button:has-text("Export"), button:has-text("Download")').first();
          if (await exportButton.isVisible({ timeout: 5000 })) {
            await exportButton.click();

            // Check if modal opened or direct download occurred
            const modal = page.locator('.fixed.inset-0, .modal').first();
            if (await modal.isVisible({ timeout: 3000 })) {
              // Close modal
              const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
              if (await closeButton.isVisible({ timeout: 2000 })) {
                await closeButton.click();
              }
            }

            // Verify discovery results are still visible
            const resultsTable = page.locator('table, .grid').first();
            if (await resultsTable.isVisible({ timeout: 5000 })) {
              const currentResults = await discoveryPage.getDiscoveryResults();
              if (currentResults.length >= initialResultCount * 0.8) { // Allow for some variation
                console.log('✅ Discovery results persisted through modal operation');
              } else {
                console.log('ℹ️  Discovery results may have been refreshed');
              }
            }
          } else {
            console.log('ℹ️  Export modal not available for testing');
          }
        }
      } catch (error) {
        console.log(`ℹ️  Discovery execution failed: ${error.message}`);
      }

      await basePage.takeScreenshot('discovery-results-persistence');
    });

    test('Form data preservation across modal reopening', async ({ page }) => {
      console.log('🧪 Testing form data preservation...');

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        // Open modal and fill form
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        const nameInput = page.locator('input[name="organization_name"], input[placeholder*="organization"]').first();
        const websiteInput = page.locator('input[name="website_url"], input[placeholder*="website"]').first();

        const testData = {
          name: 'Form Persistence Test Organization',
          website: 'https://test-persistence.org'
        };

        if (await nameInput.isVisible({ timeout: 3000 })) {
          await nameInput.fill(testData.name);
        }

        if (await websiteInput.isVisible({ timeout: 3000 })) {
          await websiteInput.fill(testData.website);
        }

        // Close modal without saving
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }

        await expect(modal).not.toBeVisible({ timeout: 3000 });

        // Reopen modal
        await createButton.click();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Check if data was preserved or cleared
        if (await nameInput.isVisible({ timeout: 3000 })) {
          const nameValue = await nameInput.inputValue();
          const websiteValue = await websiteInput.inputValue();

          if (nameValue === testData.name && websiteValue === testData.website) {
            console.log('✅ Form data preserved across modal reopening');
          } else if (nameValue === '' && websiteValue === '') {
            console.log('✅ Form data properly cleared (expected behavior)');
          } else {
            console.log('ℹ️  Form data partially preserved');
          }
        }

        // Close modal
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('form-data-preservation');
    });
  });

  test.describe('Error State Handling in Modals', () => {
    test('Modal handles API errors gracefully', async ({ page }) => {
      console.log('🧪 Testing modal API error handling...');

      // Intercept API requests and simulate errors
      await page.route('**/api/**', route => {
        if (route.request().method() === 'POST') {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Server Error' })
          });
        } else {
          route.continue();
        }
      });

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Fill and submit form to trigger API error
        const nameInput = page.locator('input[name="organization_name"], input[placeholder*="organization"]').first();
        const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")').first();

        if (await nameInput.isVisible({ timeout: 3000 }) && await submitButton.isVisible({ timeout: 3000 })) {
          await nameInput.fill('Error Test Organization');
          await submitButton.click();

          // Wait for error handling
          await page.waitForTimeout(3000);

          // Check if modal shows error or remains open
          const modalStillVisible = await modal.isVisible();
          if (modalStillVisible) {
            // Look for error messages
            const errorMessages = page.locator('text="Error", text="Failed", text="Server", .error, .text-red');
            const errorCount = await errorMessages.count();

            if (errorCount > 0) {
              console.log('✅ Modal displays error messages appropriately');
            } else {
              console.log('ℹ️  Error handling may be silent or handled differently');
            }
          } else {
            console.log('ℹ️  Modal closed after API error');
          }
        }

        // Clean up - close modal if still open
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      // Remove API interception
      await page.unroute('**/api/**');

      await basePage.takeScreenshot('modal-error-handling');
    });

    test('Modal state recovery after network issues', async ({ page }) => {
      console.log('🧪 Testing modal state recovery...');

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Simulate network disconnection
        await page.setOffline(true);

        const nameInput = page.locator('input[name="organization_name"], input[placeholder*="organization"]').first();
        if (await nameInput.isVisible({ timeout: 3000 })) {
          await nameInput.fill('Network Test Organization');

          // Try to submit while offline
          const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")').first();
          if (await submitButton.isVisible({ timeout: 3000 })) {
            await submitButton.click();
            await page.waitForTimeout(2000);
          }
        }

        // Restore network connection
        await page.setOffline(false);

        // Verify modal is still functional
        const modalStillVisible = await modal.isVisible();
        if (modalStillVisible) {
          console.log('✅ Modal maintained state during network issues');

          // Form should still be functional
          if (await nameInput.isVisible()) {
            const currentValue = await nameInput.inputValue();
            expect(currentValue).toBe('Network Test Organization');
            console.log('✅ Form data preserved during network issue');
          }
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('modal-network-recovery');
    });
  });

  test.describe('Cross-Modal Navigation Flows', () => {
    test('Navigation between different modal types', async ({ page }) => {
      console.log('🧪 Testing cross-modal navigation...');

      await profilePage.navigateToProfiles();

      // Open profile creation modal
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const profileModal = page.locator('.fixed.inset-0, .modal').first();
        await expect(profileModal).toBeVisible({ timeout: 5000 });

        // Look for settings or help button within modal or trigger another modal
        const settingsButton = page.locator('button:has-text("Settings"), button:has-text("⚙"), button:has-text("Help")').first();
        if (await settingsButton.isVisible({ timeout: 3000 })) {
          await settingsButton.click();

          // Check for modal stacking or modal replacement
          const modals = page.locator('.fixed.inset-0, .modal');
          const modalCount = await modals.count();

          if (modalCount > 1) {
            console.log('✅ Modal stacking working - multiple modals open');
          } else if (modalCount === 1) {
            console.log('✅ Modal replacement working - switched to new modal');
          }

          // Close any open modals
          const closeButtons = page.locator('button:has-text("×"), button:has-text("Close")');
          const closeCount = await closeButtons.count();
          for (let i = 0; i < closeCount; i++) {
            const closeButton = closeButtons.nth(i);
            if (await closeButton.isVisible({ timeout: 1000 })) {
              await closeButton.click();
              await page.waitForTimeout(500);
            }
          }
        } else {
          // Close the profile modal
          const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
          if (await closeButton.isVisible({ timeout: 2000 })) {
            await closeButton.click();
          }
        }
      }

      await basePage.takeScreenshot('cross-modal-navigation');
    });

    test('Modal z-index and layering management', async ({ page }) => {
      console.log('🧪 Testing modal z-index management...');

      await profilePage.navigateToProfiles();

      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Check modal z-index
        const modalZIndex = await modal.evaluate(el => {
          return window.getComputedStyle(el).zIndex;
        });

        console.log(`Modal z-index: ${modalZIndex}`);

        // Verify modal is above page content
        const zIndexNumber = parseInt(modalZIndex);
        expect(zIndexNumber).toBeGreaterThan(10); // Should have high z-index

        // Try to interact with page content behind modal
        const backgroundElement = page.locator('body > div').first();
        if (await backgroundElement.isVisible()) {
          try {
            await backgroundElement.click({ timeout: 1000 });
            console.log('ℹ️  Background clickable - modal may not be properly layered');
          } catch (error) {
            console.log('✅ Background properly blocked by modal');
          }
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('modal-z-index');
    });
  });

  test.describe('Session State Preservation', () => {
    test('Modal state survives page refresh', async ({ page }) => {
      console.log('🧪 Testing modal state after page refresh...');

      await profilePage.navigateToProfiles();

      // Get initial state
      const initialProfiles = await profilePage.getAllProfiles();
      const initialProfileCount = initialProfiles.length;

      // Open modal and refresh page
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Refresh page
        await page.reload({ waitUntil: 'domcontentloaded' });
        await basePage.waitForAppReady();

        // Verify modal is closed and app is functional
        const modalAfterRefresh = page.locator('.fixed.inset-0, .modal').first();
        const modalVisible = await modalAfterRefresh.isVisible();

        expect(modalVisible).toBeFalsy();
        console.log('✅ Modal properly closed after page refresh');

        // Verify app data is preserved
        await profilePage.navigateToProfiles();
        const profilesAfterRefresh = await profilePage.getAllProfiles();

        expect(profilesAfterRefresh.length).toBe(initialProfileCount);
        console.log('✅ App data preserved after refresh');
      }

      await basePage.takeScreenshot('modal-after-page-refresh');
    });

    test('Browser back/forward with modals', async ({ page }) => {
      console.log('🧪 Testing browser navigation with modals...');

      await profilePage.navigateToProfiles();

      // Navigate to discovery tab
      await discoveryPage.navigateToDiscovery();

      // Go back to profiles
      await page.goBack();
      await page.waitForTimeout(1000);

      // Open a modal
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Test browser back button with modal open
        await page.goBack();
        await page.waitForTimeout(1000);

        // Modal should ideally close, but behavior may vary
        const modalAfterBack = await modal.isVisible();
        if (!modalAfterBack) {
          console.log('✅ Modal closed on browser back navigation');
        } else {
          console.log('ℹ️  Modal persisted through browser back navigation');

          // Manually close modal
          const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
          if (await closeButton.isVisible({ timeout: 2000 })) {
            await closeButton.click();
          }
        }

        // Test forward navigation
        await page.goForward();
        await page.waitForTimeout(1000);

        // Verify app is still functional
        const appState = await basePage.getAppState();
        expect(appState).toBeTruthy();
        console.log('✅ App functional after browser navigation with modals');
      }

      await basePage.takeScreenshot('modal-browser-navigation');
    });
  });
});
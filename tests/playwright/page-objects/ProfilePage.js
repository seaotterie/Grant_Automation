/**
 * Profile Page Object Model
 * 
 * Handles all profile-related interactions:
 * - Profile creation and editing
 * - Profile selection and navigation
 * - Enhanced Data tab verification
 * - Tax data validation
 */

const { expect } = require('@playwright/test');
const BasePage = require('./BasePage');

class ProfilePage extends BasePage {
  constructor(page) {
    super(page);
  }

  /**
   * Navigate to the profiles tab
   */
  async navigateToProfiles() {
    await this.switchTab('profiles');
    await this.waitForAPIResponse('/api/profiles');
  }

  /**
   * Create a new profile with the given data
   * @param {Object} profileData - Profile information
   */
  async createProfile(profileData) {
    // Click create profile button
    await this.clickElement(this.selectors.profile_management.create_profile_button);
    
    // Wait for modal to appear
    await this.handleModal(this.selectors.profile_management.profile_modal, true);
    
    // Fill in profile information
    await this.fillInput(
      this.selectors.profile_management.organization_name_input, 
      profileData.organization_name
    );
    
    if (profileData.website_url) {
      await this.fillInput(
        this.selectors.profile_management.website_url_input,
        profileData.website_url
      );
    }
    
    // Add mission if provided
    if (profileData.mission) {
      const missionSelector = '[data-testid="mission-textarea"]';
      if (await this.isElementVisible(missionSelector)) {
        await this.fillInput(missionSelector, profileData.mission);
      }
    }
    
    // Add focus areas if provided
    if (profileData.focus_areas && profileData.focus_areas.length > 0) {
      await this.selectFocusAreas(profileData.focus_areas);
    }
    
    // Add geographic focus if provided
    if (profileData.geographic_focus && profileData.geographic_focus.length > 0) {
      await this.selectGeographicFocus(profileData.geographic_focus);
    }
    
    // Save the profile
    await this.clickElement(this.selectors.profile_management.save_profile_button);
    
    // Wait for modal to close and profile to be created
    await this.handleModal(this.selectors.profile_management.profile_modal, false);
    await this.waitForAPIResponse('/api/profiles');
    
    return await this.getCreatedProfileId();
  }

  /**
   * Select focus areas during profile creation
   * @param {Array} focusAreas - Array of focus area strings
   */
  async selectFocusAreas(focusAreas) {
    for (const area of focusAreas) {
      const areaSelector = `[data-testid="focus-area-${area.toLowerCase().replace(/\s+/g, '-')}"]`;
      if (await this.isElementVisible(areaSelector)) {
        await this.clickElement(areaSelector);
      }
    }
  }

  /**
   * Select geographic focus during profile creation
   * @param {Array} geographicAreas - Array of geographic area strings
   */
  async selectGeographicFocus(geographicAreas) {
    for (const area of geographicAreas) {
      const areaSelector = `[data-testid="geo-focus-${area.toLowerCase().replace(/\s+/g, '-')}"]`;
      if (await this.isElementVisible(areaSelector)) {
        await this.clickElement(areaSelector);
      }
    }
  }

  /**
   * Get the ID of the most recently created profile
   */
  async getCreatedProfileId() {
    const appState = await this.getAppState();
    const profiles = appState.profiles || [];
    
    if (profiles.length > 0) {
      // Return the most recent profile ID
      return profiles[profiles.length - 1].profile_id || profiles[profiles.length - 1].id;
    }
    
    return null;
  }

  /**
   * Select an existing profile by ID or name
   * @param {string} profileIdentifier - Profile ID or name
   */
  async selectProfile(profileIdentifier) {
    // Look for profile card with matching ID or name
    const profileCards = await this.page.locator(this.selectors.profile_management.profile_card);
    const count = await profileCards.count();
    
    for (let i = 0; i < count; i++) {
      const card = profileCards.nth(i);
      const cardText = await card.textContent();
      
      if (cardText.includes(profileIdentifier)) {
        await card.click();
        
        // Wait for profile to be selected in app state
        await this.page.waitForFunction(
          (identifier) => {
            const app = window.catalynxApp;
            return app && app.selectedProfile && 
                   (app.selectedProfile.profile_id === identifier ||
                    app.selectedProfile.id === identifier ||
                    app.selectedProfile.organization_name === identifier);
          },
          profileIdentifier,
          { timeout: 5000 }
        );
        
        return true;
      }
    }
    
    throw new Error(`Profile not found: ${profileIdentifier}`);
  }

  /**
   * Navigate to Enhanced Data tab for tax data verification
   * @param {string} profileId - Profile ID to view
   */
  async navigateToEnhancedData(profileId) {
    // Ensure profile is selected
    if (profileId) {
      await this.selectProfile(profileId);
    }
    
    // Click Enhanced Data tab
    await this.clickElement(this.selectors.enhanced_data.enhanced_data_tab);
    
    // Wait for data to load
    await this.waitForLoadingComplete();
  }

  /**
   * Verify tax data display in Enhanced Data tab
   * @param {Object} expectedData - Expected tax data values
   */
  async verifyTaxDataDisplay(expectedData) {
    // Check if EIN is displayed
    if (expectedData.ein) {
      const einText = await this.getElementText(this.selectors.enhanced_data.ein_display);
      expect(einText).toContain(expectedData.ein);
    }
    
    // Check if BMF data section is visible
    if (expectedData.expected_bmf_data) {
      const bmfSection = await this.isElementVisible(this.selectors.enhanced_data.bmf_data_section);
      expect(bmfSection).toBeTruthy();
    }
    
    // Verify source attribution is displayed
    const sourceAttribution = await this.isElementVisible(this.selectors.enhanced_data.source_attribution);
    expect(sourceAttribution).toBeTruthy();
    
    // Check confidence scoring
    const confidenceScore = await this.isElementVisible(this.selectors.enhanced_data.confidence_score);
    expect(confidenceScore).toBeTruthy();
    
    // Verify verification badge for real data
    if (expectedData.expected_bmf_data || expectedData.expected_990_data) {
      const verificationBadge = await this.isElementVisible(this.selectors.enhanced_data.verification_badge);
      expect(verificationBadge).toBeTruthy();
    }
  }

  /**
   * Verify that source attribution shows correct data sources
   * @param {Array} expectedSources - Expected data source names
   */
  async verifySourceAttribution(expectedSources) {
    const attributionElement = this.page.locator(this.selectors.enhanced_data.source_attribution);
    await expect(attributionElement).toBeVisible();
    
    const attributionText = await attributionElement.textContent();
    
    for (const source of expectedSources) {
      expect(attributionText).toContain(source);
    }
  }

  /**
   * Get confidence score value from the UI
   * @returns {number} Confidence score as a percentage
   */
  async getConfidenceScore() {
    const scoreElement = this.page.locator(this.selectors.enhanced_data.confidence_score);
    await expect(scoreElement).toBeVisible();
    
    const scoreText = await scoreElement.textContent();
    const scoreMatch = scoreText.match(/(\d+)%/);
    
    if (scoreMatch) {
      return parseInt(scoreMatch[1]);
    }
    
    throw new Error('Could not extract confidence score from UI');
  }

  /**
   * Verify that fake/test data is not displayed
   */
  async verifyNoFakeData() {
    const page = this.page;
    
    // Check for common test data indicators
    const fakeDataIndicators = [
      'Test Organization',
      'Example.com',
      'Fake',
      'Sample',
      '123-45-6789',
      'test@example.com'
    ];
    
    const pageContent = await page.textContent('body');
    
    for (const indicator of fakeDataIndicators) {
      expect(pageContent).not.toContain(indicator);
    }
  }

  /**
   * Check if organization data was automatically populated from website
   * @param {string} websiteUrl - The website URL that was entered
   */
  async verifyWebsiteDataExtraction(websiteUrl) {
    // Wait for any automatic data extraction to complete
    await this.waitForLoadingComplete();
    
    // Check if EIN was extracted
    const einElement = this.page.locator(this.selectors.enhanced_data.ein_display);
    
    if (await einElement.isVisible()) {
      const einText = await einElement.textContent();
      
      // EIN should be in format XX-XXXXXXX
      const einPattern = /\d{2}-\d{7}/;
      expect(einText).toMatch(einPattern);
      
      console.log(`✅ EIN extracted from website ${websiteUrl}: ${einText}`);
      return einText;
    }
    
    return null;
  }

  /**
   * Get all profiles listed on the page
   * @returns {Array} Array of profile objects
   */
  async getAllProfiles() {
    await this.navigateToProfiles();
    
    const profileCards = await this.page.locator(this.selectors.profile_management.profile_card);
    const count = await profileCards.count();
    const profiles = [];
    
    for (let i = 0; i < count; i++) {
      const card = profileCards.nth(i);
      const name = await card.getAttribute('data-profile-name') || 
                   await card.locator('[data-testid="profile-name"]').textContent();
      const id = await card.getAttribute('data-profile-id') ||
                 await card.locator('[data-testid="profile-id"]').textContent();
      
      profiles.push({ id, name });
    }
    
    return profiles;
  }

  /**
   * Delete a profile by ID
   * @param {string} profileId - Profile ID to delete
   */
  async deleteProfile(profileId) {
    await this.selectProfile(profileId);
    
    const deleteButton = `[data-testid="delete-profile-${profileId}"]`;
    if (await this.isElementVisible(deleteButton)) {
      await this.clickElement(deleteButton);
      
      // Confirm deletion if confirmation dialog appears
      const confirmButton = '[data-testid="confirm-delete"]';
      if (await this.isElementVisible(confirmButton)) {
        await this.clickElement(confirmButton);
      }
      
      // Wait for profile to be removed
      await this.waitForAPIResponse('/api/profiles');
    }
  }

  /**
   * Export profile data
   * @param {string} profileId - Profile ID to export
   * @param {string} format - Export format (pdf, excel, etc.)
   */
  async exportProfile(profileId, format = 'pdf') {
    await this.selectProfile(profileId);
    
    const exportButton = `[data-testid="export-${format}-btn"]`;
    await this.clickElement(exportButton);
    
    // Wait for download to start
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain(profileId);
    expect(download.suggestedFilename()).toContain(format);
    
    return download;
  }
}

module.exports = ProfilePage;
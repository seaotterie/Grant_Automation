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

  /**
   * Advanced profile creation with validation
   * @param {Object} profileData - Enhanced profile data
   * @param {Object} options - Creation options
   */
  async createProfileWithValidation(profileData, options = {}) {
    const {
      validateFields = true,
      skipDuplicateCheck = false,
      takeScreenshots = false
    } = options;

    try {
      // Check for duplicates if requested
      if (!skipDuplicateCheck) {
        const existingProfiles = await this.getAllProfiles();
        const duplicate = existingProfiles.find(p =>
          p.name === profileData.organization_name ||
          p.ein === profileData.ein
        );

        if (duplicate) {
          throw new Error(`Duplicate profile detected: ${duplicate.name || duplicate.ein}`);
        }
      }

      // Take initial screenshot if requested
      if (takeScreenshots) {
        await this.takeScreenshot('profile-creation-start');
      }

      // Enhanced form filling with validation
      await this.clickElement(this.selectors.profile_management.create_profile_button);
      await this.handleModal(this.selectors.profile_management.profile_modal, true);

      // Organization name (required)
      await this.fillInputWithValidation('organization_name', profileData.organization_name, { required: true });

      // EIN (if provided)
      if (profileData.ein) {
        await this.fillInputWithValidation('ein', profileData.ein, { pattern: /^\d{2}-?\d{7}$/ });
      }

      // Website URL (if provided)
      if (profileData.website_url) {
        await this.fillInputWithValidation('website_url', profileData.website_url, { type: 'url' });
      }

      // Contact information
      if (profileData.contact_email) {
        await this.fillInputWithValidation('contact_email', profileData.contact_email, { type: 'email' });
      }

      if (profileData.phone_number) {
        await this.fillInputWithValidation('phone_number', profileData.phone_number);
      }

      // Address information
      if (profileData.address) {
        await this.fillAddressInformation(profileData.address);
      }

      // Financial information
      if (profileData.annual_budget) {
        await this.fillInputWithValidation('annual_budget', profileData.annual_budget.toString(), { type: 'number' });
      }

      // Mission and description
      if (profileData.mission) {
        await this.fillTextArea('mission', profileData.mission);
      }

      if (profileData.description) {
        await this.fillTextArea('description', profileData.description);
      }

      // Focus areas and geographic focus
      if (profileData.focus_areas) {
        await this.selectFocusAreas(profileData.focus_areas);
      }

      if (profileData.geographic_focus) {
        await this.selectGeographicFocus(profileData.geographic_focus);
      }

      // Take form completion screenshot
      if (takeScreenshots) {
        await this.takeScreenshot('profile-form-completed');
      }

      // Save and validate
      await this.clickElement(this.selectors.profile_management.save_profile_button);
      await this.handleModal(this.selectors.profile_management.profile_modal, false);
      await this.waitForAPIResponse('/api/profiles');

      const profileId = await this.getCreatedProfileId();

      // Verify creation success
      if (validateFields) {
        await this.validateProfileCreation(profileId, profileData);
      }

      if (takeScreenshots) {
        await this.takeScreenshot('profile-creation-complete');
      }

      return profileId;

    } catch (error) {
      await this.takeScreenshot(`profile-creation-error-${Date.now()}`);
      throw error;
    }
  }

  /**
   * Fill input with validation
   */
  async fillInputWithValidation(fieldName, value, validation = {}) {
    const selector = `input[name="${fieldName}"], input[id="${fieldName}"], [data-testid="${fieldName}"]`;

    await this.fillInput(selector, value);

    // Validate based on type
    if (validation.required && !value) {
      throw new Error(`Required field ${fieldName} is empty`);
    }

    if (validation.pattern && !validation.pattern.test(value)) {
      throw new Error(`Field ${fieldName} does not match pattern: ${validation.pattern}`);
    }

    if (validation.type === 'email' && !value.includes('@')) {
      throw new Error(`Invalid email format for ${fieldName}: ${value}`);
    }

    if (validation.type === 'url' && !value.match(/^https?:\/\//)) {
      throw new Error(`Invalid URL format for ${fieldName}: ${value}`);
    }
  }

  /**
   * Fill textarea fields
   */
  async fillTextArea(fieldName, value) {
    const selector = `textarea[name="${fieldName}"], textarea[id="${fieldName}"], [data-testid="${fieldName}-textarea"]`;

    if (await this.isElementVisible(selector)) {
      await this.fillInput(selector, value);
    }
  }

  /**
   * Fill address information
   */
  async fillAddressInformation(address) {
    const addressFields = {
      street: address.street,
      city: address.city,
      state: address.state,
      zip_code: address.zip_code,
      country: address.country || 'United States'
    };

    for (const [field, value] of Object.entries(addressFields)) {
      if (value) {
        const selector = `input[name="${field}"], input[id="${field}"], [data-testid="${field}"]`;
        if (await this.isElementVisible(selector)) {
          await this.fillInput(selector, value);
        }
      }
    }
  }

  /**
   * Validate profile creation
   */
  async validateProfileCreation(profileId, originalData) {
    await this.selectProfile(profileId);

    // Navigate to Enhanced Data to verify
    await this.navigateToEnhancedData(profileId);

    // Validate organization name
    const nameElement = this.page.locator('[data-testid="organization-name"], .organization-name');
    if (await nameElement.isVisible()) {
      const displayedName = await nameElement.textContent();
      expect(displayedName).toContain(originalData.organization_name);
    }

    // Validate EIN if provided
    if (originalData.ein) {
      await this.verifyTaxDataDisplay({ ein: originalData.ein });
    }

    // Validate website if provided
    if (originalData.website_url) {
      const websiteElement = this.page.locator('[data-testid="website-url"], .website-url');
      if (await websiteElement.isVisible()) {
        const displayedUrl = await websiteElement.textContent();
        expect(displayedUrl).toContain(originalData.website_url);
      }
    }
  }

  /**
   * Bulk profile operations
   */
  async createMultipleProfiles(profilesData, options = {}) {
    const results = [];
    const { batchSize = 5, delayBetweenBatches = 2000 } = options;

    for (let i = 0; i < profilesData.length; i += batchSize) {
      const batch = profilesData.slice(i, i + batchSize);

      console.log(`Creating batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(profilesData.length / batchSize)}`);

      for (const profileData of batch) {
        try {
          const profileId = await this.createProfileWithValidation(profileData, {
            ...options,
            skipDuplicateCheck: true // Skip for bulk operations
          });

          results.push({
            success: true,
            profileId: profileId,
            data: profileData
          });
        } catch (error) {
          results.push({
            success: false,
            error: error.message,
            data: profileData
          });
        }
      }

      // Delay between batches to avoid overwhelming the system
      if (i + batchSize < profilesData.length) {
        await this.page.waitForTimeout(delayBetweenBatches);
      }
    }

    return results;
  }

  /**
   * Profile comparison functionality
   */
  async compareProfiles(profileId1, profileId2) {
    const profile1Data = await this.getProfileData(profileId1);
    const profile2Data = await this.getProfileData(profileId2);

    return {
      profile1: profile1Data,
      profile2: profile2Data,
      differences: this.calculateProfileDifferences(profile1Data, profile2Data),
      similarity: this.calculateProfileSimilarity(profile1Data, profile2Data)
    };
  }

  /**
   * Get comprehensive profile data
   */
  async getProfileData(profileId) {
    await this.selectProfile(profileId);
    await this.navigateToEnhancedData(profileId);

    return await this.page.evaluate(() => {
      const data = {
        basicInfo: {},
        financialInfo: {},
        contactInfo: {},
        metadata: {}
      };

      // Extract basic information
      const nameElement = document.querySelector('[data-testid="organization-name"], .organization-name');
      if (nameElement) data.basicInfo.name = nameElement.textContent.trim();

      const einElement = document.querySelector('[data-testid="ein"], .ein-display');
      if (einElement) data.basicInfo.ein = einElement.textContent.trim();

      const websiteElement = document.querySelector('[data-testid="website-url"], .website-url');
      if (websiteElement) data.basicInfo.website = websiteElement.textContent.trim();

      // Extract financial information
      const budgetElement = document.querySelector('[data-testid="annual-budget"], .annual-budget');
      if (budgetElement) data.financialInfo.annualBudget = budgetElement.textContent.trim();

      // Extract metadata
      const confidenceElement = document.querySelector('[data-testid="confidence-score"], .confidence-score');
      if (confidenceElement) data.metadata.confidenceScore = confidenceElement.textContent.trim();

      const lastUpdatedElement = document.querySelector('[data-testid="last-updated"], .last-updated');
      if (lastUpdatedElement) data.metadata.lastUpdated = lastUpdatedElement.textContent.trim();

      return data;
    });
  }

  /**
   * Calculate differences between two profiles
   */
  calculateProfileDifferences(profile1, profile2) {
    const differences = [];

    const compareObjects = (obj1, obj2, path = '') => {
      for (const key in obj1) {
        const fullPath = path ? `${path}.${key}` : key;

        if (obj2[key] === undefined) {
          differences.push({
            field: fullPath,
            profile1Value: obj1[key],
            profile2Value: 'undefined',
            type: 'missing_in_profile2'
          });
        } else if (obj1[key] !== obj2[key]) {
          if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
            compareObjects(obj1[key], obj2[key], fullPath);
          } else {
            differences.push({
              field: fullPath,
              profile1Value: obj1[key],
              profile2Value: obj2[key],
              type: 'different_values'
            });
          }
        }
      }

      for (const key in obj2) {
        const fullPath = path ? `${path}.${key}` : key;
        if (obj1[key] === undefined) {
          differences.push({
            field: fullPath,
            profile1Value: 'undefined',
            profile2Value: obj2[key],
            type: 'missing_in_profile1'
          });
        }
      }
    };

    compareObjects(profile1, profile2);
    return differences;
  }

  /**
   * Calculate similarity score between profiles
   */
  calculateProfileSimilarity(profile1, profile2) {
    let totalFields = 0;
    let matchingFields = 0;

    const compareFields = (obj1, obj2) => {
      for (const key in obj1) {
        totalFields++;
        if (obj2[key] !== undefined) {
          if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
            compareFields(obj1[key], obj2[key]);
          } else if (obj1[key] === obj2[key]) {
            matchingFields++;
          }
        }
      }

      for (const key in obj2) {
        if (obj1[key] === undefined) {
          totalFields++;
        }
      }
    };

    compareFields(profile1, profile2);

    return {
      totalFields: totalFields,
      matchingFields: matchingFields,
      similarityPercentage: totalFields > 0 ? (matchingFields / totalFields) * 100 : 0
    };
  }

  /**
   * Advanced profile search and filtering
   */
  async searchProfiles(searchCriteria) {
    await this.navigateToProfiles();

    const allProfiles = await this.getAllProfiles();
    const filteredProfiles = [];

    for (const profile of allProfiles) {
      const profileData = await this.getProfileData(profile.id);

      let matches = true;

      // Check name criteria
      if (searchCriteria.name && !profileData.basicInfo.name?.toLowerCase().includes(searchCriteria.name.toLowerCase())) {
        matches = false;
      }

      // Check EIN criteria
      if (searchCriteria.ein && profileData.basicInfo.ein !== searchCriteria.ein) {
        matches = false;
      }

      // Check website criteria
      if (searchCriteria.website && !profileData.basicInfo.website?.includes(searchCriteria.website)) {
        matches = false;
      }

      // Check budget range
      if (searchCriteria.budgetRange) {
        const budget = parseInt(profileData.financialInfo.annualBudget?.replace(/[^\d]/g, '') || '0');
        if (budget < searchCriteria.budgetRange.min || budget > searchCriteria.budgetRange.max) {
          matches = false;
        }
      }

      if (matches) {
        filteredProfiles.push({
          ...profile,
          data: profileData
        });
      }
    }

    return filteredProfiles;
  }

  /**
   * Profile performance monitoring
   */
  async monitorProfileOperations(operations = []) {
    const performanceMetrics = {
      operations: [],
      totalTime: 0,
      averageTime: 0,
      errors: []
    };

    for (const operation of operations) {
      const startTime = performance.now();

      try {
        switch (operation.type) {
          case 'create':
            await this.createProfileWithValidation(operation.data);
            break;
          case 'select':
            await this.selectProfile(operation.profileId);
            break;
          case 'delete':
            await this.deleteProfile(operation.profileId);
            break;
          case 'export':
            await this.exportProfile(operation.profileId, operation.format);
            break;
          default:
            throw new Error(`Unknown operation type: ${operation.type}`);
        }

        const endTime = performance.now();
        const duration = endTime - startTime;

        performanceMetrics.operations.push({
          type: operation.type,
          duration: duration,
          success: true
        });

        performanceMetrics.totalTime += duration;

      } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;

        performanceMetrics.operations.push({
          type: operation.type,
          duration: duration,
          success: false,
          error: error.message
        });

        performanceMetrics.errors.push({
          operation: operation.type,
          error: error.message
        });

        performanceMetrics.totalTime += duration;
      }
    }

    performanceMetrics.averageTime = performanceMetrics.operations.length > 0
      ? performanceMetrics.totalTime / performanceMetrics.operations.length
      : 0;

    return performanceMetrics;
  }
}

module.exports = ProfilePage;
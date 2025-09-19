/**
 * Discovery Page Object Model
 * 
 * Handles all discovery-related interactions:
 * - Discovery execution and configuration
 * - Results filtering and pagination
 * - Opportunity management and scoring
 * - Stage management workflow
 */

const { expect } = require('@playwright/test');
const BasePage = require('./BasePage');

class DiscoveryPage extends BasePage {
  constructor(page) {
    super(page);
  }

  /**
   * Navigate to the Discovery tab
   */
  async navigateToDiscovery() {
    await this.switchTab('discovery');
    await this.waitForLoadingComplete();
  }

  /**
   * Execute discovery for the selected profile
   * @param {Object} options - Discovery configuration options
   */
  async executeDiscovery(options = {}) {
    const {
      tracks = ['nonprofit', 'government'],
      maxResults = 50,
      includeEntityCache = true
    } = options;
    
    // Ensure we're on the discovery tab
    await this.navigateToDiscovery();
    
    // Configure discovery options if UI allows
    await this.configureDiscoveryOptions(tracks, maxResults, includeEntityCache);
    
    // Click execute discovery button
    await this.clickElement(this.selectors.discovery.execute_discovery_button);
    
    // Wait for discovery to complete
    await this.waitForDiscoveryCompletion();
    
    // Wait for results to load
    await this.waitForAPIResponse('/api/discovery');
    await this.waitForLoadingComplete();
    
    return await this.getDiscoveryResults();
  }

  /**
   * Configure discovery options (if UI provides controls)
   * @param {Array} tracks - Discovery tracks to use
   * @param {number} maxResults - Maximum results to return
   * @param {boolean} includeEntityCache - Whether to include entity cache
   */
  async configureDiscoveryOptions(tracks, maxResults, includeEntityCache) {
    // Check for discovery configuration panel
    const configPanel = '[data-testid="discovery-config-panel"]';
    
    if (await this.isElementVisible(configPanel)) {
      // Configure tracks
      for (const track of tracks) {
        const trackCheckbox = `[data-testid="track-${track}-checkbox"]`;
        if (await this.isElementVisible(trackCheckbox)) {
          const isChecked = await this.page.isChecked(trackCheckbox);
          if (!isChecked) {
            await this.clickElement(trackCheckbox);
          }
        }
      }
      
      // Set max results if input exists
      const maxResultsInput = '[data-testid="max-results-input"]';
      if (await this.isElementVisible(maxResultsInput)) {
        await this.fillInput(maxResultsInput, maxResults.toString());
      }
      
      // Configure entity cache option
      const entityCacheCheckbox = '[data-testid="entity-cache-checkbox"]';
      if (await this.isElementVisible(entityCacheCheckbox)) {
        const isChecked = await this.page.isChecked(entityCacheCheckbox);
        if (isChecked !== includeEntityCache) {
          await this.clickElement(entityCacheCheckbox);
        }
      }
    }
  }

  /**
   * Wait for discovery execution to complete
   */
  async waitForDiscoveryCompletion() {
    // Wait for loading state to start
    await this.page.waitForTimeout(1000);
    
    // Wait for loading to complete
    await this.waitForLoadingComplete();
    
    // Wait for success notification or results to appear
    try {
      await this.page.waitForSelector(
        this.selectors.discovery.discovery_results,
        { state: 'visible', timeout: this.timeouts.discovery_execution }
      );
    } catch (error) {
      throw new Error('Discovery execution timed out or failed');
    }
  }

  /**
   * Get discovery results from the UI
   * @returns {Array} Array of discovery result objects
   */
  async getDiscoveryResults() {
    await this.page.waitForSelector(this.selectors.discovery.results_table, {
      state: 'visible',
      timeout: this.timeouts.discovery_execution || 30000
    });
    
    const results = await this.page.evaluate(() => {
      const app = window.catalynxApp;
      return app ? app.discoveryResults : [];
    });
    
    return results || [];
  }

  /**
   * Get the count of discovery results
   * @returns {number} Number of results found
   */
  async getResultsCount() {
    const results = await this.getDiscoveryResults();
    return results.length;
  }

  /**
   * Apply filters to discovery results
   * @param {Object} filters - Filter criteria
   */
  async applyFilters(filters) {
    const {
      stage = null,
      minScore = null,
      organizationType = null,
      geographicArea = null
    } = filters;
    
    // Open filter dropdown
    await this.clickElement(this.selectors.discovery.filter_dropdown);
    
    // Apply stage filter
    if (stage) {
      const stageFilter = `[data-testid="filter-stage-${stage}"]`;
      if (await this.isElementVisible(stageFilter)) {
        await this.clickElement(stageFilter);
      }
    }
    
    // Apply minimum score filter
    if (minScore) {
      const scoreInput = '[data-testid="min-score-input"]';
      if (await this.isElementVisible(scoreInput)) {
        await this.fillInput(scoreInput, minScore.toString());
      }
    }
    
    // Apply organization type filter
    if (organizationType) {
      const typeFilter = `[data-testid="filter-org-type-${organizationType}"]`;
      if (await this.isElementVisible(typeFilter)) {
        await this.clickElement(typeFilter);
      }
    }
    
    // Apply geographic filter
    if (geographicArea) {
      const geoFilter = `[data-testid="filter-geo-${geographicArea.toLowerCase()}"]`;
      if (await this.isElementVisible(geoFilter)) {
        await this.clickElement(geoFilter);
      }
    }
    
    // Apply filters
    const applyFiltersButton = '[data-testid="apply-filters-btn"]';
    if (await this.isElementVisible(applyFiltersButton)) {
      await this.clickElement(applyFiltersButton);
      await this.waitForLoadingComplete();
    }
  }

  /**
   * Navigate through paginated results
   * @param {number} pageNumber - Page number to navigate to
   */
  async navigateToPage(pageNumber) {
    const pagination = this.selectors.discovery.pagination_controls;
    await this.page.waitForSelector(pagination, {
      state: 'visible',
      timeout: this.timeouts.navigation || 10000
    });
    
    const pageButton = `[data-testid="page-${pageNumber}"]`;
    if (await this.isElementVisible(pageButton)) {
      await this.clickElement(pageButton);
      await this.waitForLoadingComplete();
    } else {
      throw new Error(`Page ${pageNumber} not found in pagination`);
    }
  }

  /**
   * Select specific opportunities from results
   * @param {Array} organizationNames - Names of organizations to select
   */
  async selectOpportunities(organizationNames) {
    const selectedOpportunities = [];
    
    for (const orgName of organizationNames) {
      const opportunityRow = `[data-testid="opportunity-row"][data-org-name="${orgName}"]`;
      
      if (await this.isElementVisible(opportunityRow)) {
        const checkbox = `${opportunityRow} [data-testid="opportunity-checkbox"]`;
        await this.clickElement(checkbox);
        selectedOpportunities.push(orgName);
      }
    }
    
    return selectedOpportunities;
  }

  /**
   * Move selected opportunities to a different stage
   * @param {Array} organizationNames - Organizations to move
   * @param {string} targetStage - Target stage (discovery, prospects, applications, etc.)
   */
  async moveOpportunitiesToStage(organizationNames, targetStage) {
    // Select opportunities
    await this.selectOpportunities(organizationNames);
    
    // Click stage management button
    const stageButton = '[data-testid="manage-stages-btn"]';
    await this.clickElement(stageButton);
    
    // Select target stage
    const stageOption = `[data-testid="stage-option-${targetStage}"]`;
    await this.clickElement(stageOption);
    
    // Confirm action
    const confirmButton = '[data-testid="confirm-stage-move"]';
    if (await this.isElementVisible(confirmButton)) {
      await this.clickElement(confirmButton);
    }
    
    // Wait for update to complete
    await this.waitForAPIResponse('/api/opportunities');
    await this.waitForLoadingComplete();
  }

  /**
   * Execute comprehensive scoring on selected opportunities
   * @param {Array} organizationNames - Organizations to score
   * @param {Array} scoringMethods - Scoring methods to use
   */
  async executeComprehensiveScoring(organizationNames, scoringMethods = ['government', 'financial', 'network']) {
    // Select opportunities
    await this.selectOpportunities(organizationNames);
    
    // Click scoring button
    const scoringButton = '[data-testid="comprehensive-scoring-btn"]';
    await this.clickElement(scoringButton);
    
    // Configure scoring methods
    for (const method of scoringMethods) {
      const methodCheckbox = `[data-testid="scoring-method-${method}"]`;
      if (await this.isElementVisible(methodCheckbox)) {
        const isChecked = await this.page.isChecked(methodCheckbox);
        if (!isChecked) {
          await this.clickElement(methodCheckbox);
        }
      }
    }
    
    // Execute scoring
    const executeButton = '[data-testid="execute-scoring-btn"]';
    await this.clickElement(executeButton);
    
    // Wait for scoring to complete
    await this.waitForLoadingComplete();
    await this.waitForAPIResponse('/api/scoring');
    
    return await this.getScoringResults();
  }

  /**
   * Get scoring results from the application state
   * @returns {Array} Array of scoring results
   */
  async getScoringResults() {
    return await this.page.evaluate(() => {
      const app = window.catalynxApp;
      return app ? app.scoringResults : [];
    });
  }

  /**
   * Verify discovery results quality
   * @param {Object} expectations - Expected result characteristics
   */
  async verifyResultsQuality(expectations) {
    const results = await this.getDiscoveryResults();
    
    // Check minimum number of results
    if (expectations.minResults) {
      expect(results.length).toBeGreaterThanOrEqual(expectations.minResults);
    }
    
    // Check maximum number of results
    if (expectations.maxResults) {
      expect(results.length).toBeLessThanOrEqual(expectations.maxResults);
    }
    
    // Verify all results have required fields
    const requiredFields = expectations.requiredFields || ['organization_name', 'ein'];
    
    for (const result of results) {
      for (const field of requiredFields) {
        expect(result).toHaveProperty(field);
        expect(result[field]).toBeTruthy();
      }
    }
    
    // Check for data quality indicators
    if (expectations.noTestData) {
      for (const result of results) {
        expect(result.organization_name).not.toMatch(/test|fake|sample|example/i);
        if (result.ein) {
          expect(result.ein).toMatch(/^\d{2}-\d{7}$/); // Valid EIN format
        }
      }
    }
  }

  /**
   * Export discovery results
   * @param {string} format - Export format (pdf, excel, csv)
   * @param {Object} options - Export options
   */
  async exportResults(format = 'excel', options = {}) {
    const exportButton = `[data-testid="export-${format}-btn"]`;
    await this.clickElement(exportButton);
    
    // Configure export options if dialog appears
    const exportDialog = '[data-testid="export-options-dialog"]';
    if (await this.isElementVisible(exportDialog)) {
      // Configure options as needed
      if (options.includeScoring) {
        const includeScoringCheckbox = '[data-testid="include-scoring-checkbox"]';
        if (await this.isElementVisible(includeScoringCheckbox)) {
          await this.clickElement(includeScoringCheckbox);
        }
      }
      
      // Confirm export
      const confirmExportButton = '[data-testid="confirm-export-btn"]';
      await this.clickElement(confirmExportButton);
    }
    
    // Wait for download
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain(format);
    
    return download;
  }

  /**
   * Get opportunity details for a specific organization
   * @param {string} organizationName - Name of the organization
   */
  async getOpportunityDetails(organizationName) {
    const opportunityRow = `[data-testid="opportunity-row"][data-org-name="${organizationName}"]`;
    await this.clickElement(opportunityRow);
    
    // Wait for details panel to open
    const detailsPanel = '[data-testid="opportunity-details-panel"]';
    await this.page.waitForSelector(detailsPanel, { state: 'visible' });
    
    // Extract details from panel
    return await this.page.evaluate(() => {
      const panel = document.querySelector('[data-testid="opportunity-details-panel"]');
      if (!panel) return null;
      
      return {
        organizationName: panel.querySelector('[data-testid="org-name"]')?.textContent,
        ein: panel.querySelector('[data-testid="ein"]')?.textContent,
        revenue: panel.querySelector('[data-testid="revenue"]')?.textContent,
        assets: panel.querySelector('[data-testid="assets"]')?.textContent,
        eligibilityScore: panel.querySelector('[data-testid="eligibility-score"]')?.textContent,
        compositeScore: panel.querySelector('[data-testid="composite-score"]')?.textContent
      };
    });
  }

  /**
   * Close opportunity details panel
   */
  async closeOpportunityDetails() {
    const closeButton = '[data-testid="close-details-btn"]';
    if (await this.isElementVisible(closeButton)) {
      await this.clickElement(closeButton);
    }
  }
}

module.exports = DiscoveryPage;
/**
 * Screening Management Module
 * Handles discovery execution and opportunity screening
 *
 * Replaces: DISCOVER, PLAN, and ANALYZE stages (3 → 1 stage)
 * APIs Used: /api/v2/discovery/*, Tool 10 (Opportunity Screening)
 */

function screeningModule() {
    return {
        // =================================================================
        // STATE
        // =================================================================

        // Discovery State
        discoveryResults: [],
        discoveryLoading: false,
        currentDiscoveryTrack: 'nonprofit',
        discoverySession: null,
        summaryCounts: {
            total_found: 0,
            auto_qualified: 0,
            review: 0,
            consider: 0,
            low_priority: 0,
            scrapy_completed: 0
        },

        // Screening State
        screeningResults: [],
        screeningLoading: false,
        screeningMode: 'fast', // 'fast' or 'thorough'

        // Selection State (Human Gateway)
        selectedForIntelligence: [],
        selectionNotes: {},

        // Filters & Sorting
        filterCriteria: {
            ntee_codes: [],
            states: [],
            min_assets: null,
            max_assets: null,
            min_revenue: null,
            max_revenue: null,
            foundation_code: null
        },
        sortBy: 'score',
        sortOrder: 'desc',

        // UI State
        showCriteriaModal: false,
        showSelectionPanel: false,
        viewMode: 'grid', // 'grid' or 'list'
        showDetailsModal: false,
        selectedOpportunity: null,
        detailsModalTab: 'scores' // 'scores', 'details', 'grants', 'website'

        // =================================================================
        // DISCOVERY OPERATIONS
        // =================================================================

        /**
         * Execute nonprofit discovery using new unified endpoint
         * Calls: POST /api/v2/profiles/{profileId}/discover
         * Returns: BMF + 990 + Multi-Dimensional Scores
         *
         * @param {string} profileId - Profile ID with Target NTEE Codes
         * @param {Object} options - Discovery options (max_results, auto_scrapy_count)
         */
        async executeNonprofitDiscovery(profileId, options = {}) {
            this.discoveryLoading = true;
            this.discoveryResults = [];

            try {
                const requestData = {
                    max_results: options.max_results || 200,
                    auto_scrapy_count: options.auto_scrapy_count || 20
                };

                console.log(`Starting nonprofit discovery for profile ${profileId}...`);

                const response = await fetch(`/api/v2/profiles/${profileId}/discover`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Discovery failed');
                }

                const data = await response.json();

                if (data.status === 'success') {
                    this.discoveryResults = data.opportunities || [];
                    this.summaryCounts = data.summary;

                    console.log(`Discovery complete: ${data.summary.total_found} organizations found`);
                    console.log(`Auto-Qualified: ${data.summary.auto_qualified}, Review: ${data.summary.review}`);

                    this.showNotification?.(
                        `Found ${data.summary.total_found} opportunities (${data.summary.auto_qualified} auto-qualified)`,
                        'success'
                    );

                    return data;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Nonprofit discovery failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.discoveryLoading = false;
            }
        },

        /**
         * Execute discovery across different tracks (LEGACY - for other tracks)
         * @param {string} track - nonprofit, federal, state, commercial, bmf
         * @param {Object} criteria - Search/filter criteria
         * @param {string} profileId - Optional profile context
         */
        async executeDiscovery(track, criteria = null, profileId = null) {
            this.discoveryLoading = true;
            this.discoveryResults = [];

            try {
                const requestData = {
                    track: track || this.currentDiscoveryTrack,
                    criteria: criteria || this.filterCriteria,
                    profile_id: profileId
                };

                const response = await fetch('/api/v2/discovery/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Discovery failed');
                }

                const data = await response.json();

                if (data.success) {
                    this.discoveryResults = data.results || [];
                    this.discoverySession = data.session_id;
                    this.currentDiscoveryTrack = track;

                    console.log(`Discovery complete: ${data.total_results} results (${track})`);
                    this.showNotification?.(
                        `Found ${data.total_results} opportunities`,
                        'success'
                    );

                    return data;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Discovery failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.discoveryLoading = false;
            }
        },

        /**
         * Execute BMF discovery (optimized path)
         * @param {Object} filters - BMF-specific filters
         */
        async executeBMFDiscovery(filters = null) {
            this.discoveryLoading = true;

            try {
                const params = new URLSearchParams();
                const criteria = filters || this.filterCriteria;

                if (criteria.ntee_codes?.length) {
                    params.append('ntee_codes', criteria.ntee_codes.join(','));
                }
                if (criteria.states?.length) {
                    params.append('states', criteria.states.join(','));
                }
                if (criteria.min_assets) {
                    params.append('min_assets', criteria.min_assets);
                }
                if (criteria.max_assets) {
                    params.append('max_assets', criteria.max_assets);
                }
                if (criteria.min_revenue) {
                    params.append('min_revenue', criteria.min_revenue);
                }
                if (criteria.max_revenue) {
                    params.append('max_revenue', criteria.max_revenue);
                }
                if (criteria.foundation_code) {
                    params.append('foundation_code', criteria.foundation_code);
                }

                const response = await fetch(`/api/v2/discovery/bmf?${params}`);

                if (!response.ok) {
                    throw new Error('BMF discovery failed');
                }

                const data = await response.json();

                if (data.success) {
                    this.discoveryResults = data.organizations || [];
                    this.currentDiscoveryTrack = 'bmf';

                    console.log(`BMF Discovery: ${data.total_count} organizations found`);
                    this.showNotification?.(
                        `Found ${data.total_count} organizations`,
                        'success'
                    );

                    return data;
                } else {
                    throw new Error('BMF discovery failed');
                }

            } catch (error) {
                console.error('BMF discovery failed:', error);
                this.showNotification?.('BMF discovery failed', 'error');
                throw error;
            } finally {
                this.discoveryLoading = false;
            }
        },

        /**
         * Unified search across all sources
         * @param {string} query - Search query
         * @param {Array} tracks - Tracks to search
         */
        async unifiedSearch(query, tracks = ['nonprofit', 'bmf', 'federal']) {
            this.discoveryLoading = true;

            try {
                const response = await fetch('/api/v2/discovery/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query,
                        tracks,
                        filters: this.filterCriteria
                    })
                });

                if (!response.ok) {
                    throw new Error('Search failed');
                }

                const data = await response.json();

                if (data.success) {
                    this.discoveryResults = data.results || [];

                    console.log(`Search complete: ${data.total_results} results`);
                    this.showNotification?.(
                        `Found ${data.total_results} results for "${query}"`,
                        'success'
                    );

                    return data;
                }

            } catch (error) {
                console.error('Search failed:', error);
                this.showNotification?.('Search failed', 'error');
                throw error;
            } finally {
                this.discoveryLoading = false;
            }
        },

        // =================================================================
        // SCREENING OPERATIONS (Tool 10)
        // =================================================================

        /**
         * Screen opportunities using Tool 10 (Opportunity Screening)
         * @param {Array} opportunities - Opportunities to screen
         * @param {string} mode - 'fast' ($0.0004) or 'thorough' ($0.02)
         */
        async screenOpportunities(opportunities = null, mode = null) {
            this.screeningLoading = true;

            try {
                const oppsToScreen = opportunities || this.discoveryResults;
                const screeningMode = mode || this.screeningMode;

                if (!oppsToScreen || oppsToScreen.length === 0) {
                    throw new Error('No opportunities to screen');
                }

                // Use api-helpers.js screenOpportunities function
                // This is already implemented from Phase 9 Week 1
                if (typeof screenOpportunities !== 'function') {
                    throw new Error('Screening function not available');
                }

                const result = await screenOpportunities(oppsToScreen, screeningMode);

                if (result.success) {
                    this.screeningResults = result.data.recommended || [];

                    const cost = result.cost || 0;
                    const screened = result.data.screened || oppsToScreen.length;
                    const recommended = this.screeningResults.length;

                    console.log(
                        `Screening complete: ${screened} screened → ${recommended} recommended ($${cost.toFixed(2)})`
                    );

                    this.showNotification?.(
                        `Screened ${screened} opportunities, ${recommended} recommended`,
                        'success'
                    );

                    return result;
                } else {
                    throw new Error('Screening failed');
                }

            } catch (error) {
                console.error('Screening failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.screeningLoading = false;
            }
        },

        /**
         * Batch screen with fast then thorough modes
         * (Two-stage funnel: 200 → 50 → 10-15)
         */
        async batchScreen() {
            this.screeningLoading = true;

            try {
                // Stage 1: Fast screening (200 → 50)
                console.log('Stage 1: Fast screening...');
                const fastResult = await this.screenOpportunities(
                    this.discoveryResults,
                    'fast'
                );

                const fastCandidates = fastResult.data.recommended || [];

                // Stage 2: Thorough screening (50 → 10-15)
                console.log('Stage 2: Thorough screening...');
                const thoroughResult = await this.screenOpportunities(
                    fastCandidates,
                    'thorough'
                );

                const totalCost = (fastResult.cost || 0) + (thoroughResult.cost || 0);

                console.log(
                    `Batch screening complete: ${this.discoveryResults.length} → ${fastCandidates.length} → ${this.screeningResults.length} (Total: $${totalCost.toFixed(2)})`
                );

                this.showNotification?.(
                    `Batch screening complete: ${this.screeningResults.length} top candidates`,
                    'success'
                );

                return {
                    success: true,
                    fast_results: fastCandidates.length,
                    thorough_results: this.screeningResults.length,
                    total_cost: totalCost
                };

            } catch (error) {
                console.error('Batch screening failed:', error);
                this.showNotification?.('Batch screening failed', 'error');
                throw error;
            } finally {
                this.screeningLoading = false;
            }
        },

        // =================================================================
        // HUMAN GATEWAY (Selection)
        // =================================================================

        /**
         * Select opportunity for deep intelligence
         * @param {Object} opportunity
         */
        selectForIntelligence(opportunity) {
            const index = this.selectedForIntelligence.findIndex(
                o => o.opportunity_id === opportunity.opportunity_id
            );

            if (index > -1) {
                // Deselect
                this.selectedForIntelligence.splice(index, 1);
                delete this.selectionNotes[opportunity.opportunity_id];
            } else {
                // Select
                this.selectedForIntelligence.push(opportunity);
            }

            console.log(`Selected for intelligence: ${this.selectedForIntelligence.length}`);
        },

        /**
         * Check if opportunity is selected
         * @param {Object} opportunity
         */
        isSelected(opportunity) {
            return this.selectedForIntelligence.some(
                o => o.opportunity_id === opportunity.opportunity_id
            );
        },

        /**
         * Add notes to selected opportunity
         * @param {string} opportunityId
         * @param {string} notes
         */
        addSelectionNotes(opportunityId, notes) {
            this.selectionNotes[opportunityId] = notes;
        },

        /**
         * Clear all selections
         */
        clearSelections() {
            this.selectedForIntelligence = [];
            this.selectionNotes = {};
            console.log('Selections cleared');
        },

        /**
         * Proceed to intelligence stage with selected opportunities
         */
        proceedToIntelligence() {
            if (this.selectedForIntelligence.length === 0) {
                this.showNotification?.('Please select at least one opportunity', 'warning');
                return false;
            }

            console.log(`Proceeding to intelligence with ${this.selectedForIntelligence.length} opportunities`);

            // Dispatch event to switch to intelligence stage
            this.$dispatch?.('proceed-to-intelligence', {
                opportunities: this.selectedForIntelligence,
                notes: this.selectionNotes
            });

            // Switch stage
            this.switchStage?.('intelligence');

            return true;
        },

        // =================================================================
        // FILTERS & SORTING
        // =================================================================

        /**
         * Update filter criteria
         * @param {Object} criteria
         */
        updateFilters(criteria) {
            this.filterCriteria = { ...this.filterCriteria, ...criteria };
            console.log('Filters updated:', this.filterCriteria);
        },

        /**
         * Clear all filters
         */
        clearFilters() {
            this.filterCriteria = {
                ntee_codes: [],
                states: [],
                min_assets: null,
                max_assets: null,
                min_revenue: null,
                max_revenue: null,
                foundation_code: null
            };
            console.log('Filters cleared');
        },

        /**
         * Get filtered and sorted results
         */
        get filteredResults() {
            const results = this.screeningResults.length > 0
                ? this.screeningResults
                : this.discoveryResults;

            // Sort results
            return results.sort((a, b) => {
                const aVal = a[this.sortBy] || 0;
                const bVal = b[this.sortBy] || 0;

                if (this.sortOrder === 'asc') {
                    return aVal > bVal ? 1 : -1;
                } else {
                    return aVal < bVal ? 1 : -1;
                }
            });
        },

        /**
         * Change sort
         * @param {string} column
         */
        changeSort(column) {
            if (this.sortBy === column) {
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortBy = column;
                this.sortOrder = 'desc';
            }
        },

        // =================================================================
        // UI HELPERS
        // =================================================================

        /**
         * Open criteria configuration modal
         */
        openCriteriaModal() {
            this.showCriteriaModal = true;
        },

        /**
         * Close criteria modal
         */
        closeCriteriaModal() {
            this.showCriteriaModal = false;
        },

        /**
         * Toggle selection panel
         */
        toggleSelectionPanel() {
            this.showSelectionPanel = !this.showSelectionPanel;
        },

        /**
         * Toggle view mode
         */
        toggleViewMode() {
            this.viewMode = this.viewMode === 'grid' ? 'list' : 'grid';
        },

        /**
         * Calculate estimated screening cost
         */
        getEstimatedCost() {
            const count = this.discoveryResults.length;
            if (this.screeningMode === 'fast') {
                return count * 0.0004;
            } else {
                return count * 0.02;
            }
        },

        /**
         * Get selection summary
         */
        getSelectionSummary() {
            const total = this.selectedForIntelligence.length;
            const withNotes = Object.keys(this.selectionNotes).length;

            return {
                total,
                withNotes,
                ready: total > 0
            };
        },

        /**
         * View opportunity details modal
         * @param {Object} opportunity
         */
        viewOpportunityDetails(opportunity) {
            this.selectedOpportunity = opportunity;
            this.detailsModalTab = 'scores';
            this.showDetailsModal = true;
        },

        /**
         * Close details modal
         */
        closeDetailsModal() {
            this.showDetailsModal = false;
            this.selectedOpportunity = null;
        },

        /**
         * Switch details modal tab
         * @param {string} tab - 'scores', 'details', 'grants', 'website'
         */
        switchDetailsTab(tab) {
            this.detailsModalTab = tab;
        },

        /**
         * Run web research for selected opportunity
         */
        async runWebResearch() {
            if (!this.selectedOpportunity) return;

            try {
                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.ein}/research`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.selectedOpportunity.web_search_complete = true;
                    this.selectedOpportunity.web_data = data.web_data;
                    this.showNotification?.('Web research complete', 'success');
                } else {
                    throw new Error('Web research failed');
                }
            } catch (error) {
                console.error('Web research error:', error);
                this.showNotification?.(error.message, 'error');
            }
        },

        /**
         * Promote opportunity to INTELLIGENCE stage
         */
        async promoteToIntelligence() {
            if (!this.selectedOpportunity) return;

            try {
                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.ein}/promote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: '' })
                });

                if (response.ok) {
                    this.showNotification?.('Promoted to INTELLIGENCE stage', 'success');
                    this.closeDetailsModal();
                    this.$dispatch?.('opportunity-promoted', this.selectedOpportunity);
                } else {
                    throw new Error('Promotion failed');
                }
            } catch (error) {
                console.error('Promotion error:', error);
                this.showNotification?.(error.message, 'error');
            }
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = screeningModule;
}

// CRITICAL: Attach to window for Alpine.js to see it
window.screeningModule = screeningModule;

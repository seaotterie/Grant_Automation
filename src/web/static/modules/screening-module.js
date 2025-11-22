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

        // Selected Profile (updated via event)
        currentProfileId: null,
        selectedProfile: null,

        // Discovery State
        discoveryResults: [],
        discoveryLoading: false,
        currentDiscoveryTrack: 'nonprofit',
        discoverySession: null,
        summaryCounts: {
            total_found: 0,
            qualified: 0,
            review: 0,
            consider: 0,
            low_priority: 0,
            scrapy_completed: 0
        },

        // Discovery Freshness Metadata
        discoveryMetadata: {
            last_discovery_date: null,
            hours_since_discovery: null,
            freshness_status: 'unknown',
            should_refresh: false,
            total_discoveries_run: 0
        },
        freshnessIcon: '⚪',
        freshnessText: 'No discoveries yet',
        freshnessColor: 'gray',

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
        detailsModalTab: 'scores', // 'scores', 'details', 'grants', 'website', 'notes'
        showDiscoveryModal: false,
        discoverySourcesSelected: ['nonprofits'], // Default to nonprofits checked
        showLowPriority: false, // Hide low priority by default
        selectedOpportunities: [], // Track selected opportunities for batch actions
        categoryFilter: null, // Filter by category level (null = show all, 'qualified', 'review', 'consider', 'low_priority')
        webResearchLoading: false, // Web research loading state
        opportunityWebsiteUrl: '', // Website URL for web research

        // URL Discovery State (Phase 5)
        urlDiscoveryInProgress: false,
        excludeLowPriority: true,  // Skip low_priority by default
        urlDiscoveryProgress: {
            total: 0,
            processed: 0,
            found: 0,
            not_found: 0,
            cached: 0,
            discovered: 0,
            elapsed_seconds: 0,
            skipped: 0  // Low priority opportunities skipped
        },
        urlStatistics: {
            total: 0,
            available: 0,
            missing: 0,
            percentage_available: 0,
            by_source: {},
            by_verification: {}
        },
        showUrlStatsModal: false,

        // Discovery Funnel Statistics (Phase 2)
        funnelStatistics: null,
        showFunnelStatsModal: false,

        // Notes State
        opportunityNotes: '',
        notesSaving: false,
        notesSaved: false,
        notesDebounceTimer: null,

        // =================================================================
        // LIFECYCLE & INITIALIZATION
        // =================================================================

        /**
         * Initialize screening module - load saved opportunities if profile exists
         */
        async init() {
            // Try to get profile ID from window global (set by profiles-module.js)
            if (!this.currentProfileId && window.currentProfileId) {
                this.currentProfileId = window.currentProfileId;
            }

            // If we have a profile ID but no profile object, fetch it
            if (this.currentProfileId && !this.selectedProfile) {
                try {
                    const response = await fetch(`/api/v2/profiles/${this.currentProfileId}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.profile) {
                            this.selectedProfile = data.profile;
                            console.log('[Screening] Loaded profile from API:', this.selectedProfile.name);
                        }
                    }
                } catch (error) {
                    console.warn('[Screening] Could not load profile:', error);
                }
            }

            // Load saved opportunities if we have a currentProfileId
            if (this.currentProfileId) {
                console.log('[Screening] init() - Loading saved opportunities for currentProfileId:', this.currentProfileId);
                await this.loadSavedOpportunities(this.currentProfileId);
            } else {
                console.log('[Screening] init() - No currentProfileId, skipping loadSavedOpportunities');
            }

            // Listen for profile selection events from PROFILES tab
            window.addEventListener('profile-selected', async (event) => {
                const newProfile = event.detail;
                console.log('[Screening] Profile selected event received:', newProfile?.name);

                if (newProfile && newProfile.profile_id !== this.currentProfileId) {
                    console.log('[Screening] Switching from profile', this.currentProfileId, 'to', newProfile.profile_id);

                    // Update profile references
                    this.currentProfileId = newProfile.profile_id;
                    this.selectedProfile = newProfile;

                    // Clear old discovery results
                    this.discoveryResults = [];
                    this.summaryCounts = {
                        total_found: 0,
                        qualified: 0,
                        review: 0,
                        consider: 0,
                        low_priority: 0,
                        scrapy_completed: 0
                    };

                    // Load opportunities for new profile
                    await this.loadSavedOpportunities(newProfile.profile_id);

                    console.log('[Screening] Loaded', this.discoveryResults.length, 'saved opportunities for profile', newProfile.name);
                }
            });
        },

        /**
         * Load saved opportunities from database for current profile
         */
        async loadSavedOpportunities(profileId) {
            if (!profileId) {
                console.log('[Screening] loadSavedOpportunities called with no profileId');
                return;
            }

            console.log('[Screening] Loading saved opportunities for profile:', profileId);

            try {
                // Don't filter by stage - load all opportunities for this profile
                // Discovery creates opportunities with stages: qualified_prospects, candidates, prospects
                const url = `/api/v2/profiles/${profileId}/opportunities`;
                console.log('[Screening] Fetching from URL:', url);

                const response = await fetch(url);
                console.log('[Screening] Response status:', response.status, response.statusText);

                // 404 is OK - means no saved opportunities yet
                if (response.status === 404) {
                    console.log('[Screening] No saved opportunities found (404) - this is OK');
                    return;
                }

                if (!response.ok) {
                    console.warn(`[Screening] Failed to load opportunities: ${response.status} ${response.statusText}`);
                    return;
                }

                const data = await response.json();
                console.log('[Screening] Received data:', {
                    status: data.status,
                    opportunityCount: data.opportunities?.length || 0,
                    summary: data.summary,
                    discovery_metadata: data.discovery_metadata
                });

                if (data.status === 'success') {
                    // Update opportunities and summary
                    this.discoveryResults = data.opportunities || [];
                    this.summaryCounts = data.summary || {};

                    // Update freshness metadata
                    this.discoveryMetadata = data.discovery_metadata || {};
                    this.updateFreshnessIndicators();

                    if (data.opportunities?.length > 0) {
                        console.log('[Screening] Setting discoveryResults to', data.opportunities.length, 'opportunities');
                        this.showNotification?.(`Loaded ${data.opportunities.length} opportunities (${this.freshnessText})`, 'info');
                    } else {
                        console.log('[Screening] No opportunities to load (empty array)');
                    }
                } else {
                    console.log('[Screening] Unsuccessful status or no data');
                }

            } catch (error) {
                console.error('[Screening] Failed to load saved opportunities:', error);
                // Don't show error notification - it's normal to have no saved opportunities
            }
        },

        /**
         * Update freshness indicators based on discovery metadata
         */
        updateFreshnessIndicators() {
            const meta = this.discoveryMetadata;

            if (!meta.last_discovery_date) {
                this.freshnessIcon = '⚪';
                this.freshnessText = 'No discoveries yet';
                this.freshnessColor = 'gray';
                return;
            }

            const hours = meta.hours_since_discovery || 0;

            if (meta.freshness_status === 'fresh') {
                this.freshnessIcon = '🟢';
                this.freshnessText = `Fresh (${Math.floor(hours)}h ago)`;
                this.freshnessColor = 'green';
            } else if (meta.freshness_status === 'aging') {
                this.freshnessIcon = '🟡';
                this.freshnessText = `${Math.floor(hours)}h ago`;
                this.freshnessColor = 'yellow';
            } else if (meta.freshness_status === 'stale') {
                this.freshnessIcon = '🔴';
                const days = Math.floor(hours / 24);
                this.freshnessText = days === 0 ? `${Math.floor(hours)}h ago` : `Stale (${days}d ago)`;
                this.freshnessColor = 'red';
            } else {
                this.freshnessIcon = '⚪';
                this.freshnessText = 'Unknown freshness';
                this.freshnessColor = 'gray';
            }

            console.log('[Screening] Freshness updated:', {
                status: meta.freshness_status,
                hours: hours,
                icon: this.freshnessIcon,
                text: this.freshnessText
            });
        },

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

            // Show initial progress message
            this.showNotification?.('🔍 Starting discovery... Searching nonprofits in database', 'info');

            try {
                const requestData = {
                    max_results: options.max_results || 200,
                    auto_scrapy_count: options.auto_scrapy_count || 20,
                    min_score_threshold: options.min_score_threshold || 0.50,  // Lower threshold to show more results (was 0.62)
                    apply_score_filter: options.apply_score_filter !== undefined ? options.apply_score_filter : true,
                    include_funnel_stats: true  // Always include funnel stats for transparency
                };

                const response = await fetch(`/api/v2/profiles/${profileId}/discover`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Discovery failed');
                }

                // Show progress: enriching data
                this.showNotification?.('📊 Enriching with 990 data and calculating scores...', 'info');

                const data = await response.json();

                if (data.status === 'success') {
                    this.discoveryResults = data.opportunities || [];
                    this.summaryCounts = data.summary;

                    // Capture funnel statistics if included (Phase 2)
                    if (data.funnel_statistics) {
                        this.funnelStatistics = data.funnel_statistics;
                        console.log('[FUNNEL_STATS] Captured:', this.funnelStatistics);
                    }

                    this.showNotification?.(
                        `✅ Found ${data.summary.total_found} opportunities (${data.summary.qualified} qualified, ${data.summary.review} for review)`,
                        'success'
                    );

                    // Load URL statistics after discovery
                    await this.loadUrlStatistics();

                    // Reload opportunities to get updated discovery_metadata (freshness info)
                    await this.loadSavedOpportunities(profileId);
                    console.log('[Screening] Reloaded opportunities after discovery to update freshness metadata');

                    // Dispatch event to refresh profiles list (updates Last Discovery column in PROFILES tab)
                    window.dispatchEvent(new CustomEvent('discovery-completed', {
                        detail: { profile_id: profileId }
                    }));
                    console.log('[Screening] Dispatched discovery-completed event');

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
         * Promotes selected opportunities to intelligence stage via API
         */
        async proceedToIntelligence() {
            if (this.selectedForIntelligence.length === 0) {
                this.showNotification?.('Please select at least one opportunity', 'warning');
                return false;
            }

            console.log(`Proceeding to intelligence with ${this.selectedForIntelligence.length} opportunities`);

            // Promote each selected opportunity to intelligence stage
            let promoted = 0;
            let failed = 0;

            for (const opp of this.selectedForIntelligence) {
                try {
                    const notes = this.selectionNotes[opp.opportunity_id] || '';
                    const response = await fetch(`/api/v2/opportunities/${opp.opportunity_id}/promote-with-notes`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            notes: notes,
                            priority_level: 'high',
                            promoted_to: 'intelligence'
                        })
                    });

                    if (response.ok) {
                        promoted++;
                    } else {
                        failed++;
                        console.error(`Failed to promote ${opp.organization_name}`);
                    }
                } catch (error) {
                    failed++;
                    console.error(`Error promoting ${opp.organization_name}:`, error);
                }
            }

            // Show result notification
            if (promoted > 0) {
                this.showNotification?.(
                    `✅ Promoted ${promoted} opportunities to Intelligence stage`,
                    'success'
                );
            }

            if (failed > 0) {
                this.showNotification?.(
                    `⚠️ Failed to promote ${failed} opportunities`,
                    'warning'
                );
            }

            // Clear selections
            this.selectedForIntelligence = [];
            this.selectionNotes = {};

            // Reload opportunities to reflect changes
            if (this.currentProfileId) {
                await this.loadSavedOpportunities(this.currentProfileId);
            }

            // Switch to intelligence stage
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

            // Lock body scroll when modal opens
            document.body.style.overflow = 'hidden';

            // Load notes for this opportunity
            this.opportunityNotes = opportunity.notes || '';
            this.notesSaved = false;
            this.notesSaving = false;
        },

        /**
         * Close details modal
         */
        closeDetailsModal() {
            this.showDetailsModal = false;
            this.selectedOpportunity = null;

            // Restore body scroll when modal closes
            document.body.style.overflow = '';

            // Clear notes state
            this.opportunityNotes = '';
            this.notesSaved = false;
            this.notesSaving = false;

            // Clear any pending debounce timer
            if (this.notesDebounceTimer) {
                clearTimeout(this.notesDebounceTimer);
                this.notesDebounceTimer = null;
            }
        },

        /**
         * Switch details modal tab
         * @param {string} tab - 'scores', 'details', 'grants', 'website'
         */
        switchDetailsTab(tab) {
            this.detailsModalTab = tab;
        },

        /**
         * Run web research for selected opportunity (Tool 25 - Web Intelligence)
         */
        async runWebResearch() {
            if (!this.selectedOpportunity) return;

            this.webResearchLoading = true;
            this.showNotification?.('🕷️ Starting web research with Scrapy (Tool 25)...', 'info');

            try {
                // Prepare request body with optional website URL
                const requestBody = {};
                if (this.opportunityWebsiteUrl && this.opportunityWebsiteUrl.trim()) {
                    requestBody.website_url = this.opportunityWebsiteUrl.trim();
                    console.log('[WEB_RESEARCH] Using user-provided URL:', requestBody.website_url);
                }

                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/research`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                if (response.ok) {
                    const data = await response.json();

                    if (data.success) {
                        // Update opportunity with web data (in selectedOpportunity AND opportunities array)
                        this.selectedOpportunity.web_search_complete = data.web_search_complete;
                        this.selectedOpportunity.web_data = data.web_data;

                        // CRITICAL: Also update the opportunity in the discoveryResults array so results persist
                        if (this.discoveryResults && Array.isArray(this.discoveryResults)) {
                            const oppIndex = this.discoveryResults.findIndex(
                                opp => opp.opportunity_id === this.selectedOpportunity.opportunity_id
                            );
                            if (oppIndex !== -1) {
                                this.discoveryResults[oppIndex].web_search_complete = data.web_search_complete;
                                this.discoveryResults[oppIndex].web_data = data.web_data;
                                console.log('[WEB_RESEARCH] Updated discoveryResults array at index', oppIndex);
                            } else {
                                console.log('[WEB_RESEARCH] Opportunity not found in discoveryResults array, ID:', this.selectedOpportunity.opportunity_id);
                            }
                        } else {
                            console.log('[WEB_RESEARCH] No discoveryResults array available, web data stored in selectedOpportunity only');
                        }

                        // Show success notification with stats
                        const leadershipCount = data.web_data?.leadership?.length || 0;
                        const executionTime = data.execution_time?.toFixed(1) || '?';

                        this.showNotification?.(
                            `✅ Web research complete! Found ${leadershipCount} leadership members (${data.pages_scraped} pages in ${executionTime}s)`,
                            'success'
                        );

                        // Don't auto-switch tabs - let user control navigation
                    } else {
                        // Log full response for debugging
                        console.error('Web research response:', data);
                        throw new Error(`Web research returned no data: ${JSON.stringify(data)}`);
                    }
                } else {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    console.error('Web research HTTP error:', response.status, errorData);
                    throw new Error(errorData.detail || `Web research failed (HTTP ${response.status})`);
                }
            } catch (error) {
                console.error('Web research error:', error);
                this.showNotification?.(
                    `❌ Web research failed: ${error.message}`,
                    'error'
                );
            } finally {
                this.webResearchLoading = false;
            }
        },

        /**
         * Promote opportunity to next category_level or intelligence stage
         */
        async promoteOpportunity() {
            if (!this.selectedOpportunity) return;

            // Validate opportunity_id exists
            if (!this.selectedOpportunity.opportunity_id) {
                console.error('Missing opportunity_id:', this.selectedOpportunity);
                this.showNotification?.(
                    'Cannot promote: This opportunity needs to be re-discovered. Please run Discovery again.',
                    'error'
                );
                return;
            }

            try {
                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/promote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    const data = await response.json();

                    // Update selected opportunity with new state
                    this.selectedOpportunity.category_level = data.new_category;
                    this.selectedOpportunity.current_stage = data.new_stage;

                    // Show success notification
                    this.showNotification?.(data.message, 'success');

                    // If promoted to intelligence stage, close modal and reload
                    if (data.new_stage === 'intelligence') {
                        this.closeDetailsModal();
                        this.$dispatch?.('opportunity-promoted', this.selectedOpportunity);
                        // Reload opportunities to update counts
                        if (this.currentProfileId) {
                            await this.loadSavedOpportunities(this.currentProfileId);
                        }
                    } else {
                        // Just update the display for category level changes
                        // Reload opportunities to update counts
                        if (this.currentProfileId) {
                            await this.loadSavedOpportunities(this.currentProfileId);
                        }
                    }
                } else {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(errorData.detail || 'Promotion failed');
                }
            } catch (error) {
                console.error('Promotion error:', error);
                this.showNotification?.(`❌ Promotion failed: ${error.message}`, 'error');
            }
        },

        /**
         * Demote opportunity to previous category_level
         */
        async demoteOpportunity() {
            if (!this.selectedOpportunity) return;

            // Validate opportunity_id exists
            if (!this.selectedOpportunity.opportunity_id) {
                console.error('Missing opportunity_id:', this.selectedOpportunity);
                this.showNotification?.(
                    'Cannot demote: This opportunity needs to be re-discovered. Please run Discovery again.',
                    'error'
                );
                return;
            }

            // Don't demote if already at low_priority
            if (this.selectedOpportunity.category_level === 'low_priority') {
                this.showNotification?.('⚠️ Cannot demote below low_priority', 'warning');
                return;
            }

            try {
                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/demote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    const data = await response.json();

                    // Update selected opportunity with new state
                    this.selectedOpportunity.category_level = data.new_category;

                    // Show success notification
                    this.showNotification?.(data.message, 'success');

                    // Reload opportunities to update counts
                    if (this.currentProfileId) {
                        await this.loadSavedOpportunities(this.currentProfileId);
                    }
                } else {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(errorData.detail || 'Demotion failed');
                }
            } catch (error) {
                console.error('Demotion error:', error);
                this.showNotification?.(`❌ Demotion failed: ${error.message}`, 'error');
            }
        },

        /**
         * Legacy method - kept for backward compatibility
         */
        async promoteToIntelligence() {
            return this.promoteOpportunity();
        },

        /**
         * Auto-save notes with debouncing (saves 1 second after user stops typing)
         */
        autoSaveNotes() {
            // Clear existing timer
            if (this.notesDebounceTimer) {
                clearTimeout(this.notesDebounceTimer);
            }

            // Reset saved indicator
            this.notesSaved = false;

            // Set new timer to save after 1 second of inactivity
            this.notesDebounceTimer = setTimeout(async () => {
                await this.saveNotesToDatabase();
            }, 1000);
        },

        /**
         * Save notes to database
         */
        async saveNotesToDatabase() {
            if (!this.selectedOpportunity) return;

            this.notesSaving = true;
            this.notesSaved = false;

            try {
                const response = await fetch(`/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/notes`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: this.opportunityNotes })
                });

                if (response.ok) {
                    const data = await response.json();

                    // Update selected opportunity with saved notes
                    this.selectedOpportunity.notes = data.notes;

                    // Show saved indicator
                    this.notesSaved = true;
                    this.notesSaving = false;

                    // Hide saved indicator after 2 seconds
                    setTimeout(() => {
                        this.notesSaved = false;
                    }, 2000);

                    console.log(`Notes saved: ${data.character_count} characters`);
                } else {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(errorData.detail || 'Failed to save notes');
                }
            } catch (error) {
                console.error('Notes save error:', error);
                this.notesSaving = false;
                this.showNotification?.(`❌ Failed to save notes: ${error.message}`, 'error');
            }
        },

        // =================================================================
        // NEW SIMPLIFIED UI HELPERS
        // =================================================================

        /**
         * Get filtered discovery results (by category filter)
         */
        get filteredDiscoveryResults() {
            if (!this.discoveryResults || this.discoveryResults.length === 0) {
                return [];
            }

            let results = this.discoveryResults;

            // Apply category filter if set
            if (this.categoryFilter !== null) {
                results = results.filter(opp => opp.category_level === this.categoryFilter);
            }

            // Sort by current sort criteria
            return this.sortOpportunitiesByField(results, this.sortBy);
        },

        /**
         * Sort opportunities by field
         */
        sortOpportunitiesByField(opportunities, field) {
            const sorted = [...opportunities];

            if (field === 'overall_score') {
                return sorted.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
            } else if (field === 'organization_name') {
                return sorted.sort((a, b) => (a.organization_name || '').localeCompare(b.organization_name || ''));
            } else if (field === 'revenue') {
                return sorted.sort((a, b) => (b.revenue || 0) - (a.revenue || 0));
            }

            return sorted;
        },

        /**
         * Sort discovery results (triggered by dropdown)
         */
        sortDiscoveryResults() {
            // Sorting is handled by computed property filteredDiscoveryResults
            console.log(`Sorting by: ${this.sortBy}`);
        },

        /**
         * Check if opportunity is selected
         */
        isOpportunitySelected(opportunity) {
            return this.selectedOpportunities.some(
                opp => opp.ein === opportunity.ein
            );
        },

        /**
         * Toggle opportunity selection
         */
        toggleOpportunitySelection(opportunity) {
            const index = this.selectedOpportunities.findIndex(
                opp => opp.ein === opportunity.ein
            );

            if (index > -1) {
                // Deselect
                this.selectedOpportunities.splice(index, 1);
            } else {
                // Select
                this.selectedOpportunities.push(opportunity);
            }

            console.log(`Selected opportunities: ${this.selectedOpportunities.length}`);
        },

        /**
         * Promote selected opportunities to INTELLIGENCE tab
         */
        async promoteSelectedOpportunities() {
            if (this.selectedOpportunities.length === 0) {
                this.showNotification?.('Please select at least one opportunity', 'warning');
                return;
            }

            try {
                // Promote each selected opportunity
                const promotePromises = this.selectedOpportunities.map(opp =>
                    fetch(`/api/v2/opportunities/${opp.opportunity_id}/promote`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    })
                );

                const responses = await Promise.all(promotePromises);
                const successful = responses.filter(r => r.ok).length;

                this.showNotification?.(
                    `Successfully promoted ${successful} of ${this.selectedOpportunities.length} opportunities`,
                    'success'
                );

                // Clear selections and reload
                this.selectedOpportunities = [];
                await this.loadSavedOpportunities(this.currentProfileId);

            } catch (error) {
                console.error('Batch promotion error:', error);
                this.showNotification?.(`Failed to promote opportunities: ${error.message}`, 'error');
            }
        },

        // =================================================================
        // URL DISCOVERY FUNCTIONS (Phase 5 - $0.00 Cost)
        // =================================================================

        /**
         * Discover URLs for all opportunities in current profile
         * Cost: $0.00 (pure database queries)
         */
        async discoverAllUrls(forceRefresh = false) {
            if (!this.currentProfileId) {
                this.showNotification?.('No profile selected', 'warning');
                return;
            }

            this.urlDiscoveryInProgress = true;
            this.urlDiscoveryProgress = {
                total: 0,
                processed: 0,
                found: 0,
                not_found: 0,
                cached: 0,
                discovered: 0,
                elapsed_seconds: 0,
                skipped: 0
            };

            try {
                console.log('[URL_DISCOVERY] Starting bulk URL discovery...');

                // Calculate skipped count (low_priority)
                const skippedCount = this.excludeLowPriority ? this.summaryCounts.low_priority : 0;
                const eligibleCount = this.summaryCounts.total_found - skippedCount;

                const skipMsg = this.excludeLowPriority ? ` (skipping ${skippedCount} low priority)` : '';
                this.showNotification?.(`🔍 Discovering URLs for ${eligibleCount} opportunities${skipMsg}... ($0.00)`, 'info');

                const response = await fetch(
                    `/api/v2/profiles/${this.currentProfileId}/discover-urls?force_refresh=${forceRefresh}&exclude_low_priority=${this.excludeLowPriority}`,
                    { method: 'POST' }
                );

                if (!response.ok) {
                    throw new Error(`URL discovery failed: ${response.status}`);
                }

                const data = await response.json();

                // Update progress with final results (reuse skippedCount from above)
                this.urlDiscoveryProgress = {
                    ...data.result,
                    skipped: skippedCount
                };
                this.urlStatistics = data.statistics;

                console.log('[URL_DISCOVERY] Complete:', data.result);

                // Show success notification with X/Y format
                const found = data.result.found;
                const notFound = data.result.not_found;
                const total = data.result.total;
                const time = Math.round(data.result.elapsed_seconds);

                const skipSummary = skippedCount > 0 ? `, ${skippedCount} skipped` : '';
                this.showNotification?.(
                    `✅ Searched ${total} opportunities: ${found} URLs found, ${notFound} missing${skipSummary} (${time}s, $0.00)`,
                    'success'
                );

                // Reload opportunities to show URLs
                await this.loadSavedOpportunities(this.currentProfileId);

            } catch (error) {
                console.error('[URL_DISCOVERY] Error:', error);
                this.showNotification?.(`URL discovery failed: ${error.message}`, 'error');
            } finally {
                this.urlDiscoveryInProgress = false;
            }
        },

        /**
         * Load URL statistics for current profile
         */
        async loadUrlStatistics() {
            if (!this.currentProfileId) return;

            try {
                const response = await fetch(`/api/v2/profiles/${this.currentProfileId}/url-statistics`);
                if (response.ok) {
                    const data = await response.json();
                    this.urlStatistics = data.statistics;
                    console.log('[URL_STATS] Loaded:', this.urlStatistics);
                }
            } catch (error) {
                console.error('[URL_STATS] Error loading statistics:', error);
            }
        },

        /**
         * Get computed URL discovery percentage
         */
        get urlDiscoveryPercent() {
            if (this.urlDiscoveryProgress.total === 0) return 0;
            return Math.round((this.urlDiscoveryProgress.processed / this.urlDiscoveryProgress.total) * 100);
        },

        /**
         * Get eligible opportunity count for URL discovery (excludes low_priority if filter enabled)
         */
        get urlDiscoveryEligibleCount() {
            const skipped = this.excludeLowPriority ? this.summaryCounts.low_priority : 0;
            return this.summaryCounts.total_found - skipped;
        },

        /**
         * Show URL statistics modal
         */
        showUrlStatisticsModal() {
            this.showUrlStatsModal = true;
        },

        /**
         * Show funnel statistics modal
         */
        showFunnelStatisticsModal() {
            this.showFunnelStatsModal = true;
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = screeningModule;
}

// CRITICAL: Attach to window for Alpine.js to see it
window.screeningModule = screeningModule;

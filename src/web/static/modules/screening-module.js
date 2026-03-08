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
        detailsModalTab: 'scores', // 'scores', 'details', 'grants', 'officers', 'notes'
        showDiscoveryModal: false,
        discoverySourcesSelected: ['nonprofits'], // Default to nonprofits checked
        showLowPriority: false, // Hide low priority by default
        selectedOpportunities: [], // Track selected opportunities for batch actions
        categoryFilter: null, // Filter by category level (null = show all, 'qualified', 'review', 'consider', 'low_priority')
        webResearchLoading: false, // Web research loading state
        opportunityWebsiteUrl: '', // Website URL for web research

        // 990 Filing History state
        filingHistoryOpen: false,
        filingHistoryLoading: false,
        filingHistoryData: null,
        filingAnalysisLoading: false,
        filingAnalysisResult: null,
        filingAnalysisPdfUrl: null,

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

        // 990 Batch Analysis State
        ninetiesSearchInProgress: false,
        ninetiesSearchProgress: {
            total: 0,
            processed: 0,
            found: 0,
            failed: 0,
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

        // Session Cost Tracking
        sessionApiCost: 0,

        // Plan Screening Filter — batch size limiter
        // Selects top N unprocessed opportunities by score for AI pipeline
        planFilterEnabled: true,
        planFilterBatchSize: 10,        // 10, 25, 50, 100, or custom
        planFilterBatchSizes: [10, 25, 50, 100],
        planFilterCustomSize: null,

        // Batch Screen State
        batchScreenJobId: null,
        batchScreenStatus: null,   // null | 'running' | 'complete' | 'failed'
        batchScreenProgress: 0,
        batchScreenTotal: 0,
        batchScreenMode: 'fast',
        batchScreenThreshold: 0.50,
        batchScreenResults: [],
        batchScreenAboveThreshold: 0,
        batchScreenEstimatedCost: 0,
        batchScreenPollTimer: null,

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
        // PLAN SCREENING FILTER — Top-N Batch Selection
        // =================================================================

        /**
         * Get the effective batch size (custom or preset).
         */
        getEffectiveBatchSize() {
            return this.planFilterCustomSize || this.planFilterBatchSize;
        },

        /**
         * Set batch size from preset buttons.
         */
        setPlanFilterBatchSize(size) {
            this.planFilterBatchSize = size;
            this.planFilterCustomSize = null;
        },

        /**
         * Check if an opportunity has been processed for a specific pipeline step.
         * Each step has its own independent completion indicator.
         */
        _isProcessedFor(opp, step) {
            switch (step) {
                case 'urls':    return !!(opp.filing_history_loaded);
                case 'web':     return !!(opp.web_search_complete && opp.web_data);
                case '990s':    return !!(opp.pdf_analyzed);
                case 'fast':    return opp.tool1_score != null;
                case 'thorough': return opp.tool1_score?.mode === 'thorough';
                default:        return opp.tool1_score != null;
            }
        },

        /**
         * Get opportunities sorted by score descending.
         * Excludes low_priority if showLowPriority is false.
         */
        _getSortedByScore() {
            let opps = [...this.discoveryResults];

            // Respect the existing low-priority filter
            if (!this.showLowPriority) {
                opps = opps.filter(opp => {
                    const score = opp.overall_score || 0;
                    return score >= 0.50;
                });
            }

            // Sort by overall_score descending
            opps.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
            return opps;
        },

        /**
         * Get the next batch of unprocessed opportunities for a specific pipeline step.
         * Each step has its own independent processed check so batches don't interfere.
         * @param {string} step - 'urls' | 'web' | '990s' | 'fast' | 'thorough'
         */
        getNextBatchFor(step) {
            const batchSize = this.getEffectiveBatchSize();
            const sorted = this._getSortedByScore();
            const unprocessed = sorted.filter(opp => !this._isProcessedFor(opp, step));

            const batch = unprocessed.slice(0, batchSize);
            const processedCount = sorted.length - unprocessed.length;
            const batchNumber = Math.floor(processedCount / batchSize) + 1;

            return {
                opportunities: batch,
                ids: batch.map(opp => opp.opportunity_id).filter(Boolean),
                batchNumber: batchNumber,
                batchSize: batchSize,
                totalUnprocessed: unprocessed.length,
                totalProcessed: processedCount,
                totalEligible: sorted.length,
                scoreRange: batch.length > 0
                    ? { high: batch[0].overall_score || 0, low: batch[batch.length - 1].overall_score || 0 }
                    : { high: 0, low: 0 }
            };
        },

        /** Backward-compat alias — defaults to 'fast' step. */
        getNextBatch() {
            return this.getNextBatchFor('fast');
        },

        /**
         * Get IDs for a specific pipeline step's batch.
         * When plan filter is enabled, returns only the top-N unprocessed for that step.
         * When disabled, returns all IDs.
         * @param {string} step - 'urls' | 'web' | '990s' | 'fast' | 'thorough'
         */
        getAIPipelineTargetIds(step = 'fast') {
            if (!this.planFilterEnabled) {
                return this.discoveryResults
                    .map(opp => opp.opportunity_id)
                    .filter(Boolean);
            }
            return this.getNextBatchFor(step).ids;
        },

        /**
         * Get estimated cost for the current batch across pipeline steps.
         */
        getPlanFilterEstimatedCost() {
            const batch = this.getNextBatch();
            const count = batch.opportunities.length;
            const screenCost = this.batchScreenMode === 'fast' ? 0.001 : 0.01;
            return {
                urlSearch: 0,                           // Free
                pdfAnalysis: count * 0.02,             // ~$0.02 per PDF
                aiScreen: count * screenCost,           // $0.001 or $0.01 per opp
                total: (count * 0.02) + (count * screenCost)
            };
        },

        // =================================================================
        // BATCH SCREENING (Screen All Unscreened)
        // =================================================================

        /**
         * Count unscreened opportunities (for button display when filter is off).
         */
        _getUnscreenedCount() {
            return this.discoveryResults.filter(opp => !opp.tool1_score).length;
        },

        /**
         * Return the IDs of opportunities to screen in the next batch.
         * Uses per-step independent batch logic so fast/thorough batches don't share a counter.
         */
        _getUnscreenedIds() {
            const step = this.batchScreenMode === 'thorough' ? 'thorough' : 'fast';
            if (this.planFilterEnabled) {
                return this.getNextBatchFor(step).ids;
            }
            return this.discoveryResults
                .filter(opp => !opp.tool1_score)
                .map(opp => opp.opportunity_id)
                .filter(Boolean);
        },

        /**
         * Return Tool 1 score for an opportunity (from analysis_discovery or local cache).
         */
        getAnalysisStatus(opp) {
            return {
                scored: opp.tool1_score != null,
                web: !!(opp.web_search_complete && opp.web_data),
                filing: !!(opp.filing_history_loaded),
                pdf: !!(opp.pdf_analyzed),
            };
        },

        async screenAllFast() {
            this.batchScreenMode = 'fast';
            await this.screenAllUnscreened();
        },

        async screenAllThorough() {
            this.batchScreenMode = 'thorough';
            await this.screenAllUnscreened();
        },

        /**
         * Start a batch Tool 1 screening job for all unscreened opportunities.
         */
        async screenAllUnscreened() {
            const ids = this._getUnscreenedIds();
            if (ids.length === 0) {
                const msg = this.planFilterEnabled
                    ? `All opportunities in batch ${this.getNextBatch().batchNumber} already have Tool 1 scores`
                    : 'All opportunities already have Tool 1 scores';
                this.showNotification?.(msg, 'info');
                return;
            }

            const costPerOpp = this.batchScreenMode === 'fast' ? 0.001 : 0.01;
            const estimatedCost = (ids.length * costPerOpp).toFixed(2);
            const batchLabel = this.planFilterEnabled
                ? ` (Top ${this.getEffectiveBatchSize()} unscreened by score)`
                : '';

            if (!confirm(`Screen ${ids.length} opportunities${batchLabel} in ${this.batchScreenMode} mode?\n\nEstimated cost: $${estimatedCost}\n\nProceed?`)) {
                return;
            }

            this.batchScreenStatus = 'running';
            this.batchScreenProgress = 0;
            this.batchScreenTotal = ids.length;
            this.batchScreenEstimatedCost = parseFloat(estimatedCost);
            this.batchScreenJobId = null;
            this.batchScreenResults = [];

            try {
                const response = await fetch('/api/v2/opportunities/batch-screen', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        profile_id: this.currentProfileId,
                        opportunity_ids: ids,
                        mode: this.batchScreenMode,
                        threshold: this.batchScreenThreshold,
                    }),
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(err.detail || `HTTP ${response.status}`);
                }

                const data = await response.json();
                this.batchScreenJobId = data.job_id;
                this.showNotification?.(`Batch screening started (${ids.length} opportunities, $${estimatedCost} est.)`, 'info');

                // Poll for completion
                this._pollBatchScreenStatus();

            } catch (error) {
                console.error('Batch screen start error:', error);
                this.batchScreenStatus = 'failed';
                this.showNotification?.(`❌ Batch screen failed: ${error.message}`, 'error');
            }
        },

        /**
         * Poll batch screen job status every 2 seconds.
         */
        _pollBatchScreenStatus() {
            if (this.batchScreenPollTimer) clearInterval(this.batchScreenPollTimer);

            this.batchScreenPollTimer = setInterval(async () => {
                if (!this.batchScreenJobId) return;
                try {
                    const response = await fetch(`/api/v2/opportunities/batch-screen/${this.batchScreenJobId}`);
                    if (!response.ok) return;
                    const job = await response.json();

                    this.batchScreenProgress = job.processed || job.progress || 0;
                    this.batchScreenTotal = job.total || this.batchScreenTotal;

                    if (job.status === 'complete') {
                        clearInterval(this.batchScreenPollTimer);
                        this.batchScreenPollTimer = null;
                        this.batchScreenStatus = 'complete';
                        this.batchScreenResults = job.results || [];
                        this.batchScreenAboveThreshold = (job.above_threshold || []).length;
                        // Track session cost from actual batch screen cost
                        this.sessionApiCost += job.estimated_cost || 0;

                        this.showNotification?.(
                            `✅ Batch screening complete: ${this.batchScreenResults.length} screened, ` +
                            `${this.batchScreenAboveThreshold} above ${Math.round(this.batchScreenThreshold * 100)}% threshold`,
                            'success'
                        );

                        // Refresh opportunity table so tool1_score values appear
                        if (this.currentProfileId) {
                            await this.loadSavedOpportunities(this.currentProfileId);
                        }
                    } else if (job.status === 'failed') {
                        clearInterval(this.batchScreenPollTimer);
                        this.batchScreenPollTimer = null;
                        this.batchScreenStatus = 'failed';
                        this.showNotification?.(`❌ Batch screen failed: ${job.error || 'Unknown error'}`, 'error');
                    }
                } catch (e) {
                    console.warn('Batch screen poll error:', e);
                }
            }, 2000);
        },

        /**
         * Filter discovery results to only show opportunities above the batch screen threshold.
         */
        applyRecommendedFilters() {
            const threshold = this.batchScreenThreshold;
            const total = this.discoveryResults.length;
            // Only filter on Tool 1 AI score — do not fall back to algorithmic score
            const screened = this.discoveryResults.filter(opp => opp.tool1_score != null);
            if (screened.length === 0) {
                this.showNotification?.('No AI screening scores found — run "Screen All" first, then reload the page', 'warning');
                return;
            }
            const above = screened.filter(opp => (opp.tool1_score?.overall_score ?? 0) >= threshold);
            if (above.length === 0) {
                this.showNotification?.(
                    `All ${screened.length} screened opportunities scored below ${Math.round(threshold * 100)}% — try lowering the threshold`,
                    'warning'
                );
                return;
            }
            this.discoveryResults = above;
            this.summaryCounts = { ...this.summaryCounts, total_found: above.length };
            this.showNotification?.(
                `Showing ${above.length} of ${total} opportunities with AI score ≥ ${Math.round(threshold * 100)}%`,
                'success'
            );
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

            // Reset filing history state for new opportunity
            this.filingHistoryOpen = false;
            this.filingHistoryLoading = false;
            this.filingHistoryData = null;
            this.filingAnalysisLoading = false;
            this.filingAnalysisResult = null;
            this.filingAnalysisPdfUrl = null;
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
         * @param {string} tab - 'scores', 'details', 'grants', 'officers', 'notes'
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
                        const wd = data.web_data || {};
                        const executionTime = data.execution_time?.toFixed(1) || '?';
                        const parts = [];
                        const leadershipCount = wd.leadership?.length || 0;
                        const programCount = wd.programs?.length || 0;
                        const factCount = wd.key_facts?.length || 0;
                        if (leadershipCount > 0) parts.push(`${leadershipCount} leader${leadershipCount > 1 ? 's' : ''}`);
                        if (programCount > 0) parts.push(`${programCount} program${programCount > 1 ? 's' : ''}`);
                        if (factCount > 0) parts.push(`${factCount} key facts`);
                        if (wd.mission) parts.push('mission');
                        if ((wd.contact?.email || wd.contact?.phone)) parts.push('contact');
                        const aiLabel = wd.ai_interpreted ? ' (AI interpreted)' : '';
                        const summary = parts.length > 0 ? parts.join(', ') : 'website & contact';

                        // Track session cost (~$0.02 per web research run)
                        if (!data.cache_hit) this.sessionApiCost += 0.02;

                        this.showNotification?.(
                            `✅ Web research complete${aiLabel}: ${summary} — ${data.pages_scraped} pages in ${executionTime}s`,
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
         * Load 990 filing history with PDF links for selected opportunity
         */
        async load990Filings() {
            if (!this.selectedOpportunity) return;
            this.filingHistoryLoading = true;
            this.filingHistoryData = null;
            this.filingAnalysisResult = null;
            this.filingAnalysisPdfUrl = null;
            try {
                const response = await fetch(
                    `/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/990-filings`
                );
                if (response.ok) {
                    const data = await response.json();
                    this.filingHistoryData = data.filings || [];
                } else {
                    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    this.showNotification?.(`Failed to load filing history: ${err.detail}`, 'error');
                }
            } catch (error) {
                console.error('Filing history error:', error);
                this.showNotification?.(`Filing history error: ${error.message}`, 'error');
            } finally {
                this.filingHistoryLoading = false;
            }
        },

        /**
         * Send a 990 PDF to Claude for grant-intelligence extraction
         */
        async analyze990PDF(pdfUrl, taxYear) {
            if (!this.selectedOpportunity || !pdfUrl) return;
            this.filingAnalysisLoading = true;
            this.filingAnalysisResult = null;
            this.filingAnalysisPdfUrl = pdfUrl;
            try {
                const response = await fetch(
                    `/api/v2/opportunities/${this.selectedOpportunity.opportunity_id}/analyze-990-pdf`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pdf_url: pdfUrl, tax_year: taxYear })
                    }
                );
                if (response.ok) {
                    const data = await response.json();
                    this.filingAnalysisResult = data.extraction;
                    // Track session cost (~$0.02 per PDF analysis)
                    if (!data.cache_hit) this.sessionApiCost += 0.02;
                    this.showNotification?.('990 PDF analysis complete', 'success');
                } else {
                    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    this.showNotification?.(`PDF analysis failed: ${err.detail}`, 'error');
                }
            } catch (error) {
                console.error('990 PDF analysis error:', error);
                this.showNotification?.(`PDF analysis error: ${error.message}`, 'error');
            } finally {
                this.filingAnalysisLoading = false;
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
         * Batch analyze 990 PDFs for all opportunities in current profile.
         * Uses most recent filing from cached filing_history (run Find URLs first).
         * Cost: ~$0.01-0.03 per PDF (Claude Haiku), cached per EIN.
         */
        async batchAnalyze990Pdfs() {
            if (!this.currentProfileId) {
                this.showNotification?.('No profile selected', 'warning');
                return;
            }

            const ids = this.getAIPipelineTargetIds('990s');

            if (ids.length === 0) {
                this.showNotification?.('No opportunities to analyze', 'warning');
                return;
            }

            const batchLabel = this.planFilterEnabled ? ` (Top ${this.getEffectiveBatchSize()} unanalyzed)` : '';
            const estimatedCost = (ids.length * 0.02).toFixed(2);
            if (!confirm(`Analyze 990 PDFs for ${ids.length} opportunities${batchLabel}?\n\nEstimated cost: ~$${estimatedCost} (Claude Haiku, cached per EIN)\nRequires filing history — run Search Website (①) first if not done.\n\nProceed?`)) {
                return;
            }

            this.ninetiesSearchInProgress = true;
            this.ninetiesSearchProgress = { total: ids.length, processed: 0, found: 0, failed: 0 };
            this.showNotification?.(`Starting 990 PDF analysis for ${ids.length} organizations...`, 'info');

            try {
                const response = await fetch('/api/v2/opportunities/batch-analyze-990-pdfs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        opportunity_ids: ids,
                        force_refresh: false,
                    }),
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    throw new Error(err.detail || `HTTP ${response.status}`);
                }

                const data = await response.json();

                this.ninetiesSearchProgress = {
                    total: data.total || ids.length,
                    processed: data.analyzed + data.skipped + data.errors,
                    found: data.analyzed || 0,
                    failed: data.errors || 0,
                };

                // Track session API cost
                this.sessionApiCost += data.estimated_cost_usd || 0;

                this.showNotification?.(
                    `✅ 990 analysis complete: ${data.analyzed} analyzed (${data.cached} cached), ` +
                    `${data.skipped} skipped (no PDF), ${data.errors} errors`,
                    'success'
                );

                console.log('[990_BATCH] Results:', data);

            } catch (error) {
                console.error('[990_BATCH] Error:', error);
                this.showNotification?.(`990 batch analysis failed: ${error.message}`, 'error');
            } finally {
                this.ninetiesSearchInProgress = false;
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

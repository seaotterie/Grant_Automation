/**
 * Intelligence Analysis Module
 * Deep analysis using Tool 2, reports, export, and packages
 *
 * Replaces: EXAMINE and APPROACH stages (2 → 1 stage)
 * Tools Used: Tool 2 (Deep Intelligence), Tool 18 (Export), Tool 19 (Package), Tool 21 (Report)
 */

function intelligenceModule() {
    return {
        // =================================================================
        // STATE
        // =================================================================

        // Profile State
        currentProfileId: null,  // Store profile ID for API calls

        // Opportunities State
        selectedOpportunities: [],
        selectionNotes: {},

        // Intelligence Results
        intelligenceResults: {},
        analysisProgress: {},

        // Analysis Configuration - 2-Tier System (Updated Oct 2025)
        selectedDepth: 'essentials',
        depths: [
            {
                id: 'essentials',
                name: 'ESSENTIALS',
                price: 2.00,
                time: '15-20 min',
                description: '4-stage AI + network intelligence + historical analysis',
                features: [
                    '4-Stage AI Analysis',
                    'Network Intelligence (board profiling, connections)',
                    'Historical Funding Analysis (5 years)',
                    'Geographic & Competitive Analysis',
                    'Risk Assessment & Strategic Recommendations'
                ]
            },
            {
                id: 'premium',
                name: 'PREMIUM',
                price: 8.00,
                time: '30-40 min',
                description: '+ Enhanced pathways + policy analysis + comprehensive dossier',
                features: [
                    'Everything in ESSENTIALS',
                    'Enhanced Network Pathways (warm introductions)',
                    'Decision Maker Profiling & Engagement',
                    'Policy Analysis (federal + state)',
                    'Strategic Consulting Insights',
                    'Comprehensive Dossier (20+ pages)'
                ]
            }
        ],

        // Export & Reporting
        selectedReportTemplate: 'comprehensive',
        reportTemplates: [
            { id: 'comprehensive', name: 'Comprehensive Report', pages: '20-30' },
            { id: 'executive', name: 'Executive Summary', pages: '5-10' },
            { id: 'risk', name: 'Risk Assessment', pages: '10-15' },
            { id: 'implementation', name: 'Implementation Plan', pages: '15-20' }
        ],

        // UI State
        currentOpportunityIndex: 0,
        showDepthSelector: false,
        showReportModal: false,
        showExportModal: false,
        showIntelligenceModal: false,       // Intelligence View Details modal
        selectedIntelligenceOpp: null,      // Currently viewed opportunity in modal
        intelligenceModalTab: 'scores',     // Active tab in modal
        intelligenceModalIndex: -1,         // Current position in selectedOpportunities list

        // Selection State (for checkboxes)
        selectedOpportunitiesForBatch: [],  // Track checkbox selections

        // Filter/Sort State for INTELLIGENCE table
        intelligenceCategoryFilter: null,   // null = all, 'qualified', 'review', 'consider', 'low_priority'
        intelligenceSortBy: 'composite_score',  // 'composite_score' | 'organization_name' | 'revenue'

        // Loading States
        analyzing: false,
        generating: false,
        exporting: false,

        // Per-opp action loading flags (modal action row)
        intelFindUrlsLoading: false,
        intelWebSearchLoading: false,
        intel990sLoading: false,
        intelScreenFastLoading: false,
        intelScreenThoroughLoading: false,
        intelEssentialsLoading: false,
        intelPremiumLoading: false,
        intelConnectionsLoading: false,
        intelNetworkingLoading: false,

        // Network Graph State
        networkGraphStats: null,
        networkBuildLoading: false,
        networkRankLoading: false,
        networkRankedFunders: [],
        networkFindUrlsLoading: false,
        network990Loading: false,
        networkXmlLookupLoading: false,

        // =================================================================
        // LIFECYCLE
        // =================================================================

        /**
         * Initialize intelligence module with selected opportunities
         * @param {Array} opportunities
         * @param {Object} notes
         * @param {number} profileId - Optional profile ID to load intelligence opportunities from database
         */
        async init(opportunities, notes = {}, profileId = null) {
            // Store profile ID for API calls
            this.currentProfileId = profileId;

            // If opportunities are provided, use them (manual workflow)
            if (opportunities && opportunities.length > 0) {
                this.selectedOpportunities = opportunities;
                this.selectionNotes = notes || {};
            }
            // Otherwise, load from database if profileId provided (automatic workflow)
            else if (profileId) {
                await this.loadIntelligenceOpportunities(profileId);
            }

            // Auto-select first opportunity
            if (this.selectedOpportunities.length > 0) {
                this.currentOpportunityIndex = 0;
            }
        },

        /**
         * Load opportunities from database that are in Intelligence stage
         * @param {number} profileId - Profile ID to load opportunities for
         */
        async loadIntelligenceOpportunities(profileId) {
            try {
                console.log(`Loading intelligence opportunities for profile ${profileId}`);

                const response = await fetch(`/api/v2/profiles/${profileId}/opportunities?stage=intelligence`);

                if (!response.ok) {
                    throw new Error(`Failed to load intelligence opportunities: ${response.statusText}`);
                }

                const data = await response.json();

                this.selectedOpportunities = data.opportunities || [];

                // Restore persisted AI results so the Summary/Analysis tabs render
                // and Essentials/Premium don't re-bill on reload.
                for (const opp of this.selectedOpportunities) {
                    const oppId = opp.opportunity_id || opp.id;
                    const hasEssentials = opp.essentials_result;
                    const hasPremium    = opp.premium_result;
                    const hasConnections = opp.connection_analysis;

                    if (hasEssentials || hasPremium || hasConnections) {
                        if (!this.intelligenceResults[oppId]) {
                            this.intelligenceResults[oppId] = { opportunity: opp };
                        }
                        if (hasEssentials) {
                            this.intelligenceResults[oppId].analysis  = opp.essentials_result;
                            this.intelligenceResults[oppId].depth     = 'essentials';
                            this.intelligenceResults[oppId].cost      = opp.essentials_result?.user_price || 2.00;
                        }
                        if (hasPremium) {
                            this.intelligenceResults[oppId].analysis  = opp.premium_result;
                            this.intelligenceResults[oppId].depth     = 'premium';
                            this.intelligenceResults[oppId].cost      = opp.premium_result?.user_price || 8.00;
                        }
                        if (hasConnections) {
                            this.intelligenceResults[oppId].connections = opp.connection_analysis;
                        }
                        if (opp.networking_result) {
                            this.intelligenceResults[oppId].networking = {
                                success: true,
                                ...opp.networking_result,
                            };
                        }
                    }
                }

                console.log(`Loaded ${this.selectedOpportunities.length} intelligence opportunities`);

                // Load network graph stats (free, $0)
                this.networkLoadStats(profileId).catch(() => {});

                if (this.selectedOpportunities.length === 0) {
                    this.showNotification?.(
                        'No opportunities in Intelligence stage yet. Qualify opportunities in SCREENING tab first.',
                        'info'
                    );
                }

                return this.selectedOpportunities;

            } catch (error) {
                console.error('Failed to load intelligence opportunities:', error);
                this.showNotification?.(
                    `Failed to load opportunities: ${error.message}`,
                    'error'
                );
                this.selectedOpportunities = [];
                return [];
            }
        },

        // =================================================================
        // MODAL & SELECTION OPERATIONS
        // =================================================================

        /**
         * Open Intelligence View Details modal for an opportunity
         * @param {string} opportunityId - Opportunity ID to view
         */
        openIntelligenceModal(opportunityId) {
            // Find the opportunity in selected opportunities
            const idx = this.selectedOpportunities.findIndex(
                o => o.opportunity_id === opportunityId || o.id === opportunityId
            );

            if (idx < 0) {
                console.error('Opportunity not found:', opportunityId);
                return;
            }

            const opp = this.selectedOpportunities[idx];
            this.selectedIntelligenceOpp = opp;
            this.intelligenceModalIndex = idx;
            this.intelligenceModalTab = 'scores';  // Reset to Score Breakdown tab
            this.showIntelligenceModal = true;

            // Reset action loading flags
            this.intelFindUrlsLoading = false;
            this.intelWebSearchLoading = false;
            this.intel990sLoading = false;
            this.intelScreenFastLoading = false;
            this.intelScreenThoroughLoading = false;
            this.intelEssentialsLoading = false;
            this.intelPremiumLoading = false;

            console.log('Opened intelligence modal for:', opp.organization_name);
            console.log('[Intelligence Modal] Full opportunity data:', opp);
            console.log('[Intelligence Modal] Data structure check:', {
                has_990_data: !!opp['990_data'],
                has_grant_history: !!opp.grant_history,
                has_dimensional_scores: !!opp.dimensional_scores,
                has_web_data: !!opp.web_data,
                revenue: opp.revenue,
                assets: opp.assets
            });
            console.log('[Intelligence Modal] Top-level fields:', Object.keys(opp));
            if (opp['990_data']) {
                console.log('[Intelligence Modal] 990_data keys:', Object.keys(opp['990_data']));
            }
            if (opp.grant_history) {
                console.log('[Intelligence Modal] grant_history length:', opp.grant_history.length);
            }
            if (opp.dimensional_scores) {
                console.log('[Intelligence Modal] dimensional_scores:', opp.dimensional_scores);
            }
            if (opp.web_data) {
                console.log('[Intelligence Modal] web_data keys:', Object.keys(opp.web_data));
            }
        },

        /**
         * Close Intelligence View Details modal
         */
        closeIntelligenceModal() {
            this.showIntelligenceModal = false;
            this.selectedIntelligenceOpp = null;
            this.intelligenceModalIndex = -1;
        },

        /**
         * Navigate to prev/next opportunity in Intelligence modal
         * @param {number} direction - -1 for prev, +1 for next
         */
        navigateIntelligenceModal(direction) {
            const newIndex = this.intelligenceModalIndex + direction;
            if (newIndex < 0 || newIndex >= this.selectedOpportunities.length) return;
            this.intelligenceModalIndex = newIndex;
            const opp = this.selectedOpportunities[newIndex];
            this.openIntelligenceModal(opp.opportunity_id || opp.id);
        },

        /**
         * Switch tabs in Intelligence modal
         * @param {string} tab - Tab name (scores, details, grants, officers, notes, summary, analysis)
         */
        switchIntelligenceTab(tab) {
            this.intelligenceModalTab = tab;
        },

        // =================================================================
        // MODAL ACTION ROW FUNCTIONS
        // =================================================================

        /**
         * ① Find URLs — fetch 990 filing history for the current intelligence modal opportunity
         */
        async intelFindUrls() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp?.opportunity_id) return;
            const oppId = opp.opportunity_id;
            this.intelFindUrlsLoading = true;
            try {
                const resp = await fetch(`/api/v2/opportunities/${oppId}/990-filings`);
                if (resp.ok) {
                    const data = await resp.json();
                    const filings = data.filings || [];
                    this.selectedIntelligenceOpp = { ...opp, filing_history: filings };
                    const idx = this.selectedOpportunities.findIndex(o => o.opportunity_id === oppId);
                    if (idx >= 0) this.selectedOpportunities[idx] = { ...this.selectedOpportunities[idx], filing_history: filings };
                    this.showNotification?.('Find URLs', `Found ${filings.length} filings`, 'success');
                } else {
                    const err = await resp.json().catch(() => ({}));
                    this.showNotification?.('Find URLs', err.detail || 'Failed to load filing history', 'error');
                }
            } catch (e) {
                console.error('intelFindUrls error:', e);
                this.showNotification?.('Find URLs', 'Network error', 'error');
            } finally {
                this.intelFindUrlsLoading = false;
            }
        },

        /**
         * ② Search Website — run Haiku web intelligence for the current intelligence modal opportunity
         */
        async intelSearchWebsite() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp?.opportunity_id) return;
            const oppId = opp.opportunity_id;
            this.intelWebSearchLoading = true;
            try {
                const resp = await fetch(`/api/v2/opportunities/${oppId}/research`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                if (resp.ok) {
                    const data = await resp.json();
                    // No-URL short-circuit
                    if (!data.success && data.reason === 'no_url_found') {
                        this.showNotification?.('Search Website', `No website URL found for ${opp.organization_name}. Try entering a URL manually.`, 'warning');
                    } else if (data.web_data) {
                        this.selectedIntelligenceOpp = { ...opp, web_data: data.web_data, web_search_complete: true };
                        const idx = this.selectedOpportunities.findIndex(o => o.opportunity_id === oppId);
                        if (idx >= 0) this.selectedOpportunities[idx] = { ...this.selectedOpportunities[idx], web_data: data.web_data, web_search_complete: true };
                    }
                    if (data.success) this.showNotification?.('Search Website', 'Web intelligence gathered successfully', 'success');
                } else {
                    const err = await resp.json().catch(() => ({}));
                    this.showNotification?.('Search Website', err.detail || 'Web research failed', 'error');
                }
            } catch (e) {
                console.error('intelSearchWebsite error:', e);
                this.showNotification?.('Search Website', 'Network error', 'error');
            } finally {
                this.intelWebSearchLoading = false;
            }
        },

        /**
         * ③ Search 990s — extract grant intelligence from the most recent 990 PDF
         */
        async intelSearch990s() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp?.opportunity_id) return;
            const oppId = opp.opportunity_id;
            const filings = opp.filing_history || [];
            const filing = filings.find(f => f.pdf_url);
            if (!filing) {
                this.showNotification?.('Search 990s', 'Run Find URLs first to get a 990 PDF link', 'warning');
                return;
            }
            this.intel990sLoading = true;
            try {
                const resp = await fetch(`/api/v2/opportunities/${oppId}/analyze-990-pdf`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pdf_url: filing.pdf_url, tax_year: filing.tax_year || null })
                });
                if (resp.ok) {
                    const data = await resp.json();
                    const updates = { pdf_analyzed: true };
                    if (data.extraction) updates.pdf_extraction = data.extraction;
                    this.selectedIntelligenceOpp = { ...opp, ...updates };
                    const idx = this.selectedOpportunities.findIndex(o => o.opportunity_id === oppId);
                    if (idx >= 0) this.selectedOpportunities[idx] = { ...this.selectedOpportunities[idx], ...updates };
                    this.showNotification?.('Search 990s', 'PDF extraction complete', 'success');
                } else {
                    const err = await resp.json().catch(() => ({}));
                    this.showNotification?.('Search 990s', err.detail || '990 PDF analysis failed', 'error');
                }
            } catch (e) {
                console.error('intelSearch990s error:', e);
                this.showNotification?.('Search 990s', 'Network error', 'error');
            } finally {
                this.intel990sLoading = false;
            }
        },

        /**
         * ④ Screen Fast — run fast screening on the current modal opportunity
         */
        async intelScreenFast() {
            await this._intelScreen('fast');
        },

        /**
         * ⑤ Screen Thorough — run thorough screening on the current modal opportunity
         */
        async intelScreenThorough() {
            await this._intelScreen('thorough');
        },

        async _intelScreen(mode) {
            const opp = this.selectedIntelligenceOpp;
            if (!opp?.opportunity_id) return;
            const oppId = opp.opportunity_id;
            if (mode === 'fast') this.intelScreenFastLoading = true;
            else this.intelScreenThoroughLoading = true;
            try {
                const resp = await fetch(`/api/v2/opportunities/${oppId}/screen?mode=${mode}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (resp.ok) {
                    const data = await resp.json();
                    const scoreKey = mode === 'fast' ? 'tool1_score_fast' : 'tool1_score_thorough';
                    const updates = {};
                    if (data.tool1_score) updates[scoreKey] = data.tool1_score;
                    if (data.category_level) updates.category_level = data.category_level;
                    if (data.overall_score !== undefined) updates.overall_score = data.overall_score;
                    Object.assign(this.selectedIntelligenceOpp, updates);
                    const idx = this.selectedOpportunities.findIndex(o => o.opportunity_id === oppId);
                    if (idx >= 0) Object.assign(this.selectedOpportunities[idx], updates);
                    const score = data.tool1_score ? ': ' + Math.round((data.tool1_score.overall_score || 0) * 100) + '%' : '';
                    this.showNotification(mode === 'fast' ? 'Screen Fast' : 'Screen Thorough', `Complete${score}`, 'success');
                } else {
                    const err = await resp.json().catch(() => ({}));
                    this.showNotification(mode === 'fast' ? 'Screen Fast' : 'Screen Thorough', err.detail || 'Screening failed', 'error');
                }
            } catch (e) {
                console.error('_intelScreen error:', e);
                this.showNotification(mode === 'fast' ? 'Screen Fast' : 'Screen Thorough', 'Network error', 'error');
            } finally {
                if (mode === 'fast') this.intelScreenFastLoading = false;
                else this.intelScreenThoroughLoading = false;
            }
        },

        /**
         * ⑥ Run Essentials AI — run ESSENTIALS deep intelligence for the current modal opportunity.
         * Auto-triggers Six Degrees connection analysis (⑧) on success.
         */
        async intelRunEssentials() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp) return;
            this.intelEssentialsLoading = true;
            try {
                const screeningContext = this._buildScreeningContext(opp);
                await this.analyzeOpportunity(opp, 'essentials', null, null, screeningContext);
                // Show summary tab so the user sees the AI recommendation + key highlights.
                this.intelligenceModalTab = 'summary';
                // Auto-run connections analysis (Six Degrees — part of Essentials tier).
                // On completion it switches to the Officers tab.
                await this.intelRunConnections();
            } finally {
                this.intelEssentialsLoading = false;
            }
        },

        /**
         * ⑦ Run Premium AI — run PREMIUM deep intelligence for the current modal opportunity.
         * If Essentials has already been run, passes the existing result so the backend
         * skips the core stages and only runs the 3 Premium-specific analyses.
         */
        async intelRunPremium() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp) return;
            this.intelPremiumLoading = true;
            try {
                const oppId = opp.opportunity_id || opp.id;
                const existingEssentials = this.intelligenceResults[oppId]?.analysis || null;
                if (existingEssentials) {
                    console.log('[intelRunPremium] Upgrade path: passing existing Essentials result to skip core stages');
                }
                const screeningContext = this._buildScreeningContext(opp);
                await this.analyzeOpportunity(opp, 'premium', null, existingEssentials, screeningContext);
            } finally {
                this.intelPremiumLoading = false;
            }
        },

        /**
         * ⑧ Run Connections — Six Degrees connection analysis for the current modal opportunity.
         * Compares profile board members with the funder's leadership team.
         */
        async intelRunConnections() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp) return;
            const oppId = opp.opportunity_id || opp.id;
            this.intelConnectionsLoading = true;
            try {
                const resp = await fetch(
                    `/api/v2/opportunities/${oppId}/run-connections`,
                    { method: 'POST' }
                );
                const data = await resp.json();
                if (data.success) {
                    // Always write through intelligenceResults (declared reactive object).
                    // Directly assigning a new property to the opp object bypasses Alpine.js
                    // reactivity and the Officers tab template won't update.
                    if (!this.intelligenceResults[oppId]) {
                        // Seed with opportunity so templates that read result.opportunity
                        // don't throw when Connections runs before Essentials.
                        this.intelligenceResults[oppId] = { opportunity: opp };
                    }
                    this.intelligenceResults[oppId].connections = data.connection_analysis;
                    // Switch to Officers & Directors tab so the user sees the results.
                    this.intelligenceModalTab = 'officers';
                    this.showNotification?.('Connections', 'Six Degrees analysis complete — see Officers tab', 'success');
                }
                return data;
            } catch (e) {
                console.error('[intelRunConnections] Error:', e);
                this.showNotification?.('Connections', 'Network error', 'error');
            } finally {
                this.intelConnectionsLoading = false;
            }
        },

        /**
         * ⑨ Run Networking — BFS graph paths + Sonnet narration ($4.00).
         * Discovers 1st/2nd/3rd degree connections via the persistent network graph.
         */
        async intelRunNetworking() {
            const opp = this.selectedIntelligenceOpp;
            if (!opp) return;
            const oppId = opp.opportunity_id || opp.id;
            this.intelNetworkingLoading = true;
            try {
                const resp = await fetch(
                    `/api/v2/opportunities/${oppId}/run-networking`,
                    { method: 'POST' }
                );
                const data = await resp.json();
                if (data.success) {
                    if (!this.intelligenceResults[oppId]) {
                        this.intelligenceResults[oppId] = { opportunity: opp };
                    }
                    this.intelligenceResults[oppId].networking = data;
                    this.intelligenceModalTab = 'network-paths';
                    this.showNotification?.('Networking', `Found ${data.paths_found || 0} connection path(s)`, 'success');
                } else if (data.error) {
                    this.showNotification?.('Networking', data.error, 'warning');
                }
                return data;
            } catch (e) {
                console.error('[intelRunNetworking] Error:', e);
                this.showNotification?.('Networking', 'Network error', 'error');
            } finally {
                this.intelNetworkingLoading = false;
            }
        },

        /**
         * Open the Intelligence modal for the first opportunity matching a given EIN.
         */
        openIntelligenceModalByEin(ein) {
            if (!ein) return;
            const opp = this.selectedOpportunities.find(o => o.ein === ein);
            if (opp) {
                const id = opp.opportunity_id || opp.id;
                this.openIntelligenceModal(id);
                this.$nextTick?.(() => { this.intelligenceModalTab = 'network-paths'; });
            }
        },

        /**
         * Return networking result for an opportunity (from results cache or opp object).
         */
        getNetworkingResult(opp) {
            if (!opp) return null;
            const oppId = opp.opportunity_id || opp.id;
            return this.intelligenceResults[oppId]?.networking
                || (opp?.networking_result ? { success: true, ...opp.networking_result } : null);
        },

        /**
         * Return the connection_analysis for an opportunity (from results cache or opp object).
         */
        getConnectionAnalysis(opp) {
            if (!opp) return null;
            const oppId = opp.opportunity_id || opp.id;
            return this.intelligenceResults[oppId]?.connections
                || opp?.connection_analysis
                || null;
        },

        /**
         * Return a Tailwind class pair for a connection_strength badge.
         */
        strengthClass(strength) {
            const map = {
                strong:   'bg-green-100 text-green-700',
                moderate: 'bg-yellow-100 text-yellow-700',
                weak:     'bg-gray-100 text-gray-500',
                none:     'bg-gray-100 text-gray-500',
                unknown:  'bg-blue-100 text-blue-600',
            };
            return map[strength] || 'bg-gray-100 text-gray-500';
        },

        /**
         * Build a screening_context dict from whatever SCREENING pipeline data is available
         * on the opportunity object. Passed to the backend so Claude can use it in analysis.
         */
        _buildScreeningContext(opp) {
            const ctx = {};
            if (opp.web_data) ctx.web_data = opp.web_data;
            if (opp.pdf_extraction) ctx.pdf_extraction = opp.pdf_extraction;
            if (opp.tool1_score_fast) ctx.fast_screen = opp.tool1_score_fast;
            if (opp.tool1_score_thorough) ctx.thorough_screen = opp.tool1_score_thorough;
            // Include base screening score if present
            if (opp.score !== undefined || opp.one_sentence_summary) {
                ctx.initial_score = {};
                if (opp.score !== undefined) ctx.initial_score.overall_score = opp.score;
                if (opp.one_sentence_summary) ctx.initial_score.one_sentence_summary = opp.one_sentence_summary;
                if (opp.strengths?.length) ctx.initial_score.strengths = opp.strengths;
                if (opp.concerns?.length) ctx.initial_score.concerns = opp.concerns;
            }
            return Object.keys(ctx).length > 0 ? ctx : null;
        },

        /**
         * Toggle opportunity selection for batch operations
         * @param {string} opportunityId - Opportunity ID to toggle
         */
        toggleOpportunitySelection(opportunityId) {
            const index = this.selectedOpportunitiesForBatch.indexOf(opportunityId);
            if (index === -1) {
                this.selectedOpportunitiesForBatch.push(opportunityId);
            } else {
                this.selectedOpportunitiesForBatch.splice(index, 1);
            }
        },

        /**
         * Check if opportunity is selected
         * @param {string} opportunityId - Opportunity ID to check
         */
        isOpportunitySelected(opportunityId) {
            return this.selectedOpportunitiesForBatch.includes(opportunityId);
        },

        /**
         * Analyze selected opportunities (batch operation)
         */
        async analyzeSelected() {
            if (this.selectedOpportunitiesForBatch.length === 0) {
                this.showNotification?.('Please select at least one opportunity', 'warning');
                return;
            }

            const selectedOpps = this.selectedOpportunities.filter(
                opp => this.selectedOpportunitiesForBatch.includes(opp.opportunity_id || opp.id)
            );

            console.log(`Analyzing ${selectedOpps.length} selected opportunities`);

            const results = [];
            let totalCost = 0;

            for (const opp of selectedOpps) {
                try {
                    const result = await this.analyzeOpportunity(opp, this.selectedDepth);
                    results.push(result);
                    totalCost += result.cost || 0;
                } catch (error) {
                    console.error(`Failed to analyze ${opp.organization_name}:`, error);
                }
            }

            // Clear selections after analysis
            this.selectedOpportunitiesForBatch = [];

            this.showNotification?.(
                `Analyzed ${results.length} opportunities for $${totalCost.toFixed(2)}`,
                'success'
            );

            return {
                success: true,
                results,
                total_cost: totalCost,
                completed: results.length,
                failed: selectedOpps.length - results.length
            };
        },

        // =================================================================
        // DEEP INTELLIGENCE OPERATIONS (Tool 2)
        // =================================================================

        /**
         * Analyze opportunity with selected depth
         * @param {Object} opportunity
         * @param {string} depth - quick, standard, enhanced, complete
         * @param {Object} profileData - Optional profile context
         */
        async analyzeOpportunity(opportunity, depth = null, profileData = null, existingEssentialsResult = null, screeningContext = null) {
            const analysisDepth = depth || this.selectedDepth;
            const oppId = opportunity.opportunity_id || opportunity.id;

            this.analyzing = true;
            this.analysisProgress[oppId] = { status: 'analyzing', progress: 0 };

            try {
                // Use api-helpers.js analyzeOpportunityDeep function
                // This is already implemented from Phase 9 Week 1
                if (typeof analyzeOpportunityDeep !== 'function') {
                    throw new Error('Deep intelligence function not available');
                }

                // Create profile object with ID for API call
                // Try multiple sources for profile ID
                let profileId = profileData?.profile_id || profileData?.id || this.currentProfileId;

                // Fallback: Try to get from window or root
                if (!profileId && typeof window !== 'undefined') {
                    profileId = window.currentProfileId;
                }

                // Final validation
                if (!profileId) {
                    throw new Error('Profile ID is required for deep intelligence analysis. Please ensure a profile is selected.');
                }

                const profile = { profile_id: profileId };

                const result = await analyzeOpportunityDeep(
                    opportunity,
                    profile,
                    analysisDepth,
                    existingEssentialsResult,
                    screeningContext
                );

                if (result.success) {
                    this.intelligenceResults[oppId] = {
                        opportunity,
                        depth: analysisDepth,
                        analysis: result.data,
                        cost: result.cost,
                        timestamp: new Date().toISOString()
                    };

                    this.analysisProgress[oppId] = { status: 'complete', progress: 100 };

                    this.showNotification?.(
                        `Analysis complete for ${opportunity.organization_name}`,
                        'success'
                    );

                    return result;
                } else {
                    throw new Error('Analysis failed');
                }

            } catch (error) {
                console.error('Analysis failed:', error);
                this.analysisProgress[oppId] = { status: 'error', progress: 0, error: error.message };
                this.showNotification?.(
                    `Analysis failed: ${error.message}`,
                    'error'
                );
                throw error;
            } finally {
                this.analyzing = false;
            }
        },

        /**
         * Analyze all selected opportunities
         * @param {string} depth
         */
        async analyzeAll(depth = null) {
            const analysisDepth = depth || this.selectedDepth;

            const results = [];
            let totalCost = 0;

            for (const opportunity of this.selectedOpportunities) {
                try {
                    const result = await this.analyzeOpportunity(opportunity, analysisDepth);
                    results.push(result);
                    totalCost += result.cost || 0;
                } catch (error) {
                    console.error(`Failed to analyze ${opportunity.organization_name}:`, error);
                    // Continue with next opportunity
                }
            }

            this.showNotification?.(
                `Analyzed ${results.length} opportunities for $${totalCost.toFixed(2)}`,
                'success'
            );

            return {
                success: true,
                results,
                total_cost: totalCost,
                completed: results.length,
                failed: this.selectedOpportunities.length - results.length
            };
        },

        // =================================================================
        // REPORT GENERATION (Tool 21)
        // =================================================================

        /**
         * Generate report for opportunity
         * @param {string} opportunityId
         * @param {string} template - comprehensive, executive, risk, implementation
         */
        async generateReport(opportunityId, template = null) {
            const reportTemplate = template || this.selectedReportTemplate;

            this.generating = true;

            try {
                const intelligence = this.intelligenceResults[opportunityId];
                if (!intelligence) {
                    throw new Error('No intelligence data available. Analyze first.');
                }

                // Use api-helpers.js generateReport function
                if (typeof generateReport !== 'function') {
                    throw new Error('Report generation function not available');
                }

                // Get the opportunity and profile data
                const opportunity = intelligence.opportunity;
                const profile = {
                    profile_id: this.currentProfileId || window.currentProfileId,
                    ...intelligence.profile
                };

                const result = await generateReport(
                    opportunity,
                    profile,
                    reportTemplate,
                    'html'
                );

                if (result.success) {
                    this.showNotification?.('Report generated successfully', 'success');

                    // Store report with intelligence
                    this.intelligenceResults[opportunityId].report = {
                        template: reportTemplate,
                        data: result.data,
                        timestamp: new Date().toISOString()
                    };

                    return result;
                } else {
                    throw new Error('Report generation failed');
                }

            } catch (error) {
                console.error('Report generation failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.generating = false;
            }
        },

        // =================================================================
        // DATA EXPORT (Tool 18)
        // =================================================================

        /**
         * Export intelligence data
         * @param {string} opportunityId
         * @param {string} format - json, csv, excel, pdf
         */
        async exportData(opportunityId, format = 'pdf') {
            this.exporting = true;

            try {
                const intelligence = this.intelligenceResults[opportunityId];
                if (!intelligence) {
                    throw new Error('No intelligence data to export');
                }

                // Use api-helpers.js exportData function
                if (typeof exportData !== 'function') {
                    throw new Error('Export function not available');
                }

                const result = await exportData(
                    intelligence,
                    `intelligence_${opportunityId}`,
                    format
                );

                if (result.success) {
                    this.showNotification?.(
                        `Exported as ${format.toUpperCase()}`,
                        'success'
                    );

                    return result;
                } else {
                    throw new Error('Export failed');
                }

            } catch (error) {
                console.error('Export failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.exporting = false;
            }
        },

        // =================================================================
        // GRANT PACKAGE GENERATION (Tool 19)
        // =================================================================

        /**
         * Generate grant application package
         * @param {string} opportunityId
         */
        async generatePackage(opportunityId) {
            this.generating = true;

            try {
                const intelligence = this.intelligenceResults[opportunityId];
                if (!intelligence) {
                    throw new Error('No intelligence data available');
                }

                const response = await fetch('/api/v1/tools/Grant Package Generator Tool/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        inputs: {
                            opportunity: intelligence.opportunity,
                            intelligence: intelligence.analysis
                        }
                    })
                });

                if (!response.ok) {
                    throw new Error('Package generation failed');
                }

                const result = await response.json();

                if (result.success) {
                    this.showNotification?.('Grant package created successfully', 'success');

                    // Store package with intelligence
                    this.intelligenceResults[opportunityId].package = {
                        data: result.data,
                        timestamp: new Date().toISOString()
                    };

                    return result;
                } else {
                    throw new Error('Package generation failed');
                }

            } catch (error) {
                console.error('Package generation failed:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.generating = false;
            }
        },

        // =================================================================
        // NAVIGATION & UI
        // =================================================================

        /**
         * Get current opportunity
         */
        get currentOpportunity() {
            return this.selectedOpportunities[this.currentOpportunityIndex];
        },

        /**
         * Navigate to next opportunity
         */
        nextOpportunity() {
            if (this.currentOpportunityIndex < this.selectedOpportunities.length - 1) {
                this.currentOpportunityIndex++;
            }
        },

        /**
         * Navigate to previous opportunity
         */
        prevOpportunity() {
            if (this.currentOpportunityIndex > 0) {
                this.currentOpportunityIndex--;
            }
        },

        /**
         * Jump to specific opportunity
         * @param {number} index
         */
        goToOpportunity(index) {
            if (index >= 0 && index < this.selectedOpportunities.length) {
                this.currentOpportunityIndex = index;
            }
        },

        /**
         * Check if opportunity has been analyzed
         * @param {string} opportunityId
         */
        hasIntelligence(opportunityId) {
            // Only true when Essentials AI analysis has actually run (has .analysis key).
            // A connections-only entry {opportunity, connections} must not block Essentials.
            return !!this.intelligenceResults[opportunityId]?.analysis;
        },

        /**
         * Get intelligence for opportunity
         * @param {string} opportunityId
         */
        getIntelligence(opportunityId) {
            return this.intelligenceResults[opportunityId];
        },

        /**
         * Get analysis progress
         * @param {string} opportunityId
         */
        getProgress(opportunityId) {
            return this.analysisProgress[opportunityId] || { status: 'pending', progress: 0 };
        },

        /**
         * Select depth tier
         * @param {string} depth
         */
        selectDepth(depth) {
            this.selectedDepth = depth;
            this.showDepthSelector = false;
        },

        /**
         * Toggle depth selector
         */
        toggleDepthSelector() {
            this.showDepthSelector = !this.showDepthSelector;
        },

        /**
         * Open report modal
         * @param {string} opportunityId
         */
        openReportModal(opportunityId) {
            if (!this.hasIntelligence(opportunityId)) {
                this.showNotification?.('Please analyze first', 'warning');
                return;
            }
            this.showReportModal = true;
        },

        /**
         * Close report modal
         */
        closeReportModal() {
            this.showReportModal = false;
        },

        /**
         * Open export modal
         * @param {string} opportunityId
         */
        openExportModal(opportunityId) {
            if (!this.hasIntelligence(opportunityId)) {
                this.showNotification?.('Please analyze first', 'warning');
                return;
            }
            this.showExportModal = true;
        },

        /**
         * Close export modal
         */
        closeExportModal() {
            this.showExportModal = false;
        },

        // =================================================================
        // COST CALCULATION
        // =================================================================

        /**
         * Calculate total cost for all opportunities
         */
        getEstimatedCost() {
            const depth = this.depths.find(d => d.id === this.selectedDepth);
            if (!depth) return 0;

            return this.selectedOpportunities.length * depth.price;
        },

        /**
         * Get cost breakdown
         */
        getCostBreakdown() {
            const depth = this.depths.find(d => d.id === this.selectedDepth);
            if (!depth) return null;

            return {
                per_opportunity: depth.price,
                total_opportunities: this.selectedOpportunities.length,
                estimated_total: this.getEstimatedCost(),
                depth: depth.name
            };
        },

        /**
         * Get actual spent cost
         */
        getActualCost() {
            return Object.values(this.intelligenceResults)
                .reduce((sum, result) => sum + (result.cost || 0), 0);
        },

        // =================================================================
        // NOTES MANAGEMENT
        // =================================================================

        /**
         * Save notes for an opportunity
         * @param {string} opportunityId - Opportunity ID to save notes for
         */
        async saveNotes(opportunityId) {
            try {
                const opp = this.selectedOpportunities.find(
                    o => o.opportunity_id === opportunityId || o.id === opportunityId
                );

                if (!opp || !opp.notes) {
                    this.showNotification?.('No notes to save', 'warning');
                    return;
                }

                // Save notes to database via API
                const response = await fetch(`/api/v2/opportunities/${opportunityId}/notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        notes: opp.notes
                    })
                });

                if (!response.ok) {
                    throw new Error(`Failed to save notes: ${response.statusText}`);
                }

                this.showNotification?.('Notes saved successfully', 'success');

                console.log(`Saved notes for opportunity ${opportunityId}`);

            } catch (error) {
                console.error('Failed to save notes:', error);
                this.showNotification?.(
                    `Failed to save notes: ${error.message}`,
                    'error'
                );
            }
        },

        // =================================================================
        // COMPOSITE SCORE & RED FLAGS
        // =================================================================

        /**
         * Compute a composite score from all available pipeline signals.
         * Mirrors the same method in screening-module.js.
         */
        computeCompositeScore(opp) {
            const candidates = [];
            candidates.push({ score: parseFloat(opp.overall_score) || 0, weight: 0.05 });
            if (opp.web_search_complete && opp.web_data) {
                candidates.push({ score: parseFloat(opp.web_data.data_quality_score) || 0, weight: 0.10 });
            }
            if (opp.pdf_analyzed) {
                candidates.push({ score: 0.70, weight: 0.10 });
            }
            const fast = opp.tool1_score_fast || (opp.tool1_score?.mode === 'fast' ? opp.tool1_score : null);
            if (fast) candidates.push({ score: parseFloat(fast.overall_score) || 0, weight: 0.35 });
            if (opp.tool1_score_thorough) {
                candidates.push({ score: parseFloat(opp.tool1_score_thorough.overall_score) || 0, weight: 0.40 });
            }
            const totalWeight = candidates.reduce((s, c) => s + c.weight, 0);
            if (totalWeight === 0) return 0;
            return Math.round(candidates.reduce((s, c) => s + c.score * c.weight, 0) / totalWeight * 100) / 100;
        },

        /**
         * Get RED flags for an opportunity.
         */
        getRedFlags(opp) {
            const flags = [];
            const webData = opp.web_data?.grant_funder_intelligence || opp.web_data || {};
            const appStatus = (webData.application_status || '').toLowerCase();
            if (/not accepting|by invitation|closed|not open/.test(appStatus)) {
                flags.push({ code: 'app_closed', severity: 'critical',
                    label: 'Closed', tooltip: `Application status: ${webData.application_status}` });
            }
            const geo = (webData.geographic_limitations || []);
            const geoText = Array.isArray(geo) ? geo.join(' ').toLowerCase() : String(geo).toLowerCase();
            const foreignPattern = /canada|alberta|ontario|british columbia|united kingdom|australia/i;
            if (foreignPattern.test(geoText)) {
                flags.push({ code: 'geo_mismatch', severity: 'critical',
                    label: 'Foreign', tooltip: `Geographic scope: ${Array.isArray(geo) ? geo.join(', ') : geo}` });
            }
            const fastElig = opp.tool1_score_fast?.eligibility_score;
            const thorElig = opp.tool1_score_thorough?.eligibility_score;
            if ((fastElig !== undefined && fastElig < 0.25) || (thorElig !== undefined && thorElig < 0.25)) {
                flags.push({ code: 'eligibility_fail', severity: 'critical',
                    label: 'Ineligible', tooltip: `Eligibility score: ${Math.round((fastElig !== undefined ? fastElig : thorElig) * 100)}%` });
            }
            return flags;
        },

        hasRedFlag(opp) {
            return this.getRedFlags(opp).some(f => f.severity === 'critical');
        },

        // =================================================================
        // INTELLIGENCE TABLE FILTER / SORT
        // =================================================================

        /**
         * Filtered and sorted INTELLIGENCE table rows.
         */
        get filteredIntelligenceOpps() {
            let opps = [...this.selectedOpportunities];
            if (this.intelligenceCategoryFilter) {
                opps = opps.filter(o => o.category_level === this.intelligenceCategoryFilter);
            }
            if (this.intelligenceSortBy === 'composite_score') {
                opps.sort((a, b) => this.computeCompositeScore(b) - this.computeCompositeScore(a));
            } else if (this.intelligenceSortBy === 'organization_name') {
                opps.sort((a, b) => (a.organization_name || '').localeCompare(b.organization_name || ''));
            } else if (this.intelligenceSortBy === 'revenue') {
                opps.sort((a, b) => (b.revenue || 0) - (a.revenue || 0));
            }
            return opps;
        },

        /**
         * Category counts for INTELLIGENCE filter bar.
         */
        get intelligenceCategoryCounts() {
            const counts = { all: 0, qualified: 0, review: 0, consider: 0, low_priority: 0 };
            for (const o of this.selectedOpportunities) {
                counts.all++;
                const cat = o.category_level || 'low_priority';
                if (counts[cat] !== undefined) counts[cat]++;
            }
            return counts;
        },

        // =================================================================
        // SUMMARY & STATS
        // =================================================================

        /**
         * Get analysis summary
         */
        // =================================================================
        // NETWORK GRAPH
        // =================================================================

        /**
         * Load network graph stats from server ($0.00).
         */
        async networkLoadStats(profileId) {
            const pid = profileId || this.currentProfileId;
            if (!pid) return;
            try {
                const resp = await fetch(`/api/v2/network/graph-stats?profile_id=${encodeURIComponent(pid)}`);
                if (resp.ok) {
                    this.networkGraphStats = await resp.json();
                }
            } catch (e) {
                console.warn('[networkLoadStats]', e);
            }
        },

        /**
         * Populate graph from cached ein_intelligence ($0.00).
         */
        async networkBuildFromCache() {
            const pid = this.currentProfileId;
            if (!pid) return;
            this.networkBuildLoading = true;
            try {
                const resp = await fetch('/api/v2/network/populate-graph', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: pid }),
                });
                const data = await resp.json();
                if (data.success) {
                    this.showNotification?.('Network Graph', `${data.people_added} people added · ${data.graph_total_size} total in graph`, 'success');
                    await this.networkLoadStats(pid);
                } else {
                    this.showNotification?.('Network Graph', data.detail || 'Build failed', 'error');
                }
            } catch (e) {
                console.error('[networkBuildFromCache]', e);
                this.showNotification?.('Network Graph', 'Network error', 'error');
            } finally {
                this.networkBuildLoading = false;
            }
        },

        /**
         * Fetch 990 XML from ProPublica and parse officers directly — no AI, $0.00.
         * Handles all preflight statuses (needs_url, needs_990_search, pdf_no_officers).
         * After completing, refreshes graph stats automatically.
         */
        async networkXmlOfficerLookup() {
            const pid = this.currentProfileId;
            if (!pid) return;
            this.networkXmlLookupLoading = true;
            try {
                const resp = await fetch('/api/v2/network/xml-officer-lookup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: pid, limit: 30 }),
                });
                const data = await resp.json();
                if (data.success) {
                    const msg = data.eins_with_officers > 0
                        ? `${data.officers_added} officers found in ${data.eins_with_officers} funders · ${data.eins_no_xml} had no XML`
                        : `No officers found in XML (${data.eins_no_xml} funders had no XML or empty officer sections)`;
                    this.showNotification?.('990 XML Lookup', msg, data.eins_with_officers > 0 ? 'success' : 'info');
                    await this.networkLoadStats(pid);
                } else {
                    this.showNotification?.('990 XML Lookup', data.detail || 'Lookup failed', 'error');
                }
            } catch (e) {
                console.error('[networkXmlOfficerLookup]', e);
                this.showNotification?.('990 XML Lookup', 'Network error', 'error');
            } finally {
                this.networkXmlLookupLoading = false;
            }
        },

        /**
         * Find filing history URLs for funders that have no filing_history yet ($0.00 ProPublica).
         * After completing, refreshes stats and triggers populate-graph.
         */
        async networkFindMissingUrls() {
            const pid = this.currentProfileId;
            if (!pid) return;
            this.networkFindUrlsLoading = true;
            try {
                const resp = await fetch('/api/v2/network/discover-filings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: pid, limit: 50 }),
                });
                const data = await resp.json();
                this.showNotification?.('Find URLs', `${data.filing_histories_found} new filing histories found · ${data.already_cached} already cached`, 'success');
                await this.networkLoadStats(pid);
            } catch (e) {
                console.error('[networkFindMissingUrls]', e);
                this.showNotification?.('Find URLs', 'Network error', 'error');
            } finally {
                this.networkFindUrlsLoading = false;
            }
        },

        /**
         * Run 990 PDF analysis only for funders that have filing_history but no officers yet.
         * Collects opportunity_ids from coverage items with preflight='needs_990_search',
         * calls the existing batch-analyze-990-pdfs endpoint, then harvests into graph.
         */
        async networkSearch990ForMissing() {
            const pid = this.currentProfileId;
            if (!pid || !this.networkGraphStats?.coverage) return;
            this.network990Loading = true;
            try {
                // Collect opp IDs for funders that need 990 search
                // (has filing URL but no PDF analysis yet, OR PDF ran but had no officers)
                const targetStatuses = ['needs_990_search', 'pdf_no_officers'];
                const oppIds = [];
                for (const funder of this.networkGraphStats.coverage) {
                    if (targetStatuses.includes(funder.preflight)) {
                        oppIds.push(...(funder.opportunity_ids || []));
                    }
                }
                if (oppIds.length === 0) {
                    this.showNotification?.('Search 990s', 'No funders need 990 search right now', 'info');
                    return;
                }
                const resp = await fetch('/api/v2/opportunities/batch-analyze-990-pdfs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ opportunity_ids: oppIds }),
                });
                const data = await resp.json();
                const done = (data.results || []).filter(r => r.status === 'success').length;
                this.showNotification?.('Search 990s', `${done} PDFs analyzed · harvesting into graph...`, 'success');
                // Harvest newly extracted officers into graph
                await this.networkBuildFromCache();
            } catch (e) {
                console.error('[networkSearch990ForMissing]', e);
                this.showNotification?.('Search 990s', 'Network error', 'error');
            } finally {
                this.network990Loading = false;
            }
        },

        /**
         * Rank all funders by BFS warmth ($0.00).
         */
        async networkRankFunders() {
            const pid = this.currentProfileId;
            if (!pid) return;
            this.networkRankLoading = true;
            try {
                const resp = await fetch('/api/v2/network/rank-funders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: pid, max_degree: 3 }),
                });
                const data = await resp.json();
                this.networkRankedFunders = data.ranked_funders || [];
                const hot = this.networkRankedFunders.filter(f => f.strength === 'hot').length;
                const warm = this.networkRankedFunders.filter(f => f.strength === 'warm').length;
                this.showNotification?.('Funder Ranking', `${hot} hot · ${warm} warm funders identified`, 'success');
            } catch (e) {
                console.error('[networkRankFunders]', e);
                this.showNotification?.('Funder Ranking', 'Network error', 'error');
            } finally {
                this.networkRankLoading = false;
            }
        },

        getSummary() {
            const total = this.selectedOpportunities.length;
            const analyzed = Object.keys(this.intelligenceResults).length;
            const withReports = Object.values(this.intelligenceResults)
                .filter(r => r.report).length;
            const withPackages = Object.values(this.intelligenceResults)
                .filter(r => r.package).length;

            return {
                total,
                analyzed,
                pending: total - analyzed,
                withReports,
                withPackages,
                totalCost: this.getActualCost(),
                progress: total > 0 ? (analyzed / total * 100).toFixed(0) : 0
            };
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = intelligenceModule;
}

// CRITICAL: Attach to window for Alpine.js to see it
window.intelligenceModule = intelligenceModule;

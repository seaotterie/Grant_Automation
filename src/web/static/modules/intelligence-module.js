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
        intelligenceModalTab: 'summary',    // Active tab in modal

        // Selection State (for checkboxes)
        selectedOpportunitiesForBatch: [],  // Track checkbox selections

        // Loading States
        analyzing: false,
        generating: false,
        exporting: false,

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

                console.log(`Loaded ${this.selectedOpportunities.length} intelligence opportunities`);

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
            const opp = this.selectedOpportunities.find(
                o => o.opportunity_id === opportunityId || o.id === opportunityId
            );

            if (!opp) {
                console.error('Opportunity not found:', opportunityId);
                return;
            }

            this.selectedIntelligenceOpp = opp;
            this.intelligenceModalTab = 'summary';  // Reset to first tab
            this.showIntelligenceModal = true;

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
        },

        /**
         * Switch tabs in Intelligence modal
         * @param {string} tab - Tab name (summary, scores, analysis, details, grants, officers, website, notes)
         */
        switchIntelligenceTab(tab) {
            this.intelligenceModalTab = tab;
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
        async analyzeOpportunity(opportunity, depth = null, profileData = null) {
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
                    analysisDepth
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

                const result = await generateReport(
                    intelligence.analysis,
                    reportTemplate
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
            return !!this.intelligenceResults[opportunityId];
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
        // SUMMARY & STATS
        // =================================================================

        /**
         * Get analysis summary
         */
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

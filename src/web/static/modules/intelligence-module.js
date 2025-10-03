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

        // Opportunities State
        selectedOpportunities: [],
        selectionNotes: {},

        // Intelligence Results
        intelligenceResults: {},
        analysisProgress: {},

        // Analysis Configuration
        selectedDepth: 'standard',
        depths: [
            {
                id: 'quick',
                name: 'Quick Intelligence',
                price: 0.75,
                time: '5-10 min',
                description: '4-stage AI analysis with scoring'
            },
            {
                id: 'standard',
                name: 'Standard Intelligence',
                price: 7.50,
                time: '15-20 min',
                description: '+ Historical funding analysis'
            },
            {
                id: 'enhanced',
                name: 'Enhanced Intelligence',
                price: 22.00,
                time: '30-45 min',
                description: '+ Document analysis & network intelligence'
            },
            {
                id: 'complete',
                name: 'Complete Intelligence',
                price: 42.00,
                time: '45-60 min',
                description: '+ Policy analysis & monitoring'
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
         */
        init(opportunities, notes = {}) {
            this.selectedOpportunities = opportunities || [];
            this.selectionNotes = notes || {};

            console.log(`Intelligence module initialized with ${this.selectedOpportunities.length} opportunities`);

            // Auto-select first opportunity
            if (this.selectedOpportunities.length > 0) {
                this.currentOpportunityIndex = 0;
            }
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

                const result = await analyzeOpportunityDeep(
                    opportunity,
                    analysisDepth,
                    profileData
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

                    const depthInfo = this.depths.find(d => d.id === analysisDepth);
                    console.log(
                        `Analysis complete: ${opportunity.organization_name} (${depthInfo?.name}, $${result.cost})`
                    );

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

            console.log(`Starting batch analysis: ${this.selectedOpportunities.length} opportunities (${analysisDepth})`);

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

            console.log(
                `Batch analysis complete: ${results.length}/${this.selectedOpportunities.length} successful (Total: $${totalCost.toFixed(2)})`
            );

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
                    console.log(`Report generated: ${opportunityId} (${reportTemplate})`);
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
                    console.log(`Export complete: ${format.toUpperCase()}`);
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

                const response = await fetch('/api/v1/tools/grant-package-generator-tool/execute', {
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
                    console.log(`Package generated: ${opportunityId}`);
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
            console.log('Depth selected:', depth);
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

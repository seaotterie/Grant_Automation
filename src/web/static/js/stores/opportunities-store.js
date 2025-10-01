// Opportunities Alpine.js Store
// Manages all opportunity-related state and operations
// Extracted from main Alpine app for better organization

// Initialize opportunities store
document.addEventListener('alpine:init', () => {
    Alpine.store('opportunities', {
        // State
        opportunitiesData: [],
        filteredOpportunities: [],
        selectedOpportunity: null,

        // Funnel stage data
        prospects: [],
        qualified: [],
        candidates: [],
        targets: [],
        opportunities: [],

        // Discovery and analysis state
        discoveryActive: false,
        discoveryResults: null,
        analysisStatus: 'idle',
        analysisResults: {},

        // Opportunity metrics
        candidatesCount: 0,
        totalScore: 0,
        averageScore: 0,

        // Getters
        get hasOpportunities() {
            return this.opportunitiesData.length > 0;
        },

        get opportunityCount() {
            return this.opportunitiesData.length;
        },

        get prospectsCount() {
            return this.prospects.length;
        },

        get qualifiedCount() {
            return this.qualified.length;
        },

        get candidatesCount() {
            return this.candidates.length;
        },

        get targetsCount() {
            return this.targets.length;
        },

        get opportunitiesCount() {
            return this.opportunities.length;
        },

        // Stage-based getters using CatalynxUtils
        get prospectsByStage() {
            return this.opportunitiesData.filter(opp =>
                CatalynxUtils.getActualStage(opp) === 'prospects'
            );
        },

        get qualifiedByStage() {
            return this.opportunitiesData.filter(opp =>
                CatalynxUtils.getActualStage(opp) === 'qualified'
            );
        },

        get candidatesByStage() {
            return this.opportunitiesData.filter(opp =>
                CatalynxUtils.getActualStage(opp) === 'candidates'
            );
        },

        get targetsByStage() {
            return this.opportunitiesData.filter(opp =>
                CatalynxUtils.getActualStage(opp) === 'targets'
            );
        },

        get opportunitiesByStage() {
            return this.opportunitiesData.filter(opp =>
                CatalynxUtils.getActualStage(opp) === 'opportunities'
            );
        },

        // Actions
        async loadOpportunities(profileId) {
            if (!profileId) {
                console.warn('⚠️ No profile ID provided for opportunity loading');
                return [];
            }

            console.log('📋 Loading opportunities for profile:', profileId);

            try {
                const response = await ApiClient.profiles.getOpportunities(profileId);
                const rawOpportunities = response.opportunities || response || [];

                // Standardize and validate opportunities
                const standardizedOpportunities = rawOpportunities
                    .map(opp => CatalynxUtils.standardizeOpportunityData(opp))
                    .filter(opp => opp && CatalynxUtils.validateOpportunitySchema(opp));

                // Deduplicate opportunities
                this.opportunitiesData = CatalynxUtils.deduplicateOpportunities(standardizedOpportunities);

                // Update stage arrays
                this.updateStageArrays();

                // Update metrics
                this.updateMetrics();

                console.log('✅ Loaded opportunities:', {
                    total: this.opportunitiesData.length,
                    prospects: this.prospects.length,
                    qualified: this.qualified.length,
                    candidates: this.candidates.length,
                    targets: this.targets.length,
                    opportunities: this.opportunities.length
                });

                return this.opportunitiesData;

            } catch (error) {
                console.error('❌ Failed to load opportunities:', error);
                ErrorHandler.showError(error, { operation: 'Load Opportunities', profileId });
                return [];
            }
        },

        updateStageArrays() {
            // Clear existing arrays
            this.prospects = [];
            this.qualified = [];
            this.candidates = [];
            this.targets = [];
            this.opportunities = [];

            // Categorize opportunities by stage
            this.opportunitiesData.forEach(opportunity => {
                const stage = CatalynxUtils.getActualStage(opportunity);

                switch (stage) {
                    case 'prospects':
                        this.prospects.push(opportunity);
                        break;
                    case 'qualified':
                        this.qualified.push(opportunity);
                        break;
                    case 'candidates':
                        this.candidates.push(opportunity);
                        break;
                    case 'targets':
                        this.targets.push(opportunity);
                        break;
                    case 'opportunities':
                        this.opportunities.push(opportunity);
                        break;
                    default:
                        // Default to prospects for unknown stages
                        this.prospects.push(opportunity);
                }
            });

            // Update filtered opportunities
            this.filteredOpportunities = [...this.opportunitiesData];
        },

        updateMetrics() {
            if (this.opportunitiesData.length === 0) {
                this.candidatesCount = 0;
                this.totalScore = 0;
                this.averageScore = 0;
                return;
            }

            // Count candidates
            this.candidatesCount = this.candidates.length;

            // Calculate total and average scores
            const scores = this.opportunitiesData
                .map(opp => opp.compatibility_score || opp.raw_score || 0)
                .filter(score => score > 0);

            this.totalScore = scores.reduce((sum, score) => sum + score, 0);
            this.averageScore = scores.length > 0 ? this.totalScore / scores.length : 0;
        },

        selectOpportunity(opportunity) {
            console.log('👆 Selected opportunity:', opportunity?.organization_name || 'None');
            this.selectedOpportunity = opportunity;
        },

        async startDiscovery(profileId, processors = [], options = {}) {
            console.log('🚀 Starting discovery for profile:', profileId, 'with processors:', processors);

            this.discoveryActive = true;
            this.discoveryResults = null;

            try {
                const response = await ApiClient.discovery.start(profileId, processors, options);
                this.discoveryResults = response;

                console.log('✅ Discovery completed:', response);
                return response;

            } catch (error) {
                console.error('❌ Discovery failed:', error);
                ErrorHandler.showError(error, { operation: 'Start Discovery', profileId });
                throw error;
            } finally {
                this.discoveryActive = false;
            }
        },

        async getDiscoveryStatus(profileId) {
            try {
                const status = await ApiClient.discovery.getStatus(profileId);
                return status;
            } catch (error) {
                console.error('❌ Failed to get discovery status:', error);
                return null;
            }
        },

        filterOpportunities(searchTerm = '', filters = {}) {
            if (!searchTerm && Object.keys(filters).length === 0) {
                this.filteredOpportunities = [...this.opportunitiesData];
                return;
            }

            this.filteredOpportunities = this.opportunitiesData.filter(opportunity => {
                // Text search
                if (searchTerm) {
                    const searchLower = searchTerm.toLowerCase();
                    const matchesText =
                        opportunity.organization_name?.toLowerCase().includes(searchLower) ||
                        opportunity.program_name?.toLowerCase().includes(searchLower) ||
                        opportunity.description?.toLowerCase().includes(searchLower);

                    if (!matchesText) return false;
                }

                // Stage filter
                if (filters.stage) {
                    const actualStage = CatalynxUtils.getActualStage(opportunity);
                    if (actualStage !== filters.stage) return false;
                }

                // Source filter
                if (filters.source && opportunity.discovery_source !== filters.source) {
                    return false;
                }

                // Score filter
                if (filters.minScore) {
                    const score = opportunity.compatibility_score || opportunity.raw_score || 0;
                    if (score < filters.minScore) return false;
                }

                return true;
            });

            console.log(`🔍 Filtered ${this.filteredOpportunities.length} of ${this.opportunitiesData.length} opportunities`);
        },

        // Move opportunity between stages
        moveOpportunityToStage(opportunityId, newStage) {
            const opportunity = this.opportunitiesData.find(opp => opp.opportunity_id === opportunityId);
            if (!opportunity) {
                console.warn('⚠️ Opportunity not found:', opportunityId);
                return false;
            }

            console.log(`🔄 Moving opportunity ${opportunity.organization_name} to stage: ${newStage}`);

            // Update the opportunity stage
            opportunity.funnel_stage = newStage;
            opportunity.stage_updated_at = new Date().toISOString();

            // Refresh stage arrays and metrics
            this.updateStageArrays();
            this.updateMetrics();

            return true;
        },

        // Bulk operations
        moveOpportunitiesToStage(opportunityIds, newStage) {
            let moved = 0;
            opportunityIds.forEach(id => {
                if (this.moveOpportunityToStage(id, newStage)) {
                    moved++;
                }
            });

            console.log(`🔄 Moved ${moved} opportunities to ${newStage}`);
            return moved;
        },

        // Reset store
        reset() {
            this.opportunitiesData = [];
            this.filteredOpportunities = [];
            this.selectedOpportunity = null;
            this.prospects = [];
            this.qualified = [];
            this.candidates = [];
            this.targets = [];
            this.opportunities = [];
            this.discoveryActive = false;
            this.discoveryResults = null;
            this.analysisStatus = 'idle';
            this.analysisResults = {};
            this.candidatesCount = 0;
            this.totalScore = 0;
            this.averageScore = 0;
        }
    });

    console.log('🎯 Opportunities store initialized');
});
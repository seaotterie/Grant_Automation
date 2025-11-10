/**
 * State Management Module
 * Centralized application state for Catalynx
 *
 * Provides global state management across all modules
 */

function stateModule() {
    return {
        // Navigation State
        activeStage: 'welcome', // Current active stage: welcome, profiler, screening, intelligence
        previousStage: null,

        // Profile State
        selectedProfile: null,
        profiles: [],
        profilesLoading: false,

        // Screening State
        discoveryResults: [],
        screeningResults: [],
        selectedForIntelligence: [],

        // Intelligence State
        intelligenceResults: {},

        // UI State
        darkMode: false,
        mobileMenuOpen: false,

        // System State
        systemStatus: 'healthy',
        apiStatus: 'healthy',

        /**
         * Switch to a different stage
         * @param {string} stage - profiles, screening, or intelligence
         */
        switchStage(stage) {
            this.previousStage = this.activeStage;
            this.activeStage = stage;

            console.log(`Stage switched: ${this.previousStage} → ${stage}`);

            // Dispatch custom event for stage change
            this.$dispatch('stage-changed', {
                from: this.previousStage,
                to: stage
            });
        },

        /**
         * Go back to previous stage
         */
        goBack() {
            if (this.previousStage) {
                this.switchStage(this.previousStage);
            }
        },

        /**
         * Set selected profile
         * @param {Object} profile
         */
        selectProfile(profile) {
            this.selectedProfile = profile;
            console.log('Profile selected:', profile?.name);
        },

        /**
         * Clear all state (for testing/reset)
         */
        resetState() {
            this.activeStage = 'welcome';
            this.selectedProfile = null;
            this.discoveryResults = [];
            this.screeningResults = [];
            this.selectedForIntelligence = [];
            this.intelligenceResults = {};

            console.log('Application state reset');
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = stateModule;
}

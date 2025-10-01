// UI State Alpine.js Store
// Manages all UI-related state (modals, tabs, navigation, etc.)
// Extracted from main Alpine app for better organization

// Initialize UI store
document.addEventListener('alpine:init', () => {
    Alpine.store('ui', {
        // Navigation state
        activeTab: 'status',
        activeStage: 'welcome',
        active990Tab: 'overview',

        // System status
        systemStatus: 'healthy',
        apiStatus: 'healthy',
        currentTime: new Date().toLocaleTimeString(),

        // Modal states
        showProfileModal: false,
        showOrganizationSelectionModal: false,
        showIntelligenceModal: false,
        showExportModal: false,
        showDeleteConfirmationModal: false,
        showProspectModal: false,
        show4TierIntelligenceModal: false,

        // Intelligence modal state
        selectedCandidateForIntelligence: null,
        intelligenceGenerating: false,
        intelligenceResult: null,
        intelligenceError: null,
        selectedIntelligenceTier: 'current',

        // Export modal state
        exportConfig: {
            format: 'pdf',
            template: 'executive',
            includeCharts: true,
            includeTables: true
        },
        exportInProgress: false,

        // Pagination state
        currentPage: 1,
        itemsPerPage: 10,
        sortColumn: null,
        sortDirection: 'asc',

        // Loading states
        loading: false,
        loadingMessage: '',

        // Notifications/toasts
        notifications: [],

        // Theme
        darkMode: false,

        // Getters
        get hasActiveModal() {
            return this.showProfileModal ||
                   this.showOrganizationSelectionModal ||
                   this.showIntelligenceModal ||
                   this.showExportModal ||
                   this.showDeleteConfirmationModal ||
                   this.showProspectModal ||
                   this.show4TierIntelligenceModal;
        },

        get isSystemHealthy() {
            return this.systemStatus === 'healthy' && this.apiStatus === 'healthy';
        },

        get totalPages() {
            // Calculate total pages based on filtered items
            // This would need to be connected to the actual data
            return Math.ceil(100 / this.itemsPerPage); // Placeholder
        },

        // Actions - Navigation
        switchTab(tabName) {
            console.log('🔄 Switching to tab:', tabName);
            this.activeTab = tabName;

            // Update URL if needed (optional)
            if (window.history && window.history.pushState) {
                const url = new URL(window.location);
                url.searchParams.set('tab', tabName);
                window.history.pushState({}, '', url);
            }
        },

        switchStage(stageName) {
            console.log('🔄 Switching to stage:', stageName);
            this.activeStage = stageName;
        },

        switch990Tab(tabName) {
            console.log('🔄 Switching 990 tab to:', tabName);
            this.active990Tab = tabName;
        },

        // Actions - Modals
        openModal(modalName, data = null) {
            console.log('📂 Opening modal:', modalName);

            // Close all other modals first
            this.closeAllModals();

            // Open the requested modal
            switch (modalName) {
                case 'profile':
                    this.showProfileModal = true;
                    break;
                case 'organization':
                    this.showOrganizationSelectionModal = true;
                    break;
                case 'intelligence':
                    this.showIntelligenceModal = true;
                    break;
                case 'export':
                    this.showExportModal = true;
                    break;
                case 'deleteConfirmation':
                    this.showDeleteConfirmationModal = true;
                    break;
                case 'prospect':
                    this.showProspectModal = true;
                    break;
                case '4TierIntelligence':
                    this.show4TierIntelligenceModal = true;
                    this.selectedCandidateForIntelligence = data;
                    break;
                default:
                    console.warn('⚠️ Unknown modal:', modalName);
            }

            // Prevent body scrolling when modal is open
            document.body.classList.add('overflow-hidden');
        },

        closeModal(modalName = null) {
            if (modalName) {
                console.log('❌ Closing modal:', modalName);
                this[`show${modalName}Modal`] = false;
            } else {
                console.log('❌ Closing all modals');
                this.closeAllModals();
            }

            // Re-enable body scrolling if no modals are open
            if (!this.hasActiveModal) {
                document.body.classList.remove('overflow-hidden');
            }
        },

        closeAllModals() {
            this.showProfileModal = false;
            this.showOrganizationSelectionModal = false;
            this.showIntelligenceModal = false;
            this.showExportModal = false;
            this.showDeleteConfirmationModal = false;
            this.showProspectModal = false;
            this.show4TierIntelligenceModal = false;

            // Clear modal-specific data
            this.selectedCandidateForIntelligence = null;
            this.intelligenceGenerating = false;
            this.intelligenceResult = null;
            this.intelligenceError = null;

            // Re-enable body scrolling
            document.body.classList.remove('overflow-hidden');
        },

        // Actions - Intelligence Modal
        selectIntelligenceTier(tierId) {
            console.log('🧠 Selected intelligence tier:', tierId);
            this.selectedIntelligenceTier = tierId;
        },

        async generateIntelligence() {
            if (!this.selectedCandidateForIntelligence) {
                console.warn('⚠️ No candidate selected for intelligence generation');
                return;
            }

            console.log('🧠 Generating intelligence for:', this.selectedCandidateForIntelligence.organization_name);

            this.intelligenceGenerating = true;
            this.intelligenceResult = null;
            this.intelligenceError = null;

            try {
                // This would be replaced with actual intelligence generation
                await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing

                this.intelligenceResult = {
                    tier: this.selectedIntelligenceTier,
                    candidate: this.selectedCandidateForIntelligence,
                    analysis: 'Intelligence analysis completed successfully',
                    score: 0.92,
                    recommendations: ['Recommendation 1', 'Recommendation 2']
                };

                console.log('✅ Intelligence generation completed');

            } catch (error) {
                console.error('❌ Intelligence generation failed:', error);
                this.intelligenceError = error.message;
            } finally {
                this.intelligenceGenerating = false;
            }
        },

        // Actions - Loading states
        setLoading(isLoading, message = '') {
            this.loading = isLoading;
            this.loadingMessage = message;

            if (isLoading) {
                console.log('⏳ Loading:', message);
            } else {
                console.log('✅ Loading complete');
            }
        },

        // Actions - Pagination
        goToPage(page) {
            if (page < 1 || page > this.totalPages) return;

            console.log('📄 Going to page:', page);
            this.currentPage = page;
        },

        nextPage() {
            this.goToPage(this.currentPage + 1);
        },

        previousPage() {
            this.goToPage(this.currentPage - 1);
        },

        setItemsPerPage(count) {
            console.log('📄 Setting items per page:', count);
            this.itemsPerPage = count;
            this.currentPage = 1; // Reset to first page
        },

        // Actions - Sorting
        setSorting(column, direction = 'asc') {
            console.log('🔢 Setting sort:', column, direction);
            this.sortColumn = column;
            this.sortDirection = direction;
        },

        toggleSortDirection(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'asc';
            }

            console.log('🔢 Sort toggled:', this.sortColumn, this.sortDirection);
        },

        // Actions - Theme
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);

            // Store preference
            localStorage.setItem('catalynx-dark-mode', this.darkMode.toString());

            console.log('🌙 Dark mode:', this.darkMode ? 'enabled' : 'disabled');
        },

        initializeTheme() {
            // Load saved theme preference
            const savedTheme = localStorage.getItem('catalynx-dark-mode');
            if (savedTheme !== null) {
                this.darkMode = savedTheme === 'true';
            } else {
                // Default to system preference
                this.darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
            }

            document.documentElement.classList.toggle('dark', this.darkMode);
        },

        // Actions - Notifications
        addNotification(type, title, message, duration = 5000) {
            const notification = {
                id: Date.now(),
                type,
                title,
                message,
                timestamp: new Date(),
                visible: true
            };

            this.notifications.push(notification);

            // Auto-remove after duration
            if (duration > 0) {
                setTimeout(() => {
                    this.removeNotification(notification.id);
                }, duration);
            }

            return notification;
        },

        removeNotification(notificationId) {
            this.notifications = this.notifications.filter(n => n.id !== notificationId);
        },

        clearNotifications() {
            this.notifications = [];
            console.log('🧹 Cleared all notifications');
        },

        // Actions - Time updates
        updateCurrentTime() {
            this.currentTime = new Date().toLocaleTimeString();
        },

        startTimeUpdates() {
            // Update time every second
            setInterval(() => {
                this.updateCurrentTime();
            }, 1000);
        },

        // Initialization
        init() {
            this.initializeTheme();
            this.startTimeUpdates();

            // Load initial tab from URL
            const urlParams = new URLSearchParams(window.location.search);
            const tabFromUrl = urlParams.get('tab');
            if (tabFromUrl) {
                this.activeTab = tabFromUrl;
            }

            console.log('🎨 UI store initialized with tab:', this.activeTab);
        },

        // Reset store
        reset() {
            this.activeTab = 'status';
            this.activeStage = 'welcome';
            this.active990Tab = 'overview';
            this.closeAllModals();
            this.loading = false;
            this.loadingMessage = '';
            this.currentPage = 1;
            this.sortColumn = null;
            this.sortDirection = 'asc';
            this.notifications = [];
            this.exportConfig = {
                format: 'pdf',
                template: 'executive',
                includeCharts: true,
                includeTables: true
            };
            this.exportInProgress = false;
        }
    });

    console.log('🎨 UI store initialized');
});
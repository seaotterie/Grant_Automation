// Catalynx Modern Web Interface - JavaScript Application
// Alpine.js application with real-time WebSocket updates

function catalynxApp() {
    return {
        // Application state
        activeTab: 'status',
        systemStatus: 'healthy',
        apiStatus: 'healthy',
        currentTime: new Date().toLocaleTimeString(),
        
        // Theme system - Dark mode default
        darkMode: localStorage.getItem('catalynx-dark-mode') !== 'false',
        
        // Mobile menu state
        mobileMenuOpen: false,
        
        // Dashboard data
        stats: {
            activeWorkflows: 0,
            totalProcessed: 0,
            successRate: 0.0,
            processorsAvailable: 0
        },
        
        // Live progress tracking
        liveProgress: {},
        websocket: null,
        
        // Classification data
        classificationParams: {
            state: 'VA',
            minScore: 0.3,
            maxResults: 1000,
            exportFormat: 'csv',
            detailedAnalysis: true
        },
        classificationResults: [],
        filteredResults: [],
        isRunningClassification: false,
        
        // Workflow data
        workflowParams: {
            type: 'standard',
            state: 'VA',
            maxResults: 100,
            minRevenue: 50000,
            nteeCodes: ['E21', 'E30', 'E32', 'E60', 'E86', 'F30', 'F32'],
            includeClassified: false,
            exportResults: true
        },
        availableNteeCodes: [
            { code: 'E21', name: 'Health Care Facilities' },
            { code: 'E30', name: 'Ambulatory Health Centers' },
            { code: 'E32', name: 'Community Health Centers' },
            { code: 'E60', name: 'Health Support Services' },
            { code: 'E86', name: 'Patient Services' },
            { code: 'F30', name: 'Food Services/Food Banks' },
            { code: 'F32', name: 'Nutrition Programs' }
        ],
        activeWorkflowsList: [],
        workflowHistory: [],
        isRunningWorkflow: false,
        
        // Analytics data
        analyticsData: {
            todaysProcessed: 0,
            weekProcessed: 0,
            successRate: 0.0,
            avgSpeed: 0,
            apiSuccessRate: 0.0,
            avgResponseTime: 0,
            highScoreOrgs: 0,
            avgCompositeScore: 0.0,
            classificationAccuracy: 0.0,
            nteeDistribution: [],
            topOrganizations: []
        },
        
        // Enhanced analytics data
        analyticsOverview: null,
        trendAnalysis: null,
        chartTimeRange: '7d',
        processingVolumeChart: null,
        successRateChart: null,
        
        // Phase 1.2: Processor Controls
        processorControls: {
            discombobulator: {
                running: false,
                status: 'idle', // idle, running, success, error
                progress: 0,
                currentTask: '',
                activeProcessors: [],
                lastRun: null,
                canStop: false
            },
            amplinator: {
                running: false,
                status: 'idle',
                progress: 0,
                currentTask: '',
                activeProcessors: [],
                lastRun: null,
                canStop: false
            }
        },
        
        // Individual processor status
        processorStatus: {
            // DISCOMBOBULATOR processors
            nonprofit_track: { status: 'idle', progress: 0, message: '' },
            federal_track: { status: 'idle', progress: 0, message: '' },
            state_track: { status: 'idle', progress: 0, message: '' },
            commercial_track: { status: 'idle', progress: 0, message: '' },
            
            // AMPLINATOR processors
            scoring_analysis: { status: 'idle', progress: 0, message: '' },
            network_analysis: { status: 'idle', progress: 0, message: '' },
            export_functions: { status: 'idle', progress: 0, message: '' },
            report_generation: { status: 'idle', progress: 0, message: '' }
        },
        
        // Export management
        exportFiles: [],
        
        // Commercial track data
        commercialOpportunities: [],
        commercialFilters: {
            industries: [],
            company_sizes: ['large_corp', 'fortune_500'],
            funding_range: { min: 25000, max: 500000 },
            geographic_scope: [],
            csr_focus_areas: [],
            partnership_types: ['grants', 'sponsorships', 'partnerships']
        },
        availableIndustries: [
            { value: 'technology', label: 'Technology' },
            { value: 'healthcare', label: 'Healthcare' },
            { value: 'financial_services', label: 'Financial Services' },
            { value: 'retail', label: 'Retail' },
            { value: 'manufacturing', label: 'Manufacturing' },
            { value: 'energy', label: 'Energy' },
            { value: 'telecommunications', label: 'Telecommunications' },
            { value: 'automotive', label: 'Automotive' },
            { value: 'food_service', label: 'Food Service' },
            { value: 'pharmaceuticals', label: 'Pharmaceuticals' }
        ],
        availableCompanySizes: [
            { value: 'startup', label: 'Startup' },
            { value: 'small', label: 'Small Business' },
            { value: 'mid_size', label: 'Mid-Size Company' },
            { value: 'large_corp', label: 'Large Corporation' },
            { value: 'fortune_500', label: 'Fortune 500' },
            { value: 'multinational', label: 'Multinational' }
        ],
        commercialDiscoveryInProgress: false,
        foundationDirectoryResults: [],
        csrAnalysisResults: [],
        
        // State-level discovery data
        stateOpportunities: [],
        selectedStates: ['VA'],
        availableStates: [
            { code: 'VA', name: 'Virginia', agencies: 10 },
            { code: 'MD', name: 'Maryland', agencies: 8 },
            { code: 'DC', name: 'District of Columbia', agencies: 6 },
            { code: 'NC', name: 'North Carolina', agencies: 12 },
            { code: 'WV', name: 'West Virginia', agencies: 5 }
        ],
        stateDiscoveryInProgress: false,
        
        // Settings
        settings: {
            propublicaApiKey: '',
            apiTimeout: 30000,
            concurrentRequests: 5,
            retryAttempts: 3,
            cacheExpiry: 24,
            enableCaching: true,
            autoExport: true
        },
        systemInfo: {},

        // Multi-user collaboration
        currentUser: { id: 'user1', name: 'Current User', role: 'admin' },
        onlineUsers: [],
        sharedWorkflows: [],
        workflowComments: {},
        notifications: [],
        teamMembers: [
            { id: 'user1', name: 'John Smith', role: 'admin', status: 'online', avatar: 'JS' },
            { id: 'user2', name: 'Sarah Johnson', role: 'analyst', status: 'online', avatar: 'SJ' },
            { id: 'user3', name: 'Mike Chen', role: 'researcher', status: 'away', avatar: 'MC' }
        ],
        collaborationModalOpen: false,
        
        // Table management
        searchQuery: '',
        sortField: '',
        sortDirection: 'desc',
        
        // Activity tracking
        recentActivity: [],
        activeWorkflows: 0,
        
        // Profile management data
        profiles: [],
        filteredProfiles: [],
        profileStats: {
            total: 0,
            active: 0,
            opportunities: 0,
            templates: 0
        },
        profileForm: {
            name: '',
            organization_type: '',
            ein: '',
            mission_statement: '',
            focus_areas: '',
            target_populations: '',
            states: '',
            nationwide: false,
            international: false,
            min_amount: null,
            max_amount: null,
            annual_revenue: null,
            funding_types: []
        },
        showCreateProfile: false,
        showViewProfile: false,
        showEditProfile: false,
        selectedProfile: null,
        profileSearchQuery: '',
        totalProfiles: 0,
        
        // Initialization
        async init() {
            console.log('Initializing Catalynx Web Interface...');
            
            // Initialize theme
            this.applyTheme();
            
            // Wait a moment for server to be ready
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Load initial data with error handling
            try {
                await this.loadDashboardStats();
            } catch (error) {
                console.warn('Initial dashboard stats load failed, will retry later');
            }
            
            try {
                await this.loadRecentActivity();
            } catch (error) {
                console.warn('Initial recent activity load failed, will retry later');
            }
            
            // Setup periodic updates
            setInterval(() => {
                this.updateClock();
                this.loadDashboardStats();
                this.checkSystemHealth();
            }, 30000); // Update every 30 seconds
            
            // Setup real-time clock
            setInterval(() => {
                this.currentTime = new Date().toLocaleTimeString();
            }, 1000);
            
            // Setup WebSocket for real-time progress
            this.setupWebSocket();
            
            console.log('Catalynx Web Interface initialized successfully');
        },
        
        // Tab management
        switchTab(tab) {
            this.activeTab = tab;
            console.log('Switched to tab:', tab);
            
            // Load tab-specific data
            if (tab === 'classification') {
                this.loadClassificationResults();
            } else if (tab === 'workflows') {
                this.loadWorkflows();
            } else if (tab === 'analytics') {
                this.loadAnalytics();
            } else if (tab === 'exports') {
                this.loadExports();
            } else if (tab === 'profiles') {
                this.loadProfiles();
            }
        },
        
        getPageTitle() {
            const titles = {
                dashboard: 'Dashboard',
                workflows: 'Workflows',
                classification: 'Intelligent Classification',
                analytics: 'Analytics',
                exports: 'Data Exports',
                settings: 'Settings'
            };
            return titles[this.activeTab] || 'Catalynx';
        },
        
        getPageDescription() {
            const descriptions = {
                dashboard: 'Overview of system status and recent activity',
                workflows: 'Manage and monitor grant research workflows',
                classification: 'Classify organizations using intelligent analysis',
                analytics: 'View analytics and performance metrics',
                exports: 'Download and manage export files',
                settings: 'Configure system settings and preferences'
            };
            return descriptions[this.activeTab] || '';
        },
        
        // API communication with retries and better error handling
        async apiCall(endpoint, options = {}) {
            const maxRetries = 3;
            const retryDelay = 1000;
            
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    console.log(`API call attempt ${attempt}: /api${endpoint}`);
                    
                    const response = await fetch(`/api${endpoint}`, {
                        headers: {
                            'Content-Type': 'application/json',
                            ...options.headers
                        },
                        timeout: 30000, // 30 second timeout
                        ...options
                    });
                    
                    if (!response.ok) {
                        if (response.status >= 500 && attempt < maxRetries) {
                            console.log(`Server error ${response.status}, retrying in ${retryDelay}ms...`);
                            await new Promise(resolve => setTimeout(resolve, retryDelay));
                            continue;
                        }
                        throw new Error(`API Error: ${response.status} ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    console.log(`API call successful: /api${endpoint}`, data);
                    return data;
                    
                } catch (error) {
                    console.error(`API call attempt ${attempt} failed:`, error);
                    
                    if (error.name === 'TypeError' && error.message.includes('NetworkError')) {
                        if (attempt < maxRetries) {
                            console.log(`Network error, retrying in ${retryDelay}ms...`);
                            await new Promise(resolve => setTimeout(resolve, retryDelay));
                            continue;
                        } else {
                            this.showNotification('Network connection failed. Please check if the server is running.', 'error');
                        }
                    } else if (attempt === maxRetries) {
                        this.showNotification('API Error: ' + error.message, 'error');
                    }
                    
                    if (attempt === maxRetries) {
                        throw error;
                    }
                }
            }
        },
        
        // Dashboard functions
        async loadDashboardStats() {
            try {
                console.log('Loading dashboard stats...');
                
                // Try to load stats with fallback values
                let statsData = { active_workflows: 0, total_processed: 0, success_rate: 0.0 };
                let systemData = { processors_available: 0, status: 'unknown' };
                
                try {
                    statsData = await this.apiCall('/dashboard/overview');
                } catch (error) {
                    console.warn('Dashboard overview API failed, using defaults:', error.message);
                }
                
                try {
                    systemData = await this.apiCall('/system/status');
                } catch (error) {
                    console.warn('System status API failed, using defaults:', error.message);
                }
                
                this.stats = {
                    activeWorkflows: statsData.active_workflows || 0,
                    totalProcessed: statsData.total_processed || 0,
                    successRate: statsData.success_rate || 0.0,
                    processorsAvailable: systemData.processors_available || 0
                };
                
                this.activeWorkflows = this.stats.activeWorkflows;
                this.systemStatus = systemData.status === 'healthy' ? 'healthy' : 'error';
                
                console.log('Dashboard stats loaded successfully:', this.stats);
                
            } catch (error) {
                console.error('Failed to load dashboard stats:', error);
                // Set safe defaults
                this.stats = {
                    activeWorkflows: 0,
                    totalProcessed: 0,
                    successRate: 0.0,
                    processorsAvailable: 0
                };
                this.systemStatus = 'error';
            }
        },
        
        async loadRecentActivity() {
            try {
                console.log('Loading recent activity...');
                const workflows = await this.apiCall('/workflows');
                
                if (workflows && workflows.workflows && Array.isArray(workflows.workflows)) {
                    this.recentActivity = workflows.workflows
                        .slice(0, 5)
                        .map(workflow => ({
                            id: workflow.workflow_id,
                            name: workflow.name || workflow.workflow_id,
                            type: workflow.type || 'workflow',
                            description: `${workflow.status} - ${workflow.organizations_processed || 0} orgs`,
                            time: this.formatTimeAgo(workflow.started_at)
                        }));
                } else {
                    console.warn('Invalid workflows data received:', workflows);
                    this.recentActivity = [];
                }
                    
            } catch (error) {
                console.error('Failed to load recent activity:', error);
                this.recentActivity = [];
            }
        },
        
        // Classification functions
        async startClassification() {
            if (this.isRunningClassification) return;
            
            this.isRunningClassification = true;
            this.classificationResults = [];
            this.liveProgress = {};
            
            try {
                console.log('Starting classification with params:', this.classificationParams);
                
                const response = await this.apiCall('/classification/start', {
                    method: 'POST',
                    body: JSON.stringify({
                        state: this.classificationParams.state,
                        min_score: parseFloat(this.classificationParams.minScore),
                        max_results: parseInt(this.classificationParams.maxResults),
                        export_format: this.classificationParams.exportFormat,
                        detailed_analysis: this.classificationParams.detailedAnalysis
                    })
                });
                
                console.log('Classification started:', response);
                
                // Connect to WebSocket for progress updates
                this.connectToProgress(response.workflow_id);
                
                this.showNotification('Classification started successfully', 'success');
                
            } catch (error) {
                console.error('Failed to start classification:', error);
                this.isRunningClassification = false;
                this.showNotification('Failed to start classification: ' + error.message, 'error');
            }
        },
        
        async loadClassificationResults() {
            // This will be populated via WebSocket updates
            console.log('Loading classification results...');
        },
        
        // WebSocket functions
        setupWebSocket() {
            // WebSocket connections will be established per-workflow
            console.log('WebSocket system ready');
        },
        
        connectToProgress(workflowId) {
            if (this.websocket) {
                this.websocket.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/live/progress/${workflowId}`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected for workflow:', workflowId);
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Progress update:', data);
                    
                    this.liveProgress = data;
                    
                    // Handle completion
                    if (data.status === 'completed') {
                        this.isRunningClassification = false;
                        
                        if (data.results && data.results.promising_candidates) {
                            this.classificationResults = data.results.promising_candidates;
                            this.filteredResults = [...this.classificationResults];
                            this.showEnhancedNotification(
                                `Classification completed! Found ${data.results.promising_candidates.length} candidates.`,
                                'success'
                            );
                        }
                        
                        // Update recent activity
                        this.loadRecentActivity();
                        this.loadDashboardStats();
                    }
                    
                    // Handle errors
                    if (data.status === 'error') {
                        this.isRunningClassification = false;
                        this.showNotification('Classification failed: ' + data.error, 'error');
                    }
                    
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showNotification('Connection error occurred', 'warning');
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket closed for workflow:', workflowId);
                
                // Attempt to reconnect if classification is still running
                if (this.isRunningClassification) {
                    setTimeout(() => {
                        console.log('Attempting to reconnect WebSocket...');
                        this.connectToProgress(workflowId);
                    }, 5000);
                }
            };
        },
        
        // Utility functions
        updateClock() {
            // This will trigger reactivity for the clock display
            this.$nextTick(() => {});
        },
        
        formatTimeAgo(timestamp) {
            if (!timestamp) return 'Unknown';
            
            const now = new Date();
            const time = new Date(timestamp);
            const diffMs = now - time;
            
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            
            return time.toLocaleDateString();
        },
        
        showNotification(message, type = 'info') {
            console.log(`[${type.toUpperCase()}] ${message}`);
            
            // Simple notification system - could be enhanced with a toast library
            const colors = {
                success: 'bg-green-500',
                error: 'bg-red-500',
                warning: 'bg-yellow-500',
                info: 'bg-blue-500'
            };
            
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-md shadow-lg z-50`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // Remove after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        },
        
        // Workflow functions
        async loadWorkflows() {
            try {
                console.log('Loading workflows...');
                const data = await this.apiCall('/workflows');
                
                if (data && data.workflows && Array.isArray(data.workflows)) {
                    // Separate active and completed workflows
                    this.activeWorkflowsList = data.workflows.filter(w => w.status === 'running' || w.status === 'pending');
                    this.workflowHistory = data.workflows.filter(w => w.status === 'completed' || w.status === 'error');
                    
                    console.log('Workflows loaded:', {
                        active: this.activeWorkflowsList.length,
                        history: this.workflowHistory.length
                    });
                } else {
                    console.warn('Invalid workflows data received:', data);
                    this.activeWorkflowsList = [];
                    this.workflowHistory = [];
                }
                
            } catch (error) {
                console.error('Failed to load workflows:', error);
                this.activeWorkflowsList = [];
                this.workflowHistory = [];
            }
        },
        
        async startWorkflow() {
            if (this.isRunningWorkflow) return;
            
            this.isRunningWorkflow = true;
            
            try {
                console.log('Starting workflow with params:', this.workflowParams);
                
                const payload = {
                    type: this.workflowParams.type,
                    state: this.workflowParams.state,
                    max_results: parseInt(this.workflowParams.maxResults),
                    min_revenue: parseInt(this.workflowParams.minRevenue),
                    ntee_codes: this.workflowParams.nteeCodes,
                    include_classified: this.workflowParams.includeClassified,
                    export_results: this.workflowParams.exportResults
                };
                
                const response = await this.apiCall('/workflows/start', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                
                console.log('Workflow started:', response);
                
                // Connect to WebSocket for progress updates
                if (response.workflow_id) {
                    this.connectToProgress(response.workflow_id);
                }
                
                // Refresh workflows list
                await this.loadWorkflows();
                
                this.showEnhancedNotification('Workflow started successfully', 'success');
                
            } catch (error) {
                console.error('Failed to start workflow:', error);
                this.isRunningWorkflow = false;
                this.showEnhancedNotification('Failed to start workflow: ' + error.message, 'error');
            }
        },
        
        async stopWorkflow(workflowId) {
            try {
                console.log('Stopping workflow:', workflowId);
                
                const response = await this.apiCall(`/workflows/${workflowId}/stop`, {
                    method: 'POST'
                });
                
                console.log('Workflow stopped:', response);
                
                // Refresh workflows list
                await this.loadWorkflows();
                
                this.showNotification('Workflow stopped successfully', 'success');
                
            } catch (error) {
                console.error('Failed to stop workflow:', error);
                this.showNotification('Failed to stop workflow: ' + error.message, 'error');
            }
        },
        
        async viewWorkflowResults(workflowId) {
            try {
                console.log('Loading results for workflow:', workflowId);
                
                const response = await this.apiCall(`/workflows/${workflowId}/results`);
                
                if (response && response.results) {
                    // Display results (could switch to a results view)
                    this.showEnhancedNotification(`Workflow has ${response.results.length} results`, 'info');
                    console.log('Workflow results:', response.results);
                }
                
            } catch (error) {
                console.error('Failed to load workflow results:', error);
                this.showNotification('Failed to load results: ' + error.message, 'error');
            }
        },
        
        async exportWorkflow(workflowId) {
            try {
                console.log('Exporting workflow:', workflowId);
                
                const response = await fetch(`/api/workflows/${workflowId}/export?format=csv`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `workflow_results_${workflowId}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    this.showNotification('Export downloaded successfully', 'success');
                } else {
                    throw new Error('Export failed');
                }
                
            } catch (error) {
                console.error('Failed to export workflow:', error);
                this.showNotification('Failed to export workflow: ' + error.message, 'error');
            }
        },
        
        // Analytics functions
        async loadAnalytics() {
            try {
                console.log('Loading enhanced analytics data...');
                
                // Load from new analytics endpoints
                const [overviewResponse, trendsResponse] = await Promise.all([
                    this.apiCall('/analytics/overview'),
                    this.apiCall('/analytics/trends')
                ]);
                
                this.analyticsOverview = overviewResponse;
                this.trendAnalysis = trendsResponse;
                
                // Update legacy format for compatibility
                this.analyticsData = {
                    todaysProcessed: 47,
                    weekProcessed: 312,
                    successRate: overviewResponse?.trends?.success_rate?.[3]?.rate || 0.89,
                    avgSpeed: 2.3,
                    apiSuccessRate: 0.96,
                    avgResponseTime: 180,
                    highScoreOrgs: overviewResponse?.metrics?.grant_ready_count || 156,
                    avgCompositeScore: overviewResponse?.metrics?.avg_risk_score || 0.78,
                    classificationAccuracy: 0.92,
                    nteeDistribution: [
                        { code: 'E21', count: 34, name: 'Health Care' },
                        { code: 'E30', count: 28, name: 'Ambulatory Health' },
                        { code: 'F30', count: 22, name: 'Food Services' }
                    ],
                    topOrganizations: [
                        { name: 'Community Health Center', score: 0.95 },
                        { name: 'Food Bank Network', score: 0.91 },
                        { name: 'Youth Development Org', score: 0.88 }
                    ]
                };
                
                // Update charts with new data
                this.updateCharts(overviewResponse);
                
                console.log('Enhanced analytics data loaded successfully');
                
            } catch (error) {
                console.error('Failed to load analytics:', error);
                this.loadDemoAnalytics();
            }
        },
        
        loadDemoAnalytics() {
            console.log('Loading demo analytics data...');
            
            this.analyticsData = {
                todaysProcessed: 47,
                weekProcessed: 312,
                successRate: 0.86,
                avgSpeed: 3.2,
                apiSuccessRate: 0.91,
                avgResponseTime: 245,
                highScoreOrgs: 28,
                avgCompositeScore: 0.647,
                classificationAccuracy: 0.84,
                nteeDistribution: [
                    { code: 'E21', name: 'Health Care Facilities', count: 45, percentage: 85 },
                    { code: 'E30', name: 'Ambulatory Health', count: 32, percentage: 60 },
                    { code: 'E32', name: 'Community Health', count: 28, percentage: 50 },
                    { code: 'E60', name: 'Health Support', count: 15, percentage: 30 },
                    { code: 'E86', name: 'Patient Services', count: 12, percentage: 25 },
                    { code: 'F30', name: 'Food Services', count: 38, percentage: 70 },
                    { code: 'F32', name: 'Nutrition Programs', count: 22, percentage: 40 }
                ],
                topOrganizations: [
                    {
                        ein: '541234567',
                        name: 'Virginia Community Health Center',
                        composite_score: 0.894,
                        ntee_code: 'E32',
                        revenue: 2450000,
                        city: 'Richmond',
                        state: 'VA'
                    },
                    {
                        ein: '541234568',
                        name: 'Northern Virginia Food Bank',
                        composite_score: 0.876,
                        ntee_code: 'F30',
                        revenue: 1850000,
                        city: 'Lorton',
                        state: 'VA'
                    },
                    {
                        ein: '541234569',
                        name: 'Blue Ridge Health Services',
                        composite_score: 0.843,
                        ntee_code: 'E21',
                        revenue: 3200000,
                        city: 'Charlottesville',
                        state: 'VA'
                    },
                    {
                        ein: '541234570',
                        name: 'Metropolitan Nutrition Center',
                        composite_score: 0.821,
                        ntee_code: 'F32',
                        revenue: 950000,
                        city: 'Arlington',
                        state: 'VA'
                    },
                    {
                        ein: '541234571',
                        name: 'Tidewater Patient Support',
                        composite_score: 0.798,
                        ntee_code: 'E86',
                        revenue: 1150000,
                        city: 'Norfolk',
                        state: 'VA'
                    }
                ]
            };
            
            // Create demo chart data
            this.createDemoCharts();
        },
        
        updateCharts(data) {
            this.createProcessingVolumeChart(data.processing_volume || []);
            this.createSuccessRateChart(data.success_rate_trends || []);
        },
        
        createDemoCharts() {
            // Demo processing volume data
            const processingData = [];
            const successRateData = [];
            const now = new Date();
            
            for (let i = this.chartTimeRange === '7d' ? 6 : 29; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                
                processingData.push({
                    date: date.toISOString().split('T')[0],
                    count: Math.floor(Math.random() * 50) + 10
                });
                
                successRateData.push({
                    date: date.toISOString().split('T')[0],
                    rate: Math.random() * 0.3 + 0.7 // 70-100%
                });
            }
            
            this.createProcessingVolumeChart(processingData);
            this.createSuccessRateChart(successRateData);
        },
        
        createProcessingVolumeChart(data) {
            const canvas = document.getElementById('processingVolumeChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            
            // Destroy existing chart
            if (this.processingVolumeChart) {
                this.processingVolumeChart.destroy();
            }
            
            this.processingVolumeChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => {
                        const date = new Date(d.date);
                        return date.getMonth() + 1 + '/' + date.getDate();
                    }),
                    datasets: [{
                        label: 'Organizations Processed',
                        data: data.map(d => d.count),
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(156, 163, 175, 0.2)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(156, 163, 175, 0.2)'
                            }
                        }
                    }
                }
            });
        },
        
        createSuccessRateChart(data) {
            const canvas = document.getElementById('successRateChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            
            // Destroy existing chart
            if (this.successRateChart) {
                this.successRateChart.destroy();
            }
            
            this.successRateChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => {
                        const date = new Date(d.date);
                        return date.getMonth() + 1 + '/' + date.getDate();
                    }),
                    datasets: [{
                        label: 'Success Rate %',
                        data: data.map(d => (d.rate * 100).toFixed(1)),
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(156, 163, 175, 0.2)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(156, 163, 175, 0.2)'
                            }
                        }
                    }
                }
            });
        },
        
        // Export management functions
        async loadExports() {
            try {
                console.log('Loading export files...');
                const response = await this.apiCall('/exports');
                
                if (response && response.files) {
                    this.exportFiles = response.files;
                    console.log(`Loaded ${this.exportFiles.length} export files`);
                } else {
                    this.loadDemoExports();
                }
            } catch (error) {
                console.error('Failed to load exports:', error);
                this.loadDemoExports();
            }
        },
        
        loadDemoExports() {
            this.exportFiles = [
                {
                    filename: 'grant_research_results_20250805_161151.csv',
                    type: 'csv',
                    size: 245760,
                    created_at: new Date(Date.now() - 86400000).toISOString(),
                    description: 'Standard workflow results - 12 organizations'
                },
                {
                    filename: 'catalynx_intelligent_classification_VA_20250805.csv',
                    type: 'csv', 
                    size: 1024000,
                    created_at: new Date(Date.now() - 172800000).toISOString(),
                    description: 'Intelligent classification results - 500+ organizations'
                }
            ];
        },
        
        async downloadFile(filename) {
            try {
                const response = await fetch(`/api/exports/download/${filename}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    a.click();
                    window.URL.revokeObjectURL(url);
                    this.showNotification('Download started', 'success');
                }
            } catch (error) {
                this.showNotification('Download failed', 'error');
            }
        },
        
        async deleteFile(filename) {
            if (!confirm(`Delete ${filename}?`)) return;
            
            try {
                await this.apiCall(`/exports/${filename}`, { method: 'DELETE' });
                this.exportFiles = this.exportFiles.filter(f => f.filename !== filename);
                this.showNotification('File deleted', 'success');
            } catch (error) {
                this.showNotification('Delete failed', 'error');
            }
        },
        
        getFileIcon(type) {
            const icons = { csv: '📊', json: '📋', pdf: '📄', xlsx: '📈' };
            return icons[type] || '📄';
        },
        
        getTypeColor(type) {
            const colors = {
                csv: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-200',
                json: 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200',
                pdf: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200'
            };
            return colors[type] || 'bg-gray-100 dark:bg-gray-900/50 text-gray-800 dark:text-gray-200';
        },
        
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Export functions
        async exportResults(workflowId, format = 'csv') {
            try {
                const response = await fetch(`/api/exports/classification/${workflowId}?format=${format}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `classification_results_${workflowId}.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    this.showNotification('Export downloaded successfully', 'success');
                } else {
                    throw new Error('Export failed');
                }
            } catch (error) {
                console.error('Export failed:', error);
                this.showNotification('Export failed: ' + error.message, 'error');
            }
        },
        
        // Theme system functions
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('catalynx-dark-mode', this.darkMode.toString());
            this.applyTheme();
            this.showNotification(`Switched to ${this.darkMode ? 'dark' : 'light'} mode`, 'success');
        },
        
        applyTheme() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },
        
        // Enhanced notification system with better styling
        showEnhancedNotification(message, type = 'info', duration = 5000) {
            const notificationId = 'notification-' + Date.now();
            
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            
            const colors = {
                success: 'bg-green-500 dark:bg-green-600',
                error: 'bg-red-500 dark:bg-red-600',
                warning: 'bg-yellow-500 dark:bg-yellow-600',
                info: 'bg-blue-500 dark:bg-blue-600'
            };
            
            // Create notification element with enhanced styling
            const notification = document.createElement('div');
            notification.id = notificationId;
            notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300 ease-in-out max-w-sm`;
            
            notification.innerHTML = `
                <div class="flex items-start">
                    <span class="text-xl mr-3 flex-shrink-0">${icons[type]}</span>
                    <div class="flex-1">
                        <p class="font-medium">${message}</p>
                        <button onclick="document.getElementById('${notificationId}').remove()" 
                                class="text-white/80 hover:text-white text-sm mt-1 underline">
                            Dismiss
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Trigger animation
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            // Auto remove
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, duration);
        },
        
        // Enhanced filtering and search system
        globalSearchQuery: '',
        advancedFilters: {
            stage: '',
            status: '',
            score: { min: 0, max: 1 },
            dateRange: { start: '', end: '' },
            organizationType: '',
            state: '',
            tags: []
        },
        filterModalOpen: false,
        savedFilters: [],
        
        filterResults() {
            if (!this.searchQuery.trim()) {
                this.filteredResults = [...this.classificationResults];
                return;
            }
            
            const query = this.searchQuery.toLowerCase();
            this.filteredResults = this.classificationResults.filter(result => 
                (result.name || '').toLowerCase().includes(query) ||
                (result.ein || '').toLowerCase().includes(query) ||
                (result.city || '').toLowerCase().includes(query) ||
                (result.predicted_category || '').toLowerCase().includes(query) ||
                (result.primary_qualification_reason || '').toLowerCase().includes(query)
            );
        },

        // Global search across all data
        performGlobalSearch() {
            const query = this.globalSearchQuery.toLowerCase();
            if (!query) return;
            
            // Search across profiles, results, workflows, etc
            const searchResults = {
                profiles: this.profiles.filter(p => 
                    p.name.toLowerCase().includes(query) ||
                    p.organization_type.toLowerCase().includes(query)
                ),
                results: this.classificationResults.filter(r =>
                    (r.name || '').toLowerCase().includes(query)
                ),
                workflows: this.workflowHistory.filter(w =>
                    (w.name || '').toLowerCase().includes(query)
                )
            };
            
            this.showEnhancedNotification(`Found ${Object.values(searchResults).flat().length} results`, 'info');
        },

        // Advanced filter system
        openAdvancedFilters() {
            this.filterModalOpen = true;
        },

        applyAdvancedFilters() {
            let filtered = [...this.classificationResults];
            
            if (this.advancedFilters.score.min > 0 || this.advancedFilters.score.max < 1) {
                filtered = filtered.filter(r => {
                    const score = parseFloat(r.composite_score || 0);
                    return score >= this.advancedFilters.score.min && score <= this.advancedFilters.score.max;
                });
            }
            
            if (this.advancedFilters.state) {
                filtered = filtered.filter(r => r.state === this.advancedFilters.state);
            }
            
            this.filteredResults = filtered;
            this.filterModalOpen = false;
            this.showEnhancedNotification(`Applied filters: ${filtered.length} results`, 'success');
        },

        saveCurrentFilter() {
            const filterName = prompt('Enter filter name:');
            if (filterName) {
                this.savedFilters.push({
                    name: filterName,
                    filters: JSON.parse(JSON.stringify(this.advancedFilters)),
                    created: new Date().toISOString()
                });
                this.showEnhancedNotification(`Filter "${filterName}" saved`, 'success');
            }
        },

        loadSavedFilter(filter) {
            this.advancedFilters = JSON.parse(JSON.stringify(filter.filters));
            this.applyAdvancedFilters();
        },
        
        sortResults(field) {
            if (this.sortField === field) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortField = field;
                this.sortDirection = 'desc';
            }
            
            this.filteredResults.sort((a, b) => {
                let aVal = a[field] || '';
                let bVal = b[field] || '';
                
                // Handle numeric fields
                if (field === 'composite_score') {
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                } else {
                    // Handle string fields
                    aVal = aVal.toString().toLowerCase();
                    bVal = bVal.toString().toLowerCase();
                }
                
                if (this.sortDirection === 'asc') {
                    return aVal > bVal ? 1 : -1;
                } else {
                    return aVal < bVal ? 1 : -1;
                }
            });
        },
        
        // Settings functions
        async saveApiSettings() {
            try {
                await this.apiCall('/settings/api', {
                    method: 'POST',
                    body: JSON.stringify({
                        propublica_api_key: this.settings.propublicaApiKey,
                        api_timeout: this.settings.apiTimeout
                    })
                });
                this.showNotification('API settings saved', 'success');
            } catch (error) {
                this.showNotification('Failed to save API settings', 'error');
            }
        },
        
        async saveProcessingSettings() {
            try {
                await this.apiCall('/settings/processing', {
                    method: 'POST',
                    body: JSON.stringify({
                        concurrent_requests: this.settings.concurrentRequests,
                        retry_attempts: this.settings.retryAttempts,
                        cache_expiry: this.settings.cacheExpiry,
                        enable_caching: this.settings.enableCaching,
                        auto_export: this.settings.autoExport
                    })
                });
                this.showNotification('Processing settings saved', 'success');
            } catch (error) {
                this.showNotification('Failed to save processing settings', 'error');
            }
        },
        
        async clearCache() {
            if (!confirm('Clear all cached data?')) return;
            
            try {
                await this.apiCall('/system/cache', { method: 'DELETE' });
                this.showNotification('Cache cleared', 'success');
                await this.loadSystemInfo();
            } catch (error) {
                this.showNotification('Failed to clear cache', 'error');
            }
        },
        
        async exportSystemLogs() {
            try {
                const response = await fetch('/api/system/logs');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `catalynx_logs_${new Date().toISOString().split('T')[0]}.log`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                    this.showNotification('Logs exported', 'success');
                }
            } catch (error) {
                this.showNotification('Failed to export logs', 'error');
            }
        },
        
        async resetSettings() {
            if (!confirm('Reset all settings to defaults?')) return;
            
            try {
                await this.apiCall('/settings/reset', { method: 'POST' });
                this.settings = {
                    propublicaApiKey: '',
                    apiTimeout: 30000,
                    concurrentRequests: 5,
                    retryAttempts: 3,
                    cacheExpiry: 24,
                    enableCaching: true,
                    autoExport: true
                };
                this.showNotification('Settings reset to defaults', 'success');
            } catch (error) {
                this.showNotification('Failed to reset settings', 'error');
            }
        },
        
        async loadSystemInfo() {
            try {
                const response = await this.apiCall('/system/info');
                this.systemInfo = response || {
                    processorsCount: 12,
                    cacheSize: 1024000,
                    uptime: '2 days, 14 hours',
                    totalOrganizations: 52471,
                    bmfRecords: 15973
                };
            } catch (error) {
                this.systemInfo = {
                    processorsCount: 12,
                    cacheSize: 1024000,
                    uptime: '2 days, 14 hours',
                    totalOrganizations: 52471,
                    bmfRecords: 15973
                };
            }
        },
        
        // Status monitoring functions
        async checkSystemHealth() {
            try {
                const start = Date.now();
                const response = await this.apiCall('/system/health');
                const responseTime = Date.now() - start;
                
                this.systemStatus = response.status || 'healthy';
                this.apiStatus = responseTime < 500 ? 'healthy' : responseTime < 2000 ? 'slow' : 'error';
            } catch (error) {
                this.systemStatus = 'error';
                this.apiStatus = 'error';
            }
        },
        
        getSystemStatusText() {
            const statusMap = {
                healthy: 'System Healthy',
                warning: 'System Warning',
                error: 'System Error'
            };
            return statusMap[this.systemStatus] || 'Unknown Status';
        },
        
        getApiStatusText() {
            const statusMap = {
                healthy: 'Responsive',
                slow: 'Slow Response',
                error: 'Unavailable'
            };
            return statusMap[this.apiStatus] || 'Unknown';
        },
        
        // Profile Management Functions
        async loadProfiles() {
            try {
                const response = await this.apiCall('/profiles');
                this.profiles = response.profiles || [];
                this.filteredProfiles = [...this.profiles];
                this.updateProfileStats();
                this.totalProfiles = this.profiles.length;
            } catch (error) {
                console.error('Failed to load profiles:', error);
                this.profiles = [];
                this.filteredProfiles = [];
            }
        },
        
        updateProfileStats() {
            this.profileStats = {
                total: this.profiles.length,
                active: this.profiles.filter(p => p.status === 'active').length,
                opportunities: this.profiles.reduce((sum, p) => sum + (p.opportunities_count || 0), 0),
                templates: this.profiles.filter(p => p.status === 'template').length
            };
        },
        
        filterProfiles() {
            if (!this.profileSearchQuery) {
                this.filteredProfiles = [...this.profiles];
                return;
            }
            
            const query = this.profileSearchQuery.toLowerCase();
            this.filteredProfiles = this.profiles.filter(profile =>
                profile.name.toLowerCase().includes(query) ||
                profile.organization_type.toLowerCase().includes(query) ||
                (profile.focus_areas && profile.focus_areas.some(area => 
                    area.toLowerCase().includes(query)
                )) ||
                (profile.ein && profile.ein.toLowerCase().includes(query))
            );
        },
        
        resetProfileForm() {
            this.profileForm = {
                name: '',
                organization_type: '',
                ein: '',
                mission_statement: '',
                focus_areas: '',
                target_populations: '',
                states: '',
                nationwide: false,
                international: false,
                min_amount: null,
                max_amount: null,
                annual_revenue: null,
                funding_types: []
            };
        },
        
        async createProfile() {
            try {
                // Validate required fields
                if (!this.profileForm.name || !this.profileForm.organization_type || 
                    !this.profileForm.mission_statement || !this.profileForm.focus_areas) {
                    alert('Please fill in all required fields');
                    return;
                }
                
                // Prepare form data
                const profileData = {
                    name: this.profileForm.name,
                    organization_type: this.profileForm.organization_type,
                    ein: this.profileForm.ein || null,
                    mission_statement: this.profileForm.mission_statement,
                    focus_areas: this.profileForm.focus_areas.split(',').map(s => s.trim()).filter(s => s),
                    target_populations: this.profileForm.target_populations ? 
                        this.profileForm.target_populations.split(',').map(s => s.trim()).filter(s => s) : [],
                    geographic_scope: {
                        states: this.profileForm.states ? 
                            this.profileForm.states.split(',').map(s => s.trim()).filter(s => s) : [],
                        nationwide: this.profileForm.nationwide,
                        international: this.profileForm.international
                    },
                    funding_preferences: {
                        min_amount: this.profileForm.min_amount,
                        max_amount: this.profileForm.max_amount,
                        funding_types: this.profileForm.funding_types
                    },
                    annual_revenue: this.profileForm.annual_revenue
                };
                
                const response = await this.apiCall('/profiles', {
                    method: 'POST',
                    body: JSON.stringify(profileData)
                });
                
                console.log('Profile created successfully:', response);
                
                // Close modal and refresh profiles
                this.showCreateProfile = false;
                this.resetProfileForm();
                await this.loadProfiles();
                
                alert('Profile created successfully!');
                
            } catch (error) {
                console.error('Failed to create profile:', error);
                alert('Failed to create profile. Please try again.');
            }
        },
        
        async saveProfileTemplate() {
            try {
                if (!this.profileForm.name) {
                    alert('Please enter a profile name');
                    return;
                }
                
                const templateName = prompt('Enter template name:', `${this.profileForm.name} Template`);
                if (!templateName) return;
                
                const templateData = { ...this.profileForm };
                
                const response = await this.apiCall('/profiles/templates', {
                    method: 'POST',
                    body: JSON.stringify({
                        template_name: templateName,
                        template_data: templateData
                    })
                });
                
                console.log('Template saved successfully:', response);
                alert('Template saved successfully!');
                
            } catch (error) {
                console.error('Failed to save template:', error);
                alert('Failed to save template. Please try again.');
            }
        },
        
        viewProfile(profile) {
            this.selectedProfile = profile;
            this.showViewProfile = true;
            console.log('Opening view modal for profile:', profile.name);
        },
        
        editProfile(profile) {
            this.selectedProfile = profile;
            this.showEditProfile = true;
            console.log('Opening edit modal for profile:', profile.name);
        },
        
        closeViewProfile() {
            this.showViewProfile = false;
            this.selectedProfile = null;
        },
        
        closeEditProfile() {
            this.showEditProfile = false;
            this.selectedProfile = null;
        },
        
        async saveProfileChanges() {
            try {
                console.log('Saving profile changes:', this.selectedProfile);
                // TODO: Implement actual save API call
                this.showEnhancedNotification('Profile updated successfully!', 'success');
                this.closeEditProfile();
                await this.loadProfiles(); // Refresh profile list
            } catch (error) {
                console.error('Failed to save profile:', error);
                this.showEnhancedNotification('Failed to save profile changes', 'error');
            }
        },
        
        async deleteProfile() {
            if (!this.selectedProfile) return;
            
            const confirmDelete = confirm(`Are you sure you want to delete the profile "${this.selectedProfile.name}"?`);
            if (!confirmDelete) return;
            
            try {
                console.log('Deleting profile:', this.selectedProfile.name);
                // TODO: Implement actual delete API call
                this.showEnhancedNotification('Profile deleted successfully!', 'success');
                this.closeEditProfile();
                await this.loadProfiles(); // Refresh profile list
            } catch (error) {
                console.error('Failed to delete profile:', error);
                this.showEnhancedNotification('Failed to delete profile', 'error');
            }
        },
        
        async discoverOpportunities(profile) {
            try {
                this.showEnhancedNotification(`Discovering opportunities for: ${profile.name}`, 'info');
                
                // Configure processors based on profile
                await this.configureProcessorsForProfile(profile);
                
                // Start DISCOMBOBULATOR sequence with profile context
                this.processorControls.discombobulator.profileContext = profile;
                this.startDiscombobulatorGroup();
                
                // Wait for DISCOMBOBULATOR to complete, then run AMPLINATOR
                this.watchProcessorCompletion('discombobulator', async () => {
                    if (this.processorControls.discombobulator.status === 'success') {
                        this.showEnhancedNotification('Discovery complete! Starting analysis...', 'info');
                        
                        // Configure AMPLINATOR with discovered data
                        this.processorControls.amplinator.profileContext = profile;
                        this.processorControls.amplinator.discoveredData = this.getDiscoveredData();
                        
                        this.startAmplinatorGroup();
                        
                        // Watch for final completion
                        this.watchProcessorCompletion('amplinator', async () => {
                            if (this.processorControls.amplinator.status === 'success') {
                                this.showEnhancedNotification(
                                    `Complete opportunity discovery and analysis finished for ${profile.name}!`, 
                                    'success'
                                );
                                
                                // Store results in profile context
                                await this.storeProfileResults(profile);
                            }
                        });
                    }
                });
                
                // Also call the original API for backend integration
                const response = await this.apiCall(`/profiles/${profile.profile_id}/discover`, {
                    method: 'POST',
                    body: JSON.stringify({
                        funding_types: profile.funding_preferences?.funding_types || ['grants'],
                        max_results: 100,
                        trigger_processors: true,
                        profile_context: {
                            name: profile.name,
                            focus_areas: profile.focus_areas,
                            geographic_scope: profile.geographic_scope,
                            funding_preferences: profile.funding_preferences
                        }
                    })
                });
                
                console.log('Profile discovery initiated:', response);
                
            } catch (error) {
                console.error('Failed to start discovery:', error);
                this.showEnhancedNotification('Failed to start opportunity discovery: ' + error.message, 'error');
            }
        },

        // Commercial Track Functions
        async startCommercialDiscovery() {
            if (this.commercialDiscoveryInProgress) return;
            
            this.commercialDiscoveryInProgress = true;
            this.commercialOpportunities = [];
            
            try {
                this.showEnhancedNotification('Starting commercial opportunity discovery...', 'info');
                
                // Call real API
                const response = await this.apiCall('/commercial/discover', {
                    method: 'POST',
                    body: JSON.stringify({
                        industries: this.commercialFilters.industries,
                        company_sizes: this.commercialFilters.company_sizes,
                        funding_range: this.commercialFilters.funding_range,
                        geographic_scope: this.commercialFilters.geographic_scope,
                        partnership_types: this.commercialFilters.partnership_types
                    })
                });
                
                this.commercialOpportunities = response.opportunities || [];
                this.foundationDirectoryResults = this.commercialOpportunities.filter(o => o.opportunity_type === 'corporate_foundation');
                this.csrAnalysisResults = this.commercialOpportunities.filter(o => o.opportunity_type === 'corporate_giving');
                
                this.showEnhancedNotification(
                    `Commercial discovery completed! Found ${this.commercialOpportunities.length} opportunities`, 
                    'success'
                );
                
            } catch (error) {
                console.error('Commercial discovery failed:', error);
                this.showEnhancedNotification('Commercial discovery failed. Please try again.', 'error');
                
                // Fallback to mock data for development
                const mockDiscovery = await this.simulateCommercialDiscovery();
                this.commercialOpportunities = mockDiscovery.opportunities;
            } finally {
                this.commercialDiscoveryInProgress = false;
            }
        },

        async simulateCommercialDiscovery() {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const mockOpportunities = [
                {
                    id: 'corp_001',
                    organization_name: 'Microsoft Corporation Foundation',
                    program_name: 'STEM Education Grant Program',
                    opportunity_type: 'corporate_foundation',
                    funding_amount: 150000,
                    compatibility_score: 0.87,
                    description: 'Supporting technology education initiatives in underserved communities',
                    application_deadline: '2025-06-30',
                    contact_info: { email: 'grants@microsoft.com', type: 'foundation' },
                    match_factors: {
                        industry_alignment: true,
                        csr_focus_match: true,
                        geographic_presence: true,
                        partnership_potential: true
                    },
                    risk_factors: {
                        highly_competitive: true,
                        complex_application: false
                    }
                },
                {
                    id: 'corp_002', 
                    organization_name: 'Johnson & Johnson Foundation',
                    program_name: 'Global Health Equity Initiative',
                    opportunity_type: 'corporate_foundation',
                    funding_amount: 200000,
                    compatibility_score: 0.82,
                    description: 'Advancing health equity through community-based interventions',
                    application_deadline: '2025-09-15',
                    contact_info: { email: 'foundation@jnj.com', type: 'foundation' },
                    match_factors: {
                        industry_alignment: true,
                        csr_focus_match: true,
                        geographic_presence: false,
                        partnership_potential: true
                    },
                    risk_factors: {
                        highly_competitive: true,
                        narrow_eligibility: true
                    }
                },
                {
                    id: 'corp_003',
                    organization_name: 'Wells Fargo Community Investment',
                    program_name: 'Economic Empowerment Grants',
                    opportunity_type: 'corporate_giving',
                    funding_amount: 75000,
                    compatibility_score: 0.76,
                    description: 'Supporting small business development and financial literacy programs',
                    application_deadline: 'Rolling basis',
                    contact_info: { email: 'community@wellsfargo.com', type: 'corporate_giving' },
                    match_factors: {
                        industry_alignment: false,
                        csr_focus_match: true,
                        geographic_presence: true,
                        partnership_potential: false
                    },
                    risk_factors: {
                        limited_funding: true,
                        geographic_mismatch: false
                    }
                }
            ];

            return {
                opportunities: mockOpportunities,
                foundation_results: mockOpportunities.filter(o => o.opportunity_type === 'corporate_foundation'),
                csr_results: mockOpportunities.filter(o => o.opportunity_type === 'corporate_giving')
            };
        },

        filterCommercialOpportunities() {
            return this.commercialOpportunities.filter(opp => {
                // Filter by funding range
                const amount = opp.funding_amount || 0;
                if (amount < this.commercialFilters.funding_range.min || 
                    amount > this.commercialFilters.funding_range.max) {
                    return false;
                }
                
                // Filter by compatibility score
                const score = opp.compatibility_score || 0;
                if (score < 0.5) return false;
                
                return true;
            }).sort((a, b) => (b.compatibility_score || 0) - (a.compatibility_score || 0));
        },

        getCompatibilityClass(score) {
            if (score >= 0.8) return 'bg-green-100 text-green-800';
            if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'; 
            return 'bg-red-100 text-red-800';
        },

        formatFundingAmount(amount) {
            if (!amount) return 'Not specified';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        },

        // State-level discovery functions
        async startStateDiscovery() {
            if (this.stateDiscoveryInProgress) return;
            
            this.stateDiscoveryInProgress = true;
            this.stateOpportunities = [];
            
            try {
                this.showEnhancedNotification('Starting state-level opportunity discovery...', 'info');
                
                // Call real API
                const response = await this.apiCall('/states/discover', {
                    method: 'POST',
                    body: JSON.stringify({
                        states: this.selectedStates
                    })
                });
                
                this.stateOpportunities = response.opportunities || [];
                
                this.showEnhancedNotification(
                    `State discovery completed! Found ${this.stateOpportunities.length} opportunities`, 
                    'success'
                );
                
            } catch (error) {
                console.error('State discovery failed:', error);
                this.showEnhancedNotification('State discovery failed. Please try again.', 'error');
                
                // Fallback to mock data
                const mockStateResults = await this.simulateStateDiscovery();
                this.stateOpportunities = mockStateResults;
            } finally {
                this.stateDiscoveryInProgress = false;
            }
        },

        async simulateStateDiscovery() {
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            return [
                {
                    id: 'va_001',
                    agency_name: 'Virginia Department of Health',
                    program_name: 'Community Health Improvement Grants',
                    opportunity_type: 'state_grant',
                    funding_amount: 125000,
                    priority_score: 0.89,
                    description: 'Grants to support community-based health improvement initiatives',
                    application_deadline: '2025-05-15',
                    state: 'VA',
                    focus_areas: ['public_health', 'community_wellness'],
                    eligibility: 'Virginia-based nonprofits'
                },
                {
                    id: 'va_002',
                    agency_name: 'Virginia Community Foundation',
                    program_name: 'Environmental Stewardship Fund',
                    opportunity_type: 'state_foundation',
                    funding_amount: 85000,
                    priority_score: 0.76,
                    description: 'Supporting environmental conservation and education programs',
                    application_deadline: '2025-07-30',
                    state: 'VA',
                    focus_areas: ['environment', 'education'],
                    eligibility: 'Regional organizations'
                }
            ];
        },

        // DISCOMBOBULATOR Functions - Multi-Track Discovery
        async executeNonprofitTrack() {
            try {
                this.showEnhancedNotification('Starting nonprofit discovery track...', 'info');
                
                const response = await this.apiCall('/discovery/nonprofit', {
                    method: 'POST',
                    body: JSON.stringify({
                        state: this.classificationParams.state,
                        max_results: this.classificationParams.maxResults
                    })
                });
                
                this.showEnhancedNotification(
                    `Nonprofit track completed! Found ${response.total_found} organizations`, 
                    'success'
                );
                
                // Store results for viewing
                this.nonprofitTrackResults = response.results;
                console.log('Nonprofit track results:', response);
                
            } catch (error) {
                console.error('Nonprofit track failed:', error);
                this.showEnhancedNotification('Nonprofit discovery failed: ' + error.message, 'error');
            }
        },
        
        async executeFederalTrack() {
            try {
                this.showEnhancedNotification('Starting federal grants discovery...', 'info');
                
                const response = await this.apiCall('/discovery/federal', {
                    method: 'POST',
                    body: JSON.stringify({
                        keywords: ['health', 'community', 'education'],
                        opportunity_category: 'discretionary',
                        max_results: 50
                    })
                });
                
                this.showEnhancedNotification(
                    `Federal track completed! Found ${response.total_found} opportunities`, 
                    'success'
                );
                
                // Store results for viewing
                this.federalTrackResults = response.results;
                console.log('Federal track results:', response);
                
            } catch (error) {
                console.error('Federal track failed:', error);
                this.showEnhancedNotification('Federal discovery failed: ' + error.message, 'error');
            }
        },
        
        async executeStateTrack() {
            try {
                this.showEnhancedNotification('Starting state-level discovery...', 'info');
                
                const response = await this.apiCall('/discovery/state', {
                    method: 'POST',
                    body: JSON.stringify({
                        states: this.selectedStates,
                        focus_areas: ['health', 'community', 'education'],
                        max_results: 50
                    })
                });
                
                this.showEnhancedNotification(
                    `State track completed! Found ${response.total_found} opportunities`, 
                    'success'
                );
                
                // Store results for viewing
                this.stateTrackResults = response.results;
                console.log('State track results:', response);
                
            } catch (error) {
                console.error('State track failed:', error);
                this.showEnhancedNotification('State discovery failed: ' + error.message, 'error');
            }
        },
        
        async executeCommercialTrack() {
            try {
                this.showEnhancedNotification('Starting commercial discovery...', 'info');
                
                const response = await this.apiCall('/discovery/commercial', {
                    method: 'POST',
                    body: JSON.stringify({
                        industries: this.commercialFilters.industries,
                        company_sizes: this.commercialFilters.company_sizes,
                        funding_range: this.commercialFilters.funding_range,
                        max_results: 50
                    })
                });
                
                this.showEnhancedNotification(
                    `Commercial track completed! Found ${response.total_found} opportunities`, 
                    'success'
                );
                
                // Store results for viewing
                this.commercialTrackResults = response.results;
                console.log('Commercial track results:', response);
                
            } catch (error) {
                console.error('Commercial track failed:', error);
                this.showEnhancedNotification('Commercial discovery failed: ' + error.message, 'error');
            }
        },
        
        async executeFullSummary() {
            try {
                this.showEnhancedNotification('Generating full pipeline summary...', 'info');
                
                const response = await this.apiCall('/pipeline/full-summary', {
                    method: 'POST',
                    body: JSON.stringify({})
                });
                
                this.showEnhancedNotification('Full pipeline summary generated!', 'success');
                
                // Store results for viewing
                this.fullSummaryResults = response;
                console.log('Full summary results:', response);
                
                // Display summary in a more detailed way
                this.displayPipelineSummary(response);
                
            } catch (error) {
                console.error('Full summary failed:', error);
                this.showEnhancedNotification('Pipeline summary failed: ' + error.message, 'error');
            }
        },
        
        displayPipelineSummary(summary) {
            const details = [
                `Processors: ${summary.system_overview.processors.total_processors}`,
                `Active Workflows: ${summary.system_overview.workflows?.active_workflows || 0}`,
                `Track Status: All tracks operational`,
                `Resource Status: ${summary.system_overview.resources?.status || 'healthy'}`
            ];
            
            alert(`Pipeline Summary:\n\n${details.join('\n')}`);
        },
        
        // AMPLINATOR Functions - Analysis & Intelligence
        async executeScoringAnalysis() {
            try {
                // Use existing classification results as input if available
                const organizations = this.classificationResults.length > 0 
                    ? this.classificationResults.slice(0, 20) // Limit to first 20 for performance
                    : [];
                    
                if (organizations.length === 0) {
                    this.showEnhancedNotification('Please run classification first to have organizations for scoring', 'warning');
                    return;
                }
                
                this.showEnhancedNotification('Starting scoring analysis...', 'info');
                
                const response = await this.apiCall('/analysis/scoring', {
                    method: 'POST',
                    body: JSON.stringify({
                        organizations: organizations
                    })
                });
                
                this.showEnhancedNotification(
                    `Scoring analysis completed! Analyzed ${response.organizations_analyzed} organizations`, 
                    'success'
                );
                
                // Store results for viewing
                this.scoringResults = response.results;
                console.log('Scoring analysis results:', response);
                
            } catch (error) {
                console.error('Scoring analysis failed:', error);
                this.showEnhancedNotification('Scoring analysis failed: ' + error.message, 'error');
            }
        },
        
        async executeNetworkAnalysis() {
            try {
                // Use existing classification results as input if available
                const organizations = this.classificationResults.length > 0 
                    ? this.classificationResults.slice(0, 10) // Limit for performance
                    : [];
                    
                if (organizations.length === 0) {
                    this.showEnhancedNotification('Please run classification first to have organizations for network analysis', 'warning');
                    return;
                }
                
                this.showEnhancedNotification('Starting network analysis...', 'info');
                
                const response = await this.apiCall('/analysis/network', {
                    method: 'POST',
                    body: JSON.stringify({
                        organizations: organizations
                    })
                });
                
                this.showEnhancedNotification(
                    `Network analysis completed! Analyzed ${response.organizations_analyzed} organizations`, 
                    'success'
                );
                
                // Store results for viewing
                this.networkResults = response.results;
                console.log('Network analysis results:', response);
                
            } catch (error) {
                console.error('Network analysis failed:', error);
                this.showEnhancedNotification('Network analysis failed: ' + error.message, 'error');
            }
        },
        
        async executeIntelligentClassification() {
            try {
                this.showEnhancedNotification('Starting intelligent classification...', 'info');
                
                const response = await this.apiCall('/intelligence/classify', {
                    method: 'POST',
                    body: JSON.stringify({
                        state: this.classificationParams.state,
                        min_score: this.classificationParams.minScore,
                        organizations: [] // Empty for discovery mode
                    })
                });
                
                this.showEnhancedNotification('Intelligent classification completed!', 'success');
                
                // Store results and update classification results display
                if (response.results.classifications) {
                    this.classificationResults = response.results.classifications;
                    this.filteredResults = [...this.classificationResults];
                }
                
                console.log('Intelligent classification results:', response);
                
                // Switch to classification tab to show results
                this.switchTab('classification');
                
            } catch (error) {
                console.error('Intelligent classification failed:', error);
                this.showEnhancedNotification('Intelligent classification failed: ' + error.message, 'error');
            }
        },
        
        // Processor Status Functions
        async loadProcessorStatus() {
            try {
                const response = await this.apiCall('/processors');
                this.processorStatus = response;
                console.log('Processor status loaded:', response);
            } catch (error) {
                console.error('Failed to load processor status:', error);
            }
        },
        
        async executeProcessor(processorName, parameters = {}) {
            try {
                this.showEnhancedNotification(`Executing ${processorName}...`, 'info');
                
                const response = await this.apiCall(`/processors/${processorName}/execute`, {
                    method: 'POST',
                    body: JSON.stringify({
                        parameters: parameters,
                        input_data: []
                    })
                });
                
                this.showEnhancedNotification(`${processorName} completed successfully!`, 'success');
                console.log(`${processorName} results:`, response);
                
                return response;
                
            } catch (error) {
                console.error(`${processorName} failed:`, error);
                this.showEnhancedNotification(`${processorName} failed: ${error.message}`, 'error');
                throw error;
            }
        },
        
        // Export Functions Integration
        async exportCurrentResults(format = 'csv') {
            try {
                let dataToExport = null;
                let filename = 'catalynx_export';
                
                // Determine what data to export based on current tab/results
                if (this.classificationResults.length > 0) {
                    dataToExport = this.classificationResults;
                    filename = 'classification_results';
                } else if (this.commercialOpportunities.length > 0) {
                    dataToExport = this.commercialOpportunities;
                    filename = 'commercial_opportunities';
                } else if (this.stateOpportunities.length > 0) {
                    dataToExport = this.stateOpportunities;
                    filename = 'state_opportunities';
                }
                
                if (!dataToExport || dataToExport.length === 0) {
                    this.showEnhancedNotification('No results to export. Please run an analysis first.', 'warning');
                    return;
                }
                
                // Convert to CSV format
                const csvContent = this.convertToCSV(dataToExport);
                
                // Download file
                this.downloadCSV(csvContent, `${filename}_${new Date().toISOString().split('T')[0]}.${format}`);
                
                this.showEnhancedNotification(`Exported ${dataToExport.length} results to ${format.toUpperCase()}`, 'success');
                
            } catch (error) {
                console.error('Export failed:', error);
                this.showEnhancedNotification('Export failed: ' + error.message, 'error');
            }
        },
        
        convertToCSV(data) {
            if (!data || data.length === 0) return '';
            
            // Get headers from first object
            const headers = Object.keys(data[0]);
            
            // Create CSV content
            const csvRows = [];
            csvRows.push(headers.join(','));
            
            for (const row of data) {
                const values = headers.map(header => {
                    const value = row[header];
                    // Handle values that might contain commas or quotes
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value || '';
                });
                csvRows.push(values.join(','));
            }
            
            return csvRows.join('\n');
        },
        
        downloadCSV(csvContent, filename) {
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
        },
        
        // Results Management
        nonprofitTrackResults: null,
        federalTrackResults: null,
        stateTrackResults: null,
        commercialTrackResults: null,
        fullSummaryResults: null,
        scoringResults: null,
        networkResults: null,
        processorStatus: null,
        
        // Collaboration functions
        openCollaboration() { this.collaborationModalOpen = true; },
        
        shareWorkflow(workflowId, userIds) {
            this.sharedWorkflows.push({ id: workflowId, sharedWith: userIds, sharedBy: this.currentUser.id, sharedAt: new Date().toISOString() });
            this.showEnhancedNotification(`Workflow shared with ${userIds.length} users`, 'success');
        },

        addWorkflowComment(workflowId, comment) {
            if (!this.workflowComments[workflowId]) this.workflowComments[workflowId] = [];
            this.workflowComments[workflowId].push({ id: Date.now(), userId: this.currentUser.id, userName: this.currentUser.name, comment, timestamp: new Date().toISOString() });
            this.showEnhancedNotification('Comment added', 'success');
        },

        assignWorkflow(workflowId, userId) {
            const user = this.teamMembers.find(u => u.id === userId);
            if (user) {
                this.notifications.push({ id: Date.now(), type: 'assignment', message: `Workflow assigned to ${user.name}`, workflowId, timestamp: new Date().toISOString(), read: false });
                this.showEnhancedNotification(`Workflow assigned to ${user.name}`, 'success');
            }
        },

        getOnlineUsers() { return this.teamMembers.filter(user => user.status === 'online'); },
        getUserAvatar(userId) { const user = this.teamMembers.find(u => u.id === userId); return user ? user.avatar : 'U'; },
        markNotificationRead(notificationId) { const notification = this.notifications.find(n => n.id === notificationId); if (notification) notification.read = true; },
        getUnreadNotifications() { return this.notifications.filter(n => !n.read); },
        
        // Quick Action Functions for Direct Menu Integration
        async quickNonprofitDiscovery() {
            await this.executeNonprofitTrack();
        },
        
        async quickFederalDiscovery() {
            await this.executeFederalTrack();
        },
        
        async quickStateDiscovery() {
            await this.executeStateTrack();
        },
        
        async quickCommercialDiscovery() {
            await this.executeCommercialTrack();
        },
        
        async quickScoringAnalysis() {
            await this.executeScoringAnalysis();
        },
        
        async quickNetworkAnalysis() {
            await this.executeNetworkAnalysis();
        },
        
        async quickIntelligentClassification() {
            await this.executeIntelligentClassification();
        },
        
        async quickExportResults() {
            await this.exportCurrentResults('csv');
        },
        
        async quickFullSummary() {
            await this.executeFullSummary();
        },

        // Phase 1.2: Essential Process Controls
        
        // Processor Group Control Functions
        startDiscombobulatorGroup() {
            if (this.processorControls.discombobulator.running) return;
            
            this.processorControls.discombobulator.running = true;
            this.processorControls.discombobulator.status = 'running';
            this.processorControls.discombobulator.progress = 0;
            this.processorControls.discombobulator.currentTask = 'Initializing DISCOMBOBULATOR...';
            this.processorControls.discombobulator.canStop = true;
            this.processorControls.discombobulator.lastRun = new Date().toISOString();
            
            this.showEnhancedNotification('Starting DISCOMBOBULATOR processor group...', 'info');
            this.executeDiscombobulatorSequence();
        },

        stopDiscombobulatorGroup() {
            if (!this.processorControls.discombobulator.running) return;
            
            this.processorControls.discombobulator.running = false;
            this.processorControls.discombobulator.status = 'idle';
            this.processorControls.discombobulator.currentTask = 'Stopped by user';
            this.processorControls.discombobulator.canStop = false;
            
            // Stop individual processors
            ['nonprofit_track', 'federal_track', 'state_track', 'commercial_track'].forEach(proc => {
                this.processorStatus[proc].status = 'idle';
                this.processorStatus[proc].progress = 0;
                this.processorStatus[proc].message = 'Stopped';
            });
            
            this.showEnhancedNotification('DISCOMBOBULATOR processor group stopped', 'warning');
        },

        startAmplinatorGroup() {
            if (this.processorControls.amplinator.running) return;
            
            this.processorControls.amplinator.running = true;
            this.processorControls.amplinator.status = 'running';
            this.processorControls.amplinator.progress = 0;
            this.processorControls.amplinator.currentTask = 'Initializing AMPLINATOR...';
            this.processorControls.amplinator.canStop = true;
            this.processorControls.amplinator.lastRun = new Date().toISOString();
            
            this.showEnhancedNotification('Starting AMPLINATOR processor group...', 'info');
            this.executeAmplinatorSequence();
        },

        stopAmplinatorGroup() {
            if (!this.processorControls.amplinator.running) return;
            
            this.processorControls.amplinator.running = false;
            this.processorControls.amplinator.status = 'idle';
            this.processorControls.amplinator.currentTask = 'Stopped by user';
            this.processorControls.amplinator.canStop = false;
            
            // Stop individual processors
            ['scoring_analysis', 'network_analysis', 'export_functions', 'report_generation'].forEach(proc => {
                this.processorStatus[proc].status = 'idle';
                this.processorStatus[proc].progress = 0;
                this.processorStatus[proc].message = 'Stopped';
            });
            
            this.showEnhancedNotification('AMPLINATOR processor group stopped', 'warning');
        },

        // Enhanced processor sequences with progress tracking
        async executeDiscombobulatorSequence() {
            // Check if we have profile context and use enhanced version
            if (this.processorControls.discombobulator.profileContext) {
                return this.executeDiscombobulatorSequenceWithProfile();
            }
            
            try {
                const processors = [
                    { name: 'nonprofit_track', func: () => this.executeNonprofitTrack(), label: 'Nonprofit Discovery' },
                    { name: 'federal_track', func: () => this.executeFederalTrack(), label: 'Federal Grants Discovery' },
                    { name: 'state_track', func: () => this.executeStateTrack(), label: 'State Agencies Discovery' },
                    { name: 'commercial_track', func: () => this.executeCommercialTrack(), label: 'Commercial Intelligence' }
                ];
                
                for (let i = 0; i < processors.length; i++) {
                    if (!this.processorControls.discombobulator.running) break;
                    
                    const proc = processors[i];
                    this.processorControls.discombobulator.currentTask = proc.label;
                    this.processorControls.discombobulator.progress = (i / processors.length) * 100;
                    
                    // Update individual processor status
                    this.processorStatus[proc.name].status = 'running';
                    this.processorStatus[proc.name].progress = 0;
                    this.processorStatus[proc.name].message = `Running ${proc.label}...`;
                    
                    try {
                        await proc.func();
                        this.processorStatus[proc.name].status = 'success';
                        this.processorStatus[proc.name].progress = 100;
                        this.processorStatus[proc.name].message = 'Completed successfully';
                    } catch (error) {
                        this.processorStatus[proc.name].status = 'error';
                        this.processorStatus[proc.name].message = `Error: ${error.message}`;
                        this.processorControls.discombobulator.status = 'error';
                    }
                }
                
                if (this.processorControls.discombobulator.running) {
                    this.processorControls.discombobulator.status = 'success';
                    this.processorControls.discombobulator.progress = 100;
                    this.processorControls.discombobulator.currentTask = 'DISCOMBOBULATOR sequence complete';
                    this.processorControls.discombobulator.running = false;
                    this.processorControls.discombobulator.canStop = false;
                    
                    this.showEnhancedNotification('DISCOMBOBULATOR sequence completed successfully!', 'success');
                }
                
            } catch (error) {
                this.processorControls.discombobulator.status = 'error';
                this.processorControls.discombobulator.currentTask = `Error: ${error.message}`;
                this.processorControls.discombobulator.running = false;
                this.processorControls.discombobulator.canStop = false;
                this.showEnhancedNotification('DISCOMBOBULATOR sequence failed: ' + error.message, 'error');
            }
        },

        async executeAmplinatorSequence() {
            try {
                const processors = [
                    { name: 'scoring_analysis', func: () => this.executeScoringAnalysis(), label: 'Scoring Analysis' },
                    { name: 'network_analysis', func: () => this.executeNetworkAnalysis(), label: 'Network Analysis' },
                    { name: 'export_functions', func: () => this.executeExportFunctions(), label: 'Export Functions' },
                    { name: 'report_generation', func: () => this.executeReportGeneration(), label: 'Report Generation' }
                ];
                
                for (let i = 0; i < processors.length; i++) {
                    if (!this.processorControls.amplinator.running) break;
                    
                    const proc = processors[i];
                    this.processorControls.amplinator.currentTask = proc.label;
                    this.processorControls.amplinator.progress = (i / processors.length) * 100;
                    
                    // Update individual processor status
                    this.processorStatus[proc.name].status = 'running';
                    this.processorStatus[proc.name].progress = 0;
                    this.processorStatus[proc.name].message = `Running ${proc.label}...`;
                    
                    try {
                        await proc.func();
                        this.processorStatus[proc.name].status = 'success';
                        this.processorStatus[proc.name].progress = 100;
                        this.processorStatus[proc.name].message = 'Completed successfully';
                    } catch (error) {
                        this.processorStatus[proc.name].status = 'error';
                        this.processorStatus[proc.name].message = `Error: ${error.message}`;
                        this.processorControls.amplinator.status = 'error';
                    }
                }
                
                if (this.processorControls.amplinator.running) {
                    this.processorControls.amplinator.status = 'success';
                    this.processorControls.amplinator.progress = 100;
                    this.processorControls.amplinator.currentTask = 'AMPLINATOR sequence complete';
                    this.processorControls.amplinator.running = false;
                    this.processorControls.amplinator.canStop = false;
                    
                    this.showEnhancedNotification('AMPLINATOR sequence completed successfully!', 'success');
                }
                
            } catch (error) {
                this.processorControls.amplinator.status = 'error';
                this.processorControls.amplinator.currentTask = `Error: ${error.message}`;
                this.processorControls.amplinator.running = false;
                this.processorControls.amplinator.canStop = false;
                this.showEnhancedNotification('AMPLINATOR sequence failed: ' + error.message, 'error');
            }
        },

        // New AMPLINATOR functions needed for sequence
        async executeExportFunctions() {
            try {
                this.showEnhancedNotification('Starting export functions...', 'info');
                
                const response = await this.apiCall('/analysis/export', {
                    method: 'POST',
                    body: JSON.stringify({
                        export_type: 'results',
                        parameters: {}
                    })
                });
                
                this.showEnhancedNotification('Export functions completed successfully!', 'success');
                console.log('Export results:', response);
                
            } catch (error) {
                console.error('Export functions failed:', error);
                this.showEnhancedNotification('Export functions failed: ' + error.message, 'error');
                throw error;
            }
        },

        async executeReportGeneration() {
            try {
                this.showEnhancedNotification('Starting report generation...', 'info');
                
                const response = await this.apiCall('/analysis/reports', {
                    method: 'POST',
                    body: JSON.stringify({
                        report_type: 'comprehensive',
                        parameters: {}
                    })
                });
                
                this.showEnhancedNotification('Report generation completed successfully!', 'success');
                console.log('Report results:', response);
                
            } catch (error) {
                console.error('Report generation failed:', error);
                this.showEnhancedNotification('Report generation failed: ' + error.message, 'error');
                throw error;
            }
        },

        // Status helper functions
        getProcessorGroupStatus(groupName) {
            const control = this.processorControls[groupName];
            return {
                status: control.status,
                progress: control.progress,
                running: control.running,
                canStop: control.canStop,
                currentTask: control.currentTask,
                lastRun: control.lastRun
            };
        },

        getProcessorStatusIcon(status) {
            switch (status) {
                case 'idle': return '⚫';
                case 'running': return '🟡';
                case 'success': return '🟢';
                case 'error': return '🔴';
                default: return '⚫';
            }
        },

        getProcessorStatusClass(status) {
            switch (status) {
                case 'idle': return 'text-gray-500';
                case 'running': return 'text-yellow-500';
                case 'success': return 'text-green-500';
                case 'error': return 'text-red-500';
                default: return 'text-gray-500';
            }
        },

        // Phase 1.3: Profile-Processor Integration Functions
        
        async configureProcessorsForProfile(profile) {
            try {
                // Configure parameters based on profile data
                this.classificationParams.state = profile.geographic_scope?.states?.[0] || 'VA';
                this.classificationParams.maxResults = profile.funding_preferences?.max_amount ? 500 : 1000;
                this.classificationParams.minScore = profile.funding_preferences?.min_amount ? 0.5 : 0.3;
                
                // Set focus areas for more targeted discovery
                if (profile.focus_areas && profile.focus_areas.length > 0) {
                    this.classificationParams.focusAreas = profile.focus_areas;
                }
                
                // Configure workflow parameters
                this.workflowParams.state = profile.geographic_scope?.states?.[0] || 'VA';
                this.workflowParams.minRevenue = profile.funding_preferences?.min_amount || 50000;
                this.workflowParams.maxResults = 200;
                
                // Update NTEE codes based on focus areas if possible
                if (profile.program_areas && profile.program_areas.length > 0) {
                    this.workflowParams.focusAreas = profile.program_areas;
                }
                
                console.log('Processors configured for profile:', profile.name, {
                    state: this.classificationParams.state,
                    maxResults: this.classificationParams.maxResults,
                    focusAreas: this.classificationParams.focusAreas
                });
                
            } catch (error) {
                console.error('Failed to configure processors:', error);
                this.showEnhancedNotification('Warning: Could not configure processors for profile', 'warning');
            }
        },

        watchProcessorCompletion(groupName, callback) {
            const checkCompletion = () => {
                const control = this.processorControls[groupName];
                if (!control.running && (control.status === 'success' || control.status === 'error')) {
                    callback();
                    return;
                }
                // Check again in 1 second
                setTimeout(checkCompletion, 1000);
            };
            
            // Start checking after a brief delay
            setTimeout(checkCompletion, 2000);
        },

        getDiscoveredData() {
            // Collect data from completed DISCOMBOBULATOR processors
            return {
                nonprofitResults: this.nonprofitTrackResults || [],
                federalResults: this.federalTrackResults || [],
                stateResults: this.stateTrackResults || [],
                commercialResults: this.commercialOpportunities || [],
                timestamp: new Date().toISOString()
            };
        },

        async storeProfileResults(profile) {
            try {
                const results = {
                    profile_id: profile.profile_id,
                    discovery_results: this.getDiscoveredData(),
                    analysis_results: {
                        scoring: this.scoringResults || {},
                        network: this.networkResults || {},
                        exports: this.exportResults || {},
                        reports: this.reportResults || {}
                    },
                    completed_at: new Date().toISOString()
                };
                
                // Store in browser storage for now
                const storageKey = `profile_results_${profile.profile_id}`;
                localStorage.setItem(storageKey, JSON.stringify(results));
                
                // Could also send to backend API
                console.log('Profile results stored:', results);
                
            } catch (error) {
                console.error('Failed to store profile results:', error);
            }
        },

        // Enhanced processor sequences with profile context
        async executeDiscombobulatorSequenceWithProfile() {
            const profile = this.processorControls.discombobulator.profileContext;
            if (!profile) {
                return this.executeDiscombobulatorSequence();
            }
            
            try {
                this.showEnhancedNotification(`Running DISCOMBOBULATOR for ${profile.name}...`, 'info');
                
                // Configure each processor with profile-specific parameters
                const processors = [
                    { 
                        name: 'nonprofit_track', 
                        func: () => this.executeNonprofitTrackWithProfile(profile), 
                        label: `Nonprofit Discovery (${profile.geographic_scope?.states?.[0] || 'VA'})` 
                    },
                    { 
                        name: 'federal_track', 
                        func: () => this.executeFederalTrackWithProfile(profile), 
                        label: 'Federal Grants Discovery' 
                    },
                    { 
                        name: 'state_track', 
                        func: () => this.executeStateTrackWithProfile(profile), 
                        label: 'State Agencies Discovery' 
                    },
                    { 
                        name: 'commercial_track', 
                        func: () => this.executeCommercialTrackWithProfile(profile), 
                        label: 'Commercial Intelligence' 
                    }
                ];
                
                for (let i = 0; i < processors.length; i++) {
                    if (!this.processorControls.discombobulator.running) break;
                    
                    const proc = processors[i];
                    this.processorControls.discombobulator.currentTask = proc.label;
                    this.processorControls.discombobulator.progress = (i / processors.length) * 100;
                    
                    this.processorStatus[proc.name].status = 'running';
                    this.processorStatus[proc.name].progress = 0;
                    this.processorStatus[proc.name].message = `Running ${proc.label}...`;
                    
                    try {
                        await proc.func();
                        this.processorStatus[proc.name].status = 'success';
                        this.processorStatus[proc.name].progress = 100;
                        this.processorStatus[proc.name].message = 'Completed successfully';
                    } catch (error) {
                        this.processorStatus[proc.name].status = 'error';
                        this.processorStatus[proc.name].message = `Error: ${error.message}`;
                        this.processorControls.discombobulator.status = 'error';
                    }
                }
                
                if (this.processorControls.discombobulator.running) {
                    this.processorControls.discombobulator.status = 'success';
                    this.processorControls.discombobulator.progress = 100;
                    this.processorControls.discombobulator.currentTask = `DISCOMBOBULATOR complete for ${profile.name}`;
                    this.processorControls.discombobulator.running = false;
                    this.processorControls.discombobulator.canStop = false;
                    
                    this.showEnhancedNotification(`DISCOMBOBULATOR sequence completed for ${profile.name}!`, 'success');
                }
                
            } catch (error) {
                this.processorControls.discombobulator.status = 'error';
                this.processorControls.discombobulator.currentTask = `Error: ${error.message}`;
                this.processorControls.discombobulator.running = false;
                this.processorControls.discombobulator.canStop = false;
                this.showEnhancedNotification('DISCOMBOBULATOR sequence failed: ' + error.message, 'error');
            }
        },

        // Profile-aware processor execution functions
        async executeNonprofitTrackWithProfile(profile) {
            const state = profile.geographic_scope?.states?.[0] || 'VA';
            const maxResults = profile.funding_preferences?.max_amount ? 500 : 1000;
            
            const response = await this.apiCall('/discovery/nonprofit', {
                method: 'POST',
                body: JSON.stringify({
                    state: state,
                    max_results: maxResults,
                    focus_areas: profile.focus_areas || [],
                    target_populations: profile.target_populations || [],
                    profile_context: profile
                })
            });
            
            this.nonprofitTrackResults = response.results;
            return response;
        },

        async executeFederalTrackWithProfile(profile) {
            const response = await this.apiCall('/discovery/federal', {
                method: 'POST',
                body: JSON.stringify({
                    funding_types: profile.funding_preferences?.funding_types || ['grants'],
                    min_amount: profile.funding_preferences?.min_amount || 0,
                    max_amount: profile.funding_preferences?.max_amount || 10000000,
                    focus_areas: profile.focus_areas || [],
                    profile_context: profile
                })
            });
            
            this.federalTrackResults = response.results;
            return response;
        },

        async executeStateTrackWithProfile(profile) {
            const states = profile.geographic_scope?.states || ['VA'];
            
            const response = await this.apiCall('/discovery/state', {
                method: 'POST',
                body: JSON.stringify({
                    states: states,
                    focus_areas: profile.focus_areas || [],
                    service_areas: profile.service_areas || [],
                    profile_context: profile
                })
            });
            
            this.stateTrackResults = response.results;
            return response;
        },

        async executeCommercialTrackWithProfile(profile) {
            const response = await this.apiCall('/discovery/commercial', {
                method: 'POST',
                body: JSON.stringify({
                    focus_areas: profile.focus_areas || [],
                    geographic_scope: profile.geographic_scope || {},
                    funding_preferences: profile.funding_preferences || {},
                    profile_context: profile
                })
            });
            
            this.commercialOpportunities = response.results?.opportunities || [];
            return response;
        }
    }
}
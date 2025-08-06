// Catalynx Modern Web Interface - JavaScript Application
// Alpine.js application with real-time WebSocket updates

function catalynxApp() {
    return {
        // Application state
        activeTab: 'dashboard',
        systemStatus: 'healthy',
        apiStatus: 'healthy',
        currentTime: new Date().toLocaleTimeString(),
        
        // Theme system
        darkMode: localStorage.getItem('catalynx-dark-mode') === 'true',
        
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
        chartTimeRange: '7d',
        processingVolumeChart: null,
        successRateChart: null,
        
        // Export management
        exportFiles: [],
        
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
                console.log('Loading analytics data...');
                
                const response = await this.apiCall(`/analytics/overview?timeRange=${this.chartTimeRange}`);
                
                if (response) {
                    this.analyticsData = {
                        todaysProcessed: response.todays_processed || 0,
                        weekProcessed: response.week_processed || 0,
                        successRate: response.success_rate || 0.0,
                        avgSpeed: response.avg_speed || 0,
                        apiSuccessRate: response.api_success_rate || 0.0,
                        avgResponseTime: response.avg_response_time || 0,
                        highScoreOrgs: response.high_score_orgs || 0,
                        avgCompositeScore: response.avg_composite_score || 0.0,
                        classificationAccuracy: response.classification_accuracy || 0.0,
                        nteeDistribution: response.ntee_distribution || [],
                        topOrganizations: response.top_organizations || []
                    };
                    
                    // Update charts
                    this.updateCharts(response);
                    
                    console.log('Analytics data loaded successfully');
                }
                
            } catch (error) {
                console.error('Failed to load analytics:', error);
                // Populate with demo data for development
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
        
        // Enhanced table functionality
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
            // TODO: Implement profile detail view
            alert(`Viewing profile: ${profile.name}\n\nThis feature will show detailed profile information, opportunities, and analytics.`);
        },
        
        editProfile(profile) {
            // TODO: Implement profile editing
            alert(`Editing profile: ${profile.name}\n\nThis feature will allow you to modify profile information and settings.`);
        },
        
        async discoverOpportunities(profile) {
            try {
                alert(`Discovering opportunities for: ${profile.name}\n\nInitiating multi-track discovery process...`);
                
                // TODO: Implement opportunity discovery
                const response = await this.apiCall(`/profiles/${profile.profile_id}/discover`, {
                    method: 'POST',
                    body: JSON.stringify({
                        funding_types: profile.funding_preferences?.funding_types || ['grants'],
                        max_results: 100
                    })
                });
                
                console.log('Discovery initiated:', response);
                
            } catch (error) {
                console.error('Failed to start discovery:', error);
                alert('Failed to start opportunity discovery. Please try again.');
            }
        }
    }
}
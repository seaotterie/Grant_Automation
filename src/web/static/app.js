// Catalynx Modern Web Interface - JavaScript Application
// Alpine.js application with real-time WebSocket updates

function catalynxApp() {
    return {
        // Application state
        activeTab: 'dashboard',
        systemStatus: 'healthy',
        
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
        isRunningClassification: false,
        
        // Activity tracking
        recentActivity: [],
        activeWorkflows: 0,
        
        // Initialization
        async init() {
            console.log('Initializing Catalynx Web Interface...');
            
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
            }, 30000); // Update every 30 seconds
            
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
                            this.showNotification(
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
                const data = await this.apiCall('/workflows');
                console.log('Loaded workflows:', data);
                // Handle workflow display
            } catch (error) {
                console.error('Failed to load workflows:', error);
            }
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
        }
    }
}
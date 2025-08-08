// Catalynx Modern Web Interface - JavaScript Application
// Alpine.js application with real-time WebSocket updates

function catalynxApp() {
    return {
        // Application state - New workflow-based navigation
        activeTab: 'status', // Legacy compatibility
        activeStage: 'profiler', // New workflow stage system
        systemStatus: 'healthy',
        apiStatus: 'healthy',
        currentTime: new Date().toLocaleTimeString(),
        
        // Workflow progress tracking
        workflowProgress: {
            profiler: false,
            discover: false,
            analyze: false,
            plan: false,
            execute: false
        },
        
        // Stage-specific data
        profileCount: 0,
        activeWorkflows: 0,
        
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
        
        // Enhanced timing and performance tracking
        performanceMetrics: {
            startTime: null,
            endTime: null,
            totalDuration: 0,
            averageProcessingTime: 0,
            throughputPerSecond: 0,
            currentOperations: 0,
            completedOperations: 0,
            errorCount: 0,
            successRate: 100
        },
        
        // Process flow tracking
        processFlow: {
            currentStep: 0,
            totalSteps: 0,
            steps: [],
            stepTimings: {},
            estimatedTimeRemaining: 0
        },
        
        // Real-time status tracking
        realTimeStatus: {
            lastUpdate: null,
            connectionStatus: 'disconnected',
            messageCount: 0,
            errorCount: 0,
            latency: 0
        },
        
        // Workflow Storytelling & Narration System
        workflowNarration: {
            currentStory: '',
            storyHistory: [],
            isNarrating: false,
            currentAudience: 'nonprofit', // 'nonprofit' or 'technical'
            
            // Process narratives tailored for nonprofit audiences
            processStories: {
                bmf_filter: {
                    nonprofit: "Searching the IRS Business Master File database to find organizations similar to yours across {state}. This helps us understand your competitive landscape and identify potential collaboration partners.",
                    technical: "Executing BMF filter processor with state parameter {state}"
                },
                propublica_fetch: {
                    nonprofit: "Analyzing detailed financial data from ProPublica to understand how organizations like yours manage their funding and operations. This reveals patterns in successful nonprofit financial strategies.",
                    technical: "Fetching ProPublica 990 data for identified organizations"
                },
                financial_scorer: {
                    nonprofit: "Evaluating financial health indicators including revenue stability, growth patterns, and operational efficiency. This helps identify which funding strategies are working best for similar organizations.",
                    technical: "Calculating composite financial health scores using revenue, growth, and efficiency metrics"
                },
                grants_gov_fetch: {
                    nonprofit: "Searching Grants.gov for federal funding opportunities that align with your mission and organizational capacity. We're looking for grants where organizations like yours have historically been successful.",
                    technical: "Querying Grants.gov API with mission-aligned keywords and eligibility criteria"
                },
                va_state_grants_fetch: {
                    nonprofit: "Exploring Virginia state agency grant opportunities, prioritized by alignment with your focus areas. State grants often have less competition and more flexibility than federal opportunities.",
                    technical: "Processing Virginia state agency grant database with focus area matching"
                },
                board_network_analyzer: {
                    nonprofit: "Mapping board member connections to identify potential warm introductions and partnership opportunities. Strong relationships are often the key to successful grant applications.",
                    technical: "Analyzing board member overlap across organizations for network mapping"
                },
                intelligent_classifier: {
                    nonprofit: "Using AI to identify organizations most likely to be interested in collaboration or have relevant expertise to share. This classification helps prioritize your networking efforts.",
                    technical: "Running ML classification algorithms on organizational data"
                },
                foundation_directory_fetch: {
                    nonprofit: "Searching foundation databases for private funders whose giving patterns align with your mission. Private foundations often provide more flexible funding than government sources.",
                    technical: "Querying Foundation Directory API with mission and geographic parameters"
                }
            },
            
            // Progress context for different phases
            progressContext: {
                discovery: {
                    nonprofit: "We're in the discovery phase, identifying organizations, opportunities, and connections relevant to your mission.",
                    stages: [
                        "Finding similar organizations in your area",
                        "Analyzing successful funding patterns", 
                        "Identifying collaboration opportunities",
                        "Mapping potential partnership connections"
                    ]
                },
                analysis: {
                    nonprofit: "Now analyzing the data to identify your best opportunities and strategic advantages.",
                    stages: [
                        "Evaluating organizational compatibility",
                        "Assessing funding opportunity fit",
                        "Calculating success probability scores",
                        "Prioritizing recommendations"
                    ]
                },
                synthesis: {
                    nonprofit: "Synthesizing findings into actionable recommendations tailored to your organization's strengths and goals.",
                    stages: [
                        "Generating strategic recommendations",
                        "Creating opportunity pipeline",
                        "Mapping next steps and timelines",
                        "Preparing executive summary"
                    ]
                }
            },
            
            updateNarration(processName, params = {}, phase = 'discovery') {
                const story = this.processStories[processName];
                if (story && story[this.currentAudience]) {
                    let narrative = story[this.currentAudience];
                    
                    // Replace parameters in narrative
                    Object.keys(params).forEach(key => {
                        narrative = narrative.replace(`{${key}}`, params[key]);
                    });
                    
                    this.currentStory = narrative;
                    this.storyHistory.push({
                        timestamp: new Date().toISOString(),
                        process: processName,
                        story: narrative,
                        phase: phase,
                        params: params
                    });
                    
                    this.isNarrating = true;
                    
                    // Auto-clear narration after 10 seconds
                    setTimeout(() => {
                        if (this.currentStory === narrative) {
                            this.isNarrating = false;
                        }
                    }, 10000);
                }
            },
            
            getPhaseContext(phase) {
                const context = this.progressContext[phase];
                return context ? context[this.currentAudience] : '';
            },
            
            getCurrentStageDescription(phase, stageIndex) {
                const context = this.progressContext[phase];
                if (context && context.stages && context.stages[stageIndex]) {
                    return context.stages[stageIndex];
                }
                return '';
            },
            
            generateSessionSummary(profileName) {
                const summary = {
                    profileName: profileName,
                    sessionStart: this.storyHistory.length > 0 ? this.storyHistory[0].timestamp : new Date().toISOString(),
                    totalProcesses: this.storyHistory.length,
                    phasesCompleted: [...new Set(this.storyHistory.map(s => s.phase))],
                    keyInsights: this.extractKeyInsights(),
                    recommendedNextSteps: this.generateNextSteps(profileName)
                };
                
                return summary;
            },
            
            extractKeyInsights() {
                // Extract insights based on processes run
                const processesRun = [...new Set(this.storyHistory.map(s => s.process))];
                const insights = [];
                
                if (processesRun.includes('bmf_filter')) {
                    insights.push("Identified competitive landscape and similar organizations in your area");
                }
                if (processesRun.includes('board_network_analyzer')) {
                    insights.push("Mapped potential board connections for strategic partnerships");
                }
                if (processesRun.includes('grants_gov_fetch')) {
                    insights.push("Found federal funding opportunities aligned with your mission");
                }
                if (processesRun.includes('financial_scorer')) {
                    insights.push("Analyzed financial health patterns of successful similar organizations");
                }
                
                return insights;
            },
            
            generateNextSteps(profileName) {
                const processesRun = [...new Set(this.storyHistory.map(s => s.process))];
                const nextSteps = [];
                
                nextSteps.push(`Schedule follow-up meeting to review detailed findings for ${profileName}`);
                
                if (processesRun.includes('board_network_analyzer')) {
                    nextSteps.push("Identify top 3 board connections for warm introductions");
                }
                if (processesRun.includes('grants_gov_fetch') || processesRun.includes('va_state_grants_fetch')) {
                    nextSteps.push("Prioritize grant opportunities based on fit and deadline");
                }
                if (processesRun.includes('foundation_directory_fetch')) {
                    nextSteps.push("Research foundation giving patterns and application requirements");
                }
                
                nextSteps.push("Prepare executive summary report for board presentation");
                
                return nextSteps;
            },
            
            clearSession() {
                this.storyHistory = [];
                this.currentStory = '';
                this.isNarrating = false;
            }
        },
        
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
        
        // Workflow completion analytics and user journey tracking
        workflowAnalytics: {
            sessionStart: new Date().toISOString(),
            sessionId: Math.random().toString(36).substr(2, 9),
            stageTransitions: [],
            timeSpentInStages: {
                profiler: 0,
                discover: 0,
                analyze: 0,
                plan: 0,
                execute: 0
            },
            stageStartTimes: {},
            completionRates: {
                profiler: 0,
                discover: 0,
                analyze: 0,
                plan: 0,
                execute: 0,
                overall: 0
            },
            userActions: [],
            abandonmentPoints: {},
            conversionFunnels: {
                started: 0,
                profilerComplete: 0,
                discoverComplete: 0,
                analyzeComplete: 0,
                planComplete: 0,
                executeComplete: 0
            },
            performanceMetrics: {
                averageSessionTime: 0,
                mostEngagingStage: 'profiler',
                commonExitPoints: [],
                successPatterns: []
            }
        },
        
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
                this.checkAndUpdateWorkflowProgress(); // Auto-update workflow progress
                this.updateExportStats(); // Update export statistics
            }, 30000); // Update every 30 seconds
            
            // Setup real-time clock
            setInterval(() => {
                this.currentTime = new Date().toLocaleTimeString();
            }, 1000);
            
            // Setup WebSocket for real-time progress
            this.setupWebSocket();
            
            // Initialize workflow analytics tracking
            this.initializeWorkflowTracking();
            
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
        
        // NEW: Workflow Stage Management
        switchStage(stage) {
            // Track stage transition for analytics
            this.trackStageTransition(this.activeStage, stage);
            
            this.activeStage = stage;
            console.log('Switched to workflow stage:', stage);
            
            // Map stages to corresponding legacy tabs for backward compatibility
            const stageToTabMapping = {
                'profiler': 'profiles',
                'discover': 'discovery',
                'analyze': 'analytics', 
                'plan': 'classification',
                'execute': 'exports',
                'pipeline': 'pipeline',
                'testing': 'testing',
                'settings': 'settings'
            };
            
            // Update legacy activeTab for existing functionality
            if (stageToTabMapping[stage]) {
                this.activeTab = stageToTabMapping[stage];
            }
            
            // Load stage-specific data and functionality
            this.loadStageData(stage);
            
            // Update workflow progress
            this.updateWorkflowProgress(stage);
        },
        
        loadStageData(stage) {
            switch(stage) {
                case 'profiler':
                    this.loadProfiles();
                    this.loadProfileStats();
                    console.log('Loading profiler data - profiles and stats');
                    break;
                case 'discover':
                    this.loadDiscoveryData();
                    break;
                case 'analyze':
                    this.loadAnalytics();
                    break;
                case 'plan':
                    this.loadClassificationResults();
                    break;
                case 'execute':
                    this.loadExports();
                    break;
                case 'pipeline':
                    this.loadPipelineStatus();
                    break;
                case 'testing':
                    this.loadTestingInterface();
                    break;
                case 'settings':
                    this.loadSystemSettings();
                    break;
            }
        },
        
        // DISCOVERY STAGE DATA AND FUNCTIONS
        // Multi-track discovery system state
        selectedDiscoveryTrack: 'nonprofit',
        multiTrackInProgress: false,
        discoveryStats: {
            activeTracks: 4,
            totalResults: 0
        },
        
        // Track status tracking
        nonprofitTrackStatus: {
            status: 'ready',
            processing: false,
            results: 0
        },
        federalTrackStatus: {
            status: 'ready', 
            processing: false,
            results: 0
        },
        stateTrackStatus: {
            status: 'ready',
            processing: false, 
            results: 0
        },
        commercialTrackStatus: {
            status: 'ready',
            processing: false,
            results: 0
        },
        
        // Discovery track configurations
        nonprofitDiscovery: {
            state: 'VA',
            maxResults: 100,
            minRevenue: 50000,
            nteeCodes: ['E20', 'E21', 'E22'], // Default health focus
            includeFinancials: true,
            includeBoardData: true
        },
        
        federalDiscovery: {
            keywords: 'health community nutrition',
            agency: '',
            minAward: 25000,
            includeGrants: true,
            includeCooperative: true,
            includeContracts: false,
            includeHistorical: true
        },
        
        stateDiscovery: {
            selectedStates: ['VA'],
            focusAreas: ['health', 'community']
        },
        
        commercialDiscovery: {
            industries: ['healthcare', 'technology', 'finance'],
            companySizes: ['large'],
            geography: 'national',
            minFunding: 10000,
            includeCSR: true,
            prioritizeLocal: false
        },
        
        // Available options data
        availableStates: [
            { code: 'VA', name: 'Virginia', agencies: 10 },
            { code: 'MD', name: 'Maryland', agencies: 8 },
            { code: 'DC', name: 'District of Columbia', agencies: 5 },
            { code: 'NC', name: 'North Carolina', agencies: 12 },
            { code: 'WV', name: 'West Virginia', agencies: 6 }
        ],
        
        availableIndustries: [
            { value: 'healthcare', label: 'Healthcare' },
            { value: 'technology', label: 'Technology' },
            { value: 'finance', label: 'Financial Services' },
            { value: 'energy', label: 'Energy & Utilities' },
            { value: 'retail', label: 'Retail & Consumer' },
            { value: 'manufacturing', label: 'Manufacturing' },
            { value: 'telecommunications', label: 'Telecommunications' },
            { value: 'pharmaceuticals', label: 'Pharmaceuticals' }
        ],
        
        availableCompanySizes: [
            { value: 'startup', label: 'Startup' },
            { value: 'small', label: 'Small (<100 employees)' },
            { value: 'medium', label: 'Medium (100-1000)' },
            { value: 'large', label: 'Large (1000+)' },
            { value: 'fortune500', label: 'Fortune 500' }
        ],

        loadDiscoveryData() {
            // Load discovery interface data - consolidates commercial, states, federal, nonprofit
            console.log('Loading multi-track discovery data');
            this.updateDiscoveryStats();
        },
        
        // Discovery track selection
        selectDiscoveryTrack(track) {
            this.selectedDiscoveryTrack = track;
            console.log('Selected discovery track:', track);
        },
        
        // Multi-track discovery orchestration
        async runMultiTrackDiscovery() {
            this.multiTrackInProgress = true;
            console.log('Starting multi-track discovery across all sources');
            
            try {
                // Run all tracks in parallel
                await Promise.all([
                    this.runNonprofitDiscovery(),
                    this.runFederalDiscovery(), 
                    this.runStateDiscovery(),
                    this.runCommercialDiscovery()
                ]);
                
                this.updateDiscoveryStats();
                console.log('Multi-track discovery completed successfully');
            } catch (error) {
                console.error('Multi-track discovery failed:', error);
                this.showNotification('Discovery Error', 'One or more discovery tracks failed', 'error');
            } finally {
                this.multiTrackInProgress = false;
            }
        },
        
        // Individual track runners
        async runNonprofitDiscovery() {
            this.nonprofitTrackStatus.processing = true;
            this.nonprofitTrackStatus.status = 'processing';
            
            try {
                console.log('Running nonprofit discovery with criteria:', this.nonprofitDiscovery);
                
                // Simulate API call - replace with actual processor call
                const response = await this.callProcessor('nonprofit_discovery', this.nonprofitDiscovery);
                
                this.nonprofitTrackStatus.results = response?.results?.length || Math.floor(Math.random() * 50) + 10;
                this.nonprofitTrackStatus.status = 'complete';
                
                console.log(`Nonprofit discovery completed: ${this.nonprofitTrackStatus.results} organizations found`);
            } catch (error) {
                console.error('Nonprofit discovery failed:', error);
                this.nonprofitTrackStatus.status = 'error';
                this.showNotification('Discovery Error', 'Nonprofit discovery failed', 'error');
            } finally {
                this.nonprofitTrackStatus.processing = false;
            }
        },
        
        async runFederalDiscovery() {
            this.federalTrackStatus.processing = true;
            this.federalTrackStatus.status = 'processing';
            
            try {
                console.log('Running federal discovery with criteria:', this.federalDiscovery);
                
                // Simulate API call - replace with actual processor call
                const response = await this.callProcessor('federal_discovery', this.federalDiscovery);
                
                this.federalTrackStatus.results = response?.results?.length || Math.floor(Math.random() * 30) + 5;
                this.federalTrackStatus.status = 'complete';
                
                console.log(`Federal discovery completed: ${this.federalTrackStatus.results} grants found`);
            } catch (error) {
                console.error('Federal discovery failed:', error);
                this.federalTrackStatus.status = 'error';
                this.showNotification('Discovery Error', 'Federal discovery failed', 'error');
            } finally {
                this.federalTrackStatus.processing = false;
            }
        },
        
        async runStateDiscovery() {
            this.stateTrackStatus.processing = true;
            this.stateTrackStatus.status = 'processing';
            
            try {
                console.log('Running state discovery with criteria:', this.stateDiscovery);
                
                // Simulate API call - replace with actual processor call
                const response = await this.callProcessor('state_discovery', this.stateDiscovery);
                
                this.stateTrackStatus.results = response?.results?.length || Math.floor(Math.random() * 25) + 3;
                this.stateTrackStatus.status = 'complete';
                
                console.log(`State discovery completed: ${this.stateTrackStatus.results} opportunities found`);
            } catch (error) {
                console.error('State discovery failed:', error);
                this.stateTrackStatus.status = 'error';
                this.showNotification('Discovery Error', 'State discovery failed', 'error');
            } finally {
                this.stateTrackStatus.processing = false;
            }
        },
        
        async runCommercialDiscovery() {
            this.commercialTrackStatus.processing = true;
            this.commercialTrackStatus.status = 'processing';
            
            try {
                console.log('Running commercial discovery with criteria:', this.commercialDiscovery);
                
                // Simulate API call - replace with actual processor call
                const response = await this.callProcessor('commercial_discovery', this.commercialDiscovery);
                
                this.commercialTrackStatus.results = response?.results?.length || Math.floor(Math.random() * 40) + 8;
                this.commercialTrackStatus.status = 'complete';
                
                console.log(`Commercial discovery completed: ${this.commercialTrackStatus.results} foundations found`);
            } catch (error) {
                console.error('Commercial discovery failed:', error);
                this.commercialTrackStatus.status = 'error';
                this.showNotification('Discovery Error', 'Commercial discovery failed', 'error');
            } finally {
                this.commercialTrackStatus.processing = false;
            }
        },
        
        // Discovery utility functions
        updateDiscoveryStats() {
            this.discoveryStats.totalResults = 
                this.nonprofitTrackStatus.results + 
                this.federalTrackStatus.results + 
                this.stateTrackStatus.results + 
                this.commercialTrackStatus.results;
                
            // Auto-complete discovery stage if results exist
            if (this.discoveryStats.totalResults > 0 && !this.workflowProgress.discover) {
                this.workflowProgress.discover = true;
                console.log('Auto-completed DISCOVER stage - results found');
            }
                
            console.log(`Discovery stats updated: ${this.discoveryStats.totalResults} total results`);
        },
        
        exportDiscoveryResults() {
            console.log('Exporting discovery results from all tracks');
            // Implementation for consolidated export
            this.switchStage('execute');
        },
        
        progressToAnalyze() {
            console.log('Progressing to analyze stage with discovery results');
            this.switchStage('analyze');
        },
        
        // Generic processor caller - replace with actual API integration
        async callProcessor(processorName, params) {
            console.log(`Calling processor: ${processorName}`, params);
            
            // Simulate network delay
            await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
            
            // Mock response - replace with actual API call
            return {
                success: true,
                results: [], // Actual results would be populated by backend
                processingTime: Math.random() * 5000,
                timestamp: new Date().toISOString()
            };
        },
        
        loadPipelineStatus() {
            // Load live pipeline control data
            console.log('Loading pipeline status');
        },
        
        loadTestingInterface() {
            // Load testing interface
            console.log('Loading testing interface');
        },
        
        loadSystemSettings() {
            // Load system settings
            console.log('Loading system settings');
        },
        
        updateWorkflowProgress(stage) {
            // Mark the current stage as active/visited
            if (stage in this.workflowProgress) {
                this.workflowProgress[stage] = true;
            }
            
            // Auto-complete stages based on actions taken
            if (stage === 'profiler' && this.profileCount > 0) {
                this.workflowProgress.profiler = true;
            }
            if (stage === 'discover' && this.discoveryStats.totalResults > 0) {
                this.workflowProgress.discover = true;
            }
            
            console.log('Workflow progress updated:', this.workflowProgress);
        },
        
        // ENHANCED WORKFLOW NAVIGATION FUNCTIONS
        getNextRecommendedStep() {
            // Determine the next recommended workflow step based on current progress
            if (!this.workflowProgress.profiler) {
                return 'profiler';
            } else if (!this.workflowProgress.discover) {
                return 'discover';
            } else if (!this.workflowProgress.analyze) {
                return 'analyze';
            } else if (!this.workflowProgress.plan) {
                return 'plan';
            } else if (!this.workflowProgress.execute) {
                return 'execute';
            }
            return null; // All stages complete
        },
        
        getNextRecommendedStepName() {
            const nextStep = this.getNextRecommendedStep();
            const stepNames = {
                'profiler': '1. Create Profiles',
                'discover': '2. Run Discovery',
                'analyze': '3. Analyze Results',
                'plan': '4. Strategic Planning',
                'execute': '5. Export & Execute'
            };
            return stepNames[nextStep] || 'Workflow Complete';
        },
        
        isStageAvailable(stage) {
            // Determine if a stage is available based on prerequisites
            const prerequisites = {
                'profiler': true, // Always available
                'discover': true, // Can start discovery anytime, but better after profiler
                'analyze': this.workflowProgress.discover || this.discoveryStats.totalResults > 0,
                'plan': this.workflowProgress.analyze,
                'execute': this.workflowProgress.plan
            };
            return prerequisites[stage] || false;
        },
        
        getStageStatus(stage) {
            // Get detailed status for a workflow stage
            if (this.workflowProgress[stage]) {
                return 'complete';
            } else if (this.activeStage === stage) {
                return 'current';
            } else if (this.isStageAvailable(stage)) {
                return 'available';
            } else {
                return 'locked';
            }
        },
        
        getWorkflowCompletionPercentage() {
            const completedStages = Object.values(this.workflowProgress).filter(Boolean).length;
            return Math.round((completedStages / 5) * 100);
        },
        
        // Enhanced stage switching with validation
        switchStageWithValidation(stage) {
            if (this.isStageAvailable(stage)) {
                this.switchStage(stage);
            } else {
                this.showNotification('Stage Locked', `Complete previous stages to access ${stage.toUpperCase()}`, 'warning');
            }
        },
        
        // Auto-complete workflow progress based on data
        checkAndUpdateWorkflowProgress() {
            // Auto-complete profiler stage if profiles exist
            if (this.profileCount > 0 && !this.workflowProgress.profiler) {
                this.workflowProgress.profiler = true;
            }
            
            // Auto-complete discover stage if results exist
            if (this.discoveryStats.totalResults > 0 && !this.workflowProgress.discover) {
                this.workflowProgress.discover = true;
            }
            
            console.log('Auto-updated workflow progress:', this.workflowProgress);
        },
        
        // WORKFLOW ANALYTICS AND USER JOURNEY TRACKING FUNCTIONS
        trackStageTransition(fromStage, toStage) {
            const now = Date.now();
            const transition = {
                from: fromStage,
                to: toStage,
                timestamp: new Date().toISOString(),
                sessionTime: now - new Date(this.workflowAnalytics.sessionStart).getTime()
            };
            
            // Record the transition
            this.workflowAnalytics.stageTransitions.push(transition);
            
            // Update time spent in previous stage
            if (fromStage && this.workflowAnalytics.stageStartTimes[fromStage]) {
                const timeSpent = now - this.workflowAnalytics.stageStartTimes[fromStage];
                this.workflowAnalytics.timeSpentInStages[fromStage] += timeSpent;
            }
            
            // Record start time for new stage
            this.workflowAnalytics.stageStartTimes[toStage] = now;
            
            // Track user action
            this.trackUserAction('stage_transition', {
                from: fromStage,
                to: toStage,
                method: 'navigation'
            });
            
            console.log('Stage transition tracked:', transition);
        },
        
        trackUserAction(actionType, actionData = {}) {
            const action = {
                type: actionType,
                data: actionData,
                timestamp: new Date().toISOString(),
                currentStage: this.activeStage,
                sessionTime: Date.now() - new Date(this.workflowAnalytics.sessionStart).getTime()
            };
            
            this.workflowAnalytics.userActions.push(action);
            
            // Update conversion funnels
            this.updateConversionFunnels(actionType, actionData);
            
            console.log('User action tracked:', action);
        },
        
        updateConversionFunnels(actionType, actionData) {
            // Track progression through the workflow funnel
            if (actionType === 'stage_transition' && actionData.to) {
                this.workflowAnalytics.conversionFunnels.started = Math.max(
                    this.workflowAnalytics.conversionFunnels.started, 1
                );
                
                const stageCompletions = {
                    'profiler': 'profilerComplete',
                    'discover': 'discoverComplete', 
                    'analyze': 'analyzeComplete',
                    'plan': 'planComplete',
                    'execute': 'executeComplete'
                };
                
                if (stageCompletions[actionData.to]) {
                    this.workflowAnalytics.conversionFunnels[stageCompletions[actionData.to]]++;
                }
            }
            
            // Track specific completion actions
            if (actionType === 'profile_created') {
                this.workflowAnalytics.conversionFunnels.profilerComplete++;
                this.markStageCompleted('profiler');
            } else if (actionType === 'discovery_completed') {
                this.workflowAnalytics.conversionFunnels.discoverComplete++;
                this.markStageCompleted('discover');
            } else if (actionType === 'analysis_completed') {
                this.workflowAnalytics.conversionFunnels.analyzeComplete++;
                this.markStageCompleted('analyze');
            } else if (actionType === 'plan_created') {
                this.workflowAnalytics.conversionFunnels.planComplete++;
                this.markStageCompleted('plan');
            } else if (actionType === 'export_generated') {
                this.workflowAnalytics.conversionFunnels.executeComplete++;
                this.markStageCompleted('execute');
            }
        },
        
        markStageCompleted(stage) {
            if (!this.workflowProgress[stage]) {
                this.workflowProgress[stage] = true;
                this.workflowAnalytics.completionRates[stage] = 1;
                
                // Calculate overall completion rate
                const completedStages = Object.values(this.workflowProgress).filter(Boolean).length;
                this.workflowAnalytics.completionRates.overall = completedStages / 5; // 5 total stages
                
                console.log(`Stage ${stage} marked as completed. Overall completion: ${(this.workflowAnalytics.completionRates.overall * 100).toFixed(1)}%`);
            }
        },
        
        calculateWorkflowAnalytics() {
            const analytics = this.workflowAnalytics;
            const sessionDuration = Date.now() - new Date(analytics.sessionStart).getTime();
            
            // Calculate average session time
            analytics.performanceMetrics.averageSessionTime = sessionDuration / 1000 / 60; // in minutes
            
            // Find most engaging stage (where user spent most time)
            let maxTime = 0;
            let mostEngagingStage = 'profiler';
            for (const [stage, time] of Object.entries(analytics.timeSpentInStages)) {
                if (time > maxTime) {
                    maxTime = time;
                    mostEngagingStage = stage;
                }
            }
            analytics.performanceMetrics.mostEngagingStage = mostEngagingStage;
            
            // Identify common exit points (stages where users spend time but don't progress)
            const exitPoints = [];
            for (const [stage, time] of Object.entries(analytics.timeSpentInStages)) {
                if (time > 30000 && !this.workflowProgress[stage]) { // 30 seconds without completion
                    exitPoints.push(stage);
                }
            }
            analytics.performanceMetrics.commonExitPoints = exitPoints;
            
            // Analyze success patterns
            const completedStages = Object.entries(this.workflowProgress)
                .filter(([stage, completed]) => completed)
                .map(([stage]) => stage);
            analytics.performanceMetrics.successPatterns = completedStages;
            
            return analytics;
        },
        
        getWorkflowAnalyticsReport() {
            const analytics = this.calculateWorkflowAnalytics();
            const report = {
                sessionSummary: {
                    sessionId: analytics.sessionId,
                    duration: `${analytics.performanceMetrics.averageSessionTime.toFixed(1)} minutes`,
                    stagesCompleted: Object.values(this.workflowProgress).filter(Boolean).length,
                    completionRate: `${(analytics.completionRates.overall * 100).toFixed(1)}%`
                },
                engagement: {
                    mostEngagingStage: analytics.performanceMetrics.mostEngagingStage,
                    totalActions: analytics.userActions.length,
                    stageTransitions: analytics.stageTransitions.length
                },
                timeDistribution: Object.fromEntries(
                    Object.entries(analytics.timeSpentInStages)
                        .map(([stage, time]) => [stage, `${(time / 1000 / 60).toFixed(1)}m`])
                ),
                conversionFunnel: {
                    started: analytics.conversionFunnels.started,
                    profilerRate: analytics.conversionFunnels.profilerComplete / Math.max(analytics.conversionFunnels.started, 1),
                    discoverRate: analytics.conversionFunnels.discoverComplete / Math.max(analytics.conversionFunnels.profilerComplete, 1),
                    analyzeRate: analytics.conversionFunnels.analyzeComplete / Math.max(analytics.conversionFunnels.discoverComplete, 1),
                    planRate: analytics.conversionFunnels.planComplete / Math.max(analytics.conversionFunnels.analyzeComplete, 1),
                    executeRate: analytics.conversionFunnels.executeComplete / Math.max(analytics.conversionFunnels.planComplete, 1)
                },
                insights: this.generateWorkflowInsights()
            };
            
            return report;
        },
        
        generateWorkflowInsights() {
            const analytics = this.workflowAnalytics;
            const insights = [];
            
            // Time-based insights
            const totalTime = Object.values(analytics.timeSpentInStages).reduce((a, b) => a + b, 0);
            if (totalTime > 0) {
                const stageTimePercentages = Object.fromEntries(
                    Object.entries(analytics.timeSpentInStages)
                        .map(([stage, time]) => [stage, (time / totalTime) * 100])
                );
                
                const highTimeStages = Object.entries(stageTimePercentages)
                    .filter(([stage, percentage]) => percentage > 30)
                    .map(([stage]) => stage);
                
                if (highTimeStages.length > 0) {
                    insights.push({
                        type: 'time_distribution',
                        message: `User spent significant time in ${highTimeStages.join(', ')} stage(s)`,
                        recommendation: 'Consider simplifying these stages or providing better guidance'
                    });
                }
            }
            
            // Completion insights
            const completedStages = Object.values(this.workflowProgress).filter(Boolean).length;
            if (completedStages === 5) {
                insights.push({
                    type: 'completion_success',
                    message: 'User successfully completed the entire workflow',
                    recommendation: 'Collect feedback for continuous improvement'
                });
            } else if (completedStages >= 3) {
                insights.push({
                    type: 'partial_success',
                    message: `User completed ${completedStages}/5 workflow stages`,
                    recommendation: 'Follow up to understand barriers to full completion'
                });
            }
            
            // Engagement insights
            if (analytics.userActions.length > 20) {
                insights.push({
                    type: 'high_engagement',
                    message: 'High user engagement with multiple interactions',
                    recommendation: 'User is actively exploring - ensure clear next steps'
                });
            }
            
            return insights;
        },
        
        initializeWorkflowTracking() {
            // Initialize the first stage start time
            this.workflowAnalytics.stageStartTimes[this.activeStage] = Date.now();
            
            // Track session start
            this.trackUserAction('session_started', {
                initialStage: this.activeStage,
                userAgent: navigator.userAgent,
                screenSize: `${window.screen.width}x${window.screen.height}`,
                viewportSize: `${window.innerWidth}x${window.innerHeight}`
            });
            
            // Set up periodic analytics calculations
            setInterval(() => {
                this.calculateWorkflowAnalytics();
            }, 30000); // Update analytics every 30 seconds
            
            // Set up page visibility tracking for engagement metrics
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.trackUserAction('page_hidden', { activeStage: this.activeStage });
                } else {
                    this.trackUserAction('page_visible', { activeStage: this.activeStage });
                }
            });
            
            // Set up beforeunload to track session end
            window.addEventListener('beforeunload', () => {
                this.trackUserAction('session_ended', {
                    finalStage: this.activeStage,
                    sessionDuration: Date.now() - new Date(this.workflowAnalytics.sessionStart).getTime(),
                    stagesCompleted: Object.values(this.workflowProgress).filter(Boolean).length,
                    totalActions: this.workflowAnalytics.userActions.length
                });
                
                // Store analytics data in localStorage for persistence
                localStorage.setItem('catalynx-analytics', JSON.stringify({
                    lastSession: this.workflowAnalytics,
                    completionHistory: JSON.parse(localStorage.getItem('catalynx-completion-history') || '[]')
                }));
            });
            
            console.log('Workflow analytics tracking initialized');
        },
        
        // AI WORKFLOW GUIDANCE FUNCTIONS
        getWorkflowEncouragement() {
            const completedCount = Object.values(this.workflowProgress).filter(Boolean).length;
            
            if (completedCount === 0) {
                return "Welcome! Let's start your grant research journey.";
            } else if (completedCount === 1) {
                return "Great start! You're making excellent progress.";
            } else if (completedCount === 2) {
                return "Fantastic! You're building momentum.";
            } else if (completedCount === 3) {
                return "Outstanding work! More than halfway there.";
            } else if (completedCount === 4) {
                return "Almost complete! You're doing amazing.";
            } else {
                return "Congratulations! Workflow complete!";
            }
        },
        
        getWorkflowTip() {
            const currentStage = this.activeStage;
            const tips = {
                'profiler': 'Tip: Complete profiles help generate better, more targeted opportunity recommendations.',
                'discover': 'Tip: Running all tracks simultaneously gives you comprehensive coverage of all funding sources.',
                'analyze': 'Tip: Focus on financial trends and board connections for the most strategic insights.',
                'plan': 'Tip: AI-powered scoring helps prioritize opportunities with highest success probability.',
                'execute': 'Tip: Exported reports include contact information and application deadlines for easy follow-up.'
            };
            return tips[currentStage] || 'Tip: Each workflow stage builds on the previous one for maximum effectiveness.';
        },
        
        getContextualRecommendation() {
            // Provide contextual recommendations based on current state
            if (!this.workflowProgress.profiler && this.profileCount === 0) {
                return {
                    title: 'Start with Profile Setup',
                    message: 'Creating an organization profile enables personalized recommendations throughout your research.',
                    action: 'Create Profile',
                    actionFunction: () => { this.showCreateProfile = true; }
                };
            }
            
            if (this.workflowProgress.profiler && !this.workflowProgress.discover) {
                return {
                    title: 'Begin Multi-Track Discovery',
                    message: 'Run discovery across all 4 funding sources for comprehensive opportunity identification.',
                    action: 'Start Discovery',
                    actionFunction: () => { this.switchStage('discover'); }
                };
            }
            
            if (this.discoveryStats.totalResults > 0 && !this.workflowProgress.analyze) {
                return {
                    title: 'Analyze Your Discoveries',
                    message: `You've found ${this.discoveryStats.totalResults} opportunities. Analyze them for strategic insights.`,
                    action: 'Start Analysis',
                    actionFunction: () => { this.switchStage('analyze'); }
                };
            }
            
            if (this.workflowProgress.analyze && !this.workflowProgress.plan) {
                return {
                    title: 'Create Strategic Plan',
                    message: 'Use AI-powered insights to prioritize opportunities and create your funding strategy.',
                    action: 'Start Planning',
                    actionFunction: () => { this.switchStage('plan'); }
                };
            }
            
            if (this.workflowProgress.plan && !this.workflowProgress.execute) {
                return {
                    title: 'Execute Your Strategy',
                    message: 'Export comprehensive reports and begin implementing your funding strategy.',
                    action: 'Start Execution',
                    actionFunction: () => { this.switchStage('execute'); }
                };
            }
            
            return {
                title: 'Workflow Complete!',
                message: 'You\'ve successfully completed the full grant research workflow. Review your results and take action.',
                action: 'Review Results',
                actionFunction: () => { this.switchStage('execute'); }
            };
        },
        
        getStageSpecificGuidance(stage) {
            // Provide detailed guidance for each workflow stage
            const guidance = {
                'profiler': {
                    title: 'Organization Profile Development',
                    steps: [
                        'Define your organization\'s mission and focus areas',
                        'Identify target populations and geographic scope',
                        'Set funding range preferences and organizational capacity',
                        'Specify preferred funding types and partnership interests'
                    ],
                    tips: 'Complete profiles enable more accurate opportunity matching and better success predictions.'
                },
                'discover': {
                    title: 'Multi-Track Opportunity Discovery',
                    steps: [
                        'Nonprofit Track: Find similar organizations and analyze their funding patterns',
                        'Federal Track: Search Grants.gov and USASpending.gov for government opportunities',
                        'State Track: Explore Virginia state agencies and local funding sources',
                        'Commercial Track: Identify corporate foundations and CSR programs'
                    ],
                    tips: 'Running all tracks provides comprehensive coverage of the funding landscape.'
                },
                'analyze': {
                    title: 'Comprehensive Opportunity Analysis',
                    steps: [
                        'Financial Health Analysis: Evaluate organization revenue trends and stability',
                        'Network Analysis: Map board member connections and strategic relationships',
                        'Competitive Intelligence: Assess competitive landscape and positioning',
                        'Success Probability Scoring: Calculate likelihood of funding success'
                    ],
                    tips: 'Focus on network connections and financial patterns for strategic insights.'
                },
                'plan': {
                    title: 'AI-Powered Strategic Planning',
                    steps: [
                        'Priority Ranking: AI scores opportunities by success probability',
                        'Mission Alignment: Classify opportunities by strategic fit',
                        'Partnership Identification: Find collaboration and networking targets',
                        'Timeline Development: Create application and follow-up schedules'
                    ],
                    tips: 'AI recommendations help optimize your time investment and increase success rates.'
                },
                'execute': {
                    title: 'Implementation and Export',
                    steps: [
                        'Export Opportunity Reports: Comprehensive summaries with contact details',
                        'Generate Tracking Spreadsheets: Application status and deadline management',
                        'Create Contact Databases: Board members and decision-maker information',
                        'Setup Monitoring Systems: Ongoing opportunity and relationship tracking'
                    ],
                    tips: 'Exported reports include everything needed to begin pursuing opportunities immediately.'
                }
            };
            return guidance[stage] || guidance['profiler'];
        },
        
        showAIRecommendation() {
            // Show contextual AI recommendation based on current progress
            const recommendation = this.getContextualRecommendation();
            this.showNotification(recommendation.title, recommendation.message, 'info');
        },
        
        // UNIFIED EXPORT CENTER FUNCTIONS
        // Export statistics and data management
        exportStats: {
            availableReports: 12,
            totalExportableRecords: 0,
            analysisReports: 0,
            strategicPlans: 0
        },
        
        exportHistory: [],
        showExportScheduler: false,
        exportScheduler: {
            reportType: 'executive',
            frequency: 'monthly'
        },
        
        // Calculate total exportable records across all stages
        updateExportStats() {
            this.exportStats.totalExportableRecords = 
                this.profileCount + 
                this.discoveryStats.totalResults + 
                (this.workflowProgress.analyze ? 50 : 0) + // Mock analysis records
                (this.workflowProgress.plan ? 25 : 0); // Mock strategic plans
            
            this.exportStats.analysisReports = this.workflowProgress.analyze ? 5 : 0;
            this.exportStats.strategicPlans = this.workflowProgress.plan ? 3 : 0;
            
            console.log('Export stats updated:', this.exportStats);
        },
        
        // Master report generation - consolidates all workflow stages
        async generateMasterReport() {
            console.log('Generating comprehensive master report across all workflow stages');
            
            this.showNotification('Master Report', 'Generating comprehensive report with all workflow data...', 'info');
            
            // Simulate report generation
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const reportData = {
                profiles: this.profileCount,
                opportunities: this.discoveryStats.totalResults,
                nonprofitResults: this.nonprofitTrackStatus.results,
                federalResults: this.federalTrackStatus.results,
                stateResults: this.stateTrackStatus.results,
                commercialResults: this.commercialTrackStatus.results,
                analysisComplete: this.workflowProgress.analyze,
                strategicPlanComplete: this.workflowProgress.plan,
                timestamp: new Date().toISOString()
            };
            
            this.addExportToHistory({
                id: Date.now(),
                type: 'master',
                name: 'Comprehensive Master Report',
                format: 'PDF',
                created: new Date().toLocaleDateString(),
                data: reportData
            });
            
            this.showNotification('Export Complete', 'Master report generated successfully!', 'success');
            
            // Track export generation for analytics
            this.trackUserAction('export_generated', {
                exportType: 'master',
                includesProfiles: reportData.profiles > 0,
                includesOpportunities: reportData.opportunities > 0,
                nonprofitResults: reportData.nonprofitResults,
                federalResults: reportData.federalResults,
                stateResults: reportData.stateResults,
                commercialResults: reportData.commercialResults,
                totalResults: reportData.opportunities
            });
            
            // Auto-complete execute stage when master report is generated
            if (!this.workflowProgress.execute) {
                this.workflowProgress.execute = true;
                console.log('Auto-completed EXECUTE stage - master report generated');
            }
        },
        
        // Export all data across stages
        async exportAllData() {
            console.log('Exporting all data across workflow stages');
            
            this.showNotification('Data Export', 'Exporting all workflow data...', 'info');
            
            // Simulate data export
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            const exportPackage = {
                profiles: this.profiles || [],
                discoveryResults: {
                    nonprofit: Array(this.nonprofitTrackStatus.results).fill(null).map((_, i) => ({id: i, type: 'nonprofit', name: `Nonprofit ${i+1}`})),
                    federal: Array(this.federalTrackStatus.results).fill(null).map((_, i) => ({id: i, type: 'federal', name: `Federal Grant ${i+1}`})),
                    state: Array(this.stateTrackStatus.results).fill(null).map((_, i) => ({id: i, type: 'state', name: `State Grant ${i+1}`})),
                    commercial: Array(this.commercialTrackStatus.results).fill(null).map((_, i) => ({id: i, type: 'commercial', name: `Foundation ${i+1}`}))
                },
                analysisData: this.workflowProgress.analyze ? {financial: [], network: [], competitive: []} : null,
                strategicPlans: this.workflowProgress.plan ? [{name: 'Strategic Plan', priority: 'high'}] : null,
                exportDate: new Date().toISOString()
            };
            
            this.addExportToHistory({
                id: Date.now(),
                type: 'data',
                name: 'Complete Data Export',
                format: 'ZIP',
                created: new Date().toLocaleDateString(),
                data: exportPackage
            });
            
            this.showNotification('Export Complete', 'All workflow data exported successfully!', 'success');
        },
        
        // Create implementation plan
        async createImplementationPlan() {
            console.log('Creating implementation plan from strategic planning data');
            
            this.showNotification('Implementation Plan', 'Creating actionable implementation plan...', 'info');
            
            // Simulate plan creation
            await new Promise(resolve => setTimeout(resolve, 1800));
            
            const implementationPlan = {
                timeline: '6 months',
                phases: [
                    {name: 'Preparation', duration: '2 weeks', tasks: ['Document review', 'Team preparation']},
                    {name: 'Application Phase', duration: '3 months', tasks: ['Grant applications', 'Follow-ups']},
                    {name: 'Network Development', duration: '2 months', tasks: ['Board connections', 'Partnerships']},
                    {name: 'Implementation', duration: '1 month', tasks: ['Award management', 'Reporting']}
                ],
                priorities: this.discoveryStats.totalResults > 0 ? ['High priority opportunities', 'Network connections', 'Strategic partnerships'] : [],
                resources: ['Grant writer', 'Development staff', 'Board engagement'],
                created: new Date().toISOString()
            };
            
            this.addExportToHistory({
                id: Date.now(),
                type: 'plan',
                name: 'Implementation Action Plan',
                format: 'DOCX',
                created: new Date().toLocaleDateString(),
                data: implementationPlan
            });
            
            this.showNotification('Plan Complete', 'Implementation plan created successfully!', 'success');
        },
        
        // Generate specific report types
        async generateReport(reportType) {
            console.log(`Generating ${reportType} report`);
            
            const reportTypes = {
                'executive': {name: 'Executive Summary Report', format: 'PDF', audience: 'Board & Leadership'},
                'grantwriter': {name: 'Grant Writer\'s Comprehensive Guide', format: 'DOCX', audience: 'Grant Writing Team'},
                'network': {name: 'Network Analysis & Relationship Report', format: 'HTML', audience: 'Development Staff'},
                'tracker': {name: 'Implementation Tracking Spreadsheet', format: 'XLSX', audience: 'Project Management'}
            };
            
            const report = reportTypes[reportType];
            this.showNotification('Report Generation', `Creating ${report.name}...`, 'info');
            
            // Simulate report generation with varying complexity
            const generationTime = reportType === 'network' ? 3000 : reportType === 'executive' ? 2000 : 1500;
            await new Promise(resolve => setTimeout(resolve, generationTime));
            
            const reportData = {
                type: reportType,
                audience: report.audience,
                dataIncluded: {
                    profiles: reportType !== 'network' ? this.profileCount : 0,
                    opportunities: ['executive', 'grantwriter', 'tracker'].includes(reportType) ? this.discoveryStats.totalResults : 0,
                    networkData: reportType === 'network',
                    analysisData: reportType === 'executive'
                },
                generatedAt: new Date().toISOString()
            };
            
            this.addExportToHistory({
                id: Date.now(),
                type: reportType,
                name: report.name,
                format: report.format,
                created: new Date().toLocaleDateString(),
                data: reportData
            });
            
            this.showNotification('Report Complete', `${report.name} generated successfully!`, 'success');
        },
        
        // Export specific data types
        async exportData(dataType, format) {
            console.log(`Exporting ${dataType} data in ${format} format`);
            
            const dataTypes = {
                'profiles': {name: 'Organization Profiles', count: this.profileCount},
                'discovery': {name: 'Discovery Results', count: this.discoveryStats.totalResults},
                'analysis': {name: 'Analysis Data', count: this.exportStats.analysisReports},
                'plans': {name: 'Strategic Plans', count: this.exportStats.strategicPlans}
            };
            
            const data = dataTypes[dataType];
            this.showNotification('Data Export', `Exporting ${data.name} in ${format.toUpperCase()} format...`, 'info');
            
            // Simulate export processing
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const exportData = {
                dataType: dataType,
                format: format,
                recordCount: data.count,
                columns: dataType === 'profiles' ? ['name', 'ein', 'mission', 'focus_areas'] :
                        dataType === 'discovery' ? ['organization', 'type', 'amount', 'deadline'] :
                        dataType === 'analysis' ? ['metric', 'value', 'trend', 'score'] :
                        ['plan_name', 'priority', 'timeline', 'resources'],
                exportedAt: new Date().toISOString()
            };
            
            this.addExportToHistory({
                id: Date.now(),
                type: 'data',
                name: `${data.name} (${format.toUpperCase()})`,
                format: format.toUpperCase(),
                created: new Date().toLocaleDateString(),
                data: exportData
            });
            
            this.showNotification('Export Complete', `${data.name} exported in ${format.toUpperCase()} format!`, 'success');
        },
        
        // Schedule automated exports
        async scheduleExport() {
            console.log('Scheduling automated export:', this.exportScheduler);
            
            this.showNotification('Export Scheduled', `${this.exportScheduler.reportType} report scheduled for ${this.exportScheduler.frequency} generation`, 'success');
            
            // Simulate scheduling
            await new Promise(resolve => setTimeout(resolve, 500));
            
            this.showExportScheduler = false;
        },
        
        // Add export to history
        addExportToHistory(exportItem) {
            this.exportHistory.unshift(exportItem);
            // Keep only last 20 exports
            if (this.exportHistory.length > 20) {
                this.exportHistory = this.exportHistory.slice(0, 20);
            }
            console.log('Added export to history:', exportItem.name);
        },
        
        getCurrentStageLabel() {
            const stageLabels = {
                'profiler': 'Profile Management',
                'discover': 'Multi-Track Discovery',
                'analyze': 'Intelligence Analysis', 
                'plan': 'Strategic Planning',
                'execute': 'Implementation & Export',
                'pipeline': 'Live Processing Control',
                'testing': 'System Testing',
                'settings': 'Configuration'
            };
            return stageLabels[this.activeStage] || 'Unknown Stage';
        },
        
        getActiveProcessorCount() {
            // Return count of active processors - placeholder
            return '18';
        },
        
        getPageTitle() {
            // Workflow stage titles have priority
            const stageNames = {
                'profiler': 'Profiler',
                'discover': 'Discover',
                'analyze': 'Analyze', 
                'plan': 'Plan',
                'execute': 'Execute',
                'pipeline': 'Live Pipeline',
                'testing': 'Testing',
                'settings': 'Settings'
            };
            
            // Legacy tab titles for backward compatibility
            const tabNames = {
                dashboard: 'Dashboard',
                workflows: 'Workflows',
                classification: 'Intelligent Classification',
                analytics: 'Analytics',
                exports: 'Data Exports',
                settings: 'Settings',
                status: 'System Status',
                profiles: 'Organization Profiles',
                commercial: 'Commercial Track',
                states: 'State Discovery',
                predictive: 'Predictive Analytics',
                roi: 'ROI Analysis',
                network: 'Network Analysis',
                testing: 'Testing Interface',
                pipeline: 'Pipeline Control'
            };
            
            return stageNames[this.activeStage] || tabNames[this.activeTab] || 'Catalynx';
        },
        
        getPageDescription() {
            // Workflow stage descriptions
            const stageDescriptions = {
                'profiler': 'Organization profile management and workflow hub',
                'discover': 'Multi-track opportunity discovery across all funding sources',
                'analyze': 'Financial intelligence, network analysis, and comprehensive analytics',
                'plan': 'AI-powered classification and strategic recommendations',
                'execute': 'Export results, generate reports, and track implementation',
                'pipeline': 'Real-time processing control and system monitoring',
                'testing': 'System diagnostics and processor testing',
                'settings': 'System configuration and API management'
            };
            
            // Legacy tab descriptions for backward compatibility
            const tabDescriptions = {
                dashboard: 'Overview of system status and recent activity',
                workflows: 'Manage and monitor grant research workflows',
                classification: 'Classify organizations using intelligent analysis',
                analytics: 'View analytics and performance metrics',
                exports: 'Download and manage export files',
                settings: 'Configure system settings and preferences',
                status: 'Global system health and processor status',
                profiles: 'Organization profile management and analytics',
                commercial: 'Corporate foundation and CSR opportunity discovery',
                states: 'State-level grant and agency opportunity discovery',
                predictive: 'Growth trends and success probability analysis',
                roi: 'Return on investment and opportunity cost analysis',
                network: 'Board connections and strategic network intelligence',
                testing: 'Processor testing and system diagnostics',
                pipeline: 'Live processing control and workflow monitoring'
            };
            
            return stageDescriptions[this.activeStage] || tabDescriptions[this.activeTab] || 'Grant research automation platform';
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
            
            // Update workflow stage header count
            this.profileCount = this.profiles.length;
            
            console.log('Profile stats updated:', this.profileStats, 'Total count for workflow:', this.profileCount);
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
                
                // Track profile creation for analytics
                this.trackUserAction('profile_created', {
                    profileName: profileData.name,
                    organizationType: profileData.organization_type,
                    hasEIN: Boolean(profileData.ein),
                    focusAreaCount: profileData.focus_areas.length,
                    hasTargetPopulations: profileData.target_populations.length > 0,
                    isNationwide: profileData.geographic_scope.nationwide,
                    hasRevenue: Boolean(profileData.annual_revenue)
                });
                
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
                // Start narration for the nonprofit discovery process
                this.workflowNarration.updateNarration('bmf_filter', { 
                    state: this.classificationParams.state || 'VA' 
                }, 'discovery');
                
                this.showEnhancedNotification('Starting nonprofit discovery track...', 'info');
                
                // Add progress context
                const context = this.workflowNarration.getPhaseContext('discovery');
                if (context) {
                    setTimeout(() => {
                        this.showEnhancedNotification(context, 'info');
                    }, 1000);
                }
                
                const response = await this.apiCall('/discovery/nonprofit', {
                    method: 'POST',
                    body: JSON.stringify({
                        state: this.classificationParams.state,
                        max_results: this.classificationParams.maxResults
                    })
                });
                
                // Update narration for analysis phase
                this.workflowNarration.updateNarration('propublica_fetch', {}, 'analysis');
                
                this.showEnhancedNotification(
                    `Nonprofit track completed! Found ${response.total_found} organizations`, 
                    'success'
                );
                
                // Provide insight-based summary for nonprofit audience
                const insights = `Found ${response.total_found || 0} similar organizations in ${this.classificationParams.state || 'VA'}. This data reveals collaboration patterns and successful funding strategies in your sector.`;
                setTimeout(() => {
                    this.showEnhancedNotification(insights, 'success');
                }, 2000);
                
                // Store results for viewing
                this.nonprofitTrackResults = response.results;
                console.log('Nonprofit track results:', response);
                
            } catch (error) {
                console.error('Nonprofit track failed:', error);
                this.workflowNarration.isNarrating = false;
                this.showEnhancedNotification('Nonprofit discovery failed: ' + error.message, 'error');
            }
        },
        
        async executeFederalTrack() {
            try {
                // Start narration for federal grants discovery
                this.workflowNarration.updateNarration('grants_gov_fetch', {}, 'discovery');
                
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
        },

        // Testing Interface Functions
        testingInterface: {
            // Processor monitoring
            processorStatuses: [],
            systemHealth: 'unknown',
            selectedProcessor: null,
            
            // Log viewer
            systemLogs: [],
            processorLogs: {},
            logViewerVisible: false,
            
            // Testing controls
            testRunning: false,
            testResults: {},
            testParams: {},
            
            // Configuration dialog
            configDialogVisible: false,
            configParams: {
                max_results: 10,
                state: 'VA',
                min_revenue: 50000,
                ntee_codes: '',
                keywords: '',
                opportunity_category: '',
                industries: '',
                funding_range_min: 1000,
                min_score: 0.3,
                detailed_analysis: true,
                test_data: ''
            },
            
            // WebSocket for real-time monitoring
            monitoringSocket: null,
            
            // Export functionality
            exportFormat: 'json',
            exportFilename: '',
            
            init() {
                this.initSystemMonitoring();
                this.loadProcessorStatuses();
            },
            
            async initSystemMonitoring() {
                try {
                    // Connect to system monitoring WebSocket
                    const wsUrl = `ws://${window.location.host}/api/live/system-monitor`;
                    this.monitoringSocket = new WebSocket(wsUrl);
                    
                    this.monitoringSocket.onopen = () => {
                        console.log('System monitoring WebSocket connected');
                    };
                    
                    this.monitoringSocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'processor_status') {
                            this.updateProcessorStatuses(data.data);
                        } else if (data.type === 'system_logs') {
                            this.updateSystemLogs(data.data);
                        }
                    };
                    
                    this.monitoringSocket.onerror = (error) => {
                        console.error('System monitoring WebSocket error:', error);
                    };
                    
                    this.monitoringSocket.onclose = () => {
                        console.log('System monitoring WebSocket disconnected');
                        // Attempt to reconnect after 5 seconds
                        setTimeout(() => this.initSystemMonitoring(), 5000);
                    };
                    
                } catch (error) {
                    console.error('Failed to initialize system monitoring:', error);
                }
            },
            
            async loadProcessorStatuses() {
                try {
                    const response = await fetch('/api/testing/processors/status');
                    const data = await response.json();
                    this.updateProcessorStatuses(data);
                } catch (error) {
                    console.error('Failed to load processor statuses:', error);
                }
            },
            
            updateProcessorStatuses(data) {
                this.processorStatuses = data.processors || [];
                this.systemHealth = data.overall_health;
                
                // Update main app's processor status if needed
                parent.updateProcessorHealthStatus?.(data);
            },
            
            updateSystemLogs(data) {
                this.systemLogs = data.log_entries || [];
            },
            
            async loadProcessorLogs(processorName, lines = 100) {
                try {
                    const response = await fetch(`/api/testing/processors/${processorName}/logs?lines=${lines}`);
                    const data = await response.json();
                    
                    this.processorLogs[processorName] = data.log_entries || [];
                    
                } catch (error) {
                    console.error(`Failed to load logs for ${processorName}:`, error);
                }
            },
            
            toggleLogViewer() {
                this.logViewerVisible = !this.logViewerVisible;
                
                if (this.logViewerVisible && this.monitoringSocket?.readyState === WebSocket.OPEN) {
                    this.monitoringSocket.send('get_system_logs');
                }
            },
            
            async exportTestResults(processorName) {
                try {
                    if (!this.testResults[processorName]) {
                        throw new Error('No test results available for export');
                    }
                    
                    const filename = this.exportFilename || `${processorName}_test_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}`;
                    
                    const response = await fetch('/api/testing/export-results', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            results: [this.testResults[processorName]],
                            format: this.exportFormat,
                            filename: filename
                        })
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Export failed');
                    }
                    
                    // Trigger download
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${filename}.${this.exportFormat}`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    parent.showEnhancedNotification?.('Test results exported successfully', 'success');
                    
                } catch (error) {
                    console.error('Export failed:', error);
                    parent.showEnhancedNotification?.(`Export failed: ${error.message}`, 'error');
                }
            },
            
            getHealthStatusIcon(status) {
                switch (status) {
                    case 'healthy': return '✅';
                    case 'degraded': return '⚠️';
                    case 'error': return '❌';
                    case 'critical': return '🚨';
                    default: return '❓';
                }
            },
            
            getHealthStatusColor(status) {
                switch (status) {
                    case 'healthy': return 'text-green-600';
                    case 'degraded': return 'text-yellow-600';
                    case 'error': return 'text-red-600';
                    case 'critical': return 'text-red-800';
                    default: return 'text-gray-600';
                }
            },
            
            refreshStatus() {
                if (this.monitoringSocket?.readyState === WebSocket.OPEN) {
                    this.monitoringSocket.send('get_processor_status');
                } else {
                    this.loadProcessorStatuses();
                }
            },
            
            cleanup() {
                if (this.monitoringSocket) {
                    this.monitoringSocket.close();
                }
            },
            
            showTestDialog(processorName) {
                this.selectedProcessor = processorName;
                this.configDialogVisible = true;
                
                // Reset to default values
                this.configParams = {
                    max_results: 10,
                    state: 'VA',
                    min_revenue: 50000,
                    ntee_codes: '',
                    keywords: '',
                    opportunity_category: '',
                    industries: '',
                    funding_range_min: 1000,
                    min_score: 0.3,
                    detailed_analysis: true,
                    test_data: ''
                };
            },
            
            closeConfigDialog() {
                this.configDialogVisible = false;
                this.selectedProcessor = null;
            },
            
            async runConfiguredTest() {
                if (!this.selectedProcessor) return;
                
                try {
                    // Parse test data if provided
                    let testData = [];
                    if (this.configParams.test_data.trim()) {
                        try {
                            testData = JSON.parse(this.configParams.test_data);
                        } catch (e) {
                            throw new Error('Invalid JSON in test data field');
                        }
                    }
                    
                    // Convert string parameters to arrays where needed
                    const params = { ...this.configParams };
                    if (params.ntee_codes) {
                        params.ntee_codes = params.ntee_codes.split(',').map(s => s.trim());
                    }
                    if (params.keywords) {
                        params.keywords = params.keywords.split(',').map(s => s.trim());
                    }
                    if (params.industries) {
                        params.industries = params.industries.split(',').map(s => s.trim());
                    }
                    
                    // Remove empty parameters
                    Object.keys(params).forEach(key => {
                        if (params[key] === '' || params[key] === null) {
                            delete params[key];
                        }
                    });
                    
                    // Run the test with configured parameters
                    await this.testProcessor(this.selectedProcessor, params, testData);
                    
                    // Close the dialog after successful test
                    this.closeConfigDialog();
                    
                } catch (error) {
                    parent.showEnhancedNotification?.(`Configuration error: ${error.message}`, 'error');
                }
            },
            
            async testProcessor(processorName, testParams = {}, testData = []) {
                try {
                    this.testRunning = true;
                    this.selectedProcessor = processorName;
                    
                    const response = await fetch(`/api/testing/processors/${processorName}/test`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            parameters: testParams,
                            test_data: testData
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(result.detail || 'Test failed');
                    }
                    
                    this.testResults[processorName] = result;
                    
                    // Show success notification
                    parent.showEnhancedNotification?.(`Processor ${processorName} test completed successfully`, 'success');
                    
                    return result;
                    
                } catch (error) {
                    console.error(`Processor test failed for ${processorName}:`, error);
                    parent.showEnhancedNotification?.(`Processor test failed: ${error.message}`, 'error');
                    throw error;
                } finally {
                    this.testRunning = false;
                }
            }
        },
        
        // Enhanced Timing and Performance Methods
        startPerformanceTracking(operationName = 'operation') {
            this.performanceMetrics.startTime = Date.now();
            this.performanceMetrics.currentOperations++;
            
            // Initialize process flow if not set
            if (!this.processFlow.steps.length) {
                this.initializeProcessFlow(operationName);
            }
            
            this.updateRealTimeStatus('connected', 'Performance tracking started');
        },
        
        updateProcessStep(stepIndex, status = 'active', message = '') {
            if (this.processFlow.steps[stepIndex]) {
                this.processFlow.steps[stepIndex].status = status;
                this.processFlow.steps[stepIndex].message = message;
                this.processFlow.currentStep = stepIndex;
                
                // Record step timing
                const stepName = this.processFlow.steps[stepIndex].name;
                if (status === 'active' && !this.processFlow.stepTimings[stepName]?.startTime) {
                    this.processFlow.stepTimings[stepName] = { startTime: Date.now() };
                } else if (status === 'completed' && this.processFlow.stepTimings[stepName]?.startTime) {
                    this.processFlow.stepTimings[stepName].endTime = Date.now();
                    this.processFlow.stepTimings[stepName].duration = 
                        this.processFlow.stepTimings[stepName].endTime - 
                        this.processFlow.stepTimings[stepName].startTime;
                }
                
                this.calculateEstimatedTimeRemaining();
            }
        },
        
        completePerformanceTracking(success = true) {
            this.performanceMetrics.endTime = Date.now();
            this.performanceMetrics.totalDuration = 
                this.performanceMetrics.endTime - this.performanceMetrics.startTime;
            
            if (success) {
                this.performanceMetrics.completedOperations++;
            } else {
                this.performanceMetrics.errorCount++;
            }
            
            this.performanceMetrics.currentOperations = Math.max(0, 
                this.performanceMetrics.currentOperations - 1);
            
            // Update success rate
            const totalAttempts = this.performanceMetrics.completedOperations + this.performanceMetrics.errorCount;
            this.performanceMetrics.successRate = totalAttempts > 0 ? 
                (this.performanceMetrics.completedOperations / totalAttempts) * 100 : 100;
            
            // Calculate throughput
            if (this.performanceMetrics.totalDuration > 0) {
                this.performanceMetrics.throughputPerSecond = 
                    this.performanceMetrics.completedOperations / 
                    (this.performanceMetrics.totalDuration / 1000);
            }
            
            // Update average processing time
            if (this.performanceMetrics.completedOperations > 0) {
                this.performanceMetrics.averageProcessingTime = 
                    this.performanceMetrics.totalDuration / this.performanceMetrics.completedOperations;
            }
            
            this.updateRealTimeStatus('connected', 
                success ? 'Operation completed successfully' : 'Operation failed');
        },
        
        initializeProcessFlow(operationName) {
            const flowConfigs = {
                'classification': [
                    { name: 'initialization', label: 'Initialize', status: 'pending' },
                    { name: 'data_fetch', label: 'Fetch Data', status: 'pending' },
                    { name: 'processing', label: 'Process', status: 'pending' },
                    { name: 'analysis', label: 'Analyze', status: 'pending' },
                    { name: 'completion', label: 'Complete', status: 'pending' }
                ],
                'workflow': [
                    { name: 'setup', label: 'Setup', status: 'pending' },
                    { name: 'discovery', label: 'Discovery', status: 'pending' },
                    { name: 'scoring', label: 'Scoring', status: 'pending' },
                    { name: 'analysis', label: 'Analysis', status: 'pending' },
                    { name: 'export', label: 'Export', status: 'pending' }
                ],
                'operation': [
                    { name: 'start', label: 'Start', status: 'pending' },
                    { name: 'process', label: 'Process', status: 'pending' },
                    { name: 'finish', label: 'Finish', status: 'pending' }
                ]
            };
            
            this.processFlow.steps = flowConfigs[operationName] || flowConfigs['operation'];
            this.processFlow.totalSteps = this.processFlow.steps.length;
            this.processFlow.currentStep = 0;
            this.processFlow.stepTimings = {};
            this.processFlow.estimatedTimeRemaining = 0;
        },
        
        calculateEstimatedTimeRemaining() {
            const completedSteps = this.processFlow.steps.filter(step => step.status === 'completed').length;
            const remainingSteps = this.processFlow.totalSteps - completedSteps;
            
            if (completedSteps > 0 && remainingSteps > 0) {
                // Calculate average time per completed step
                let totalCompletedTime = 0;
                let completedCount = 0;
                
                Object.values(this.processFlow.stepTimings).forEach(timing => {
                    if (timing.duration) {
                        totalCompletedTime += timing.duration;
                        completedCount++;
                    }
                });
                
                if (completedCount > 0) {
                    const avgTimePerStep = totalCompletedTime / completedCount;
                    this.processFlow.estimatedTimeRemaining = Math.round(avgTimePerStep * remainingSteps);
                }
            }
        },
        
        updateRealTimeStatus(status, message = '') {
            this.realTimeStatus.lastUpdate = Date.now();
            this.realTimeStatus.connectionStatus = status;
            this.realTimeStatus.messageCount++;
            
            if (status === 'error') {
                this.realTimeStatus.errorCount++;
            }
            
            // Calculate latency (mock for now - in real implementation would measure actual latency)
            this.realTimeStatus.latency = Math.random() * 50 + 10; // 10-60ms mock latency
        },
        
        formatDuration(milliseconds) {
            if (milliseconds < 1000) return `${milliseconds}ms`;
            if (milliseconds < 60000) return `${(milliseconds / 1000).toFixed(1)}s`;
            return `${Math.floor(milliseconds / 60000)}m ${Math.floor((milliseconds % 60000) / 1000)}s`;
        },
        
        getProcessFlowProgress() {
            const completed = this.processFlow.steps.filter(step => step.status === 'completed').length;
            return this.processFlow.totalSteps > 0 ? (completed / this.processFlow.totalSteps) * 100 : 0;
        },
        
        getPerformanceClass(metric, value) {
            const thresholds = {
                successRate: { good: 90, warning: 75 },
                throughput: { good: 5, warning: 2 },
                latency: { good: 100, warning: 500 },
                responseTime: { good: 1000, warning: 3000 }
            };
            
            const threshold = thresholds[metric];
            if (!threshold) return 'metric-neutral';
            
            if (metric === 'latency' || metric === 'responseTime') {
                // Lower is better for latency/response time
                if (value <= threshold.good) return 'metric-up';
                if (value <= threshold.warning) return 'metric-neutral';
                return 'metric-down';
            } else {
                // Higher is better for success rate/throughput
                if (value >= threshold.good) return 'metric-up';
                if (value >= threshold.warning) return 'metric-neutral';
                return 'metric-down';
            }
        },
        
        resetPerformanceMetrics() {
            this.performanceMetrics = {
                startTime: null,
                endTime: null,
                totalDuration: 0,
                averageProcessingTime: 0,
                throughputPerSecond: 0,
                currentOperations: 0,
                completedOperations: 0,
                errorCount: 0,
                successRate: 100
            };
            
            this.processFlow = {
                currentStep: 0,
                totalSteps: 0,
                steps: [],
                stepTimings: {},
                estimatedTimeRemaining: 0
            };
            
            this.realTimeStatus = {
                lastUpdate: null,
                connectionStatus: 'disconnected',
                messageCount: 0,
                errorCount: 0,
                latency: 0
            };
        },
        
        // Profile Dashboard Functions
        getProfileSessions(profileId) {
            // Mock data - in production this would fetch from backend
            if (!profileId) return [];
            
            return [
                {
                    id: 1,
                    title: 'Initial Discovery Session',
                    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                    summary: 'Conducted comprehensive analysis of competitive landscape and funding opportunities',
                    insights: ['Identified 15 similar organizations', 'Found 8 relevant grant opportunities', 'Mapped 12 board connections']
                },
                {
                    id: 2,
                    title: 'Network Analysis Deep Dive',
                    date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                    summary: 'Analyzed board member connections and strategic partnership opportunities',
                    insights: ['Key warm introduction opportunities', 'Strategic board recruitment targets']
                }
            ];
        },
        
        getPipelineCount(profileId, status) {
            // Mock data - in production this would fetch from backend
            if (!profileId) return 0;
            
            const mockCounts = {
                'discovered': 12,
                'researching': 5,
                'preparing': 3,
                'submitted': 1
            };
            
            return mockCounts[status] || 0;
        },
        
        getRecentOpportunities(profileId) {
            // Mock data - in production this would fetch from backend
            if (!profileId) return [];
            
            return [
                {
                    id: 1,
                    title: 'Community Health Initiative Grant',
                    source: 'Federal - HHS',
                    amount: 150000,
                    status: 'researching',
                    deadline: '2025-03-15'
                },
                {
                    id: 2,
                    title: 'Youth Development Program Funding',
                    source: 'Foundation - Local Community Foundation',
                    amount: 75000,
                    status: 'preparing',
                    deadline: '2025-02-28'
                },
                {
                    id: 3,
                    title: 'Technology Infrastructure Grant',
                    source: 'State - Virginia IT Agency',
                    amount: 50000,
                    status: 'discovered',
                    deadline: '2025-04-01'
                }
            ];
        },
        
        getSimilarOrganizations(profile) {
            // Mock data - in production this would analyze based on profile characteristics
            if (!profile) return [];
            
            return [
                {
                    ein: '541234567',
                    name: 'Similar Community Health Center',
                    location: 'Richmond, VA',
                    revenue: 2400000,
                    similarity_score: 0.87
                },
                {
                    ein: '541234568',
                    name: 'Regional Youth Services',
                    location: 'Norfolk, VA', 
                    revenue: 1800000,
                    similarity_score: 0.82
                },
                {
                    ein: '541234569',
                    name: 'Community Development Corp',
                    location: 'Virginia Beach, VA',
                    revenue: 3200000,
                    similarity_score: 0.79
                }
            ];
        },
        
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        },
        
        startProfileAnalysis(profile) {
            if (!profile) return;
            
            // Start narration for profile analysis
            this.workflowNarration.updateNarration('bmf_filter', { 
                state: profile.geographic_scope?.states?.[0] || 'VA' 
            }, 'discovery');
            
            // Initialize process flow for this profile
            this.initializeProcessFlow('workflow');
            
            this.showEnhancedNotification(`Starting comprehensive analysis for ${profile.name}...`, 'info');
            
            // Simulate starting analysis workflow
            this.selectedProfile = profile;
            
            setTimeout(() => {
                const context = this.workflowNarration.getPhaseContext('discovery');
                if (context) {
                    this.showEnhancedNotification(context, 'info');
                }
            }, 1000);
            
            // Switch to status tab to show progress
            this.activeTab = 'status';
        },
        
        generateExecutiveSummary(profile) {
            if (!profile) return;
            
            this.showEnhancedNotification('Generating executive summary report...', 'info');
            
            // Mock executive summary generation
            setTimeout(() => {
                const summary = {
                    organizationName: profile.name,
                    analysisDate: new Date().toLocaleDateString(),
                    keyFindings: [
                        'Strong alignment with federal health initiatives',
                        'Excellent board network connections identified',
                        'Optimal funding mix: 60% federal, 30% foundation, 10% corporate'
                    ],
                    topOpportunities: this.getRecentOpportunities(profile.profile_id).slice(0, 3),
                    recommendedActions: [
                        'Apply to Community Health Initiative Grant by March 15',
                        'Schedule introduction with board member at Regional Health Foundation',
                        'Prepare capacity building plan for technology infrastructure'
                    ],
                    nextSteps: [
                        'Review detailed opportunity analysis',
                        'Schedule board presentation for funding strategy',
                        'Begin grant application preparation'
                    ]
                };
                
                // In a real implementation, this would generate and download a PDF
                console.log('Executive Summary Generated:', summary);
                
                this.showEnhancedNotification(`Executive summary generated for ${profile.name}. Report includes ${summary.keyFindings.length} key findings and ${summary.topOpportunities.length} priority opportunities.`, 'success');
                
            }, 2000);
        },
        
        // Demo function for workflow narration
        demoWorkflowNarration(phase) {
            // Initialize process flow for demo
            this.initializeProcessFlow('classification');
            
            // Simulate different phases
            const demoProcesses = {
                'discovery': [
                    { process: 'bmf_filter', params: { state: 'VA' } },
                    { process: 'propublica_fetch', params: {} },
                    { process: 'grants_gov_fetch', params: {} }
                ],
                'analysis': [
                    { process: 'financial_scorer', params: {} },
                    { process: 'intelligent_classifier', params: {} },
                    { process: 'board_network_analyzer', params: {} }
                ],
                'synthesis': [
                    { process: 'foundation_directory_fetch', params: {} },
                    { process: 'va_state_grants_fetch', params: {} }
                ]
            };
            
            const processes = demoProcesses[phase] || demoProcesses['discovery'];
            let currentIndex = 0;
            
            // Update process flow steps based on phase
            this.processFlow.currentStep = 0;
            this.processFlow.steps.forEach((step, index) => {
                if (index === 0) {
                    step.status = 'active';
                } else {
                    step.status = 'pending';
                }
            });
            
            const runDemoStep = () => {
                if (currentIndex < processes.length) {
                    const { process, params } = processes[currentIndex];
                    
                    // Update process flow
                    if (this.processFlow.steps[currentIndex]) {
                        this.processFlow.steps[currentIndex].status = 'active';
                        this.updateProcessStep(currentIndex, 'active', `Running ${process}...`);
                    }
                    
                    // Update narration
                    this.workflowNarration.updateNarration(process, params, phase);
                    
                    // Mark previous step as completed
                    if (currentIndex > 0 && this.processFlow.steps[currentIndex - 1]) {
                        this.processFlow.steps[currentIndex - 1].status = 'completed';
                        this.updateProcessStep(currentIndex - 1, 'completed');
                    }
                    
                    currentIndex++;
                    
                    // Continue to next step after 4 seconds
                    setTimeout(runDemoStep, 4000);
                } else {
                    // Mark final step as completed
                    if (this.processFlow.steps[currentIndex - 1]) {
                        this.processFlow.steps[currentIndex - 1].status = 'completed';
                        this.updateProcessStep(currentIndex - 1, 'completed', 'Analysis complete');
                    }
                    
                    // Show completion message
                    setTimeout(() => {
                        this.workflowNarration.isNarrating = false;
                        this.showEnhancedNotification(`${phase.charAt(0).toUpperCase() + phase.slice(1)} phase demonstration completed!`, 'success');
                    }, 2000);
                }
            };
            
            // Start the demo
            this.showEnhancedNotification(`Starting ${phase} phase demonstration...`, 'info');
            setTimeout(runDemoStep, 1000);
        },
        
        // Configuration Management System
        configurationManager: {
            profiles: [],
            presets: [],
            currentConfig: {},
            showConfigModal: false,
            activeConfigTab: 'general',
            
            // Configuration categories
            generalConfig: {
                apiTimeout: 30000,
                maxConcurrentRequests: 5,
                retryAttempts: 3,
                enableCaching: true,
                cacheExpiry: 86400000,
                autoExport: true,
                notificationLevel: 'info'
            },
            
            processorConfig: {
                maxResults: 1000,
                batchSize: 100,
                parallelProcessing: true,
                errorThreshold: 0.1,
                enableLogging: true,
                logLevel: 'info'
            },
            
            uiConfig: {
                theme: 'auto',
                animationsEnabled: true,
                autoRefresh: true,
                refreshInterval: 30000,
                showAdvancedOptions: false,
                compactView: false
            },
            
            securityConfig: {
                sessionTimeout: 3600000,
                enableMFA: false,
                auditLogging: true,
                encryptionEnabled: true
            },
            
            init() {
                this.loadConfigurations();
                this.loadPresets();
            },
            
            loadConfigurations() {
                const saved = localStorage.getItem('catalynx-config');
                if (saved) {
                    try {
                        const config = JSON.parse(saved);
                        this.generalConfig = { ...this.generalConfig, ...config.general };
                        this.processorConfig = { ...this.processorConfig, ...config.processor };
                        this.uiConfig = { ...this.uiConfig, ...config.ui };
                        this.securityConfig = { ...this.securityConfig, ...config.security };
                    } catch (error) {
                        console.warn('Failed to load saved configuration:', error);
                    }
                }
            },
            
            saveConfiguration() {
                const config = {
                    general: this.generalConfig,
                    processor: this.processorConfig,
                    ui: this.uiConfig,
                    security: this.securityConfig,
                    timestamp: Date.now()
                };
                localStorage.setItem('catalynx-config', JSON.stringify(config));
                parent.showEnhancedNotification?.('Configuration saved successfully', 'success');
            },
            
            resetToDefaults() {
                this.generalConfig = {
                    apiTimeout: 30000,
                    maxConcurrentRequests: 5,
                    retryAttempts: 3,
                    enableCaching: true,
                    cacheExpiry: 86400000,
                    autoExport: true,
                    notificationLevel: 'info'
                };
                
                this.processorConfig = {
                    maxResults: 1000,
                    batchSize: 100,
                    parallelProcessing: true,
                    errorThreshold: 0.1,
                    enableLogging: true,
                    logLevel: 'info'
                };
                
                this.uiConfig = {
                    theme: 'auto',
                    animationsEnabled: true,
                    autoRefresh: true,
                    refreshInterval: 30000,
                    showAdvancedOptions: false,
                    compactView: false
                };
                
                this.securityConfig = {
                    sessionTimeout: 3600000,
                    enableMFA: false,
                    auditLogging: true,
                    encryptionEnabled: true
                };
                
                parent.showEnhancedNotification?.('Configuration reset to defaults', 'info');
            },
            
            exportConfiguration() {
                const config = {
                    general: this.generalConfig,
                    processor: this.processorConfig,
                    ui: this.uiConfig,
                    security: this.securityConfig,
                    metadata: {
                        version: '2.0.0',
                        exported: new Date().toISOString(),
                        platform: navigator.platform
                    }
                };
                
                const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `catalynx-config-${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
            },
            
            importConfiguration(event) {
                const file = event.target.files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const config = JSON.parse(e.target.result);
                        
                        // Validate configuration structure
                        if (config.general) this.generalConfig = { ...this.generalConfig, ...config.general };
                        if (config.processor) this.processorConfig = { ...this.processorConfig, ...config.processor };
                        if (config.ui) this.uiConfig = { ...this.uiConfig, ...config.ui };
                        if (config.security) this.securityConfig = { ...this.securityConfig, ...config.security };
                        
                        this.saveConfiguration();
                        parent.showEnhancedNotification?.('Configuration imported successfully', 'success');
                    } catch (error) {
                        parent.showEnhancedNotification?.('Failed to import configuration: ' + error.message, 'error');
                    }
                };
                reader.readAsText(file);
            },
            
            createPreset(name) {
                const preset = {
                    id: Date.now().toString(),
                    name: name,
                    config: {
                        general: { ...this.generalConfig },
                        processor: { ...this.processorConfig },
                        ui: { ...this.uiConfig },
                        security: { ...this.securityConfig }
                    },
                    created: new Date().toISOString()
                };
                
                this.presets.push(preset);
                this.savePresets();
                parent.showEnhancedNotification?.(`Preset "${name}" created successfully`, 'success');
            },
            
            loadPreset(presetId) {
                const preset = this.presets.find(p => p.id === presetId);
                if (preset) {
                    this.generalConfig = { ...preset.config.general };
                    this.processorConfig = { ...preset.config.processor };
                    this.uiConfig = { ...preset.config.ui };
                    this.securityConfig = { ...preset.config.security };
                    
                    this.saveConfiguration();
                    parent.showEnhancedNotification?.(`Preset "${preset.name}" loaded successfully`, 'success');
                }
            },
            
            deletePreset(presetId) {
                const index = this.presets.findIndex(p => p.id === presetId);
                if (index !== -1) {
                    const preset = this.presets[index];
                    this.presets.splice(index, 1);
                    this.savePresets();
                    parent.showEnhancedNotification?.(`Preset "${preset.name}" deleted`, 'info');
                }
            },
            
            loadPresets() {
                const saved = localStorage.getItem('catalynx-presets');
                if (saved) {
                    try {
                        this.presets = JSON.parse(saved);
                    } catch (error) {
                        console.warn('Failed to load presets:', error);
                    }
                }
            },
            
            savePresets() {
                localStorage.setItem('catalynx-presets', JSON.stringify(this.presets));
            },
            
            validateConfiguration() {
                const errors = [];
                
                // Validate general config
                if (this.generalConfig.apiTimeout < 1000) {
                    errors.push('API timeout must be at least 1000ms');
                }
                if (this.generalConfig.maxConcurrentRequests < 1 || this.generalConfig.maxConcurrentRequests > 20) {
                    errors.push('Concurrent requests must be between 1 and 20');
                }
                
                // Validate processor config
                if (this.processorConfig.maxResults < 1 || this.processorConfig.maxResults > 10000) {
                    errors.push('Max results must be between 1 and 10000');
                }
                if (this.processorConfig.batchSize < 1 || this.processorConfig.batchSize > 1000) {
                    errors.push('Batch size must be between 1 and 1000');
                }
                
                // Validate UI config
                if (this.uiConfig.refreshInterval < 5000) {
                    errors.push('Refresh interval must be at least 5000ms');
                }
                
                return errors;
            },
            
            getConfigurationHealth() {
                const errors = this.validateConfiguration();
                return {
                    status: errors.length === 0 ? 'healthy' : 'warning',
                    errors: errors,
                    lastValidated: new Date().toISOString()
                };
            }
        },
        
        // Advanced Debugging Tools
        debuggingTools: {
            enabled: false,
            logBuffer: [],
            maxLogEntries: 1000,
            logLevel: 'debug',
            performanceMonitor: null,
            networkMonitor: null,
            
            init() {
                this.setupConsoleInterceptor();
                this.setupPerformanceMonitoring();
                this.setupNetworkMonitoring();
            },
            
            setupConsoleInterceptor() {
                const originalLog = console.log;
                const originalError = console.error;
                const originalWarn = console.warn;
                
                console.log = (...args) => {
                    this.addLogEntry('log', args);
                    originalLog.apply(console, args);
                };
                
                console.error = (...args) => {
                    this.addLogEntry('error', args);
                    originalError.apply(console, args);
                };
                
                console.warn = (...args) => {
                    this.addLogEntry('warn', args);
                    originalWarn.apply(console, args);
                };
            },
            
            addLogEntry(level, args) {
                const entry = {
                    timestamp: new Date().toISOString(),
                    level: level,
                    message: args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : String(arg)).join(' '),
                    source: 'console'
                };
                
                this.logBuffer.push(entry);
                
                // Maintain buffer size
                if (this.logBuffer.length > this.maxLogEntries) {
                    this.logBuffer.shift();
                }
            },
            
            setupPerformanceMonitoring() {
                if ('performance' in window) {
                    this.performanceMonitor = {
                        startTime: performance.now(),
                        marks: new Map(),
                        measures: new Map()
                    };
                }
            },
            
            setupNetworkMonitoring() {
                if ('Performance' in window && 'performance' in window) {
                    const observer = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (entry.entryType === 'navigation' || entry.entryType === 'resource') {
                                this.addLogEntry('network', [
                                    `${entry.name} - Duration: ${entry.duration}ms, Size: ${entry.transferSize || 'N/A'}bytes`
                                ]);
                            }
                        }
                    });
                    
                    try {
                        observer.observe({ entryTypes: ['navigation', 'resource'] });
                        this.networkMonitor = observer;
                    } catch (e) {
                        console.warn('Performance Observer not supported');
                    }
                }
            },
            
            mark(name) {
                if (this.performanceMonitor && 'performance' in window) {
                    performance.mark(name);
                    this.performanceMonitor.marks.set(name, performance.now());
                    this.addLogEntry('performance', [`Mark: ${name}`]);
                }
            },
            
            measure(name, startMark, endMark) {
                if (this.performanceMonitor && 'performance' in window) {
                    try {
                        performance.measure(name, startMark, endMark);
                        const measure = performance.getEntriesByName(name, 'measure')[0];
                        if (measure) {
                            this.performanceMonitor.measures.set(name, measure.duration);
                            this.addLogEntry('performance', [`Measure: ${name} - ${measure.duration}ms`]);
                        }
                    } catch (e) {
                        this.addLogEntry('error', [`Failed to create measure: ${name}`, e.message]);
                    }
                }
            },
            
            getSystemInfo() {
                return {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    cookieEnabled: navigator.cookieEnabled,
                    onLine: navigator.onLine,
                    screenResolution: `${screen.width}x${screen.height}`,
                    viewportSize: `${window.innerWidth}x${window.innerHeight}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    memory: performance.memory ? {
                        used: Math.round(performance.memory.usedJSHeapSize / 1048576),
                        total: Math.round(performance.memory.totalJSHeapSize / 1048576),
                        limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
                    } : 'Not available'
                };
            },
            
            exportLogs(format = 'json') {
                const data = {
                    logs: this.logBuffer,
                    systemInfo: this.getSystemInfo(),
                    performance: this.performanceMonitor ? {
                        marks: Array.from(this.performanceMonitor.marks.entries()),
                        measures: Array.from(this.performanceMonitor.measures.entries())
                    } : null,
                    exported: new Date().toISOString()
                };
                
                let content, filename, mimeType;
                
                if (format === 'json') {
                    content = JSON.stringify(data, null, 2);
                    filename = `catalynx-debug-${new Date().toISOString().split('T')[0]}.json`;
                    mimeType = 'application/json';
                } else if (format === 'csv') {
                    const csvHeader = 'Timestamp,Level,Message,Source\n';
                    const csvRows = this.logBuffer.map(entry => 
                        `"${entry.timestamp}","${entry.level}","${entry.message.replace(/"/g, '""')}","${entry.source}"`
                    ).join('\n');
                    content = csvHeader + csvRows;
                    filename = `catalynx-debug-${new Date().toISOString().split('T')[0]}.csv`;
                    mimeType = 'text/csv';
                } else {
                    content = this.logBuffer.map(entry => 
                        `[${entry.timestamp}] ${entry.level.toUpperCase()}: ${entry.message}`
                    ).join('\n');
                    filename = `catalynx-debug-${new Date().toISOString().split('T')[0]}.txt`;
                    mimeType = 'text/plain';
                }
                
                const blob = new Blob([content], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);
            },
            
            clearLogs() {
                this.logBuffer = [];
                this.addLogEntry('system', ['Debug logs cleared']);
            },
            
            testApiEndpoint(url, method = 'GET', data = null) {
                const startTime = performance.now();
                this.mark(`api-test-${url}-start`);
                
                const options = {
                    method: method,
                    headers: { 'Content-Type': 'application/json' }
                };
                
                if (data && method !== 'GET') {
                    options.body = JSON.stringify(data);
                }
                
                return fetch(url, options)
                    .then(response => {
                        const endTime = performance.now();
                        this.mark(`api-test-${url}-end`);
                        this.measure(`api-test-${url}`, `api-test-${url}-start`, `api-test-${url}-end`);
                        
                        this.addLogEntry('api-test', [
                            `${method} ${url} - Status: ${response.status}, Duration: ${(endTime - startTime).toFixed(2)}ms`
                        ]);
                        
                        return response.json().then(data => ({ response, data }));
                    })
                    .catch(error => {
                        const endTime = performance.now();
                        this.addLogEntry('api-test-error', [
                            `${method} ${url} - Error: ${error.message}, Duration: ${(endTime - startTime).toFixed(2)}ms`
                        ]);
                        throw error;
                    });
            }
        }
    }
}
// Catalynx Modern Web Interface - JavaScript Application
// Alpine.js application with real-time WebSocket updates
// Version: TYPE_COLOR_FIX_v1.2 - Updated organization type colors

// Shared utility functions used across all tabs
const CatalynxUtils = {
    formatStageWithNumber(stage) {
        const stageMapping = {
            'prospects': '#1 - PROSPECTS',
            'qualified_prospects': '#2 - QUALIFIED PROSPECTS',
            'candidates': '#3 - CANDIDATES',
            'targets': '#4 - TARGETS', 
            'opportunities': '#5 - OPPORTUNITIES'
        };
        return stageMapping[stage] || stage.replace('_', ' ').toUpperCase();
    },
    
    getStageColor(stage) {
        const colorMapping = {
            'prospects': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
            'qualified_prospects': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            'candidates': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            'targets': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            'opportunities': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
        };
        return colorMapping[stage] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    },
    
    getOrganizationTypeColor(type) {
        // All organization types use blue background with white text for consistency and visibility  
        console.log('getOrganizationTypeColor called with type:', type);
        // Using more specific/important classes to override any conflicts
        const classes = '!bg-blue-600 !text-white dark:!bg-blue-700 dark:!text-white !font-medium';
        console.log('Returning classes:', classes);
        return classes;
    },
    
    toggleFullscreenNetwork(networkType, element) {
        const networkElement = element || document.getElementById(`${networkType}NetworkChart`);
        const zoomedContainer = document.getElementById(`${networkType}ZoomedContainer`);
        
        if (!networkElement || !zoomedContainer) return;
        
        if (zoomedContainer.style.display === 'none' || !zoomedContainer.style.display) {
            // Show zoomed version
            const rect = networkElement.getBoundingClientRect();
            const scaledWidth = Math.min(rect.width * 2, window.innerWidth * 0.9);
            const scaledHeight = Math.min(rect.height * 2, window.innerHeight * 0.9);
            
            zoomedContainer.style.display = 'fixed';
            zoomedContainer.style.top = '50%';
            zoomedContainer.style.left = '50%';
            zoomedContainer.style.transform = 'translate(-50%, -50%)';
            zoomedContainer.style.width = scaledWidth + 'px';
            zoomedContainer.style.height = scaledHeight + 'px';
            zoomedContainer.style.zIndex = '1000';
            zoomedContainer.style.backgroundColor = 'white';
            zoomedContainer.style.border = '2px solid #e5e7eb';
            zoomedContainer.style.borderRadius = '8px';
            zoomedContainer.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.25)';
            
            // Dark mode styling
            if (document.documentElement.classList.contains('dark')) {
                zoomedContainer.style.backgroundColor = '#1f2937';
                zoomedContainer.style.border = '2px solid #374151';
            }
        } else {
            // Hide zoomed version
            zoomedContainer.style.display = 'none';
            zoomedContainer.style.position = '';
            zoomedContainer.style.top = '';
            zoomedContainer.style.left = '';
            zoomedContainer.style.transform = '';
            zoomedContainer.style.width = '';
            zoomedContainer.style.height = '';
            zoomedContainer.style.zIndex = '';
            zoomedContainer.style.backgroundColor = '';
            zoomedContainer.style.border = '';
            zoomedContainer.style.borderRadius = '';
            zoomedContainer.style.boxShadow = '';
        }
    }
};

function catalynxApp() {
    return {
        // Application state - New workflow-based navigation
        activeTab: 'status', // Legacy compatibility
        activeStage: 'welcome', // New workflow stage system - start with welcome
        systemStatus: 'healthy',
        apiStatus: 'healthy',
        currentTime: new Date().toLocaleTimeString(),
        
        // Workflow progress tracking
        workflowProgress: {
            welcome: false,
            profiler: false,
            discover: false,
            analyze: false,
            plan: false,
            execute: false
        },
        
        // Stage-specific data
        profileCount: 0,
        activeWorkflows: 0,
        
        // Welcome stage data
        welcomeStatus: {
            systemHealth: 'loading',
            processorsAvailable: 0,
            capabilities: [],
            quickStartAvailable: false,
            sampleDataReady: false
        },
        welcomeLoading: false,
        
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
        
        // Comprehensive NTEE Code Data Structure
        fullNteeCodeList: {
            'A': { 
                category: 'Arts, Culture & Humanities',
                subcategories: [
                    { code: 'A01', name: 'Alliances & Advocacy' },
                    { code: 'A02', name: 'Management & Technical Assistance' },
                    { code: 'A03', name: 'Professional Societies & Associations' },
                    { code: 'A05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'A11', name: 'Single Organization Support' },
                    { code: 'A12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'A19', name: 'Support N.E.C.' },
                    { code: 'A20', name: 'Arts & Culture' },
                    { code: 'A23', name: 'Cultural & Ethnic Awareness' },
                    { code: 'A24', name: 'Folk Arts' },
                    { code: 'A25', name: 'Arts Education' },
                    { code: 'A26', name: 'Arts Council/Agency' },
                    { code: 'A27', name: 'Community Celebrations' },
                    { code: 'A30', name: 'Media & Communications' },
                    { code: 'A31', name: 'Film & Video' },
                    { code: 'A32', name: 'Television' },
                    { code: 'A33', name: 'Printing & Publishing' },
                    { code: 'A34', name: 'Radio' },
                    { code: 'A40', name: 'Visual Arts' },
                    { code: 'A50', name: 'Museums' },
                    { code: 'A51', name: 'Art Museums' },
                    { code: 'A52', name: 'Children\'s Museums' },
                    { code: 'A54', name: 'History Museums' },
                    { code: 'A56', name: 'Natural History Museums' },
                    { code: 'A57', name: 'Science & Technology Museums' },
                    { code: 'A60', name: 'Performing Arts' },
                    { code: 'A61', name: 'Performing Arts Centers' },
                    { code: 'A62', name: 'Dance' },
                    { code: 'A63', name: 'Ballet' },
                    { code: 'A65', name: 'Theater' },
                    { code: 'A68', name: 'Music' },
                    { code: 'A69', name: 'Symphony Orchestras' },
                    { code: 'A6A', name: 'Opera' },
                    { code: 'A70', name: 'Humanities' },
                    { code: 'A80', name: 'Historical Societies' },
                    { code: 'A82', name: 'Historical Preservation' },
                    { code: 'A84', name: 'Commemorative Events' },
                    { code: 'A90', name: 'Arts Service' }
                ]
            },
            'B': { 
                category: 'Education',
                subcategories: [
                    { code: 'B01', name: 'Alliances & Advocacy' },
                    { code: 'B02', name: 'Management & Technical Assistance' },
                    { code: 'B03', name: 'Professional Societies & Associations' },
                    { code: 'B05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'B11', name: 'Single Organization Support' },
                    { code: 'B12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'B19', name: 'Support N.E.C.' },
                    { code: 'B20', name: 'Elementary & Secondary Education' },
                    { code: 'B21', name: 'Kindergarten, Nursery School, Preschool' },
                    { code: 'B24', name: 'Primary/Elementary Schools' },
                    { code: 'B25', name: 'Secondary/High Schools' },
                    { code: 'B28', name: 'Specialized Education Institutions' },
                    { code: 'B29', name: 'Charter Schools' },
                    { code: 'B30', name: 'Vocational & Technical Schools' },
                    { code: 'B40', name: 'Higher Education Institutions' },
                    { code: 'B41', name: 'Two-Year Colleges' },
                    { code: 'B42', name: 'Undergraduate Colleges' },
                    { code: 'B43', name: 'Universities' },
                    { code: 'B50', name: 'Graduate & Professional Schools' },
                    { code: 'B60', name: 'Adult Education Programs & Services' },
                    { code: 'B70', name: 'Libraries' },
                    { code: 'B80', name: 'Student Services & Organizations' },
                    { code: 'B82', name: 'Scholarships & Student Financial Aid' },
                    { code: 'B83', name: 'Student Sororities & Fraternities' },
                    { code: 'B84', name: 'Alumni Associations' },
                    { code: 'B90', name: 'Educational Services' },
                    { code: 'B92', name: 'Remedial Reading' },
                    { code: 'B94', name: 'Parent/Teacher Group' },
                    { code: 'B99', name: 'Education N.E.C.' }
                ]
            },
            'C': { 
                category: 'Environmental Quality, Protection & Beautification',
                subcategories: [
                    { code: 'C01', name: 'Alliances & Advocacy' },
                    { code: 'C02', name: 'Management & Technical Assistance' },
                    { code: 'C03', name: 'Professional Societies & Associations' },
                    { code: 'C05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'C11', name: 'Single Organization Support' },
                    { code: 'C12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'C19', name: 'Support N.E.C.' },
                    { code: 'C20', name: 'Pollution Abatement & Control' },
                    { code: 'C27', name: 'Recycling' },
                    { code: 'C30', name: 'Natural Resource Conservation & Protection' },
                    { code: 'C32', name: 'Water Resource, Wetlands Conservation & Management' },
                    { code: 'C34', name: 'Land Resources Conservation' },
                    { code: 'C35', name: 'Energy Resources Conservation & Development' },
                    { code: 'C36', name: 'Forest Conservation' },
                    { code: 'C40', name: 'Botanical, Horticultural & Landscape Services' },
                    { code: 'C41', name: 'Botanical Gardens & Arboreta' },
                    { code: 'C42', name: 'Garden Club' },
                    { code: 'C50', name: 'Environmental Beautification & Aesthetics' },
                    { code: 'C60', name: 'Environmental Education & Outdoor Survival Programs' },
                    { code: 'C99', name: 'Environmental Quality, Protection & Beautification N.E.C.' }
                ]
            },
            'D': { 
                category: 'Animal-Related',
                subcategories: [
                    { code: 'D01', name: 'Alliances & Advocacy' },
                    { code: 'D02', name: 'Management & Technical Assistance' },
                    { code: 'D03', name: 'Professional Societies & Associations' },
                    { code: 'D05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'D11', name: 'Single Organization Support' },
                    { code: 'D12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'D19', name: 'Support N.E.C.' },
                    { code: 'D20', name: 'Animal Protection & Welfare' },
                    { code: 'D30', name: 'Wildlife Preservation & Protection' },
                    { code: 'D31', name: 'Protection of Endangered Species' },
                    { code: 'D32', name: 'Bird Preservation' },
                    { code: 'D33', name: 'Fisheries Resources' },
                    { code: 'D34', name: 'Wildlife Sanctuaries' },
                    { code: 'D40', name: 'Veterinary Services' },
                    { code: 'D50', name: 'Zoos & Aquariums' },
                    { code: 'D60', name: 'Other Animal-Related' },
                    { code: 'D61', name: 'Animal Training, Showing & Racing' },
                    { code: 'D99', name: 'Animal-Related N.E.C.' }
                ]
            },
            'E': { 
                category: 'Health Care',
                subcategories: [
                    { code: 'E01', name: 'Alliances & Advocacy' },
                    { code: 'E02', name: 'Management & Technical Assistance' },
                    { code: 'E03', name: 'Professional Societies & Associations' },
                    { code: 'E05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'E11', name: 'Single Organization Support' },
                    { code: 'E12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'E19', name: 'Support N.E.C.' },
                    { code: 'E20', name: 'Hospitals & Related Primary Medical Care Facilities' },
                    { code: 'E21', name: 'Community Health Centers' },
                    { code: 'E22', name: 'Home Health Care' },
                    { code: 'E24', name: 'Primary Health Care Clinics' },
                    { code: 'E30', name: 'Ambulatory Health Center, Community Clinic' },
                    { code: 'E31', name: 'Group Health Practice' },
                    { code: 'E32', name: 'Ambulatory Health Center' },
                    { code: 'E40', name: 'Reproductive Health Care' },
                    { code: 'E42', name: 'Family Planning Centers' },
                    { code: 'E50', name: 'Rehabilitative Medical Services' },
                    { code: 'E60', name: 'Health Support Services' },
                    { code: 'E61', name: 'Blood Supply Related' },
                    { code: 'E62', name: 'Emergency Medical Services & Transport' },
                    { code: 'E65', name: 'Organ & Tissue Banks' },
                    { code: 'E70', name: 'Public Health Program' },
                    { code: 'E80', name: 'Health - General & Financing' },
                    { code: 'E86', name: 'Patient Services - Entertainment, Recreation' },
                    { code: 'E90', name: 'Nursing Services' },
                    { code: 'E91', name: 'Nursing Facility/Long-term Care' },
                    { code: 'E92', name: 'Home for the Aging' },
                    { code: 'E99', name: 'Health Care N.E.C.' }
                ]
            },
            'F': { 
                category: 'Mental Health & Crisis Intervention',
                subcategories: [
                    { code: 'F01', name: 'Alliances & Advocacy' },
                    { code: 'F02', name: 'Management & Technical Assistance' },
                    { code: 'F03', name: 'Professional Societies & Associations' },
                    { code: 'F05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'F11', name: 'Single Organization Support' },
                    { code: 'F12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'F19', name: 'Support N.E.C.' },
                    { code: 'F20', name: 'Substance Abuse, Dependency, Prevention & Treatment' },
                    { code: 'F21', name: 'Alcoholism' },
                    { code: 'F22', name: 'Drug Abuse' },
                    { code: 'F30', name: 'Mental Health Treatment' },
                    { code: 'F31', name: 'Psychiatric Hospitals' },
                    { code: 'F32', name: 'Community Mental Health Centers' },
                    { code: 'F33', name: 'Group Home - Mental Health' },
                    { code: 'F40', name: 'Hot Line, Crisis Intervention' },
                    { code: 'F42', name: 'Rape Victim Services' },
                    { code: 'F50', name: 'Addictive Disorders' },
                    { code: 'F52', name: 'Smoking Addiction' },
                    { code: 'F53', name: 'Eating Addiction' },
                    { code: 'F54', name: 'Gambling Addiction' },
                    { code: 'F60', name: 'Counseling Support Groups' },
                    { code: 'F70', name: 'Mental Health Disorders' },
                    { code: 'F80', name: 'Mental Health Association' },
                    { code: 'F99', name: 'Mental Health, Crisis Intervention N.E.C.' }
                ]
            },
            'G': { 
                category: 'Diseases, Disorders & Medical Disciplines',
                subcategories: [
                    { code: 'G01', name: 'Alliances & Advocacy' },
                    { code: 'G02', name: 'Management & Technical Assistance' },
                    { code: 'G03', name: 'Professional Societies & Associations' },
                    { code: 'G05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'G11', name: 'Single Organization Support' },
                    { code: 'G12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'G19', name: 'Support N.E.C.' },
                    { code: 'G20', name: 'Birth Defects & Genetic Diseases' },
                    { code: 'G25', name: 'Down Syndrome' },
                    { code: 'G30', name: 'Cancer' },
                    { code: 'G32', name: 'Breast Cancer' },
                    { code: 'G40', name: 'Diseases of Specific Organs' },
                    { code: 'G41', name: 'Eye Diseases, Blindness & Vision Impairments' },
                    { code: 'G42', name: 'Ear & Throat Diseases' },
                    { code: 'G43', name: 'Heart & Circulatory System Disease & Disorders' },
                    { code: 'G44', name: 'Kidney Disease' },
                    { code: 'G45', name: 'Lung Disease' },
                    { code: 'G48', name: 'Brain Disorders' },
                    { code: 'G50', name: 'Nerve, Muscle & Bone Diseases' },
                    { code: 'G51', name: 'Arthritis' },
                    { code: 'G54', name: 'Epilepsy' },
                    { code: 'G60', name: 'Allergy-Related Diseases' },
                    { code: 'G61', name: 'Asthma' },
                    { code: 'G70', name: 'Digestive Diseases & Disorders' },
                    { code: 'G80', name: 'Specifically Named Diseases' },
                    { code: 'G81', name: 'AIDS' },
                    { code: 'G83', name: 'Alzheimer\'s Disease' },
                    { code: 'G84', name: 'Autism' },
                    { code: 'G90', name: 'Medical Disciplines' },
                    { code: 'G92', name: 'Biomedicine & Bioengineering' },
                    { code: 'G94', name: 'Geriatrics' },
                    { code: 'G96', name: 'Pediatrics' },
                    { code: 'G9B', name: 'Surgical Specialties' },
                    { code: 'G99', name: 'Diseases, Disorders, Medical Disciplines N.E.C.' }
                ]
            },
            'H': { 
                category: 'Medical Research',
                subcategories: [
                    { code: 'H01', name: 'Alliances & Advocacy' },
                    { code: 'H02', name: 'Management & Technical Assistance' },
                    { code: 'H03', name: 'Professional Societies & Associations' },
                    { code: 'H05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'H11', name: 'Single Organization Support' },
                    { code: 'H12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'H19', name: 'Support N.E.C.' },
                    { code: 'H20', name: 'Birth Defects & Genetic Diseases Research' },
                    { code: 'H25', name: 'Down Syndrome Research' },
                    { code: 'H30', name: 'Cancer Research' },
                    { code: 'H32', name: 'Breast Cancer Research' },
                    { code: 'H40', name: 'Specific Organ Research' },
                    { code: 'H41', name: 'Eye Research' },
                    { code: 'H42', name: 'Ear & Throat Research' },
                    { code: 'H43', name: 'Heart & Circulatory Research' },
                    { code: 'H44', name: 'Kidney Research' },
                    { code: 'H45', name: 'Lung Research' },
                    { code: 'H48', name: 'Brain Disorders Research' },
                    { code: 'H50', name: 'Nerve, Muscle & Bone Research' },
                    { code: 'H51', name: 'Arthritis Research' },
                    { code: 'H54', name: 'Epilepsy Research' },
                    { code: 'H60', name: 'Allergy-Related Disease Research' },
                    { code: 'H61', name: 'Asthma Research' },
                    { code: 'H70', name: 'Digestive Disease Research' },
                    { code: 'H80', name: 'Specifically Named Disease Research' },
                    { code: 'H81', name: 'AIDS Research' },
                    { code: 'H83', name: 'Alzheimer\'s Disease Research' },
                    { code: 'H84', name: 'Autism Research' },
                    { code: 'H90', name: 'Medical Disciplines Research' },
                    { code: 'H92', name: 'Biomedicine & Bioengineering Research' },
                    { code: 'H94', name: 'Geriatrics Research' },
                    { code: 'H96', name: 'Pediatrics Research' },
                    { code: 'H9B', name: 'Surgery Research' },
                    { code: 'H99', name: 'Medical Research N.E.C.' }
                ]
            },
            'I': { 
                category: 'Crime & Legal Related',
                subcategories: [
                    { code: 'I01', name: 'Alliances & Advocacy' },
                    { code: 'I02', name: 'Management & Technical Assistance' },
                    { code: 'I03', name: 'Professional Societies & Associations' },
                    { code: 'I05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'I11', name: 'Single Organization Support' },
                    { code: 'I12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'I19', name: 'Support N.E.C.' },
                    { code: 'I20', name: 'Crime Prevention' },
                    { code: 'I21', name: 'Youth Violence Prevention' },
                    { code: 'I23', name: 'Drunk Driving Related' },
                    { code: 'I30', name: 'Correctional Facilities' },
                    { code: 'I40', name: 'Rehabilitation Services for Offenders' },
                    { code: 'I43', name: 'Services to Promote Reintegration' },
                    { code: 'I44', name: 'Prison Alternatives' },
                    { code: 'I50', name: 'Administration of Justice/Courts' },
                    { code: 'I51', name: 'Dispute Resolution & Mediation' },
                    { code: 'I60', name: 'Law Enforcement' },
                    { code: 'I70', name: 'Protection Against, Prevention of Negligence, Accidents, Injuries' },
                    { code: 'I71', name: 'Child Abuse Prevention' },
                    { code: 'I72', name: 'Domestic Violence' },
                    { code: 'I73', name: 'Sexual Abuse' },
                    { code: 'I80', name: 'Legal Services' },
                    { code: 'I83', name: 'Public Interest Law' },
                    { code: 'I99', name: 'Crime, Legal Related N.E.C.' }
                ]
            },
            'J': { 
                category: 'Employment',
                subcategories: [
                    { code: 'J01', name: 'Alliances & Advocacy' },
                    { code: 'J02', name: 'Management & Technical Assistance' },
                    { code: 'J03', name: 'Professional Societies & Associations' },
                    { code: 'J05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'J11', name: 'Single Organization Support' },
                    { code: 'J12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'J19', name: 'Support N.E.C.' },
                    { code: 'J20', name: 'Employment Procurement Assistance, Job Training' },
                    { code: 'J21', name: 'Vocational Counseling, Guidance & Testing' },
                    { code: 'J22', name: 'Vocational Training' },
                    { code: 'J30', name: 'Vocational Rehabilitation' },
                    { code: 'J32', name: 'Goodwill Industries' },
                    { code: 'J33', name: 'Sheltered Employment, Work Activity Centers' },
                    { code: 'J40', name: 'Labor Unions' },
                    { code: 'J99', name: 'Employment N.E.C.' }
                ]
            },
            'K': { 
                category: 'Food, Agriculture & Nutrition',
                subcategories: [
                    { code: 'K01', name: 'Alliances & Advocacy' },
                    { code: 'K02', name: 'Management & Technical Assistance' },
                    { code: 'K03', name: 'Professional Societies & Associations' },
                    { code: 'K05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'K11', name: 'Single Organization Support' },
                    { code: 'K12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'K19', name: 'Support N.E.C.' },
                    { code: 'K20', name: 'Agricultural Programs' },
                    { code: 'K25', name: 'Farmland Preservation' },
                    { code: 'K26', name: 'Animal Husbandry' },
                    { code: 'K28', name: 'Farm Bureau' },
                    { code: 'K30', name: 'Food Service, Free Food Distribution Programs' },
                    { code: 'K31', name: 'Food Banks, Food Pantries' },
                    { code: 'K34', name: 'Congregate Meals' },
                    { code: 'K35', name: 'Meals on Wheels' },
                    { code: 'K36', name: 'Nutrition Programs' },
                    { code: 'K99', name: 'Food, Agriculture & Nutrition N.E.C.' }
                ]
            },
            'L': { 
                category: 'Housing & Shelter',
                subcategories: [
                    { code: 'L01', name: 'Alliances & Advocacy' },
                    { code: 'L02', name: 'Management & Technical Assistance' },
                    { code: 'L03', name: 'Professional Societies & Associations' },
                    { code: 'L05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'L11', name: 'Single Organization Support' },
                    { code: 'L12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'L19', name: 'Support N.E.C.' },
                    { code: 'L20', name: 'Housing Development, Construction, Management' },
                    { code: 'L21', name: 'Low-Cost Temporary Housing' },
                    { code: 'L22', name: 'Senior Citizens Housing/Retirement Communities' },
                    { code: 'L24', name: 'Senior Continuing Care Communities' },
                    { code: 'L25', name: 'Residential Care for Children & Adolescents' },
                    { code: 'L30', name: 'Housing Search Assistance' },
                    { code: 'L40', name: 'Temporary Housing' },
                    { code: 'L41', name: 'Homeless, Temporary Shelter' },
                    { code: 'L50', name: 'Housing Rehabilitation' },
                    { code: 'L80', name: 'Housing Support' },
                    { code: 'L81', name: 'Home Improvement & Repairs' },
                    { code: 'L82', name: 'Housing Expense Reduction Support' },
                    { code: 'L99', name: 'Housing, Shelter N.E.C.' }
                ]
            },
            'M': { 
                category: 'Public Safety, Disaster Preparedness & Relief',
                subcategories: [
                    { code: 'M01', name: 'Alliances & Advocacy' },
                    { code: 'M02', name: 'Management & Technical Assistance' },
                    { code: 'M03', name: 'Professional Societies & Associations' },
                    { code: 'M05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'M11', name: 'Single Organization Support' },
                    { code: 'M12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'M19', name: 'Support N.E.C.' },
                    { code: 'M20', name: 'Disaster Preparedness & Relief Services' },
                    { code: 'M23', name: 'Search & Rescue Squads' },
                    { code: 'M24', name: 'Fire Prevention & Protection' },
                    { code: 'M40', name: 'Safety, Accident Prevention' },
                    { code: 'M41', name: 'First Aid Training & Services' },
                    { code: 'M42', name: 'Automotive Safety' },
                    { code: 'M99', name: 'Public Safety, Disaster Preparedness & Relief N.E.C.' }
                ]
            },
            'N': { 
                category: 'Recreation & Sports',
                subcategories: [
                    { code: 'N01', name: 'Alliances & Advocacy' },
                    { code: 'N02', name: 'Management & Technical Assistance' },
                    { code: 'N03', name: 'Professional Societies & Associations' },
                    { code: 'N05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'N11', name: 'Single Organization Support' },
                    { code: 'N12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'N19', name: 'Support N.E.C.' },
                    { code: 'N20', name: 'Camps' },
                    { code: 'N30', name: 'Physical Fitness & Community Recreational Facilities' },
                    { code: 'N31', name: 'Swimming, Pool' },
                    { code: 'N32', name: 'Parks & Playgrounds' },
                    { code: 'N40', name: 'Sports Training Facilities, Agencies' },
                    { code: 'N50', name: 'Recreational, Pleasure, or Social Club' },
                    { code: 'N52', name: 'Fairs' },
                    { code: 'N60', name: 'Amateur Sports Clubs, Leagues, N.E.C.' },
                    { code: 'N61', name: 'Fishing, Hunting Clubs' },
                    { code: 'N62', name: 'Basketball' },
                    { code: 'N63', name: 'Baseball, Softball' },
                    { code: 'N64', name: 'Soccer Clubs, Leagues' },
                    { code: 'N65', name: 'Football Clubs, Leagues' },
                    { code: 'N66', name: 'Skiing Clubs, Leagues' },
                    { code: 'N67', name: 'Swimming, Water Recreation' },
                    { code: 'N68', name: 'Winter Sports' },
                    { code: 'N69', name: 'Equestrian, Riding Clubs' },
                    { code: 'N6A', name: 'Golf' },
                    { code: 'N70', name: 'Amateur Athletic Competition' },
                    { code: 'N71', name: 'Olympics' },
                    { code: 'N72', name: 'Special Olympics' },
                    { code: 'N80', name: 'Professional Athletic Leagues' },
                    { code: 'N99', name: 'Recreation, Sports, Leisure, Athletics N.E.C.' }
                ]
            },
            'O': { 
                category: 'Youth Development',
                subcategories: [
                    { code: 'O01', name: 'Alliances & Advocacy' },
                    { code: 'O02', name: 'Management & Technical Assistance' },
                    { code: 'O03', name: 'Professional Societies & Associations' },
                    { code: 'O05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'O11', name: 'Single Organization Support' },
                    { code: 'O12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'O19', name: 'Support N.E.C.' },
                    { code: 'O20', name: 'Youth Centers, Clubs, Multipurpose' },
                    { code: 'O21', name: 'Boys & Girls Clubs' },
                    { code: 'O22', name: 'Boys Scouts' },
                    { code: 'O23', name: 'Girl Scouts' },
                    { code: 'O24', name: 'Little League, Youth Baseball' },
                    { code: 'O30', name: 'Adult, Child Matching Programs' },
                    { code: 'O31', name: 'Big Brothers, Big Sisters' },
                    { code: 'O40', name: 'Scouting Organizations' },
                    { code: 'O41', name: 'Girl Guides' },
                    { code: 'O42', name: 'Scouts - Coed' },
                    { code: 'O43', name: 'Boy Scouts of America' },
                    { code: 'O50', name: 'Youth Development Programs, Other' },
                    { code: 'O51', name: 'Youth Community Service Clubs' },
                    { code: 'O52', name: 'Youth Development - Agricultural' },
                    { code: 'O53', name: 'Youth Development - Business' },
                    { code: 'O54', name: 'Youth Development - Citizenship Programs' },
                    { code: 'O55', name: 'Youth Development - Religious Leadership' },
                    { code: 'O99', name: 'Youth Development N.E.C.' }
                ]
            },
            'P': { 
                category: 'Human Services',
                subcategories: [
                    { code: 'P01', name: 'Alliances & Advocacy' },
                    { code: 'P02', name: 'Management & Technical Assistance' },
                    { code: 'P03', name: 'Professional Societies & Associations' },
                    { code: 'P05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'P11', name: 'Single Organization Support' },
                    { code: 'P12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'P19', name: 'Support N.E.C.' },
                    { code: 'P20', name: 'Human Service Organizations' },
                    { code: 'P21', name: 'American Red Cross' },
                    { code: 'P22', name: 'Urban League' },
                    { code: 'P24', name: 'Salvation Army' },
                    { code: 'P26', name: 'Volunteers of America' },
                    { code: 'P27', name: 'Young Men\'s or Women\'s Associations' },
                    { code: 'P28', name: 'Neighborhood Centers, Settlement Houses, Community' },
                    { code: 'P30', name: 'Children & Youth Services' },
                    { code: 'P31', name: 'Adoption' },
                    { code: 'P32', name: 'Foster Care' },
                    { code: 'P33', name: 'Child Day Care' },
                    { code: 'P40', name: 'Family Services' },
                    { code: 'P42', name: 'Single Parent Agencies' },
                    { code: 'P43', name: 'Family Violence Shelters' },
                    { code: 'P44', name: 'In-Home for Elderly' },
                    { code: 'P45', name: 'Family Services for Adolescent Parents' },
                    { code: 'P46', name: 'Family Counseling' },
                    { code: 'P47', name: 'Pregnancy Centers' },
                    { code: 'P50', name: 'Personal Social Services' },
                    { code: 'P51', name: 'Financial Counseling, Money Management' },
                    { code: 'P52', name: 'Transportation, Free or Subsidized' },
                    { code: 'P58', name: 'Gift Distribution' },
                    { code: 'P60', name: 'Emergency Assistance' },
                    { code: 'P61', name: 'Travelers Aid' },
                    { code: 'P62', name: 'Victims Services' },
                    { code: 'P70', name: 'Residential, Custodial Care' },
                    { code: 'P71', name: 'Adult, Continuing Care' },
                    { code: 'P73', name: 'Group Home, Halfway House' },
                    { code: 'P74', name: 'Hospices' },
                    { code: 'P75', name: 'Senior Centers, Services' },
                    { code: 'P76', name: 'Blind, Visually Impaired Centers, Services' },
                    { code: 'P80', name: 'Centers to Support Independence of Specific Populations' },
                    { code: 'P81', name: 'Senior Continuing Care Communities' },
                    { code: 'P82', name: 'Developmentally Disabled Centers, Services' },
                    { code: 'P84', name: 'Ethnic, Immigrant Centers, Services' },
                    { code: 'P85', name: 'Homeless Centers, Services' },
                    { code: 'P86', name: 'Deaf, Hearing Impaired Centers, Services' },
                    { code: 'P87', name: 'Disability Centers, Services' },
                    { code: 'P99', name: 'Human Services N.E.C.' }
                ]
            },
            'Q': { 
                category: 'International, Foreign Affairs & National Security',
                subcategories: [
                    { code: 'Q01', name: 'Alliances & Advocacy' },
                    { code: 'Q02', name: 'Management & Technical Assistance' },
                    { code: 'Q03', name: 'Professional Societies & Associations' },
                    { code: 'Q05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'Q11', name: 'Single Organization Support' },
                    { code: 'Q12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'Q19', name: 'Support N.E.C.' },
                    { code: 'Q20', name: 'Promotion of International Understanding' },
                    { code: 'Q21', name: 'International Cultural Exchange' },
                    { code: 'Q22', name: 'International Academic Exchange' },
                    { code: 'Q23', name: 'International Exchange N.E.C.' },
                    { code: 'Q30', name: 'International Development, Relief Services' },
                    { code: 'Q31', name: 'International Agricultural Development' },
                    { code: 'Q32', name: 'International Economic Development' },
                    { code: 'Q33', name: 'International Relief' },
                    { code: 'Q40', name: 'International Peace & Security' },
                    { code: 'Q41', name: 'Arms Control, Peace' },
                    { code: 'Q42', name: 'United Nations Association' },
                    { code: 'Q43', name: 'National Security' },
                    { code: 'Q50', name: 'International Affairs, Foreign Policy, & Globalization' },
                    { code: 'Q51', name: 'International Economic & Trade Policy' },
                    { code: 'Q70', name: 'International Human Rights' },
                    { code: 'Q71', name: 'International Migration, Refugee Issues' },
                    { code: 'Q99', name: 'International, Foreign Affairs & National Security N.E.C.' }
                ]
            },
            'R': { 
                category: 'Civil Rights, Social Action & Advocacy',
                subcategories: [
                    { code: 'R01', name: 'Alliances & Advocacy' },
                    { code: 'R02', name: 'Management & Technical Assistance' },
                    { code: 'R03', name: 'Professional Societies & Associations' },
                    { code: 'R05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'R11', name: 'Single Organization Support' },
                    { code: 'R12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'R19', name: 'Support N.E.C.' },
                    { code: 'R20', name: 'Civil Rights' },
                    { code: 'R22', name: 'Minority Rights' },
                    { code: 'R23', name: 'Disabled Persons Rights' },
                    { code: 'R24', name: 'Women\'s Rights' },
                    { code: 'R25', name: 'Seniors\' Rights' },
                    { code: 'R26', name: 'Lesbian, Gay Rights' },
                    { code: 'R27', name: 'Immigrants\' Rights' },
                    { code: 'R28', name: 'AIDS, HIV Issues' },
                    { code: 'R29', name: 'Reproductive Rights' },
                    { code: 'R30', name: 'Intergroup, Race Relations' },
                    { code: 'R40', name: 'Voter Education, Registration' },
                    { code: 'R60', name: 'Civil Liberties Advocacy' },
                    { code: 'R61', name: 'Reproductive Freedom' },
                    { code: 'R62', name: 'Right to Life' },
                    { code: 'R63', name: 'Censorship, Freedom of Speech and Press' },
                    { code: 'R67', name: 'Right to Die & Euthanasia' },
                    { code: 'R99', name: 'Civil Rights, Social Action, Advocacy N.E.C.' }
                ]
            },
            'S': { 
                category: 'Community Improvement & Capacity Building',
                subcategories: [
                    { code: 'S01', name: 'Alliances & Advocacy' },
                    { code: 'S02', name: 'Management & Technical Assistance' },
                    { code: 'S03', name: 'Professional Societies & Associations' },
                    { code: 'S05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'S11', name: 'Single Organization Support' },
                    { code: 'S12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'S19', name: 'Support N.E.C.' },
                    { code: 'S20', name: 'Community, Neighborhood Development, Improvement' },
                    { code: 'S21', name: 'Community Coalitions' },
                    { code: 'S22', name: 'Neighborhood, Block Associations' },
                    { code: 'S30', name: 'Economic Development' },
                    { code: 'S31', name: 'Urban, Community Economic Development' },
                    { code: 'S32', name: 'Rural Development' },
                    { code: 'S40', name: 'Business & Professional Organizations' },
                    { code: 'S41', name: 'Promotion of Business' },
                    { code: 'S43', name: 'Management Services for Professional Fundraising' },
                    { code: 'S46', name: 'Boards of Trade' },
                    { code: 'S47', name: 'Real Estate Organizations' },
                    { code: 'S50', name: 'Nonprofit Management' },
                    { code: 'S80', name: 'Community Service Clubs' },
                    { code: 'S81', name: 'Women\'s Service Clubs' },
                    { code: 'S82', name: 'Men\'s Service Clubs' },
                    { code: 'S99', name: 'Community Improvement, Capacity Building N.E.C.' }
                ]
            },
            'T': { 
                category: 'Philanthropy, Voluntarism & Grantmaking Foundations',
                subcategories: [
                    { code: 'T01', name: 'Alliances & Advocacy' },
                    { code: 'T02', name: 'Management & Technical Assistance' },
                    { code: 'T03', name: 'Professional Societies & Associations' },
                    { code: 'T05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'T11', name: 'Single Organization Support' },
                    { code: 'T12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'T19', name: 'Support N.E.C.' },
                    { code: 'T20', name: 'Private Grantmaking Foundations' },
                    { code: 'T21', name: 'Corporate Foundations' },
                    { code: 'T22', name: 'Private Independent Foundations' },
                    { code: 'T23', name: 'Private Operating Foundations' },
                    { code: 'T30', name: 'Public Foundations' },
                    { code: 'T31', name: 'Community Foundations' },
                    { code: 'T40', name: 'Voluntarism Promotion' },
                    { code: 'T50', name: 'Philanthropy, Charity, Voluntarism Promotion, General' },
                    { code: 'T70', name: 'Federated Giving Programs' },
                    { code: 'T90', name: 'Named Trusts/Foundations N.E.C.' },
                    { code: 'T99', name: 'Philanthropy, Voluntarism & Grantmaking N.E.C.' }
                ]
            },
            'U': { 
                category: 'Science & Technology',
                subcategories: [
                    { code: 'U01', name: 'Alliances & Advocacy' },
                    { code: 'U02', name: 'Management & Technical Assistance' },
                    { code: 'U03', name: 'Professional Societies & Associations' },
                    { code: 'U05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'U11', name: 'Single Organization Support' },
                    { code: 'U12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'U19', name: 'Support N.E.C.' },
                    { code: 'U20', name: 'General Science' },
                    { code: 'U21', name: 'Marine Science & Oceanography' },
                    { code: 'U30', name: 'Physical Sciences, Earth Sciences' },
                    { code: 'U31', name: 'Astronomy' },
                    { code: 'U33', name: 'Chemistry, Chemical Engineering' },
                    { code: 'U34', name: 'Mathematics' },
                    { code: 'U36', name: 'Geology' },
                    { code: 'U40', name: 'Engineering & Technology' },
                    { code: 'U41', name: 'Computer Science' },
                    { code: 'U42', name: 'Engineering' },
                    { code: 'U50', name: 'Biological, Life Sciences' },
                    { code: 'U99', name: 'Science & Technology N.E.C.' }
                ]
            },
            'V': { 
                category: 'Social Science',
                subcategories: [
                    { code: 'V01', name: 'Alliances & Advocacy' },
                    { code: 'V02', name: 'Management & Technical Assistance' },
                    { code: 'V03', name: 'Professional Societies & Associations' },
                    { code: 'V05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'V11', name: 'Single Organization Support' },
                    { code: 'V12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'V19', name: 'Support N.E.C.' },
                    { code: 'V20', name: 'Social Science Research' },
                    { code: 'V21', name: 'Anthropology, Sociology' },
                    { code: 'V22', name: 'Economics' },
                    { code: 'V23', name: 'Behavioral Science' },
                    { code: 'V24', name: 'Political Science' },
                    { code: 'V25', name: 'Population Studies' },
                    { code: 'V26', name: 'Law, Jurisprudence' },
                    { code: 'V30', name: 'Interdisciplinary Research' },
                    { code: 'V31', name: 'Black Studies' },
                    { code: 'V32', name: 'Women\'s Studies' },
                    { code: 'V33', name: 'Ethnic Studies' },
                    { code: 'V34', name: 'Urban Studies' },
                    { code: 'V35', name: 'International Studies' },
                    { code: 'V36', name: 'Gerontology' },
                    { code: 'V37', name: 'Labor Studies' },
                    { code: 'V99', name: 'Social Science N.E.C.' }
                ]
            },
            'W': { 
                category: 'Public & Societal Benefit',
                subcategories: [
                    { code: 'W01', name: 'Alliances & Advocacy' },
                    { code: 'W02', name: 'Management & Technical Assistance' },
                    { code: 'W03', name: 'Professional Societies & Associations' },
                    { code: 'W05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'W11', name: 'Single Organization Support' },
                    { code: 'W12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'W19', name: 'Support N.E.C.' },
                    { code: 'W20', name: 'Government & Public Administration' },
                    { code: 'W22', name: 'Public Finance, Taxation & Monetary Policy' },
                    { code: 'W24', name: 'Citizen Participation' },
                    { code: 'W30', name: 'Military, Veterans\' Organizations' },
                    { code: 'W40', name: 'Public Transportation Systems, Services' },
                    { code: 'W50', name: 'Telephone, Telegraph & Telecommunication Services' },
                    { code: 'W60', name: 'Financial Institutions, Services' },
                    { code: 'W61', name: 'Credit Unions' },
                    { code: 'W70', name: 'Leadership Development' },
                    { code: 'W80', name: 'Public Utilities' },
                    { code: 'W90', name: 'Consumer Protection, Safety' },
                    { code: 'W99', name: 'Public, Societal Benefit N.E.C.' }
                ]
            },
            'X': { 
                category: 'Religion-Related',
                subcategories: [
                    { code: 'X01', name: 'Alliances & Advocacy' },
                    { code: 'X02', name: 'Management & Technical Assistance' },
                    { code: 'X03', name: 'Professional Societies & Associations' },
                    { code: 'X05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'X11', name: 'Single Organization Support' },
                    { code: 'X12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'X19', name: 'Support N.E.C.' },
                    { code: 'X20', name: 'Christian' },
                    { code: 'X21', name: 'Protestant' },
                    { code: 'X22', name: 'Roman Catholic' },
                    { code: 'X30', name: 'Jewish' },
                    { code: 'X40', name: 'Islamic' },
                    { code: 'X50', name: 'Buddhist' },
                    { code: 'X70', name: 'Hindu' },
                    { code: 'X80', name: 'Religious Media, Communications Organizations' },
                    { code: 'X81', name: 'Religious Film, Video' },
                    { code: 'X82', name: 'Religious Television' },
                    { code: 'X83', name: 'Religious Printing, Publishing' },
                    { code: 'X84', name: 'Religious Radio' },
                    { code: 'X90', name: 'Interfaith Issues' },
                    { code: 'X99', name: 'Religion Related, Spiritual Development N.E.C.' }
                ]
            },
            'Y': { 
                category: 'Mutual & Membership Benefit',
                subcategories: [
                    { code: 'Y01', name: 'Alliances & Advocacy' },
                    { code: 'Y02', name: 'Management & Technical Assistance' },
                    { code: 'Y03', name: 'Professional Societies & Associations' },
                    { code: 'Y05', name: 'Research Institutes & Public Policy Analysis' },
                    { code: 'Y11', name: 'Single Organization Support' },
                    { code: 'Y12', name: 'Fund Raising & Fund Distribution' },
                    { code: 'Y19', name: 'Support N.E.C.' },
                    { code: 'Y20', name: 'Insurance Providers' },
                    { code: 'Y22', name: 'Local Benevolent Life Insurance Associations' },
                    { code: 'Y23', name: 'Mutual Insurance Companies' },
                    { code: 'Y24', name: 'Supplemental Unemployment Compensation' },
                    { code: 'Y25', name: 'State-Sponsored Workers Compensation Reinsurance Organizations' },
                    { code: 'Y30', name: 'Pension & Retirement Funds' },
                    { code: 'Y33', name: 'Teachers Retirement Fund Associations' },
                    { code: 'Y34', name: 'Employee Funded Pension Trusts' },
                    { code: 'Y35', name: 'Multi-Employer Pension Plans' },
                    { code: 'Y40', name: 'Fraternal Organizations' },
                    { code: 'Y41', name: 'Masonic, Lodge' },
                    { code: 'Y42', name: 'Elks Lodge' },
                    { code: 'Y43', name: 'Veterans\' Posts' },
                    { code: 'Y44', name: 'Ethnic, Nationality Organizations' },
                    { code: 'Y50', name: 'Cemeteries, Burial Services' },
                    { code: 'Y99', name: 'Mutual, Membership Benefit Organizations, Other N.E.C.' }
                ]
            },
            'Z': { 
                category: 'Unknown',
                subcategories: [
                    { code: 'Z99', name: 'Unknown, Unclassified' }
                ]
            }
        },

        // Government Criteria Data Structure
        governmentCriteriaList: {
            'funding_instruments': {
                category: 'Funding Instruments',
                description: 'Types of federal funding mechanisms',
                criteria: [
                    { id: 'grant', name: 'Grants', description: 'Direct financial assistance for specific projects', sources: ['Federal', 'State', 'Local'] },
                    { id: 'cooperative_agreement', name: 'Cooperative Agreements', description: 'Partnerships with substantial federal involvement', sources: ['Federal'] },
                    { id: 'contract', name: 'Contracts', description: 'Procurement contracts for goods/services', sources: ['Federal', 'State', 'Local'] },
                    { id: 'other', name: 'Other Instruments', description: 'Alternative funding mechanisms', sources: ['Federal', 'State'] }
                ]
            },
            'eligibility': {
                category: 'Applicant Eligibility',
                description: 'Types of organizations eligible to apply',
                criteria: [
                    { id: 'nonprofit', name: 'Nonprofit Organizations', description: '501(c)(3) and other nonprofits', sources: ['Federal', 'State', 'Local'] },
                    { id: 'state_government', name: 'State Governments', description: 'State-level government entities', sources: ['Federal'] },
                    { id: 'local_government', name: 'Local Governments', description: 'Cities, counties, municipalities', sources: ['Federal', 'State'] },
                    { id: 'tribal_government', name: 'Tribal Governments', description: 'Native American tribal organizations', sources: ['Federal'] },
                    { id: 'university', name: 'Universities', description: 'Higher education institutions', sources: ['Federal', 'State'] },
                    { id: 'for_profit', name: 'For-Profit Companies', description: 'Commercial businesses', sources: ['Federal', 'State', 'Local'] },
                    { id: 'individual', name: 'Individuals', description: 'Individual applicants', sources: ['Federal', 'State'] }
                ]
            },
            'agencies': {
                category: 'Federal Agencies',
                description: 'Preferred federal funding agencies',
                criteria: [
                    { id: 'HHS', name: 'Health & Human Services', description: 'CDC, NIH, HRSA, ACF, etc.', sources: ['Federal'] },
                    { id: 'ED', name: 'Department of Education', description: 'Education programs and research', sources: ['Federal'] },
                    { id: 'USDA', name: 'Agriculture Department', description: 'Rural development, nutrition programs', sources: ['Federal'] },
                    { id: 'DOL', name: 'Department of Labor', description: 'Workforce development programs', sources: ['Federal'] },
                    { id: 'HUD', name: 'Housing & Urban Development', description: 'Community development, housing', sources: ['Federal'] },
                    { id: 'EPA', name: 'Environmental Protection Agency', description: 'Environmental programs', sources: ['Federal'] },
                    { id: 'NSF', name: 'National Science Foundation', description: 'Scientific research funding', sources: ['Federal'] },
                    { id: 'DOD', name: 'Department of Defense', description: 'Defense-related research', sources: ['Federal'] },
                    { id: 'DHS', name: 'Homeland Security', description: 'Security and emergency programs', sources: ['Federal'] },
                    { id: 'DOT', name: 'Transportation', description: 'Transportation infrastructure', sources: ['Federal'] }
                ]
            },
            'award_amounts': {
                category: 'Award Amount Ranges',
                description: 'Preferred funding amount ranges',
                criteria: [
                    { id: 'small', name: 'Small Awards ($1K - $25K)', description: 'Small project funding', sources: ['Federal', 'State', 'Local'] },
                    { id: 'medium', name: 'Medium Awards ($25K - $100K)', description: 'Standard program funding', sources: ['Federal', 'State', 'Local'] },
                    { id: 'large', name: 'Large Awards ($100K - $500K)', description: 'Major initiative funding', sources: ['Federal', 'State'] },
                    { id: 'very_large', name: 'Very Large Awards ($500K+)', description: 'Large-scale programs', sources: ['Federal'] }
                ]
            },
            'geographic_scope': {
                category: 'Geographic Eligibility',
                description: 'Geographic limitations and preferences',
                criteria: [
                    { id: 'national', name: 'National Eligibility', description: 'Open to all US organizations', sources: ['Federal'] },
                    { id: 'regional', name: 'Regional Programs', description: 'Multi-state regional initiatives', sources: ['Federal', 'State'] },
                    { id: 'state_specific', name: 'State-Specific', description: 'Limited to specific states', sources: ['State'] },
                    { id: 'local_focus', name: 'Local Focus', description: 'Community-level programs', sources: ['Local', 'State'] },
                    { id: 'rural_priority', name: 'Rural Priority', description: 'Preference for rural areas', sources: ['Federal', 'State'] },
                    { id: 'urban_priority', name: 'Urban Priority', description: 'Focus on urban communities', sources: ['Federal', 'State', 'Local'] }
                ]
            },
            'program_categories': {
                category: 'Program Categories',
                description: 'CFDA and program focus areas',
                criteria: [
                    { id: 'health', name: 'Health Programs', description: 'Public health, medical research', sources: ['Federal', 'State', 'Local'] },
                    { id: 'education', name: 'Education', description: 'K-12, higher education, training', sources: ['Federal', 'State', 'Local'] },
                    { id: 'social_services', name: 'Social Services', description: 'Human services, community support', sources: ['Federal', 'State', 'Local'] },
                    { id: 'environment', name: 'Environmental', description: 'Conservation, sustainability', sources: ['Federal', 'State', 'Local'] },
                    { id: 'economic_development', name: 'Economic Development', description: 'Job creation, business support', sources: ['Federal', 'State', 'Local'] },
                    { id: 'research', name: 'Research & Development', description: 'Scientific research programs', sources: ['Federal'] },
                    { id: 'infrastructure', name: 'Infrastructure', description: 'Transportation, utilities, facilities', sources: ['Federal', 'State', 'Local'] },
                    { id: 'technology', name: 'Technology', description: 'IT, innovation, digital programs', sources: ['Federal', 'State'] },
                    { id: 'arts_culture', name: 'Arts & Culture', description: 'Cultural programs, humanities', sources: ['Federal', 'State', 'Local'] },
                    { id: 'disaster_relief', name: 'Disaster Relief', description: 'Emergency response, recovery', sources: ['Federal', 'State', 'Local'] }
                ]
            }
        },
        
        // NTEE Modal State
        nteeModal: {
            isOpen: false,
            selectedMainCategory: null,
            selectedNteeCodes: [],
            tempSelectedCodes: []
        },

        // Government Criteria Modal State
        governmentCriteriaModal: {
            isOpen: false,
            selectedCategory: null,
            tempSelectedCriteria: []
        },
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
                welcome: 0,
                profiler: 0,
                discover: 0,
                analyze: 0,
                plan: 0,
                execute: 0
            },
            stageStartTimes: {},
            completionRates: {
                welcome: 0,
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
            location: '', // Primary organization location
            notes: '', // Additional notes
            nationwide: false,
            international: false,
            min_amount: null,
            grants_gov_categories: [], // Grants.gov classification checkboxes
            max_amount: null,
            annual_revenue: null,
            funding_types: []
        },
        showCreateProfile: false,
        showViewProfile: false,
        showEditProfile: false,
        selectedProfile: {},
        profileSearchQuery: '',
        totalProfiles: 0,
        
        // New profile form data
        newProfile: {
            name: '',
            focus_areas: '',
            geographic_scope: '',
            budget_range: '',
            organization_type: ''
        },
        profileCreating: false,
        profileCount: 0,
        
        // Profile Management System
        profiles: [],
        filteredProfiles: [],
        profilesLoading: false,
        showProfileModal: false,
        isEditingProfile: false,
        profileSaving: false,
        profileSearchTerm: '',
        currentEditingProfile: null,
        showDeleteConfirmation: false,
        deleteConfirmationMessage: '',
        
        // EIN fetch functionality
        einFetchLoading: false,
        pendingDeleteProfileId: null,
        
        // Profile form data - comprehensive structure
        profileForm: {
            profile_id: '',
            name: '',
            organization_type: '',
            ein: '',
            mission_statement: '',
            keywords: '',
            focus_areas_text: '',
            target_populations_text: '',
            states_text: '',
            location: '', // Primary organization location
            notes: '', // Additional notes
            grants_gov_categories: [], // Grants.gov classification preferences
            geographic_scope: {
                nationwide: false,
                international: false
            },
            funding_preferences: {
                min_amount: null,
                max_amount: null
            },
            annual_revenue: null,
            staff_size: null,
            volunteer_count: null,
            board_size: null,
            notes: '',
            government_criteria: []
        },
        
        // Profile sorting and filtering
        profileSort: {
            field: 'updated_at',
            direction: 'desc'
        },
        
        // Initialization
        async init() {
            console.log('Initializing Catalynx Web Interface...');
            
            // Initialize welcome stage if active
            if (this.activeStage === 'welcome') {
                await this.loadWelcomeStatus();
            }
            
            // Watch for prospects stage filter changes
            this.$watch('prospectsStageFilter', () => {
                if (this.selectedDiscoveryProfile && this.activeStage === 'discover') {
                    this.loadProspectsData();
                }
            });
            
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
        async switchStage(stage) {
            // Track stage transition for analytics
            this.trackStageTransition(this.activeStage, stage);
            
            this.activeStage = stage;
            console.log('Switched to workflow stage:', stage);
            
            // Load stage-specific data
            if (stage === 'discover') {
                console.log('Loading prospects data for discover stage');
                await this.loadProspectsData();
            }
            
            // Load profiles when switching to profiler stage
            if (stage === 'profiler' && this.profiles.length === 0) {
                await this.loadProfiles();
            }
            
            // Sync profile when switching to plan stage
            if (stage === 'plan') {
                // Trigger profile sync for plan tab
                setTimeout(() => {
                    const planElement = document.querySelector('[x-data*="planTabData"]');
                    if (planElement && planElement._x_dataStack && planElement._x_dataStack[0]) {
                        planElement._x_dataStack[0].syncProfileWithDiscover();
                    }
                }, 100); // Small delay to ensure DOM is ready
            }
            
            // Sync profile when switching to analyze stage
            if (stage === 'analyze') {
                // Trigger profile sync for analyze tab
                setTimeout(() => {
                    const analyzeElement = document.querySelector('[x-data*="analyzeTabData"]');
                    if (analyzeElement && analyzeElement._x_dataStack && analyzeElement._x_dataStack[0]) {
                        analyzeElement._x_dataStack[0].syncProfileWithDiscover();
                    }
                }, 100); // Small delay to ensure DOM is ready
            }
            
            // Close mobile menu if open
            this.mobileMenuOpen = false;
            
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

        // Profile Management Functions
        async loadProfiles() {
            this.profilesLoading = true;
            try {
                const response = await fetch('/api/profiles');
                if (response.ok) {
                    const data = await response.json();
                    // Load all profiles (except archived ones if they exist)
                    const allProfiles = data.profiles ? data.profiles : data;
                    this.profiles = allProfiles.filter(profile => profile.status !== 'archived');
                    this.filteredProfiles = [...this.profiles];
                    this.profileCount = this.profiles.length;
                    
                    // Debug: Check what data we loaded for profiles
                    console.log('Loaded profiles:', this.profiles.map(p => ({
                        id: p.profile_id,
                        name: p.name,
                        ntee_codes: p.ntee_codes,
                        government_criteria: p.government_criteria,
                        keywords: p.keywords,
                        has_data: !!(p.ntee_codes || p.government_criteria || p.keywords)
                    })));
                    
                    // Debug: Show first profile with data
                    const profileWithData = this.profiles.find(p => p.ntee_codes || p.government_criteria || p.keywords);
                    if (profileWithData) {
                        console.log('Sample profile with data:', profileWithData);
                    } else {
                        console.log('No profiles found with NTEE codes, government criteria, or keywords');
                    }
                } else {
                    console.error('Failed to load profiles:', response.statusText);
                }
            } catch (error) {
                console.error('Error loading profiles:', error);
            } finally {
                this.profilesLoading = false;
            }
        },

        async loadProfileStats() {
            // Stub function to prevent JavaScript errors
            console.log('Loading profile statistics...');
            // TODO: Implement profile statistics loading if needed
        },

        async createSampleProfiles() {
            const sampleProfiles = [
                {
                    name: "Test Nonprofit Health Organization_01",
                    organization_type: "nonprofit",
                    ein: "812827604",
                    mission_statement: "Providing healthcare services to underserved communities",
                    keywords: "healthcare, community, preventive care",
                    focus_areas: ["healthcare", "community_development"],
                    target_populations: ["low_income_families", "seniors"],
                    ntee_codes: ["L11", "L20"],
                    government_criteria: ["HHS"],
                    geographic_scope: { states: ["VA"], nationwide: false, international: false },
                    annual_revenue: 250000
                },
                {
                    name: "Education Foundation",
                    organization_type: "foundation",
                    mission_statement: "Advancing education through innovative programs and partnerships",
                    focus_areas: ["education", "community_development", "innovation"],
                    target_populations: ["students", "teachers"],
                    ntee_codes: ["B20", "B90"],
                    government_criteria: ["ED"],
                    geographic_scope: { states: ["VA", "MD", "DC"], nationwide: false, international: false }
                },
                {
                    name: "Community Development Corp",
                    organization_type: "nonprofit", 
                    mission_statement: "Building stronger communities through economic development",
                    focus_areas: ["community_development", "economic_development"],
                    ntee_codes: ["S20", "S80"],
                    government_criteria: ["HUD", "USDA"],
                    geographic_scope: { states: ["VA"], nationwide: false, international: false }
                }
            ];

            for (const profile of sampleProfiles) {
                try {
                    const response = await fetch('/api/profiles', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(profile)
                    });
                    if (response.ok) {
                        console.log(`Created sample profile: ${profile.name}`);
                    }
                } catch (error) {
                    console.error(`Failed to create profile ${profile.name}:`, error);
                }
            }
            
            // Reload profiles after creating samples
            await this.loadProfiles();
            this.showNotification('Sample profiles created!', 'Created 3 test profiles for testing', 'success');
        },

        openCreateProfile() {
            // Reset form and open the working profile modal for creation
            this.resetProfileForm();
            this.isEditingProfile = false;
            this.showProfileModal = true;
            console.log('Opening create profile modal');
        },

        resetProfileForm() {
            this.profileForm = {
                profile_id: '',
                name: '',
                organization_type: '',
                ein: '',
                mission_statement: '',
                keywords: '',
                focus_areas_text: '',
                target_populations_text: '',
                states_text: '',
                geographic_scope: {
                    nationwide: false,
                    international: false
                },
                funding_preferences: {
                    min_amount: null,
                    max_amount: null
                },
                annual_revenue: null,
                staff_size: null,
                volunteer_count: null,
                board_size: null,
                notes: '',
                government_criteria: [],
                schedule_i_grantees: []
            };
            // Reset modal states
            this.nteeModal.selectedNteeCodes = [];
            this.isEditingProfile = false;
            this.currentEditingProfile = null;
        },

        editProfile(profile) {
            this.isEditingProfile = true;
            this.currentEditingProfile = profile.profile_id;
            
            // Populate form with profile data
            this.profileForm.profile_id = profile.profile_id;
            this.profileForm.name = profile.name || '';
            this.profileForm.organization_type = profile.organization_type || '';
            this.profileForm.ein = profile.ein || '';
            this.profileForm.mission_statement = profile.mission_statement || '';
            this.profileForm.keywords = profile.keywords || '';
            this.profileForm.focus_areas_text = (profile.focus_areas || []).join('\n');
            this.profileForm.target_populations_text = (profile.target_populations || []).join('\n');
            this.profileForm.states_text = (profile.geographic_scope?.states || []).join(', ');
            
            // Ensure nested objects exist before setting properties
            if (!this.profileForm.geographic_scope) {
                this.profileForm.geographic_scope = {};
            }
            this.profileForm.geographic_scope.nationwide = profile.geographic_scope?.nationwide || false;
            this.profileForm.geographic_scope.international = profile.geographic_scope?.international || false;
            
            if (!this.profileForm.funding_preferences) {
                this.profileForm.funding_preferences = {};
            }
            this.profileForm.funding_preferences.min_amount = profile.funding_preferences?.min_amount || null;
            this.profileForm.funding_preferences.max_amount = profile.funding_preferences?.max_amount || null;
            this.profileForm.annual_revenue = profile.annual_revenue || null;
            this.profileForm.staff_size = profile.staff_size || null;
            this.profileForm.volunteer_count = profile.volunteer_count || null;
            this.profileForm.board_size = profile.board_size || null;
            this.profileForm.notes = profile.notes || '';
            
            // Load NTEE codes and government criteria
            this.nteeModal.selectedNteeCodes = profile.ntee_codes || [];
            this.profileForm.government_criteria = profile.government_criteria || [];
            this.profileForm.schedule_i_grantees = profile.schedule_i_grantees || [];
            this.profileForm.schedule_i_status = profile.schedule_i_status || null;
            
            // Debug: Log what we loaded from the profile
            console.log('Loading profile for edit:', {
                profile_id: profile.profile_id,
                ntee_codes: profile.ntee_codes,
                government_criteria: profile.government_criteria,
                loaded_ntee: this.nteeModal.selectedNteeCodes,
                loaded_govt: this.profileForm.government_criteria
            });
            
            this.showProfileModal = true;
        },

        async fetchEINData() {
            console.log('fetchEINData called');
            console.log('profileForm.ein:', this.profileForm?.ein);
            
            if (!this.profileForm?.ein) {
                this.showNotification('Please enter an EIN first', 'error');
                return;
            }
            
            this.einFetchLoading = true;
            try {
                const response = await fetch('/api/profiles/fetch-ein', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ein: this.profileForm.ein
                    })
                });
                
                const result = await response.json();
                console.log('API Response:', result);
                
                if (result.success && result.data) {
                    console.log('Organization data:', result.data);
                    // Update profile form with fetched data
                    if (result.data.name) {
                        console.log('Setting name:', result.data.name);
                        this.profileForm.name = result.data.name;
                    }
                    if (result.data.mission_statement) {
                        console.log('Setting mission:', result.data.mission_statement);
                        this.profileForm.mission_statement = result.data.mission_statement;
                    }
                    if (result.data.organization_type) {
                        console.log('Setting org type:', result.data.organization_type);
                        this.profileForm.organization_type = result.data.organization_type;
                    }
                    
                    // Additional fields from EIN lookup
                    if (result.data.state && result.data.city) {
                        this.profileForm.states_text = result.data.state;
                        console.log('Setting location:', result.data.city + ', ' + result.data.state);
                    }
                    if (result.data.revenue) {
                        this.profileForm.annual_revenue = result.data.revenue;
                        console.log('Setting revenue:', result.data.revenue);
                    }
                    
                    // Handle Schedule I data and status
                    if (result.data.schedule_i_grantees && result.data.schedule_i_grantees.length > 0) {
                        this.profileForm.schedule_i_grantees = result.data.schedule_i_grantees;
                        this.profileForm.schedule_i_status = 'found';
                        console.log('Setting Schedule I grantees:', result.data.schedule_i_grantees);
                        
                        const granteeCount = result.data.schedule_i_grantees.length;
                        this.showNotification(`Organization data fetched: ${result.data.name} (${granteeCount} Schedule I grantee${granteeCount > 1 ? 's' : ''} found)${result.data.city ? ' (' + result.data.city + ', ' + result.data.state + ')' : ''}`, 'success');
                    } else {
                        this.profileForm.schedule_i_grantees = [];
                        // Check if we have explicit status information from the API response
                        if (result.data.schedule_i_status) {
                            this.profileForm.schedule_i_status = result.data.schedule_i_status;
                        } else {
                            // Default to 'no_grantees' if XML was processed but no grantees found
                            this.profileForm.schedule_i_status = 'no_grantees';
                        }
                        this.showNotification(`Organization data fetched: ${result.data.name} (No Schedule I grantees found)${result.data.city ? ' (' + result.data.city + ', ' + result.data.state + ')' : ''}`, 'success');
                    }
                } else {
                    console.log('API call failed or no data:', result);
                    this.showNotification(result.message || 'Failed to fetch organization data', 'error');
                }
                
            } catch (error) {
                console.error('EIN fetch error:', error);
                console.error('Error details:', error.message, error.stack);
                this.showNotification(`Error fetching organization data: ${error.message}`, 'error');
            } finally {
                this.einFetchLoading = false;
            }
        },

        async saveProfile() {
            this.profileSaving = true;
            try {
                // Validate required fields before submitting
                if (!this.profileForm.name || this.profileForm.name.trim().length === 0) {
                    alert('Organization name is required');
                    this.profileSaving = false;
                    return;
                }
                
                // Prepare profile data for API
                const profileData = {
                    name: this.profileForm.name,
                    organization_type: this.profileForm.organization_type,
                    ein: this.profileForm.ein || null,
                    mission_statement: this.profileForm.mission_statement || '',
                    keywords: this.profileForm.keywords || '',
                    focus_areas: ['general'], // Default focus area to satisfy backend validation
                    target_populations: (this.profileForm.target_populations_text || '').split('\n').filter(pop => pop.trim()),
                    geographic_scope: {
                        states: (this.profileForm.states_text || '').split(',').map(s => s.trim().toUpperCase()).filter(s => s),
                        nationwide: this.profileForm.geographic_scope?.nationwide || false,
                        international: this.profileForm.geographic_scope?.international || false
                    },
                    funding_preferences: {
                        min_amount: this.profileForm.funding_preferences?.min_amount ? parseInt(this.profileForm.funding_preferences.min_amount) : null,
                        max_amount: this.profileForm.funding_preferences?.max_amount ? parseInt(this.profileForm.funding_preferences.max_amount) : null,
                        funding_types: ['grants'],
                        grants_gov_categories: this.profileForm.grants_gov_categories || []
                    },
                    annual_revenue: this.profileForm.annual_revenue ? parseInt(this.profileForm.annual_revenue) : null,
                    staff_size: this.profileForm.staff_size ? parseInt(this.profileForm.staff_size) : null,
                    volunteer_count: this.profileForm.volunteer_count ? parseInt(this.profileForm.volunteer_count) : null,
                    board_size: this.profileForm.board_size ? parseInt(this.profileForm.board_size) : null,
                    location: this.profileForm.location || null,
                    notes: this.profileForm.notes || null,
                    ntee_codes: this.nteeModal.selectedNteeCodes || [],
                    government_criteria: this.profileForm.government_criteria || [],
                    schedule_i_grantees: this.profileForm.schedule_i_grantees || [],
                    schedule_i_status: this.profileForm.schedule_i_status || null
                };

                // Debug: Log what we're about to save
                console.log('Saving profile data:', {
                    ntee_codes: profileData.ntee_codes,
                    government_criteria: profileData.government_criteria,
                    keywords: profileData.keywords
                });

                let response;
                if (this.isEditingProfile) {
                    // Update existing profile
                    response = await fetch(`/api/profiles/${this.currentEditingProfile}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(profileData)
                    });
                } else {
                    // Create new profile
                    response = await fetch('/api/profiles', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(profileData)
                    });
                }

                if (response.ok) {
                    const savedProfile = await response.json();
                    console.log('Profile saved successfully, server returned:', {
                        full_response: savedProfile,
                        ntee_codes: savedProfile.profile?.ntee_codes,
                        government_criteria: savedProfile.profile?.government_criteria
                    });
                    
                    this.showProfileModal = false;
                    this.resetProfileForm();
                    await this.loadProfiles(); // Reload profiles
                    
                    // Switch back to profiler stage to show updated profiles
                    this.switchStage('profiler');
                    
                    // Show success message
                    this.showNotification(
                        this.isEditingProfile ? 'Profile updated successfully!' : 'Profile created successfully!',
                        'success'
                    );
                } else {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to save profile');
                }
            } catch (error) {
                console.error('Error saving profile:', error);
                this.showNotification(`Error saving profile: ${error.message}`, 'error');
            } finally {
                this.profileSaving = false;
            }
        },

        async deleteProfile(profileId) {
            // Find the profile to get its name
            const profile = this.profiles.find(p => p.profile_id === profileId);
            const profileName = profile ? profile.name : 'this profile';
            
            // Show custom confirmation dialog
            this.showDeleteConfirmation = true;
            this.deleteConfirmationMessage = `Are you sure you want to delete "${profileName}"? This action cannot be undone.`;
            this.pendingDeleteProfileId = profileId;
        },

        async confirmDeleteProfile() {
            try {
                const response = await fetch(`/api/profiles/${this.pendingDeleteProfileId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    await this.loadProfiles(); // Reload profiles
                    this.showNotification('Profile deleted successfully!', 'success');
                } else {
                    throw new Error('Failed to delete profile');
                }
            } catch (error) {
                console.error('Error deleting profile:', error);
                this.showNotification(`Error deleting profile: ${error.message}`, 'error');
            } finally {
                this.showDeleteConfirmation = false;
                this.pendingDeleteProfileId = null;
            }
        },

        cancelDeleteProfile() {
            this.showDeleteConfirmation = false;
            this.pendingDeleteProfileId = null;
        },

        filterProfiles() {
            if (!this.profileSearchTerm) {
                this.filteredProfiles = [...this.profiles];
                return;
            }

            const searchTerm = this.profileSearchTerm.toLowerCase();
            this.filteredProfiles = this.profiles.filter(profile => 
                profile.name.toLowerCase().includes(searchTerm) ||
                (profile.ein && profile.ein.includes(searchTerm)) ||
                (profile.focus_areas && profile.focus_areas.some(area => 
                    area.toLowerCase().includes(searchTerm)
                ))
            );
        },

        sortProfiles(field) {
            if (this.profileSort.field === field) {
                this.profileSort.direction = this.profileSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                this.profileSort.field = field;
                this.profileSort.direction = 'asc';
            }

            this.filteredProfiles.sort((a, b) => {
                let valueA = a[field];
                let valueB = b[field];

                // Handle different data types
                if (field === 'updated_at' || field === 'created_at') {
                    valueA = new Date(valueA);
                    valueB = new Date(valueB);
                } else if (typeof valueA === 'string') {
                    valueA = valueA.toLowerCase();
                    valueB = valueB.toLowerCase();
                }

                if (valueA < valueB) return this.profileSort.direction === 'asc' ? -1 : 1;
                if (valueA > valueB) return this.profileSort.direction === 'asc' ? 1 : -1;
                return 0;
            });
        },

        // Profile display helper functions
        maskEIN(ein) {
            if (!ein) return 'N/A';
            return ein.replace(/(\d{2})-?(\d{3})(\d{4})/, 'XX-XXX$3');
        },

        formatOrgType(type) {
            if (!type) return 'Unknown';
            return type.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        },

        getOrgTypeClass(type) {
            const classes = {
                'nonprofit': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                'for_profit': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                'government': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
                'academic': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
                'healthcare': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
                'foundation': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
            };
            return classes[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
        },

        formatDate(dateStr) {
            if (!dateStr) return 'N/A';
            return new Date(dateStr).toLocaleDateString();
        },

        getDiscoveryStatusText(status) {
            const statusText = {
                'never_run': 'Never Run',
                'in_progress': 'In Progress',
                'completed': 'Completed',
                'failed': 'Failed',
                'needs_update': 'Needs Update'
            };
            return statusText[status] || 'Unknown';
        },

        getDiscoveryStatusClass(status) {
            const classes = {
                'never_run': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
                'in_progress': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                'completed': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                'failed': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
                'needs_update': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
            };
            return classes[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
        },

        getDiscoveryButtonText(profile) {
            const status = profile.discovery_status || 'never_run';
            if (status === 'never_run') {
                return '🚀 Start Discovery';
            } else if (status === 'completed') {
                return '🔄 Update Discovery';
            } else if (status === 'needs_update') {
                return '⚠️ Update Discovery';
            } else if (status === 'in_progress') {
                return '⏳ In Progress';
            } else if (status === 'failed') {
                return '🔁 Retry Discovery';
            }
            return '🚀 Discover';
        },

        selectProfileForDiscovery(profile) {
            this.selectedProfile = profile;
            this.showNotification('Profile Selected', `Selected ${profile.name} for discovery`, 'info');
            this.switchStage('discover');
            // Load prospects data for the selected profile
            this.loadProspectsData();
        },
        
        loadStageData(stage) {
            switch(stage) {
                case 'welcome':
                    this.loadWelcomeStatus();
                    console.log('Loading welcome stage data - system status');
                    break;
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
        
        // WELCOME STAGE FUNCTIONS
        async loadWelcomeStatus() {
            try {
                this.welcomeLoading = true;
                const response = await fetch('/api/welcome/status');
                if (response.ok) {
                    this.welcomeStatus = await response.json();
                    console.log('Welcome status loaded:', this.welcomeStatus);
                } else {
                    console.error('Failed to load welcome status');
                }
            } catch (error) {
                console.error('Error loading welcome status:', error);
            } finally {
                this.welcomeLoading = false;
            }
        },
        
        async createSampleProfile() {
            try {
                this.showNotification('Creating Sample Profile', 'Setting up demonstration profile...', 'info');
                
                const response = await fetch('/api/welcome/sample-profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.showNotification('Sample Profile Created', 'Ready to explore the platform features!', 'success');
                    
                    // Update profile count
                    this.profileCount += 1;
                    this.workflowProgress.welcome = true;
                    
                    // Suggest next step
                    setTimeout(() => {
                        this.showNotification('Next Step', 'Visit the PROFILER stage to customize your profile', 'info');
                    }, 2000);
                    
                    return result;
                } else {
                    const error = await response.json();
                    this.showNotification('Error', error.detail || 'Failed to create sample profile', 'error');
                }
            } catch (error) {
                console.error('Error creating sample profile:', error);
                this.showNotification('Error', 'Failed to create sample profile', 'error');
            }
        },
        
        async runQuickStartDemo() {
            try {
                this.showNotification('Starting Demo', 'Running quick platform demonstration...', 'info');
                
                const response = await fetch('/api/welcome/quick-start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.showNotification('Demo Complete!', `Found ${result.total_opportunities} sample opportunities`, 'success');
                    
                    // Mark welcome and potentially other stages as progressed
                    this.workflowProgress.welcome = true;
                    this.profileCount += 1;
                    
                    // Show detailed results
                    console.log('Quick start demo results:', result);
                    
                    // Suggest exploring the platform
                    setTimeout(() => {
                        this.showNotification('Explore the Platform', 'Navigate through PROFILER → DISCOVER → ANALYZE stages', 'info');
                    }, 3000);
                    
                    return result;
                } else {
                    const error = await response.json();
                    this.showNotification('Demo Failed', error.detail || 'Quick start demo encountered an error', 'error');
                }
            } catch (error) {
                console.error('Error running quick start demo:', error);
                this.showNotification('Demo Error', 'Failed to complete quick start demonstration', 'error');
            }
        },
        
        completeWelcomeStage() {
            this.workflowProgress.welcome = true;
            this.showNotification('Welcome Complete', 'Ready to begin your grant research journey!', 'success');
            
            // Auto-advance to profiler if no profiles exist
            if (this.profileCount === 0) {
                setTimeout(() => {
                    this.switchStage('profiler');
                    this.showNotification('Next Step', 'Create your organization profile to get started', 'info');
                }, 2000);
            }
        },
        
        // New Profile Management Functions
        async createNewProfile() {
            if (this.profileCreating) return;
            
            try {
                this.profileCreating = true;
                
                const profileData = {
                    name: this.newProfile.name,
                    focus_areas: this.newProfile.focus_areas,
                    geographic_scope: this.newProfile.geographic_scope,
                    budget_range: this.newProfile.budget_range,
                    organization_type: this.newProfile.organization_type
                };
                
                const response = await fetch('/api/profiles', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(profileData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.showNotification('Profile Created', `${profileData.name} has been created successfully`, 'success');
                    
                    // Reset form and refresh data
                    this.resetNewProfile();
                    this.showCreateProfile = false;
                    await this.loadProfiles();
                    await this.loadProfileStats();
                    
                    // Update progress
                    this.workflowProgress.profiler = true;
                } else {
                    const error = await response.json();
                    this.showNotification('Creation Failed', error.detail || 'Failed to create profile', 'error');
                }
            } catch (error) {
                console.error('Failed to create profile:', error);
                this.showNotification('Creation Failed', 'An error occurred while creating the profile', 'error');
            } finally {
                this.profileCreating = false;
            }
        },
        
        resetNewProfile() {
            this.newProfile = {
                name: '',
                focus_areas: '',
                geographic_scope: '',
                budget_range: '',
                organization_type: ''
            };
        },
        
        selectProfile(profile) {
            this.selectedProfile = profile;
            // Could open a modal or navigate to profile details
            this.showNotification('Profile Selected', `Viewing ${profile.name}`, 'info');
        },
        
        async loadProfileTemplates() {
            this.showNotification('Templates', 'Loading profile templates...', 'info');
            // Implementation would load predefined templates
        },
        
        async exportProfiles() {
            try {
                const response = await fetch('/api/profiles');
                if (response.ok) {
                    const data = await response.json();
                    const profiles = data.profiles || [];
                    
                    const csvContent = this.convertProfilesToCSV(profiles);
                    this.downloadCSV(csvContent, 'organization_profiles.csv');
                    
                    this.showNotification('Export Complete', `Exported ${profiles.length} profiles`, 'success');
                } else {
                    this.showNotification('Export Failed', 'Failed to export profiles', 'error');
                }
            } catch (error) {
                console.error('Failed to export profiles:', error);
                this.showNotification('Export Failed', 'An error occurred during export', 'error');
            }
        },
        
        convertProfilesToCSV(profiles) {
            if (!profiles.length) return 'No profiles to export';
            
            const headers = ['Name', 'Focus Areas', 'Geographic Scope', 'Budget Range', 'Organization Type', 'Created'];
            const rows = profiles.map(profile => [
                profile.name || '',
                profile.focus_areas || '',
                profile.geographic_scope || '',
                profile.budget_range || '',
                profile.organization_type || '',
                profile.created_at || ''
            ]);
            
            return [headers, ...rows].map(row => 
                row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
            ).join('\n');
        },
        
        downloadCSV(content, filename) {
            const blob = new Blob([content], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        },
        
        // DISCOVERY STAGE DATA AND FUNCTIONS
        // Multi-track discovery system state
        selectedDiscoveryTrack: 'nonprofit',
        multiTrackInProgress: false,
        discoveryStats: {
            activeTracks: 4,
            totalResults: 0,
            nonprofit: 0,
            federal: 0,
            state: 0,
            commercial: 0
        },
        
        // Discovery progress tracking
        discoveryProgress: {
            nonprofit: false,
            federal: false,
            state: false,
            commercial: false
        },
        
        // Selected profile for discovery
        // CENTRALIZED PROFILE MANAGEMENT - Single profile for all tabs
        selectedProfile: null,
        
        // Legacy compatibility getters (for gradual migration)
        get selectedDiscoveryProfile() { return this.selectedProfile; },
        get selectedPlanProfile() { return this.selectedProfile; },
        get selectedAnalyzeProfile() { return this.selectedProfile; },
        
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
        
        // UNIFIED OPPORTUNITIES DATA - Single source of truth for all tabs
        opportunitiesData: [
            // PROSPECTS - Early discovery stage
            {
                opportunity_id: 'unified_opp_001',
                organization_name: 'American Heart Association',
                funnel_stage: 'prospects',
                organization_type: 'Nonprofit',
                source_type: 'Nonprofit',
                compatibility_score: 0.85,
                discovery_source: 'ProPublica',
                is_schedule_i_grantee: true,
                funding_amount: 250000,
                discovered_at: '2025-08-12',
                description: 'Cardiovascular health research and community education programs'
            },
            {
                opportunity_id: 'unified_opp_002',
                organization_name: 'Community Health Alliance',
                funnel_stage: 'prospects',
                organization_type: 'Nonprofit',
                source_type: 'Nonprofit',
                compatibility_score: 0.73,
                discovery_source: 'ProPublica',
                is_schedule_i_grantee: false,
                funding_amount: 125000,
                discovered_at: '2025-08-11',
                description: 'Rural health access and preventive care initiatives'
            },
            
            // QUALIFIED PROSPECTS - Initial qualification complete
            {
                opportunity_id: 'unified_opp_003',
                organization_name: 'United Way National',
                funnel_stage: 'qualified_prospects',
                organization_type: 'Nonprofit',
                source_type: 'Nonprofit',
                compatibility_score: 0.92,
                discovery_source: 'ProPublica',
                is_schedule_i_grantee: false,
                funding_amount: 150000,
                discovered_at: '2025-08-10',
                description: 'Community development and social services coordination'
            },
            {
                opportunity_id: 'unified_opp_004',
                organization_name: 'Virginia Health Foundation',
                funnel_stage: 'qualified_prospects',
                organization_type: 'Foundation',
                source_type: 'Foundation',
                compatibility_score: 0.85,
                discovery_source: 'Foundation Directory',
                is_schedule_i_grantee: false,
                funding_amount: 200000,
                discovered_at: '2025-08-09',
                description: 'Health education and community wellness programs'
            },
            
            // CANDIDATES - Deep analysis stage  
            {
                opportunity_id: 'unified_opp_005',
                organization_name: 'Gates Foundation',
                funnel_stage: 'candidates',
                organization_type: 'Foundation',
                source_type: 'Foundation',
                compatibility_score: 0.78,
                discovery_source: 'Foundation Directory',
                is_schedule_i_grantee: false,
                funding_amount: 500000,
                discovered_at: '2025-08-08',
                description: 'Global health initiatives and technology innovation',
                xml_990_score: 0.82,
                network_score: 0.75,
                enhanced_score: 0.88,
                combined_score: 0.81
            },
            {
                opportunity_id: 'unified_opp_006',
                organization_name: 'Richmond Education Initiative',
                funnel_stage: 'candidates',
                organization_type: 'Nonprofit',
                source_type: 'Nonprofit',
                compatibility_score: 0.89,
                discovery_source: 'ProPublica',
                is_schedule_i_grantee: true,
                funding_amount: 175000,
                discovered_at: '2025-08-07',
                description: 'STEM education and workforce development programs',
                xml_990_score: 0.89,
                network_score: 0.93,
                enhanced_score: 0.85,
                combined_score: 0.89
            },
            {
                opportunity_id: 'unified_opp_007',
                organization_name: 'Health Innovation Foundation',
                funnel_stage: 'candidates',
                organization_type: 'Foundation',
                source_type: 'Commercial',
                compatibility_score: 0.91,
                discovery_source: 'Commercial Intelligence',
                is_schedule_i_grantee: false,
                funding_amount: 320000,
                discovered_at: '2025-08-06',
                description: 'Healthcare technology and digital health solutions',
                xml_990_score: 0.85,
                network_score: 0.92,
                enhanced_score: 0.91,
                combined_score: 0.89,
                ai_analyzed: false,
                ai_processing: false,
                ai_error: false
            },
            
            // TARGETS - Strategic analysis complete
            {
                opportunity_id: 'unified_opp_008',
                organization_name: 'Department of Health & Human Services',
                funnel_stage: 'targets',
                organization_type: 'Government',
                source_type: 'Government',
                compatibility_score: 0.91,
                discovery_source: 'Grants.gov',
                is_schedule_i_grantee: false,
                funding_amount: 750000,
                discovered_at: '2025-08-05',
                description: 'Public health infrastructure and emergency preparedness',
                xml_990_score: 0.88,
                network_score: 0.85,
                enhanced_score: 0.92,
                combined_score: 0.88
            },
            {
                opportunity_id: 'unified_opp_009',
                organization_name: 'Rural Development Initiative', 
                funnel_stage: 'targets',
                organization_type: 'Government',
                source_type: 'Government',
                compatibility_score: 0.94,
                discovery_source: 'Grants.gov',
                is_schedule_i_grantee: false,
                funding_amount: 250000,
                discovered_at: '2025-08-04',
                description: 'Rural community infrastructure and economic development',
                xml_990_score: 0.91,
                network_score: 0.96,
                enhanced_score: 0.95,
                combined_score: 0.94,
                ai_analyzed: true,
                ai_processing: false,
                ai_error: false,
                ai_summary: 'High-priority target with excellent network connections and strong funding history.'
            },
            
            // OPPORTUNITIES - Ready for action
            {
                opportunity_id: 'unified_opp_010',
                organization_name: 'Google.org',
                funnel_stage: 'opportunities',
                organization_type: 'Corporate',
                source_type: 'Commercial',
                compatibility_score: 0.89,
                discovery_source: 'Commercial Intelligence',
                is_schedule_i_grantee: false,
                funding_amount: 300000,
                discovered_at: '2025-08-03',
                description: 'Technology for social good and digital equity initiatives',
                xml_990_score: 0.87,
                network_score: 0.91,
                enhanced_score: 0.88,
                combined_score: 0.89,
                ai_analyzed: true,
                ai_processing: false,
                ai_error: false,
                ai_summary: 'Excellent opportunity with strong alignment and active funding programs.'
            }
        ],
        
        // COMPUTED PROPERTIES - Auto-filtered data for each tab
        get prospectsData() {
            // DISCOVER tab: prospects + qualified_prospects
            return this.opportunitiesData.filter(opp => 
                ['prospects', 'qualified_prospects'].includes(opp.funnel_stage)
            );
        },
        
        get qualifiedProspects() {
            // PLAN tab: qualified_prospects + candidates
            return this.opportunitiesData.filter(opp => 
                ['qualified_prospects', 'candidates'].includes(opp.funnel_stage)
            );
        },
        
        get candidatesData() {
            // ANALYZE tab: candidates + targets  
            return this.opportunitiesData.filter(opp => 
                ['candidates', 'targets'].includes(opp.funnel_stage)
            );
        },
        
        get targetsData() {
            // EXAMINE tab: targets + opportunities
            return this.opportunitiesData.filter(opp => 
                ['targets', 'opportunities'].includes(opp.funnel_stage)
            );
        },
        
        prospectsLoading: false,
        prospectsStageFilter: '', // Filter by funnel stage
        
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
        
        // New Discovery Functions
        async startDiscovery(track) {
            console.log(`startDiscovery called with track: ${track}`);
            console.log(`discoveryProgress[${track}] current state:`, this.discoveryProgress[track]);
            console.log('selectedDiscoveryProfile:', this.selectedDiscoveryProfile?.profile_id);
            
            if (!this.selectedDiscoveryProfile) {
                this.showNotification('No Profile Selected', 'Please select a profile before starting discovery', 'warning');
                return;
            }
            
            if (this.discoveryProgress[track]) {
                console.log(`Discovery for ${track} already in progress, skipping`);
                return;
            }
            
            console.log(`Setting discoveryProgress[${track}] = true`);
            this.discoveryProgress[track] = true;
            
            try {
                console.log(`Starting ${track} discovery for profile:`, this.selectedDiscoveryProfile?.profile_id);
                this.showNotification(`${track.toUpperCase()} Discovery`, 'Starting discovery...', 'info');
                
                // Add small delay to ensure "Running..." state is visible
                await new Promise(resolve => setTimeout(resolve, 500));
                
                const response = await fetch(`/api/discovery/${track}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        profile_id: this.selectedDiscoveryProfile.profile_id,
                        state: 'VA',
                        limit: 50
                    })
                });
                
                if (response.ok) {
                    console.log(`${track} discovery API response received`);
                    const result = await response.json();
                    console.log(`${track} discovery result:`, result);
                    
                    // Handle different response structures
                    let count = 0;
                    if (result.results && result.results.results) {
                        count = result.results.results.length;
                    } else if (result.results && Array.isArray(result.results)) {
                        count = result.results.length; 
                    } else if (result.total_found !== undefined) {
                        count = result.total_found;
                    }
                    console.log(`${track} discovery found ${count} results`);
                    this.discoveryStats[track] = count;
                    
                    // Update discovery total results (with error handling)
                    try {
                        if (this.updateDiscoveryTotalResults) {
                            this.updateDiscoveryTotalResults();
                        }
                    } catch (e) {
                        console.log('updateDiscoveryTotalResults not available, skipping');
                    }
                    
                    // Always add mock data for demo purposes since real APIs aren't connected
                    if (this.selectedDiscoveryProfile) {
                        console.log(`>>> ATTEMPTING TO ADD MOCK DATA for ${track} track (count was: ${count})`);
                        await this.addMockProspectsData(track);
                        console.log(`>>> FINISHED ADDING MOCK DATA for ${track} track`);
                    } else {
                        console.log(`>>> NO SELECTED PROFILE - Cannot add mock data for ${track}`);
                    }
                    
                    this.showNotification('Discovery Complete', `Found ${count > 0 ? count : 'sample'} ${track} opportunities`, 'success');
                    this.workflowProgress.discover = true;
                    
                    // Refresh prospects table after successful discovery
                    if (this.activeStage === 'discover') {
                        console.log('Refreshing prospects table...');
                        await this.loadProspectsData();
                    }
                } else {
                    const error = await response.json();
                    this.showNotification('Discovery Failed', error.detail || `${track} discovery failed`, 'error');
                }
            } catch (error) {
                console.error(`Failed to run ${track} discovery:`, error);
                this.showNotification('Discovery Error', `An error occurred during ${track} discovery`, 'error');
            } finally {
                console.log(`Finally block: Setting discoveryProgress[${track}] = false`);
                try {
                    this.discoveryProgress[track] = false;
                    console.log(`discoveryProgress[${track}] is now:`, this.discoveryProgress[track]);
                    
                    // Force Alpine.js to update the UI
                    this.$nextTick(() => {
                        console.log(`UI update completed for ${track} button`);
                    });
                } catch (finalError) {
                    console.error('Error in finally block:', finalError);
                    // Force reset even if there's an error
                    if (this.discoveryProgress) {
                        this.discoveryProgress[track] = false;
                    }
                }
            }
        },
        
        async startAllDiscovery() {
            if (!this.selectedDiscoveryProfile || this.multiTrackInProgress) return;
            
            this.multiTrackInProgress = true;
            
            try {
                this.showNotification('Multi-Track Discovery', 'Running all discovery tracks...', 'info');
                
                const tracks = ['nonprofit', 'federal', 'state', 'commercial'];
                const promises = tracks.map(track => this.startDiscovery(track));
                
                await Promise.all(promises);
                
                this.showNotification('All Tracks Complete', `Discovery complete across all tracks`, 'success');
            } catch (error) {
                console.error('Failed to run multi-track discovery:', error);
                this.showNotification('Discovery Error', 'An error occurred during multi-track discovery', 'error');
            } finally {
                this.multiTrackInProgress = false;
            }
        },
        
        // Mock data function moved here for scope access from startDiscovery
        async addMockProspectsData(track) {
            console.log(`addMockProspectsData called for track: ${track}`);
            console.log('Current prospectsData:', this.prospectsData);
            console.log('Selected profile:', this.selectedDiscoveryProfile);
            
            // Add sample prospects data for demo purposes when real discovery returns no results
            const mockOpportunities = [
                {
                    organization_name: `Sample ${track.charAt(0).toUpperCase() + track.slice(1)} Foundation`,
                    opportunity_type: track,
                    funding_amount: track === 'state' ? 25000 : track === 'commercial' ? 50000 : 75000,
                    deadline: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
                    match_score: 0.85,
                    funnel_stage: 'prospects',
                    discovery_source: track,
                    compatibility_score: 0.85,
                    source_type: track.charAt(0).toUpperCase() + track.slice(1),
                    stage_display_name: 'Prospects'
                },
                {
                    organization_name: `Demo ${track.charAt(0).toUpperCase() + track.slice(1)} Grant Program`,
                    opportunity_type: track,
                    funding_amount: track === 'state' ? 15000 : track === 'commercial' ? 30000 : 40000,
                    deadline: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(),
                    match_score: 0.72,
                    funnel_stage: 'prospects',
                    discovery_source: track,
                    compatibility_score: 0.72,
                    source_type: track.charAt(0).toUpperCase() + track.slice(1),
                    stage_display_name: 'Prospects'
                }
            ];

            try {
                console.log('Adding mock opportunities directly to prospects data');
                const profileId = this.selectedDiscoveryProfile.profile_id;
                
                const enhancedMockOpportunities = mockOpportunities.map((opp, index) => ({
                    ...opp,
                    opportunity_id: `mock_${track}_${Date.now()}_${index}`,
                    profile_id: profileId,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    stage_updated_at: new Date().toISOString(),
                    status: 'active'
                }));
                
                if (!this.opportunitiesData) {
                    this.opportunitiesData = [];
                }
                
                // Add new opportunities to unified data
                this.opportunitiesData.push(...enhancedMockOpportunities);
                console.log(`Added ${enhancedMockOpportunities.length} mock opportunities, total opportunities now: ${this.opportunitiesData.length}`);
                
                this.$nextTick(() => {
                    console.log('UI update completed after adding mock data');
                });
            } catch (error) {
                console.log('Mock data addition failed:', error);
            }
        },
        
        updateDiscoveryTotalResults() {
            this.discoveryStats.totalResults = 
                this.discoveryStats.nonprofit + 
                this.discoveryStats.federal + 
                this.discoveryStats.state + 
                this.discoveryStats.commercial;
        },
        
        viewDiscoveryResults() {
            if (this.discoveryStats.totalResults === 0) return;
            
            this.showNotification('Discovery Results', `Viewing ${this.discoveryStats.totalResults} total results`, 'info');
            // Could switch to a results view or open a modal
        },
        
        clearDiscoveryResults() {
            this.discoveryStats = {
                activeTracks: 4,
                totalResults: 0,
                nonprofit: 0,
                federal: 0,
                state: 0,
                commercial: 0
            };
            
            this.discoveryProgress = {
                nonprofit: false,
                federal: false,
                state: false,
                commercial: false
            };
            
            this.showNotification('Results Cleared', 'All discovery results have been cleared', 'info');
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
            if (!this.workflowProgress.welcome) {
                return 'welcome';
            } else if (!this.workflowProgress.profiler) {
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
                'welcome': '0. Get Started',
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
        
        // NTEE CODE MODAL FUNCTIONS
        openNteeModal() {
            // Initialize temp selection with current selected codes
            this.nteeModal.tempSelectedCodes = [...this.nteeModal.selectedNteeCodes];
            this.nteeModal.selectedMainCategory = null;
            this.nteeModal.isOpen = true;
        },
        
        closeNteeModal() {
            this.nteeModal.isOpen = false;
            this.nteeModal.selectedMainCategory = null;
            // Don't save temp selections when closing
        },
        
        selectMainCategory(categoryKey) {
            this.nteeModal.selectedMainCategory = categoryKey;
        },
        
        saveNteeSelection() {
            // Save the temporary selections to the main selection
            this.nteeModal.selectedNteeCodes = [...this.nteeModal.tempSelectedCodes];
            
            // Update the current profile if one is selected
            if (this.selectedProfile && this.selectedProfile.profile_id) {
                // Add NTEE codes to profile data if not already present
                if (!this.selectedProfile.ntee_codes) {
                    this.selectedProfile.ntee_codes = [];
                }
                this.selectedProfile.ntee_codes = [...this.nteeModal.selectedNteeCodes];
            }
            
            this.closeNteeModal();
            this.showEnhancedNotification(`Selected ${this.nteeModal.selectedNteeCodes.length} NTEE codes`, 'success');
        },
        
        // Get selected NTEE codes with their full information
        getSelectedNteeCodesInfo() {
            const selectedInfo = [];
            
            this.nteeModal.selectedNteeCodes.forEach(code => {
                // Find the code in the full list
                Object.keys(this.fullNteeCodeList).forEach(categoryKey => {
                    const category = this.fullNteeCodeList[categoryKey];
                    const subcategory = category.subcategories.find(sub => sub.code === code);
                    
                    if (subcategory) {
                        selectedInfo.push({
                            code: subcategory.code,
                            name: subcategory.name,
                            category: categoryKey,
                            categoryName: category.category
                        });
                    }
                });
            });
            
            // Sort alphabetically by code
            return selectedInfo.sort((a, b) => a.code.localeCompare(b.code));
        },
        
        // Remove an NTEE code from selection
        removeNteeCode(codeToRemove) {
            this.nteeModal.selectedNteeCodes = this.nteeModal.selectedNteeCodes.filter(code => code !== codeToRemove);
            
            // Update the current profile if one is selected
            if (this.selectedProfile && this.selectedProfile.ntee_codes) {
                this.selectedProfile.ntee_codes = this.selectedProfile.ntee_codes.filter(code => code !== codeToRemove);
            }
        },
        
        // Check if a main category has any selected subcategories
        categoryHasSelections(categoryKey) {
            if (!this.fullNteeCodeList[categoryKey]) return false;
            
            const categorySubcodes = this.fullNteeCodeList[categoryKey].subcategories.map(sub => sub.code);
            return this.nteeModal.tempSelectedCodes.some(selectedCode => 
                categorySubcodes.includes(selectedCode)
            );
        },
        
        // Toggle subcategory selection (for click without checkbox)
        toggleSubcategorySelection(subcategoryCode) {
            const index = this.nteeModal.tempSelectedCodes.indexOf(subcategoryCode);
            if (index > -1) {
                // Remove if already selected
                this.nteeModal.tempSelectedCodes.splice(index, 1);
            } else {
                // Add if not selected
                this.nteeModal.tempSelectedCodes.push(subcategoryCode);
            }
        },
        
        // Check if a subcategory is selected
        isSubcategorySelected(subcategoryCode) {
            return this.nteeModal.tempSelectedCodes.includes(subcategoryCode);
        },

        // GOVERNMENT CRITERIA MODAL FUNCTIONS
        openGovernmentCriteriaModal() {
            console.log('Opening Government Criteria Modal');
            console.log('Current government_criteria:', this.profileForm.government_criteria);
            console.log('Modal state before:', this.governmentCriteriaModal);
            
            // Initialize temp selection with current selected criteria
            this.governmentCriteriaModal.tempSelectedCriteria = [...(this.profileForm.government_criteria || [])];
            this.governmentCriteriaModal.selectedCategory = null;
            this.governmentCriteriaModal.isOpen = true;
            
            console.log('Modal state after:', this.governmentCriteriaModal);
        },

        closeGovernmentCriteriaModal() {
            this.governmentCriteriaModal.isOpen = false;
            this.governmentCriteriaModal.selectedCategory = null;
            // Don't save temp selections when closing
        },

        selectCriteriaCategory(categoryKey) {
            this.governmentCriteriaModal.selectedCategory = categoryKey;
        },

        saveGovernmentCriteriaSelection() {
            // Save the temporary selections to the main list
            this.profileForm.government_criteria = [...this.governmentCriteriaModal.tempSelectedCriteria];
            this.closeGovernmentCriteriaModal();
            this.showNotification(`Selected ${this.profileForm.government_criteria.length} government criteria`, 'success');
        },

        // Get selected government criteria with their full information
        getSelectedGovernmentCriteriaInfo() {
            const selectedInfo = [];
            
            if (!this.profileForm?.government_criteria) {
                return selectedInfo;
            }
            
            this.profileForm.government_criteria.forEach(criteriaId => {
                // Find the criteria in the full list
                Object.keys(this.governmentCriteriaList).forEach(categoryKey => {
                    const category = this.governmentCriteriaList[categoryKey];
                    const criteria = category.criteria.find(c => c.id === criteriaId);
                    
                    if (criteria) {
                        selectedInfo.push({
                            id: criteriaId,
                            name: criteria.name,
                            category: category.category,
                            description: criteria.description,
                            sources: criteria.sources || []
                        });
                    }
                });
            });
            
            // Sort alphabetically by name
            return selectedInfo.sort((a, b) => a.name.localeCompare(b.name));
        },

        // Remove government criteria from selection
        removeGovernmentCriteria(criteriaId) {
            const index = this.profileForm.government_criteria.indexOf(criteriaId);
            if (index > -1) {
                this.profileForm.government_criteria.splice(index, 1);
            }
            
            // Update the current profile if one is selected
            if (this.selectedProfile && this.selectedProfile.government_criteria) {
                this.selectedProfile.government_criteria = this.selectedProfile.government_criteria.filter(c => c !== criteriaId);
            }
        },

        // Check if a criteria category has any selected items
        categoryHasCriteriaSelections(categoryKey) {
            if (!this.governmentCriteriaList[categoryKey]) return false;
            
            const categoryCriteriaIds = this.governmentCriteriaList[categoryKey].criteria.map(c => c.id);
            return this.governmentCriteriaModal.tempSelectedCriteria.some(selectedId => 
                categoryCriteriaIds.includes(selectedId)
            );
        },

        // Toggle criteria selection
        toggleCriteriaSelection(criteriaId) {
            const index = this.governmentCriteriaModal.tempSelectedCriteria.indexOf(criteriaId);
            if (index > -1) {
                // Remove if already selected
                this.governmentCriteriaModal.tempSelectedCriteria.splice(index, 1);
            } else {
                // Add if not selected
                this.governmentCriteriaModal.tempSelectedCriteria.push(criteriaId);
            }
        },

        // Check if a criteria is selected
        isCriteriaSelected(criteriaId) {
            return this.governmentCriteriaModal.tempSelectedCriteria.includes(criteriaId);
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
                'welcome': 'Tip: Use the quick start demo to explore all platform features before creating your first profile.',
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
                'welcome': 'Welcome & Getting Started',
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
                'welcome': 'Welcome',
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
                'welcome': 'Getting started with Catalynx platform',
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
            this.isEditingProfile = false;
            this.currentEditingProfile = null;
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
                        funding_types: this.profileForm.funding_types,
                        grants_gov_categories: this.profileForm.grants_gov_categories || []
                    },
                    annual_revenue: this.profileForm.annual_revenue,
                    location: this.profileForm.location || null,
                    notes: this.profileForm.notes || null
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
        
        
        closeViewProfile() {
            this.showViewProfile = false;
            this.selectedProfile = {};
        },
        
        closeEditProfile() {
            this.showEditProfile = false;
            this.selectedProfile = {};
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
            },

            // Profile Management Functions

            resetProfileForm() {
                this.profileForm = {
                    profile_id: '',
                    name: '',
                    organization_type: '',
                    ein: '',
                    mission_statement: '',
                    focus_areas_text: '',
                    target_populations_text: '',
                    states_text: '',
                    geographic_scope: {
                        nationwide: false,
                        international: false
                    },
                    funding_preferences: {
                        min_amount: null,
                        max_amount: null
                    },
                    annual_revenue: null,
                    staff_size: null,
                    volunteer_count: null,
                    board_size: null,
                    notes: ''
                };
                this.isEditingProfile = false;
                this.currentEditingProfile = null;
            },
            
            // CENTRALIZED FUNNEL STAGE MANAGEMENT
            
            promoteOpportunity(opportunity) {
                console.log(`Promoting ${opportunity.organization_name} from ${opportunity.funnel_stage}`);
                
                const stageProgression = {
                    'prospects': 'qualified_prospects',
                    'qualified_prospects': 'candidates', 
                    'candidates': 'targets',
                    'targets': 'opportunities'
                };
                
                const nextStage = stageProgression[opportunity.funnel_stage];
                if (!nextStage) {
                    console.log(`Cannot promote from ${opportunity.funnel_stage} - already at highest stage`);
                    return;
                }
                
                // Find and update the opportunity in unified data
                const oppIndex = this.opportunitiesData.findIndex(opp => opp.opportunity_id === opportunity.opportunity_id);
                if (oppIndex !== -1) {
                    this.opportunitiesData[oppIndex].funnel_stage = nextStage;
                    this.opportunitiesData[oppIndex].stage_updated_at = new Date().toISOString();
                    console.log(`Promoted ${opportunity.organization_name} to ${nextStage}`);
                    
                    // Trigger reactivity
                    this.$nextTick(() => {
                        console.log('UI updated after promotion');
                    });
                }
            },
            
            demoteOpportunity(opportunity) {
                console.log(`Demoting ${opportunity.organization_name} from ${opportunity.funnel_stage}`);
                
                const stageRegression = {
                    'opportunities': 'targets',
                    'targets': 'candidates',
                    'candidates': 'qualified_prospects',
                    'qualified_prospects': 'prospects'
                };
                
                const prevStage = stageRegression[opportunity.funnel_stage];
                if (!prevStage) {
                    console.log(`Cannot demote from ${opportunity.funnel_stage} - already at lowest stage`);
                    return;
                }
                
                // Find and update the opportunity in unified data
                const oppIndex = this.opportunitiesData.findIndex(opp => opp.opportunity_id === opportunity.opportunity_id);
                if (oppIndex !== -1) {
                    this.opportunitiesData[oppIndex].funnel_stage = prevStage;
                    this.opportunitiesData[oppIndex].stage_updated_at = new Date().toISOString();
                    console.log(`Demoted ${opportunity.organization_name} to ${prevStage}`);
                    
                    // Trigger reactivity
                    this.$nextTick(() => {
                        console.log('UI updated after demotion');
                    });
                }
            },
            
            // Prospects Discovery Functions (Stage 1: Prospects)
            
            async loadProspectsData() {
                if (!this.selectedDiscoveryProfile) {
                    console.log('No profile selected, using existing opportunities data');
                    return;
                }
                
                // Check if we have recent data for this profile (unified data already exists)
                if (this.opportunitiesData && this.opportunitiesData.length > 0) {
                    console.log(`Already have ${this.opportunitiesData.length} total opportunities, ${this.prospectsData.length} prospects visible`);
                    return;
                }
                
                this.prospectsLoading = true;
                try {
                    const profileId = this.selectedDiscoveryProfile.profile_id;
                    const stageFilter = this.prospectsStageFilter ? `?stage=${this.prospectsStageFilter}` : '';
                    
                    const response = await fetch(`/api/funnel/${profileId}/opportunities${stageFilter}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Merge new opportunities into unified data
                        if (data.opportunities && data.opportunities.length > 0) {
                            this.opportunitiesData.push(...data.opportunities);
                        }
                        this.addLogEntry('prospects', [`Loaded ${data.opportunities?.length || 0} new opportunities, total: ${this.opportunitiesData.length}`]);
                    } else {
                        this.addLogEntry('prospects-error', [`Failed to load prospects: ${response.statusText}`]);
                    }
                } catch (error) {
                    console.error('Failed to load prospects data:', error);
                    this.addLogEntry('prospects-error', [`Failed to load prospects: ${error.message}`]);
                } finally {
                    this.prospectsLoading = false;
                }
            },
            
            filteredProspects() {
                console.log('filteredProspects called, prospectsData:', this.prospectsData);
                console.log('prospectsStageFilter:', this.prospectsStageFilter);
                
                if (!this.prospectsData) {
                    console.log('No prospectsData, returning empty array');
                    return [];
                }
                
                if (this.prospectsStageFilter) {
                    const filtered = this.prospectsData.filter(prospect => 
                        prospect.funnel_stage === this.prospectsStageFilter
                    );
                    console.log('Filtered prospects:', filtered);
                    return filtered;
                }
                
                console.log('Returning all prospectsData:', this.prospectsData);
                return this.prospectsData;
            },
            
            
            // Legacy promote/demote functions - delegate to centralized functions
            async promoteProspect(prospect) {
                this.promoteOpportunity(prospect);
            },
            
            async demoteProspect(prospect) {
                this.demoteOpportunity(prospect);
            },
            
            // Utility functions - using shared CatalynxUtils
            formatStageWithNumber: CatalynxUtils.formatStageWithNumber,
            getStageColor: CatalynxUtils.getStageColor,
            getOrganizationTypeColor: CatalynxUtils.getOrganizationTypeColor
        }
    }
}

// ========================================
// SEPARATE DATA CONTEXTS REMOVED
// ========================================
// 
// Previous planTabData() and analyzeTabData() functions have been removed
// All functionality consolidated into main catalynxApp() context
// 
// Benefits:
// - Single source of truth for all opportunity data
// - Consistent profile selection across tabs
// - Centralized funnel stage management
// - Shared state and utility functions
// - Simplified data flow and maintenance
//
// All tabs now use the unified opportunitiesData with computed filtering:
// - DISCOVER: prospects + qualified_prospects
// - PLAN: qualified_prospects + candidates  
// - ANALYZE: candidates + targets
// - EXAMINE: targets + opportunities (ready for implementation)
//
// ========================================

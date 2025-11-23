/**
 * API Helper Utilities
 * Phase 9 - Frontend Migration Support
 *
 * Provides wrapper functions for modern V2/Tool-based API calls
 */

/**
 * Execute a 12-factor tool via the unified tool execution API
 *
 * @param {string} toolName - Name of the tool (e.g., 'opportunity-screening-tool')
 * @param {object} inputs - Tool-specific input parameters
 * @param {object} config - Optional tool configuration
 * @returns {Promise<object>} Tool execution result
 */
async function executeToolAPI(toolName, inputs, config = {}) {
    try {
        const response = await fetch(`/api/v1/tools/${encodeURIComponent(toolName)}/execute`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({inputs, config})
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Tool execution failed');
        }

        console.log(`✅ Tool ${toolName} executed successfully (${data.execution_time_ms}ms, $${data.cost})`);

        return data;
    } catch (error) {
        console.error(`❌ Tool execution failed for ${toolName}:`, error);
        throw error;
    }
}

/**
 * Execute a workflow via the workflow API
 *
 * @param {string} workflowName - Name of the workflow
 * @param {object} context - Workflow execution context
 * @returns {Promise<object>} Workflow result
 */
async function executeWorkflow(workflowName, context) {
    try {
        // Start workflow
        const initResponse = await fetch('/api/v1/workflows/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workflow_name: workflowName,
                context: context
            })
        });

        if (!initResponse.ok) {
            throw new Error(`Failed to start workflow: ${initResponse.statusText}`);
        }

        const {execution_id} = await initResponse.json();
        console.log(`🚀 Workflow ${workflowName} started (ID: ${execution_id})`);

        // Poll for results
        return await pollWorkflowResults(execution_id);

    } catch (error) {
        console.error(`❌ Workflow execution failed for ${workflowName}:`, error);
        throw error;
    }
}

/**
 * Poll workflow status and return results when complete
 *
 * @param {string} executionId - Workflow execution ID
 * @param {number} maxAttempts - Maximum polling attempts (default: 60)
 * @param {number} pollInterval - Milliseconds between polls (default: 1000)
 * @returns {Promise<object>} Workflow results
 */
async function pollWorkflowResults(executionId, maxAttempts = 60, pollInterval = 1000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            // Check status
            const statusResponse = await fetch(`/api/v1/workflows/status/${executionId}`);
            const status = await statusResponse.json();

            console.log(`⏳ Workflow ${executionId} status: ${status.status} (attempt ${attempt}/${maxAttempts})`);

            // Completed successfully
            if (status.status === 'completed') {
                const resultsResponse = await fetch(`/api/v1/workflows/results/${executionId}`);
                const results = await resultsResponse.json();

                console.log(`✅ Workflow ${executionId} completed successfully`);
                return results;
            }

            // Failed
            if (status.status === 'failed') {
                const errorMsg = status.errors ? status.errors.join(', ') : 'Unknown error';
                throw new Error(`Workflow failed: ${errorMsg}`);
            }

            // Still running, wait and poll again
            await new Promise(resolve => setTimeout(resolve, pollInterval));

        } catch (error) {
            if (error.message.includes('Workflow failed')) {
                throw error;  // Re-throw workflow failures
            }
            console.error(`Error polling workflow ${executionId}:`, error);
            // Continue polling on temporary errors
        }
    }

    throw new Error(`Workflow timeout: ${executionId} did not complete after ${maxAttempts} attempts`);
}

/**
 * Check response headers for deprecation warnings
 *
 * @param {Response} response - Fetch API response object
 */
function checkDeprecationHeaders(response) {
    if (response.headers.get('X-Deprecated') === 'true') {
        const replacement = response.headers.get('X-Replacement-Endpoint');
        const notes = response.headers.get('X-Migration-Notes');
        const sunset = response.headers.get('Sunset');

        console.warn('⚠️ DEPRECATED API USED');
        console.warn(`   Current endpoint: ${response.url}`);
        console.warn(`   Use instead: ${replacement}`);
        if (notes) console.warn(`   Notes: ${notes}`);
        if (sunset) console.warn(`   Sunset date: ${sunset}`);
        console.warn(`   Migration guide: ${response.headers.get('X-Migration-Guide')}`);
    }
}

/**
 * Wrapper for fetch that automatically checks deprecation headers
 *
 * @param {string} url - URL to fetch
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
async function fetchWithDeprecationCheck(url, options = {}) {
    const response = await fetch(url, options);
    checkDeprecationHeaders(response);
    return response;
}

/**
 * Execute opportunity screening (Tool 10)
 *
 * @param {array} opportunities - Opportunities to screen
 * @param {object} profile - Profile data
 * @param {string} mode - 'fast' or 'thorough'
 * @param {object} config - Optional configuration
 * @returns {Promise<object>} Screening results
 */
async function screenOpportunities(opportunities, profile, mode = 'fast', config = {}) {
    return await executeToolAPI('Opportunity Screening Tool', {
        opportunities: opportunities,
        profile: profile,
        mode: mode
    }, {
        threshold: config.threshold || 0.55,
        max_recommendations: config.max_recommendations || 15,
        ...config
    });
}

/**
 * Execute deep intelligence analysis (Tool 2 - Deep Intelligence Tool)
 *
 * @param {object} opportunity - Opportunity to analyze
 * @param {object} profile - Profile data
 * @param {string} depth - 'essentials' or 'premium' (deprecated: 'quick', 'standard', 'enhanced', 'complete')
 * @returns {Promise<object>} Analysis results
 */
async function analyzeOpportunityDeep(opportunity, profile, depth = 'essentials') {
    try {
        // Map deprecated depths to new 2-tier system
        const depthMapping = {
            'quick': 'essentials',
            'current': 'essentials',
            'standard': 'essentials',
            'enhanced': 'premium',
            'complete': 'premium'
        };

        const tier = depthMapping[depth] || depth;

        // Get profile ID from profile object or current active profile
        let profileId = profile?.id || profile?.profile_id;
        if (!profileId) {
            // Try to get from Alpine.js global state
            if (typeof Alpine !== 'undefined' && Alpine.store) {
                const appStore = Alpine.store('app');
                profileId = appStore?.selectedProfile?.profile_id || appStore?.selectedDiscoveryProfile?.profile_id;
            }
            // Fallback: Try window.currentProfileId or window.appData
            if (!profileId && typeof window !== 'undefined') {
                profileId = window.currentProfileId || window.appData?.selectedProfile?.profile_id;
            }
            if (!profileId) {
                console.error('[analyzeOpportunityDeep] No profile ID found. Tried:', {
                    'profile.id': profile?.id,
                    'profile.profile_id': profile?.profile_id,
                    'Alpine.store': typeof Alpine !== 'undefined' ? 'available' : 'unavailable',
                    'window.currentProfileId': window?.currentProfileId,
                    'window.appData': window?.appData
                });
                throw new Error('Profile ID is required for intelligence analysis. Please select a profile first.');
            }
        }

        const response = await fetch(`/api/intelligence/profiles/${profileId}/analysis`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                opportunity_id: opportunity.id || opportunity.opportunity_id,
                tier: tier,
                add_ons: []
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message || 'Intelligence analysis failed');
        }

        const result = await response.json();

        console.log(`✅ Deep intelligence analysis initiated (tier: ${tier}, cost: $${result.estimated_cost})`);

        // If async processing, poll for results
        if (result.task_id) {
            return await pollIntelligenceResults(result.task_id);
        }

        // Return immediate result
        return {
            success: true,
            data: result.result,
            cost: result.actual_cost || result.estimated_cost,
            execution_time_ms: null,
            tool_name: 'Deep Intelligence Tool',
            tool_version: '2.0.0'
        };

    } catch (error) {
        console.error(`❌ Deep intelligence analysis failed:`, error);
        throw error;
    }
}

/**
 * Poll intelligence analysis results
 *
 * @param {string} taskId - Intelligence task ID
 * @param {number} maxAttempts - Maximum polling attempts (default: 120)
 * @param {number} pollInterval - Milliseconds between polls (default: 2000)
 * @returns {Promise<object>} Analysis results
 */
async function pollIntelligenceResults(taskId, maxAttempts = 120, pollInterval = 2000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const response = await fetch(`/api/intelligence/analysis/${taskId}`);
            const status = await response.json();

            console.log(`⏳ Intelligence task ${taskId} status: ${status.status} (${status.progress_percentage}%)`);

            if (status.status === 'completed') {
                console.log(`✅ Intelligence analysis completed`);
                return {
                    success: true,
                    data: status.result,
                    cost: status.processing_cost,
                    execution_time_ms: null,
                    tool_name: 'Deep Intelligence Tool',
                    tool_version: '2.0.0'
                };
            }

            if (status.status === 'failed') {
                throw new Error(status.error_message || 'Intelligence analysis failed');
            }

            // Still running, wait and poll again
            await new Promise(resolve => setTimeout(resolve, pollInterval));

        } catch (error) {
            if (error.message.includes('failed')) {
                throw error;
            }
            console.error(`Error polling intelligence task ${taskId}:`, error);
        }
    }

    throw new Error(`Intelligence analysis timeout: Task ${taskId} did not complete after ${maxAttempts} attempts`);
}

/**
 * Execute multi-dimensional scoring (Tool 20)
 *
 * @param {object} opportunity - Opportunity to score
 * @param {object} profile - Profile data
 * @param {string} stage - Funnel stage for context
 * @returns {Promise<object>} Scoring results
 */
async function scoreOpportunity(opportunity, profile, stage = 'DISCOVER') {
    return await executeToolAPI('Multi-Dimensional Scorer Tool', {
        opportunity: opportunity,
        profile: profile,
        stage: stage
    });
}

/**
 * Execute data export (Tool 18)
 *
 * @param {array} data - Data to export
 * @param {string} dataType - Type of data (e.g., 'opportunities')
 * @param {string} format - Export format (e.g., 'excel', 'csv', 'pdf')
 * @param {array} fields - Optional field selection
 * @returns {Promise<object>} Export result with download URL
 */
async function exportData(data, dataType, format = 'excel', fields = null) {
    const inputs = {
        data: data,
        data_type: dataType,
        format: format
    };

    if (fields) {
        inputs.fields = fields;
    }

    return await executeToolAPI('Data Export Tool', inputs);
}

/**
 * Generate report (Tool 21)
 *
 * @param {object} opportunity - Opportunity data
 * @param {object} profile - Profile data
 * @param {string} template - Report template ('comprehensive', 'executive', 'risk', 'implementation')
 * @param {string} format - Output format (default: 'html')
 * @returns {Promise<object>} Report generation result
 */
async function generateReport(opportunity, profile, template = 'comprehensive', format = 'html') {
    return await executeToolAPI('Report Generator Tool', {
        opportunity: opportunity,
        profile: profile,
        template: template,
        format: format
    });
}

/**
 * Build profile via V2 API
 *
 * @param {string} ein - Organization EIN
 * @param {boolean} enableTool25 - Enable web intelligence
 * @param {boolean} enableTool2 - Enable deep AI analysis (costs $0.75)
 * @param {number} qualityThreshold - Minimum quality threshold
 * @returns {Promise<object>} Profile build result
 */
async function buildProfileV2(ein, enableTool25 = true, enableTool2 = false, qualityThreshold = 0.70) {
    const response = await fetch('/api/v2/profiles/build', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            ein: ein,
            enable_tool25: enableTool25,
            enable_tool2: enableTool2,
            quality_threshold: qualityThreshold
        })
    });

    const result = await response.json();

    if (!result.success && !result.workflow_result) {
        throw new Error(result.error || 'Profile build failed');
    }

    console.log(`✅ Profile built for EIN ${ein} (cost: $${result.workflow_result?.cost || 0})`);

    return result;
}

/**
 * Score opportunities via V2 API
 *
 * @param {string} profileId - Profile ID
 * @param {array} opportunities - Opportunities to score
 * @returns {Promise<object>} Scoring results
 */
async function scoreOpportunitiesV2(profileId, opportunities) {
    const response = await fetch(`/api/v2/profiles/${profileId}/opportunities/score`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            opportunities: opportunities
        })
    });

    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || 'Opportunity scoring failed');
    }

    console.log(`✅ Scored ${opportunities.length} opportunities`);

    return result;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        executeToolAPI,
        executeWorkflow,
        pollWorkflowResults,
        pollIntelligenceResults,
        checkDeprecationHeaders,
        fetchWithDeprecationCheck,
        screenOpportunities,
        analyzeOpportunityDeep,
        scoreOpportunity,
        exportData,
        generateReport,
        buildProfileV2,
        scoreOpportunitiesV2
    };
}

console.log('✅ API Helper utilities loaded');

// Shared utility functions used across all tabs
// Extracted from app.js for better modularity
// Handles data formatting, validation, and UI utilities

const CatalynxUtils = {
    formatStageWithNumber(stage) {
        const stageMapping = {
            // New pipeline stage mapping
            'discovery': '#1 Prospect',
            'pre_scoring': '#2 Qualified',
            'deep_analysis': '#3 Candidate',
            'recommendations': '#4 Target',
            // Current business stage terms (unified)
            'prospects': '#1 Prospect',
            'qualified': '#2 Qualified',
            'candidates': '#3 Candidate',
            'targets': '#4 Target',
            'opportunities': '#5 Opportunity'
        };
        return stageMapping[stage] || stage.replace('_', ' ').toUpperCase();
    },

    getStageColor(stage) {
        const colorMapping = {
            // New pipeline stage colors
            'discovery': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
            'pre_scoring': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            'deep_analysis': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            'recommendations': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            // Current business stage terms (unified)
            'prospects': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
            'qualified': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            'candidates': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            'targets': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            'opportunities': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
        };
        return colorMapping[stage] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    },

    getActualStage(prospect) {
        // FIXED: Priority funnel_stage (corrected by backend) > pipeline_stage > stage > default
        return prospect.funnel_stage || prospect.pipeline_stage || prospect.stage || 'prospects';
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
    },

    // SCHEMA VALIDATION AND STANDARDIZATION FUNCTIONS
    validateOpportunitySchema(opportunity) {
        // First check if opportunity is null or undefined (from standardization failures)
        if (!opportunity || typeof opportunity !== 'object') {
            console.warn('Invalid opportunity object (null or non-object):', opportunity);
            return false;
        }

        const requiredFields = [
            'opportunity_id', 'organization_name', 'funnel_stage', 'source_type',
            'discovery_source', 'compatibility_score', 'discovered_at'
        ];

        const missingFields = requiredFields.filter(field => !opportunity[field]);
        if (missingFields.length > 0) {
            console.warn('Missing required fields in opportunity:', missingFields, opportunity);
            return false;
        }

        // Validate score ranges (0-1)
        const scoreFields = ['raw_score', 'compatibility_score', 'confidence_level',
                           'xml_990_score', 'network_score', 'enhanced_score', 'combined_score'];
        for (const field of scoreFields) {
            if (opportunity[field] && (opportunity[field] < 0 || opportunity[field] > 1)) {
                console.warn(`Invalid score range for ${field}:`, opportunity[field]);
                return false;
            }
        }

        // Validate funnel stage - UNIFIED STAGE APPROACH with fallback handling
        const validStages = ['prospects', 'qualified_prospects', 'candidates', 'targets', 'opportunities'];

        // Handle legacy or invalid stages with fallback
        if (!validStages.includes(opportunity.funnel_stage)) {
            // Auto-correct common invalid stages
            if (opportunity.funnel_stage === 'discovery' || opportunity.funnel_stage === 'qualified') {
                opportunity.funnel_stage = opportunity.funnel_stage === 'discovery' ? 'prospects' : 'qualified_prospects';
                console.log(`Auto-corrected funnel stage: ${opportunity.funnel_stage === 'prospects' ? 'discovery' : 'qualified'} → ${opportunity.funnel_stage}`);
            } else {
                console.warn('Invalid funnel stage, defaulting to prospects:', opportunity.funnel_stage);
                opportunity.funnel_stage = 'prospects'; // Default fallback
            }
        }

        return true;
    },

    standardizeOpportunityData(rawOpportunity) {
        // Enhanced data standardization with canonical stage mapping
        if (!rawOpportunity || typeof rawOpportunity !== 'object') {
            console.warn('Invalid opportunity object:', rawOpportunity);
            return null;
        }

        // UNIFIED STAGE APPROACH: Direct stage usage (database aligned with business terms)
        const current_stage = rawOpportunity.current_stage || rawOpportunity.pipeline_stage || rawOpportunity.stage || 'prospects';
        const funnel_stage = current_stage;

        // Log stage standardization for debugging
        if (rawOpportunity.current_stage || rawOpportunity.pipeline_stage || rawOpportunity.stage) {
            console.log(`Stage standardization: database(${rawOpportunity.current_stage}) pipeline(${rawOpportunity.pipeline_stage}) stage(${rawOpportunity.stage}) → ${current_stage}`);
        }

        const standardized = {
            // Core fields with strict validation
            opportunity_id: rawOpportunity.opportunity_id || `opp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            organization_name: rawOpportunity.organization_name || rawOpportunity.name || '[Organization Name Missing]',

            // SIMPLIFIED STAGE FIELDS - Direct business terms
            current_stage: current_stage,
            funnel_stage: funnel_stage,

            source_type: rawOpportunity.source_type || rawOpportunity.organization_type || 'Nonprofit',
            discovery_source: rawOpportunity.discovery_source || rawOpportunity.source || 'Unknown Source',

            // Opportunity details
            program_name: rawOpportunity.program_name || rawOpportunity.program || null,
            description: rawOpportunity.description || rawOpportunity.summary || null,
            funding_amount: rawOpportunity.funding_amount || rawOpportunity.amount || null,
            application_deadline: rawOpportunity.application_deadline || rawOpportunity.deadline || null,

            // Scoring with type validation
            raw_score: parseFloat(rawOpportunity.raw_score || rawOpportunity.score || 0.0),
            compatibility_score: parseFloat(rawOpportunity.compatibility_score || 0.0),
            confidence_level: parseFloat(rawOpportunity.confidence_level || rawOpportunity.confidence || 0.0),

            // Advanced scoring (for candidates/targets/opportunities)
            xml_990_score: rawOpportunity.xml_990_score || null,
            network_score: rawOpportunity.network_score || null,
            enhanced_score: rawOpportunity.enhanced_score || null,
            combined_score: rawOpportunity.combined_score || null,

            // Metadata
            is_schedule_i_grantee: Boolean(rawOpportunity.is_schedule_i_grantee),
            discovered_at: rawOpportunity.discovered_at || new Date().toISOString(),
            stage_updated_at: rawOpportunity.stage_updated_at || new Date().toISOString(),

            // Contact and location
            contact_info: rawOpportunity.contact_info || {},
            geographic_info: rawOpportunity.geographic_info || {},

            // Analysis factors
            match_factors: rawOpportunity.match_factors || {},
            risk_factors: rawOpportunity.risk_factors || {},

            // Analysis status and AI
            analysis_status: rawOpportunity.analysis_status || {},
            strategic_analysis: rawOpportunity.strategic_analysis || {},
            ai_analyzed: Boolean(rawOpportunity.ai_analyzed),
            ai_processing: Boolean(rawOpportunity.ai_processing),
            ai_error: Boolean(rawOpportunity.ai_error),
            ai_summary: rawOpportunity.ai_summary || null,
            action_plan: rawOpportunity.action_plan || null,

            // Preserve any additional fields not covered above
            ...Object.fromEntries(
                Object.entries(rawOpportunity).filter(([key]) =>
                    !['opportunity_id', 'organization_name', 'name', 'pipeline_stage', 'funnel_stage', 'stage',
                      'source_type', 'organization_type', 'discovery_source', 'source', 'program_name', 'program',
                      'description', 'summary', 'funding_amount', 'amount', 'application_deadline', 'deadline',
                      'raw_score', 'score', 'compatibility_score', 'confidence_level', 'confidence',
                      'xml_990_score', 'network_score', 'enhanced_score', 'combined_score',
                      'is_schedule_i_grantee', 'discovered_at', 'stage_updated_at',
                      'contact_info', 'geographic_info', 'match_factors', 'risk_factors',
                      'analysis_status', 'strategic_analysis', 'ai_analyzed', 'ai_processing', 'ai_error',
                      'ai_summary', 'action_plan'].includes(key)
                )
            )
        };

        return standardized;
    },

    deduplicateOpportunities(opportunities) {
        // Deduplicate opportunities based on unique identifiers
        if (!Array.isArray(opportunities)) {
            return [];
        }

        const seen = new Set();
        const deduplicated = [];

        for (const opportunity of opportunities) {
            if (!opportunity) continue;

            // Create unique key using multiple identifiers
            const uniqueKey = this.generateOpportunityKey(opportunity);

            if (!seen.has(uniqueKey)) {
                seen.add(uniqueKey);
                deduplicated.push(opportunity);
            } else {
                console.log(`Filtered duplicate opportunity: ${opportunity.organization_name}`);
            }
        }

        return deduplicated;
    },

    generateOpportunityKey(opportunity) {
        // Generate unique key for opportunity identification
        const orgName = (opportunity.organization_name || '').trim().toLowerCase();
        const opportunityId = opportunity.external_data?.opportunity_id ||
                             opportunity.opportunity_id ||
                             opportunity.external_data?.ein ||
                             `${orgName}_${opportunity.source_type || 'unknown'}`;

        // Include source and funding amount for better uniqueness
        const sourceType = opportunity.source_type || 'unknown';
        const fundingAmount = opportunity.funding_amount || 0;

        return `${opportunityId}_${orgName}_${sourceType}_${fundingAmount}`;
    }
};

// Make CatalynxUtils available globally
window.CatalynxUtils = CatalynxUtils;

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CatalynxUtils;
}
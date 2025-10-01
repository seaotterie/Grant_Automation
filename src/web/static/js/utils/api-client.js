// Centralized API Client for Catalynx
// Handles all HTTP requests with consistent error handling and logging
// Provides convenience methods for common API operations

const ApiClient = {
    // Base configuration
    baseURL: '', // Empty for relative URLs
    defaultHeaders: {
        'Content-Type': 'application/json'
    },

    // Request timeout in milliseconds
    defaultTimeout: 30000, // 30 seconds

    // Create request options with defaults
    _createRequestOptions(options = {}) {
        return {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            }
        };
    },

    // Add timeout to fetch requests
    _fetchWithTimeout(url, options = {}) {
        const timeout = options.timeout || this.defaultTimeout;

        return Promise.race([
            fetch(url, options),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Request timeout')), timeout)
            )
        ]);
    },

    // Core request method with error handling
    async request(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const requestOptions = this._createRequestOptions(options);

        // Log request for debugging (localhost only)
        if (window.location.hostname === 'localhost') {
            console.log(`🌐 API Request: ${requestOptions.method || 'GET'} ${url}`, requestOptions);
        }

        try {
            const response = await this._fetchWithTimeout(url, requestOptions);

            // Log response for debugging (localhost only)
            if (window.location.hostname === 'localhost') {
                console.log(`📡 API Response: ${response.status} ${url}`);
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({
                    detail: `HTTP ${response.status}: ${response.statusText}`
                }));

                const error = new Error(`Request failed: ${response.status}`);
                error.response = {
                    status: response.status,
                    statusText: response.statusText,
                    data: errorData
                };
                throw error;
            }

            // Return parsed JSON for most responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            // Return raw response for non-JSON content
            return response;

        } catch (error) {
            // Add context to error
            error.context = {
                url,
                method: requestOptions.method || 'GET',
                timestamp: new Date().toISOString()
            };

            // Use ErrorHandler if available
            if (window.ErrorHandler) {
                window.ErrorHandler.showError(error, { operation: 'API Request', url });
            } else {
                console.error('API Request failed:', error);
            }

            throw error;
        }
    },

    // Convenience methods for common HTTP verbs
    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    },

    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async put(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async patch(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    },

    // Profile-specific API methods
    profiles: {
        // Get all profiles
        async list() {
            return ApiClient.get('/api/profiles');
        },

        // Get single profile by ID
        async get(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}`);
        },

        // Create new profile
        async create(profileData) {
            return ApiClient.post('/api/profiles', profileData);
        },

        // Update existing profile
        async update(profileId, profileData) {
            return ApiClient.put(`/api/profiles/${profileId}`, profileData);
        },

        // Delete profile
        async delete(profileId) {
            return ApiClient.delete(`/api/profiles/${profileId}`);
        },

        // Get profile opportunities
        async getOpportunities(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}/opportunities`);
        },

        // Get profile metrics
        async getMetrics(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}/metrics`);
        },

        // Get verified intelligence
        async getVerifiedIntelligence(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}/verified-intelligence`);
        },

        // Get plan results
        async getPlanResults(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}/plan-results`);
        },

        // Update plan results
        async updatePlanResults(profileId, planData) {
            return ApiClient.post(`/api/profiles/${profileId}/plan-results`, planData);
        },

        // Get opportunity scores
        async getOpportunityScores(profileId, requestData) {
            return ApiClient.post(`/api/profiles/${profileId}/opportunity-scores`, requestData);
        },

        // Get leads
        async getLeads(profileId, requestData) {
            return ApiClient.post(`/api/profiles/${profileId}/leads`, requestData);
        },

        // Fetch EIN data
        async fetchEin(einData) {
            return ApiClient.post('/api/profiles/fetch-ein', einData);
        }
    },

    // Discovery and processors API methods
    discovery: {
        // Start discovery process
        async start(profileId, processors, options = {}) {
            return ApiClient.post(`/api/profiles/${profileId}/discover`, {
                processors,
                ...options
            });
        },

        // Get discovery status
        async getStatus(profileId) {
            return ApiClient.get(`/api/profiles/${profileId}/discovery-status`);
        },

        // Run specific processor
        async runProcessor(profileId, processorName, data = {}) {
            return ApiClient.post(`/api/profiles/${profileId}/processors/${processorName}`, data);
        }
    },

    // Welcome/onboarding API methods
    welcome: {
        // Get welcome status
        async getStatus() {
            return ApiClient.get('/api/welcome/status');
        },

        // Create sample profile
        async createSampleProfile(sampleData) {
            return ApiClient.post('/api/welcome/sample-profile', sampleData);
        },

        // Run quick start
        async quickStart(quickStartData) {
            return ApiClient.post('/api/welcome/quick-start', quickStartData);
        }
    },

    // Health check and system status
    system: {
        // Health check
        async health() {
            return ApiClient.get('/api/health');
        },

        // Get system status
        async status() {
            return ApiClient.get('/api/status');
        }
    },

    // Export functionality
    export: {
        // Export data in various formats
        async exportData(profileId, format = 'json', options = {}) {
            return ApiClient.post(`/api/profiles/${profileId}/export`, {
                format,
                ...options
            });
        }
    },

    // Batch operations for multiple requests
    async batch(requests) {
        const promises = requests.map(({ endpoint, options }) =>
            this.request(endpoint, options).catch(error => ({ error }))
        );

        return Promise.all(promises);
    },

    // Upload files (for future use)
    async upload(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);

        // Add additional data to form
        Object.entries(additionalData).forEach(([key, value]) => {
            formData.append(key, typeof value === 'object' ? JSON.stringify(value) : value);
        });

        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }
};

// Make ApiClient available globally
window.ApiClient = ApiClient;

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}
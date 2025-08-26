// Catalynx API Client
// Centralized API communication module extracted from monolithic app.js

class CatalynxAPI {
    constructor() {
        this.baseURL = '';  // Same origin
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
    
    async request(method, endpoint, data = null, options = {}) {
        const config = {
            method,
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(this.baseURL + endpoint, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ 
                    message: `HTTP ${response.status}: ${response.statusText}` 
                }));
                throw new Error(errorData.message || `Request failed with status ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error(`API request failed: ${method} ${endpoint}`, error);
            throw error;
        }
    }
    
    // HTTP method helpers
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, null, options);
    }
    
    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, data, options);
    }
    
    async put(endpoint, data, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }
    
    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }
    
    async patch(endpoint, data, options = {}) {
        return this.request('PATCH', endpoint, data, options);
    }
    
    // System endpoints
    async getSystemHealth() {
        return this.get('/api/system/health');
    }
    
    async getSystemStatus() {
        return this.get('/api/system/status');
    }
    
    async getDashboardOverview() {
        return this.get('/api/dashboard/overview');
    }
    
    // Profile endpoints
    async getProfiles(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/api/profiles${queryString ? '?' + queryString : ''}`);
    }
    
    async getProfile(profileId) {
        return this.get(`/api/profiles/${profileId}`);
    }
    
    async createProfile(profileData) {
        return this.post('/api/profiles', profileData);
    }
    
    async updateProfile(profileId, updateData) {
        return this.put(`/api/profiles/${profileId}`, updateData);
    }
    
    async deleteProfile(profileId) {
        return this.delete(`/api/profiles/${profileId}`);
    }
    
    async getProfileAnalytics(profileId) {
        return this.get(`/api/profiles/${profileId}/analytics`);
    }
    
    async getProfileOpportunities(profileId, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/api/profiles/${profileId}/opportunities${queryString ? '?' + queryString : ''}`);
    }
    
    // Discovery endpoints
    async getDiscoveryTracks() {
        return this.get('/api/discovery/tracks');
    }
    
    async executeDiscovery(discoveryData) {
        return this.post('/api/discovery/execute', discoveryData);
    }
    
    async getEntityCacheStats() {
        return this.get('/api/discovery/entity-cache-stats');
    }
    
    async discoverEntityAnalytics(profileId, params = {}) {
        return this.post(`/api/profiles/${profileId}/discover/entity-analytics`, params);
    }
    
    async getEntityPreview(profileId) {
        return this.get(`/api/profiles/${profileId}/discover/entity-preview`);
    }
    
    async searchOpportunities(query, params = {}) {
        const searchParams = new URLSearchParams({ q: query, ...params }).toString();
        return this.get(`/api/discovery/search?${searchParams}`);
    }
    
    // Scoring endpoints
    async scoreGovernmentOpportunity(scoringData) {
        return this.post('/api/scoring/government', scoringData);
    }
    
    async scoreFinancialFit(scoringData) {
        return this.post('/api/scoring/financial', scoringData);
    }
    
    async scoreAILite(scoringData) {
        return this.post('/api/scoring/ai-lite', scoringData);
    }
    
    async scoreNetworkAnalysis(scoringData) {
        return this.post('/api/scoring/network', scoringData);
    }
    
    async comprehensiveScoring(scoringData) {
        return this.post('/api/scoring/comprehensive', scoringData);
    }
    
    async getScoringConfiguration() {
        return this.get('/api/scoring/configuration');
    }
    
    // AI Processing endpoints
    async aiLiteValidate(requestData) {
        return this.post('/api/ai/lite-1/validate', requestData);
    }
    
    async aiLiteStrategicScore(requestData) {
        return this.post('/api/ai/lite-2/strategic-score', requestData);
    }
    
    async aiHeavyResearchBridge(requestData) {
        return this.post('/api/ai/heavy-1/research-bridge', requestData);
    }
    
    async aiHeavyComprehensiveResearch(requestData) {
        return this.post('/api/ai/heavy-2/comprehensive-research', requestData);
    }
    
    async aiOrchestratedPipeline(requestData) {
        return this.post('/api/ai/orchestrated-pipeline', requestData);
    }
    
    async getAIServiceStatus() {
        return this.get('/api/ai/service-status');
    }
    
    async getAIUsageMetrics() {
        return this.get('/api/ai/usage-metrics');
    }
    
    // Export endpoints
    async exportOpportunities(exportData) {
        return this.post('/api/export/opportunities', exportData);
    }
    
    async generateComprehensiveReport(reportData) {
        return this.post('/api/export/comprehensive-report', reportData);
    }
    
    async getExportFormats() {
        return this.get('/api/export/formats');
    }
    
    // Admin endpoints
    async getSystemOverview() {
        return this.get('/api/admin/system/overview');
    }
    
    async clearSystemCache(cacheType = 'all') {
        return this.post('/api/admin/cache/clear', { cache_type: cacheType });
    }
    
    async getRecentLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.get(`/api/admin/logs/recent${queryString ? '?' + queryString : ''}`);
    }
    
    // Utility endpoints
    async getHelp() {
        return this.get('/api/help');
    }
    
    async globalSearch(query, params = {}) {
        const searchParams = new URLSearchParams({ q: query, ...params }).toString();
        return this.get(`/api/search?${searchParams}`);
    }
    
    async submitFeedback(feedbackData) {
        return this.post('/api/feedback', feedbackData);
    }
}

// Create global API instance
const api = new CatalynxAPI();
window.CatalynxAPI = api;
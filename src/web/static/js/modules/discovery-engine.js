// Catalynx Discovery Engine Module
// Discovery workflow and processor management extracted from monolithic app.js

class CatalynxDiscoveryEngine {
    constructor(apiClient = null, websocketClient = null) {
        this.api = apiClient || (window.CatalynxAPI ? new window.CatalynxAPI() : null);
        this.ws = websocketClient || (window.CatalynxWebSocket ? new window.CatalynxWebSocket() : null);
        
        // Discovery tracks and processors
        this.discoveryTracks = {
            commercial: {
                name: 'Commercial Track',
                description: 'Foundation Directory, corporate foundations, and commercial grant databases',
                processors: ['foundation_directory_fetch', 'bmf_filter', 'propublica_fetch'],
                estimated_duration: '5-10 minutes',
                cost_range: '$0.50 - $2.00'
            },
            state: {
                name: 'State Track', 
                description: 'Virginia state agencies and local government opportunities',
                processors: ['va_state_grants_fetch'],
                estimated_duration: '2-5 minutes',
                cost_range: '$0.25 - $0.75'
            },
            government: {
                name: 'Government Track',
                description: 'Federal opportunities via Grants.gov and USASpending.gov',
                processors: ['grants_gov_fetch', 'usaspending_fetch', 'government_opportunity_scorer'],
                estimated_duration: '10-15 minutes',
                cost_range: '$1.00 - $3.00'
            },
            nonprofit: {
                name: 'Nonprofit Track',
                description: 'Peer analysis and board network intelligence',
                processors: ['board_network_analyzer', 'enhanced_network_analyzer'],
                estimated_duration: '3-8 minutes',
                cost_range: '$0.30 - $1.50'
            }
        };
        
        // Discovery session state
        this.activeSessions = new Map();
        this.sessionListeners = new Map();
    }
    
    /**
     * Start discovery session for profile
     */
    async startDiscovery(profileId, options = {}) {
        try {
            const {
                tracks = ['commercial', 'state', 'government', 'nonprofit'],
                processors = null, // Override to use specific processors
                realTime = true, // Enable real-time updates
                priority = 'normal' // normal, high, urgent
            } = options;
            
            // Validate inputs
            if (!profileId) {
                throw new Error('Profile ID is required for discovery');
            }
            
            // Create discovery session
            const sessionId = this.generateSessionId();
            const session = {
                session_id: sessionId,
                profile_id: profileId,
                tracks: tracks,
                processors: processors || this.getProcessorsForTracks(tracks),
                status: 'starting',
                progress: 0,
                started_at: new Date().toISOString(),
                estimated_completion: this.estimateCompletion(tracks),
                results: {},
                errors: [],
                metadata: {
                    priority,
                    real_time: realTime,
                    cost_estimate: this.estimateCost(tracks)
                }
            };
            
            // Store session locally
            this.activeSessions.set(sessionId, session);
            
            // Initialize WebSocket for real-time updates
            if (realTime && this.ws) {
                this.setupRealtimeUpdates(sessionId);
            }
            
            // Start discovery via API
            if (this.api) {
                const response = await this.api.post('/api/profiles/discovery/start', {
                    profile_id: profileId,
                    session_id: sessionId,
                    tracks,
                    processors: session.processors,
                    options: session.metadata
                });
                
                session.status = 'running';
                this.activeSessions.set(sessionId, session);
                
                return {
                    success: true,
                    session_id: sessionId,
                    session: session,
                    api_response: response
                };
            }
            
            // Mock discovery if no API
            this.mockDiscoveryProgress(sessionId);
            
            return {
                success: true,
                session_id: sessionId,
                session: session
            };
            
        } catch (error) {
            console.error('Failed to start discovery:', error);
            throw error;
        }
    }
    
    /**
     * Get discovery session status
     */
    getDiscoverySession(sessionId) {
        return this.activeSessions.get(sessionId) || null;
    }
    
    /**
     * Stop discovery session
     */
    async stopDiscovery(sessionId) {
        try {
            const session = this.activeSessions.get(sessionId);
            if (!session) {
                throw new Error('Discovery session not found');
            }
            
            // Stop via API
            if (this.api) {
                await this.api.post('/api/profiles/discovery/stop', {
                    session_id: sessionId
                });
            }
            
            // Update local session
            session.status = 'stopped';
            session.stopped_at = new Date().toISOString();
            
            // Clean up WebSocket listeners
            this.cleanupRealtimeUpdates(sessionId);
            
            return { success: true, session };
            
        } catch (error) {
            console.error('Failed to stop discovery:', error);
            throw error;
        }
    }
    
    /**
     * Run single processor
     */
    async runProcessor(profileId, processorName, options = {}) {
        try {
            if (!this.api) {
                throw new Error('API client required for processor execution');
            }
            
            const response = await this.api.post(`/api/processors/${processorName}/run`, {
                profile_id: profileId,
                ...options
            });
            
            return response;
            
        } catch (error) {
            console.error(`Failed to run processor ${processorName}:`, error);
            throw error;
        }
    }
    
    /**
     * Get available processors
     */
    async getAvailableProcessors() {
        try {
            if (this.api) {
                const response = await this.api.get('/api/processors');
                return response;
            }
            
            // Return mock processors if no API
            return {
                success: true,
                processors: Object.values(this.discoveryTracks).flatMap(track => track.processors)
            };
            
        } catch (error) {
            console.error('Failed to get available processors:', error);
            throw error;
        }
    }
    
    /**
     * Get discovery results for profile
     */
    async getDiscoveryResults(profileId, options = {}) {
        try {
            const {
                limit = 50,
                offset = 0,
                track = null,
                processor = null,
                since = null
            } = options;
            
            if (this.api) {
                const params = new URLSearchParams({
                    limit: limit.toString(),
                    offset: offset.toString(),
                    ...(track && { track }),
                    ...(processor && { processor }),
                    ...(since && { since })
                });
                
                const response = await this.api.get(`/api/profiles/${profileId}/discoveries?${params}`);
                return response;
            }
            
            // Return mock results if no API
            return {
                success: true,
                results: [],
                total: 0,
                has_more: false
            };
            
        } catch (error) {
            console.error('Failed to get discovery results:', error);
            throw error;
        }
    }
    
    /**
     * Setup real-time updates for discovery session
     */
    setupRealtimeUpdates(sessionId) {
        if (!this.ws) return;
        
        const listener = (event) => {
            if (event.type === 'discovery_progress' && event.session_id === sessionId) {
                this.handleDiscoveryUpdate(sessionId, event.data);
            }
        };
        
        this.sessionListeners.set(sessionId, listener);
        this.ws.addEventListener('message', listener);
    }
    
    /**
     * Handle discovery progress update
     */
    handleDiscoveryUpdate(sessionId, updateData) {
        const session = this.activeSessions.get(sessionId);
        if (!session) return;
        
        // Update session with new data
        Object.assign(session, updateData);
        
        // Emit custom event for listeners
        const event = new CustomEvent('catalynx:discovery:progress', {
            detail: { sessionId, session, update: updateData }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Cleanup real-time updates
     */
    cleanupRealtimeUpdates(sessionId) {
        const listener = this.sessionListeners.get(sessionId);
        if (listener && this.ws) {
            this.ws.removeEventListener('message', listener);
            this.sessionListeners.delete(sessionId);
        }
    }
    
    /**
     * Get processors for discovery tracks
     */
    getProcessorsForTracks(tracks) {
        return tracks.flatMap(track => this.discoveryTracks[track]?.processors || []);
    }
    
    /**
     * Estimate completion time for tracks
     */
    estimateCompletion(tracks) {
        const maxMinutes = tracks.reduce((max, track) => {
            const trackData = this.discoveryTracks[track];
            if (!trackData) return max;
            
            const duration = trackData.estimated_duration;
            const minutes = parseInt(duration.split('-')[1]) || 10;
            return Math.max(max, minutes);
        }, 5);
        
        const completionTime = new Date();
        completionTime.setMinutes(completionTime.getMinutes() + maxMinutes);
        
        return completionTime.toISOString();
    }
    
    /**
     * Estimate cost for tracks
     */
    estimateCost(tracks) {
        return tracks.reduce((total, track) => {
            const trackData = this.discoveryTracks[track];
            if (!trackData) return total;
            
            const costRange = trackData.cost_range;
            const maxCost = parseFloat(costRange.split(' - ')[1].replace('$', '')) || 1.0;
            return total + maxCost;
        }, 0);
    }
    
    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `discovery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Mock discovery progress for testing
     */
    mockDiscoveryProgress(sessionId) {
        const session = this.activeSessions.get(sessionId);
        if (!session) return;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20 + 5; // 5-25% increments
            progress = Math.min(progress, 100);
            
            session.progress = Math.round(progress);
            session.status = progress >= 100 ? 'completed' : 'running';
            
            if (progress >= 100) {
                session.completed_at = new Date().toISOString();
                session.results = {
                    opportunities_found: Math.floor(Math.random() * 20) + 5,
                    tracks_completed: session.tracks.length,
                    processors_executed: session.processors.length
                };
                clearInterval(interval);
            }
            
            // Emit progress event
            this.handleDiscoveryUpdate(sessionId, {
                progress: session.progress,
                status: session.status,
                results: session.results
            });
            
        }, 1000 + Math.random() * 2000); // 1-3 second intervals
    }
    
    /**
     * Get discovery track information
     */
    getDiscoveryTracks() {
        return this.discoveryTracks;
    }
    
    /**
     * Validate discovery options
     */
    validateDiscoveryOptions(options) {
        const errors = [];
        
        if (options.tracks) {
            const validTracks = Object.keys(this.discoveryTracks);
            const invalidTracks = options.tracks.filter(track => !validTracks.includes(track));
            if (invalidTracks.length > 0) {
                errors.push(`Invalid tracks: ${invalidTracks.join(', ')}`);
            }
        }
        
        if (options.priority && !['normal', 'high', 'urgent'].includes(options.priority)) {
            errors.push('Priority must be normal, high, or urgent');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
}

// Make available globally for modular system
window.CatalynxDiscoveryEngine = CatalynxDiscoveryEngine;

// Auto-initialize if loaded standalone
if (typeof window !== 'undefined') {
    console.log('✅ CatalynxDiscoveryEngine module loaded');
}
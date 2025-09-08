// Catalynx Profile Management Module
// Profile creation, validation, and management utilities extracted from monolithic app.js

class CatalynxProfileManager {
    constructor(apiClient = null) {
        this.api = apiClient || (window.CatalynxAPI ? new window.CatalynxAPI() : null);
        
        // NTEE Codes (abbreviated list - full list would be loaded from API)
        this.nteeCodes = {
            'A': 'Arts, Culture & Humanities',
            'B': 'Educational Institutions & Related Activities',
            'C': 'Environmental Quality, Protection & Beautification',
            'D': 'Animal-Related',
            'E': 'Health - General & Rehabilitative',
            'F': 'Mental Health, Crisis Intervention',
            'G': 'Disease, Disorders, Medical Disciplines',
            'H': 'Medical Research',
            'I': 'Crime, Legal Related',
            'J': 'Employment, Job Related',
            'K': 'Food, Agriculture & Nutrition',
            'L': 'Housing, Shelter',
            'M': 'Public Safety, Disaster Preparedness & Relief',
            'N': 'Recreation, Sports, Leisure, Athletics',
            'O': 'Youth Development',
            'P': 'Human Services - Multipurpose',
            'Q': 'International, Foreign Affairs & National Security',
            'R': 'Civil Rights, Social Action, Advocacy',
            'S': 'Community Improvement, Capacity Building',
            'T': 'Philanthropy, Voluntarism & Grantmaking Foundations',
            'U': 'Science & Technology Research Institutes, Services',
            'V': 'Social Science Research Institutes, Services',
            'W': 'Public, Society Benefit - Multipurpose',
            'X': 'Religion Related, Spiritual Development',
            'Y': 'Mutual/Membership Benefit Organizations, Other',
            'Z': 'Unknown, Unclassified'
        };
        
        // Default profile template
        this.defaultProfile = {
            profile_id: '',
            name: '',
            organization_type: '',
            ein: '',
            mission_statement: '',
            focus_areas: [],
            program_areas: [],
            target_populations: [],
            ntee_codes: [],
            states: ['VA'], // Default to Virginia
            min_revenue: null,
            max_revenue: null,
            revenue_range: '',
            budget_size: '',
            staff_size: '',
            board_size: null,
            founded_year: null,
            website: '',
            contact_email: '',
            contact_phone: '',
            address: {
                street: '',
                city: '',
                state: 'VA',
                zip: '',
                county: ''
            },
            status: 'active',
            tags: [],
            notes: '',
            created_at: null,
            updated_at: null,
            last_discovery_date: null,
            discovery_count: 0,
            discovery_status: 'never_run',
            opportunities_count: 0
        };
    }
    
    /**
     * Create new profile with validation
     */
    async createProfile(profileData) {
        try {
            // Validate required fields
            const validation = this.validateProfile(profileData);
            if (!validation.isValid) {
                throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
            }
            
            // Merge with defaults
            const profile = {
                ...this.defaultProfile,
                ...profileData,
                profile_id: profileData.profile_id || this.generateProfileId(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            
            // Create via API
            if (this.api) {
                const response = await this.api.post('/api/profiles', profile);
                return response;
            }
            
            // Return locally created profile if no API
            return { success: true, profile };
            
        } catch (error) {
            console.error('Failed to create profile:', error);
            throw error;
        }
    }
    
    /**
     * Update existing profile
     */
    async updateProfile(profileId, updateData) {
        try {
            const updatedProfile = {
                ...updateData,
                updated_at: new Date().toISOString()
            };
            
            if (this.api) {
                const response = await this.api.put(`/api/profiles/${profileId}`, updatedProfile);
                return response;
            }
            
            return { success: true, profile: updatedProfile };
            
        } catch (error) {
            console.error('Failed to update profile:', error);
            throw error;
        }
    }
    
    /**
     * Get profile by ID
     */
    async getProfile(profileId) {
        try {
            if (this.api) {
                const response = await this.api.get(`/api/profiles/${profileId}`);
                return response;
            }
            
            // Return mock profile if no API
            return { success: true, profile: { ...this.defaultProfile, profile_id: profileId } };
            
        } catch (error) {
            console.error('Failed to get profile:', error);
            throw error;
        }
    }
    
    /**
     * Get all profiles with filtering
     */
    async getProfiles(filters = {}) {
        try {
            if (this.api) {
                const queryParams = new URLSearchParams(filters).toString();
                const endpoint = `/api/profiles${queryParams ? '?' + queryParams : ''}`;
                const response = await this.api.get(endpoint);
                return response;
            }
            
            // Return mock profiles if no API
            return { success: true, profiles: [] };
            
        } catch (error) {
            console.error('Failed to get profiles:', error);
            throw error;
        }
    }
    
    /**
     * Delete profile
     */
    async deleteProfile(profileId) {
        try {
            if (this.api) {
                const response = await this.api.delete(`/api/profiles/${profileId}`);
                return response;
            }
            
            return { success: true };
            
        } catch (error) {
            console.error('Failed to delete profile:', error);
            throw error;
        }
    }
    
    /**
     * Validate profile data
     */
    validateProfile(profileData) {
        const errors = [];
        
        // Required fields
        if (!profileData.name || profileData.name.trim().length < 2) {
            errors.push('Organization name is required (minimum 2 characters)');
        }
        
        if (!profileData.organization_type) {
            errors.push('Organization type is required');
        }
        
        if (!profileData.focus_areas || profileData.focus_areas.length === 0) {
            errors.push('At least one focus area is required');
        }
        
        // EIN validation (if provided)
        if (profileData.ein && !this.validateEIN(profileData.ein)) {
            errors.push('Invalid EIN format (should be XX-XXXXXXX or XXXXXXXXX)');
        }
        
        // Email validation (if provided)
        if (profileData.contact_email && !this.validateEmail(profileData.contact_email)) {
            errors.push('Invalid email format');
        }
        
        // URL validation (if provided)
        if (profileData.website && !this.validateURL(profileData.website)) {
            errors.push('Invalid website URL format');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    
    /**
     * Validate EIN format
     */
    validateEIN(ein) {
        const einPattern = /^(\d{2}-?\d{7})$/;
        return einPattern.test(ein);
    }
    
    /**
     * Validate email format
     */
    validateEmail(email) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(email);
    }
    
    /**
     * Validate URL format
     */
    validateURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * Generate unique profile ID
     */
    generateProfileId() {
        return `profile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Get organization types
     */
    getOrganizationTypes() {
        return [
            'Nonprofit Organization',
            'Private Foundation',
            'Community Foundation',
            'Corporate Foundation',
            'Operating Foundation',
            'Public Charity',
            'Religious Organization',
            'Educational Institution',
            'Healthcare Organization',
            'Research Institution',
            'Arts Organization',
            'Environmental Organization',
            'Social Services Organization',
            'Advocacy Organization',
            'Professional Association',
            'Trade Association',
            'Other'
        ];
    }
    
    /**
     * Get NTEE codes list
     */
    getNTEECodes() {
        return this.nteeCodes;
    }
    
    /**
     * Get US states list
     */
    getStates() {
        return [
            { code: 'AL', name: 'Alabama' },
            { code: 'AK', name: 'Alaska' },
            { code: 'AZ', name: 'Arizona' },
            { code: 'AR', name: 'Arkansas' },
            { code: 'CA', name: 'California' },
            { code: 'CO', name: 'Colorado' },
            { code: 'CT', name: 'Connecticut' },
            { code: 'DE', name: 'Delaware' },
            { code: 'FL', name: 'Florida' },
            { code: 'GA', name: 'Georgia' },
            { code: 'HI', name: 'Hawaii' },
            { code: 'ID', name: 'Idaho' },
            { code: 'IL', name: 'Illinois' },
            { code: 'IN', name: 'Indiana' },
            { code: 'IA', name: 'Iowa' },
            { code: 'KS', name: 'Kansas' },
            { code: 'KY', name: 'Kentucky' },
            { code: 'LA', name: 'Louisiana' },
            { code: 'ME', name: 'Maine' },
            { code: 'MD', name: 'Maryland' },
            { code: 'MA', name: 'Massachusetts' },
            { code: 'MI', name: 'Michigan' },
            { code: 'MN', name: 'Minnesota' },
            { code: 'MS', name: 'Mississippi' },
            { code: 'MO', name: 'Missouri' },
            { code: 'MT', name: 'Montana' },
            { code: 'NE', name: 'Nebraska' },
            { code: 'NV', name: 'Nevada' },
            { code: 'NH', name: 'New Hampshire' },
            { code: 'NJ', name: 'New Jersey' },
            { code: 'NM', name: 'New Mexico' },
            { code: 'NY', name: 'New York' },
            { code: 'NC', name: 'North Carolina' },
            { code: 'ND', name: 'North Dakota' },
            { code: 'OH', name: 'Ohio' },
            { code: 'OK', name: 'Oklahoma' },
            { code: 'OR', name: 'Oregon' },
            { code: 'PA', name: 'Pennsylvania' },
            { code: 'RI', name: 'Rhode Island' },
            { code: 'SC', name: 'South Carolina' },
            { code: 'SD', name: 'South Dakota' },
            { code: 'TN', name: 'Tennessee' },
            { code: 'TX', name: 'Texas' },
            { code: 'UT', name: 'Utah' },
            { code: 'VT', name: 'Vermont' },
            { code: 'VA', name: 'Virginia' },
            { code: 'WA', name: 'Washington' },
            { code: 'WV', name: 'West Virginia' },
            { code: 'WI', name: 'Wisconsin' },
            { code: 'WY', name: 'Wyoming' },
            { code: 'DC', name: 'District of Columbia' }
        ];
    }
    
    /**
     * Get revenue ranges
     */
    getRevenueRanges() {
        return [
            { value: 'under_100k', label: 'Under $100,000' },
            { value: '100k_500k', label: '$100,000 - $500,000' },
            { value: '500k_1m', label: '$500,000 - $1,000,000' },
            { value: '1m_5m', label: '$1,000,000 - $5,000,000' },
            { value: '5m_25m', label: '$5,000,000 - $25,000,000' },
            { value: 'over_25m', label: 'Over $25,000,000' }
        ];
    }
    
    /**
     * Format profile data for display
     */
    formatProfileForDisplay(profile) {
        return {
            ...profile,
            formatted_ein: profile.ein ? this.formatEIN(profile.ein) : 'N/A',
            formatted_revenue: this.formatRevenue(profile.revenue_range),
            formatted_created: profile.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A',
            formatted_updated: profile.updated_at ? new Date(profile.updated_at).toLocaleDateString() : 'N/A',
            ntee_labels: profile.ntee_codes ? profile.ntee_codes.map(code => 
                this.nteeCodes[code.charAt(0)] || code
            ) : []
        };
    }
    
    /**
     * Format EIN for display
     */
    formatEIN(ein) {
        if (!ein) return 'N/A';
        const cleaned = ein.replace(/\D/g, '');
        return cleaned.replace(/(\d{2})(\d{7})/, '$1-$2');
    }
    
    /**
     * Format revenue range for display
     */
    formatRevenue(revenueRange) {
        const ranges = this.getRevenueRanges();
        const range = ranges.find(r => r.value === revenueRange);
        return range ? range.label : 'Not specified';
    }
}

// Make available globally for modular system
window.CatalynxProfileManager = CatalynxProfileManager;

// Auto-initialize if loaded standalone
if (typeof window !== 'undefined') {
    console.log('✅ CatalynxProfileManager module loaded');
}
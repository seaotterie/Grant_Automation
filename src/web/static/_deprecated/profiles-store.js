// Profiles Alpine.js Store
// Manages all profile-related state and operations
// Extracted from main Alpine app for better organization

// Initialize profiles store
document.addEventListener('alpine:init', () => {
    Alpine.store('profiles', {
        // State
        profiles: [],
        filteredProfiles: [],
        selectedProfile: null,

        // Profile editing state
        currentEditingProfile: null,
        editingProfileData: {},

        // Loading and status
        profilesLoading: false,
        profileCount: 0,

        // Profile form defaults
        defaultProfile: {
            name: '',
            ein: '',
            organization_type: '',
            status: 'active',
            mission_statement: '',
            focus_areas: [],
            pipeline_stage: 'prospect',
            min_revenue_requirement: null,
            application_deadline: null,
            matching_requirement: null,
            project_duration: null,
            organization_name: ''
        },

        // Getters
        get hasProfiles() {
            return this.profiles.length > 0;
        },

        get activeProfiles() {
            return this.profiles.filter(p => p.status !== 'archived');
        },

        get selectedProfileId() {
            return this.selectedProfile?.profile_id || null;
        },

        get selectedProfileName() {
            return this.selectedProfile?.organization_name || 'No Profile Selected';
        },

        // Actions
        async loadProfiles() {
            console.log('📁 Loading profiles from API...');
            this.profilesLoading = true;

            try {
                const response = await ApiClient.profiles.list();
                const allProfiles = response.profiles ? response.profiles : response;

                this.profiles = allProfiles.filter(profile => profile.status !== 'archived');
                this.filteredProfiles = [...this.profiles];
                this.profileCount = this.profiles.length;

                console.log('✅ Loaded profiles:', this.profiles.map(p => ({
                    id: p.profile_id,
                    name: p.organization_name,
                    status: p.status
                })));

                return this.profiles;

            } catch (error) {
                console.error('❌ Failed to load profiles:', error);
                ErrorHandler.showError(error, { operation: 'Load Profiles' });
                return [];
            } finally {
                this.profilesLoading = false;
            }
        },

        selectProfile(profile) {
            console.log('👆 Selected profile:', profile?.organization_name || 'None');
            this.selectedProfile = profile;

            // Update debug tools
            if (window.catalynx) {
                window.catalynx._lastSelectedProfile = profile;
            }
        },

        async createProfile(profileData) {
            console.log('➕ Creating new profile:', profileData.organization_name);

            try {
                const newProfile = await ApiClient.profiles.create(profileData);

                this.profiles.push(newProfile);
                this.filteredProfiles = [...this.profiles];
                this.profileCount = this.profiles.length;
                this.selectProfile(newProfile);

                console.log('✅ Profile created successfully');
                return newProfile;

            } catch (error) {
                console.error('❌ Failed to create profile:', error);
                ErrorHandler.showError(error, { operation: 'Create Profile' });
                throw error;
            }
        },

        async updateProfile(profileId, profileData) {
            console.log('💾 Updating profile:', profileId, profileData.organization_name);

            try {
                const updatedProfile = await ApiClient.profiles.update(profileId, profileData);

                // Update in profiles array
                const index = this.profiles.findIndex(p => p.profile_id === profileId);
                if (index !== -1) {
                    this.profiles[index] = updatedProfile;
                    this.filteredProfiles = [...this.profiles];

                    // Update selected profile if it's the one being edited
                    if (this.selectedProfile?.profile_id === profileId) {
                        this.selectedProfile = updatedProfile;
                    }
                }

                console.log('✅ Profile updated successfully');
                return updatedProfile;

            } catch (error) {
                console.error('❌ Failed to update profile:', error);
                ErrorHandler.showError(error, { operation: 'Update Profile' });
                throw error;
            }
        },

        async deleteProfile(profileId) {
            console.log('🗑️ Deleting profile:', profileId);

            try {
                await ApiClient.profiles.delete(profileId);

                // Remove from profiles array
                this.profiles = this.profiles.filter(p => p.profile_id !== profileId);
                this.filteredProfiles = [...this.profiles];
                this.profileCount = this.profiles.length;

                // Clear selection if deleted profile was selected
                if (this.selectedProfile?.profile_id === profileId) {
                    this.selectedProfile = null;
                }

                console.log('✅ Profile deleted successfully');

            } catch (error) {
                console.error('❌ Failed to delete profile:', error);
                ErrorHandler.showError(error, { operation: 'Delete Profile' });
                throw error;
            }
        },

        filterProfiles(searchTerm = '', filters = {}) {
            if (!searchTerm && Object.keys(filters).length === 0) {
                this.filteredProfiles = [...this.profiles];
                return;
            }

            this.filteredProfiles = this.profiles.filter(profile => {
                // Text search
                if (searchTerm) {
                    const searchLower = searchTerm.toLowerCase();
                    const matchesText =
                        profile.organization_name?.toLowerCase().includes(searchLower) ||
                        profile.mission_statement?.toLowerCase().includes(searchLower) ||
                        profile.ein?.includes(searchTerm);

                    if (!matchesText) return false;
                }

                // Additional filters
                if (filters.status && profile.status !== filters.status) {
                    return false;
                }

                if (filters.organization_type && profile.organization_type !== filters.organization_type) {
                    return false;
                }

                return true;
            });

            console.log(`🔍 Filtered ${this.filteredProfiles.length} of ${this.profiles.length} profiles`);
        },

        // Profile editing helpers
        startEditingProfile(profile) {
            this.currentEditingProfile = profile.profile_id;
            this.editingProfileData = { ...profile };
        },

        cancelEditingProfile() {
            this.currentEditingProfile = null;
            this.editingProfileData = {};
        },

        async saveEditingProfile() {
            if (!this.currentEditingProfile) return;

            try {
                await this.updateProfile(this.currentEditingProfile, this.editingProfileData);
                this.cancelEditingProfile();
                return true;
            } catch (error) {
                return false;
            }
        },

        // Profile validation
        validateProfile(profileData) {
            const errors = [];

            if (!profileData.organization_name?.trim()) {
                errors.push('Organization name is required');
            }

            if (!profileData.ein?.trim()) {
                errors.push('EIN is required');
            } else if (!/^\d{2}-\d{7}$/.test(profileData.ein)) {
                errors.push('EIN must be in format XX-XXXXXXX');
            }

            if (!profileData.organization_type) {
                errors.push('Organization type is required');
            }

            return {
                isValid: errors.length === 0,
                errors
            };
        },

        // Reset store
        reset() {
            this.profiles = [];
            this.filteredProfiles = [];
            this.selectedProfile = null;
            this.currentEditingProfile = null;
            this.editingProfileData = {};
            this.profilesLoading = false;
            this.profileCount = 0;
        }
    });

    console.log('🏪 Profiles store initialized');
});
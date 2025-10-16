/**
 * Profiles Management Module
 * Handles all profile CRUD operations using V2 Profile API
 *
 * Replaces: PROFILER, WELCOME, and SETTINGS stages
 * APIs Used: /api/v2/profiles/*
 */

function profilesModule() {
    return {
        // =================================================================
        // STATE
        // =================================================================

        profiles: [],
        filteredProfiles: [],
        selectedProfile: null,
        loading: false,
        error: null,

        // Pagination
        currentPage: 1,
        itemsPerPage: 50,
        totalProfiles: 0,

        // Search & Filter
        searchQuery: '',
        sortBy: 'name',
        sortOrder: 'asc',

        // Modal state (managed by event system)
        profileToDelete: null,

        // =================================================================
        // LIFECYCLE
        // =================================================================

        /**
         * Initialize profiles module
         */
        async init() {
            await this.loadProfiles();
            this.setupModalListeners();
        },

        // =================================================================
        // PROFILE CRUD OPERATIONS
        // =================================================================

        /**
         * Load all profiles with pagination and search
         * @param {number} page
         * @param {number} limit
         */
        async loadProfiles(page = null, limit = null) {
            this.loading = true;
            this.error = null;

            try {
                const currentPage = page || this.currentPage;
                const pageSize = limit || this.itemsPerPage;

                const params = new URLSearchParams({
                    page: currentPage,
                    limit: pageSize,
                    sort: this.sortBy,
                    order: this.sortOrder
                });

                if (this.searchQuery) {
                    params.append('search', this.searchQuery);
                }

                const response = await fetch(`/api/v2/profiles?${params}`);

                if (!response.ok) {
                    throw new Error(`Failed to load profiles: ${response.statusText}`);
                }

                const data = await response.json();

                // Handle both response formats: {success: true, profiles: []} and {profiles: []}
                if (data.profiles) {
                    this.profiles = data.profiles || [];
                    this.filteredProfiles = [...this.profiles]; // Initialize filtered list
                    this.totalProfiles = data.total || this.profiles.length;
                    this.currentPage = currentPage;
                } else if (data.success === false) {
                    throw new Error(data.error || 'Unknown error');
                } else {
                    throw new Error('Invalid response format');
                }

            } catch (error) {
                console.error('Failed to load profiles:', error);
                this.error = error.message;
                this.showNotification?.('Failed to load profiles', 'error');
            } finally {
                this.loading = false;
            }
        },

        /**
         * Create new profile (manual or EIN-based)
         * @param {Object} profileData
         */
        async createProfile(profileData) {
            this.loading = true;

            try {
                // Use /api/v2/profiles/build for EIN-based profile creation
                // Use /api/v2/profiles for manual creation
                const endpoint = profileData.ein
                    ? '/api/v2/profiles/build'
                    : '/api/v2/profiles';

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profileData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to create profile');
                }

                const data = await response.json();

                if (data.success) {
                    this.showNotification?.('Profile created successfully', 'success');

                    // Reload profiles list
                    await this.loadProfiles();

                    // Select new profile
                    if (data.profile) {
                        this.selectProfile(data.profile);
                    }

                    return data;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Failed to create profile:', error);
                this.error = error.message;
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
            }
        },

        /**
         * Update existing profile
         * @param {string} profileId
         * @param {Object} updates
         */
        async updateProfile(profileId, updates) {
            this.loading = true;

            try {
                const response = await fetch(`/api/v2/profiles/${profileId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updates)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to update profile');
                }

                const data = await response.json();

                if (data.success) {
                    this.showNotification?.('Profile updated successfully', 'success');

                    // Reload profiles list
                    await this.loadProfiles();

                    // Update selected profile if it's the one being edited
                    if (this.selectedProfile?.profile_id === profileId) {
                        this.selectedProfile = data.profile;
                    }

                    return data;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Failed to update profile:', error);
                this.error = error.message;
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
            }
        },

        /**
         * Delete profile
         * @param {string} profileId
         */
        async deleteProfile(profileId) {
            this.loading = true;

            try {
                const response = await fetch(`/api/v2/profiles/${profileId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to delete profile');
                }

                const data = await response.json();

                if (data.success) {
                    this.showNotification?.('Profile deleted successfully', 'success');

                    // Clear selected profile if it's the one being deleted
                    if (this.selectedProfile?.profile_id === profileId) {
                        this.selectedProfile = null;
                    }

                    // Reload profiles list
                    await this.loadProfiles();

                    this.profileToDelete = null;

                    return data;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Failed to delete profile:', error);
                this.error = error.message;
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
            }
        },

        // =================================================================
        // PROFILE ANALYTICS
        // =================================================================

        /**
         * Get consolidated analytics for a profile
         * @param {string} profileId
         */
        async getAnalytics(profileId) {
            try {
                const response = await fetch(`/api/v2/profiles/${profileId}/analytics`);

                if (!response.ok) {
                    throw new Error('Failed to load analytics');
                }

                const data = await response.json();

                if (data.success) {
                    return data.analytics;
                } else {
                    throw new Error(data.error || 'Unknown error');
                }

            } catch (error) {
                console.error('Failed to load analytics:', error);
                this.showNotification?.('Failed to load analytics', 'error');
                return null;
            }
        },

        /**
         * Get profile quality score
         * @param {string} profileId
         */
        async getQualityScore(profileId) {
            try {
                const response = await fetch(`/api/v2/profiles/${profileId}/quality`);

                if (!response.ok) {
                    throw new Error('Failed to load quality score');
                }

                const data = await response.json();
                return data;

            } catch (error) {
                console.error('Failed to load quality score:', error);
                return null;
            }
        },

        // =================================================================
        // PROFILE EXPORT
        // =================================================================

        /**
         * Export profile data
         * @param {string} profileId
         * @param {string} format - json, csv, excel, pdf
         */
        async exportProfile(profileId, format = 'json') {
            this.loading = true;

            try {
                const response = await fetch(`/api/v2/profiles/${profileId}/export`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        format,
                        include_opportunities: true
                    })
                });

                if (!response.ok) {
                    throw new Error('Export failed');
                }

                const data = await response.json();

                if (data.success) {
                    console.log('Profile exported:', format);
                    this.showNotification?.(`Profile exported as ${format.toUpperCase()}`, 'success');
                    return data.export_result;
                } else {
                    throw new Error(data.error || 'Export failed');
                }

            } catch (error) {
                console.error('Failed to export profile:', error);
                this.showNotification?.('Export failed', 'error');
                throw error;
            } finally {
                this.loading = false;
            }
        },

        // =================================================================
        // UI HELPERS
        // =================================================================

        /**
         * Select a profile
         * @param {Object} profile
         */
        selectProfile(profile) {
            this.selectedProfile = profile;

            // Store profile ID globally for other modules to access
            window.currentProfileId = profile.profile_id || profile.id;

            // Dispatch event for other modules
            this.$dispatch?.('profile-selected', { profile });
        },


        /**
         * Search profiles (debounced)
         */
        searchProfiles() {
            // Debounce search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(async () => {
                this.currentPage = 1; // Reset to first page
                await this.loadProfiles();
            }, 300);
        },

        /**
         * Change sort order
         * @param {string} column
         */
        async changeSort(column) {
            if (this.sortBy === column) {
                // Toggle sort order
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                // New column, default to ascending
                this.sortBy = column;
                this.sortOrder = 'asc';
            }

            await this.loadProfiles();
        },

        /**
         * Go to next page
         */
        async nextPage() {
            const maxPage = Math.ceil(this.totalProfiles / this.itemsPerPage);
            if (this.currentPage < maxPage) {
                this.currentPage++;
                await this.loadProfiles();
            }
        },

        /**
         * Go to previous page
         */
        async prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
                await this.loadProfiles();
            }
        },

        // =================================================================
        // MODAL EVENT HANDLERS (Phase 9 Week 4)
        // =================================================================

        /**
         * Open create profile modal (dispatch event)
         */
        openCreateModal() {
            window.dispatchEvent(new CustomEvent('open-create-profile-modal'));
        },

        /**
         * Open edit profile modal (dispatch event)
         * @param {Object} profile
         */
        openEditModal(profile) {
            this.selectedProfile = profile;
            window.dispatchEvent(new CustomEvent('open-edit-profile-modal', {
                detail: { profile }
            }));
        },

        /**
         * Open delete confirmation modal (dispatch event)
         * @param {Object} profile
         */
        openDeleteModal(profile) {
            this.profileToDelete = profile;
            window.dispatchEvent(new CustomEvent('open-delete-profile-modal', {
                detail: { profile }
            }));
        },

        /**
         * Handle create profile event
         */
        async handleCreateProfile(event) {
            const { formData, mode } = event.detail;

            try {
                if (mode === 'ein') {
                    // Use Tool 25 to fetch profile data
                    await this.createProfileFromEIN(formData.ein);
                } else {
                    // Manual profile creation
                    await this.createProfile(formData);
                }
            } catch (error) {
                console.error('Create profile failed:', error);
            }
        },

        /**
         * Create profile from EIN using Tool 25
         * @param {string} ein
         */
        async createProfileFromEIN(ein) {
            this.loading = true;

            try {
                // Send EIN as-is - backend handles both "123456789" and "12-3456789" formats
                const response = await fetch('/api/v2/profiles/build', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ein: ein.trim() })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to create profile from EIN');
                }

                const data = await response.json();

                if (data.success) {
                    this.showNotification?.('Profile created successfully', 'success');
                    await this.loadProfiles();

                    if (data.profile) {
                        this.selectProfile(data.profile);
                    }
                }
            } catch (error) {
                console.error('Failed to create profile from EIN:', error);
                this.showNotification?.(error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
            }
        },

        /**
         * Handle delete profile confirmed event
         */
        async handleDeleteProfile(event) {
            const { profileId } = event.detail;

            try {
                await this.deleteProfile(profileId);
            } catch (error) {
                console.error('Delete profile failed:', error);
            }
        },

        /**
         * Handle research profile event (Research button)
         * Calls BMF, 990 parsers, and Tool 25 to populate profile data
         */
        async handleResearchProfile(detail) {
            // Handle both event object and direct detail parameter
            const data = detail?.detail || detail;
            const { ein } = data || {};

            if (!ein) {
                console.error('No EIN provided for research');
                this.showNotification?.('EIN required for research', 'error');
                return;
            }

            this.loading = true;
            this.showNotification?.('Researching organization...', 'info');

            try {
                // Call the profile fetch endpoint (BMF + 990 + Tool 25)
                const response = await fetch(`/api/profiles/fetch-ein`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ein })
                });

                if (!response.ok) {
                    throw new Error(`Research failed: ${response.statusText}`);
                }

                const data = await response.json();
                console.log('Research response:', data);
                console.log('Profile data:', data.profile_data);

                if (data.success && data.profile_data) {
                    // Update current profile with researched data
                    if (this.selectedProfile) {
                        // Update all fields with BMF data (including empty values)
                        // This ensures the profile reflects what's actually in the BMF database
                        const nteeCode = data.profile_data.ntee_code || data.profile_data.ntee_code_990 || '';

                        // Show "None Found" message if BMF has no NTEE code
                        const nteeDisplayValue = nteeCode || 'None Found - Enter Manually (optional)';

                        Object.assign(this.selectedProfile, {
                            ntee_code_990: nteeDisplayValue,
                            city: data.profile_data.city || '',
                            state: data.profile_data.state || '',
                            revenue: data.profile_data.revenue || 0,
                            assets: data.profile_data.assets || 0
                        });

                        // Dispatch event to update modal (Alpine doesn't track deep object changes)
                        window.dispatchEvent(new CustomEvent('profile-research-complete', {
                            detail: { profile: this.selectedProfile }
                        }));

                        // Show appropriate notification based on NTEE code availability
                        if (!nteeCode) {
                            this.showNotification?.(
                                `Research complete - NTEE code not found in BMF database`,
                                'warning'
                            );
                        } else {
                            this.showNotification?.(
                                `Research complete for ${data.profile_data.name}`,
                                'success'
                            );
                        }
                    }
                } else {
                    throw new Error(data.error || 'Research failed');
                }
            } catch (error) {
                console.error('Research failed:', error);
                this.showNotification?.(
                    `Research failed: ${error.message}`,
                    'error'
                );
            } finally {
                this.loading = false;
            }
        },

        /**
         * Handle NTEE codes selected event
         */
        handleNTEECodesSelected(event) {
            const { codes } = event.detail;

            if (this.selectedProfile) {
                this.selectedProfile.ntee_codes = codes;
            }
        },

        /**
         * Handle government criteria selected event
         */
        handleGovernmentCriteriaSelected(event) {
            const { criteria } = event.detail;

            if (this.selectedProfile) {
                this.selectedProfile.government_criteria = criteria;
            }
        },

        /**
         * Get NTEE code name from code
         * @param {string} code - e.g., 'F40'
         * @returns {string} - e.g., 'Hot Line, Crisis Intervention'
         */
        getNteeCodeName(code) {
            // This would load from NTEE_CODES data
            // For now, return the code itself
            return code;
        },

        /**
         * Remove NTEE code from profile
         * @param {string} code
         */
        removeNteeCode(code) {
            if (this.selectedProfile && this.selectedProfile.ntee_codes) {
                this.selectedProfile.ntee_codes = this.selectedProfile.ntee_codes.filter(c => c !== code);
            }
        },

        /**
         * Remove government criteria from profile
         * @param {string} criteriaId
         */
        removeGovernmentCriteria(criteriaId) {
            if (this.selectedProfile && this.selectedProfile.government_criteria) {
                this.selectedProfile.government_criteria = this.selectedProfile.government_criteria.filter(
                    c => c.id !== criteriaId
                );
            }
        },

        /**
         * Get CSS class for criteria source badge
         * @param {string} source - 'Federal', 'State', or 'Local'
         * @returns {string} - Tailwind CSS classes
         */
        getCriteriaSourceBadgeClass(source) {
            const badges = {
                'Federal': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
                'State': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
                'Local': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
            };
            return badges[source] || 'bg-gray-100 text-gray-800';
        },

        /**
         * Save profile changes (called from modal)
         */
        async saveProfile() {
            if (!this.selectedProfile) return;

            try {
                await this.updateProfile(this.selectedProfile.profile_id, this.selectedProfile);
                window.dispatchEvent(new CustomEvent('close-edit-profile-modal'));
            } catch (error) {
                console.error('Save profile failed:', error);
            }
        },

        /**
         * Setup event listeners for modals
         */
        setupModalListeners() {
            // Prevent duplicate listener registration
            if (this._listenersSetup) {
                return;
            }
            this._listenersSetup = true;

            // Listen for create profile event
            window.addEventListener('create-profile', (event) => {
                this.handleCreateProfile(event);
            });

            // Listen for delete profile confirmed event
            window.addEventListener('delete-profile-confirmed', (event) => {
                this.handleDeleteProfile(event);
            });

            // Listen for research profile event (Research button)
            window.addEventListener('research-profile', (event) => {
                this.handleResearchProfile(event);
            });

            // Listen for NTEE codes selected event
            window.addEventListener('ntee-codes-selected', (event) => {
                this.handleNTEECodesSelected(event);
            });

            // Listen for government criteria selected event
            window.addEventListener('government-criteria-selected', (event) => {
                this.handleGovernmentCriteriaSelected(event);
            });
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = profilesModule;
}

// CRITICAL: Attach to window for Alpine.js to see it
window.profilesModule = profilesModule;

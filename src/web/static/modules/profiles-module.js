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

        // Modals
        showCreateModal: false,
        showEditModal: false,
        showDeleteModal: false,
        profileToDelete: null,

        // =================================================================
        // LIFECYCLE
        // =================================================================

        /**
         * Initialize profiles module
         */
        async init() {
            console.log('Profiles module initialized');
            await this.loadProfiles();
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

                if (data.success) {
                    this.profiles = data.profiles || [];
                    this.totalProfiles = data.total || this.profiles.length;
                    this.currentPage = currentPage;

                    console.log(`Loaded ${this.profiles.length} profiles (page ${currentPage})`);
                } else {
                    throw new Error(data.error || 'Unknown error');
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
                    console.log('Profile created:', data.profile?.name || data.profile_id);
                    this.showNotification?.('Profile created successfully', 'success');

                    // Reload profiles list
                    await this.loadProfiles();

                    // Select new profile
                    if (data.profile) {
                        this.selectProfile(data.profile);
                    }

                    // Close modal
                    this.showCreateModal = false;

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
                    console.log('Profile updated:', profileId);
                    this.showNotification?.('Profile updated successfully', 'success');

                    // Reload profiles list
                    await this.loadProfiles();

                    // Update selected profile if it's the one being edited
                    if (this.selectedProfile?.profile_id === profileId) {
                        this.selectedProfile = data.profile;
                    }

                    // Close modal
                    this.showEditModal = false;

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
                    console.log('Profile deleted:', profileId);
                    this.showNotification?.('Profile deleted successfully', 'success');

                    // Clear selected profile if it's the one being deleted
                    if (this.selectedProfile?.profile_id === profileId) {
                        this.selectedProfile = null;
                    }

                    // Reload profiles list
                    await this.loadProfiles();

                    // Close modal
                    this.showDeleteModal = false;
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
            console.log('Profile selected:', profile.name);

            // Dispatch event for other modules
            this.$dispatch?.('profile-selected', { profile });
        },

        /**
         * Open create profile modal
         */
        openCreateModal() {
            this.showCreateModal = true;
        },

        /**
         * Open edit profile modal
         * @param {Object} profile
         */
        openEditModal(profile) {
            this.selectedProfile = profile;
            this.showEditModal = true;
        },

        /**
         * Open delete confirmation modal
         * @param {Object} profile
         */
        openDeleteModal(profile) {
            this.profileToDelete = profile;
            this.showDeleteModal = true;
        },

        /**
         * Close all modals
         */
        closeModals() {
            this.showCreateModal = false;
            this.showEditModal = false;
            this.showDeleteModal = false;
            this.profileToDelete = null;
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
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = profilesModule;
}

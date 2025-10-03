/**
 * Shared Utilities Module
 * Common functions used across all modules
 *
 * Provides: dark mode, notifications, formatting, validation
 */

function sharedModule() {
    return {
        // =================================================================
        // DARK MODE
        // =================================================================

        darkMode: localStorage.getItem('darkMode') === 'true',

        /**
         * Toggle dark mode
         */
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
            localStorage.setItem('darkMode', this.darkMode);
            console.log('Dark mode:', this.darkMode ? 'enabled' : 'disabled');
        },

        /**
         * Initialize dark mode from localStorage
         */
        initDarkMode() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            }
        },

        // =================================================================
        // NOTIFICATIONS
        // =================================================================

        notifications: [],

        /**
         * Show notification toast
         * @param {string} message
         * @param {string} type - success, error, warning, info
         * @param {number} duration - milliseconds
         */
        showNotification(message, type = 'info', duration = 5000) {
            const notification = {
                id: Date.now(),
                message,
                type,
                visible: true
            };

            this.notifications.push(notification);

            // Auto-dismiss
            if (duration > 0) {
                setTimeout(() => {
                    this.dismissNotification(notification.id);
                }, duration);
            }

            console.log(`[${type.toUpperCase()}]`, message);
            return notification;
        },

        /**
         * Dismiss notification by ID
         * @param {number} id
         */
        dismissNotification(id) {
            const index = this.notifications.findIndex(n => n.id === id);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        },

        // =================================================================
        // FORMATTING
        // =================================================================

        /**
         * Format number as currency
         * @param {number} amount
         * @returns {string}
         */
        formatCurrency(amount) {
            if (!amount && amount !== 0) return 'N/A';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        },

        /**
         * Format date
         * @param {string|Date} date
         * @returns {string}
         */
        formatDate(date) {
            if (!date) return 'N/A';
            return new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        },

        /**
         * Format datetime
         * @param {string|Date} datetime
         * @returns {string}
         */
        formatDateTime(datetime) {
            if (!datetime) return 'N/A';
            return new Date(datetime).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        /**
         * Format number with commas
         * @param {number} num
         * @returns {string}
         */
        formatNumber(num) {
            if (!num && num !== 0) return 'N/A';
            return new Intl.NumberFormat('en-US').format(num);
        },

        /**
         * Format percentage
         * @param {number} value - 0 to 1
         * @param {number} decimals
         * @returns {string}
         */
        formatPercent(value, decimals = 0) {
            if (!value && value !== 0) return 'N/A';
            return (value * 100).toFixed(decimals) + '%';
        },

        /**
         * Format EIN with dash
         * @param {string} ein
         * @returns {string}
         */
        formatEIN(ein) {
            if (!ein) return 'N/A';
            // Add dash if missing: 123456789 → 12-3456789
            if (ein.length === 9 && !ein.includes('-')) {
                return `${ein.slice(0, 2)}-${ein.slice(2)}`;
            }
            return ein;
        },

        // =================================================================
        // VALIDATION
        // =================================================================

        /**
         * Validate EIN format
         * @param {string} ein
         * @returns {boolean}
         */
        validateEIN(ein) {
            if (!ein) return false;
            // Accept both formats: 12-3456789 or 123456789
            return /^\d{2}-?\d{7}$/.test(ein);
        },

        /**
         * Validate email
         * @param {string} email
         * @returns {boolean}
         */
        validateEmail(email) {
            if (!email) return false;
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },

        /**
         * Validate URL
         * @param {string} url
         * @returns {boolean}
         */
        validateURL(url) {
            if (!url) return false;
            try {
                new URL(url);
                return true;
            } catch {
                return false;
            }
        },

        // =================================================================
        // UTILITIES
        // =================================================================

        /**
         * Copy text to clipboard
         * @param {string} text
         */
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showNotification('Copied to clipboard', 'success', 2000);
                return true;
            } catch (error) {
                console.error('Copy failed:', error);
                this.showNotification('Failed to copy', 'error', 2000);
                return false;
            }
        },

        /**
         * Download data as file
         * @param {string} data
         * @param {string} filename
         * @param {string} mimeType
         */
        downloadFile(data, filename, mimeType = 'text/plain') {
            const blob = new Blob([data], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
            URL.revokeObjectURL(url);

            this.showNotification(`Downloaded ${filename}`, 'success', 2000);
        },

        /**
         * Debounce function calls
         * @param {Function} func
         * @param {number} wait
         * @returns {Function}
         */
        debounce(func, wait = 300) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Deep clone object
         * @param {Object} obj
         * @returns {Object}
         */
        deepClone(obj) {
            return JSON.parse(JSON.stringify(obj));
        },

        /**
         * Generate unique ID
         * @returns {string}
         */
        generateId() {
            return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = sharedModule;
}

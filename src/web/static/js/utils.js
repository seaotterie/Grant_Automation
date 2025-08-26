// Catalynx Utility Functions
// Shared utility functions extracted from monolithic app.js

const CatalynxUtils = {
    formatStageWithNumber(stage) {
        const stageMapping = {
            // New pipeline stage mapping
            'discovery': '#1 Prospect',
            'pre_scoring': '#2 Qualified',
            'deep_analysis': '#3 Candidate',
            'recommendations': '#4 Target',
            // Legacy support for old stages
            'prospects': '#1 Prospect',
            'qualified_prospects': '#2 Qualified',
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
            // Legacy support for old stages
            'prospects': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
            'qualified_prospects': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            'candidates': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            'targets': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            'opportunities': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
        };
        return colorMapping[stage] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    },
    
    getActualStage(prospect) {
        // Priority: pipeline_stage > funnel_stage > stage > default
        return prospect.pipeline_stage || prospect.funnel_stage || prospect.stage || 'discovery';
    },
    
    getOrganizationTypeColor(type) {
        // All organization types use blue background with white text for consistency and visibility  
        console.log('getOrganizationTypeColor called with type:', type);
        // Using more specific/important classes to override any conflicts
        const classes = '!bg-blue-600 !text-white dark:!bg-blue-700 dark:!text-white !font-medium';
        console.log('Returning classes:', classes);
        return classes;
    },
    
    formatCurrency(amount) {
        if (amount === null || amount === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    },
    
    formatNumber(number) {
        if (number === null || number === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US').format(number);
    },
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return dateString;
        }
    },
    
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    },
    
    truncateText(text, maxLength = 100) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },
    
    throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, duration);
    },
    
    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification('Copied to clipboard!', 'success');
            }).catch(() => {
                this.fallbackCopyToClipboard(text);
            });
        } else {
            this.fallbackCopyToClipboard(text);
        }
    },
    
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            this.showNotification('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    },
    
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    validateRequired(value) {
        return value !== null && value !== undefined && value !== '';
    },
    
    sanitizeHtml(html) {
        const temp = document.createElement('div');
        temp.textContent = html;
        return temp.innerHTML;
    },
    
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    },
    
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        
        const cloned = {};
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = this.deepClone(obj[key]);
            }
        }
        return cloned;
    }
};

// Make utils available globally
window.CatalynxUtils = CatalynxUtils;
// Enhanced Error Handling System
// Extracted from app.js for better modularity
// Handles user-friendly error notifications, retry logic, and fallback UI

const ErrorHandler = {
    // Error display state
    currentError: null,
    retryAttempts: new Map(),
    maxRetryAttempts: 3,

    // Show user-friendly error notification
    showError(error, context = {}) {
        console.error('Error:', error, context);

        // Parse error response if available
        const errorInfo = this.parseErrorResponse(error);

        // Show toast notification
        this.showToast({
            type: 'error',
            title: errorInfo.title,
            message: errorInfo.message,
            actions: errorInfo.actions,
            context: context
        });

        // Store current error for retry functionality
        this.currentError = { error, context, errorInfo };

        return errorInfo;
    },

    // Parse standardized error responses
    parseErrorResponse(error) {
        // Default error info
        let errorInfo = {
            title: 'Error Occurred',
            message: 'An unexpected error occurred. Please try again.',
            actions: ['retry'],
            canRetry: true,
            severity: 'medium'
        };

        try {
            // Handle fetch response errors
            if (error.response) {
                const data = error.response.data || error.response;

                if (data.error_type) {
                    // Standardized error response
                    errorInfo.title = data.message || errorInfo.title;
                    errorInfo.message = data.recovery_guidance?.suggested_actions?.[0] || errorInfo.message;
                    errorInfo.canRetry = data.recovery_guidance?.retry_allowed || false;
                    errorInfo.actions = this.getActionsFromRecovery(data.recovery_guidance);
                } else if (data.detail) {
                    // FastAPI HTTPException
                    errorInfo.title = 'Request Failed';
                    errorInfo.message = data.detail;
                }

                // Set severity based on status code
                if (error.response.status >= 500) {
                    errorInfo.severity = 'high';
                } else if (error.response.status >= 400) {
                    errorInfo.severity = 'medium';
                }

            } else if (error.message) {
                // JavaScript error
                if (error.message.includes('network') || error.message.includes('fetch')) {
                    errorInfo.title = 'Network Error';
                    errorInfo.message = 'Check your internet connection and try again.';
                } else if (error.message.includes('timeout')) {
                    errorInfo.title = 'Request Timeout';
                    errorInfo.message = 'The request took too long. Please try again.';
                } else {
                    errorInfo.message = error.message;
                }
            }

        } catch (parseError) {
            console.warn('Error parsing error response:', parseError);
        }

        return errorInfo;
    },

    // Get user actions from recovery guidance
    getActionsFromRecovery(guidance) {
        const actions = ['dismiss'];

        if (guidance?.retry_allowed) {
            actions.unshift('retry');
        }

        if (guidance?.documentation_link) {
            actions.push('help');
        }

        return actions;
    },

    // Show toast notification
    showToast({ type = 'info', title, message, actions = ['dismiss'], duration = 5000, context = {} }) {
        const toast = {
            id: Date.now(),
            type,
            title,
            message,
            actions,
            context,
            timestamp: new Date(),
            visible: true
        };

        // Add to Alpine.js toast system
        if (window.alpine && window.alpine.store && window.alpine.store('toasts')) {
            window.alpine.store('toasts').add(toast);
        } else {
            // Fallback to console and browser notification
            console.log(`${type.toUpperCase()}: ${title} - ${message}`);
            this.showFallbackNotification(toast);
        }

        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                this.dismissToast(toast.id);
            }, duration);
        }

        return toast;
    },

    // Fallback notification for when Alpine.js isn't available
    showFallbackNotification(toast) {
        // Create a simple popup
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 max-w-sm p-4 rounded-lg shadow-lg z-50 ${
            toast.type === 'error' ? 'bg-red-100 border-red-400 text-red-700' :
            toast.type === 'warning' ? 'bg-yellow-100 border-yellow-400 text-yellow-700' :
            toast.type === 'success' ? 'bg-green-100 border-green-400 text-green-700' :
            'bg-blue-100 border-blue-400 text-blue-700'
        }`;

        notification.innerHTML = `
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-semibold">${toast.title}</h4>
                    <p class="text-sm">${toast.message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    },

    // Dismiss toast notification
    dismissToast(toastId) {
        if (window.alpine && window.alpine.store && window.alpine.store('toasts')) {
            window.alpine.store('toasts').dismiss(toastId);
        }
    },

    // Retry last failed operation
    async retry(operation = null, context = {}) {
        const error = this.currentError;
        if (!error || !error.errorInfo.canRetry) {
            this.showError(new Error('No retryable operation available'));
            return false;
        }

        const operationKey = operation || `${error.context.operation || 'unknown'}_${error.context.url || 'unknown'}`;
        const attempts = this.retryAttempts.get(operationKey) || 0;

        if (attempts >= this.maxRetryAttempts) {
            this.showError(new Error('Maximum retry attempts exceeded. Please refresh the page or contact support.'));
            return false;
        }

        // Increment retry counter
        this.retryAttempts.set(operationKey, attempts + 1);

        // Show retry notification
        this.showToast({
            type: 'info',
            title: 'Retrying Operation',
            message: `Attempt ${attempts + 1} of ${this.maxRetryAttempts}...`,
            duration: 2000
        });

        try {
            // If a specific retry function is provided, use it
            if (context.retryFunction && typeof context.retryFunction === 'function') {
                await context.retryFunction();
            } else {
                // Generic retry - re-execute the failed operation
                console.log('Generic retry not implemented yet - please refresh the page');
                return false;
            }

            // Success - clear retry counter
            this.retryAttempts.delete(operationKey);
            this.showToast({
                type: 'success',
                title: 'Operation Succeeded',
                message: 'The operation completed successfully.',
                duration: 3000
            });

            return true;

        } catch (retryError) {
            console.error('Retry failed:', retryError);
            this.showError(retryError, { ...context, isRetry: true });
            return false;
        }
    },

    // Wrap fetch requests with error handling
    async safeFetch(url, options = {}) {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            // Check if response is ok
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

            return response;

        } catch (error) {
            // Add context to error
            error.context = {
                url,
                method: options.method || 'GET',
                requestId,
                timestamp: new Date().toISOString()
            };

            throw error;
        }
    },

    // Handle API responses with error checking
    async handleApiResponse(responsePromise, context = {}) {
        try {
            const response = await responsePromise;
            return response;
        } catch (error) {
            const errorInfo = this.showError(error, context);

            // Determine if we should throw or return null
            if (errorInfo.severity === 'high' || context.throwOnError) {
                throw error;
            }

            return null;
        }
    }
};

// Make ErrorHandler available globally
window.ErrorHandler = ErrorHandler;

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
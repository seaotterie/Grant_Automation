/**
 * Modal Component Module
 * Reusable modal system with Alpine.js integration
 *
 * Features:
 * - Alpine.js x-show/x-transition integration
 * - Keyboard shortcuts (ESC to close)
 * - Backdrop click to close
 * - Focus management
 * - Stacked modals support
 */

function modalComponent() {
    return {
        // =================================================================
        // STATE
        // =================================================================

        // Active modals (supports stacking)
        activeModals: [],

        // Modal z-index management
        baseZIndex: 50,

        // =================================================================
        // CORE MODAL OPERATIONS
        // =================================================================

        /**
         * Open a modal
         * @param {string} modalId - Unique modal identifier
         * @param {object} data - Optional data to pass to modal
         */
        openModal(modalId, data = null) {
            // Check if already open
            if (this.isModalOpen(modalId)) {
                console.warn(`Modal ${modalId} is already open`);
                return;
            }

            // Add to active modals stack
            this.activeModals.push({
                id: modalId,
                data: data,
                zIndex: this.baseZIndex + this.activeModals.length
            });

            // Prevent body scroll
            this.preventBodyScroll();

            // Setup keyboard listener
            this.setupKeyboardListener();

            // Dispatch open event
            this.$dispatch('modal-opened', { modalId, data });

            console.log(`Modal opened: ${modalId}`);
        },

        /**
         * Close a modal
         * @param {string} modalId - Modal to close (defaults to topmost)
         */
        closeModal(modalId = null) {
            // If no modalId specified, close topmost modal
            if (!modalId && this.activeModals.length > 0) {
                modalId = this.activeModals[this.activeModals.length - 1].id;
            }

            // Remove from stack
            const index = this.activeModals.findIndex(m => m.id === modalId);
            if (index > -1) {
                const modal = this.activeModals.splice(index, 1)[0];

                // Restore body scroll if no modals left
                if (this.activeModals.length === 0) {
                    this.restoreBodyScroll();
                }

                // Dispatch close event
                this.$dispatch('modal-closed', { modalId: modal.id });

                console.log(`Modal closed: ${modalId}`);
            }
        },

        /**
         * Close all modals
         */
        closeAllModals() {
            while (this.activeModals.length > 0) {
                this.closeModal();
            }
        },

        /**
         * Check if modal is open
         * @param {string} modalId
         * @returns {boolean}
         */
        isModalOpen(modalId) {
            return this.activeModals.some(m => m.id === modalId);
        },

        /**
         * Get modal data
         * @param {string} modalId
         * @returns {object|null}
         */
        getModalData(modalId) {
            const modal = this.activeModals.find(m => m.id === modalId);
            return modal ? modal.data : null;
        },

        /**
         * Get modal z-index
         * @param {string} modalId
         * @returns {number}
         */
        getModalZIndex(modalId) {
            const modal = this.activeModals.find(m => m.id === modalId);
            return modal ? modal.zIndex : this.baseZIndex;
        },

        // =================================================================
        // KEYBOARD HANDLING
        // =================================================================

        keyboardListener: null,

        /**
         * Setup keyboard event listener
         */
        setupKeyboardListener() {
            if (this.keyboardListener) return;

            this.keyboardListener = (e) => {
                // ESC key closes topmost modal
                if (e.key === 'Escape' && this.activeModals.length > 0) {
                    e.preventDefault();
                    this.closeModal();
                }
            };

            document.addEventListener('keydown', this.keyboardListener);
        },

        /**
         * Remove keyboard event listener
         */
        removeKeyboardListener() {
            if (this.keyboardListener) {
                document.removeEventListener('keydown', this.keyboardListener);
                this.keyboardListener = null;
            }
        },

        // =================================================================
        // SCROLL MANAGEMENT
        // =================================================================

        bodyScrollPosition: 0,

        /**
         * Prevent body scroll when modal is open
         */
        preventBodyScroll() {
            if (this.activeModals.length === 1) {
                // Only on first modal
                this.bodyScrollPosition = window.pageYOffset;
                document.body.style.overflow = 'hidden';
                document.body.style.position = 'fixed';
                document.body.style.top = `-${this.bodyScrollPosition}px`;
                document.body.style.width = '100%';
            }
        },

        /**
         * Restore body scroll when all modals closed
         */
        restoreBodyScroll() {
            document.body.style.removeProperty('overflow');
            document.body.style.removeProperty('position');
            document.body.style.removeProperty('top');
            document.body.style.removeProperty('width');
            window.scrollTo(0, this.bodyScrollPosition);

            // Remove keyboard listener
            this.removeKeyboardListener();
        },

        // =================================================================
        // BACKDROP HANDLING
        // =================================================================

        /**
         * Handle backdrop click
         * @param {string} modalId
         */
        handleBackdropClick(modalId) {
            // Close modal when clicking backdrop
            this.closeModal(modalId);
        },

        /**
         * Prevent modal content clicks from closing
         * @param {Event} event
         */
        handleModalClick(event) {
            event.stopPropagation();
        },

        // =================================================================
        // FOCUS MANAGEMENT
        // =================================================================

        /**
         * Focus first input in modal
         * @param {string} modalId
         */
        focusFirstInput(modalId) {
            this.$nextTick(() => {
                const modalElement = document.querySelector(`[data-modal="${modalId}"]`);
                if (modalElement) {
                    const firstInput = modalElement.querySelector('input, textarea, select, button');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }
            });
        },

        // =================================================================
        // UTILITY METHODS
        // =================================================================

        /**
         * Initialize modal system
         */
        init() {
            console.log('Modal component initialized');

            // Listen for global modal events
            this.$watch('activeModals', (value) => {
                console.log(`Active modals: ${value.length}`);
            });
        },

        /**
         * Cleanup on destroy
         */
        destroy() {
            this.closeAllModals();
            this.removeKeyboardListener();
            console.log('Modal component destroyed');
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { modalComponent };
}

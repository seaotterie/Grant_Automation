/**
 * Modal Loader - Dynamically load modal templates
 * This file loads all modal HTML templates into the DOM
 *
 * Usage: Include this script after Alpine.js initialization
 */

(function() {
    'use strict';

    console.log('Modal Loader: Initializing...');

    /**
     * Load modal templates into DOM
     */
    async function loadModalTemplates() {
        const modalContainer = document.createElement('div');
        modalContainer.id = 'modal-templates-container';

        try {
            // Load all modal templates
            const templates = [
                '/static/templates/profile-modals.html',
                '/static/templates/ntee-selection-modal.html',
                '/static/templates/government-criteria-modal.html',
                '/static/templates/create-delete-modals.html'
            ];

            for (const templateUrl of templates) {
                try {
                    const response = await fetch(templateUrl);
                    if (response.ok) {
                        const html = await response.text();
                        modalContainer.innerHTML += html;
                        console.log(`Modal Loader: Loaded ${templateUrl}`);
                    } else {
                        console.warn(`Modal Loader: Failed to load ${templateUrl} - ${response.status}`);
                    }
                } catch (error) {
                    console.error(`Modal Loader: Error loading ${templateUrl}:`, error);
                }
            }

            // Append to body
            document.body.appendChild(modalContainer);
            console.log('Modal Loader: All templates loaded successfully');

            // Dispatch event to signal modals are ready
            window.dispatchEvent(new CustomEvent('modals-loaded'));

        } catch (error) {
            console.error('Modal Loader: Fatal error:', error);
        }
    }

    /**
     * Initialize when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadModalTemplates);
    } else {
        loadModalTemplates();
    }

})();

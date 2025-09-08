// Catalynx Module Loader
// Dynamic module loading system for architecture migration

class CatalynxModuleLoader {
    constructor(config = null) {
        this.config = config || window.CatalynxConfig;
        this.loadedModules = new Map();
        this.loadPromises = new Map();
        this.loadOrder = [
            'utils',
            'api/client',
            'modules/websocket',
            'modules/charts', 
            'modules/pagination',
            'modules/profile-management',
            'modules/discovery-engine'
        ];
        
        // Module registry for checking availability
        this.moduleRegistry = {
            'utils': 'CatalynxUtils',
            'api/client': 'CatalynxAPI',
            'modules/websocket': 'CatalynxWebSocket',
            'modules/charts': 'CatalynxCharts',
            'modules/pagination': 'CatalynxPagination', 
            'modules/profile-management': 'CatalynxProfileManager',
            'modules/discovery-engine': 'CatalynxDiscoveryEngine'
        };
        
        this.startTime = performance.now();
    }
    
    /**
     * Initialize module loading based on configuration
     */
    async initialize() {
        const mode = this.config.getArchitectureMode();
        
        console.log(`🚀 Initializing Catalynx - Architecture Mode: ${mode}`);
        
        switch (mode) {
            case 'modular':
                return await this.loadModularArchitecture();
                
            case 'hybrid':
                return await this.loadHybridArchitecture();
                
            case 'monolithic':
            default:
                return await this.loadMonolithicArchitecture();
        }
    }
    
    /**
     * Load full modular architecture
     */
    async loadModularArchitecture() {
        try {
            console.log('📦 Loading modular architecture...');
            
            // Load all modules
            const results = await this.loadModules(this.loadOrder);
            
            // Verify all modules loaded
            const failed = results.filter(r => !r.success);
            if (failed.length > 0 && !this.config.get('architecture.fallback_to_monolithic')) {
                throw new Error(`Failed to load modules: ${failed.map(f => f.module).join(', ')}`);
            }
            
            // Initialize modular app
            await this.initializeModularApp();
            
            const loadTime = performance.now() - this.startTime;
            console.log(`✅ Modular architecture loaded successfully in ${loadTime.toFixed(2)}ms`);
            
            return {
                success: true,
                mode: 'modular',
                modules: results,
                loadTime
            };
            
        } catch (error) {
            console.error('❌ Modular architecture failed:', error);
            
            if (this.config.get('architecture.fallback_to_monolithic')) {
                console.log('🔄 Falling back to monolithic architecture...');
                return await this.loadMonolithicArchitecture();
            }
            
            throw error;
        }
    }
    
    /**
     * Load hybrid architecture (selective modular components)
     */
    async loadHybridArchitecture() {
        try {
            console.log('🔀 Loading hybrid architecture...');
            
            // Load only enabled modular components
            const enabledComponents = this.config.get('architecture.enable_modular_components') || [];
            const modulesToLoad = this.loadOrder.filter(module => {
                const componentName = this.getComponentName(module);
                return enabledComponents.includes(componentName) || 
                       ['utils', 'api/client'].includes(componentName); // Always load core
            });
            
            console.log('📦 Loading modules:', modulesToLoad);
            
            const results = await this.loadModules(modulesToLoad);
            
            // Initialize hybrid app
            await this.initializeHybridApp(enabledComponents);
            
            const loadTime = performance.now() - this.startTime;
            console.log(`✅ Hybrid architecture loaded successfully in ${loadTime.toFixed(2)}ms`);
            
            return {
                success: true,
                mode: 'hybrid',
                modules: results,
                enabledComponents,
                loadTime
            };
            
        } catch (error) {
            console.error('❌ Hybrid architecture failed:', error);
            
            if (this.config.get('architecture.fallback_to_monolithic')) {
                console.log('🔄 Falling back to monolithic architecture...');
                return await this.loadMonolithicArchitecture();
            }
            
            throw error;
        }
    }
    
    /**
     * Load traditional monolithic architecture
     */
    async loadMonolithicArchitecture() {
        try {
            console.log('📋 Loading monolithic architecture...');
            
            // The monolithic app.js is already loaded via script tag
            // Just verify it's available
            if (typeof window.catalynxApp !== 'function') {
                throw new Error('Monolithic catalynxApp function not available');
            }
            
            const loadTime = performance.now() - this.startTime;
            console.log(`✅ Monolithic architecture ready in ${loadTime.toFixed(2)}ms`);
            
            return {
                success: true,
                mode: 'monolithic',
                loadTime
            };
            
        } catch (error) {
            console.error('❌ Monolithic architecture failed:', error);
            throw error;
        }
    }
    
    /**
     * Load multiple modules
     */
    async loadModules(moduleList) {
        const results = [];
        
        for (const module of moduleList) {
            try {
                const result = await this.loadModule(module);
                results.push(result);
            } catch (error) {
                results.push({
                    success: false,
                    module,
                    error: error.message
                });
            }
        }
        
        return results;
    }
    
    /**
     * Load single module
     */
    async loadModule(modulePath) {
        // Check if already loaded
        if (this.loadedModules.has(modulePath)) {
            return this.loadedModules.get(modulePath);
        }
        
        // Check if already loading
        if (this.loadPromises.has(modulePath)) {
            return await this.loadPromises.get(modulePath);
        }
        
        const loadPromise = this._loadModuleScript(modulePath);
        this.loadPromises.set(modulePath, loadPromise);
        
        try {
            const result = await loadPromise;
            this.loadedModules.set(modulePath, result);
            this.loadPromises.delete(modulePath);
            return result;
        } catch (error) {
            this.loadPromises.delete(modulePath);
            throw error;
        }
    }
    
    /**
     * Actually load module script
     */
    _loadModuleScript(modulePath) {
        return new Promise((resolve, reject) => {
            const globalName = this.moduleRegistry[modulePath];
            
            // Check if module is already available globally
            if (globalName && window[globalName]) {
                resolve({
                    success: true,
                    module: modulePath,
                    globalName,
                    cached: true
                });
                return;
            }
            
            const script = document.createElement('script');
            const startTime = performance.now();
            
            script.onload = () => {
                const loadTime = performance.now() - startTime;
                
                // Verify module loaded correctly
                if (globalName && !window[globalName]) {
                    reject(new Error(`Module ${modulePath} loaded but ${globalName} not found`));
                    return;
                }
                
                if (this.config.get('development.module_load_timing')) {
                    console.log(`📦 Module ${modulePath} loaded in ${loadTime.toFixed(2)}ms`);
                }
                
                resolve({
                    success: true,
                    module: modulePath,
                    globalName,
                    loadTime,
                    cached: false
                });
            };
            
            script.onerror = () => {
                reject(new Error(`Failed to load module: ${modulePath}`));
            };
            
            script.src = `/static/js/${modulePath}.js`;
            document.head.appendChild(script);
        });
    }
    
    /**
     * Initialize modular app
     */
    async initializeModularApp() {
        // Load modular app if not already loaded
        if (!window.catalynxApp) {
            await this.loadModule('app_modular');
        }
        
        // Initialize Alpine.js with modular data
        if (window.Alpine && window.catalynxApp) {
            window.Alpine.data('catalynxApp', window.catalynxApp);
        }
    }
    
    /**
     * Initialize hybrid app
     */
    async initializeHybridApp(enabledComponents) {
        // Enhance existing monolithic app with modular components
        if (typeof window.catalynxApp === 'function' && enabledComponents.includes('pagination')) {
            // Replace monolithic pagination with modular version
            this.injectModularPagination();
        }
        
        // Add other hybrid enhancements as needed
    }
    
    /**
     * Inject modular pagination into monolithic app
     */
    injectModularPagination() {
        if (!window.CatalynxPagination) return;
        
        console.log('🔀 Injecting modular pagination into monolithic app...');
        
        // Store reference to original catalynxApp
        const originalCatalynxApp = window.catalynxApp;
        
        // Create enhanced version
        window.catalynxApp = function() {
            const appData = originalCatalynxApp();
            const pagination = new window.CatalynxPagination();
            
            // Replace pagination methods with modular versions
            appData.getPaginatedData = function(data) {
                return pagination.getPaginatedData(data, {
                    currentPage: this.currentPage,
                    itemsPerPage: this.itemsPerPage,
                    sortColumn: this.sortColumn,
                    sortDirection: this.sortDirection
                });
            };
            
            appData.getTotalPages = function(data) {
                return pagination.getTotalPages(data, this.itemsPerPage);
            };
            
            appData.sortTable = function(column) {
                const newState = pagination.sortTable({
                    currentPage: this.currentPage,
                    itemsPerPage: this.itemsPerPage,
                    sortColumn: this.sortColumn,
                    sortDirection: this.sortDirection
                }, column);
                
                this.currentPage = newState.currentPage;
                this.sortColumn = newState.sortColumn;
                this.sortDirection = newState.sortDirection;
            };
            
            // Add other pagination methods
            appData.nextPage = function(data) {
                const newState = pagination.nextPage({
                    currentPage: this.currentPage,
                    itemsPerPage: this.itemsPerPage,
                    sortColumn: this.sortColumn,
                    sortDirection: this.sortDirection
                }, data);
                this.currentPage = newState.currentPage;
            };
            
            appData.prevPage = function() {
                const newState = pagination.prevPage({
                    currentPage: this.currentPage,
                    itemsPerPage: this.itemsPerPage,
                    sortColumn: this.sortColumn,
                    sortDirection: this.sortDirection
                });
                this.currentPage = newState.currentPage;
            };
            
            appData.goToPage = function(page) {
                const totalPages = this.getTotalPages();
                const newState = pagination.goToPage({
                    currentPage: this.currentPage,
                    itemsPerPage: this.itemsPerPage,
                    sortColumn: this.sortColumn,
                    sortDirection: this.sortDirection
                }, page, totalPages);
                this.currentPage = newState.currentPage;
            };
            
            return appData;
        };
        
        console.log('✅ Modular pagination injected successfully');
    }
    
    /**
     * Get component name from module path
     */
    getComponentName(modulePath) {
        const parts = modulePath.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace('.js', '').replace('-', '_');
    }
    
    /**
     * Check if all required modules are loaded
     */
    areModulesLoaded(moduleList) {
        return moduleList.every(module => {
            const globalName = this.moduleRegistry[module];
            return globalName && window[globalName];
        });
    }
    
    /**
     * Get loading status
     */
    getLoadingStatus() {
        const status = {
            mode: this.config.getArchitectureMode(),
            loaded: Array.from(this.loadedModules.keys()),
            loading: Array.from(this.loadPromises.keys()),
            failed: []
        };
        
        // Check for failed modules
        this.loadedModules.forEach((result, module) => {
            if (!result.success) {
                status.failed.push(module);
            }
        });
        
        return status;
    }
}

// Make available globally
window.CatalynxModuleLoader = CatalynxModuleLoader;

console.log('✅ CatalynxModuleLoader loaded');
// Catalynx Configuration Management
// Feature flags and environment configuration for architecture migration

class CatalynxConfig {
    constructor() {
        // Default configuration
        this.defaultConfig = {
            // Architecture settings
            architecture: {
                mode: 'monolithic', // 'monolithic', 'modular', 'hybrid'
                enable_modular_components: [],
                fallback_to_monolithic: true
            },
            
            // Feature flags
            features: {
                modular_pagination: false,
                modular_profiles: false,
                modular_discovery: false,
                modular_charts: false,
                real_time_updates: true,
                debug_mode: false,
                performance_monitoring: true
            },
            
            // Performance settings
            performance: {
                lazy_load_modules: true,
                enable_service_worker: false,
                cache_ttl_seconds: 3600
            },
            
            // Development settings
            development: {
                verbose_logging: false,
                module_load_timing: false,
                error_boundaries: true
            }
        };
        
        // Load configuration from localStorage or use defaults
        this.config = this.loadConfiguration();
    }
    
    /**
     * Load configuration from localStorage with fallback to defaults
     */
    loadConfiguration() {
        try {
            const stored = localStorage.getItem('catalynx_config');
            if (stored) {
                const parsed = JSON.parse(stored);
                return this.mergeDeep(this.defaultConfig, parsed);
            }
        } catch (error) {
            console.warn('Failed to load stored configuration, using defaults:', error);
        }
        
        return { ...this.defaultConfig };
    }
    
    /**
     * Save configuration to localStorage
     */
    saveConfiguration() {
        try {
            localStorage.setItem('catalynx_config', JSON.stringify(this.config));
            return true;
        } catch (error) {
            console.error('Failed to save configuration:', error);
            return false;
        }
    }
    
    /**
     * Get configuration value by path
     */
    get(path) {
        return path.split('.').reduce((obj, key) => obj && obj[key], this.config);
    }
    
    /**
     * Set configuration value by path
     */
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, key) => {
            if (!obj[key]) obj[key] = {};
            return obj[key];
        }, this.config);
        
        target[lastKey] = value;
        this.saveConfiguration();
        
        // Emit configuration change event
        this.emitConfigChange(path, value);
    }
    
    /**
     * Check if feature is enabled
     */
    isEnabled(featureName) {
        return this.get(`features.${featureName}`) === true;
    }
    
    /**
     * Enable feature
     */
    enableFeature(featureName) {
        this.set(`features.${featureName}`, true);
    }
    
    /**
     * Disable feature
     */
    disableFeature(featureName) {
        this.set(`features.${featureName}`, false);
    }
    
    /**
     * Get current architecture mode
     */
    getArchitectureMode() {
        return this.get('architecture.mode');
    }
    
    /**
     * Set architecture mode
     */
    setArchitectureMode(mode) {
        if (!['monolithic', 'modular', 'hybrid'].includes(mode)) {
            throw new Error('Invalid architecture mode. Must be: monolithic, modular, or hybrid');
        }
        
        this.set('architecture.mode', mode);
    }
    
    /**
     * Check if modular component is enabled
     */
    isModularComponentEnabled(componentName) {
        const enabledComponents = this.get('architecture.enable_modular_components') || [];
        return enabledComponents.includes(componentName) || this.getArchitectureMode() === 'modular';
    }
    
    /**
     * Enable modular component
     */
    enableModularComponent(componentName) {
        const enabled = this.get('architecture.enable_modular_components') || [];
        if (!enabled.includes(componentName)) {
            enabled.push(componentName);
            this.set('architecture.enable_modular_components', enabled);
        }
    }
    
    /**
     * Disable modular component
     */
    disableModularComponent(componentName) {
        const enabled = this.get('architecture.enable_modular_components') || [];
        const filtered = enabled.filter(name => name !== componentName);
        this.set('architecture.enable_modular_components', filtered);
    }
    
    /**
     * Get debug configuration
     */
    getDebugConfig() {
        return {
            debug_mode: this.isEnabled('debug_mode'),
            verbose_logging: this.get('development.verbose_logging'),
            module_load_timing: this.get('development.module_load_timing'),
            performance_monitoring: this.isEnabled('performance_monitoring')
        };
    }
    
    /**
     * Reset configuration to defaults
     */
    resetToDefaults() {
        this.config = { ...this.defaultConfig };
        this.saveConfiguration();
        this.emitConfigChange('*', this.config);
    }
    
    /**
     * Get all configuration
     */
    getAll() {
        return { ...this.config };
    }
    
    /**
     * Emit configuration change event
     */
    emitConfigChange(path, value) {
        const event = new CustomEvent('catalynx:config:change', {
            detail: { path, value, config: this.config }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Deep merge objects
     */
    mergeDeep(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target))
                        Object.assign(output, { [key]: source[key] });
                    else
                        output[key] = this.mergeDeep(target[key], source[key]);
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }
    
    /**
     * Check if value is object
     */
    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
    
    /**
     * Create configuration preset
     */
    createPreset(name, config) {
        try {
            const presets = JSON.parse(localStorage.getItem('catalynx_config_presets') || '{}');
            presets[name] = config;
            localStorage.setItem('catalynx_config_presets', JSON.stringify(presets));
            return true;
        } catch (error) {
            console.error('Failed to create preset:', error);
            return false;
        }
    }
    
    /**
     * Load configuration preset
     */
    loadPreset(name) {
        try {
            const presets = JSON.parse(localStorage.getItem('catalynx_config_presets') || '{}');
            if (presets[name]) {
                this.config = this.mergeDeep(this.defaultConfig, presets[name]);
                this.saveConfiguration();
                this.emitConfigChange('*', this.config);
                return true;
            }
        } catch (error) {
            console.error('Failed to load preset:', error);
        }
        return false;
    }
    
    /**
     * Get available presets
     */
    getPresets() {
        try {
            return JSON.parse(localStorage.getItem('catalynx_config_presets') || '{}');
        } catch (error) {
            console.error('Failed to get presets:', error);
            return {};
        }
    }
}

// Create global configuration instance
window.CatalynxConfig = window.CatalynxConfig || new CatalynxConfig();

// Development presets
if (window.CatalynxConfig && typeof window.CatalynxConfig.createPreset === 'function') {
    // Modular development preset
    window.CatalynxConfig.createPreset('modular_dev', {
        architecture: {
            mode: 'modular',
            enable_modular_components: ['pagination', 'profiles', 'discovery', 'charts'],
            fallback_to_monolithic: false
        },
        features: {
            modular_pagination: true,
            modular_profiles: true,
            modular_discovery: true,
            modular_charts: true,
            debug_mode: true
        },
        development: {
            verbose_logging: true,
            module_load_timing: true
        }
    });
    
    // Hybrid testing preset
    window.CatalynxConfig.createPreset('hybrid_test', {
        architecture: {
            mode: 'hybrid',
            enable_modular_components: ['pagination'],
            fallback_to_monolithic: true
        },
        features: {
            modular_pagination: true,
            debug_mode: true,
            performance_monitoring: true
        }
    });
    
    // Production safe preset
    window.CatalynxConfig.createPreset('production_safe', {
        architecture: {
            mode: 'monolithic',
            fallback_to_monolithic: true
        },
        features: {
            debug_mode: false,
            performance_monitoring: true
        },
        development: {
            verbose_logging: false
        }
    });
}

console.log('✅ CatalynxConfig loaded - Current mode:', window.CatalynxConfig.getArchitectureMode());
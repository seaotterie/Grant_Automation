/**
 * Test Configurations for Catalynx Playwright Tests
 * 
 * This file contains:
 * - Test data profiles
 * - Test scenarios
 * - Configuration settings
 * - Mock data for testing
 */

/**
 * Test profiles for different scenarios
 */
const profiles = [
  {
    id: 'heroes_bridge_foundation',
    name: 'Heroes Bridge Foundation Test Profile',
    organization_name: 'Heroes Bridge Foundation',
    mission: 'Supporting veterans and military families through mental health services and community programs',
    focus_areas: ['Veterans Services', 'Mental Health', 'Community Support'],
    geographic_focus: ['Virginia', 'DC', 'Maryland'],
    revenue_range: '$1M-5M',
    funding_types: ['Federal Grants', 'Foundation Grants', 'Individual Donations'],
    ein: '81-2827604',
    website_url: 'https://heroesbridge.org',
    test_data: {
      expected_bmf_data: true,
      expected_990_data: true,
      expected_board_data: true
    }
  },
  {
    id: 'fauquier_foundation',
    name: 'Fauquier Foundation Test Profile',
    organization_name: 'The Fauquier Foundation',
    mission: 'Improving quality of life in Fauquier County through strategic philanthropy',
    focus_areas: ['Community Development', 'Education', 'Health'],
    geographic_focus: ['Fauquier County', 'Virginia'],
    revenue_range: '$500K-1M',
    funding_types: ['Foundation Grants', 'Corporate Sponsorship'],
    ein: '30-0219424',
    website_url: 'https://fauquierfoundation.org',
    test_data: {
      expected_bmf_data: true,
      expected_990_data: true,
      expected_board_data: false
    }
  },
  {
    id: 'test_nonprofit_profile',
    name: 'Generic Test Nonprofit Profile',
    organization_name: 'Test Nonprofit Organization',
    mission: 'Testing and validation of grant research platform functionality',
    focus_areas: ['Testing', 'Quality Assurance', 'Software Development'],
    geographic_focus: ['Virginia', 'National'],
    revenue_range: '$100K-500K',
    funding_types: ['Federal Grants', 'State Grants'],
    ein: '12-3456789',
    website_url: 'https://example-nonprofit.org',
    test_data: {
      expected_bmf_data: false,
      expected_990_data: false,
      expected_board_data: false,
      is_synthetic: true
    }
  },
  // Additional test profiles for comprehensive testing
  {
    id: 'education_foundation_test',
    name: 'Education Foundation E2E Test',
    organization_name: 'Education Foundation E2E',
    mission: 'Supporting educational initiatives and student success programs',
    focus_areas: ['Education', 'Youth Development', 'STEM'],
    geographic_focus: ['Virginia', 'Maryland'],
    revenue_range: '$500K-1M',
    funding_types: ['Federal Grants', 'Foundation Grants'],
    ein: '11-1111111',
    website_url: 'https://education-foundation-test.org',
    contact_email: 'test@education-foundation.org',
    phone_number: '555-0101',
    annual_budget: 750000,
    address: {
      street: '123 Education Lane',
      city: 'Richmond',
      state: 'VA',
      zip_code: '23219',
      country: 'United States'
    },
    test_data: {
      expected_bmf_data: false,
      expected_990_data: false,
      expected_board_data: false,
      is_synthetic: true,
      for_workflow_testing: true
    }
  },
  {
    id: 'healthcare_initiative_test',
    name: 'Healthcare Initiative E2E Test',
    organization_name: 'Healthcare Initiative E2E',
    mission: 'Improving community health outcomes through innovative programs',
    focus_areas: ['Healthcare', 'Community Health', 'Mental Health'],
    geographic_focus: ['Virginia', 'DC'],
    revenue_range: '$1M-5M',
    funding_types: ['Federal Grants', 'State Grants', 'Individual Donations'],
    ein: '22-2222222',
    website_url: 'https://healthcare-initiative-test.org',
    contact_email: 'test@healthcare-initiative.org',
    phone_number: '555-0202',
    annual_budget: 1500000,
    address: {
      street: '456 Health Street',
      city: 'Norfolk',
      state: 'VA',
      zip_code: '23501',
      country: 'United States'
    },
    test_data: {
      expected_bmf_data: false,
      expected_990_data: false,
      expected_board_data: false,
      is_synthetic: true,
      for_workflow_testing: true
    }
  },
  {
    id: 'environmental_action_test',
    name: 'Environmental Action E2E Test',
    organization_name: 'Environmental Action E2E',
    mission: 'Protecting natural resources and promoting environmental sustainability',
    focus_areas: ['Environment', 'Sustainability', 'Conservation'],
    geographic_focus: ['Virginia', 'National'],
    revenue_range: '$250K-500K',
    funding_types: ['Foundation Grants', 'Corporate Sponsorship'],
    ein: '33-3333333',
    website_url: 'https://environmental-action-test.org',
    contact_email: 'test@environmental-action.org',
    phone_number: '555-0303',
    annual_budget: 350000,
    address: {
      street: '789 Green Way',
      city: 'Virginia Beach',
      state: 'VA',
      zip_code: '23451',
      country: 'United States'
    },
    test_data: {
      expected_bmf_data: false,
      expected_990_data: false,
      expected_board_data: false,
      is_synthetic: true,
      for_workflow_testing: true
    }
  }
];

/**
 * Test scenarios for different workflows
 */
const scenarios = {
  tax_data_verification: {
    name: 'Tax Data First Verification System',
    description: 'Verify that real tax data is properly displayed and attributed',
    profiles: ['heroes_bridge_foundation', 'fauquier_foundation'],
    steps: [
      'Navigate to profile creation',
      'Enter organization website URL',
      'Verify EIN extraction',
      'Check Enhanced Data tab',
      'Validate 990 data display',
      'Verify source attribution',
      'Check confidence scoring'
    ],
    expected_outcomes: {
      ein_extracted: true,
      bmf_data_displayed: true,
      source_attribution_visible: true,
      confidence_score_shown: true
    }
  },
  
  complete_discovery_workflow: {
    name: 'Complete Discovery Workflow',
    description: 'End-to-end discovery process from profile to opportunities',
    profiles: ['heroes_bridge_foundation'],
    steps: [
      'Create or select profile',
      'Navigate to Discovery tab',
      'Execute entity-analytics discovery',
      'Review discovery results',
      'Apply filtering and scoring',
      'Move opportunities through stages',
      'Generate reports'
    ],
    expected_outcomes: {
      opportunities_found: true,
      results_filterable: true,
      scoring_applied: true,
      reports_generated: true
    }
  },
  
  intelligence_tiers_validation: {
    name: 'Intelligence Tiers System',
    description: 'Test the 4-tier intelligence system pricing and functionality',
    profiles: ['heroes_bridge_foundation'],
    tiers: [
      {
        name: 'CURRENT',
        price: '$0.75',
        duration: '5-10 min',
        features: ['4-stage AI analysis', 'Strategic recommendations']
      },
      {
        name: 'STANDARD', 
        price: '$7.50',
        duration: '15-20 min',
        features: ['Historical funding analysis', 'Geographic patterns']
      },
      {
        name: 'ENHANCED',
        price: '$22.00', 
        duration: '30-45 min',
        features: ['Document analysis', 'Network intelligence']
      },
      {
        name: 'COMPLETE',
        price: '$42.00',
        duration: '45-60 min', 
        features: ['Policy analysis', 'Strategic consulting']
      }
    ]
  },
  
  performance_validation: {
    name: 'System Performance Validation',
    description: 'Validate system performance metrics and response times',
    metrics: {
      page_load_time: { max: 3000, unit: 'ms' },
      api_response_time: { max: 1000, unit: 'ms' },
      chart_render_time: { max: 500, unit: 'ms' },
      cache_hit_rate: { min: 85, unit: '%' }
    }
  },
  
  visual_regression: {
    name: 'Visual Regression Testing',
    description: 'Ensure UI consistency across updates',
    components: [
      'dashboard_overview',
      'profile_creation_modal',
      'discovery_results_table',
      'enhanced_data_tab',
      'opportunity_cards',
      'chart_visualizations'
    ]
  },

  // New comprehensive testing scenarios
  enhanced_scraping_validation: {
    name: 'Enhanced Scraping Features Testing',
    description: 'Test Scrapy-MCP parallel processing capabilities',
    scraping_strategies: ['parallel', 'adaptive', 'mcp_only', 'scrapy_only'],
    test_urls: [
      'https://httpbin.org/html',
      'https://example.com',
      'https://httpbin.org/json'
    ],
    expected_outcomes: {
      strategy_switching: true,
      progress_monitoring: true,
      data_quality_validation: true,
      performance_comparison: true
    }
  },

  four_tier_intelligence_testing: {
    name: '4-Tier Intelligence System Validation',
    description: 'Comprehensive testing of all business intelligence tiers',
    tiers: [
      {
        name: 'CURRENT',
        price: 0.75,
        duration_minutes: [5, 10],
        features: ['4-stage AI analysis', 'strategic recommendations'],
        processing_type: 'lite'
      },
      {
        name: 'STANDARD',
        price: 7.50,
        duration_minutes: [15, 20],
        features: ['Historical funding analysis', 'geographic patterns', 'temporal trends'],
        processing_type: 'standard'
      },
      {
        name: 'ENHANCED',
        price: 22.00,
        duration_minutes: [30, 45],
        features: ['Document analysis', 'network intelligence', 'decision maker profiles'],
        processing_type: 'enhanced'
      },
      {
        name: 'COMPLETE',
        price: 42.00,
        duration_minutes: [45, 60],
        features: ['Policy analysis', 'real-time monitoring', '26+ page reports', 'strategic consulting'],
        processing_type: 'comprehensive'
      }
    ],
    validation_points: [
      'tier_selection_interface',
      'pricing_display_accuracy',
      'feature_matrix_validation',
      'processing_workflow_execution',
      'output_quality_assessment',
      'cost_tracking_accuracy'
    ]
  },

  end_to_end_workflows: {
    name: 'Complete User Journey Testing',
    description: 'Test complete workflows from start to finish',
    workflows: [
      {
        name: 'complete_grant_research',
        steps: ['profile_creation', 'discovery_execution', 'ai_analysis', 'report_export'],
        expected_duration_minutes: 15,
        success_criteria: ['profile_created', 'opportunities_discovered', 'analysis_completed', 'report_generated']
      },
      {
        name: 'intelligence_enhancement',
        steps: ['basic_profile', 'enhanced_data_collection', 'advanced_analysis', 'results_review'],
        expected_duration_minutes: 20,
        success_criteria: ['data_enhanced', 'analysis_upgraded', 'insights_generated']
      },
      {
        name: 'multi_profile_management',
        steps: ['create_multiple_profiles', 'profile_switching', 'comparison_analysis'],
        expected_duration_minutes: 10,
        success_criteria: ['profiles_created', 'switching_functional', 'comparison_accurate']
      },
      {
        name: 'decision_support',
        steps: ['comprehensive_analysis', 'findings_review', 'strategic_planning', 'implementation'],
        expected_duration_minutes: 25,
        success_criteria: ['analysis_complete', 'decisions_supported', 'plans_generated']
      }
    ]
  },

  error_recovery_scenarios: {
    name: 'Error Recovery and Resilience Testing',
    description: 'Test system recovery from various error conditions',
    error_types: [
      {
        type: 'network_timeout',
        simulation: 'api_delay_15s',
        expected_recovery: 'retry_mechanism',
        max_recovery_time_seconds: 30
      },
      {
        type: 'server_error_500',
        simulation: 'internal_server_error',
        expected_recovery: 'error_display_and_retry',
        max_recovery_time_seconds: 10
      },
      {
        type: 'service_unavailable_503',
        simulation: 'service_temporarily_unavailable',
        expected_recovery: 'retry_after_delay',
        max_recovery_time_seconds: 60
      },
      {
        type: 'client_side_js_error',
        simulation: 'javascript_exception',
        expected_recovery: 'graceful_degradation',
        max_recovery_time_seconds: 5
      },
      {
        type: 'resource_loading_failure',
        simulation: 'css_js_404',
        expected_recovery: 'fallback_resources',
        max_recovery_time_seconds: 15
      }
    ]
  },

  performance_benchmarks: {
    name: 'Performance and Core Web Vitals Testing',
    description: 'Comprehensive performance validation and optimization',
    core_web_vitals: {
      largest_contentful_paint: { good: 2500, needs_improvement: 4000 },
      first_input_delay: { good: 100, needs_improvement: 300 },
      cumulative_layout_shift: { good: 0.1, needs_improvement: 0.25 }
    },
    performance_metrics: {
      page_load_time: { target: 3000, max: 5000, unit: 'ms' },
      tab_switching_time: { target: 300, max: 500, unit: 'ms' },
      api_response_time: { target: 500, max: 1000, unit: 'ms' },
      chart_render_time: { target: 500, max: 1000, unit: 'ms' },
      memory_usage_increase: { target: 50, max: 100, unit: 'MB' }
    },
    accessibility_requirements: {
      wcag_level: '2.1 AA',
      color_contrast_ratio: 4.5,
      keyboard_navigation: true,
      screen_reader_support: true,
      focus_management: true
    }
  },

  cross_browser_compatibility: {
    name: 'Cross-Browser Validation Testing',
    description: 'Ensure consistent functionality across supported browsers',
    browsers: [
      {
        name: 'Chrome',
        version_min: '120',
        features_to_test: ['webgl', 'fetch', 'promises', 'local_storage', 'css_grid'],
        performance_baseline: true
      },
      {
        name: 'Firefox',
        version_min: '120',
        features_to_test: ['webgl', 'fetch', 'promises', 'local_storage', 'css_grid'],
        performance_comparison: true
      }
    ],
    viewport_sizes: [
      { width: 1920, height: 1080, name: 'desktop_1080p' }
    ],
    feature_parity_tests: [
      'basic_navigation',
      'profile_management',
      'discovery_execution',
      'modal_interactions',
      'form_submissions',
      'chart_rendering'
    ]
  },

  modal_state_management: {
    name: 'Modal Dialog State Management Testing',
    description: 'Test modal dialogs, focus management, and state persistence',
    modal_types: [
      {
        name: 'profile_creation',
        trigger: 'create_profile_button',
        required_fields: ['organization_name'],
        optional_fields: ['website_url', 'mission'],
        validation_rules: ['name_required', 'url_format']
      },
      {
        name: 'organization_selection',
        trigger: 'select_organization_button',
        features: ['search', 'filter', 'pagination'],
        interaction_types: ['click', 'keyboard']
      },
      {
        name: 'intelligence_analysis',
        trigger: 'analyze_button',
        features: ['progress_tracking', 'cancellation', 'results_display'],
        long_running: true
      },
      {
        name: 'export_configuration',
        trigger: 'export_button',
        options: ['pdf', 'excel', 'powerpoint'],
        validation_required: ['format_selection']
      }
    ],
    state_management_tests: [
      'modal_open_animation',
      'focus_trap_functionality',
      'data_persistence',
      'error_handling',
      'cross_modal_navigation',
      'session_state_preservation'
    ]
  }
};

/**
 * Mock data for testing
 */
const mockData = {
  system_status: {
    processors_available: 36,
    cache_enabled: true,
    database_connected: true,
    cache_hit_rate: 85.7,
    active_workflows: 3,
    total_processed: 1247,
    success_rate: 94.2
  },
  
  sample_opportunities: [
    {
      organization_name: 'Department of Veterans Affairs',
      title: 'Mental Health Services Grant',
      amount: '$250,000',
      deadline: '2024-12-31',
      eligibility_score: 0.89,
      composite_score: 0.84,
      stage: 'prospects'
    },
    {
      organization_name: 'Virginia Department of Health',
      title: 'Community Health Initiative',
      amount: '$150,000', 
      deadline: '2024-11-15',
      eligibility_score: 0.75,
      composite_score: 0.71,
      stage: 'discovery'
    }
  ],
  
  bmf_data_sample: {
    ein: '81-2827604',
    organization_name: 'Heroes Bridge Foundation',
    ntee_code: 'P20',
    ruling_date: '2012-01-15',
    activity_code: '566',
    classification: '501(c)(3)',
    deductibility: 'Yes',
    foundation_code: '15',
    asset_amount: 1234567,
    income_amount: 987654,
    revenue_amount: 876543
  }
};

/**
 * Test selectors for common UI elements - Updated for comprehensive testing
 */
const selectors = {
  navigation: {
    // Main tab navigation
    overview_tab: 'button:has-text("Overview")',
    discover_tab: 'button:has-text("DISCOVER")',
    plan_tab: 'button:has-text("PLAN")',
    analyze_tab: 'button:has-text("ANALYZE")',
    examine_tab: 'button:has-text("EXAMINE")',
    approach_tab: 'button:has-text("APPROACH")',

    // Sub-navigation for nested components
    sub_tabs: {
      enhanced_data_990: 'button:has-text("990 Data")',
      enhanced_data_schedule_i: 'button:has-text("Schedule-I")',
      enhanced_data_foundation: 'button:has-text("Foundation Intel")',
      discovery_results_government: 'button:has-text("Government")',
      discovery_results_foundation: 'button:has-text("Foundation")',
      discovery_results_corporate: 'button:has-text("Corporate")',
      analysis_current: 'button:has-text("Current")',
      analysis_standard: 'button:has-text("Standard")',
      analysis_enhanced: 'button:has-text("Enhanced")',
      analysis_complete: 'button:has-text("Complete")'
    }
  },

  profile_management: {
    create_profile_button: 'button:has-text("Create Profile")',
    profile_modal: '.fixed.inset-0, [role="dialog"], .modal',
    organization_name_input: 'input[name="organization_name"], input[id="organization_name"], [data-testid="organization_name"]',
    website_url_input: 'input[name="website_url"], input[id="website_url"], [data-testid="website_url"]',
    ein_input: 'input[name="ein"], input[id="ein"], [data-testid="ein"]',
    contact_email_input: 'input[name="contact_email"], input[id="contact_email"], [data-testid="contact_email"]',
    phone_number_input: 'input[name="phone_number"], input[id="phone_number"], [data-testid="phone_number"]',
    annual_budget_input: 'input[name="annual_budget"], input[id="annual_budget"], [data-testid="annual_budget"]',
    mission_textarea: 'textarea[name="mission"], textarea[id="mission"], [data-testid="mission-textarea"]',
    description_textarea: 'textarea[name="description"], textarea[id="description"], [data-testid="description-textarea"]',
    save_profile_button: 'button:has-text("Create Profile"), button:has-text("Save"), button[type="submit"]',
    cancel_profile_button: 'button:has-text("Cancel"), button:has-text("Close")',
    profile_card: '.bg-white.dark\\:bg-gray-800, .border, .rounded-lg, [data-testid="profile-card"]',
    profile_name: '[data-testid="profile-name"], .profile-name',
    profile_id: '[data-testid="profile-id"], .profile-id',
    delete_profile_button: '[data-testid*="delete-profile"], button:has-text("Delete")',
    export_pdf_button: '[data-testid="export-pdf-btn"], button:has-text("Export PDF")',
    export_excel_button: '[data-testid="export-excel-btn"], button:has-text("Export Excel")'
  },

  enhanced_data: {
    enhanced_data_tab: 'button:has-text("Enhanced Data")',
    basic_info_tab: 'button:has-text("Basic Information")',
    ein_display: '[data-testid="ein"], .ein-display, text=/\\d{2}-\\d{7}/',
    organization_name_display: '[data-testid="organization-name"], .organization-name',
    website_url_display: '[data-testid="website-url"], .website-url',
    annual_budget_display: '[data-testid="annual-budget"], .annual-budget',
    bmf_data_section: '[data-testid="bmf-data"], text="BMF", text="Business Master File"',
    source_attribution: '[data-testid="source-attribution"], text="Source", text="IRS", text="990"',
    confidence_score: '[data-testid="confidence-score"], .confidence-score, text=/%/',
    verification_badge: '[data-testid="verification-badge"], .bg-green, .text-green, text="Verified"',
    last_updated: '[data-testid="last-updated"], .last-updated'
  },

  discovery: {
    execute_discovery_button: 'button:has-text("Run All Tracks"), button:has-text("Start"), button:has-text("Discover"), button:has-text("DISCOVER")',
    discovery_progress: '[data-testid="discovery-progress"], text="Discovery in progress", text="Processing", text="Running"',
    discovery_results: '.overflow-x-auto, table, [data-testid="discovery-results"]',
    results_table: 'table, .grid, [data-testid="results-table"]',
    filter_dropdown: 'button:has-text("Filter"), select, [data-testid="filter-dropdown"]',
    pagination_controls: 'button:has-text("Previous"), button:has-text("Next"), button:has-text("1"), [data-testid="pagination"]',
    opportunity_card: '[data-testid="opportunity-card"], .opportunity-card',
    government_filter: 'text="Government", text="Federal", [data-testid="government-filter"]',
    foundation_filter: 'text="Foundation", text="Private", [data-testid="foundation-filter"]',
    enhanced_discovery_button: 'button:has-text("Enhanced"), button:has-text("Deep"), button:has-text("Comprehensive")'
  },

  intelligence: {
    // 4-tier intelligence system selectors
    tier_selection: {
      current_tier: 'text="CURRENT", text="$0.75", button:has-text("CURRENT")',
      standard_tier: 'text="STANDARD", text="$7.50", button:has-text("STANDARD")',
      enhanced_tier: 'text="ENHANCED", text="$22.00", button:has-text("ENHANCED")',
      complete_tier: 'text="COMPLETE", text="$42.00", button:has-text("COMPLETE")'
    },
    processing: {
      lite_button: 'button:has-text("Lite"), button:has-text("Basic")',
      heavy_button: 'button:has-text("Heavy"), button:has-text("Advanced"), button:has-text("Comprehensive")',
      processing_indicator: 'text="Processing", text="Analyzing", text="AI Analysis", text="AI Processing"',
      analysis_stages: 'text="PLAN", text="ANALYZE", text="EXAMINE", text="APPROACH"',
      progress_bar: '[data-testid="progress-bar"], .progress-bar, .w-full'
    },
    results: {
      analysis_complete: 'text="Analysis Complete", text="Results", text="Strategic"',
      recommendations: 'text="Recommendation", text="Strategy", text="Action"',
      strategic_output: 'text="Strategic", text="Implementation", text="Next"'
    }
  },

  export: {
    export_button: 'button:has-text("Export"), button:has-text("Download"), button:has-text("Report")',
    export_modal: '[data-testid="export-modal"], [role="dialog"]:has(text="Export")',
    format_options: {
      pdf: 'text="PDF", option:has-text("PDF"), [data-testid="export-pdf"]',
      excel: 'text="Excel", option:has-text("Excel"), [data-testid="export-excel"]',
      powerpoint: 'text="PowerPoint", option:has-text("PowerPoint"), [data-testid="export-powerpoint"]',
      html: 'text="HTML", option:has-text("HTML"), [data-testid="export-html"]'
    },
    generate_button: 'button:has-text("Generate"), button:has-text("Create Report"), button:has-text("Export")',
    download_button: 'button:has-text("Download"), a:has-text("Download")',
    download_status: 'text="Generated", text="Complete", text="Ready"'
  },

  modals: {
    // General modal selectors
    modal_overlay: '.fixed.inset-0, [role="dialog"], .modal',
    modal_content: '.modal-content, [role="dialog"] > div',
    modal_header: '.modal-header, h1, h2, h3',
    modal_body: '.modal-body, .modal-content > div',
    modal_footer: '.modal-footer, .flex.justify-end',
    close_button: 'button:has-text("×"), button:has-text("Close"), button:has-text("Cancel"), [aria-label="Close"]',

    // Specific modal types
    profile_creation: '[data-testid="profile-modal"], [role="dialog"]:has(text="Create Profile")',
    organization_selection: '[data-testid="organization-modal"], [role="dialog"]:has(text="Organization")',
    intelligence_analysis: '[data-testid="analysis-modal"], [role="dialog"]:has(text="Analysis")',
    export_configuration: '[data-testid="export-modal"], [role="dialog"]:has(text="Export")',
    settings: '[data-testid="settings-modal"], [role="dialog"]:has(text="Settings")',
    confirmation_dialog: '[data-testid="confirm-modal"], [role="dialog"]:has(text="Confirm")'
  },

  charts: {
    // Canvas elements for Chart.js
    system_performance_chart: 'canvas, [data-testid="performance-chart"]',
    scoring_distribution_chart: 'canvas, [data-testid="scoring-chart"]',
    revenue_breakdown_chart: 'canvas, [data-testid="revenue-chart"]',
    chart_container: '.chart-container, [data-testid="chart-container"]',
    chart_legend: '.chart-legend, [data-testid="chart-legend"]'
  },

  scraping: {
    // Enhanced scraping feature selectors
    scraping_strategy_selector: '[data-testid="scraping-strategy"], select:has(option[value="parallel"])',
    strategy_options: {
      parallel: 'option[value="parallel"], text="Parallel"',
      adaptive: 'option[value="adaptive"], text="Adaptive"',
      mcp_only: 'option[value="mcp_only"], text="MCP Only"',
      scrapy_only: 'option[value="scrapy_only"], text="Scrapy Only"'
    },
    progress_monitor: '[data-testid="scraping-progress"], .scraping-progress',
    quality_metrics: '[data-testid="quality-metrics"], .quality-metrics',
    performance_comparison: '[data-testid="performance-comparison"], .performance-comparison'
  },

  accessibility: {
    // ARIA and accessibility selectors
    main_content: 'main, [role="main"], #main',
    navigation: 'nav, [role="navigation"]',
    banner: 'header, [role="banner"]',
    skip_links: 'a[href="#main"], a[href="#content"]',
    live_regions: '[aria-live], [role="status"], [role="alert"]',
    focus_indicators: ':focus, :focus-visible',
    headings: 'h1, h2, h3, h4, h5, h6',
    form_labels: 'label, [aria-label], [aria-labelledby]',
    required_fields: '[required], [aria-required="true"]'
  },

  // Common UI patterns found in the app
  common: {
    loading_spinner: '.opacity-50, text="Loading", text="Processing", [data-testid="loading"]',
    success_notification: '.bg-green, text="Success", text="Complete", [data-testid="success"]',
    error_notification: '.bg-red, text="Error", text="Failed", [data-testid="error"]',
    warning_notification: '.bg-yellow, text="Warning", [data-testid="warning"]',
    info_notification: '.bg-blue, text="Info", [data-testid="info"]',
    modal_close: 'button:has-text("×"), button:has-text("Close"), button:has-text("Cancel")',
    retry_button: 'button:has-text("Retry"), button:has-text("Try Again")',
    refresh_button: 'button:has-text("Refresh"), button:has-text("Reload")',
    save_button: 'button:has-text("Save"), button[type="submit"]',
    cancel_button: 'button:has-text("Cancel"), button[type="button"]',
    confirm_button: 'button:has-text("Confirm"), button:has-text("OK"), button:has-text("Yes")',
    delete_button: 'button:has-text("Delete"), button:has-text("Remove")'
  }
};

/**
 * Test timeouts and delays - Enhanced for comprehensive testing
 */
const timeouts = {
  // Navigation and basic UI
  navigation: 5000,
  page_load: 10000,
  tab_switching: 2000,
  modal_animation: 1000,

  // API and data operations
  api_response: 10000,
  api_timeout_test: 15000,
  discovery_execution: 30000,
  analysis_processing: 45000,
  report_generation: 60000,

  // Chart and visualization
  chart_render: 3000,
  chart_animation: 1500,

  // Performance testing
  performance_measurement: 10000,
  core_web_vitals: 15000,
  memory_monitoring: 20000,

  // Error recovery
  error_recovery: 30000,
  retry_attempts: 5000,
  network_recovery: 10000,

  // Intelligence system
  tier_processing: {
    current: 600000,    // 10 minutes (5-10 min range)
    standard: 1200000,  // 20 minutes (15-20 min range)
    enhanced: 2700000,  // 45 minutes (30-45 min range)
    complete: 3600000   // 60 minutes (45-60 min range)
  },

  // Accessibility testing
  accessibility_scan: 5000,
  keyboard_navigation: 3000,
  focus_management: 2000,

  // Cross-browser testing
  browser_feature_detection: 3000,
  compatibility_check: 5000,

  // Scraping operations
  scraping_execution: 45000,
  scraping_strategy_switch: 10000,
  data_quality_validation: 15000
};

/**
 * Test URLs and endpoints - Enhanced for comprehensive testing
 */
const urls = {
  base: 'http://localhost:8000',
  api: {
    // System endpoints
    system_status: '/api/system/status',
    system_health: '/api/system/health',
    system_metrics: '/api/system/metrics',

    // Core application endpoints
    profiles: '/api/profiles',
    discovery: '/api/discovery',
    dashboard: '/api/dashboard/overview',

    // Intelligence system endpoints
    intelligence_tiers: '/api/intelligence/tiers',
    intelligence_process: '/api/intelligence/process',
    intelligence_queue: '/api/intelligence/queue',

    // Analysis endpoints
    analysis_lite: '/api/analysis/lite',
    analysis_heavy: '/api/analysis/heavy',
    analysis_comprehensive: '/api/analysis/comprehensive',

    // Export endpoints
    export_pdf: '/api/export/pdf',
    export_excel: '/api/export/excel',
    export_powerpoint: '/api/export/powerpoint',

    // Enhanced scraping endpoints
    scrape_enhanced: '/api/scrape/enhanced',
    scrape_progress: '/api/scrape/progress',
    scrape_quality: '/api/scrape/quality',

    // Cost tracking endpoints
    costs_summary: '/api/costs/summary',
    costs_breakdown: '/api/costs/breakdown',

    // Performance monitoring
    performance_metrics: '/api/performance/metrics',
    network_metrics: '/api/network/metrics'
  },

  // Test URLs for external validation
  test_urls: {
    httpbin_html: 'https://httpbin.org/html',
    httpbin_json: 'https://httpbin.org/json',
    example_org: 'https://example.com',
    connectivity_test: 'https://www.google.com'
  },

  // Documentation and help
  docs: {
    api_documentation: '/api/docs',
    user_guide: '/docs/user-guide',
    test_documentation: '/docs/testing'
  }
};

module.exports = {
  profiles,
  scenarios,
  mockData,
  selectors,
  timeouts,
  urls
};
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
 * Test selectors for common UI elements - Updated for actual Catalynx application
 */
const selectors = {
  navigation: {
    // Main tab navigation (based on actual inspection)
    overview_tab: 'button:has-text("Overview")',
    discover_tab: 'button:has-text("DISCOVER")', 
    plan_tab: 'button:has-text("PLAN")',
    analyze_tab: 'button:has-text("ANALYZE")',
    examine_tab: 'button:has-text("EXAMINE")',
    approach_tab: 'button:has-text("APPROACH")'
  },
  
  profile_management: {
    create_profile_button: 'button:has-text("Create Profile")',
    profile_modal: '.fixed.inset-0', // Modal overlay
    organization_name_input: 'input[name="organization_name"], input[placeholder*="organization"], input[placeholder*="Organization"]',
    website_url_input: 'input[name="website_url"], input[placeholder*="website"], input[placeholder*="Website"], input[placeholder*="URL"]',
    save_profile_button: 'button:has-text("Create Profile")',
    profile_card: '.bg-white.dark\\:bg-gray-800, .border, .rounded-lg' // Profile cards
  },
  
  enhanced_data: {
    enhanced_data_tab: 'button:has-text("Enhanced Data")',
    basic_info_tab: 'button:has-text("Basic Information")',
    ein_display: 'text=/\\d{2}-\\d{7}/', // EIN format
    bmf_data_section: 'text="BMF", text="Business Master File"',
    source_attribution: 'text="Source", text="IRS", text="990"',
    confidence_score: 'text=/%/', // Percentage indicators
    verification_badge: '.bg-green, .text-green, text="Verified"'
  },
  
  discovery: {
    execute_discovery_button: 'button:has-text("Run All Tracks"), button:has-text("Start"), button:has-text("Discover")',
    discovery_results: '.overflow-x-auto, table',
    results_table: 'table, .grid',
    filter_dropdown: 'button:has-text("Filter"), select',
    pagination_controls: 'button:has-text("Previous"), button:has-text("Next"), button:has-text("1")'
  },
  
  charts: {
    // Canvas elements for Chart.js
    system_performance_chart: 'canvas',
    scoring_distribution_chart: 'canvas',
    revenue_breakdown_chart: 'canvas'
  },
  
  // Common UI patterns found in the app
  common: {
    loading_spinner: '.opacity-50, text="Loading", text="Processing"',
    success_notification: '.bg-green, text="Success", text="Complete"',
    error_notification: '.bg-red, text="Error", text="Failed"',
    modal_close: 'button:has-text("×"), button:has-text("Close"), button:has-text("Cancel")'
  }
};

/**
 * Test timeouts and delays
 */
const timeouts = {
  navigation: 5000,
  api_response: 10000,
  chart_render: 3000,
  modal_animation: 1000,
  discovery_execution: 30000,
  report_generation: 45000
};

/**
 * Test URLs and endpoints
 */
const urls = {
  base: 'http://localhost:8000',
  api: {
    system_status: '/api/system/status',
    system_health: '/api/system/health',
    profiles: '/api/profiles',
    discovery: '/api/discovery',
    dashboard: '/api/dashboard/overview'
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
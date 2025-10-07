// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for Catalynx Grant Research Intelligence Platform
 * 
 * This configuration supports:
 * - Multi-browser testing (Chromium, Firefox, WebKit)
 * - Visual regression testing
 * - Performance monitoring
 * - Cross-platform compatibility
 * 
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  // Test directory
  testDir: './tests',
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'reports/html-report' }],
    ['json', { outputFile: 'reports/test-results.json' }],
    ['junit', { outputFile: 'reports/junit-results.xml' }],
    ['allure-playwright', { outputFolder: 'reports/allure-results' }]
  ],
  
  // Global test configuration
  use: {
    // Base URL for the Catalynx application
    baseURL: 'http://localhost:8000',
    
    // Global test timeout
    actionTimeout: 30000,
    navigationTimeout: 30000,
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Record video on failure
    video: 'retain-on-failure',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Browser context options
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    
    // Extra HTTP headers
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9'
    }
  },

  // Global setup and teardown
  globalSetup: require.resolve('./fixtures/global-setup'),
  globalTeardown: require.resolve('./fixtures/global-teardown'),

  // Configure projects for major browsers
  projects: [
    // Desktop Browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Enable file downloads
        acceptDownloads: true,
        // Enable permissions for testing
        permissions: ['clipboard-read', 'clipboard-write']
      },
    },
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        acceptDownloads: true
      },
    },
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        acceptDownloads: true
      },
    },

    // Mobile Testing - DEPRECATED (October 7, 2025)
    // Catalynx is a desktop web application, not a mobile app
    // Mobile tests moved to tests/_mobile_deprecated/
    // {
    //   name: 'mobile-chrome',
    //   use: {
    //     ...devices['Pixel 5']
    //   },
    // },
    // {
    //   name: 'mobile-safari',
    //   use: {
    //     ...devices['iPhone 13']
    //   },
    // },

    // High DPI Testing
    {
      name: 'high-dpi',
      use: {
        ...devices['Desktop Chrome HiDPI'],
        acceptDownloads: true
      },
    }
  ],

  // Test-specific configurations
  expect: {
    // Visual comparison threshold
    threshold: 0.2,
    
    // Animation handling
    toHaveScreenshot: {
      threshold: 0.2,
      mode: 'test',
      animations: 'disabled'
    },
    
    // Default timeout for expect() calls
    timeout: 10000
  },

  // Output directories
  outputDir: 'test-results/',
  
  // Timeout configuration
  timeout: 60000,
  
  // Test matching patterns
  testMatch: [
    '**/*.spec.js',
    '**/*.test.js'
  ],
  
  // Files to ignore
  testIgnore: [
    '**/node_modules/**',
    '**/reports/**',
    '**/test-results/**'
  ],

  // Web server configuration for local development
  webServer: {
    command: 'echo "Catalynx server should be running on http://localhost:8000"',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
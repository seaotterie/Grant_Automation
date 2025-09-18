/**
 * Global Setup for Playwright Tests
 * 
 * This file handles:
 * - Environment validation
 * - Test data preparation
 * - Authentication setup
 * - System health checks
 */

const { chromium } = require('@playwright/test');

async function globalSetup() {
  console.log('🔧 Catalynx Playwright Global Setup Starting...');
  
  const startTime = Date.now();
  
  try {
    // 1. Environment Validation
    console.log('📋 Validating test environment...');
    await validateEnvironment();
    
    // 2. System Health Check
    console.log('🏥 Performing system health check...');
    await performHealthCheck();
    
    // 3. Test Data Preparation
    console.log('📊 Preparing test data...');
    await prepareTestData();
    
    // 4. Authentication Setup (if needed)
    console.log('🔐 Setting up authentication...');
    await setupAuthentication();
    
    const duration = Date.now() - startTime;
    console.log(`✅ Global setup completed successfully in ${duration}ms`);
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  }
}

/**
 * Validate that the test environment is properly configured
 */
async function validateEnvironment() {
  const requiredEnvVars = ['NODE_ENV'];
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    console.warn(`⚠️  Missing environment variables: ${missingVars.join(', ')}`);
  }
  
  // Check if base URL is accessible
  const baseUrl = process.env.BASE_URL || 'http://localhost:8000';
  console.log(`🔗 Testing connectivity to ${baseUrl}`);
  
  try {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const response = await page.goto(baseUrl, { 
      timeout: 30000,
      waitUntil: 'domcontentloaded' 
    });
    
    if (!response.ok()) {
      throw new Error(`Server responded with ${response.status()}`);
    }
    
    // Check if essential elements are present
    const titleElement = await page.locator('title').first();
    const title = await titleElement.textContent();
    
    if (!title || !title.includes('Catalynx')) {
      console.warn('⚠️  Page title does not contain "Catalynx" - may not be the correct application');
    }
    
    await browser.close();
    console.log('✅ Environment validation passed');
    
  } catch (error) {
    throw new Error(`Environment validation failed: ${error.message}`);
  }
}

/**
 * Perform system health check
 */
async function performHealthCheck() {
  try {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    // Check system status endpoint
    const response = await page.goto('http://localhost:8000/api/system/status', {
      timeout: 15000
    });
    
    if (response.ok()) {
      const statusData = await response.json();
      console.log('📊 System Status:', {
        processors_available: statusData.processors_available,
        cache_enabled: statusData.cache_enabled,
        database_connected: statusData.database_connected
      });
    } else {
      console.warn('⚠️  System status endpoint not accessible');
    }
    
    await browser.close();
    console.log('✅ Health check completed');
    
  } catch (error) {
    console.warn('⚠️  Health check failed:', error.message);
    // Don't fail the setup for health check issues
  }
}

/**
 * Prepare test data and fixtures
 */
async function prepareTestData() {
  // Load test configurations
  const testConfig = require('./test-configurations');
  
  // Validate test data integrity
  if (!testConfig.profiles || testConfig.profiles.length === 0) {
    console.warn('⚠️  No test profiles configured');
  }
  
  if (!testConfig.scenarios || Object.keys(testConfig.scenarios).length === 0) {
    console.warn('⚠️  No test scenarios configured');
  }
  
  console.log(`📋 Test data loaded: ${testConfig.profiles?.length || 0} profiles, ${Object.keys(testConfig.scenarios || {}).length} scenarios`);
}

/**
 * Setup authentication if required
 */
async function setupAuthentication() {
  // For now, Catalynx appears to use basic authentication
  // This can be expanded when authentication is implemented
  console.log('🔓 No authentication setup required for current configuration');
}

module.exports = globalSetup;
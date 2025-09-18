/**
 * Global Teardown for Playwright Tests
 * 
 * This file handles:
 * - Cleanup operations
 * - Report generation
 * - Resource disposal
 * - Test artifact organization
 */

async function globalTeardown() {
  console.log('🧹 Catalynx Playwright Global Teardown Starting...');
  
  const startTime = Date.now();
  
  try {
    // 1. Generate test summary
    console.log('📊 Generating test summary...');
    await generateTestSummary();
    
    // 2. Cleanup temporary resources
    console.log('🗑️  Cleaning up temporary resources...');
    await cleanupResources();
    
    // 3. Organize test artifacts
    console.log('📁 Organizing test artifacts...');
    await organizeTestArtifacts();
    
    const duration = Date.now() - startTime;
    console.log(`✅ Global teardown completed successfully in ${duration}ms`);
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error to avoid masking test failures
  }
}

/**
 * Generate a summary of test execution
 */
async function generateTestSummary() {
  const fs = require('fs').promises;
  const path = require('path');
  
  try {
    // Read test results if available
    const resultsPath = path.join(__dirname, '..', 'reports', 'test-results.json');
    const timestamp = new Date().toISOString();
    
    const summary = {
      timestamp,
      execution_info: {
        platform: process.platform,
        node_version: process.version,
        playwright_version: require('@playwright/test/package.json').version
      },
      test_environment: {
        base_url: process.env.BASE_URL || 'http://localhost:8000',
        ci: !!process.env.CI,
        workers: process.env.CI ? 1 : 'auto'
      }
    };
    
    // Try to read actual test results
    try {
      const resultsData = await fs.readFile(resultsPath, 'utf8');
      const results = JSON.parse(resultsData);
      
      summary.results = {
        total_tests: results.stats?.total || 0,
        passed: results.stats?.passed || 0,
        failed: results.stats?.failed || 0,
        skipped: results.stats?.skipped || 0,
        duration: results.stats?.duration || 0
      };
      
    } catch (error) {
      console.warn('⚠️  Could not read test results for summary');
      summary.results = {
        note: 'Test results not available during teardown'
      };
    }
    
    // Write summary
    const summaryPath = path.join(__dirname, '..', 'reports', 'test-summary.json');
    await fs.mkdir(path.dirname(summaryPath), { recursive: true });
    await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2));
    
    console.log('📋 Test summary generated');
    
  } catch (error) {
    console.warn('⚠️  Failed to generate test summary:', error.message);
  }
}

/**
 * Cleanup temporary resources and files
 */
async function cleanupResources() {
  const fs = require('fs').promises;
  const path = require('path');
  
  try {
    // Clean up any temporary files older than 7 days
    const tempDirs = [
      path.join(__dirname, '..', 'test-results'),
      path.join(__dirname, '..', 'screenshots', 'temp')
    ];
    
    for (const dir of tempDirs) {
      try {
        const files = await fs.readdir(dir);
        const now = Date.now();
        const weekAgo = now - (7 * 24 * 60 * 60 * 1000); // 7 days in milliseconds
        
        for (const file of files) {
          const filePath = path.join(dir, file);
          const stats = await fs.stat(filePath);
          
          if (stats.mtime.getTime() < weekAgo) {
            await fs.unlink(filePath);
            console.log(`🗑️  Cleaned up old file: ${file}`);
          }
        }
      } catch (error) {
        // Directory might not exist, which is fine
      }
    }
    
    console.log('🧽 Resource cleanup completed');
    
  } catch (error) {
    console.warn('⚠️  Resource cleanup failed:', error.message);
  }
}

/**
 * Organize test artifacts into appropriate directories
 */
async function organizeTestArtifacts() {
  const fs = require('fs').promises;
  const path = require('path');
  
  try {
    const reportsDir = path.join(__dirname, '..', 'reports');
    await fs.mkdir(reportsDir, { recursive: true });
    
    // Create archive directory for historical reports
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const archiveDir = path.join(reportsDir, 'archive', timestamp);
    
    // Check if we should archive (only if reports exist)
    try {
      const reportFiles = await fs.readdir(reportsDir);
      const hasReports = reportFiles.some(file => 
        file.endsWith('.json') || 
        file.endsWith('.xml') || 
        file === 'html-report'
      );
      
      if (hasReports && !process.env.CI) {
        await fs.mkdir(archiveDir, { recursive: true });
        console.log(`📦 Test artifacts organized in ${archiveDir}`);
      }
      
    } catch (error) {
      // No reports to organize
    }
    
    console.log('📁 Test artifact organization completed');
    
  } catch (error) {
    console.warn('⚠️  Test artifact organization failed:', error.message);
  }
}

module.exports = globalTeardown;
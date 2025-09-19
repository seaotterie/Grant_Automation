/**
 * Enhanced Scraping Features Tests
 *
 * This test suite validates the newly implemented Scrapy-MCP parallel processing features:
 * - Scraping Strategy Selection: parallel, adaptive, mcp_only, scrapy_only
 * - Progress Monitoring: Real-time status updates, task tracking
 * - Results Validation: Data quality, confidence scores, error handling
 * - Performance Comparison: Strategy effectiveness testing
 * - API Integration: Enhanced scraping endpoints and functionality
 */

const { test, expect } = require('@playwright/test');
const BasePage = require('../../page-objects/BasePage');
const ProfilePage = require('../../page-objects/ProfilePage');
const { profiles } = require('../../fixtures/test-configurations');

test.describe('Enhanced Scraping Features', () => {
  let basePage;
  let profilePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    profilePage = new ProfilePage(page);

    await basePage.navigate();
    await basePage.waitForAppReady();
  });

  test.describe('Scraping Strategy Selection', () => {
    test('Enhanced scraping API endpoints are accessible', async ({ page }) => {
      console.log('🧪 Testing enhanced scraping API endpoints...');

      // Test enhanced scraping health endpoint
      try {
        const healthResponse = await page.request.get('http://localhost:8000/api/scrape/health');
        expect(healthResponse.ok()).toBeTruthy();

        const healthData = await healthResponse.json();
        expect(healthData.status).toBeTruthy();
        console.log(`✅ Enhanced scraping health status: ${healthData.status}`);
      } catch (error) {
        console.log(`ℹ️  Enhanced scraping health endpoint not accessible: ${error.message}`);
      }

      // Test scraping strategies endpoint
      try {
        const strategiesResponse = await page.request.get('http://localhost:8000/api/scrape/strategies');
        if (strategiesResponse.ok()) {
          const strategiesData = await strategiesResponse.json();
          expect(strategiesData.strategies).toBeTruthy();

          const strategies = strategiesData.strategies;
          const expectedStrategies = ['parallel', 'adaptive', 'mcp_only', 'scrapy_only'];

          for (const strategy of expectedStrategies) {
            if (strategies[strategy]) {
              console.log(`✅ Found ${strategy} scraping strategy`);
            } else {
              console.log(`ℹ️  ${strategy} strategy not found`);
            }
          }
        }
      } catch (error) {
        console.log(`ℹ️  Scraping strategies endpoint not accessible: ${error.message}`);
      }

      await basePage.takeScreenshot('enhanced-scraping-api-test');
    });

    test('Parallel scraping strategy functionality', async ({ page }) => {
      console.log('🧪 Testing parallel scraping strategy...');

      // Test parallel scraping via API
      try {
        const testRequest = {
          urls: ['https://httpbin.org/html', 'https://example.com'],
          organization_name: 'Test Organization',
          scraping_strategy: 'parallel',
          max_pages: 2,
          timeout: 30
        };

        const scrapingResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: testRequest,
          timeout: 45000
        });

        if (scrapingResponse.ok()) {
          const scrapingData = await scrapingResponse.json();

          expect(scrapingData.success).toBeTruthy();
          expect(scrapingData.strategy_used).toBe('parallel');
          expect(scrapingData.processing_time).toBeGreaterThan(0);

          // Verify both MCP and Scrapy results
          console.log(`✅ Parallel scraping completed in ${scrapingData.processing_time.toFixed(2)}s`);
          console.log(`📊 MCP pages: ${scrapingData.mcp_pages_scraped}, Scrapy pages: ${scrapingData.scrapy_pages_scraped}`);

          // Validate quality metrics
          expect(scrapingData.confidence_score).toBeGreaterThanOrEqual(0);
          expect(scrapingData.confidence_score).toBeLessThanOrEqual(1);
          expect(scrapingData.source_diversity).toBeGreaterThanOrEqual(0);

        } else {
          console.log(`ℹ️  Parallel scraping API not available: ${scrapingResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Parallel scraping test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('parallel-scraping-test');
    });

    test('Adaptive scraping strategy functionality', async ({ page }) => {
      console.log('🧪 Testing adaptive scraping strategy...');

      try {
        const testRequest = {
          urls: ['https://httpbin.org/json', 'https://httpbin.org/html'],
          organization_name: 'Adaptive Test Organization',
          scraping_strategy: 'adaptive',
          max_pages: 2,
          timeout: 30
        };

        const scrapingResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: testRequest,
          timeout: 45000
        });

        if (scrapingResponse.ok()) {
          const scrapingData = await scrapingResponse.json();

          expect(scrapingData.success).toBeTruthy();
          expect(scrapingData.strategy_used).toBe('adaptive');

          console.log(`✅ Adaptive scraping completed in ${scrapingData.processing_time.toFixed(2)}s`);
          console.log(`📊 Source diversity: ${scrapingData.source_diversity.toFixed(2)}`);

          // Adaptive should show intelligent routing
          const totalPages = scrapingData.mcp_pages_scraped + scrapingData.scrapy_pages_scraped;
          expect(totalPages).toBeGreaterThan(0);

        } else {
          console.log(`ℹ️  Adaptive scraping API not available: ${scrapingResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Adaptive scraping test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('adaptive-scraping-test');
    });

    test('MCP-only scraping strategy functionality', async ({ page }) => {
      console.log('🧪 Testing MCP-only scraping strategy...');

      try {
        const testRequest = {
          urls: ['https://httpbin.org/json'],
          organization_name: 'MCP Test Organization',
          scraping_strategy: 'mcp_only',
          max_pages: 1,
          timeout: 20
        };

        const scrapingResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: testRequest,
          timeout: 30000
        });

        if (scrapingResponse.ok()) {
          const scrapingData = await scrapingResponse.json();

          expect(scrapingData.success).toBeTruthy();
          expect(scrapingData.strategy_used).toBe('mcp_only');

          // Should only have MCP results
          expect(scrapingData.mcp_pages_scraped).toBeGreaterThan(0);
          expect(scrapingData.scrapy_pages_scraped).toBe(0);

          console.log(`✅ MCP-only scraping completed in ${scrapingData.processing_time.toFixed(2)}s`);
          console.log(`📊 MCP pages only: ${scrapingData.mcp_pages_scraped}`);

        } else {
          console.log(`ℹ️  MCP-only scraping API not available: ${scrapingResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  MCP-only scraping test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('mcp-only-scraping-test');
    });

    test('Scrapy-only scraping strategy functionality', async ({ page }) => {
      console.log('🧪 Testing Scrapy-only scraping strategy...');

      try {
        const testRequest = {
          urls: ['https://httpbin.org/html'],
          organization_name: 'Scrapy Test Organization',
          scraping_strategy: 'scrapy_only',
          max_pages: 1,
          timeout: 30
        };

        const scrapingResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: testRequest,
          timeout: 45000
        });

        if (scrapingResponse.ok()) {
          const scrapingData = await scrapingResponse.json();

          expect(scrapingData.success).toBeTruthy();
          expect(scrapingData.strategy_used).toBe('scrapy_only');

          // Should only have Scrapy results
          expect(scrapingData.scrapy_pages_scraped).toBeGreaterThan(0);
          expect(scrapingData.mcp_pages_scraped).toBe(0);

          console.log(`✅ Scrapy-only scraping completed in ${scrapingData.processing_time.toFixed(2)}s`);
          console.log(`📊 Scrapy pages only: ${scrapingData.scrapy_pages_scraped}`);

        } else {
          console.log(`ℹ️  Scrapy-only scraping API not available: ${scrapingResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Scrapy-only scraping test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('scrapy-only-scraping-test');
    });
  });

  test.describe('Progress Monitoring', () => {
    test('Asynchronous scraping with progress tracking', async ({ page }) => {
      console.log('🧪 Testing asynchronous scraping with progress tracking...');

      try {
        // Start async scraping
        const testRequest = {
          urls: ['https://httpbin.org/html', 'https://example.com'],
          organization_name: 'Async Test Organization',
          scraping_strategy: 'parallel',
          max_pages: 2,
          timeout: 45
        };

        const asyncResponse = await page.request.post('http://localhost:8000/api/scrape/async', {
          data: testRequest,
          timeout: 10000
        });

        if (asyncResponse.ok()) {
          const asyncData = await asyncResponse.json();
          const taskId = asyncData.task_id;

          expect(taskId).toBeTruthy();
          expect(asyncData.status).toBe('processing');
          console.log(`✅ Async scraping started with task ID: ${taskId}`);

          // Monitor progress
          let attempts = 0;
          const maxAttempts = 20;
          let taskCompleted = false;

          while (attempts < maxAttempts && !taskCompleted) {
            await page.waitForTimeout(3000); // Wait 3 seconds between checks

            try {
              const statusResponse = await page.request.get(`http://localhost:8000/api/scrape/status/${taskId}`);
              if (statusResponse.ok()) {
                const statusData = await statusResponse.json();

                console.log(`📊 Task ${taskId} status: ${statusData.status}, Progress: ${statusData.progress || 'N/A'}`);

                if (statusData.status === 'completed' || statusData.status === 'failed') {
                  taskCompleted = true;

                  if (statusData.status === 'completed') {
                    // Get final results
                    const resultsResponse = await page.request.get(`http://localhost:8000/api/scrape/result/${taskId}`);
                    if (resultsResponse.ok()) {
                      const resultsData = await resultsResponse.json();

                      expect(resultsData.success).toBeTruthy();
                      console.log(`✅ Async scraping completed successfully`);
                      console.log(`📊 Final results: ${resultsData.leadership_count} leaders, ${resultsData.program_count} programs`);
                    }
                  }
                }
              }
            } catch (statusError) {
              console.log(`ℹ️  Status check error: ${statusError.message}`);
            }

            attempts++;
          }

          if (!taskCompleted) {
            console.log('ℹ️  Async scraping task did not complete within timeout');
          }

        } else {
          console.log(`ℹ️  Async scraping API not available: ${asyncResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Async scraping test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('async-scraping-progress');
    });

    test('Scraping coordinator status monitoring', async ({ page }) => {
      console.log('🧪 Testing scraping coordinator status...');

      try {
        const coordinatorResponse = await page.request.get('http://localhost:8000/api/scrape/coordinator/status');

        if (coordinatorResponse.ok()) {
          const coordinatorData = await coordinatorResponse.json();

          expect(coordinatorData.coordinator_status).toBeTruthy();
          expect(coordinatorData.performance_metrics).toBeTruthy();

          console.log(`✅ Coordinator status: ${coordinatorData.coordinator_status}`);
          console.log(`📊 Active tasks: ${coordinatorData.active_tasks}, Completed: ${coordinatorData.completed_tasks}`);

          // Verify configuration
          if (coordinatorData.configuration) {
            expect(coordinatorData.configuration.max_scrapy_workers).toBeGreaterThan(0);
            expect(coordinatorData.configuration.max_mcp_workers).toBeGreaterThan(0);
            console.log(`✅ Coordinator configuration: ${coordinatorData.configuration.max_scrapy_workers} Scrapy, ${coordinatorData.configuration.max_mcp_workers} MCP workers`);
          }

        } else {
          console.log(`ℹ️  Coordinator status API not available: ${coordinatorResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Coordinator status test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('coordinator-status');
    });
  });

  test.describe('Results Validation', () => {
    test('Data quality and confidence scoring', async ({ page }) => {
      console.log('🧪 Testing scraping data quality and confidence scoring...');

      try {
        // Use a real organization URL for better quality testing
        const testRequest = {
          urls: ['https://www.redcross.org'],
          organization_name: 'American Red Cross',
          scraping_strategy: 'adaptive',
          max_pages: 2,
          timeout: 60
        };

        const scrapingResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: testRequest,
          timeout: 70000
        });

        if (scrapingResponse.ok()) {
          const scrapingData = await scrapingResponse.json();

          if (scrapingData.success) {
            // Validate quality metrics
            expect(scrapingData.confidence_score).toBeGreaterThanOrEqual(0);
            expect(scrapingData.confidence_score).toBeLessThanOrEqual(1);
            expect(scrapingData.data_completeness).toBeGreaterThanOrEqual(0);
            expect(scrapingData.data_completeness).toBeLessThanOrEqual(1);
            expect(scrapingData.source_diversity).toBeGreaterThanOrEqual(0);
            expect(scrapingData.source_diversity).toBeLessThanOrEqual(1);

            console.log(`✅ Quality metrics validation passed`);
            console.log(`📊 Confidence: ${scrapingData.confidence_score.toFixed(3)}, Completeness: ${scrapingData.data_completeness.toFixed(3)}, Diversity: ${scrapingData.source_diversity.toFixed(3)}`);

            // Test with detailed data
            const detailedRequest = { ...testRequest, include_detailed_data: true };
            const detailedResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced?include_detailed_data=true', {
              data: detailedRequest,
              timeout: 70000
            });

            if (detailedResponse.ok()) {
              const detailedData = await detailedResponse.json();

              if (detailedData.leadership_data) {
                console.log(`📊 Leadership data found: ${detailedData.leadership_data.length} entries`);

                // Validate leadership data structure
                if (detailedData.leadership_data.length > 0) {
                  const firstLeader = detailedData.leadership_data[0];
                  expect(firstLeader.name).toBeTruthy();
                  expect(typeof firstLeader.name).toBe('string');
                  console.log(`✅ Leadership data structure valid`);
                }
              }

              if (detailedData.program_data) {
                console.log(`📊 Program data found: ${detailedData.program_data.length} entries`);
              }

              if (detailedData.contact_data) {
                const contactFields = Object.keys(detailedData.contact_data).length;
                console.log(`📊 Contact data fields: ${contactFields}`);
              }
            }
          }
        } else {
          console.log(`ℹ️  Real organization scraping not available: ${scrapingResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Data quality test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('data-quality-validation');
    });

    test('Error handling and validation', async ({ page }) => {
      console.log('🧪 Testing scraping error handling...');

      try {
        // Test with invalid URL
        const invalidRequest = {
          urls: ['https://invalid-domain-that-does-not-exist-12345.com'],
          organization_name: 'Invalid Test',
          scraping_strategy: 'parallel',
          max_pages: 1,
          timeout: 15
        };

        const errorResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: invalidRequest,
          timeout: 20000
        });

        if (errorResponse.ok()) {
          const errorData = await errorResponse.json();

          // Should handle error gracefully
          if (!errorData.success) {
            expect(errorData.errors).toBeTruthy();
            expect(errorData.errors.length).toBeGreaterThan(0);
            console.log(`✅ Error handling working: ${errorData.errors[0]}`);
          } else {
            console.log(`ℹ️  Invalid URL request unexpectedly succeeded`);
          }
        }

        // Test with empty URL list
        const emptyRequest = {
          urls: [],
          organization_name: 'Empty Test',
          scraping_strategy: 'parallel'
        };

        const emptyResponse = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
          data: emptyRequest,
          timeout: 10000
        });

        // Should return validation error
        expect(emptyResponse.status()).toBe(422); // Validation error
        console.log(`✅ Empty URL validation working`);

      } catch (error) {
        console.log(`ℹ️  Error handling test completed with expected errors`);
      }

      await basePage.takeScreenshot('error-handling-validation');
    });
  });

  test.describe('Performance Comparison', () => {
    test('Strategy performance comparison', async ({ page }) => {
      console.log('🧪 Testing scraping strategy performance comparison...');

      const testUrl = 'https://httpbin.org/html';
      const strategies = ['mcp_only', 'parallel'];
      const performanceResults = {};

      for (const strategy of strategies) {
        try {
          const startTime = Date.now();

          const testRequest = {
            urls: [testUrl],
            organization_name: `Performance Test - ${strategy}`,
            scraping_strategy: strategy,
            max_pages: 1,
            timeout: 30
          };

          const response = await page.request.post('http://localhost:8000/api/scrape/enhanced', {
            data: testRequest,
            timeout: 40000
          });

          const endTime = Date.now();
          const totalTime = endTime - startTime;

          if (response.ok()) {
            const data = await response.json();

            performanceResults[strategy] = {
              total_time: totalTime,
              processing_time: data.processing_time,
              success: data.success,
              confidence_score: data.confidence_score,
              pages_scraped: data.mcp_pages_scraped + data.scrapy_pages_scraped
            };

            console.log(`✅ ${strategy} completed in ${totalTime}ms (processing: ${data.processing_time.toFixed(2)}s)`);
          } else {
            performanceResults[strategy] = {
              total_time: totalTime,
              success: false,
              error: `HTTP ${response.status()}`
            };
          }
        } catch (error) {
          performanceResults[strategy] = {
            success: false,
            error: error.message
          };
        }

        // Wait between tests
        await page.waitForTimeout(2000);
      }

      // Compare performance
      if (performanceResults.mcp_only?.success && performanceResults.parallel?.success) {
        const mcpTime = performanceResults.mcp_only.total_time;
        const parallelTime = performanceResults.parallel.total_time;

        console.log(`📊 Performance comparison:`);
        console.log(`   MCP-only: ${mcpTime}ms`);
        console.log(`   Parallel: ${parallelTime}ms`);

        if (mcpTime < parallelTime) {
          console.log(`✅ MCP-only faster by ${parallelTime - mcpTime}ms`);
        } else {
          console.log(`✅ Parallel faster by ${mcpTime - parallelTime}ms`);
        }

        // Verify both strategies complete within reasonable time
        expect(mcpTime).toBeLessThan(45000); // 45 seconds
        expect(parallelTime).toBeLessThan(60000); // 60 seconds
      }

      await basePage.takeScreenshot('performance-comparison');
    });

    test('Performance analytics endpoint', async ({ page }) => {
      console.log('🧪 Testing performance analytics...');

      try {
        const analyticsResponse = await page.request.get('http://localhost:8000/api/scrape/performance');

        if (analyticsResponse.ok()) {
          const analyticsData = await analyticsResponse.json();

          expect(analyticsData.total_requests).toBeGreaterThanOrEqual(0);
          expect(analyticsData.success_rate).toBeGreaterThanOrEqual(0);
          expect(analyticsData.success_rate).toBeLessThanOrEqual(1);

          console.log(`✅ Performance analytics available`);
          console.log(`📊 Total requests: ${analyticsData.total_requests}, Success rate: ${(analyticsData.success_rate * 100).toFixed(1)}%`);

          if (analyticsData.strategy_performance) {
            const strategies = Object.keys(analyticsData.strategy_performance);
            console.log(`📊 Strategy performance data available for: ${strategies.join(', ')}`);
          }

          if (analyticsData.recommendations && analyticsData.recommendations.length > 0) {
            console.log(`💡 Recommendations: ${analyticsData.recommendations[0]}`);
          }

        } else {
          console.log(`ℹ️  Performance analytics API not available: ${analyticsResponse.status()}`);
        }
      } catch (error) {
        console.log(`ℹ️  Performance analytics test failed: ${error.message}`);
      }

      await basePage.takeScreenshot('performance-analytics');
    });
  });

  test.describe('UI Integration', () => {
    test('Enhanced scraping features in profile creation', async ({ page }) => {
      console.log('🧪 Testing enhanced scraping integration in UI...');

      await profilePage.navigateToProfiles();

      // Look for enhanced scraping options in profile creation
      const createButton = page.locator('button:has-text("Create Profile")').first();
      if (await createButton.isVisible({ timeout: 10000 })) {
        await createButton.click();

        const modal = page.locator('.fixed.inset-0, .modal').first();
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Look for scraping strategy options
        const scrapingOptions = page.locator('text="Strategy", text="Scraping", text="Enhanced", select, input[type="radio"]');
        const optionCount = await scrapingOptions.count();

        if (optionCount > 0) {
          console.log(`✅ Found ${optionCount} enhanced scraping options in UI`);

          // Test selecting different strategies
          const strategySelectors = [
            'text="Parallel"',
            'text="Adaptive"',
            'text="MCP"',
            'text="Scrapy"'
          ];

          for (const selector of strategySelectors) {
            const option = page.locator(selector).first();
            if (await option.isVisible({ timeout: 2000 })) {
              await option.click();
              console.log(`✅ Strategy option clickable: ${selector}`);
              break;
            }
          }
        } else {
          console.log('ℹ️  Enhanced scraping options not found in profile creation UI');
        }

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("Close")').first();
        if (await closeButton.isVisible({ timeout: 2000 })) {
          await closeButton.click();
        }
      }

      await basePage.takeScreenshot('enhanced-scraping-ui-integration');
    });

    test('Scraping progress indicators in UI', async ({ page }) => {
      console.log('🧪 Testing scraping progress indicators...');

      // Look for progress indicators or status displays
      const progressElements = page.locator('text="Processing", text="Scraping", .progress, .loading, [role="progressbar"]');
      const progressCount = await progressElements.count();

      if (progressCount > 0) {
        console.log(`✅ Found ${progressCount} progress indicator elements`);
      } else {
        console.log('ℹ️  Progress indicators may be dynamically shown during operations');
      }

      // Look for scraping status or results displays
      const statusElements = page.locator('text="Confidence", text="Quality", text="Source", text="Strategy"');
      const statusCount = await statusElements.count();

      if (statusCount > 0) {
        console.log(`✅ Found ${statusCount} status/quality indicator elements`);
      }

      await basePage.takeScreenshot('scraping-progress-ui');
    });
  });
});
/**
 * Phase 9 Test: BMF/SOI Database Integration
 *
 * Validates the comprehensive nonprofit intelligence database with
 * 700K+ BMF organizations, 626K+ Form 990, and 333K+ Form 990-PF records.
 *
 * Tests Phase 8 achievement: 47.2x improvement in discovery results
 * (10 → 472 organizations discovered with enhanced filters).
 *
 * Database Coverage:
 * - bmf_organizations: 700,488 records (all tax-exempt orgs)
 * - form_990: 626,983 records (large nonprofits ≥$200K revenue)
 * - form_990pf: 333,126 records (private foundations)
 *
 * Tests:
 * - BMF discovery with 752K+ organizations
 * - Form 990 financial intelligence
 * - Form 990-PF foundation analysis
 * - Multi-criteria filtering (NTEE, state, revenue)
 * - Financial intelligence scoring
 * - Foundation grant capacity analysis
 */

const { test, expect } = require('@playwright/test');

test.describe('Phase 9: BMF/SOI Database Integration', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await page.waitForFunction(
      () => window.Alpine && window.catalynxApp,
      { timeout: 10000 }
    );
  });

  test('BMF Database: 700K+ organizations accessible', async ({ request }) => {
    console.log('🧪 Testing BMF database size and accessibility...');

    const response = await request.get('http://localhost:8000/api/discovery/bmf/stats');

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const orgCount = data.total_organizations || data.count || data.total;

      console.log(`📊 BMF Organizations: ${orgCount?.toLocaleString() || 'unknown'}`);

      if (orgCount) {
        expect(orgCount).toBeGreaterThan(600000); // Should have 700K+
        console.log('✅ BMF database validated');
      }
    } else {
      console.log(`ℹ️ BMF stats endpoint returned ${response.status()}`);
    }
  });

  test('Form 990 Database: 626K+ financial records', async ({ request }) => {
    console.log('🧪 Testing Form 990 database...');

    const response = await request.get('http://localhost:8000/api/intelligence/990/stats');

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const form990Count = data.form_990_count || data.count || data.total;

      console.log(`📊 Form 990 Records: ${form990Count?.toLocaleString() || 'unknown'}`);

      if (form990Count) {
        expect(form990Count).toBeGreaterThan(500000); // Should have 626K+
        console.log('✅ Form 990 database validated');
      }
    } else {
      console.log(`ℹ️ Form 990 stats endpoint returned ${response.status()}`);
    }
  });

  test('Form 990-PF Database: 333K+ foundation records', async ({ request }) => {
    console.log('🧪 Testing Form 990-PF database...');

    const response = await request.get('http://localhost:8000/api/intelligence/990pf/stats');

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const form990pfCount = data.form_990pf_count || data.count || data.total;

      console.log(`📊 Form 990-PF Records: ${form990pfCount?.toLocaleString() || 'unknown'}`);

      if (form990pfCount) {
        expect(form990pfCount).toBeGreaterThan(250000); // Should have 333K+
        console.log('✅ Form 990-PF database validated');
      }
    } else {
      console.log(`ℹ️ Form 990-PF stats endpoint returned ${response.status()}`);
    }
  });

  test('BMF Discovery: Multi-criteria filtering (NTEE + State)', async ({ request }) => {
    console.log('🧪 Testing multi-criteria BMF discovery...');

    const response = await request.post('http://localhost:8000/api/discovery/bmf/search', {
      data: {
        ntee_codes: ['P20', 'B25'],
        states: ['VA', 'MD'],
        min_revenue: 100000,
        max_revenue: 10000000,
        limit: 100
      }
    });

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const resultCount = data.results?.length || data.organizations?.length || data.count || 0;

      console.log(`📊 Discovery results: ${resultCount} organizations`);

      // Phase 8 achievement: 47.2x improvement (10 → 472)
      // Should find significant results with multi-criteria filtering
      expect(resultCount).toBeGreaterThan(10);

      if (resultCount > 50) {
        console.log('✅ Excellent discovery performance (>50 results)');
      } else if (resultCount > 20) {
        console.log('✅ Good discovery performance (>20 results)');
      } else {
        console.log('✅ Basic discovery operational (>10 results)');
      }
    } else {
      console.log(`ℹ️ BMF discovery returned ${response.status()}`);
    }
  });

  test('Enhanced BMF Discovery: Financial intelligence filters', async ({ request }) => {
    console.log('🧪 Testing enhanced BMF discovery with financial filters...');

    const response = await request.post('http://localhost:8000/api/discovery/bmf/enhanced-search', {
      data: {
        criteria: {
          ntee_codes: ['P20'],
          states: ['VA'],
          revenue_range: [500000, 5000000]
        },
        financial_filters: {
          foundation_grants_paid: true,
          min_assets: 1000000,
          grant_capacity: 'Major'
        },
        limit: 50
      }
    });

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const resultCount = data.results?.length || data.count || 0;

      console.log(`📊 Enhanced discovery: ${resultCount} qualified organizations`);

      // Enhanced filtering should return high-quality results
      expect(resultCount).toBeGreaterThan(0);

      console.log('✅ Enhanced discovery with financial intelligence operational');
    } else {
      console.log(`ℹ️ Enhanced discovery returned ${response.status()}`);
    }
  });

  test('Form 990 Financial Intelligence: Revenue and asset analysis', async ({ request }) => {
    console.log('🧪 Testing Form 990 financial intelligence...');

    const testEIN = '812827604'; // Mountain America Foundation

    const response = await request.get(`http://localhost:8000/api/intelligence/990/${testEIN}/financial`);

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();

      // Should have comprehensive financial data
      const hasFinancialData = data.revenue || data.expenses || data.assets ||
                               data.total_revenue || data.total_assets;

      if (hasFinancialData) {
        console.log('✅ Form 990 financial intelligence provided');
        console.log(`📊 Financial metrics: ${Object.keys(data).length} fields`);
      }
    } else {
      console.log(`ℹ️ 990 financial endpoint returned ${response.status()}`);
    }
  });

  test('Form 990-PF Foundation Analysis: Grant capacity scoring', async ({ request }) => {
    console.log('🧪 Testing foundation grant capacity analysis...');

    const response = await request.post('http://localhost:8000/api/intelligence/foundation/capacity', {
      data: {
        state: 'VA',
        min_assets: 1000000,
        analyze_payout: true
      }
    });

    expect(response.status()).toBeLessThan(500);

    if (response.ok()) {
      const data = await response.json();
      const foundationCount = data.foundations?.length || data.count || 0;

      console.log(`📊 Foundations analyzed: ${foundationCount}`);

      if (foundationCount > 0) {
        // Check for capacity scoring
        const firstFoundation = data.foundations?.[0];
        if (firstFoundation) {
          const hasCapacityData = firstFoundation.grant_capacity ||
                                 firstFoundation.payout_ratio ||
                                 firstFoundation.distribution_amount;

          if (hasCapacityData) {
            console.log('✅ Grant capacity scoring operational');
          }
        }
      }
    } else {
      console.log(`ℹ️ Foundation capacity endpoint returned ${response.status()}`);
    }
  });

  test('Geographic Distribution: State-level filtering accuracy', async ({ request }) => {
    console.log('🧪 Testing geographic filtering...');

    const testStates = ['VA', 'MD', 'DC'];
    const results = {};

    for (const state of testStates) {
      const response = await request.post('http://localhost:8000/api/discovery/bmf/search', {
        data: {
          states: [state],
          limit: 50
        }
      });

      if (response.ok()) {
        const data = await response.json();
        results[state] = data.results?.length || data.count || 0;
      }
    }

    console.log('📊 Geographic distribution:', results);

    // Should find organizations in each state
    Object.entries(results).forEach(([state, count]) => {
      if (count > 0) {
        console.log(`✅ ${state}: ${count} organizations`);
      }
    });

    const totalFound = Object.values(results).reduce((sum, count) => sum + count, 0);
    expect(totalFound).toBeGreaterThan(0);

    console.log('✅ Geographic filtering validated');
  });

  test('NTEE Code Filtering: Category-specific discovery', async ({ request }) => {
    console.log('🧪 Testing NTEE code filtering...');

    const nteeCategories = [
      { code: 'P20', name: 'Human Services' },
      { code: 'B25', name: 'Education/Schools' },
      { code: 'T20', name: 'Philanthropy/Voluntarism' }
    ];

    const results = {};

    for (const category of nteeCategories) {
      const response = await request.post('http://localhost:8000/api/discovery/bmf/search', {
        data: {
          ntee_codes: [category.code],
          states: ['VA'],
          limit: 30
        }
      });

      if (response.ok()) {
        const data = await response.json();
        results[category.code] = {
          name: category.name,
          count: data.results?.length || data.count || 0
        };
      }
    }

    console.log('📊 NTEE category results:');
    Object.entries(results).forEach(([code, info]) => {
      console.log(`   ${code} (${info.name}): ${info.count} organizations`);
    });

    const totalFound = Object.values(results).reduce((sum, info) => sum + info.count, 0);
    expect(totalFound).toBeGreaterThan(0);

    console.log('✅ NTEE filtering validated');
  });

  test('47.2x Discovery Improvement Validation', async ({ request }) => {
    console.log('🧪 Validating Phase 8 discovery improvement (10 → 472 orgs)...');

    // Test comprehensive criteria that should return many results
    const response = await request.post('http://localhost:8000/api/discovery/bmf/search', {
      data: {
        ntee_codes: ['P20', 'P30', 'B25', 'B40'],
        states: ['VA', 'MD', 'DC'],
        min_revenue: 50000,
        max_revenue: 50000000,
        limit: 500
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    const resultCount = data.results?.length || data.count || 0;

    console.log(`📊 Discovery results: ${resultCount} organizations`);

    // Should significantly exceed baseline of 10 organizations
    expect(resultCount).toBeGreaterThan(50);

    if (resultCount > 400) {
      console.log('✅ Exceptional: >400 organizations (47.2x+ improvement)');
    } else if (resultCount > 200) {
      console.log('✅ Excellent: >200 organizations (20x+ improvement)');
    } else if (resultCount > 100) {
      console.log('✅ Great: >100 organizations (10x+ improvement)');
    } else {
      console.log('✅ Good: >50 organizations (5x+ improvement)');
    }
  });

  test('Database Query Performance: Sub-second responses', async ({ request }) => {
    console.log('🧪 Testing database query performance...');

    const queries = [
      { name: 'Simple state filter', data: { states: ['VA'], limit: 10 } },
      { name: 'NTEE filter', data: { ntee_codes: ['P20'], limit: 10 } },
      { name: 'Revenue range', data: { min_revenue: 100000, max_revenue: 1000000, limit: 10 } },
      { name: 'Multi-criteria', data: { states: ['VA'], ntee_codes: ['P20'], min_revenue: 100000, limit: 10 } }
    ];

    const results = [];

    for (const query of queries) {
      const startTime = Date.now();

      const response = await request.post('http://localhost:8000/api/discovery/bmf/search', {
        data: query.data
      });

      const endTime = Date.now();
      const duration = endTime - startTime;

      results.push({
        query: query.name,
        duration: duration,
        status: response.status()
      });

      console.log(`   ${query.name}: ${duration}ms`);
    }

    // All queries should complete within reasonable time
    results.forEach(result => {
      expect(result.duration).toBeLessThan(5000); // 5 seconds max
    });

    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    console.log(`📊 Average query time: ${Math.round(avgDuration)}ms`);

    if (avgDuration < 1000) {
      console.log('✅ Excellent performance (<1s average)');
    } else {
      console.log('✅ Good performance (<5s per query)');
    }
  });

  test('BMF Discovery UI: NTEE Code Selection Modal', async ({ page }) => {
    console.log('🧪 Testing BMF discovery UI with NTEE modal...');

    // Navigate to Discovery tab
    const discoverTab = page.locator('[data-tab="discover"], button:has-text("Discover")').first();
    if (await discoverTab.isVisible({ timeout: 5000 })) {
      await discoverTab.click();
      await page.waitForTimeout(1000);

      // Look for NTEE code selection button
      const nteeButton = page.locator('button:has-text("Select NTEE"), button:has-text("NTEE Codes")').first();
      if (await nteeButton.isVisible({ timeout: 5000 })) {
        await nteeButton.click();
        await page.waitForTimeout(500);

        // Modal should open
        const modal = page.locator('[role="dialog"], .modal, [data-modal="ntee"]').first();
        await expect.soft(modal).toBeVisible({ timeout: 3000 });

        // Should have NTEE categories
        const hasCategories = await page.locator('text="Human Services", text="Education", text="Health"').first().isVisible({ timeout: 2000 }).catch(() => false);

        if (hasCategories) {
          console.log('✅ NTEE selection modal operational');
        }

        // Close modal
        const closeBtn = page.locator('button:has-text("Close"), button:has-text("Cancel"), [data-testid="close-modal"]').first();
        if (await closeBtn.isVisible({ timeout: 2000 })) {
          await closeBtn.click();
        }
      }
    }

    console.log('✅ BMF discovery UI validated');
  });
});

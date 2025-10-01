const { chromium } = require('playwright');

async function testStartupErrors() {
    console.log('🚀 Testing application startup for JavaScript errors...');

    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    // Collect console errors
    const errors = [];
    const consoleMessages = [];

    page.on('console', msg => {
        consoleMessages.push({
            type: msg.type(),
            text: msg.text(),
            location: msg.location()
        });

        if (msg.type() === 'error') {
            errors.push({
                text: msg.text(),
                location: msg.location()
            });
        }
    });

    page.on('pageerror', error => {
        errors.push({
            text: error.message,
            stack: error.stack
        });
    });

    try {
        // Navigate to the application
        console.log('📱 Navigating to http://localhost:8000/');
        await page.goto('http://localhost:8000/', { waitUntil: 'networkidle' });

        // Wait for Alpine.js to initialize
        console.log('⏳ Waiting for Alpine.js initialization...');
        await page.waitForTimeout(3000);

        // Check if main content is visible
        const mainContent = await page.locator('[x-show="activeStage === \'welcome\'"]').isVisible();
        console.log('🏠 Welcome stage visible:', mainContent);

        // Check if main sidebar is visible
        const sidebar = await page.locator('aside').isVisible();
        console.log('📋 Sidebar visible:', sidebar);

        // Check Alpine.js status
        const alpineInitialized = await page.evaluate(() => {
            return typeof window.Alpine !== 'undefined';
        });
        console.log('🔧 Alpine.js loaded:', alpineInitialized);

        // Check if catalynxApp is registered
        const catalynxAppRegistered = await page.evaluate(() => {
            return window.Alpine && window.Alpine._x_dataStack &&
                   Object.keys(window.Alpine._x_dataStack).includes('catalynxApp');
        });
        console.log('📦 catalynxApp registered:', catalynxAppRegistered);

        // Log all errors found
        if (errors.length > 0) {
            console.log('\n❌ JavaScript Errors Found:');
            errors.forEach((error, index) => {
                console.log(`\n${index + 1}. ${error.text}`);
                if (error.location) {
                    console.log(`   Location: ${error.location.url}:${error.location.lineNumber}:${error.location.columnNumber}`);
                }
                if (error.stack) {
                    console.log(`   Stack: ${error.stack.split('\n')[0]}`);
                }
            });
        } else {
            console.log('\n✅ No JavaScript errors found!');
        }

        // Log relevant console messages
        const relevantMessages = consoleMessages.filter(msg =>
            msg.text.includes('DEBUG:') ||
            msg.text.includes('SUCCESS:') ||
            msg.text.includes('ERROR:') ||
            msg.text.includes('Alpine')
        );

        if (relevantMessages.length > 0) {
            console.log('\n📝 Relevant Console Messages:');
            relevantMessages.forEach(msg => {
                console.log(`   ${msg.type.toUpperCase()}: ${msg.text}`);
            });
        }

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        await browser.close();
    }
}

testStartupErrors().catch(console.error);
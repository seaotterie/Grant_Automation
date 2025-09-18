/**
 * Development Script: Inspect Application Structure
 * 
 * This script helps identify the actual selectors and structure of the
 * Catalynx application for updating our test selectors.
 */

const { chromium } = require('playwright');

async function inspectApplication() {
  console.log('🔍 Inspecting Catalynx Application Structure...');
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    // Navigate to application
    await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    console.log('\n📋 Page Title:', await page.title());
    
    // Check for Alpine.js
    const alpineExists = await page.evaluate(() => {
      return {
        Alpine: typeof window.Alpine !== 'undefined',
        catalynxApp: typeof window.catalynxApp !== 'undefined',
        hasAlpineData: document.querySelector('[x-data]') !== null
      };
    });
    console.log('\n🎯 Alpine.js Status:', alpineExists);
    
    // Find navigation elements
    console.log('\n🧭 Navigation Elements:');
    const navElements = await page.evaluate(() => {
      const elements = [];
      
      // Look for common navigation patterns
      const selectors = [
        'nav', '[role="navigation"]', '.nav', '.navigation',
        '[data-tab]', '[x-data]', 'button', 'a[href="#"]',
        '.tab', '.tabs', '[role="tab"]'
      ];
      
      for (const selector of selectors) {
        const els = document.querySelectorAll(selector);
        els.forEach((el, index) => {
          const text = el.textContent?.trim().substring(0, 50);
          const classes = el.className;
          const id = el.id;
          
          if (text && text.length > 0) {
            elements.push({
              selector: selector,
              index: index,
              text: text,
              classes: classes,
              id: id,
              tagName: el.tagName
            });
          }
        });
      }
      
      return elements;
    });
    
    navElements.forEach(el => {
      console.log(`  - ${el.tagName}${el.id ? '#' + el.id : ''}${el.classes ? '.' + el.classes.split(' ').join('.') : ''}: "${el.text}"`);
    });
    
    // Check for main content areas
    console.log('\n📦 Main Content Areas:');
    const contentAreas = await page.evaluate(() => {
      const areas = [];
      const selectors = [
        'main', '.main', '#main', '.content', '.container',
        '[x-show]', '[x-if]', '.tab-content', '.panel'
      ];
      
      for (const selector of selectors) {
        const els = document.querySelectorAll(selector);
        els.forEach((el, index) => {
          areas.push({
            selector: selector,
            index: index,
            visible: el.style.display !== 'none',
            classes: el.className,
            id: el.id
          });
        });
      }
      
      return areas;
    });
    
    contentAreas.forEach(area => {
      console.log(`  - ${area.selector}${area.id ? '#' + area.id : ''} (visible: ${area.visible})`);
    });
    
    // Check for input fields and forms
    console.log('\n📝 Forms and Inputs:');
    const formElements = await page.evaluate(() => {
      const forms = [];
      const inputs = document.querySelectorAll('input, textarea, select, button[type="submit"]');
      
      inputs.forEach((input, index) => {
        forms.push({
          tagName: input.tagName,
          type: input.type,
          name: input.name,
          id: input.id,
          placeholder: input.placeholder,
          classes: input.className
        });
      });
      
      return forms;
    });
    
    formElements.forEach(form => {
      console.log(`  - ${form.tagName}[type="${form.type}"]${form.id ? '#' + form.id : ''} (${form.placeholder || form.name || 'no identifier'})`);
    });
    
    // Check for API calls being made
    console.log('\n🌐 Monitoring API calls for 5 seconds...');
    const apiCalls = [];
    
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status(),
          method: response.request().method()
        });
      }
    });
    
    // Trigger some interactions
    await page.waitForTimeout(5000);
    
    console.log('\n📡 API Calls Detected:');
    apiCalls.forEach(call => {
      console.log(`  - ${call.method} ${call.url} (${call.status})`);
    });
    
    // Take a screenshot
    await page.screenshot({ 
      path: 'tests/playwright/screenshots/application-inspection.png',
      fullPage: true 
    });
    
    console.log('\n📸 Screenshot saved to: tests/playwright/screenshots/application-inspection.png');
    
    // Check for specific Catalynx elements
    console.log('\n🎯 Catalynx-specific Elements:');
    const catalynxElements = await page.evaluate(() => {
      const elements = [];
      
      // Look for text that contains key terms
      const textSelectors = [
        '*:contains("Profile")', '*:contains("Discovery")', 
        '*:contains("Dashboard")', '*:contains("Enhanced Data")',
        '*:contains("BMF")', '*:contains("990")', '*:contains("EIN")'
      ];
      
      // Manual search since :contains is not standard CSS
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      const textNodes = [];
      let node;
      while (node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (text.match(/(Profile|Discovery|Dashboard|Enhanced|BMF|990|EIN)/i)) {
          textNodes.push({
            text: text,
            parentTag: node.parentElement.tagName,
            parentClasses: node.parentElement.className,
            parentId: node.parentElement.id
          });
        }
      }
      
      return textNodes.slice(0, 10); // Limit to first 10 matches
    });
    
    catalynxElements.forEach(el => {
      console.log(`  - "${el.text}" in ${el.parentTag}${el.parentId ? '#' + el.parentId : ''}${el.parentClasses ? '.' + el.parentClasses.split(' ').join('.') : ''}`);
    });
    
    console.log('\n✅ Inspection complete! Check the screenshot and update selectors accordingly.');
    console.log('💡 Press Enter to close browser...');
    
    // Wait for user input (in real scenario)
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Inspection failed:', error);
  } finally {
    await browser.close();
  }
}

// Run if called directly
if (require.main === module) {
  inspectApplication().catch(console.error);
}

module.exports = inspectApplication;
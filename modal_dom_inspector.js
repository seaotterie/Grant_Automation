// Modal DOM Structure Inspector
// Run this in browser console when the modal is open to diagnose positioning issues

console.log("=== MODAL DOM STRUCTURE INSPECTOR ===");

// Find the modal elements
const modal = document.querySelector('[x-show="showProfileModal"]');
const flexContainer = document.querySelector('[style*="display: flex; flex-direction: column"]');
const footer = document.querySelector('[style*="background-color: yellow"]');
const debugText = document.querySelector('[style*="FOOTER v13"]') || document.querySelector('div:contains("FOOTER v13")');

console.log("\n1. ELEMENT LOCATIONS:");
console.log("Modal container:", modal);
console.log("Flex container:", flexContainer);
console.log("Footer element:", footer);
console.log("Debug text element:", debugText);

if (footer) {
    console.log("\n2. FOOTER HIERARCHY:");
    let current = footer;
    let level = 0;
    while (current && level < 10) {
        const tagInfo = current.tagName + (current.className ? '.' + current.className.split(' ').join('.') : '');
        const styleInfo = current.style.cssText ? ` [style="${current.style.cssText.substring(0, 50)}..."]` : '';
        console.log(`  ${level === 0 ? 'FOOTER' : 'Parent ' + level}: ${tagInfo}${styleInfo}`);
        current = current.parentElement;
        level++;
    }
}

if (flexContainer) {
    console.log("\n3. FLEXBOX CONTAINER CHILDREN:");
    Array.from(flexContainer.children).forEach((child, index) => {
        const tagInfo = child.tagName + (child.className ? '.' + child.className.split(' ').join('.') : '');
        const isFooter = child.style.backgroundColor === 'yellow' || child.querySelector('[style*="background-color: yellow"]');
        console.log(`  Child ${index}: ${tagInfo} ${isFooter ? '*** THIS IS THE FOOTER ***' : ''}`);
    });
}

console.log("\n4. FOOTER POSITION CHECK:");
if (footer && flexContainer) {
    const isDirectChild = footer.parentElement === flexContainer;
    console.log("Is footer direct child of flexbox container?", isDirectChild);

    if (!isDirectChild) {
        console.log("PROBLEM: Footer is not direct child of flexbox container!");
        console.log("Footer parent:", footer.parentElement.tagName, footer.parentElement.className);
        console.log("Expected parent:", flexContainer.tagName, flexContainer.className);
    } else {
        console.log("✓ Footer is correctly positioned as direct child");
    }
}

console.log("\n5. DOM PATH ANALYSIS:");
if (footer) {
    const getPath = (element) => {
        const path = [];
        let current = element;
        while (current) {
            let selector = current.tagName.toLowerCase();
            if (current.id) selector += '#' + current.id;
            if (current.className) selector += '.' + current.className.split(' ').join('.');
            path.unshift(selector);
            current = current.parentElement;
        }
        return path.join(' > ');
    };
    console.log("Footer path:", getPath(footer));
}

console.log("\n6. VISUAL BOUNDS CHECK:");
if (footer && modal) {
    const footerRect = footer.getBoundingClientRect();
    const modalRect = modal.getBoundingClientRect();

    console.log("Footer bounds:", footerRect);
    console.log("Modal bounds:", modalRect);

    const isInsideModal = (
        footerRect.left >= modalRect.left &&
        footerRect.right <= modalRect.right &&
        footerRect.top >= modalRect.top &&
        footerRect.bottom <= modalRect.bottom
    );

    console.log("Is footer visually inside modal?", isInsideModal);

    if (!isInsideModal) {
        console.log("VISUAL PROBLEM: Footer appears outside modal bounds!");
        console.log("Footer is", footerRect.bottom - modalRect.bottom, "pixels below modal");
    }
}

console.log("\n=== END INSPECTION ===");
console.log("INSTRUCTIONS: Open the profile modal, then run this script to see the actual DOM structure");
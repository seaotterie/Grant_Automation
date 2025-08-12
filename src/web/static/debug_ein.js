// Debug script for EIN functionality
console.log('EIN Debug Script Loaded');

// Add EIN functionality to existing Alpine app if missing
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking EIN functionality...');
    
    // Add a global test function
    window.testEinButton = function() {
        console.log('Testing EIN button click...');
        
        // Find the Alpine.js app instance
        const app = document.querySelector('[x-data]');
        if (app && app._x_dataStack) {
            const data = app._x_dataStack[0];
            console.log('Alpine data found:', Object.keys(data));
            
            if ('showEinInput' in data) {
                console.log('showEinInput exists, setting to true');
                data.showEinInput = true;
            } else {
                console.log('showEinInput not found, adding it');
                data.showEinInput = true;
                data.einInput = '';
                data.einLookupInProgress = false;
                
                // Add the function if missing
                if (!data.createProfileFromEin) {
                    data.createProfileFromEin = async function() {
                        console.log('EIN creation function called');
                        alert('EIN function working! EIN: ' + this.einInput);
                    };
                }
            }
        } else {
            console.log('Alpine app not found');
        }
    };
    
    // Auto-test after 2 seconds
    setTimeout(() => {
        console.log('Running automatic EIN test...');
        
        // Try to find and click the EIN button
        const einButton = Array.from(document.querySelectorAll('button')).find(btn => 
            btn.textContent.includes('Create from EIN')
        );
        
        if (einButton) {
            console.log('EIN button found:', einButton);
            console.log('Button onclick:', einButton.getAttribute('onclick'));
            console.log('Button @click:', einButton.getAttribute('@click'));
        } else {
            console.log('EIN button not found');
        }
        
    }, 2000);
});
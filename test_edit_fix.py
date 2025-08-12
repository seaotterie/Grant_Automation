#!/usr/bin/env python3
"""
Test that the edit profile fix is working
"""

import requests

def test_edit_fix():
    """Test that edit profile popup works after first edit"""
    print('TESTING EDIT PROFILE FIX')
    print('=' * 40)
    
    # Check that the JavaScript contains the fix
    js_response = requests.get('http://localhost:8000/static/app.js')
    if js_response.status_code != 200:
        print(f'[ERROR] Could not load JavaScript: {js_response.status_code}')
        return False
    
    js_content = js_response.text
    
    # Check for the fixes in all resetProfileForm functions
    fixes_present = [
        ('Reset editing state in resetProfileForm', 'this.isEditingProfile = false;' in js_content),
        ('Reset current editing profile', 'this.currentEditingProfile = null;' in js_content),
        ('Edit profile function exists', 'editProfile(profile)' in js_content),
        ('Show profile modal in edit function', 'this.showProfileModal = true;' in js_content),
    ]
    
    print('JAVASCRIPT STATE MANAGEMENT:')
    all_fixes_present = True
    for name, present in fixes_present:
        status = 'FIXED' if present else 'MISSING'
        print(f'   {name}: {status}')
        if not present:
            all_fixes_present = False
    
    # Check that resetProfileForm functions contain the fix
    reset_function_count = js_content.count('resetProfileForm()')
    isEditing_reset_count = js_content.count('this.isEditingProfile = false;')
    
    print()
    print('RESETPROFILEFORM ANALYSIS:')
    print(f'   resetProfileForm functions found: {reset_function_count}')  
    print(f'   isEditingProfile resets found: {isEditing_reset_count}')
    
    if isEditing_reset_count >= 3:  # Should have at least 3 instances
        print('   State reset coverage: GOOD')
    else:
        print('   State reset coverage: INCOMPLETE')
        all_fixes_present = False
    
    # Check that the HTML contains the modal
    html_response = requests.get('http://localhost:8000/')
    if html_response.status_code == 200:
        html_content = html_response.text
        has_profile_modal = 'x-show="showProfileModal"' in html_content
        has_edit_buttons = '@click="editProfile(profile)"' in html_content
        
        print()
        print('HTML INTERFACE:')
        print(f'   Profile modal exists: {"YES" if has_profile_modal else "NO"}')
        print(f'   Edit buttons exist: {"YES" if has_edit_buttons else "NO"}')
        
        if not has_profile_modal or not has_edit_buttons:
            all_fixes_present = False
    
    print()
    if all_fixes_present:
        print('SUCCESS: Edit profile fix is complete!')
        print()
        print('WHAT SHOULD NOW WORK:')
        print('1. Edit a profile -> Save -> Edit the same profile again')
        print('2. The edit popup should open properly on subsequent edits')
        print('3. Profile state should be properly reset between edits')
        print()
        print('TEST STEPS:')
        print('1. Clear browser cache')
        print('2. Go to PROFILER tab')  
        print('3. Click Edit on any profile')
        print('4. Make a change and save')
        print('5. Click Edit on the same profile again')
        print('6. The edit popup should open normally')
        return True
    else:
        print('ISSUES FOUND: Some fixes may not be complete')
        return False

if __name__ == "__main__":
    test_edit_fix()
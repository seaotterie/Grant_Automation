#!/usr/bin/env python3
"""
Check what's in the current index.html file
"""

from pathlib import Path

def check_current_index():
    """Check current index.html content"""
    html_file = Path('src/web/static/index.html')
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f'CURRENT INDEX.HTML ANALYSIS')
    print(f'=' * 50)
    print(f'File size: {len(content)} characters')
    print()
    
    # Check for discovery features
    features = [
        ('Discovery Column Header', 'Discovery</th>'),
        ('Radio Button Input', 'type="radio"'),
        ('Profile Selection Check', 'selectedDiscoveryProfile?.profile_id === profile.profile_id'),
        ('Discovery Status Function', 'getDiscoveryStatusClass'),
        ('Profile Selection Method', 'selectProfileForDiscovery'),
        ('Discovery Page Section', 'Selected Profile for Discovery'),
        ('Profile Navigation Fix', "this.switchStage('profiler')"),
        ('Delete Dialog Variable', 'showDeleteConfirmation'),
    ]
    
    print('DISCOVERY FEATURES CHECK:')
    print('-' * 30)
    for name, pattern in features:
        found = pattern in content
        status = "FOUND" if found else "MISSING"
        print(f'{name}: {status}')
    
    # Count occurrences
    print()
    print('FEATURE COUNTS:')
    print('-' * 30)
    print(f'Radio buttons: {content.count("type=\"radio\"")}')
    print(f'Discovery status calls: {content.count("getDiscoveryStatusClass")}')
    print(f'Profile selection calls: {content.count("selectProfileForDiscovery")}')
    print(f'switchStage calls: {content.count("switchStage")}')
    
    # Check for Alpine.js initialization
    print()
    print('ALPINE.JS CHECK:')
    print('-' * 30)
    
    import re
    x_data_matches = re.findall(r'x-data="([^"]*)"', content)
    print(f'x-data attributes: {len(x_data_matches)}')
    if x_data_matches:
        print(f'First x-data: {x_data_matches[0]}')
    
    # Look for showDeleteConfirmation initialization
    if 'showDeleteConfirmation:' in content:
        print('showDeleteConfirmation initialization found in HTML')
    else:
        print('showDeleteConfirmation initialization NOT found in HTML')

if __name__ == "__main__":
    check_current_index()
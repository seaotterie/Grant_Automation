#!/usr/bin/env python3
"""
Debug script to compare what's in the HTML file vs what's being served
"""

import requests
from pathlib import Path
import re

def debug_html_serving():
    """Compare file content vs served content"""
    print("DEBUGGING HTML SERVING")
    print("=" * 60)
    
    # Read the actual file content
    html_file_path = Path("src/web/static/index.html")
    
    if not html_file_path.exists():
        print(f"[ERROR] HTML file not found: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    print(f"HTML file size: {len(file_content)} characters")
    
    # Get served content
    try:
        response = requests.get("http://localhost:8000/")
        served_content = response.text
        print(f"Served content size: {len(served_content)} characters")
        
        if len(file_content) == len(served_content):
            print("[OK] File and served content are same size")
        else:
            print(f"[WARNING] Size difference: {abs(len(file_content) - len(served_content))} characters")
            
    except Exception as e:
        print(f"[ERROR] Could not fetch served content: {e}")
        return
    
    print("\n1. KEY DISCOVERY FEATURES CHECK")
    print("-" * 40)
    
    discovery_features = [
        ('Discovery Column Header', 'Discovery</th>'),
        ('Radio Button Input', 'type="radio"'),
        ('Selected Profile Check', 'selectedDiscoveryProfile?.profile_id === profile.profile_id'),
        ('Discovery Status Function', 'getDiscoveryStatusClass('),
        ('Profile Selection Method', 'selectProfileForDiscovery('),
        ('Discovery Page Section', 'Selected Profile for Discovery'),
        ('Profile Navigation Fix', "this.switchStage('profiler')"),
        ('Delete Dialog Variable', 'showDeleteConfirmation'),
    ]
    
    print("Feature Analysis (FILE vs SERVED):")
    for name, pattern in discovery_features:
        in_file = pattern in file_content
        in_served = pattern in served_content
        
        if in_file and in_served:
            status = "[OK]"
        elif in_file and not in_served:
            status = "[ISSUE] In file but NOT served"
        elif not in_file and in_served:
            status = "[STRANGE] Not in file but IS served"
        else:
            status = "[MISSING] Not in file or served"
            
        print(f"  {status} {name}")
    
    print("\n2. DELETE DIALOG INITIALIZATION DEBUG")
    print("-" * 40)
    
    # Look for Alpine.js initialization
    alpine_pattern = r'x-data="([^"]*)"'
    alpine_matches_file = re.findall(alpine_pattern, file_content)
    alpine_matches_served = re.findall(alpine_pattern, served_content)
    
    print(f"Alpine x-data in file: {len(alpine_matches_file)} matches")
    print(f"Alpine x-data served: {len(alpine_matches_served)} matches")
    
    if alpine_matches_file:
        print(f"First x-data in file: {alpine_matches_file[0][:100]}...")
    if alpine_matches_served:
        print(f"First x-data served: {alpine_matches_served[0][:100]}...")
    
    # Look for showDeleteConfirmation initialization
    delete_init_patterns = [
        r'showDeleteConfirmation:\s*false',
        r'showDeleteConfirmation:\s*true'
    ]
    
    for pattern in delete_init_patterns:
        file_matches = re.findall(pattern, file_content, re.IGNORECASE)
        served_matches = re.findall(pattern, served_content, re.IGNORECASE)
        
        if file_matches or served_matches:
            print(f"Delete confirmation init: File={len(file_matches)}, Served={len(served_matches)}")
            if file_matches:
                print(f"  File: {file_matches[0]}")
            if served_matches:
                print(f"  Served: {served_matches[0]}")
    
    print("\n3. FILE MODIFICATION TIME")
    print("-" * 40)
    
    import time
    mtime = html_file_path.stat().st_mtime
    readable_time = time.ctime(mtime)
    print(f"index.html last modified: {readable_time}")
    
    # Check app.js modification time too
    js_file_path = Path("src/web/static/app.js")
    if js_file_path.exists():
        js_mtime = js_file_path.stat().st_mtime
        js_readable_time = time.ctime(js_mtime)
        print(f"app.js last modified: {js_readable_time}")
    
    print("\n4. CONTENT HASH COMPARISON")
    print("-" * 40)
    
    import hashlib
    file_hash = hashlib.md5(file_content.encode()).hexdigest()
    served_hash = hashlib.md5(served_content.encode()).hexdigest()
    
    print(f"File content hash: {file_hash}")
    print(f"Served content hash: {served_hash}")
    
    if file_hash == served_hash:
        print("[OK] File and served content are IDENTICAL")
    else:
        print("[ISSUE] File and served content are DIFFERENT!")
        
        # Try to find differences
        file_lines = file_content.split('\n')
        served_lines = served_content.split('\n')
        
        differences = []
        max_lines = max(len(file_lines), len(served_lines))
        
        for i in range(max_lines):
            file_line = file_lines[i] if i < len(file_lines) else ""
            served_line = served_lines[i] if i < len(served_lines) else ""
            
            if file_line != served_line:
                differences.append((i + 1, file_line[:100], served_line[:100]))
                if len(differences) >= 5:  # Show first 5 differences
                    break
        
        if differences:
            print("\nFirst few differences:")
            for line_num, file_snippet, served_snippet in differences:
                print(f"  Line {line_num}:")
                print(f"    File: {file_snippet}...")
                print(f"    Served: {served_snippet}...")

if __name__ == "__main__":
    debug_html_serving()
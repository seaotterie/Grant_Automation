#!/usr/bin/env python3
"""
Save the actual served content to see what's different
"""

import requests

def save_served_content():
    """Save the actual served content for comparison"""
    try:
        response = requests.get("http://localhost:8000/")
        served_content = response.text
        
        # Save to file for examination
        with open("actual_served_content.html", "w", encoding="utf-8") as f:
            f.write(served_content)
        
        print(f"Served content saved to actual_served_content.html")
        print(f"Size: {len(served_content)} characters")
        
        # Get the original file for comparison
        from pathlib import Path
        html_file_path = Path("src/web/static/index.html")
        
        if html_file_path.exists():
            with open(html_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            with open("original_file_content.html", "w", encoding="utf-8") as f:
                f.write(file_content)
            
            print(f"Original file saved to original_file_content.html")
            print(f"Size: {len(file_content)} characters")
            print(f"Difference: {len(served_content) - len(file_content)} characters")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    save_served_content()
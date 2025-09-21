#!/usr/bin/env python3
"""
Unicode Encoding Fix Utility v2
Applies improved UTF-8 encoding fixes with proper error handling.
"""

import os
import re
from pathlib import Path

def fix_unicode_encoding(file_path):
    """Fix Unicode encoding issues in a Python file with improved error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has the improved fix
        if 'hasattr(sys.stdout, \'buffer\')' in content:
            print(f"PASS {file_path.name} - Already has improved fix")
            return True

        # Find and replace old encoding fix
        old_encoding_pattern = r'# Configure UTF-8 encoding for Windows\nif os\.name == \'nt\':\s*\n\s*import codecs\s*\n\s*sys\.stdout = codecs\.getwriter\(\'utf-8\'\)\(sys\.stdout\.buffer, \'strict\'\)\s*\n\s*sys\.stderr = codecs\.getwriter\(\'utf-8\'\)\(sys\.stderr\.buffer, \'strict\'\)'

        new_encoding_fix = '''# Configure UTF-8 encoding for Windows
if os.name == 'nt':
    import codecs
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        # stdout/stderr may already be wrapped or redirected
        pass'''

        # Replace old fix with new fix
        new_content = re.sub(old_encoding_pattern, new_encoding_fix, content, flags=re.MULTILINE)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"FIXED {file_path.name} - Updated to improved encoding fix")
            return True
        else:
            print(f"SKIP {file_path.name} - No encoding fix found to update")
            return True

    except Exception as e:
        print(f"ERROR {file_path.name} - Error: {str(e)}")
        return False

def main():
    """Fix Unicode encoding in all test framework files"""
    print("Fixing Unicode Encoding Issues v2")
    print("=" * 50)

    # Define file patterns to fix
    file_patterns = [
        "test_framework/**/*.py",
        "tests/integrated/*.py"
    ]

    total_files = 0
    fixed_files = 0

    base_path = Path(__file__).parent

    for pattern in file_patterns:
        for file_path in base_path.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                total_files += 1
                if fix_unicode_encoding(file_path):
                    fixed_files += 1

    print("\n" + "=" * 50)
    print(f"Summary: {fixed_files}/{total_files} files processed")

    if fixed_files == total_files:
        print("SUCCESS: All Unicode encoding issues fixed!")
        return True
    else:
        print(f"WARNING: {total_files - fixed_files} files had issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
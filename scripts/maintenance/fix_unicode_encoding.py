#!/usr/bin/env python3
"""
Unicode Encoding Fix Utility
Applies UTF-8 encoding fixes to all test framework files to resolve Windows Unicode issues.
"""

import os
import re
from pathlib import Path

def fix_unicode_encoding(file_path):
    """Fix Unicode encoding issues in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the file already has encoding fix
        if 'Configure UTF-8 encoding for Windows' in content:
            print(f"PASS {file_path.name} - Already fixed")
            return True

        # Find the import section
        import_pattern = r'(import\s+\w+.*?(?:\n.*?)*?)(\n\n|\n(?=[^#\s]))'
        match = re.search(import_pattern, content, re.MULTILINE)

        if match:
            imports_section = match.group(1)

            # Add encoding fix after imports
            encoding_fix = """
# Configure UTF-8 encoding for Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
"""

            # Check if we need to add os import
            if 'import os' not in imports_section:
                imports_section += '\nimport os'

            # Check if we need to add sys import
            if 'import sys' not in imports_section:
                imports_section += '\nimport sys'

            # Replace the imports section with imports + encoding fix
            new_content = content.replace(
                match.group(1),
                imports_section + encoding_fix,
                1
            )

            # Write the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"FIXED {file_path.name} - Fixed Unicode encoding")
            return True
        else:
            print(f"WARN {file_path.name} - Could not find import section")
            return False

    except Exception as e:
        print(f"ERROR {file_path.name} - Error: {str(e)}")
        return False

def main():
    """Fix Unicode encoding in all test framework files"""
    print("Fixing Unicode Encoding Issues")
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
#!/usr/bin/env python3
"""
Final cleanup script to remove all old content between the placeholder sections and main closure.
Keeps only the simple stage placeholders inside the main container.
"""

def cleanup_html():
    html_file = r"C:\Users\cotte\Documents\Home\03_Dad\_Projects\2025\ClaudeCode\Grant_Automation\src\web\static\index.html"
    
    # Read the file
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines()
    
    # Find the bounds - keep content up to and including system-controls placeholder
    keep_until = -1
    main_closure = -1
    
    for i, line in enumerate(lines):
        if 'activeStage === \'system-controls\'' in line:
            # Find the end of this div (next few lines)
            for j in range(i + 1, min(i + 10, len(lines))):
                if '</div>' in lines[j] and 'text-center p-8' not in lines[j]:
                    keep_until = j
                    break
        elif line.strip() == '</main>':
            main_closure = i
            break
    
    if keep_until == -1 or main_closure == -1:
        print(f"Could not find bounds. keep_until={keep_until}, main_closure={main_closure}")
        return
    
    print(f"Found system-controls end at line {keep_until + 1}")
    print(f"Found main closure at line {main_closure + 1}")
    print(f"Will remove {main_closure - keep_until - 1} lines of old content")
    
    # Keep content up to system-controls end, then jump to main closure
    new_lines = lines[:keep_until + 1]
    new_lines.append("")
    new_lines.append("                <!-- OLD SECTIONS REMOVED - NOW INSIDE MAIN CONTAINER -->")
    new_lines.append("                <!-- END NEW WORKFLOW STAGE CONTENT SECTIONS      -->") 
    new_lines.append("                <!-- ============================================== -->")
    new_lines.append("")
    new_lines.extend(lines[main_closure:])
    
    # Write the cleaned content
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Cleanup complete! Removed {main_closure - keep_until - 1} lines of old content.")
    print("All stage sections now have simple placeholders inside main container.")

if __name__ == '__main__':
    cleanup_html()
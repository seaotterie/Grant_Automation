#!/usr/bin/env python3
"""
Migrate Tools to Use Shared Path Helper
Automatically updates 46+ tool files to use the new path_helper module
"""

import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# Pattern to match the old path management anti-pattern
OLD_PATTERN = re.compile(
    r'import sys\s+from pathlib import Path\s+'
    r'# Add src to path for imports\s+'
    r'project_root = Path\(__file__\)\.parent\.parent\.parent\.parent\s+'
    r'sys\.path\.insert\(0, str\(project_root\)\)',
    re.MULTILINE | re.DOTALL
)

# New import to replace it
NEW_IMPORT = """from src.core.tool_framework.path_helper import setup_tool_paths

# Setup paths for imports
project_root = setup_tool_paths(__file__)"""


def migrate_tool_file(file_path: Path) -> bool:
    """
    Migrate a single tool file to use the new path helper.

    Args:
        file_path: Path to the tool file

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text()

        # Check if already migrated
        if 'path_helper import setup_tool_paths' in content:
            logger.debug(f"  Already migrated: {file_path.relative_to(Path.cwd())}")
            return False

        # Check if file has the old pattern
        if 'sys.path.insert(0, str(project_root))' not in content:
            return False

        # Use regex to handle all variations of whitespace and line breaks
        pattern = re.compile(
            r'import sys\s+'
            r'from pathlib import Path\s+'
            r'(?:#.*\n\s*)?'  # Optional comment
            r'(?:# Add src to path for imports\s+)?'  # Optional comment
            r'project_root = Path\(__file__\)\.parent(?:\.parent){3,4}\s+'  # 3 or 4 .parent calls
            r'sys\.path\.insert\(0, str\(project_root\)\)',
            re.MULTILINE
        )

        new_content = pattern.sub(NEW_IMPORT, content)

        if new_content != content:
            file_path.write_text(new_content)
            logger.info(f"✓ Migrated: {file_path.relative_to(Path.cwd())}")
            return True
        else:
            logger.warning(f"⚠ Pattern found but not replaced in: {file_path.relative_to(Path.cwd())}")
            # Show the problematic section for debugging
            if 'sys.path.insert' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'sys.path.insert' in line:
                        context = '\n'.join(lines[max(0, i-5):i+2])
                        logger.debug(f"  Context:\n{context}")
                        break
            return False

    except Exception as e:
        logger.error(f"✗ Failed to migrate {file_path}: {e}")
        return False


def main():
    """Migrate all tool files to use shared path helper"""

    project_root = Path(__file__).parent.parent
    tools_dir = project_root / "tools"

    logger.info("=" * 70)
    logger.info("Tool Path Migration Script")
    logger.info("=" * 70)
    logger.info(f"Project root: {project_root}")
    logger.info(f"Tools directory: {tools_dir}")
    logger.info("")

    # Find all Python files in tools directory
    tool_files = list(tools_dir.glob("**/app/*.py"))

    logger.info(f"Found {len(tool_files)} Python files in tools/*/app/")
    logger.info("")

    migrated_count = 0
    for tool_file in tool_files:
        if migrate_tool_file(tool_file):
            migrated_count += 1

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"Migration complete: {migrated_count} files updated")
    logger.info("=" * 70)

    if migrated_count > 0:
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Review the changes: git diff")
        logger.info("2. Test the tools to ensure they still work")
        logger.info("3. Commit the changes: git add . && git commit -m 'Migrate tools to shared path helper'")
    else:
        logger.info("No files needed migration (all already using path_helper)")


if __name__ == "__main__":
    main()

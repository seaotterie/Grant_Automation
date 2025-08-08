#!/usr/bin/env python3
"""
Test script to debug processor registry scanning
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_registry_scan():
    print("Testing registry scan...")
    
    # Test auto registry scanning
    try:
        from src.processors.registry import get_auto_registry, register_all_processors
        
        # Get the registry and check what files it finds
        registry = get_auto_registry()
        
        processors_dir = Path(__file__).parent / "src" / "processors"
        print(f"Scanning directory: {processors_dir}")
        
        # Check if our new files exist
        export_file = processors_dir / "export" / "export_processor.py"
        report_file = processors_dir / "reports" / "report_generator.py"
        
        print(f"Export processor file exists: {export_file.exists()}")
        print(f"Report processor file exists: {report_file.exists()}")
        
        # Run the registration
        count = register_all_processors()
        print(f"Total processors registered: {count}")
        
        # Check workflow engine registry
        from src.core.workflow_engine import get_workflow_engine
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        print(f"Processors in engine registry: {len(processors)}")
        print(f"Processor names: {', '.join(processors)}")
        
        export_found = "export_processor" in processors
        report_found = "report_generator" in processors
        
        print(f"Export processor found: {export_found}")
        print(f"Report generator found: {report_found}")
        
        return export_found and report_found
        
    except Exception as e:
        print(f"Registry scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_registry_scan()
    if success:
        print("\n[OK] Registry scan tests passed!")
    else:
        print("\n[FAIL] Registry scan tests failed!")
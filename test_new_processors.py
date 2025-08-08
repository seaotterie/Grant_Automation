#!/usr/bin/env python3
"""
Test script to validate new export and report processors
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_new_processors():
    print("Testing new processors...")
    
    # Test export processor
    try:
        from src.processors.export.export_processor import ExportProcessor, register_processor
        print("[OK] Export processor imports successfully")
        
        # Test instantiation
        processor = ExportProcessor()
        print(f"[OK] Export processor instantiated: {processor.metadata.name}")
        
        # Test registration
        register_processor()
        print("[OK] Export processor registration successful")
        
    except Exception as e:
        print(f"[FAIL] Export processor failed: {e}")
        return False
    
    # Test report processor
    try:
        from src.processors.reports.report_generator import ReportGenerator, register_processor as register_report
        print("[OK] Report generator imports successfully")
        
        # Test instantiation
        processor = ReportGenerator()
        print(f"[OK] Report generator instantiated: {processor.metadata.name}")
        
        # Test registration
        register_report()
        print("[OK] Report generator registration successful")
        
    except Exception as e:
        print(f"[FAIL] Report generator failed: {e}")
        return False
    
    # Test workflow integration
    try:
        from src.core.workflow_engine import get_workflow_engine
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        
        export_found = "export_processor" in processors
        report_found = "report_generator" in processors
        
        print(f"[{'OK' if export_found else 'FAIL'}] Export processor in registry: {export_found}")
        print(f"[{'OK' if report_found else 'FAIL'}] Report generator in registry: {report_found}")
        print(f"Total processors: {len(processors)}")
        
        return export_found and report_found
        
    except Exception as e:
        print(f"[FAIL] Workflow engine integration failed: {e}")
        return False

if __name__ == "__main__":
    success = test_new_processors()
    if success:
        print("\n[OK] All new processor tests passed!")
    else:
        print("\n[FAIL] Some new processor tests failed!")
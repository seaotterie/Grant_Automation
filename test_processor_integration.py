#!/usr/bin/env python3
"""
Test script to validate processor integration
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.processors.registry import get_processor_summary
from src.core.workflow_engine import get_workflow_engine

def test_processor_integration():
    print("Testing processor integration...")
    
    # Test processor summary
    try:
        summary = get_processor_summary()
        print(f"[OK] Processor summary works: {summary['total_processors']} processors found")
        print(f"  Processors: {', '.join(summary['processor_names'])}")
    except Exception as e:
        print(f"[FAIL] Processor summary failed: {e}")
        return False
    
    # Test workflow engine
    try:
        engine = get_workflow_engine()
        processors = engine.registry.list_processors()
        print(f"[OK] Workflow engine works: {len(processors)} processors registered")
    except Exception as e:
        print(f"[FAIL] Workflow engine failed: {e}")
        return False
    
    print("\n[OK] All processor integration tests passed!")
    return True

if __name__ == "__main__":
    test_processor_integration()
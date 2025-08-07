#!/usr/bin/env python3
"""
Quick test to verify dashboard components are working.
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_dashboard_imports():
    """Test that all dashboard components can be imported."""
    try:
        # Test core imports
        from src.core.workflow_engine import WorkflowEngine
        from src.core.data_models import WorkflowConfig
        print("[PASS] Core components imported successfully")
        
        # Test workflow engine initialization
        engine = WorkflowEngine()
        print("[PASS] Workflow engine initialized")
        
        # Test configuration creation
        config = WorkflowConfig(
            target_ein="541669652",
            max_results=5,
            state_filter="VA"
        )
        print("[PASS] Workflow configuration created")
        
        # Test processor registration
        from src.processors.registry import register_all_processors
        count = register_all_processors()
        print(f"[PASS] {count} processors registered successfully")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Dashboard test failed: {e}")
        return False

def test_streamlit_components():
    """Test Streamlit-specific components."""
    try:
        import streamlit as st
        print(f"[PASS] Streamlit {st.__version__} available")
        
        import plotly
        print(f"[PASS] Plotly {plotly.__version__} available")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Streamlit components test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Dashboard Components...")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_dashboard_imports()
    print()
    
    # Test Streamlit
    success &= test_streamlit_components()
    print()
    
    if success:
        print("SUCCESS: All dashboard tests passed!")
        print()
        print("To launch dashboard:")
        print("   Windows: launch_dashboard.bat")
        print("   Manual:  grant-research-env\\Scripts\\streamlit run src\\dashboard\\app.py")
        print()
        print("Dashboard URL: http://localhost:8501")
    else:
        print("FAILED: Some dashboard tests failed")
        sys.exit(1)
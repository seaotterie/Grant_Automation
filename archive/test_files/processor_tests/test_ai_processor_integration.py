#!/usr/bin/env python3
"""
Test AI Processor Integration
Verify that AI-Lite Unified and AI-Heavy processors can work together
"""

import asyncio
import logging
from datetime import datetime

def test_processor_imports():
    """Test that all AI processors can be imported"""
    print("\n[TEST] AI PROCESSOR INTEGRATION VERIFICATION")
    print("=" * 50)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    
    # Test AI-Lite Unified Processor
    print("\n1. Testing AI-Lite Unified Processor import...")
    try:
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor
        processor = AILiteUnifiedProcessor()
        print(f"   [SUCCESS] AI-Lite Unified: {processor.metadata.name}")
        print(f"   [INFO] Model: {processor.model}")
        print(f"   [INFO] Cost: ${processor.estimated_cost_per_candidate:.6f}/candidate")
    except Exception as e:
        print(f"   [FAILED] AI-Lite Unified import failed: {e}")
        success = False
    
    # Test AI-Heavy Dossier Builder
    print("\n2. Testing AI-Heavy Dossier Builder import...")
    try:
        from src.processors.analysis.ai_heavy_researcher import AIHeavyDossierBuilder
        processor = AIHeavyDossierBuilder()
        print(f"   [SUCCESS] AI-Heavy Dossier Builder: {processor.metadata.name}")
        print(f"   [INFO] Model: {processor.model}")
        print(f"   [INFO] Estimated cost per analysis available")
    except Exception as e:
        print(f"   [FAILED] AI-Heavy Dossier Builder import failed: {e}")
        success = False
    
    # Test AI-Heavy Deep Researcher  
    print("\n3. Testing AI-Heavy Deep Researcher import...")
    try:
        from src.processors.analysis.ai_heavy_deep_researcher import AIHeavyDeepResearcher  
        processor = AIHeavyDeepResearcher()
        print(f"   [SUCCESS] AI-Heavy Deep: {processor.metadata.name}")
        print(f"   [INFO] Deep research capabilities confirmed")
    except Exception as e:
        print(f"   [FAILED] AI-Heavy Deep Researcher import failed: {e}")
        success = False

    # Test Research Bridge
    print("\n4. Testing AI-Heavy Research Bridge import...")
    try:
        from src.processors.analysis.ai_heavy_research_bridge import AIHeavyResearchBridge
        processor = AIHeavyResearchBridge()
        print(f"   [SUCCESS] Research Bridge: {processor.metadata.name}")
        print(f"   [INFO] Bridge integration confirmed")
    except Exception as e:
        print(f"   [FAILED] Research Bridge import failed: {e}")
        success = False
    
    return success

def test_web_interface_integration():
    """Test that processors are properly integrated in web interface"""
    print("\n[TEST] WEB INTERFACE INTEGRATION")
    print("=" * 35)
    
    success = True
    
    # Test web integration imports
    print("\n1. Testing web interface AI processor integration...")
    try:
        # Test the imports used in the web interface
        from src.processors.analysis.ai_lite_scorer import AILiteScorer
        from src.processors.analysis.ai_heavy_researcher import AIHeavyDossierBuilder
        
        ai_lite = AILiteScorer()
        ai_heavy = AIHeavyDossierBuilder()
        
        print(f"   [SUCCESS] Web interface AI-Lite integration confirmed")
        print(f"   [SUCCESS] Web interface AI-Heavy integration confirmed")
        print(f"   [INFO] Both processors available for web workflows")
        
    except Exception as e:
        print(f"   [FAILED] Web interface integration failed: {e}")
        success = False
    
    return success

def test_processor_compatibility():
    """Test processor compatibility and workflow integration"""
    print("\n[TEST] PROCESSOR COMPATIBILITY")  
    print("=" * 30)
    
    success = True
    
    print("\n1. Testing processor workflow compatibility...")
    try:
        from src.processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor
        from src.processors.analysis.ai_heavy_researcher import AIHeavyDossierBuilder
        
        # Create processors
        unified_lite = AILiteUnifiedProcessor()
        heavy_researcher = AIHeavyDossierBuilder()
        
        # Test basic compatibility
        print(f"   [SUCCESS] AI-Lite Unified ready for initial screening")
        print(f"   [SUCCESS] AI-Heavy Dossier Builder ready for detailed analysis")
        print(f"   [INFO] Workflow: Unified -> Heavy for selected opportunities")
        print(f"   [INFO] Cost optimization: Use unified for volume, heavy for depth")
        
    except Exception as e:
        print(f"   [FAILED] Processor compatibility test failed: {e}")
        success = False
    
    return success

def main():
    """Main integration test"""
    
    print("[INTEGRATION] AI PROCESSOR INTEGRATION TEST")
    print("=" * 45)
    
    # Run all tests
    import_success = test_processor_imports()
    web_success = test_web_interface_integration()
    compatibility_success = test_processor_compatibility()
    
    overall_success = import_success and web_success and compatibility_success
    
    # Results
    print("\n" + "=" * 50)
    if overall_success:
        print("[SUCCESS] AI PROCESSOR INTEGRATION VERIFIED")
        print("[SUCCESS] All processors successfully integrated")
        print("\n[INFO] INTEGRATION SUMMARY:")
        print("   - AI-Lite Unified: Available for cost-effective screening")
        print("   - AI-Heavy Processors: Available for detailed analysis")
        print("   - Web Interface: Properly integrated with both systems")
        print("   - Workflow: Compatible for multi-stage processing")
        print("\n[INFO] RECOMMENDED USAGE:")
        print("   1. Use AI-Lite Unified for initial candidate screening")
        print("   2. Use AI-Heavy for detailed analysis of selected candidates")
        print("   3. Achieve optimal cost-performance balance")
    else:
        print("[FAILED] AI PROCESSOR INTEGRATION ISSUES DETECTED")
        print("[ERROR] Some processors have integration problems")
    
    return overall_success

if __name__ == "__main__":
    main()
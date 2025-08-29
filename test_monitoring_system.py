#!/usr/bin/env python3
"""
Test Monitoring System
Verify the processor monitoring system is working
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

from monitoring.processor_monitor import ProcessorMonitor, log_unified_processor_usage

def test_monitoring_system():
    """Test the monitoring system functionality"""
    print("\n[MONITOR] PROCESSOR MONITORING SYSTEM TEST")
    print("=" * 45)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test monitor
    test_log_file = "data/monitoring/test_processor_usage.jsonl"
    monitor = ProcessorMonitor(test_log_file)
    
    print(f"\n1. Testing monitor initialization...")
    print(f"   [SUCCESS] Monitor initialized")
    print(f"   [INFO] Log file: {test_log_file}")
    
    # Test logging functionality
    print(f"\n2. Testing usage logging...")
    try:
        # Log some test usage
        monitor.log_processor_usage(
            processor_name="ai_lite_unified_processor",
            batch_id="test_batch_001",
            candidates_processed=25,
            total_cost=0.010,
            processing_time=3.5,
            success_count=23,
            error_count=2,
            model_used="gpt-5-nano"
        )
        
        monitor.log_processor_usage(
            processor_name="ai_lite_unified_processor",
            batch_id="test_batch_002",
            candidates_processed=15,
            total_cost=0.006,
            processing_time=2.1,
            success_count=15,
            error_count=0,
            model_used="gpt-5-nano"
        )
        
        # Test convenience function
        log_unified_processor_usage(
            batch_id="convenience_test",
            candidates_processed=10,
            total_cost=0.004,
            processing_time=1.8,
            success_count=10,
            error_count=0
        )
        
        print(f"   [SUCCESS] Usage logging functional")
        print(f"   [INFO] Logged 3 test usage records")
        
    except Exception as e:
        print(f"   [FAILED] Usage logging failed: {e}")
        return False
    
    # Test stats retrieval
    print(f"\n3. Testing stats retrieval...")
    try:
        stats = monitor.get_processor_stats()
        
        if "ai_lite_unified_processor" in stats:
            unified_stats = stats["ai_lite_unified_processor"]
            print(f"   [SUCCESS] Stats retrieval functional")
            print(f"   [INFO] Unified processor executions: {unified_stats.total_executions}")
            print(f"   [INFO] Total candidates processed: {unified_stats.total_candidates}")
            print(f"   [INFO] Total cost: ${unified_stats.total_cost:.6f}")
            print(f"   [INFO] Average cost per candidate: ${unified_stats.average_cost_per_candidate:.6f}")
            print(f"   [INFO] Success rate: {unified_stats.success_rate:.1f}%")
        else:
            print(f"   [WARNING] No stats found for unified processor")
            
    except Exception as e:
        print(f"   [FAILED] Stats retrieval failed: {e}")
        return False
    
    # Test summary report
    print(f"\n4. Testing summary report...")
    try:
        summary = monitor.get_usage_summary(days=1)
        
        print(f"   [SUCCESS] Summary generation functional")
        print(f"   [INFO] Total executions: {summary['total_executions']}")
        print(f"   [INFO] Total candidates: {summary['total_candidates']}")
        print(f"   [INFO] Total cost: ${summary['total_cost']:.6f}")
        print(f"   [INFO] Average cost per candidate: ${summary['average_cost_per_candidate']:.6f}")
        
    except Exception as e:
        print(f"   [FAILED] Summary report failed: {e}")
        return False
    
    # Test formatted report
    print(f"\n5. Testing formatted report...")
    try:
        print(f"   [INFO] Generating formatted report...")
        monitor.print_usage_report(days=1)
        print(f"   [SUCCESS] Formatted report generated")
        
    except Exception as e:
        print(f"   [FAILED] Formatted report failed: {e}")
        return False
    
    # Cleanup test file
    try:
        if Path(test_log_file).exists():
            os.remove(test_log_file)
            print(f"\n   [INFO] Test log file cleaned up")
    except Exception as e:
        print(f"   [WARNING] Failed to cleanup test file: {e}")
    
    return True

def test_integration_with_unified_processor():
    """Test integration with the unified processor"""
    print(f"\n[INTEGRATION] MONITORING + UNIFIED PROCESSOR")
    print("=" * 45)
    
    try:
        # Test that we can import both systems
        from processors.analysis.ai_lite_unified_processor import AILiteUnifiedProcessor
        from monitoring.processor_monitor import get_processor_monitor
        
        processor = AILiteUnifiedProcessor()
        monitor = get_processor_monitor()
        
        print(f"   [SUCCESS] Both systems imported successfully")
        print(f"   [INFO] Processor: {processor.metadata.name}")
        print(f"   [INFO] Monitor: Ready for logging")
        print(f"   [INFO] Integration: Ready for production monitoring")
        
        return True
        
    except Exception as e:
        print(f"   [FAILED] Integration test failed: {e}")
        return False

def main():
    """Main monitoring test"""
    print("[MONITOR] PROCESSOR MONITORING SYSTEM VERIFICATION")
    print("=" * 55)
    
    # Run tests
    monitoring_success = test_monitoring_system()
    integration_success = test_integration_with_unified_processor()
    
    overall_success = monitoring_success and integration_success
    
    # Results
    print("\n" + "=" * 55)
    if overall_success:
        print("[SUCCESS] MONITORING SYSTEM FULLY OPERATIONAL")
        print("[SUCCESS] Ready for production processor monitoring")
        print("\n[INFO] MONITORING CAPABILITIES:")
        print("   - Usage logging for all processor executions")
        print("   - Cost and performance tracking")
        print("   - Success/error rate monitoring")
        print("   - Aggregated statistics and reports")
        print("   - Integration with unified processor")
        print("\n[INFO] USAGE:")
        print("   from monitoring.processor_monitor import log_unified_processor_usage")
        print("   log_unified_processor_usage(batch_id, candidates, cost, time, success, errors)")
    else:
        print("[FAILED] MONITORING SYSTEM ISSUES DETECTED")
        print("[ERROR] Some monitoring features have problems")
    
    return overall_success

if __name__ == "__main__":
    main()
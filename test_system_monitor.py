#!/usr/bin/env python3
"""
Test script for the System Monitor
Demonstrates comprehensive system monitoring and analytics capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.system_monitor import get_system_monitor


async def main():
    """Run comprehensive system monitoring tests."""
    print("Starting System Monitoring Analysis")
    print("=" * 60)
    
    # Initialize monitor
    monitor = get_system_monitor()
    
    try:
        # Test 1: System Health Overview
        print("\n1. SYSTEM HEALTH OVERVIEW")
        print("-" * 40)
        health = await monitor.get_system_health()
        
        print(f"Overall Health: {health['overall_health'].upper()}")
        print(f"Timestamp: {health['timestamp']}")
        
        metrics = health['metrics']
        print(f"\nCurrent Metrics:")
        print(f"  CPU Usage: {metrics['cpu_percent']:.1f}%")
        print(f"  Memory Usage: {metrics['memory_percent']:.1f}% ({metrics['memory_used_gb']:.1f}GB / {metrics['memory_total_gb']:.1f}GB)")
        print(f"  Disk Usage: {metrics['disk_percent']:.1f}% ({metrics['disk_used_gb']:.1f}GB / {metrics['disk_total_gb']:.1f}GB)")
        print(f"  Active Processes: {metrics['active_processes']}")
        if metrics['response_time_ms']:
            print(f"  API Response Time: {metrics['response_time_ms']:.1f}ms")
        
        # Processor health
        processor_health = health['processor_health']
        if processor_health:
            print(f"\nProcessor Health ({len(processor_health)} processors):")
            for name, health_data in list(processor_health.items())[:5]:  # Show first 5
                print(f"  {name}: {health_data['status'].upper()} (Success: {health_data['success_rate']:.1%})")
        
        # Active alerts
        active_alerts = health['active_alerts']
        if active_alerts:
            print(f"\nActive Alerts ({len(active_alerts)}):")
            for alert in active_alerts[:3]:  # Show first 3
                print(f"  {alert['level'].upper()}: {alert['title']}")
        else:
            print("\nNo active alerts")
        
        # Recommendations
        recommendations = health['recommendations']
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"  - {rec}")
        
        # Test 2: Usage Analytics
        print("\n\n2. USAGE ANALYTICS (Last 7 Days)")
        print("-" * 40)
        analytics = await monitor.get_usage_analytics(days=7)
        
        print(f"Period: {analytics.period_start[:10]} to {analytics.period_end[:10]}")
        print(f"Total Discoveries: {analytics.total_discoveries}")
        print(f"Profiles Created: {analytics.profiles_created}")
        print(f"Opportunities Found: {analytics.opportunities_found}")
        print(f"Average Session Duration: {analytics.avg_session_duration:.1f} minutes")
        print(f"Error Rate: {analytics.error_rate:.1%}")
        
        if analytics.top_processors:
            print(f"\nTop Processors:")
            for i, processor in enumerate(analytics.top_processors[:5], 1):
                print(f"  {i}. {processor['name']}: {processor['usage_count']} runs (avg {processor['avg_duration']:.1f}s)")
        
        if analytics.peak_usage_hours:
            hours_str = ", ".join([f"{h}:00" for h in analytics.peak_usage_hours[:6]])
            print(f"\nPeak Usage Hours: {hours_str}")
        
        # Test 3: Performance Report
        print("\n\n3. PERFORMANCE REPORT (Last 24 Hours)")
        print("-" * 40)
        performance = await monitor.get_performance_report(hours=24)
        
        if 'error' in performance:
            print(performance['error'])
        else:
            print(f"Report Period: {performance['period']}")
            print(f"Metrics Collected: {performance['metrics_count']}")
            
            # Performance stats
            stats = performance['performance_stats']
            print(f"\nPerformance Statistics:")
            print(f"  CPU - Current: {stats['cpu']['current']:.1f}%, Average: {stats['cpu']['average']:.1f}%, Peak: {stats['cpu']['max']:.1f}%")
            print(f"  Memory - Current: {stats['memory']['current']:.1f}%, Average: {stats['memory']['average']:.1f}%, Peak: {stats['memory']['max']:.1f}%")
            print(f"  Disk - Current: {stats['disk']['current']:.1f}%, Average: {stats['disk']['average']:.1f}%, Peak: {stats['disk']['max']:.1f}%")
            
            # Trends
            if 'trends' in performance:
                trends = performance['trends']
                print(f"\nTrends:")
                print(f"  CPU Trend: {trends['cpu_trend']} ({trends['cpu_change']:.1f}% change)")
            
            # Alerts summary
            alerts_summary = performance['alerts_summary']
            print(f"\nAlerts Summary:")
            print(f"  Total: {alerts_summary['total_alerts']}")
            print(f"  Critical: {alerts_summary['critical_alerts']}")
            print(f"  Warnings: {alerts_summary['warning_alerts']}")
            print(f"  Resolved: {alerts_summary['resolved_alerts']}")
            
            # Recommendations
            if performance['recommendations']:
                print(f"\nRecommendations:")
                for rec in performance['recommendations']:
                    print(f"  - {rec}")
        
        # Test 4: Brief Monitoring Demo
        print("\n\n4. BRIEF MONITORING DEMONSTRATION")
        print("-" * 40)
        print("Running 10-second monitoring demo...")
        
        # Start monitoring for a brief period
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # Let it run for 10 seconds
        await asyncio.sleep(10)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        monitoring_task.cancel()
        
        # Get updated health after brief monitoring
        updated_health = await monitor.get_system_health()
        print(f"Updated Health Status: {updated_health['overall_health'].upper()}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SYSTEM MONITORING SUMMARY")
        print("-" * 40)
        
        overall_status = updated_health['overall_health']
        total_discoveries = analytics.total_discoveries
        error_rate = analytics.error_rate
        active_alerts_count = len(updated_health['active_alerts'])
        
        print(f"System Status: {overall_status.upper()}")
        print(f"Recent Activity: {total_discoveries} discoveries in last 7 days")
        print(f"System Reliability: {(1-error_rate):.1%} success rate")
        print(f"Active Monitoring Alerts: {active_alerts_count}")
        
        # Health assessment
        if overall_status == "excellent":
            print("\nAssessment: System is operating at peak performance")
        elif overall_status == "good":
            print("\nAssessment: System performance is within acceptable ranges")
        elif overall_status == "warning":
            print("\nAssessment: Some performance issues detected - monitoring recommended")
        else:
            print("\nAssessment: Critical issues detected - immediate attention required")
        
        # Save comprehensive monitoring report
        output_file = Path("system_monitoring_report.json")
        report_data = {
            "generated_at": updated_health['timestamp'],
            "health_overview": updated_health,
            "usage_analytics": {
                "period_days": 7,
                "total_discoveries": analytics.total_discoveries,
                "profiles_created": analytics.profiles_created,
                "opportunities_found": analytics.opportunities_found,
                "error_rate": analytics.error_rate,
                "top_processors": analytics.top_processors
            },
            "performance_report": performance,
            "summary": {
                "overall_status": overall_status,
                "reliability_score": 1 - error_rate,
                "active_alerts": active_alerts_count,
                "monitoring_period": "24 hours"
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed monitoring report saved to: {output_file}")
        print("\nSystem monitoring analysis complete!")
        
    except Exception as e:
        print(f"Error during system monitoring: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
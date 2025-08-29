"""
Simple Processor Usage Monitor
Track usage and performance of the AI-Lite Unified Processor
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class ProcessorUsageRecord:
    """Record of processor usage"""
    timestamp: str
    processor_name: str
    batch_id: str
    candidates_processed: int
    total_cost: float
    processing_time: float
    success_count: int
    error_count: int
    model_used: str

@dataclass
class ProcessorStats:
    """Aggregated processor statistics"""
    processor_name: str
    total_executions: int
    total_candidates: int
    total_cost: float
    total_processing_time: float
    average_cost_per_candidate: float
    average_processing_time: float
    success_rate: float
    last_used: str

class ProcessorMonitor:
    """Simple monitoring system for processor usage"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up log file path
        if log_file:
            self.log_file = Path(log_file)
        else:
            self.log_file = Path("data/monitoring/processor_usage.jsonl")
        
        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Processor monitor initialized with log file: {self.log_file}")
    
    def log_processor_usage(
        self,
        processor_name: str,
        batch_id: str,
        candidates_processed: int,
        total_cost: float,
        processing_time: float,
        success_count: int,
        error_count: int,
        model_used: str = "unknown"
    ):
        """Log a processor usage record"""
        record = ProcessorUsageRecord(
            timestamp=datetime.now().isoformat(),
            processor_name=processor_name,
            batch_id=batch_id,
            candidates_processed=candidates_processed,
            total_cost=total_cost,
            processing_time=processing_time,
            success_count=success_count,
            error_count=error_count,
            model_used=model_used
        )
        
        try:
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(record)) + '\n')
            
            self.logger.info(f"Logged usage for {processor_name}: {candidates_processed} candidates, ${total_cost:.6f}")
            
        except Exception as e:
            self.logger.error(f"Failed to log processor usage: {e}")
    
    def get_processor_stats(self, processor_name: Optional[str] = None, days: int = 30) -> Dict[str, ProcessorStats]:
        """Get aggregated processor statistics"""
        stats = {}
        
        try:
            if not self.log_file.exists():
                return stats
            
            # Read usage records
            cutoff_time = datetime.now() - timedelta(days=days)
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record_data = json.loads(line.strip())
                        record_time = datetime.fromisoformat(record_data['timestamp'])
                        
                        # Skip old records
                        if record_time < cutoff_time:
                            continue
                        
                        # Filter by processor name if specified
                        proc_name = record_data['processor_name']
                        if processor_name and proc_name != processor_name:
                            continue
                        
                        # Initialize stats for this processor
                        if proc_name not in stats:
                            stats[proc_name] = {
                                'total_executions': 0,
                                'total_candidates': 0,
                                'total_cost': 0.0,
                                'total_processing_time': 0.0,
                                'total_success': 0,
                                'total_errors': 0,
                                'last_used': record_data['timestamp']
                            }
                        
                        # Update stats
                        proc_stats = stats[proc_name]
                        proc_stats['total_executions'] += 1
                        proc_stats['total_candidates'] += record_data['candidates_processed']
                        proc_stats['total_cost'] += record_data['total_cost']
                        proc_stats['total_processing_time'] += record_data['processing_time']
                        proc_stats['total_success'] += record_data['success_count']
                        proc_stats['total_errors'] += record_data['error_count']
                        
                        # Update last used
                        if record_data['timestamp'] > proc_stats['last_used']:
                            proc_stats['last_used'] = record_data['timestamp']
                            
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        self.logger.warning(f"Failed to parse record: {e}")
                        continue
            
            # Convert to ProcessorStats objects
            result = {}
            for proc_name, raw_stats in stats.items():
                total_processed = raw_stats['total_success'] + raw_stats['total_errors']
                
                result[proc_name] = ProcessorStats(
                    processor_name=proc_name,
                    total_executions=raw_stats['total_executions'],
                    total_candidates=raw_stats['total_candidates'],
                    total_cost=raw_stats['total_cost'],
                    total_processing_time=raw_stats['total_processing_time'],
                    average_cost_per_candidate=(
                        raw_stats['total_cost'] / raw_stats['total_candidates'] 
                        if raw_stats['total_candidates'] > 0 else 0.0
                    ),
                    average_processing_time=(
                        raw_stats['total_processing_time'] / raw_stats['total_executions']
                        if raw_stats['total_executions'] > 0 else 0.0
                    ),
                    success_rate=(
                        raw_stats['total_success'] / total_processed * 100 
                        if total_processed > 0 else 0.0
                    ),
                    last_used=raw_stats['last_used']
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get processor stats: {e}")
            return {}
    
    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get a summary of processor usage over the specified period"""
        stats = self.get_processor_stats(days=days)
        
        if not stats:
            return {
                'period_days': days,
                'total_processors': 0,
                'total_executions': 0,
                'total_candidates': 0,
                'total_cost': 0.0,
                'processors': {}
            }
        
        total_executions = sum(s.total_executions for s in stats.values())
        total_candidates = sum(s.total_candidates for s in stats.values())
        total_cost = sum(s.total_cost for s in stats.values())
        
        return {
            'period_days': days,
            'total_processors': len(stats),
            'total_executions': total_executions,
            'total_candidates': total_candidates,
            'total_cost': total_cost,
            'average_cost_per_candidate': total_cost / total_candidates if total_candidates > 0 else 0.0,
            'processors': {name: asdict(stat) for name, stat in stats.items()}
        }
    
    def print_usage_report(self, days: int = 7):
        """Print a formatted usage report"""
        summary = self.get_usage_summary(days)
        
        print(f"\n[MONITOR] PROCESSOR USAGE REPORT ({days} days)")
        print("=" * 50)
        
        if summary['total_processors'] == 0:
            print("No processor usage recorded in the specified period.")
            return
        
        print(f"Period: Last {days} days")
        print(f"Total Processors: {summary['total_processors']}")
        print(f"Total Executions: {summary['total_executions']}")
        print(f"Total Candidates: {summary['total_candidates']}")
        print(f"Total Cost: ${summary['total_cost']:.6f}")
        print(f"Average Cost/Candidate: ${summary['average_cost_per_candidate']:.6f}")
        
        print(f"\n[INFO] PROCESSOR DETAILS:")
        for name, stats in summary['processors'].items():
            print(f"\n{name}:")
            print(f"  Executions: {stats['total_executions']}")
            print(f"  Candidates: {stats['total_candidates']}")
            print(f"  Cost: ${stats['total_cost']:.6f}")
            print(f"  Avg Cost/Candidate: ${stats['average_cost_per_candidate']:.6f}")
            print(f"  Avg Processing Time: {stats['average_processing_time']:.2f}s")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Last Used: {stats['last_used']}")

# Global monitor instance
_global_monitor: Optional[ProcessorMonitor] = None

def get_processor_monitor() -> ProcessorMonitor:
    """Get the global processor monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ProcessorMonitor()
    return _global_monitor

def log_unified_processor_usage(
    batch_id: str,
    candidates_processed: int,
    total_cost: float,
    processing_time: float,
    success_count: int,
    error_count: int
):
    """Convenience function to log AI-Lite Unified Processor usage"""
    monitor = get_processor_monitor()
    monitor.log_processor_usage(
        processor_name="ai_lite_unified_processor",
        batch_id=batch_id,
        candidates_processed=candidates_processed,
        total_cost=total_cost,
        processing_time=processing_time,
        success_count=success_count,
        error_count=error_count,
        model_used="gpt-5-nano"
    )

if __name__ == "__main__":
    # Demo usage
    monitor = ProcessorMonitor()
    
    # Simulate some usage
    monitor.log_processor_usage(
        processor_name="ai_lite_unified_processor",
        batch_id="demo_test",
        candidates_processed=10,
        total_cost=0.004,
        processing_time=2.5,
        success_count=9,
        error_count=1,
        model_used="gpt-5-nano"
    )
    
    # Print report
    monitor.print_usage_report(days=30)
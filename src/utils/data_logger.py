"""
Comprehensive Data Logger (Kermit-style) for Stage Management Debugging
Provides detailed observability into data flow: Database → Backend → Frontend → UI
"""

import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict, Counter

class DataLogger:
    """Advanced data logger with structured output and cross-system tracking"""
    
    def __init__(self, name: str = "DataLogger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with custom formatting
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Custom formatter for structured output
            formatter = logging.Formatter(
                '[DATA] %(asctime)s [%(name)s] %(levelname)s: %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Internal tracking
        self.session_id = f"session_{int(time.time())}"
        self.operation_count = 0
        self.stage_transitions = []
        self.performance_metrics = {}
        
    def operation_start(self, operation: str, context: Dict[str, Any] = None) -> str:
        """Start tracking a data flow operation"""
        self.operation_count += 1
        op_id = f"{self.session_id}_op_{self.operation_count}"
        
        start_time = time.time()
        self.performance_metrics[op_id] = {
            'operation': operation,
            'start_time': start_time,
            'context': context or {}
        }
        
        self.logger.info(f"START [{op_id}] {operation}")
        if context:
            self.logger.info(f"   Context: {self._format_dict(context)}")
        
        return op_id
    
    def operation_end(self, op_id: str, result: Any = None):
        """End tracking a data flow operation"""
        if op_id in self.performance_metrics:
            end_time = time.time()
            duration = end_time - self.performance_metrics[op_id]['start_time']
            operation = self.performance_metrics[op_id]['operation']
            
            self.logger.info(f"END   [{op_id}] {operation} ({duration:.3f}s)")
            if result is not None:
                if isinstance(result, (list, dict)):
                    self.logger.info(f"   Result: {self._format_data_summary(result)}")
                else:
                    self.logger.info(f"   Result: {result}")
            
            self.performance_metrics[op_id]['end_time'] = end_time
            self.performance_metrics[op_id]['duration'] = duration
            self.performance_metrics[op_id]['result'] = result
    
    def log_stage_data(self, source: str, data: Union[List[Dict], Dict], context: str = ""):
        """Log stage distribution and data quality"""
        self.logger.info(f"STAGE DATA [{source}] {context}")
        
        if isinstance(data, list):
            # Analyze stage distribution
            stage_counts = self._analyze_stages(data)
            total_items = len(data)
            
            self.logger.info(f"   Total Items: {total_items}")
            self.logger.info(f"   Stage Breakdown:")
            for stage, count in sorted(stage_counts.items()):
                percentage = (count / total_items * 100) if total_items > 0 else 0
                self.logger.info(f"      - {stage}: {count} ({percentage:.1f}%)")
            
            # Data quality checks
            self._log_data_quality(data)
            
        elif isinstance(data, dict):
            self.logger.info(f"   Single Item: {self._format_dict(data)}")
    
    def log_filter_operation(self, filter_name: str, input_count: int, output_count: int, 
                           filter_criteria: Dict[str, Any] = None):
        """Log filtering operations"""
        percentage_kept = (output_count / input_count * 100) if input_count > 0 else 0
        
        self.logger.info(f"FILTER [{filter_name}] {input_count} -> {output_count} ({percentage_kept:.1f}% kept)")
        if filter_criteria:
            self.logger.info(f"   Criteria: {self._format_dict(filter_criteria)}")
    
    def log_api_request(self, endpoint: str, params: Dict[str, Any] = None, 
                       response_data: Any = None):
        """Log API request and response"""
        self.logger.info(f"API REQUEST: {endpoint}")
        if params:
            self.logger.info(f"   Params: {self._format_dict(params)}")
        if response_data:
            self.logger.info(f"   Response: {self._format_data_summary(response_data)}")
    
    def log_frontend_computed(self, computed_name: str, input_size: int, 
                            output_size: int, execution_time: float = None):
        """Log frontend computed property execution"""
        self.logger.info(f"COMPUTED [{computed_name}] {input_size} -> {output_size}")
        if execution_time:
            self.logger.info(f"   Execution: {execution_time:.3f}s")
    
    def log_stage_transition(self, opportunity_id: str, from_stage: str, 
                           to_stage: str, context: str = ""):
        """Log stage transitions for promotion/demotion"""
        transition = {
            'timestamp': datetime.now().isoformat(),
            'opportunity_id': opportunity_id,
            'from_stage': from_stage,
            'to_stage': to_stage,
            'context': context
        }
        self.stage_transitions.append(transition)
        
        self.logger.info(f"STAGE TRANSITION: {opportunity_id}")
        self.logger.info(f"   {from_stage} -> {to_stage}")
        if context:
            self.logger.info(f"   Context: {context}")
    
    def log_error(self, error: Exception, context: str = "", data: Any = None):
        """Log errors with context"""
        self.logger.error(f"ERROR: {context}")
        self.logger.error(f"   Exception: {str(error)}")
        if data:
            self.logger.error(f"   Data: {self._format_data_summary(data)}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current logging session"""
        return {
            'session_id': self.session_id,
            'operation_count': self.operation_count,
            'stage_transitions': len(self.stage_transitions),
            'performance_metrics': {
                op_id: {
                    'operation': metrics['operation'],
                    'duration': metrics.get('duration', 'in_progress')
                }
                for op_id, metrics in self.performance_metrics.items()
            }
        }
    
    def _analyze_stages(self, data: List[Dict]) -> Dict[str, int]:
        """Analyze stage distribution in data"""
        stage_counts = Counter()
        
        for item in data:
            # Check multiple possible stage fields
            stage = (item.get('funnel_stage') or 
                    item.get('current_stage') or 
                    item.get('pipeline_stage') or 
                    item.get('stage') or 
                    'unknown')
            stage_counts[stage] += 1
        
        return dict(stage_counts)
    
    def _log_data_quality(self, data: List[Dict]):
        """Log data quality metrics"""
        if not data:
            return
        
        # Check for missing required fields
        required_fields = ['opportunity_id', 'organization_name', 'funnel_stage']
        missing_counts = Counter()
        
        for item in data:
            for field in required_fields:
                if not item.get(field):
                    missing_counts[field] += 1
        
        if missing_counts:
            self.logger.warning(f"   WARNING Missing Fields:")
            for field, count in missing_counts.items():
                self.logger.warning(f"      - {field}: {count} items missing")
    
    def _format_dict(self, d: Dict, max_items: int = 3) -> str:
        """Format dictionary for logging"""
        if len(d) <= max_items:
            return str(d)
        else:
            items = list(d.items())[:max_items]
            return f"{dict(items)} ... (+{len(d) - max_items} more)"
    
    def _format_data_summary(self, data: Any) -> str:
        """Format data summary for logging"""
        if isinstance(data, list):
            return f"[{len(data)} items]"
        elif isinstance(data, dict):
            if 'opportunities' in data and isinstance(data['opportunities'], list):
                return f"{{opportunities: [{len(data['opportunities'])} items], ...}}"
            else:
                return f"{{{len(data)} keys}}"
        else:
            return str(data)[:100] + ("..." if len(str(data)) > 100 else "")

# Global logger instance
stage_logger = DataLogger("StageManagement")

# Convenience functions for common use cases
def log_database_query(query_type: str, results: Any, context: str = ""):
    """Log database query results"""
    stage_logger.log_stage_data("DATABASE", results, f"{query_type} - {context}")

def log_api_endpoint(endpoint: str, params: Dict = None, response: Any = None):
    """Log API endpoint call"""
    stage_logger.log_api_request(endpoint, params, response)

def log_frontend_filter(filter_name: str, input_count: int, output_count: int, criteria: Dict = None):
    """Log frontend filtering operation"""
    stage_logger.log_filter_operation(filter_name, input_count, output_count, criteria)

def log_stage_change(opportunity_id: str, from_stage: str, to_stage: str, context: str = ""):
    """Log stage transition"""
    stage_logger.log_stage_transition(opportunity_id, from_stage, to_stage, context)

# Export main logger for direct use
__all__ = ['DataLogger', 'stage_logger', 'log_database_query', 'log_api_endpoint', 
           'log_frontend_filter', 'log_stage_change']
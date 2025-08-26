"""
Comprehensive Error Recovery Framework
Provides intelligent error classification, circuit breaker patterns, retry logic, and graceful degradation
"""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from functools import wraps
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Error categories for classification"""
    API_ERROR = "api_error"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    NETWORK = "network"
    VALIDATION = "validation"
    PROCESSING = "processing"
    STORAGE = "storage"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class RecoveryAction(str, Enum):
    """Available recovery actions"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    IGNORE = "ignore"

@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    timestamp: datetime = None
    source: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recovery_actions: List[RecoveryAction] = None
    user_message: Optional[str] = None
    support_reference: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.recovery_actions is None:
            self.recovery_actions = []

@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    failure_threshold: int = 5
    reset_timeout: int = 60  # seconds
    
class RetryPolicy:
    """Retry policy configuration"""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
            
        return delay

class ErrorClassifier:
    """Intelligent error classification system"""
    
    @staticmethod
    def classify_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Classify an error and determine appropriate recovery actions"""
        
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # API and HTTP errors
        if "rate limit" in error_str or "429" in error_str:
            return ErrorInfo(
                error_id=f"rate_limit_{int(time.time())}",
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                message=f"Rate limit exceeded: {error}",
                recovery_actions=[RecoveryAction.RETRY],
                user_message="Processing rate limit reached. Retrying automatically with delay.",
                context=context
            )
        
        if "authentication" in error_str or "401" in error_str or "unauthorized" in error_str:
            return ErrorInfo(
                error_id=f"auth_{int(time.time())}",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                message=f"Authentication failed: {error}",
                recovery_actions=[RecoveryAction.ESCALATE],
                user_message="Authentication error. Please check your API keys in Settings.",
                context=context
            )
        
        if "timeout" in error_str or error_type == "TimeoutError":
            return ErrorInfo(
                error_id=f"timeout_{int(time.time())}",
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                message=f"Operation timed out: {error}",
                recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                user_message="Operation timed out. Retrying with extended timeout.",
                context=context
            )
        
        if "network" in error_str or "connection" in error_str or error_type in ["ConnectionError", "NetworkError"]:
            return ErrorInfo(
                error_id=f"network_{int(time.time())}",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"Network error: {error}",
                recovery_actions=[RecoveryAction.RETRY],
                user_message="Network connectivity issue. Retrying connection.",
                context=context
            )
        
        if "validation" in error_str or error_type == "ValidationError":
            return ErrorInfo(
                error_id=f"validation_{int(time.time())}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message=f"Validation error: {error}",
                recovery_actions=[RecoveryAction.ESCALATE],
                user_message="Invalid data provided. Please check your input.",
                context=context
            )
        
        # General processing errors
        if error_type in ["ValueError", "TypeError", "KeyError"]:
            return ErrorInfo(
                error_id=f"processing_{int(time.time())}",
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                message=f"Processing error: {error}",
                recovery_actions=[RecoveryAction.FALLBACK],
                user_message="Processing error occurred. Using fallback method.",
                context=context
            )
        
        # Default classification
        return ErrorInfo(
            error_id=f"unknown_{int(time.time())}",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message=f"Unexpected error: {error}",
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
            user_message="Unexpected error occurred. Attempting recovery.",
            context=context
        )

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: int = 60):
        self.name = name
        self.state = CircuitBreakerState(failure_threshold=failure_threshold, reset_timeout=reset_timeout)
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        async with self._lock:
            # Check if circuit should reset
            if (self.state.state == "open" and 
                self.state.last_failure_time and
                datetime.now() - self.state.last_failure_time > timedelta(seconds=self.state.reset_timeout)):
                self.state.state = "half_open"
                logger.info(f"Circuit breaker {self.name} transitioning to half-open")
        
        # Circuit is open - fail fast
        if self.state.state == "open":
            raise Exception(f"Circuit breaker {self.name} is OPEN - failing fast")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Success - reset failure count
            async with self._lock:
                if self.state.state == "half_open":
                    self.state.state = "closed"
                    logger.info(f"Circuit breaker {self.name} reset to closed")
                self.state.failure_count = 0
            
            return result
            
        except Exception as e:
            async with self._lock:
                self.state.failure_count += 1
                self.state.last_failure_time = datetime.now()
                
                if self.state.failure_count >= self.state.failure_threshold:
                    self.state.state = "open"
                    logger.warning(f"Circuit breaker {self.name} OPENED after {self.state.failure_count} failures")
            
            raise e

class ErrorRecoveryManager:
    """Central error recovery management system"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorInfo] = []
        self.fallback_handlers: Dict[str, Callable] = {}
        
    def register_circuit_breaker(self, name: str, failure_threshold: int = 5, reset_timeout: int = 60) -> CircuitBreaker:
        """Register a new circuit breaker"""
        circuit_breaker = CircuitBreaker(name, failure_threshold, reset_timeout)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
    
    def register_fallback_handler(self, operation: str, handler: Callable):
        """Register a fallback handler for an operation"""
        self.fallback_handlers[operation] = handler
    
    async def execute_with_recovery(self, 
                                    operation: str,
                                    func: Callable,
                                    retry_policy: Optional[RetryPolicy] = None,
                                    fallback_func: Optional[Callable] = None,
                                    context: Optional[Dict[str, Any]] = None,
                                    *args, **kwargs) -> Any:
        """Execute function with comprehensive error recovery"""
        
        if retry_policy is None:
            retry_policy = RetryPolicy()
        
        circuit_breaker = self.circuit_breakers.get(operation)
        
        for attempt in range(retry_policy.max_attempts):
            try:
                if circuit_breaker:
                    result = await circuit_breaker.call(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Success
                return result
                
            except Exception as e:
                error_info = ErrorClassifier.classify_error(e, context)
                error_info.source = operation
                self.error_history.append(error_info)
                
                logger.warning(f"Error in {operation} (attempt {attempt + 1}): {error_info.message}")
                
                # Check if we should retry
                if (attempt + 1 < retry_policy.max_attempts and 
                    RecoveryAction.RETRY in error_info.recovery_actions):
                    delay = retry_policy.get_delay(attempt)
                    logger.info(f"Retrying {operation} in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                    continue
                
                # Try fallback if available
                if RecoveryAction.FALLBACK in error_info.recovery_actions:
                    fallback = fallback_func or self.fallback_handlers.get(operation)
                    if fallback:
                        try:
                            logger.info(f"Attempting fallback for {operation}")
                            result = await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                            return result
                        except Exception as fallback_error:
                            logger.error(f"Fallback failed for {operation}: {fallback_error}")
                
                # All recovery attempts failed
                raise e
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]
        
        summary = {
            "total_errors": len(recent_errors),
            "by_category": {},
            "by_severity": {},
            "top_errors": []
        }
        
        for error in recent_errors:
            # By category
            category_key = error.category.value
            if category_key not in summary["by_category"]:
                summary["by_category"][category_key] = 0
            summary["by_category"][category_key] += 1
            
            # By severity
            severity_key = error.severity.value
            if severity_key not in summary["by_severity"]:
                summary["by_severity"][severity_key] = 0
            summary["by_severity"][severity_key] += 1
        
        # Top error messages
        error_counts = {}
        for error in recent_errors:
            if error.message not in error_counts:
                error_counts[error.message] = 0
            error_counts[error.message] += 1
        
        summary["top_errors"] = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return summary

# Global error recovery manager instance
error_recovery_manager = ErrorRecoveryManager()

def with_error_recovery(operation: str, 
                       retry_policy: Optional[RetryPolicy] = None,
                       fallback_func: Optional[Callable] = None):
    """Decorator for automatic error recovery"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await error_recovery_manager.execute_with_recovery(
                operation=operation,
                func=func,
                retry_policy=retry_policy,
                fallback_func=fallback_func,
                *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            async def async_func(*args, **kwargs):
                return func(*args, **kwargs)
            
            return asyncio.run(error_recovery_manager.execute_with_recovery(
                operation=operation,
                func=async_func,
                retry_policy=retry_policy,
                fallback_func=fallback_func,
                *args, **kwargs
            ))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Utility functions for common error recovery patterns

def create_ai_retry_policy() -> RetryPolicy:
    """Create retry policy optimized for AI API calls"""
    return RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        backoff_factor=2.0,
        jitter=True
    )

def create_network_retry_policy() -> RetryPolicy:
    """Create retry policy optimized for network operations"""
    return RetryPolicy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=15.0,
        backoff_factor=1.5,
        jitter=True
    )

# Initialize common circuit breakers
def initialize_circuit_breakers():
    """Initialize common circuit breakers"""
    error_recovery_manager.register_circuit_breaker("openai_api", failure_threshold=5, reset_timeout=60)
    error_recovery_manager.register_circuit_breaker("data_processing", failure_threshold=3, reset_timeout=30)
    error_recovery_manager.register_circuit_breaker("file_operations", failure_threshold=3, reset_timeout=15)

# Initialize on module load
initialize_circuit_breakers()
"""
Utility Decorators
Common decorators for logging, retry logic, and performance monitoring.
"""
import asyncio
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Union
from datetime import datetime


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log execution time of functions.
    Works with both sync and async functions.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {e}")
            raise
    
    # Return appropriate wrapper based on whether function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Decorator to retry function calls on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch and retry on
        on_retry: Optional callback function called before each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}, retrying in {current_delay}s")
                    
                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(attempt, e)
                            else:
                                on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback error: {callback_error}")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}, retrying in {current_delay}s")
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback error: {callback_error}")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def rate_limit(calls_per_second: float = 1.0) -> Callable:
    """
    Decorator to rate limit function calls.
    
    Args:
        calls_per_second: Maximum calls per second allowed
    """
    min_interval = 1.0 / calls_per_second
    last_call_time = 0.0
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal last_call_time
            
            current_time = time.time()
            time_since_last_call = current_time - last_call_time
            
            if time_since_last_call < min_interval:
                sleep_time = min_interval - time_since_last_call
                await asyncio.sleep(sleep_time)
            
            last_call_time = time.time()
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal last_call_time
            
            current_time = time.time()
            time_since_last_call = current_time - last_call_time
            
            if time_since_last_call < min_interval:
                sleep_time = min_interval - time_since_last_call
                time.sleep(sleep_time)
            
            last_call_time = time.time()
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_result(ttl_seconds: int = 3600, key_func: Optional[Callable] = None) -> Callable:
    """
    Decorator to cache function results with TTL.
    
    Args:
        ttl_seconds: Time to live for cached results in seconds
        key_func: Optional function to generate cache key from args/kwargs
    """
    cache = {}
    
    def default_key_func(*args, **kwargs):
        """Default cache key generation."""
        return str(args) + str(sorted(kwargs.items()))
    
    if key_func is None:
        key_func = default_key_func
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs)
            current_time = time.time()
            
            # Check if we have a valid cached result
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    return result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            # Clean old cache entries (simple cleanup)
            if len(cache) > 1000:  # Prevent unlimited growth
                old_keys = [k for k, (_, ts) in cache.items() if current_time - ts > ttl_seconds]
                for key in old_keys:
                    del cache[key]
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs)
            current_time = time.time()
            
            # Check if we have a valid cached result
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            # Clean old cache entries
            if len(cache) > 1000:
                old_keys = [k for k, (_, ts) in cache.items() if current_time - ts > ttl_seconds]
                for key in old_keys:
                    del cache[key]
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_input(**validators) -> Callable:
    """
    Decorator to validate function inputs.
    
    Usage:
        @validate_input(ein=validate_ein, state=validate_state)
        def my_function(ein, state):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each specified parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for parameter '{param_name}': {value}")
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for parameter '{param_name}': {value}")
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def timeout(seconds: float) -> Callable:
    """
    Decorator to add timeout to async functions.
    
    Args:
        seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger = logging.getLogger(func.__module__)
                logger.error(f"{func.__name__} timed out after {seconds} seconds")
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
        
        return wrapper
    
    return decorator


def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure and log detailed performance metrics.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        start_memory = None
        
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024
                    memory_used = end_memory - start_memory
                except Exception as e:

                    logger.warning(f"Unexpected error: {e}")

                    pass
            
            metrics = {
                'function': func.__name__,
                'execution_time': f"{execution_time:.3f}s",
                'memory_delta': f"{memory_used:.1f}MB" if memory_used else "N/A"
            }
            
            logger.info(f"Performance metrics: {metrics}")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        start_memory = None
        
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pass
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024
                    memory_used = end_memory - start_memory
                except Exception as e:

                    logger.warning(f"Unexpected error: {e}")

                    pass
            
            metrics = {
                'function': func.__name__,
                'execution_time': f"{execution_time:.3f}s",
                'memory_delta': f"{memory_used:.1f}MB" if memory_used else "N/A"
            }
            
            logger.info(f"Performance metrics: {metrics}")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
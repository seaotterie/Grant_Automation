# Error Handling Standards

## Logging Guidelines

### Import Pattern
```python
import logging
logger = logging.getLogger(__name__)
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages  
- **WARNING**: Something unexpected but handled
- **ERROR**: Error that affects functionality
- **CRITICAL**: Serious error that may stop execution

### Exception Handling Patterns

#### 1. Specific Exception Handling (Preferred)
```python
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value provided: {e}")
    return None
except ConnectionError as e:
    logger.warning(f"Connection failed, will retry: {e}")
    # retry logic
except Exception as e:
    logger.error(f"Unexpected error in operation: {e}")
    raise
```

#### 2. Async Operation Timeouts
```python
try:
    result = await asyncio.wait_for(api_call(), timeout=30.0)
except asyncio.TimeoutError:
    logger.warning("API call timed out after 30 seconds")
    return None
except Exception as e:
    logger.error(f"API call failed: {e}")
    raise
```

#### 3. Parameter Validation
```python
def process_data(data: Dict[str, Any]) -> ProcessorResult:
    if not data:
        raise ValueError("Data parameter is required")
    
    if "required_field" not in data:
        raise ValueError("Missing required field: required_field")
```

### Avoid These Patterns
- [AVOID] Bare except clauses: `except:`
- [AVOID] Print statements in production code
- [AVOID] Silent failures without logging
- [AVOID] Generic error messages without context

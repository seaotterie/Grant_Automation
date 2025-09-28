# BMF Filter Tool Environment Configuration
# 12-Factor Factor 3: Config from Environment
# This file configures the tool for CSV-based processing

# ============================================================================
# DATA SOURCE CONFIGURATION (CSV Files)
# ============================================================================

# BMF CSV Input Path - Main data source
BMF_INPUT_PATH=data/input/eo_va.csv

# Filter configuration file (NTEE codes, etc.)
BMF_FILTER_CONFIG_PATH=data/input/filter_config.json

# ============================================================================
# TOOL PERFORMANCE SETTINGS
# ============================================================================

# Caching configuration
BMF_CACHE_ENABLED=true
BMF_CACHE_TTL=3600
BMF_CACHE_MAX_SIZE=1000

# Processing limits and performance
BMF_MAX_RESULTS=1000
BMF_TIMEOUT_SECONDS=30
BMF_MEMORY_LIMIT_MB=512

# ============================================================================
# HTTP SERVICE CONFIGURATION (Factor 7: Port Binding)
# ============================================================================

# Service port (different from main Catalynx to avoid conflicts)
BMF_FILTER_PORT=8001
BMF_HOST=0.0.0.0
BMF_WORKERS=1
BMF_RELOAD=false

# Health check and monitoring
HEALTH_CHECK_ENABLED=true
METRICS_ENABLED=true

# ============================================================================
# LOGGING CONFIGURATION (Factor 11: Logs as Event Streams)
# ============================================================================

# Log level for this tool
BMF_LOG_LEVEL=INFO

# Performance logging
BMF_LOG_PERFORMANCE=true

# ============================================================================
# DEVELOPMENT AND TESTING
# ============================================================================

# Development mode (enables /docs endpoint)
DEVELOPMENT_MODE=true
DEBUG_ENABLED=false

# Performance comparison with existing processor
BENCHMARK_AGAINST_EXISTING=true

# ============================================================================
# 12-FACTOR COMPLIANCE SETTINGS
# ============================================================================

# Factor 9: Disposability - Graceful shutdown timeout
GRACEFUL_SHUTDOWN_TIMEOUT=10

# Factor 6: Stateless - External cache in production
EXTERNAL_CACHE_URL=

# Factor 8: Concurrency - Process scaling
SCALE_PROCESS_MODEL=true
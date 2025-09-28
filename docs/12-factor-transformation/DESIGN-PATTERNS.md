# 12-Factor Design Patterns Library
*Reusable solution templates for 12-factor agent systems*

## Pattern Overview

This library provides proven design patterns specifically adapted for 12-factor agent systems. Each pattern includes implementation examples, BAML schemas, and integration guidelines for building scalable, maintainable AI agent platforms.

## Core Architecture Patterns

### 1. Agent Registry Pattern
**Problem**: Managing discovery and lifecycle of distributed micro-tools
**Solution**: Centralized registry with self-registration and health monitoring

```python
# src/core/agent_registry.py
class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.health_checks = {}

    def register_agent(self, agent_id: str, agent_config: AgentConfig):
        """Register agent with capabilities and health check"""
        self.agents[agent_id] = agent_config
        self.health_checks[agent_id] = datetime.utcnow()

    def discover_agents(self, capability: str) -> List[AgentConfig]:
        """Find agents by capability"""
        return [agent for agent in self.agents.values()
                if capability in agent.capabilities]

    def health_check(self, agent_id: str) -> bool:
        """Verify agent health"""
        return self.agents[agent_id].ping()
```

```baml
// baml/schemas/agent_registry.baml
class AgentConfig {
    id string
    name string
    capabilities string[]
    endpoint string
    version string
    health_check_url string
    metadata map<string, string>
}

class RegistryResponse {
    agents AgentConfig[]
    total_count int
    healthy_count int
}
```

**12-Factor Alignment**:
- **Factor VI (Processes)**: Stateless registry service
- **Factor IV (Backing Services)**: Agents as attached resources
- **Factor VIII (Concurrency)**: Horizontal scaling of agent instances

### 2. Configuration Injection Pattern
**Problem**: Factor III compliance with complex multi-agent configurations
**Solution**: Hierarchical configuration with environment-specific overrides

```python
# src/core/config_manager.py
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any

class AgentConfig(BaseSettings):
    agent_id: str
    capabilities: List[str]
    max_concurrent_tasks: int = Field(default=10)
    timeout_seconds: int = Field(default=300)

    class Config:
        env_prefix = f"AGENT_{agent_id.upper()}_"
        env_file = ".env"

class SystemConfig(BaseSettings):
    """Global system configuration"""
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Agent-specific configs loaded dynamically
    def get_agent_config(self, agent_id: str) -> AgentConfig:
        return AgentConfig(agent_id=agent_id)

# Usage
config = SystemConfig()
bmf_config = config.get_agent_config("bmf_filter")
```

```yaml
# Environment template for .env
# Global Configuration
DATABASE_URL=sqlite:///data/catalynx.db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO

# Agent-Specific Configuration
AGENT_BMF_FILTER_MAX_CONCURRENT_TASKS=5
AGENT_BMF_FILTER_TIMEOUT_SECONDS=120
AGENT_AI_HEAVY_MAX_CONCURRENT_TASKS=2
AGENT_AI_HEAVY_TIMEOUT_SECONDS=600
```

**12-Factor Alignment**:
- **Factor III (Config)**: Environment variables only
- **Factor V (Build/Release/Run)**: Config separate from code
- **Factor X (Dev/Prod Parity)**: Same config system across environments

### 3. Process Type Pattern
**Problem**: Factor VIII compliance with different workload types
**Solution**: Dedicated process types for web, workers, and schedulers

```python
# src/processes/web_process.py
class WebProcess:
    """HTTP API process type"""
    def __init__(self, config: SystemConfig):
        self.app = FastAPI()
        self.config = config

    def setup_routes(self):
        """Configure API endpoints"""
        @self.app.post("/api/agents/{agent_id}/execute")
        async def execute_agent(agent_id: str, request: AgentRequest):
            # Delegate to worker process via queue
            task_id = await self.queue.enqueue(agent_id, request)
            return {"task_id": task_id, "status": "queued"}

# src/processes/worker_process.py
class WorkerProcess:
    """Background task processing"""
    def __init__(self, config: SystemConfig):
        self.queue = Queue(config.redis_url)
        self.registry = AgentRegistry()

    async def process_tasks(self):
        """Main worker loop"""
        while True:
            task = await self.queue.dequeue()
            agent = self.registry.get_agent(task.agent_id)
            result = await agent.execute(task.request)
            await self.queue.complete(task.id, result)

# src/processes/scheduler_process.py
class SchedulerProcess:
    """Periodic task scheduling"""
    def __init__(self, config: SystemConfig):
        self.scheduler = AsyncScheduler()

    def setup_schedules(self):
        """Configure periodic tasks"""
        self.scheduler.add_job(
            func=self.health_check_agents,
            trigger="interval",
            minutes=5
        )
```

```dockerfile
# Dockerfile with process types
FROM python:3.11-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ /app/src/
WORKDIR /app

# Different process entry points
CMD ["python", "-m", "src.processes.web_process"]  # Default web
# CMD ["python", "-m", "src.processes.worker_process"]  # Worker
# CMD ["python", "-m", "src.processes.scheduler_process"]  # Scheduler
```

**12-Factor Alignment**:
- **Factor VIII (Concurrency)**: Scale process types independently
- **Factor VI (Processes)**: Stateless, share-nothing architecture
- **Factor IX (Disposability)**: Fast startup, graceful shutdown

### 4. Event-Driven Workflow Pattern
**Problem**: Orchestrating complex multi-agent workflows
**Solution**: Event streams with saga pattern for distributed transactions

```python
# src/workflows/event_bus.py
class EventBus:
    """Central event coordination"""
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
        self.subscribers = {}

    async def publish(self, event: WorkflowEvent):
        """Publish event to all subscribers"""
        await self.redis.publish(event.type, event.json())

    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

# src/workflows/saga_coordinator.py
class SagaCoordinator:
    """Manage distributed transactions across agents"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.sagas = {}

    async def start_saga(self, saga_id: str, workflow: WorkflowDefinition):
        """Begin distributed transaction"""
        saga = SagaInstance(saga_id, workflow)
        self.sagas[saga_id] = saga

        # Execute first step
        await self.execute_step(saga, 0)

    async def handle_step_completion(self, event: StepCompletedEvent):
        """Handle agent completion and trigger next step"""
        saga = self.sagas[event.saga_id]

        if event.success:
            await self.execute_step(saga, saga.current_step + 1)
        else:
            await self.compensate(saga, saga.current_step - 1)
```

```baml
// baml/schemas/workflow.baml
class WorkflowEvent {
    id string
    type string
    saga_id string
    timestamp string
    data map<string, string>
}

class StepDefinition {
    agent_id string
    input_schema map<string, string>
    compensation_agent_id string?
    timeout_seconds int
}

class WorkflowDefinition {
    id string
    name string
    steps StepDefinition[]
    compensations map<string, StepDefinition>
}
```

**12-Factor Alignment**:
- **Factor VI (Processes)**: Event-driven, stateless coordination
- **Factor IV (Backing Services)**: Redis as event store
- **Factor IX (Disposability)**: Resumable workflows after failures

### 5. Circuit Breaker Pattern
**Problem**: Factor IX compliance with external service failures
**Solution**: Automatic failure detection and recovery

```python
# src/resilience/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open" # Testing recovery

@dataclass
class CircuitConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    timeout_seconds: int = 30

class CircuitBreaker:
    def __init__(self, config: CircuitConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")

        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset circuit breaker on success"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

# Usage in agents
class ResilientAgent:
    def __init__(self, agent_id: str, external_service: ExternalService):
        self.agent_id = agent_id
        self.service = external_service
        self.circuit_breaker = CircuitBreaker(CircuitConfig())

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute with circuit breaker protection"""
        try:
            return await self.circuit_breaker.call(
                self._execute_internal, request
            )
        except CircuitOpenError:
            # Fallback to cached data or degraded response
            return self._fallback_response(request)
```

**12-Factor Alignment**:
- **Factor IX (Disposability)**: Robust against sudden failures
- **Factor IV (Backing Services)**: Graceful handling of backing service failures
- **Factor VI (Processes)**: Resilient stateless processing

### 6. Health Check Pattern
**Problem**: Factor IX compliance with process health monitoring
**Solution**: Comprehensive health endpoints with dependency checking

```python
# src/health/health_checker.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    details: Dict[str, Any] = None

class HealthChecker:
    def __init__(self):
        self.checks = {}

    def register_check(self, name: str, check_func: Callable):
        """Register health check function"""
        self.checks[name] = check_func

    async def check_health(self) -> HealthCheck:
        """Execute all health checks"""
        results = {}
        overall_status = HealthStatus.HEALTHY

        for name, check_func in self.checks.items():
            start_time = time.time()
            try:
                result = await check_func()
                response_time = (time.time() - start_time) * 1000

                results[name] = HealthCheck(
                    name=name,
                    status=result.status,
                    message=result.message,
                    response_time_ms=response_time,
                    details=result.details
                )

                # Aggregate status
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED

            except Exception as e:
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    response_time_ms=(time.time() - start_time) * 1000
                )
                overall_status = HealthStatus.UNHEALTHY

        return HealthCheck(
            name="overall",
            status=overall_status,
            message=f"Checked {len(results)} components",
            response_time_ms=sum(r.response_time_ms for r in results.values()),
            details=results
        )

# Web process health endpoint
@app.get("/health")
async def health_endpoint():
    """Health check endpoint for load balancers"""
    health = await health_checker.check_health()

    status_code = {
        HealthStatus.HEALTHY: 200,
        HealthStatus.DEGRADED: 200,  # Still serving traffic
        HealthStatus.UNHEALTHY: 503
    }[health.status]

    return Response(
        content=health.json(),
        status_code=status_code,
        media_type="application/json"
    )
```

```baml
// baml/schemas/health.baml
enum HealthStatus {
    HEALTHY
    DEGRADED
    UNHEALTHY
}

class HealthCheck {
    name string
    status HealthStatus
    message string
    response_time_ms float
    timestamp string
    details map<string, string>?
}

class SystemHealth {
    overall_status HealthStatus
    components HealthCheck[]
    uptime_seconds float
    version string
}
```

**12-Factor Alignment**:
- **Factor IX (Disposability)**: Readiness and liveness probes
- **Factor XI (Logs)**: Health events as structured logs
- **Factor IV (Backing Services)**: Monitor backing service health

### 7. Structured Logging Pattern
**Problem**: Factor XI compliance with observable distributed systems
**Solution**: Structured JSON logging with correlation IDs

```python
# src/logging/structured_logger.py
import json
import logging
import uuid
from contextvars import ContextVar
from typing import Dict, Any

# Context variable for correlation tracking
correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
        }

        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)

        # Add exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_logging():
    """Configure structured logging to stdout"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

class CorrelatedLogger:
    """Logger with automatic correlation ID injection"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, **extra):
        """Log info with correlation context"""
        self.logger.info(message, extra=extra)

    def error(self, message: str, **extra):
        """Log error with correlation context"""
        self.logger.error(message, extra=extra)

# Middleware for web requests
async def correlation_middleware(request: Request, call_next):
    """Add correlation ID to request context"""
    corr_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    correlation_id.set(corr_id)

    response = await call_next(request)
    response.headers['X-Correlation-ID'] = corr_id
    return response
```

```yaml
# Log aggregation config (fluentd/logstash)
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-config
data:
  fluent.conf: |
    <source>
      @type forward
      port 24224
    </source>

    <filter catalynx.**>
      @type parser
      key_name log
      format json
      reserve_data true
    </filter>

    <match catalynx.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      index_name catalynx-logs
    </match>
```

**12-Factor Alignment**:
- **Factor XI (Logs)**: Stdout-only structured event streams
- **Factor VI (Processes)**: Correlation across stateless processes
- **Factor IX (Disposability)**: Observable process lifecycle

### 8. Feature Flag Pattern
**Problem**: Factor V compliance with safe deployment and rollback
**Solution**: Runtime feature toggles with gradual rollouts

```python
# src/features/feature_flags.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class FeatureState(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLOUT = "rollout"  # Gradual percentage rollout

@dataclass
class FeatureFlag:
    name: str
    state: FeatureState
    rollout_percentage: int = 0
    conditions: Dict[str, Any] = None
    description: str = ""

class FeatureFlagManager:
    def __init__(self, config_source: str):
        self.flags = self._load_flags(config_source)

    def is_enabled(self, flag_name: str, context: Dict[str, Any] = None) -> bool:
        """Check if feature is enabled for given context"""
        flag = self.flags.get(flag_name)
        if not flag:
            return False

        if flag.state == FeatureState.DISABLED:
            return False
        elif flag.state == FeatureState.ENABLED:
            return True
        elif flag.state == FeatureState.ROLLOUT:
            return self._check_rollout(flag, context)

    def _check_rollout(self, flag: FeatureFlag, context: Dict[str, Any]) -> bool:
        """Determine if user is in rollout percentage"""
        user_id = context.get('user_id', 'anonymous')
        hash_value = hash(f"{flag.name}:{user_id}") % 100
        return hash_value < flag.rollout_percentage

# Usage in agents
class EnhancedBMFAgent:
    def __init__(self, flag_manager: FeatureFlagManager):
        self.flag_manager = flag_manager

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute with feature flag controls"""

        # Use new AI model if feature enabled
        if self.flag_manager.is_enabled('gpt5_analysis', {'user_id': request.user_id}):
            return await self._execute_with_gpt5(request)
        else:
            return await self._execute_with_gpt4(request)
```

```yaml
# feature_flags.yml (loaded from environment)
features:
  gpt5_analysis:
    state: rollout
    rollout_percentage: 25
    description: "Use GPT-5 for enhanced analysis"

  enhanced_bmf_discovery:
    state: enabled
    description: "New BMF discovery algorithm"

  real_time_notifications:
    state: disabled
    description: "WebSocket-based real-time updates"
```

**12-Factor Alignment**:
- **Factor III (Config)**: Feature flags as environment configuration
- **Factor V (Build/Release/Run)**: Runtime behavior changes without code deploy
- **Factor IX (Disposability)**: Safe rollback via flag changes

## Data Patterns

### 9. Repository Pattern with Entity Abstraction
**Problem**: Factor IV compliance with backing service abstraction
**Solution**: Data access layer with pluggable backends

```python
# src/data/repositories/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class Repository(ABC):
    """Abstract repository interface"""

    @abstractmethod
    async def create(self, entity: Any) -> str:
        """Create entity and return ID"""
        pass

    @abstractmethod
    async def get(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        pass

    @abstractmethod
    async def find(self, criteria: Dict[str, Any]) -> List[Any]:
        """Find entities by criteria"""
        pass

# src/data/repositories/profile_repository.py
class ProfileRepository(Repository):
    """Profile repository with pluggable backends"""

    def __init__(self, backend: BackingService):
        self.backend = backend

    async def create(self, profile: Profile) -> str:
        """Create profile"""
        if isinstance(self.backend, SQLiteBackend):
            return await self._create_sqlite(profile)
        elif isinstance(self.backend, PostgreSQLBackend):
            return await self._create_postgresql(profile)
        elif isinstance(self.backend, MongoBackend):
            return await self._create_mongo(profile)

# src/data/backends/sqlite_backend.py
class SQLiteBackend(BackingService):
    """SQLite implementation"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None

    async def connect(self):
        """Establish connection"""
        self.connection = await aiosqlite.connect(self.database_url)

    async def execute(self, query: str, params: Dict[str, Any]) -> Any:
        """Execute query"""
        async with self.connection.execute(query, params) as cursor:
            return await cursor.fetchall()
```

**12-Factor Alignment**:
- **Factor IV (Backing Services)**: Database as attached resource
- **Factor III (Config)**: Backend selection via environment
- **Factor X (Dev/Prod Parity)**: Same interface across environments

### 10. Event Sourcing Pattern
**Problem**: Factor VI compliance with stateless, auditable systems
**Solution**: Event-based state reconstruction with immutable event log

```python
# src/events/event_store.py
from dataclasses import dataclass
from typing import List, Dict, Any
import uuid
from datetime import datetime

@dataclass
class Event:
    id: str
    aggregate_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    version: int

class EventStore:
    """Immutable event storage"""

    def __init__(self, backend: BackingService):
        self.backend = backend

    async def append_events(self, aggregate_id: str, events: List[Event], expected_version: int):
        """Append events with optimistic concurrency"""
        # Check current version
        current_version = await self.get_current_version(aggregate_id)
        if current_version != expected_version:
            raise ConcurrencyConflictError()

        # Append events atomically
        for i, event in enumerate(events):
            event.version = expected_version + i + 1
            await self.backend.store_event(event)

    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get events for aggregate"""
        return await self.backend.get_events(aggregate_id, from_version)

# src/aggregates/profile_aggregate.py
class ProfileAggregate:
    """Profile aggregate with event sourcing"""

    def __init__(self, profile_id: str):
        self.id = profile_id
        self.version = 0
        self.name = ""
        self.organization = ""
        self.changes = []

    def create_profile(self, name: str, organization: str):
        """Command: Create profile"""
        if self.version > 0:
            raise ValueError("Profile already exists")

        event = Event(
            id=str(uuid.uuid4()),
            aggregate_id=self.id,
            event_type="ProfileCreated",
            data={"name": name, "organization": organization},
            timestamp=datetime.utcnow(),
            version=0
        )

        self._apply_event(event)
        self.changes.append(event)

    def _apply_event(self, event: Event):
        """Apply event to aggregate state"""
        if event.event_type == "ProfileCreated":
            self.name = event.data["name"]
            self.organization = event.data["organization"]
        elif event.event_type == "ProfileUpdated":
            if "name" in event.data:
                self.name = event.data["name"]

        self.version = event.version

    @classmethod
    async def load_from_events(cls, profile_id: str, event_store: EventStore):
        """Reconstruct aggregate from events"""
        aggregate = cls(profile_id)
        events = await event_store.get_events(profile_id)

        for event in events:
            aggregate._apply_event(event)

        return aggregate
```

**12-Factor Alignment**:
- **Factor VI (Processes)**: Stateless - state reconstructed from events
- **Factor IX (Disposability)**: Complete audit trail for recovery
- **Factor XI (Logs)**: Business events as first-class logs

## Integration Patterns

### 11. API Gateway Pattern
**Problem**: Factor VII compliance with unified service interface
**Solution**: Single entry point with routing, authentication, and rate limiting

```python
# src/gateway/api_gateway.py
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
from typing import Dict, List

class APIGateway:
    """Central API gateway for micro-services"""

    def __init__(self):
        self.app = FastAPI(title="Catalynx API Gateway")
        self.service_registry = {}
        self.rate_limiter = RateLimiter()
        self.auth_service = AuthService()

    def register_service(self, service_name: str, base_url: str, routes: List[str]):
        """Register micro-service"""
        self.service_registry[service_name] = {
            "base_url": base_url,
            "routes": routes,
            "health_url": f"{base_url}/health"
        }

    async def route_request(self, request: Request) -> Dict[str, Any]:
        """Route request to appropriate service"""
        path = request.url.path
        service = self._find_service_for_path(path)

        if not service:
            raise HTTPException(404, "Service not found")

        # Check rate limits
        await self.rate_limiter.check_limit(request.client.host)

        # Authenticate request
        user = await self.auth_service.authenticate(request)

        # Proxy to service
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{service['base_url']}{path}",
                headers=dict(request.headers),
                json=await request.json() if request.method in ["POST", "PUT"] else None
            )

        return response.json()

# Service registration
gateway = APIGateway()
gateway.register_service("profiles", "http://profile-service:8001", ["/api/profiles/*"])
gateway.register_service("discovery", "http://discovery-service:8002", ["/api/discovery/*"])
gateway.register_service("intelligence", "http://intelligence-service:8003", ["/api/intelligence/*"])
```

**12-Factor Alignment**:
- **Factor VII (Port Binding)**: Gateway exports HTTP service
- **Factor VIII (Concurrency)**: Route to scaled service instances
- **Factor IV (Backing Services)**: Services as attached resources

### 12. Saga Orchestration Pattern
**Problem**: Distributed transactions across multiple agents
**Solution**: Centralized orchestration with compensation logic

```python
# src/workflows/saga_orchestrator.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    step_id: str
    agent_id: str
    action: str
    input_data: Dict[str, Any]
    compensation_action: Optional[str] = None
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SagaOrchestrator:
    """Orchestrate distributed transactions"""

    def __init__(self, agent_registry: AgentRegistry, event_bus: EventBus):
        self.agent_registry = agent_registry
        self.event_bus = event_bus
        self.active_sagas = {}

    async def execute_saga(self, saga_id: str, steps: List[SagaStep]) -> bool:
        """Execute saga with compensation on failure"""
        self.active_sagas[saga_id] = {
            "steps": steps,
            "completed_steps": [],
            "current_step": 0
        }

        try:
            # Execute steps sequentially
            for i, step in enumerate(steps):
                await self._execute_step(saga_id, step)
                self.active_sagas[saga_id]["completed_steps"].append(step)
                self.active_sagas[saga_id]["current_step"] = i + 1

            return True

        except Exception as e:
            # Compensate completed steps in reverse order
            await self._compensate_saga(saga_id)
            return False

    async def _execute_step(self, saga_id: str, step: SagaStep):
        """Execute individual saga step"""
        agent = self.agent_registry.get_agent(step.agent_id)

        try:
            result = await agent.execute_action(step.action, step.input_data)
            step.status = SagaStepStatus.COMPLETED
            step.result = result

            # Publish step completed event
            await self.event_bus.publish(StepCompletedEvent(
                saga_id=saga_id,
                step_id=step.step_id,
                result=result
            ))

        except Exception as e:
            step.status = SagaStepStatus.FAILED
            step.error = str(e)
            raise

    async def _compensate_saga(self, saga_id: str):
        """Execute compensation logic for failed saga"""
        saga = self.active_sagas[saga_id]
        completed_steps = list(reversed(saga["completed_steps"]))

        for step in completed_steps:
            if step.compensation_action:
                try:
                    agent = self.agent_registry.get_agent(step.agent_id)
                    await agent.execute_action(
                        step.compensation_action,
                        step.result
                    )
                    step.status = SagaStepStatus.COMPENSATED

                except Exception as e:
                    # Log compensation failure but continue
                    logger.error(f"Compensation failed for step {step.step_id}: {e}")
```

**12-Factor Alignment**:
- **Factor VI (Processes)**: Stateless orchestration with external state
- **Factor IX (Disposability)**: Resumable transactions after failures
- **Factor VIII (Concurrency)**: Parallel saga execution

## Implementation Guidelines

### Pattern Selection Matrix

| Use Case | Primary Patterns | Secondary Patterns |
|----------|------------------|-------------------|
| **Micro-Agent System** | Agent Registry, Process Types | Health Check, Circuit Breaker |
| **Data Processing Pipeline** | Event Sourcing, Saga Orchestration | Repository, Feature Flags |
| **API Platform** | API Gateway, Configuration Injection | Structured Logging, Health Check |
| **Batch Processing** | Process Types, Event-Driven Workflow | Circuit Breaker, Repository |
| **Real-time System** | Event Bus, Health Check | Feature Flags, Structured Logging |

### Pattern Composition Example

```python
# Complete system using multiple patterns
class CatalynxSystem:
    def __init__(self, config: SystemConfig):
        # Core infrastructure
        self.config = config
        self.event_bus = EventBus(config.redis_url)
        self.agent_registry = AgentRegistry()
        self.health_checker = HealthChecker()

        # Orchestration
        self.saga_orchestrator = SagaOrchestrator(
            self.agent_registry,
            self.event_bus
        )

        # Gateway
        self.api_gateway = APIGateway()

        # Feature management
        self.feature_flags = FeatureFlagManager(config.feature_flags_url)

        # Setup components
        self._setup_agents()
        self._setup_health_checks()
        self._setup_gateway_routes()

    def _setup_agents(self):
        """Register all micro-agents"""
        agents = [
            BMFFilterAgent(self.config.get_agent_config("bmf_filter")),
            AIHeavyAgent(self.config.get_agent_config("ai_heavy")),
            NetworkAnalyzerAgent(self.config.get_agent_config("network_analyzer"))
        ]

        for agent in agents:
            self.agent_registry.register_agent(agent.id, agent.config)

    async def execute_intelligence_tier(self, tier: str, profile_id: str) -> Dict[str, Any]:
        """Execute intelligence tier using saga pattern"""
        workflow = self._get_tier_workflow(tier)
        saga_id = f"{profile_id}_{tier}_{uuid.uuid4()}"

        success = await self.saga_orchestrator.execute_saga(saga_id, workflow.steps)

        if success:
            return await self._aggregate_results(saga_id)
        else:
            raise IntelligenceProcessingError(f"Tier {tier} processing failed")
```

### Testing Patterns

```python
# src/testing/pattern_tests.py
import pytest
from unittest.mock import AsyncMock, Mock

class TestAgentRegistryPattern:
    """Test agent registry pattern"""

    @pytest.fixture
    def registry(self):
        return AgentRegistry()

    async def test_agent_registration(self, registry):
        """Test agent registration and discovery"""
        config = AgentConfig(
            id="test_agent",
            capabilities=["analysis", "processing"]
        )

        registry.register_agent("test_agent", config)

        # Test discovery
        agents = registry.discover_agents("analysis")
        assert len(agents) == 1
        assert agents[0].id == "test_agent"

    async def test_health_checking(self, registry):
        """Test health check functionality"""
        mock_agent = Mock()
        mock_agent.ping.return_value = True

        config = AgentConfig(id="test_agent", capabilities=[])
        registry.register_agent("test_agent", config)

        health = registry.health_check("test_agent")
        assert health is True

class TestSagaPattern:
    """Test saga orchestration pattern"""

    @pytest.fixture
    def orchestrator(self):
        registry = Mock()
        event_bus = Mock()
        return SagaOrchestrator(registry, event_bus)

    async def test_successful_saga(self, orchestrator):
        """Test successful saga execution"""
        # Mock agent execution
        mock_agent = AsyncMock()
        mock_agent.execute_action.return_value = {"status": "success"}
        orchestrator.agent_registry.get_agent.return_value = mock_agent

        steps = [
            SagaStep("step1", "agent1", "action1", {}),
            SagaStep("step2", "agent2", "action2", {})
        ]

        result = await orchestrator.execute_saga("test_saga", steps)
        assert result is True
        assert mock_agent.execute_action.call_count == 2
```

---

This design patterns library provides proven templates for building scalable, maintainable 12-factor agent systems. Each pattern addresses specific architectural challenges while maintaining compliance with 12-factor principles and enabling effective composition into larger systems.
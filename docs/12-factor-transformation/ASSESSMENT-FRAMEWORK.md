# 12-Factor Assessment Framework
*Systematic evaluation methodology for existing systems*

## Framework Overview

This assessment framework provides systematic evaluation tools for measuring 12-factor compliance in existing systems and planning migration strategies. Use this framework to baseline current state, identify gaps, and track transformation progress.

## Assessment Methodology

### Phase 1: Current State Analysis
1. **System Inventory** - Catalog all components, dependencies, configurations
2. **Factor Scoring** - Rate compliance 0-4 for each of the 12 factors
3. **Gap Identification** - Document specific violations and technical debt
4. **Risk Assessment** - Evaluate transformation complexity and risks
5. **Migration Planning** - Prioritize factors and create implementation roadmap

### Phase 2: Continuous Monitoring
1. **Progress Tracking** - Regular re-assessment during transformation
2. **Metric Collection** - Automated compliance monitoring where possible
3. **Quality Gates** - Factor-specific validation criteria
4. **Rollback Planning** - Risk mitigation and contingency procedures

## 12-Factor Compliance Checklists

### Factor I: Codebase
**Score: 0-4 (0=Non-compliant, 4=Fully compliant)**

- [ ] **4 Points**: Single codebase tracked in revision control, multiple deploys
- [ ] **3 Points**: Single codebase with some deployment inconsistencies
- [ ] **2 Points**: Multiple codebases with shared components
- [ ] **1 Point**: Some version control, inconsistent deployment
- [ ] **0 Points**: No version control or multiple untracked codebases

**Assessment Questions:**
- Is there exactly one codebase per app?
- Are all components tracked in version control?
- Are deploys (dev/staging/prod) from the same codebase?
- Are shared libraries managed as dependencies?

**Current Catalynx Assessment:**
- ✅ Single Git repository
- ✅ All code tracked in version control
- ⚠️ Some configuration scattered across files
- 🔍 **Gap**: Need centralized config management

### Factor II: Dependencies
**Score: 0-4**

- [ ] **4 Points**: All dependencies explicitly declared and isolated
- [ ] **3 Points**: Most dependencies declared, minimal system assumptions
- [ ] **2 Points**: Some implicit dependencies or system tool requirements
- [ ] **1 Point**: Mix of explicit/implicit dependencies
- [ ] **0 Points**: Many implicit dependencies, system tool requirements

**Assessment Questions:**
- Are all dependencies explicitly declared in manifest (requirements.txt, package.json)?
- Does the app bundle tools like curl, ImageMagick with the app?
- Can the app run in a clean environment with only runtime and declared deps?
- Are system packages avoided in favor of app-bundled alternatives?

**Current Catalynx Assessment:**
- ✅ requirements.txt for Python dependencies
- ⚠️ Some system tool dependencies (curl for web scraping)
- 🔍 **Gap**: Bundle tools or use dependency injection for external tools

### Factor III: Config
**Score: 0-4**

- [ ] **4 Points**: All config in environment variables, no secrets in code
- [ ] **3 Points**: Most config externalized, minimal hardcoded values
- [ ] **2 Points**: Some config files, some hardcoded values
- [ ] **1 Point**: Mix of config methods, some secrets in code
- [ ] **0 Points**: Config hardcoded, secrets in repository

**Assessment Questions:**
- Are credentials stored as environment variables?
- Are environment-specific configs externalized?
- Can you deploy to new environment by only changing environment variables?
- Are no secrets committed to the codebase?

**Current Catalynx Assessment:**
- ✅ .env file for API keys and database paths
- ⚠️ Some hardcoded paths in source code
- ⚠️ Configuration scattered across multiple files
- 🔍 **Gap**: Centralize all config in environment variables

### Factor IV: Backing Services
**Score: 0-4**

- [ ] **4 Points**: All backing services accessed via URL/config, easily swappable
- [ ] **3 Points**: Most services configurable, minimal hardcoded connections
- [ ] **2 Points**: Some services hardcoded, some configurable
- [ ] **1 Point**: Mix of local and remote services
- [ ] **0 Points**: Services tightly coupled, hardcoded connections

**Assessment Questions:**
- Are databases accessed via connection strings/URLs?
- Can you swap local DB for production DB with config change only?
- Are external APIs accessed via configurable endpoints?
- Are file systems treated as attached resources?

**Current Catalynx Assessment:**
- ✅ SQLite databases configurable via paths
- ✅ OpenAI API configurable via environment
- ⚠️ Local file system paths hardcoded
- 🔍 **Gap**: Abstract file storage as attached resource

### Factor V: Build, Release, Run
**Score: 0-4**

- [ ] **4 Points**: Strict separation of build/release/run with unique releases
- [ ] **3 Points**: Mostly separated stages with some overlap
- [ ] **2 Points**: Some stage separation, manual processes
- [ ] **1 Point**: Minimal separation, ad-hoc deployment
- [ ] **0 Points**: No separation, changes made directly to running code

**Assessment Questions:**
- Is the build stage separate from runtime?
- Are releases uniquely tagged and immutable?
- Can you rollback to any previous release?
- Are runtime changes prohibited?

**Current Catalynx Assessment:**
- ⚠️ Build and run phases exist but not formalized
- ⚠️ No formal release management
- ⚠️ Direct file editing possible in production
- 🔍 **Gap**: Implement formal build/release/run pipeline

### Factor VI: Processes
**Score: 0-4**

- [ ] **4 Points**: App executes as stateless processes, no sticky sessions
- [ ] **3 Points**: Mostly stateless with minimal process state
- [ ] **2 Points**: Some process state, session data externalized
- [ ] **1 Point**: Mix of stateful/stateless design
- [ ] **0 Points**: Heavy reliance on process state and memory

**Assessment Questions:**
- Is the app stateless and share-nothing?
- Is session data stored in external stores (Redis, database)?
- Can you restart processes without data loss?
- Are processes horizontally scalable?

**Current Catalynx Assessment:**
- ✅ FastAPI application is mostly stateless
- ✅ Data persisted to SQLite databases
- ⚠️ Some in-memory caching without persistence
- 🔍 **Gap**: Externalize cache to Redis/similar backing service

### Factor VII: Port Binding
**Score: 0-4**

- [ ] **4 Points**: App exports HTTP via port binding, fully self-contained
- [ ] **3 Points**: Mostly self-contained with minimal server dependencies
- [ ] **2 Points**: Some reliance on runtime injection of webserver
- [ ] **1 Point**: Partially self-contained
- [ ] **0 Points**: Relies on runtime injection of webserver

**Assessment Questions:**
- Does the app export HTTP by binding to a port?
- Is the app completely self-contained?
- Can the app become a backing service for another app?
- Does the app rely on injection of webserver into execution environment?

**Current Catalynx Assessment:**
- ✅ FastAPI binds to configurable port (8000)
- ✅ Self-contained ASGI application
- ✅ Can serve as backing service
- 🔍 **Score**: 4/4 - Fully compliant

### Factor VIII: Concurrency
**Score: 0-4**

- [ ] **4 Points**: Process model for concurrency, different process types
- [ ] **3 Points**: Some process type diversity, mostly horizontal scaling
- [ ] **2 Points**: Limited process types, some threading
- [ ] **1 Point**: Basic concurrency patterns
- [ ] **0 Points**: Single-threaded, no concurrency model

**Assessment Questions:**
- Does the app scale out via the process model?
- Are there different process types (web, worker, scheduler)?
- Can individual process types scale independently?
- Are processes designed to handle their own internal multiplexing?

**Current Catalynx Assessment:**
- ⚠️ Single web process type
- ⚠️ No worker processes for background tasks
- ⚠️ Async processing within single process
- 🔍 **Gap**: Implement dedicated worker processes for heavy processing

### Factor IX: Disposability
**Score: 0-4**

- [ ] **4 Points**: Fast startup, graceful shutdown, robust against sudden death
- [ ] **3 Points**: Good startup/shutdown with minimal edge cases
- [ ] **2 Points**: Reasonable startup/shutdown times
- [ ] **1 Point**: Slow startup or shutdown issues
- [ ] **0 Points**: Fragile startup/shutdown processes

**Assessment Questions:**
- Do processes start up quickly (seconds, not minutes)?
- Do processes shut down gracefully on SIGTERM?
- Are processes robust against sudden death?
- Are long-running tasks designed to be resumable?

**Current Catalynx Assessment:**
- ✅ FastAPI starts quickly (~2-3 seconds)
- ⚠️ No formal graceful shutdown handling
- ⚠️ Long-running AI processes not resumable
- 🔍 **Gap**: Implement graceful shutdown and resumable task design

### Factor X: Dev/Prod Parity
**Score: 0-4**

- [ ] **4 Points**: Dev and prod identical, minimal gaps in time/personnel/tools
- [ ] **3 Points**: Mostly similar environments with minor differences
- [ ] **2 Points**: Some environmental differences, regular syncing
- [ ] **1 Point**: Significant environmental differences
- [ ] **0 Points**: Dev and prod completely different

**Assessment Questions:**
- Is the gap between dev and prod small?
- Are developers involved in deployment and monitoring?
- Are dev, staging, and prod environments similar?
- Are the same tools and versions used across environments?

**Current Catalynx Assessment:**
- ⚠️ Development uses local SQLite, production could use different DB
- ⚠️ No staging environment defined
- ⚠️ Different monitoring between dev/prod
- 🔍 **Gap**: Establish staging environment and formalize prod parity

### Factor XI: Logs
**Score: 0-4**

- [ ] **4 Points**: Logs as event streams, app never manages log files
- [ ] **3 Points**: Mostly stream-based logging with minimal file output
- [ ] **2 Points**: Some log files, some streaming
- [ ] **1 Point**: Mixed logging approaches
- [ ] **0 Points**: App manages log files directly

**Assessment Questions:**
- Does the app write to stdout/stderr only?
- Are logs treated as event streams?
- Does the app never concern itself with log file management?
- Are logs aggregated by execution environment?

**Current Catalynx Assessment:**
- ⚠️ Logging to both stdout and files
- ⚠️ Application manages log file rotation
- ⚠️ No centralized log aggregation
- 🔍 **Gap**: Convert to stdout-only logging, implement log aggregation

### Factor XII: Admin Processes
**Score: 0-4**

- [ ] **4 Points**: Admin tasks as one-off processes in identical environments
- [ ] **3 Points**: Most admin tasks properly isolated
- [ ] **2 Points**: Some admin tasks in separate processes
- [ ] **1 Point**: Mixed admin process management
- [ ] **0 Points**: Admin tasks run in production app processes

**Assessment Questions:**
- Are admin tasks run as one-off processes?
- Do admin processes run in the same environment as regular processes?
- Are admin processes shipped with application code?
- Are database migrations and one-time scripts handled properly?

**Current Catalynx Assessment:**
- ⚠️ No formal admin process framework
- ⚠️ Database setup mixed with application code
- ⚠️ No migration system for schema changes
- 🔍 **Gap**: Implement one-off admin process framework

## Gap Analysis Template

### System Overview
- **Application Name**: [Catalynx Grant Intelligence Platform]
- **Assessment Date**: [Current Date]
- **Assessor**: [Name/Team]
- **Current Architecture**: [Monolithic FastAPI + SQLite + Alpine.js frontend]

### Factor Compliance Summary
```
Factor I - Codebase:           [3/4] - ⚠️  Config scattered
Factor II - Dependencies:     [3/4] - ⚠️  Some system tools
Factor III - Config:          [2/4] - 🔴 Hardcoded paths
Factor IV - Backing Services: [3/4] - ⚠️  File system coupling
Factor V - Build/Release/Run: [1/4] - 🔴 No formal pipeline
Factor VI - Processes:        [3/4] - ⚠️  In-memory caching
Factor VII - Port Binding:    [4/4] - ✅ Fully compliant
Factor VIII - Concurrency:   [2/4] - 🔴 Single process type
Factor IX - Disposability:   [2/4] - 🔴 No graceful shutdown
Factor X - Dev/Prod Parity:  [2/4] - 🔴 No staging environment
Factor XI - Logs:            [2/4] - 🔴 File-based logging
Factor XII - Admin:          [1/4] - 🔴 No admin framework

Overall Score: 28/48 (58% - Needs Improvement)
```

### Priority Gap Matrix

| Priority | Factor | Gap Description | Impact | Effort |
|----------|--------|----------------|---------|---------|
| P0 | III - Config | Centralize all configuration in environment variables | High | Medium |
| P0 | V - Build/Release/Run | Implement formal CI/CD pipeline | High | High |
| P1 | VIII - Concurrency | Add worker processes for background tasks | Medium | Medium |
| P1 | XI - Logs | Convert to stdout-only structured logging | Medium | Low |
| P2 | X - Dev/Prod Parity | Establish staging environment | Medium | Medium |
| P2 | IX - Disposability | Implement graceful shutdown | Low | Low |
| P3 | XII - Admin | Create admin process framework | Low | Medium |

## Migration Planning Worksheets

### Phase-Based Migration Plan

#### Phase 1: Foundation (Weeks 1-2)
**Target Factors**: III (Config), XI (Logs)
- [ ] Audit all configuration sources
- [ ] Create environment variable schema
- [ ] Implement structured logging to stdout
- [ ] Remove file-based logging
- [ ] Test configuration injection

#### Phase 2: Process Architecture (Weeks 3-4)
**Target Factors**: VIII (Concurrency), VI (Processes)
- [ ] Design worker process architecture
- [ ] Implement job queue system
- [ ] Separate web and worker concerns
- [ ] Add Redis for external caching
- [ ] Test horizontal scaling

#### Phase 3: Deployment Pipeline (Weeks 5-6)
**Target Factors**: V (Build/Release/Run), X (Dev/Prod Parity)
- [ ] Create Docker build process
- [ ] Implement release tagging
- [ ] Set up staging environment
- [ ] Create deployment automation
- [ ] Test release rollback

#### Phase 4: Operations (Weeks 7-8)
**Target Factors**: IX (Disposability), XII (Admin)
- [ ] Implement graceful shutdown
- [ ] Create admin command framework
- [ ] Add health check endpoints
- [ ] Implement database migrations
- [ ] Test disaster recovery

## Risk Assessment Matrices

### Technical Risk Assessment

| Risk Category | Probability | Impact | Mitigation Strategy |
|---------------|-------------|---------|-------------------|
| Data Loss During Migration | Low | High | Database backups, staged migration |
| Service Downtime | Medium | Medium | Blue-green deployment, rollback plan |
| Performance Degradation | Medium | Medium | Load testing, gradual rollout |
| Configuration Errors | High | Medium | Validation schemas, automated testing |
| Dependency Conflicts | Low | High | Virtual environments, version pinning |

### Business Risk Assessment

| Risk Category | Probability | Impact | Mitigation Strategy |
|---------------|-------------|---------|-------------------|
| User Experience Disruption | Low | High | Maintain UI compatibility, user testing |
| Feature Delivery Delays | Medium | Medium | Parallel development, feature flags |
| Integration Failures | Medium | High | API versioning, contract testing |
| Compliance Issues | Low | High | Security audit, compliance checklist |
| Team Knowledge Gaps | High | Low | Training plan, documentation |

## Success Metrics Definitions

### Quantitative Metrics

#### Performance Metrics
- **Startup Time**: < 5 seconds (currently ~3 seconds) ✅
- **Response Time**: < 500ms for 95th percentile (baseline required)
- **Memory Usage**: < 1GB per process (baseline required)
- **CPU Utilization**: < 70% under normal load (baseline required)

#### Reliability Metrics
- **Uptime**: > 99.9% (target improvement from current state)
- **Error Rate**: < 0.1% (target improvement)
- **Recovery Time**: < 5 minutes for automated recovery
- **Deployment Success Rate**: > 99% (with rollback capability)

#### Scalability Metrics
- **Horizontal Scale**: Support 10x traffic with linear resource increase
- **Process Scaling**: Independent scaling of web vs worker processes
- **Database Connections**: Configurable connection pooling
- **Concurrent Users**: Support > 100 concurrent users

### Qualitative Metrics

#### Developer Experience
- **Deployment Simplicity**: One-command deployment ✅ (via launch_catalynx_web.bat)
- **Environment Parity**: Identical dev/staging/prod environments
- **Configuration Management**: Single source of truth for all config
- **Debugging Capability**: Structured logs with correlation IDs

#### Operations
- **Monitoring Coverage**: All 12 factors have associated metrics
- **Alerting**: Proactive alerts for factor violations
- **Documentation**: Complete runbooks for each factor
- **Security**: No secrets in code, encrypted data at rest

## Factor-Specific Validation Criteria

### Automated Validation Scripts

```python
# config_validation.py
def validate_factor_iii_config():
    """Validate all config is externalized"""
    violations = []

    # Check for hardcoded values
    hardcoded_patterns = [
        r'localhost:\d+',
        r'/[a-zA-Z0-9_/]+\.db',
        r'http://[^{]',
        r'sk-[a-zA-Z0-9]+',  # API keys
    ]

    for pattern in hardcoded_patterns:
        if find_in_codebase(pattern):
            violations.append(f"Hardcoded value found: {pattern}")

    return len(violations) == 0, violations

def validate_factor_xi_logs():
    """Validate logging compliance"""
    violations = []

    # Check for file logging
    if has_file_handlers():
        violations.append("File logging handlers found")

    # Check for stdout logging
    if not has_stdout_handlers():
        violations.append("No stdout logging configured")

    return len(violations) == 0, violations
```

### Manual Validation Checklists

#### Factor V - Build/Release/Run Validation
- [ ] Can build application without modifying source code
- [ ] Release artifacts are immutable and tagged
- [ ] Can deploy any previous release
- [ ] Runtime configuration separate from build configuration
- [ ] No direct file modifications in production

#### Factor VIII - Concurrency Validation
- [ ] Web processes handle HTTP requests only
- [ ] Background tasks run in separate worker processes
- [ ] Processes can scale independently
- [ ] No shared memory between processes
- [ ] Process types documented and defined

## Continuous Assessment Tools

### Automated Monitoring

```yaml
# prometheus_rules.yml
groups:
  - name: 12_factor_compliance
    rules:
      - alert: HardcodedConfig
        expr: config_violations_total > 0
        labels:
          factor: "III"
          severity: "warning"
        annotations:
          summary: "Configuration violations detected"

      - alert: ProcessNotDisposable
        expr: avg_shutdown_time_seconds > 30
        labels:
          factor: "IX"
          severity: "critical"
        annotations:
          summary: "Processes taking too long to shutdown"
```

### Dashboard Metrics

```json
{
  "dashboard": "12-Factor Compliance",
  "panels": [
    {
      "title": "Factor Compliance Score",
      "type": "stat",
      "targets": ["sum(factor_compliance_score) / 12"]
    },
    {
      "title": "Configuration Violations",
      "type": "graph",
      "targets": ["config_violations_total"]
    },
    {
      "title": "Process Health",
      "type": "table",
      "targets": ["process_startup_time", "process_shutdown_time"]
    }
  ]
}
```

## Assessment Report Template

### Executive Summary
- **Overall Compliance**: [X]% (Score/48)
- **Critical Issues**: [Number] factors requiring immediate attention
- **Migration Timeline**: [X] weeks estimated
- **Resource Requirements**: [X] developer weeks

### Detailed Findings
[Factor-by-factor analysis with specific recommendations]

### Implementation Roadmap
[Phase-based plan with timelines and resource allocation]

### Risk Mitigation
[Identified risks and mitigation strategies]

### Success Criteria
[Measurable goals and validation criteria]

---

This assessment framework provides systematic evaluation tools for measuring 12-factor compliance and planning successful migrations. Use the checklists, worksheets, and validation criteria to ensure thorough analysis and successful transformation outcomes.
# Catalynx Specialized Agents Guide

## Overview

This directory contains 5 specialized Claude Code subagents designed for the Catalynx grant research intelligence platform. Catalynx is a **desktop-only, single-user system** designed for professional researchers working directly with organization Points of Contact (POCs). Each agent has deep expertise in specific aspects of the system and can be invoked automatically or explicitly for focused assistance.

## Available Agents

### 1. **catalynx-data-pipeline** - Data Pipeline & Processing Expert
**When to Use:** Processor management, entity caching, API integrations, performance optimization
```bash
# Automatic invocation examples:
"The processor registry isn't discovering all 18 processors"
"Entity cache hit rate has dropped below 80%"
"Grants.gov API integration is timing out"
"Need to optimize the government opportunity scorer algorithm"
```

### 2. **catalynx-web-dev** - Full-Stack Web Development Expert  
**When to Use:** FastAPI backend, Alpine.js frontend, desktop interface optimization, professional UI/UX
```bash
# Automatic invocation examples:
"The Chart.js visualizations aren't updating in real-time"
"Desktop interface needs better keyboard shortcuts for power users"
"WebSocket connections are dropping unexpectedly"
"Need to optimize the interface for extended research sessions"
```

### 3. **catalynx-intelligence** - Intelligence & Decision Support Expert
**When to Use:** AI analysis, scoring algorithms, decision synthesis, export generation
```bash
# Automatic invocation examples:
"AI Heavy Researcher is returning low-quality analysis"
"Government opportunity scoring weights need optimization"
"Board network analysis isn't identifying key relationships"
"Export templates need formatting for POC presentations"
```

### 4. **catalynx-system-quality** - System Architecture & Quality Expert
**When to Use:** Performance optimization, testing, error handling, system architecture
```bash
# Automatic invocation examples:
"System performance has degraded below benchmarks"
"Need comprehensive test coverage for all 18 processors"
"Error handling patterns are inconsistent across components"
"Require load testing and performance validation"
```

### 5. **catalynx-docs-devops** - Documentation & DevOps Expert
**When to Use:** Technical documentation, API specs, deployment, operational procedures
```bash
# Automatic invocation examples:
"API documentation needs OpenAPI specification updates"
"Local installation process needs better setup scripts"
"Algorithm documentation needs comprehensive methodology"
"Need troubleshooting guides for common desktop issues"
```

## How to Use the Agents

### Automatic Delegation
Claude automatically selects the appropriate agent based on:
- Task description keywords and context
- Agent specialization descriptions  
- Available tools and capabilities
- Current conversation context

### Explicit Invocation
Mention the agent name directly:
```bash
"catalynx-data-pipeline, help optimize the entity cache performance"
"catalynx-web-dev, fix the mobile responsiveness issues"
"catalynx-intelligence, tune the government scorer algorithm"
```

## Common Usage Patterns

### Multi-Agent Workflows
```bash
# Complex feature development:
1. catalynx-docs-devops documents requirements
2. catalynx-system-quality designs testing strategy  
3. catalynx-data-pipeline implements backend logic
4. catalynx-web-dev creates user interface
5. catalynx-intelligence adds decision support features
6. catalynx-system-quality validates performance and quality
7. catalynx-docs-devops updates documentation and deployment
```

### Debugging Workflows
```bash
# Performance issue investigation:
1. catalynx-system-quality identifies performance bottlenecks
2. catalynx-data-pipeline optimizes processor pipeline
3. catalynx-web-dev optimizes frontend performance
4. catalynx-intelligence tunes algorithm efficiency
5. catalynx-docs-devops updates monitoring procedures
```

### Feature Enhancement Workflows  
```bash
# Adding new capabilities:
1. catalynx-intelligence designs algorithm improvements
2. catalynx-data-pipeline implements data processing changes
3. catalynx-web-dev creates user interface enhancements
4. catalynx-system-quality validates functionality and performance
5. catalynx-docs-devops documents new features and procedures
```

## Agent Coordination Benefits

### Context Isolation
Each agent operates in its own context, preventing:
- Cross-contamination between different technical domains
- Context pollution in the main conversation
- Loss of focus on high-level objectives

### Specialized Expertise
Each agent provides:
- Deep domain knowledge in specific technical areas
- Optimized tool selection for specialized tasks
- Focused problem-solving approaches
- Consistent patterns and best practices within their domain

### Efficient Collaboration
Agents work together to provide:
- Comprehensive solutions across all system aspects
- Coordinated development workflows
- Quality assurance at every stage
- Complete documentation and operational procedures

## Best Practices

### Task Definition
- Be specific about the technical domain when requesting help
- Provide context about the Catalynx system component involved
- Mention performance requirements or quality standards
- Include relevant error messages or symptoms

### Agent Selection
- Let Claude automatically select agents for most tasks
- Use explicit invocation for highly specific technical requests
- Consider multi-agent workflows for complex features
- Leverage agent expertise for their specialized domains

### Quality Assurance
- Always involve catalynx-system-quality for performance validation
- Use catalynx-docs-devops for documentation and operational procedures
- Coordinate testing across all affected system components
- Validate changes against Catalynx performance benchmarks

## System Integration

These agents are designed specifically for the Catalynx platform and understand:
- **Desktop-only, single-user workflow** for professional researchers
- **POC collaboration focus** for working directly with organization stakeholders
- **Entity-based architecture** with 85% cache hit rate optimization
- **18-processor system** with complex interdependencies  
- **Phase 6 completion status** with advanced decision support features
- **Performance standards** with sub-millisecond response time requirements
- **Professional desktop interface** with FastAPI + Alpine.js architecture

## Troubleshooting

If agents aren't being invoked correctly:
1. Check agent file syntax and YAML frontmatter
2. Verify agent descriptions match your task requirements  
3. Use explicit agent names for testing
4. Review Claude Code subagent documentation for debugging

## Agent Updates

To modify agent behavior:
1. Edit the relevant `.md` file in this directory
2. Update the system prompt or tool configuration
3. Test agent responses with sample tasks
4. Document changes in version control

---

**System Status:** 5 specialized agents configured and ready for Catalynx development workflows.
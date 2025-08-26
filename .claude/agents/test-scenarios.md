# Catalynx Agent Test Scenarios

## Testing Your Specialized Agents

Use these test scenarios to validate your agents are working correctly and being invoked appropriately.

## Data Pipeline Agent Tests

### Test 1: Entity Cache Performance
```
"The entity cache hit rate has dropped to 70% and response times are increasing. Help optimize the cache performance and investigate potential issues with the entity-based data organization."
```
**Expected:** catalynx-data-pipeline agent should be invoked to analyze cache performance.

### Test 2: Processor Registry Issues  
```
"The processor auto-discovery system is only finding 15 of the 18 processors. The registry.py file seems to have issues with the registration process for some processors."
```
**Expected:** catalynx-data-pipeline agent should handle processor registry debugging.

### Test 3: API Integration Problems
```
"Grants.gov API integration is failing with timeout errors and the unified client architecture isn't handling rate limiting properly. Need to debug the async processing patterns."
```
**Expected:** catalynx-data-pipeline agent should address API integration issues.

## Web Development Agent Tests

### Test 4: Desktop Interface Optimization
```
"The Catalynx desktop interface needs better keyboard shortcuts for power users. The Chart.js visualizations need optimization for large desktop screens and extended research sessions."
```
**Expected:** catalynx-web-dev agent should handle desktop UI optimization.

### Test 5: FastAPI + Alpine.js Integration
```  
"There are data binding issues between the FastAPI backend and Alpine.js frontend. WebSocket connections are dropping and real-time updates aren't working."
```
**Expected:** catalynx-web-dev agent should debug integration issues.

### Test 6: Professional Desktop UI
```
"Need to optimize the interface for professional research workflows and improve keyboard navigation for power users working on complex grant analysis."
```
**Expected:** catalynx-web-dev agent should handle professional desktop interface improvements.

## Intelligence Agent Tests

### Test 7: AI Processor Optimization
```
"The AI Heavy Researcher is returning low-quality analysis results and using too many API calls. Need to optimize prompts and improve cost efficiency."
```
**Expected:** catalynx-intelligence agent should optimize AI integration.

### Test 8: Scoring Algorithm Tuning
```
"The Government Opportunity Scorer needs weight adjustments based on our analysis of 45 profiles. The current eligibility scoring might be too heavily weighted."
```
**Expected:** catalynx-intelligence agent should tune scoring algorithms.

### Test 9: POC Collaboration Enhancement
```
"Need to improve the decision synthesis framework for POC presentations and enhance export capabilities for sharing analysis with organization stakeholders."
```
**Expected:** catalynx-intelligence agent should enhance POC collaboration features.

## System Quality Agent Tests

### Test 10: Performance Regression
```
"System performance has degraded and response times are above the sub-millisecond benchmark. Need comprehensive performance analysis and optimization."
```
**Expected:** catalynx-system-quality agent should investigate performance issues.

### Test 11: Testing Framework Development
```
"Need to create comprehensive test suites for all 18 processors with integration testing and performance validation. Current test coverage is insufficient."
```
**Expected:** catalynx-system-quality agent should design testing frameworks.

### Test 12: Error Handling Standardization
```
"Error handling patterns are inconsistent across processors. Need to standardize error handling and improve system reliability monitoring."
```
**Expected:** catalynx-system-quality agent should standardize error handling.

## Documentation & DevOps Agent Tests

### Test 13: API Documentation Update
```
"The OpenAPI specification needs updates for the new entity-based endpoints and the developer documentation is outdated after the Phase 6 completion."
```
**Expected:** catalynx-docs-devops agent should update API documentation.

### Test 14: Local Setup Automation
```
"Need to create better setup scripts for local installation and improve environment configuration for individual researchers setting up Catalynx on their desktops."
```
**Expected:** catalynx-docs-devops agent should handle local setup automation.

### Test 15: User Support Documentation
```
"Need comprehensive troubleshooting guides and user documentation for researchers using Catalynx for grant discovery and POC collaboration."
```
**Expected:** catalynx-docs-devops agent should create user support documentation.

## Multi-Agent Collaboration Tests

### Test 16: Complex Feature Development
```
"Need to add a new foundation discovery track that integrates with the Foundation Directory API, includes AI-powered analysis, provides real-time web interface updates, and generates professional export reports."
```
**Expected:** Multiple agents should collaborate in sequence or parallel.

### Test 17: Performance Issue Investigation
```
"The entire system is running slower than expected. Need to investigate processor performance, database queries, frontend loading times, algorithm efficiency, and create monitoring dashboards."
```
**Expected:** Multiple agents should coordinate comprehensive performance optimization.

### Test 18: System Upgrade Project
```
"Planning to upgrade the system architecture for better scalability. Need analysis of current architecture, performance testing, new component design, web interface updates, and comprehensive documentation."
```
**Expected:** All agents should contribute to system upgrade planning.

## Agent Validation Checklist

After running tests, verify:

- [ ] Agents are automatically invoked based on task descriptions
- [ ] Each agent stays focused on their domain expertise  
- [ ] Agent responses demonstrate deep knowledge of Catalynx architecture
- [ ] Multi-agent workflows coordinate properly without context pollution
- [ ] Agent tool usage is appropriate for their specialization
- [ ] Agent responses reference correct Catalynx files and components
- [ ] Performance and quality standards are maintained across agents

## Troubleshooting Agent Issues

If agents aren't working correctly:

1. **Check YAML frontmatter** - Ensure proper formatting and required fields
2. **Verify agent descriptions** - Make sure descriptions match task types  
3. **Test explicit invocation** - Use agent names directly for debugging
4. **Review tool access** - Ensure agents have appropriate tool permissions
5. **Validate file paths** - Confirm agents reference correct Catalynx file locations

## Success Metrics

Your agent system is working correctly when:

- **Automatic delegation** works for 90%+ of domain-specific tasks
- **Context isolation** prevents cross-domain confusion  
- **Expert responses** demonstrate deep technical knowledge
- **Multi-agent workflows** coordinate effectively for complex tasks
- **Development velocity** increases due to specialized assistance
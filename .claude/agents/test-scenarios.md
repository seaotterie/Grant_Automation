# Agent Triggering Test Scenarios

## Purpose

These test scenarios validate that agents are properly triggered by natural developer language. Each test should result in the expected agent being automatically selected.

## 🔍 General Purpose Agent Tests

### Test 1: Exploration and Research
```
"I need to understand how this authentication system works. Help me find the relevant files and explore the codebase structure."
```
**Expected:** general-purpose agent triggered
**Keywords:** understand, help, find, explore

### Test 2: Multi-step Investigation
```
"Search through the codebase for any references to 'user permissions' and analyze how they're implemented across different components."
```
**Expected:** general-purpose agent triggered
**Keywords:** search, analyze, investigate

## 📋 Requirements Analyst Tests

### Test 3: Feature Requirements
```
"I need to build a feature that allows users to export their data in multiple formats. What are the requirements for this?"
```
**Expected:** requirements-analyst triggered
**Keywords:** feature, requirements, users, functionality

### Test 4: User Story Creation
```
"Help me write user stories for a notification system that sends alerts to users based on their preferences."
```
**Expected:** requirements-analyst triggered
**Keywords:** user stories, system, functionality

### Test 5: Business Requirements
```
"The business wants to add a dashboard for managers to view team performance metrics. What should this include?"
```
**Expected:** requirements-analyst triggered
**Keywords:** business wants, dashboard, what should

## 🎨 UX/UI Specialist Tests

### Test 6: Interface Design
```
"The current user interface is confusing and users can't find the settings page. How can we improve the navigation?"
```
**Expected:** ux-ui-specialist triggered
**Keywords:** user interface, confusing, navigation, improve

### Test 7: Responsive Design
```
"This dashboard needs to work on mobile devices. Make it responsive and touch-friendly."
```
**Expected:** ux-ui-specialist triggered
**Keywords:** mobile, responsive, touch-friendly

### Test 8: Accessibility Concerns
```
"The website needs to be accessible to users with disabilities. What accessibility improvements should we implement?"
```
**Expected:** ux-ui-specialist triggered
**Keywords:** accessible, accessibility, users with disabilities

## 🔍 Code Reviewer Tests

### Test 9: Code Quality Review
```
"Please review this authentication function. I think it might have some security issues and could be refactored for better maintainability."
```
**Expected:** code-reviewer triggered
**Keywords:** review, function, security issues, refactored, maintainability

### Test 10: Architecture Assessment
```
"This code looks messy and hard to maintain. Can you suggest improvements and best practices for cleaning it up?"
```
**Expected:** code-reviewer triggered
**Keywords:** messy, maintain, improvements, best practices, cleaning up

### Test 11: Performance Review
```
"Is this the best approach for handling large datasets? The current implementation seems inefficient."
```
**Expected:** code-reviewer triggered
**Keywords:** best approach, implementation, inefficient

## 🧪 Testing Expert Tests

### Test 12: Test Implementation
```
"I need to write unit tests for this user service class. It handles user creation, validation, and database operations."
```
**Expected:** testing-expert triggered
**Keywords:** unit tests, service class, validation, operations

### Test 13: Debugging Tests
```
"These integration tests are failing randomly. Can you help debug why they're flaky and fix the issues?"
```
**Expected:** testing-expert triggered
**Keywords:** integration tests, failing, debug, flaky, fix

### Test 14: Test Coverage
```
"The test coverage is too low and we're missing edge cases. What testing strategy should we implement?"
```
**Expected:** testing-expert triggered
**Keywords:** test coverage, edge cases, testing strategy

## 🔒 Security Specialist Tests

### Test 15: Authentication System
```
"How do I secure this login endpoint? I want to make sure it's protected against common attacks."
```
**Expected:** security-specialist triggered
**Keywords:** secure, login, protected, attacks

### Test 16: Data Protection
```
"We need to encrypt sensitive user data and ensure it's stored securely. What's the best approach?"
```
**Expected:** security-specialist triggered
**Keywords:** encrypt, sensitive data, stored securely

### Test 17: Vulnerability Assessment
```
"Can you review this API for security vulnerabilities? I'm concerned about SQL injection and XSS attacks."
```
**Expected:** security-specialist triggered
**Keywords:** security vulnerabilities, SQL injection, XSS attacks

## 📊 Performance Optimizer Tests

### Test 18: Slow Performance
```
"This page is loading really slowly. Users are complaining about response times. How can we speed it up?"
```
**Expected:** performance-optimizer triggered
**Keywords:** loading slowly, response times, speed up

### Test 19: Database Performance
```
"The database queries are taking too long and using too much memory. We need performance optimization."
```
**Expected:** performance-optimizer triggered
**Keywords:** queries, too long, memory, performance optimization

### Test 20: System Bottlenecks
```
"The system slows down under high load. Help me identify bottlenecks and optimize resource usage."
```
**Expected:** performance-optimizer triggered
**Keywords:** slows down, high load, bottlenecks, optimize

## 🖥️ Backend Specialist Tests

### Test 21: API Development
```
"I need to create a REST API for managing user profiles. It should support CRUD operations and user authentication."
```
**Expected:** backend-specialist triggered
**Keywords:** REST API, managing, CRUD operations, authentication

### Test 22: Database Schema
```
"Design a database schema for an e-commerce platform with products, orders, customers, and inventory management."
```
**Expected:** backend-specialist triggered
**Keywords:** database schema, platform, products, orders, management

### Test 23: Server Architecture
```
"The backend needs to handle high traffic and scale horizontally. What microservices architecture should we use?"
```
**Expected:** backend-specialist triggered
**Keywords:** backend, high traffic, scale, microservices architecture

## 💻 Frontend Specialist Tests

### Test 24: Component Development
```
"Build a React component for user profile editing with form validation and state management."
```
**Expected:** frontend-specialist triggered
**Keywords:** React component, profile editing, form validation, state management

### Test 25: JavaScript Functionality
```
"The frontend needs to handle real-time updates from the server. Implement WebSocket connections and update the UI accordingly."
```
**Expected:** frontend-specialist triggered
**Keywords:** frontend, real-time updates, WebSocket, UI

### Test 26: Browser Issues
```
"This JavaScript function works in Chrome but fails in Safari. Fix the browser compatibility issues."
```
**Expected:** frontend-specialist triggered
**Keywords:** JavaScript function, Chrome, Safari, browser compatibility

## 📊 Data Specialist Tests

### Test 27: Data Processing
```
"We need to process large CSV files and transform the data before storing it in the database. Create an ETL pipeline."
```
**Expected:** data-specialist triggered
**Keywords:** process, CSV files, transform data, database, ETL pipeline

### Test 28: Query Optimization
```
"These SQL queries are running slowly on large datasets. Optimize the database performance and add proper indexing."
```
**Expected:** data-specialist triggered
**Keywords:** SQL queries, slowly, datasets, database performance, indexing

### Test 29: Data Migration
```
"We need to migrate data from MySQL to PostgreSQL while maintaining data integrity and minimizing downtime."
```
**Expected:** data-specialist triggered
**Keywords:** migrate data, MySQL, PostgreSQL, data integrity, downtime

## 🚀 DevOps Specialist Tests

### Test 30: Deployment Automation
```
"Set up automated deployment for this Node.js application. It should deploy to staging first, then production after tests pass."
```
**Expected:** devops-specialist triggered
**Keywords:** automated deployment, application, staging, production, tests

### Test 31: Infrastructure Setup
```
"Configure a Docker container for this application and set up Kubernetes orchestration for production deployment."
```
**Expected:** devops-specialist triggered
**Keywords:** Docker container, Kubernetes, orchestration, production deployment

### Test 32: CI/CD Pipeline
```
"Create a CI/CD pipeline that runs tests, builds the application, and deploys to multiple environments automatically."
```
**Expected:** devops-specialist triggered
**Keywords:** CI/CD pipeline, runs tests, builds, deploys, environments

## 📖 Documentation Specialist Tests

### Test 33: API Documentation
```
"Generate comprehensive API documentation for these REST endpoints with examples and usage instructions."
```
**Expected:** documentation-specialist triggered
**Keywords:** API documentation, REST endpoints, examples, instructions

### Test 34: User Guide
```
"Create a user guide that explains how to use the new dashboard features. Include screenshots and step-by-step instructions."
```
**Expected:** documentation-specialist triggered
**Keywords:** user guide, dashboard features, screenshots, instructions

### Test 35: Code Comments
```
"Add proper documentation comments to this complex algorithm so other developers can understand how it works."
```
**Expected:** documentation-specialist triggered
**Keywords:** documentation comments, algorithm, developers, understand

## 🔄 Multi-Agent Workflow Tests

### Test 36: Complete Feature Development
```
"I need to build a complete user authentication system with login, registration, password reset, and admin panel. This needs to be secure, well-tested, and properly documented."
```
**Expected:** Multiple agents collaborate
- requirements-analyst (break down requirements)
- security-specialist (security requirements)
- backend-specialist (API implementation)
- frontend-specialist (UI implementation)
- testing-expert (comprehensive testing)
- documentation-specialist (documentation)

### Test 37: Performance Issue Resolution
```
"Our application is running slowly across the board. The database queries are slow, the frontend is laggy, and users are complaining. We need a comprehensive performance overhaul."
```
**Expected:** Multiple agents collaborate
- performance-optimizer (identify bottlenecks)
- data-specialist (database optimization)
- frontend-specialist (frontend optimization)
- backend-specialist (server optimization)
- testing-expert (performance testing)

### Test 38: Production Deployment
```
"We're ready to deploy this new feature to production. It needs proper testing, security review, deployment automation, and user documentation."
```
**Expected:** Multiple agents collaborate
- testing-expert (final testing)
- security-specialist (security review)
- devops-specialist (deployment setup)
- documentation-specialist (user documentation)

## 📊 Agent Effectiveness Validation

### Success Criteria

**Agent Triggering (85%+ accuracy):**
- [ ] Correct agent triggered for single-domain tasks
- [ ] Multiple agents collaborate on complex tasks
- [ ] Natural language patterns properly recognized
- [ ] Edge cases handled appropriately

**Response Quality:**
- [ ] Agents provide domain-specific expertise
- [ ] Solutions are actionable and practical
- [ ] Code examples are relevant and correct
- [ ] Recommendations follow best practices

**Workflow Coordination:**
- [ ] Multi-agent tasks are properly coordinated
- [ ] Agents hand off work appropriately
- [ ] No duplicate effort or conflicting advice
- [ ] Complete coverage of user requirements

### Common Issues to Watch For

**Under-Triggering:**
- Agent not triggered when it should be
- Generic responses instead of specialist expertise
- Missing proactive engagement opportunities

**Over-Triggering:**
- Wrong agent triggered for the task
- Multiple agents triggered unnecessarily
- Agent scope too broad

**Poor Coordination:**
- Agents working in isolation on related tasks
- Conflicting recommendations from different agents
- Incomplete handoffs between specialists

## 🛠️ Debugging Agent Issues

If agents aren't triggering correctly:

1. **Check trigger keywords** - Ensure natural developer language is included
2. **Review descriptions** - Make sure they match actual use cases
3. **Test explicit invocation** - Use agent names directly for debugging
4. **Analyze conversation context** - Some triggers may be context-dependent
5. **Update trigger patterns** - Add new keywords based on actual usage

## 📈 Continuous Improvement

**Track Agent Usage:**
- Monitor which agents are called most/least frequently
- Identify common phrases that don't trigger appropriate agents
- Collect feedback on agent response quality

**Update Based on Usage:**
- Add new trigger keywords from real conversations
- Refine agent descriptions to improve selection
- Create new agents for underserved use cases
- Remove or merge underutilized agents

---

**Expected Result:** With these test scenarios, 85%+ of requests should trigger the appropriate specialist agent, resulting in more expert, actionable assistance for developers.
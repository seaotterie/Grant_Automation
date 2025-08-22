# Tasks - <Grant_Automation>

## Planning
- 8_21- Scoring
- Feedback loop where BOD and Grantor Networks feed back in to the DISCOVERY tab


## Today
- [ ] CORE-001
- [ ] BUG-001

## Backlog

## Done


## Long Term
- Add a sorting carrot to the Headers in the scrollable tables to allow sorting to table place
- Add the ability for a non-profit to upload a list of Grantors, EINs Date, and Grant value.
- Fix the tabs TOP banners above the banner.  The Title and search bar area
- DISCOVER Nonprofits area, what is the IRS data refer to if not the 990 and 990-PF

- While some non profits might not provide grants they may be of value from the BOD networking and Grantors Networking.

Tables
- freeze headers
- Filter & Sorting headers

Manual Inputs
- Websites like banks who manage foundations and trusts
- Donor lists similar to Schedule I but coming directly from the Profile and input manually
- Add a profile's grant package and docs outlining grant writing information, about us, past performance, metrics, non profit details to help with the APPROACH tab and grant writing
- Comments on View Details provided Promote and Demote reasoning


## IVV Plan

You are Claude Code acting as a Staff Engineer + IV&V-oriented Technical Writer.

Goal: Produce a single, self-contained Markdown document that fully defines a code application project so it can be handed to ChatGPT for thorough evaluation, recommendations, and independent verification & validation (IV&V). ChatGPT will then return a refined implementation plan back to you for execution.

🔒 Important constraints
- Output exactly ONE file named: PROJECT_SPEC.md
- Keep it comprehensive but lean (≈ 2,500–4,000 words). Use tables, checklists, and concise bullets.
- Include ALL diagrams as Mermaid code blocks (no external images).
- Make pragmatic assumptions where details are missing; list them in an “Assumptions & Open Questions” table.
- Do NOT write any production code in this step.

===== REQUIRED DOCUMENT STRUCTURE (fill every section) =====

# 1) Executive Summary
- Project name and one-liner value proposition
- Primary user(s) & problem statement
- Success criteria (3–5 measurable outcomes)
- Release scope for v1 (what’s in / what’s out)
- Top risks (technical, product, schedule) with mitigations

# 2) Detailed Requirements
## 2.1 Functional Requirements (FR)
- Numbered FR-IDs with short titles and traceable descriptions
- For each: priority (Must/Should/Could), owner (TBD), acceptance criteria, and test ideas

## 2.2 Non-Functional Requirements (NFR)
- Performance SLAs (latency, throughput, batch timings)
- Reliability (error budgets, retry policies, data backup/restore)
- Security & Privacy (authn/authz model, PII handling, data retention, least privilege)
- Compliance & Licensing considerations
- Observability (logs, structured events, metrics, traces)
- Accessibility targets
- Offline/Local-first behavior (if applicable)

# 3) System Architecture
- Architecture overview (Mermaid diagram: components + data flow)
- Main sequence diagrams for key user journeys
- Data model: entities, relationships, storage choices (tables/collections with fields/types)
- External integrations/APIs (endpoints, methods, request/response shapes)
- Configuration strategy (.env, secrets, key rotation)
- Error handling & resilience patterns (timeouts, retries, circuit breakers)

# 4) Technology Choices & Trade-offs
- Shortlist of viable stacks with pros/cons
- Final recommended stack and rationale
- Third-party dependencies with license notes and known risks
- Local-only vs. cloud trade-offs and chosen path

# 5) LLM Integration Plan (if used)
- Use cases (analysis, generation, classification, orchestration)
- Prompt templates (clearly labeled) and grounding strategy
- Guardrails: validation, red-teaming hooks, cost control (token budgets), caching
- Privacy controls for prompts and outputs
- Fallback behavior when models are unavailable

# 6) Test Strategy & IV&V Hooks
- Test pyramid (unit, integration, e2e) and tools
- Example test cases mapped to FR-IDs (traceability matrix table)
- Data seeding/fixtures plan
- Performance test approach and targets
- Security testing (linting, SAST/DAST plan, dependency scanning)
- IV&V checklist for ChatGPT: what to verify, how to reproduce, expected evidence

# 7) Delivery Plan
- Work Breakdown Structure (WBS) with estimates (S/M/L), dependencies, and risk notes
- Milestones with acceptance gates and demo criteria
- Definition of Ready / Definition of Done
- Quality gates (linting, formatting, type checks, pre-commit)
- Minimal repo layout (tree) with key files and placeholders

# 8) Operability
- Environment matrix (dev/test/prod or local/CI) and how to run
- Observability implementation details (log/event schema, key metrics)
- Backup/restore and disaster recovery basics
- Release versioning strategy and change management

# 9) Assumptions & Open Questions
- Table with “Item / Type (Assumption or Question) / Impact / Proposed Resolution / Owner (ChatGPT or Me)”

# 10) Handoff Bundles
## 10.1 “For ChatGPT IV&V & Recommendations”
- A concise list of targeted questions (architecture risks, NFR sufficiency, cost & complexity, data privacy, failure modes, test sufficiency, roadmap clarity)
- Specific areas where challenge/alternatives are desired
- Any cost envelope, hardware constraints, or offline requirements to pressure test

## 10.2 “For Implementation Backlog” (to be returned after ChatGPT review)
- Inline YAML block named BACKLOG_DRAFT with epics, stories, acceptance criteria, and estimates, all linked to FR-IDs (example structure below)

```yaml
BACKLOG_DRAFT:
  epics:
    - id: E1
      title: Core Data Ingest
      stories:
        - id: S1
          fr_ids: [FR-1, FR-2]
          as_a: "user"
          i_want: "to upload files"
          so_that: "they are parsed and stored"
          acceptance:
            - "Upload accepts CSV/JSON up to 50MB"
            - "Invalid rows logged with line numbers"
          estimate: "M"

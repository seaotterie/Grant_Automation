# 12-FACTOR TRANSFORMATION: START HERE
**Quick Reference for Fresh Terminal Sessions**

**Date Created**: 2025-09-29
**Last Updated**: 2025-09-29
**Status**: Ready to begin Phase 1

---

## TL;DR - Start Implementation

```bash
# 1. Read this file first (you're doing it!)
# 2. Open the final plan
code docs/12-factor-transformation/TRANSFORMATION_PLAN_V3_FINAL.md

# 3. Begin Phase 1 (see Phase 1 Kickoff section below)
```

---

## Document Index

### 📋 **Primary Documents** (Read in Order)

1. **START_HERE.md** (this file)
   - Quick reference and orientation
   - Phase 1 kickoff checklist
   - Key commands and locations

2. **TRANSFORMATION_PLAN_V3_FINAL.md** ⭐ **MAIN PLAN**
   - Complete 9-week transformation plan
   - Two-tool architecture (screening + deep intelligence)
   - All phases, tasks, and deliverables
   - **This is your implementation guide**

3. **TWO_TOOL_ARCHITECTURE_DECISION.md**
   - Detailed architecture decision record
   - Why two tools instead of one or eight
   - Tool specifications and usage patterns

4. **AI_ARCHITECTURE_ANALYSIS.md**
   - Analysis of multiple processors vs. unified tools
   - 12-factor compliance evaluation
   - Decision rationale

### 📚 **Supporting Documents** (Reference as Needed)

5. **DESIGN_CHANGES_V3.md**
   - Strategic simplification decisions
   - What was deferred and why
   - Eliminated features (bloat removal)

6. **TRANSFORMATION_PLAN_V2.md**
   - Previous plan (superseded by V3)
   - Keep for historical reference
   - Shows original 16-week timeline

7. **GAP-ANALYSIS-PLANNING-RECORD.md**
   - Original gap analysis
   - Initial tool decomposition planning

8. **IMPLEMENTATION-PLAYBOOK.md**
   - Step-by-step implementation patterns
   - Tool development guidelines

9. **TOOL-REGISTRY.md**
   - Complete tool catalog (52 original plan)
   - Now reference only - V3 plan has 19 tools

---

## Current Status Snapshot

### ✅ **Completed (17%)**
- 9 tools already operational
  - 3 XML parsers (990, 990-PF, 990-EZ)
  - 6 data processing tools (BMF, Form990 analysis, etc.)
- Branch: `feature/bmf-filter-tool-12factor`

### 🎯 **Next Up: Phase 1 (Week 1)**
- Foundation infrastructure
- Repo cleanup
- Tool registry & framework setup

### 📊 **Transformation Overview**
- **Timeline**: 9 weeks to production
- **From**: 43 processors → **To**: 19 tools
- **AI Consolidation**: 8 processors → 2 unified tools
- **Architecture**: Two-tool pipeline with human gateway

---

## Phase 1 Kickoff: Immediate Next Steps

### Day 1 Morning: Repo Cleanup 🧹

```bash
# 1. Check current branch
git status
git branch

# 2. Create Phase 1 branch (if not already on feature branch)
git checkout -b phase-1-foundation

# 3. Commit pending Playwright deletions
git status | grep "deleted:"
git add .
git commit -m "CLEANUP: Remove Playwright test artifacts (~100 files)"

# 4. Create deprecation structure
mkdir -p src/processors/_deprecated
mkdir -p tests/deprecated_processor_tests
```

**Checklist**:
- [ ] Commit Playwright deletions (~100 files)
- [ ] Create `src/processors/_deprecated/` directory
- [ ] Create `tests/deprecated_processor_tests/` directory
- [ ] Update `.gitignore` for test artifacts
- [ ] Create `DEPRECATED_PROCESSORS.md` tracking doc

### Day 1 Afternoon: Tool Infrastructure

```bash
# 1. Create core infrastructure directories
mkdir -p src/core/tool_framework
mkdir -p src/workflows
mkdir -p tools/templates

# 2. Start with base tool class
# Create: src/core/tool_framework/base_tool.py
```

**Checklist**:
- [ ] Create `src/core/tool_registry.py`
- [ ] Create `src/core/tool_framework/base_tool.py`
- [ ] Create `src/core/tool_framework/baml_validator.py`
- [ ] Create `tools/templates/tool_template/` structure
- [ ] Create `TOOL_DEVELOPMENT_GUIDE.md`

### Day 2: Workflow Engine Foundation

```bash
# Create workflow engine
mkdir -p src/workflows/engine
mkdir -p src/workflows/schemas

# Create workflow parser and executor
```

**Checklist**:
- [ ] Create `src/workflows/workflow_parser.py`
- [ ] Create `src/workflows/workflow_engine.py`
- [ ] Design workflow YAML schema
- [ ] Create workflow testing framework
- [ ] Update `CLAUDE.md` with transformation status

---

## Key File Locations

### 📁 **Planning Documents**
```
docs/12-factor-transformation/
├── START_HERE.md                      # This file
├── TRANSFORMATION_PLAN_V3_FINAL.md    # Main plan ⭐
├── TWO_TOOL_ARCHITECTURE_DECISION.md
├── AI_ARCHITECTURE_ANALYSIS.md
└── DESIGN_CHANGES_V3.md
```

### 🔧 **Existing Tools** (Already Complete)
```
tools/
├── xml-990-parser-tool/
├── xml-990pf-parser-tool/
├── xml-990ez-parser-tool/
├── bmf-filter-tool/
├── form990-analysis-tool/
├── form990-propublica-tool/
├── foundation-grant-intelligence-tool/
├── propublica-api-enrichment-tool/
└── xml-schedule-parser-tool/
```

### 🏗️ **To Be Created** (Phase 1)
```
src/core/
├── tool_registry.py               # Central tool registry
└── tool_framework/
    ├── base_tool.py               # Base class for all tools
    ├── baml_validator.py          # BAML schema validation
    └── tool_metadata.py           # Tool metadata models

src/workflows/
├── workflow_parser.py             # YAML workflow parser
├── workflow_engine.py             # Workflow execution engine
└── schemas/
    └── workflow.schema.yaml       # Workflow YAML schema

tools/templates/
└── tool_template/                 # Tool development template
    ├── app/
    ├── baml_src/
    ├── tests/
    ├── 12factors.toml
    └── README.md
```

### 🗑️ **Legacy Processors** (To Be Deprecated)
```
src/processors/
├── analysis/                      # 18 processors
├── data_collection/               # 6 processors
├── filtering/                     # 2 processors
├── export/                        # 1 processor
├── reports/                       # 1 processor
└── lookup/                        # 1 processor

Total: 43 processors → Will move to _deprecated/ as converted
```

---

## Quick Commands Reference

### Git
```bash
# Check status
git status
git branch

# Create Phase branch
git checkout -b phase-1-foundation

# Stage and commit
git add .
git commit -m "PHASE 1: Description"

# Push to remote
git push -u origin phase-1-foundation
```

### Testing
```bash
# Run existing tool tests
cd tools/xml-990-parser-tool
python -m pytest tests/

# Run all tool tests
python -m pytest tools/*/tests/
```

### Launch Web App
```bash
# Launch Catalynx web interface
launch_catalynx_web.bat

# Or directly
python src/web/main.py

# Access at: http://localhost:8000
```

### Documentation
```bash
# Update CLAUDE.md with progress
code CLAUDE.md

# Update tool inventory
code tools/TOOLS_INVENTORY.md

# Track deprecated processors
code DEPRECATED_PROCESSORS.md
```

---

## Two-Tool Architecture Quick Reference

### **Tool 1: Opportunity Screening Tool**
- **Purpose**: Screen 100s of opportunities → shortlist of 10s
- **Cost**: $0.02/opportunity (~$4-8 for 200)
- **Speed**: ~5 seconds per opportunity
- **Replaces**: 2 processors (ai_lite_unified + ai_heavy_light)

### **Human Gateway**
- Manual review & filtering
- Web scraping for context
- Selection of ~10 opportunities for deep analysis

### **Tool 2: Deep Intelligence Tool**
- **Purpose**: Comprehensive analysis of selected opportunities
- **Cost**: $0.75-$42.00 per opportunity (depth-dependent)
- **Speed**: 5-60 minutes per opportunity
- **Depths**: quick, standard, enhanced, complete
- **Replaces**: 6 processors (ai_heavy_deep + ai_heavy_researcher + 4 tiers)

---

## Context for New Terminal Session

### Tell Claude:
```
"I'm continuing the 12-factor transformation. We're ready to start Phase 1.
Please read docs/12-factor-transformation/TRANSFORMATION_PLAN_V3_FINAL.md
to understand the plan. We have 9 tools already complete and need to build
the tool infrastructure this week."
```

### Key Decisions Made:
1. ✅ Two unified AI tools (not one, not eight)
2. ✅ Human gateway between screening and deep analysis
3. ✅ Government grant tools deferred to Phase 9
4. ✅ Peer similarity tool eliminated as bloat
5. ✅ 9-week timeline (vs. 16 weeks original)
6. ✅ 19 core tools (vs. 52 original plan)

### Important Context:
- **Branch**: feature/bmf-filter-tool-12factor
- **System**: GPT-5 models only (DO NOT change to GPT-4)
- **Current State**: 9/19 tools complete (47% of MVP)
- **API Cost Reality**: Manageable, can consolidate processors
- **Cleanup Strategy**: Progressive deprecation, major cleanup Phase 7

---

## Success Metrics for Phase 1

At end of Week 1, you should have:
- [ ] Clean repo (Playwright artifacts committed, structure created)
- [ ] Tool registry operational
- [ ] Base tool class implemented
- [ ] BAML validator functional
- [ ] Workflow parser working
- [ ] Workflow engine basic functionality
- [ ] Tool development template created
- [ ] Documentation updated (CLAUDE.md, TOOL_DEVELOPMENT_GUIDE.md)

**Ready to proceed to Phase 2**: Two unified AI tools development

---

## Troubleshooting Common Issues

### Issue: Can't find planning documents
**Solution**: All plans in `docs/12-factor-transformation/`

### Issue: Confused about which processors to convert
**Solution**: Check Phase 2 in TRANSFORMATION_PLAN_V3_FINAL.md
- Week 2: Tool 1 (screening)
- Week 3: Tool 2 (deep intelligence)

### Issue: Not sure about tool structure
**Solution**: Look at existing tools in `tools/` directory
- xml-990-parser-tool is best reference
- Has complete 12factors.toml

### Issue: Unclear on 12-factor principles
**Solution**: Check existing tools' 12factors.toml files
- Factor 4: BAML structured outputs
- Factor 10: Single responsibility per tool
- Factor 12: Stateless execution

---

## Next Session Preparation

Before starting tomorrow:
1. ✅ Read this file (START_HERE.md)
2. ✅ Skim TRANSFORMATION_PLAN_V3_FINAL.md (focus on Phase 1)
3. ✅ Check git status and branch
4. ✅ Review existing tool structure (xml-990-parser-tool)
5. ✅ Start Phase 1 Day 1 checklist

---

## Contact & Support

If stuck, refer to:
- **Main Plan**: TRANSFORMATION_PLAN_V3_FINAL.md
- **Architecture**: TWO_TOOL_ARCHITECTURE_DECISION.md
- **Existing Tools**: Look at completed tools in `tools/` directory
- **CLAUDE.md**: System overview and current status

---

**Ready to Begin Phase 1!** 🚀

Start with repo cleanup, then tool infrastructure.
By end of Week 1, foundation will be ready for Tool 1 development.

Good luck tomorrow!
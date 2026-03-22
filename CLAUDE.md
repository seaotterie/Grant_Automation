# Catalynx — Grant Research Intelligence Platform

## Quick Start

```bash
python src/web/main.py          # dev server → http://localhost:8000
# or
launch_catalynx_web.bat         # Windows launcher
```

---

## CRITICAL: AI Model Configuration

**All AI calls use the Anthropic Claude API — do NOT use or restore OpenAI calls.**

| Use case | Model | Env var |
|----------|-------|---------|
| Fast screening / discovery | `claude-haiku-4-5-20251001` | `AI_LITE_MODEL` |
| Thorough screening / deep intelligence | `claude-sonnet-4-6` | `AI_HEAVY_MODEL` |
| Premium analysis (future) | `claude-opus-4-6` | `AI_RESEARCH_MODEL` |

**Key files:**
- `src/core/anthropic_service.py` — centralized Claude API client (use this)
- `src/core/openai_service.py` — legacy OpenAI client (do not extend; scheduled for removal)
- `.env` — set `ANTHROPIC_API_KEY` here

---

## Architecture

### Directory Layout

```
Grant_Automation/
├── tools/                   ← 24 operational 12-factor tools (main logic lives here)
│   ├── opportunity_screening_tool/   # Tool 1 — mass screening
│   ├── deep_intelligence_tool/       # Tool 2 — comprehensive analysis
│   ├── financial_intelligence_tool/  # Tool 10
│   ├── risk_intelligence_tool/       # Tool 11
│   ├── network_intelligence_tool/    # Tool 12
│   ├── multi_dimensional_scorer_tool/ # Tool 20
│   ├── report_generator_tool/        # Tool 21
│   ├── historical_funding_analyzer_tool/ # Tool 22
│   ├── web_intelligence_tool/        # Tool 25 — Scrapy-powered
│   └── ... (15 more tools in tools/)
├── src/
│   ├── core/
│   │   ├── anthropic_service.py  ← Claude API client
│   │   ├── tool_framework/       ← BaseTool, ToolResult, ToolExecutionContext
│   │   └── tool_registry.py      ← auto-discovers tools via 12factors.toml
│   ├── web/
│   │   ├── main.py               ← FastAPI app factory (~254 lines)
│   │   └── routers/              ← 25+ router files
│   ├── profiles/                 ← UnifiedProfileService
│   ├── workflows/                ← WorkflowEngine + YAML workflows
│   └── middleware/security.py    ← CORS, rate limiting, XSS, input validation
├── tests/                   ← pytest suite
├── docs/                    ← architecture + migration docs
└── data/
    ├── catalynx.db           ← application database (profiles, opportunities)
    └── nonprofit_intelligence.db ← BMF/SOI intelligence (2M+ records)
```

### Two-Stage Pipeline

```
200 opportunities
   → [Tool 1: Opportunity Screening]  $0.0004–$0.02/opp (Haiku)
   → Human gateway (review & select ~10)
   → [Tool 2: Deep Intelligence]      $2.00 Essentials / $8.00 Premium (Sonnet)
   → Report + scoring output
```

### Databases

| Database | File | Purpose |
|----------|------|---------|
| Application | `data/catalynx.db` | Profiles, opportunities, export records |
| Intelligence | `data/nonprofit_intelligence.db` | BMF (752K orgs), Form 990 (671K), 990-PF (235K), 990-EZ (411K) |

---

## 24 Operational Tools

All tools are in `tools/` and follow the 12-factor pattern (`12factors.toml` + `app/` module).

| # | Tool | Cost | Notes |
|---|------|------|-------|
| — | XML 990 Parser | $0.00 | Regular nonprofit 990s |
| — | XML 990-PF Parser | $0.00 | Private foundation filings |
| — | XML 990-EZ Parser | $0.00 | Small nonprofit filings |
| — | XML Schedule Parser | $0.00 | Schedule extraction |
| — | BMF Filter | $0.00 | IRS Business Master File |
| — | Form 990 Analysis | $0.00 | Financial metrics |
| — | Form 990 ProPublica | varies | ProPublica API enrichment |
| — | ProPublica API Enrichment | varies | Additional enrichment |
| — | Foundation Grant Intelligence | $0.03 | Grant-making analysis |
| 1 | Opportunity Screening | $0.0004–$0.02 | Fast/thorough modes |
| 2 | Deep Intelligence | $0.05–$0.10 AI | Essentials $2 / Premium $8 |
| 10 | Financial Intelligence | $0.03 | 15+ financial metrics |
| 11 | Risk Intelligence | $0.02 | 6-dimensional risk |
| 12 | Network Intelligence | $0.04 | Board network analysis |
| 13 | Schedule I Grant Analyzer | $0.03 | Foundation grant patterns |
| 14 | Foundation Grantee Bundling | $0.00 | Co-funding analysis |
| 16 | Data Validator | $0.00 | Schema validation |
| 17 | EIN Validator | $0.00 | EIN format + lookup |
| 18 | Data Export | $0.00 | JSON/CSV/Excel/PDF |
| 19 | Grant Package Generator | $0.00 | Application assembly |
| 20 | Multi-Dimensional Scorer | $0.00 | 5-stage scoring |
| 21 | Report Generator | $0.00 | Jinja2 HTML reports |
| 22 | Historical Funding Analyzer | $0.00 | USASpending patterns |
| 25 | Web Intelligence | $0.05–$0.25 | Scrapy web scraping |

---

## Development

### Key Commands

```bash
# Tests
pytest tests/unit/ tools/*/tests/           # fast unit tests
pytest -m integration                        # integration tests
pytest --cov=src --cov=tools                 # with coverage

# Lint / format
ruff check src/ tools/
ruff format src/ tools/

# Type check
mypy src/web/main.py src/web/routers/ --ignore-missing-imports
```

### Core Principles

1. **Use `src/core/anthropic_service.py`** for all AI calls — never call the Anthropic API directly from routers or tools.
2. **Tools go in `tools/`** — each tool gets its own directory with `12factors.toml`, `app/`, and `tests/`.
3. **Stateless tools** — no persistent state between `execute()` calls.
4. **Structured outputs** — use `ToolResult[T]` wrappers; never return raw dicts from tools.
5. **No new processors in `src/processors/`** — that directory is deprecated; use the tool framework instead.

### Adding a New Tool

```
tools/my_new_tool/
├── 12factors.toml     # tool metadata
├── README.md
├── app/
│   ├── __init__.py
│   ├── my_tool.py     # class MyNewTool(BaseTool[MyOutput])
│   └── my_models.py   # dataclass inputs/outputs
└── tests/
    ├── conftest.py
    └── test_my_tool.py
```

Inherit from `src.core.tool_framework.BaseTool` and implement `_execute()`.

---

## Relevant Docs

| Document | Purpose |
|----------|---------|
| `docs/CODE_REVIEW_AND_PLAN.md` | Active improvement plan (Phases A–F) |
| `docs/TOOL_ARCHITECTURE_MAPPING.md` | Tool ↔ processor mapping |
| `docs/MIGRATION_HISTORY.md` | Full transformation timeline |
| `docs/TODO_TRIAGE.md` | 39 TODO/FIXME markers categorised |
| `CONTRIBUTING.md` | Setup instructions for new contributors |
| `tools/TOOLS_INVENTORY.md` | Complete tool inventory |

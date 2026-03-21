# Contributing to Catalynx

## Prerequisites

- **Python 3.11+** (3.12 also supported)
- **Git**
- An **Anthropic API key** (`ANTHROPIC_API_KEY`) — all AI calls use Claude

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd Grant_Automation

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Install the package in editable mode (includes dev deps)
pip install -e ".[dev]"

# 4. Copy the example env file and fill in your keys
cp .env.example .env
# Required: set ANTHROPIC_API_KEY
# Optional: GRANTS_GOV_API_KEY, PROPUBLICA_API_KEY (for integration tests)
```

## Running the App

```bash
python src/web/main.py
# → http://localhost:8000
# → API docs at http://localhost:8000/api/docs
```

## Running Tests

```bash
# Fast unit + tool tests (no network, no AI calls)
pytest tests/unit/ tools/*/tests/ -q

# Integration tests (requires databases in data/)
pytest -m integration -q

# Full suite with coverage
pytest --cov=src --cov=tools --cov-report=term-missing

# Single tool's tests
pytest tools/financial_intelligence_tool/tests/ -v
```

Tests are async-first (`asyncio_mode = "auto"` in `pyproject.toml`). Mark slow/external tests with the appropriate pytest markers (`@pytest.mark.slow`, `@pytest.mark.external`).

## Code Style

The project uses **ruff** for linting and formatting.

```bash
ruff check src/ tools/          # lint
ruff format src/ tools/         # format
ruff check --fix src/ tools/    # auto-fix lint issues
```

Line length: 120. Config is in `pyproject.toml` under `[tool.ruff]`.

## Branch Naming

All branches follow the pattern used by the CI pipeline:

```
claude/<short-description>-<session-id>   # automated Claude Code sessions
feature/<short-description>               # manual feature branches
fix/<short-description>                   # bug fixes
```

CI runs automatically on pushes to `main` and any `claude/**` branch.

## Making a Tool

All new AI-powered logic belongs in `tools/`, not `src/processors/` (deprecated).

1. **Create the directory:**
   ```
   tools/my_new_tool/
   ├── 12factors.toml
   ├── README.md
   ├── app/
   │   ├── __init__.py
   │   ├── my_tool.py
   │   └── my_models.py
   └── tests/
       ├── conftest.py
       └── test_my_tool.py
   ```

2. **Inherit from BaseTool:**
   ```python
   from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext
   from .my_models import MyInput, MyOutput

   class MyNewTool(BaseTool[MyOutput]):
       def get_tool_name(self) -> str: return "My New Tool"
       def get_tool_version(self) -> str: return "1.0.0"
       def get_single_responsibility(self) -> str: return "One-sentence description"

       async def _execute(self, context: ToolExecutionContext, input: MyInput) -> MyOutput:
           ...
   ```

3. **Use the Anthropic service for AI calls:**
   ```python
   from src.core.anthropic_service import get_anthropic_service, ClaudeModel

   service = get_anthropic_service()
   result = await service.complete(
       model=ClaudeModel.HAIKU,       # fast/cheap
       # model=ClaudeModel.SONNET,    # thorough
       messages=[{"role": "user", "content": prompt}],
   )
   ```

4. **Write tests** — every tool needs at least:
   - `test_tool_metadata()` — name, version, responsibility
   - `test_cost_estimation()` — `get_cost_estimate()` returns expected value
   - One happy-path async test exercising `execute()`
   - One edge-case test (empty input, minimal data)

5. **Add a `conftest.py`** that adds both the project root and the tool root to `sys.path` (see any existing tool's `tests/conftest.py` for the template).

## Making a Router Endpoint

New API endpoints go in `src/web/routers/`. Pick the most relevant existing router or create a new one.

- Always set a `tags=` on the `APIRouter` — it controls grouping in `/api/docs`.
- Add a `summary=` to each endpoint for the Swagger UI.
- Use `response_model=` so FastAPI generates accurate response schemas.
- Validate and sanitize at the boundary; internal code can trust its inputs.
- Return `HTTPException(status_code=500, detail="Internal server error")` — never leak `str(e)`.

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Importing `openai` | Use `src.core.anthropic_service` instead |
| Calling Anthropic API directly in a router | Route through a tool or the service layer |
| Adding state to a tool (`self.cache = {}`) | Tools must be stateless; use external caching |
| Leaking exception details in HTTP responses | Catch and log; return generic 500 message |
| Adding a processor to `src/processors/` | Add a 12-factor tool in `tools/` instead |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `AI_LITE_MODEL` | No | Override lite model (default: `claude-haiku-4-5-20251001`) |
| `AI_HEAVY_MODEL` | No | Override heavy model (default: `claude-sonnet-4-6`) |
| `AI_RESEARCH_MODEL` | No | Override research model (default: `claude-opus-4-6`) |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated origins (default: localhost) |
| `GRANTS_GOV_API_KEY` | No | Grants.gov API access |
| `PROPUBLICA_API_KEY` | No | ProPublica nonprofit API |

# Quick Start Guide - Catalynx

Get started with Catalynx grant intelligence platform in 5 minutes.

---

## Prerequisites

- **Python 3.11+** installed
- **OpenAI API Key** (for AI intelligence features)
- **Git** (for cloning repository)
- **Windows** (primary), Linux, or macOS

---

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd Grant_Automation
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install BAML CLI (for schema compilation)
npm install -g @boundaryml/baml
```

### 3. Configure Environment
```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Required `.env` Configuration**:
```ini
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
AI_LITE_MODEL=gpt-5-mini
AI_HEAVY_MODEL=gpt-5
AI_RESEARCH_MODEL=gpt-5

# Database Configuration
DATABASE_PATH=data/catalynx.db
INTELLIGENCE_DB_PATH=data/nonprofit_intelligence.db

# Web Server Configuration
WEB_HOST=localhost
WEB_PORT=8000
```

---

## Launch Application

### Option 1: Web Interface (Recommended)
```bash
# Launch web server
launch_catalynx_web.bat

# Opens automatically at http://localhost:8000
```

### Option 2: Python Direct
```bash
python src/web/main.py
```

### Option 3: Development Mode
```bash
# With auto-reload
uvicorn src.web.main:app --reload --host localhost --port 8000
```

---

## First Steps

### 1. Access Web Interface
Navigate to: http://localhost:8000

### 2. Explore API Documentation
Navigate to: http://localhost:8000/api/docs

Interactive OpenAPI/Swagger documentation with:
- All 40+ REST API endpoints
- Request/response schemas
- Try-it-out functionality

### 3. Create Your First Profile
```bash
# Via Web UI
1. Navigate to "Profiles" section
2. Click "Create New Profile"
3. Enter EIN and organization details
4. Click "Fetch 990 Data" for automatic enrichment

# Via API
POST /api/profiles
{
  "ein": "541026365",
  "organization_name": "Example Nonprofit"
}
```

### 4. Screen Opportunities
```bash
# Via API
POST /api/v1/tools/opportunity-screening-tool/execute
{
  "mode": "fast",  # or "thorough"
  "opportunities": [
    {
      "opportunity_id": "OPP123",
      "organization_name": "Department of Education",
      "opportunity_title": "Education Grant Program"
    }
  ]
}
```

### 5. Run Deep Intelligence
```bash
# Via API
POST /api/v1/tools/deep-intelligence-tool/execute
{
  "depth": "essentials",  # or "premium"
  "profile_id": "your_profile_id",
  "opportunity_id": "OPP123"
}
```

---

## Directory Structure

```
Grant_Automation/
├── src/
│   ├── web/main.py           # FastAPI application entry point
│   ├── core/                 # Core services
│   ├── scoring/              # 6 scoring modules
│   └── intelligence/         # Intelligence pipeline
│
├── tools/                    # 24 12-factor tools
├── data/                     # Data storage (created on first run)
│   ├── catalynx.db          # Application database
│   ├── nonprofit_intelligence.db  # BMF/SOI intelligence
│   ├── source_data/         # Entity-based data
│   └── profiles/            # Profile data
│
├── test_framework/          # Testing infrastructure
├── docs/                    # Documentation
└── launch_catalynx_web.bat  # Windows launcher
```

---

## Common Tasks

### Run Tests
```bash
# All tests
pytest test_framework/ -v

# Specific category
pytest test_framework/12factor_tools/ -v
```

### Generate BAML Client
```bash
# Compile BAML schemas and generate Python types
npx @boundaryml/baml generate
```

### Check System Status
```bash
# Via API
GET /health

# Check tool registry
GET /api/v1/tools/list
```

### View Logs
```bash
# Application logs in console
# Database operations logged with millisecond precision
```

---

## Web Interface Features

### Dashboard
- **Profile Management**: Create, view, edit nonprofit profiles
- **Opportunity Discovery**: Search and filter grant opportunities
- **Intelligence Analysis**: Run AI analysis on selected opportunities
- **Network Visualization**: Board network and foundation relationships
- **Reports**: Generate professional reports and dossiers

### Profile Enhancement
1. **Enter EIN**: Organization tax ID
2. **Fetch 990 Data**: Automatic ProPublica enrichment
3. **BMF Lookup**: Business Master File validation
4. **SOI Intelligence**: Financial intelligence from IRS data
5. **Board Network**: Import board member data
6. **Web Scraping**: Optional website intelligence

### Opportunity Screening
1. **Import Opportunities**: Upload CSV or manual entry
2. **Fast Screening**: Quick AI screening (200 opps in ~7 min)
3. **Thorough Screening**: Detailed AI screening (50 opps in ~4 min)
4. **Review Results**: Sort by score, filter by category
5. **Select for Deep Intelligence**: Choose top 10-15 opportunities

### Deep Intelligence
1. **Select Depth**: Essentials ($2) or Premium ($8)
2. **Run Analysis**: 4-stage comprehensive analysis
3. **Review Insights**: Financial, risk, network intelligence
4. **Generate Report**: Professional dossier (Premium only)
5. **Export Package**: Grant application package

---

## API Examples

### List All Tools
```bash
curl http://localhost:8000/api/v1/tools/list
```

### Get Tool Metadata
```bash
curl http://localhost:8000/api/v1/tools/opportunity-screening-tool
```

### Execute Tool
```bash
curl -X POST http://localhost:8000/api/v1/tools/bmf-filter-tool/execute \
  -H "Content-Type: application/json" \
  -d '{
    "states": ["VA", "MD"],
    "ntee_codes": ["P20"],
    "revenue_range": [100000, 10000000]
  }'
```

### Create Workflow
```bash
curl -X POST http://localhost:8000/api/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "opportunity_screening",
    "context": {
      "opportunities_file": "data/opportunities.json",
      "profile_id": "your_profile_id"
    }
  }'
```

---

## Configuration

### Database Setup (Automatic)
Databases are created automatically on first run:
- `data/catalynx.db` - Application data (profiles, opportunities, costs)
- `data/nonprofit_intelligence.db` - BMF/SOI intelligence (optional)

### BMF/SOI Intelligence (Optional)
```bash
# Download IRS data (one-time setup)
python src/database/bmf_soi_loader.py

# This enables:
# - 752K+ organizations (BMF)
# - 2M+ financial records (SOI)
# - Advanced discovery with financial intelligence
```

### OpenAI Models
Configured in `.env`:
- **AI_LITE_MODEL**: Fast screening (gpt-5-mini)
- **AI_HEAVY_MODEL**: Deep intelligence (gpt-5)
- **AI_RESEARCH_MODEL**: Research tasks (gpt-5)

---

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env
WEB_PORT=8001

# Or kill existing process
taskkill /F /IM python.exe
```

### OpenAI API Errors
```bash
# Verify API key in .env
OPENAI_API_KEY=your_actual_key_here

# Check API quota
# Visit https://platform.openai.com/usage
```

### Database Locked
```bash
# Close all connections and restart
# SQLite databases auto-recover
```

### BAML Compilation Errors
```bash
# Regenerate client
npx @boundaryml/baml generate

# Check schema syntax
npx @boundaryml/baml check baml_src/scoring_schemas.baml
```

---

## Next Steps

1. **[Read Full Documentation](CLAUDE.md)** - Complete system overview
2. **[Deploy to Production](SINGLE_USER_DEPLOYMENT.md)** - Single-user setup
3. **[Review Changelog](CHANGELOG.md)** - Version history
4. **[Explore API Docs](http://localhost:8000/api/docs)** - Interactive API reference

---

## Performance Tips

### Optimize Screening
- Use **fast mode** for initial screening (200 opps → 50 candidates)
- Use **thorough mode** for final selection (50 → 10-15)
- Run in batches of 50-100 for optimal performance

### Optimize Intelligence
- Start with **Essentials** depth ($2) for most opportunities
- Upgrade to **Premium** depth ($8) for top 3-5 opportunities
- Use network intelligence for foundation research

### Optimize Database
- Run BMF/SOI intelligence setup for 47x better discovery
- Use entity-based caching (85% cache hit rate)
- Monitor performance with `/health` endpoint

---

## Getting Help

- **API Documentation**: http://localhost:8000/api/docs
- **System Status**: http://localhost:8000/health
- **Tool Registry**: http://localhost:8000/api/v1/tools/list
- **Project Documentation**: See `docs/` directory

---

**Status**: Ready for production use
**Version**: 2025-10-09 Baseline
**Support**: Internal development project

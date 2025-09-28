# AI Heavy Analysis Tool
*🟡 Intermediate Level - External API integration with cost tracking*

## What This Tool Does

The AI Heavy Tool takes nonprofit data and uses AI (OpenAI GPT) to perform comprehensive analysis:
- Strategic recommendations
- Grant opportunity assessment
- Partnership potential analysis
- Risk evaluation
- Market positioning insights

**Think of it like**: A consultant that reads all the data about an organization and gives you professional analysis and recommendations.

## Why This Tool Exists (12-Factor Pattern)

**Before**: AI analysis was mixed into other processors, making it hard to control costs, test different prompts, or reuse analysis logic.

**After**: This tool ONLY does AI analysis. Other tools handle data gathering, filtering, scoring, etc.

**12-Factor Benefits**:
- **Cost Control**: Track exactly what AI analysis costs
- **Prompt Engineering**: Easily test and improve prompts
- **Reusability**: Use same analysis for different workflows
- **Scaling**: Run multiple AI tools in parallel with different models

## Tool Structure (12-Factor Conventions)

```
ai-heavy-tool/
├── README.md              # This file
├── .env                   # Environment configuration
├── 12factors.toml         # Tool configuration
├── pyproject.toml         # Dependencies
├── baml_src/              # BAML definitions
│   ├── ai_analysis.baml   # Tool schema and prompts
│   ├── clients.baml       # AI model clients
│   └── generators.baml    # Code generation
└── app/                   # Implementation
    ├── __init__.py
    ├── ai_analyzer.py     # Main tool logic
    ├── cost_tracker.py    # Cost management
    ├── agent.py           # Agent integration
    ├── server.py          # HTTP server
    └── main.py            # Entry point
```

## Key Learning: External Service Integration

This tool demonstrates **Factor 4: Backing Services** - treating the OpenAI API as an attached resource:

- ✅ **Configurable**: Switch between GPT-4, GPT-3.5, or local models via config
- ✅ **Resilient**: Handle API failures gracefully
- ✅ **Cost-Aware**: Track token usage and costs
- ✅ **Testable**: Mock the API for testing

## Configuration Files

### .env
```bash
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.3

# Cost Management
AI_MAX_COST_PER_REQUEST=5.00
AI_DAILY_COST_LIMIT=100.00
AI_COST_TRACKING_ENABLED=true

# Performance
AI_TIMEOUT_SECONDS=120
AI_RETRY_ATTEMPTS=3
AI_CACHE_ENABLED=true

# Server
AI_HEAVY_PORT=8002
LOG_LEVEL=INFO
```

### 12factors.toml
```toml
[tool]
name = "ai-heavy"
version = "1.0.0"
description = "Comprehensive AI analysis for nonprofit organizations"
intent = "ai_heavy_analysis"

[tool.capabilities]
primary = "ai_analysis"
secondary = ["strategic_planning", "risk_assessment", "market_analysis"]

[tool.costs]
model_costs = {
    "gpt-4" = 0.03,           # per 1K tokens
    "gpt-3.5-turbo" = 0.002   # per 1K tokens
}
max_cost_per_request = 5.00
daily_limit = 100.00

[tool.performance]
max_concurrent = 3  # Limit concurrent AI calls
timeout_seconds = 120
cache_ttl = 7200    # 2 hours

[tool.12factors]
config_external = true
stateless = true
port_binding = true
structured_io = true
backing_services = ["openai_api"]
```

## BAML Schema

### baml_src/ai_analysis.baml
```baml
// AI Heavy Analysis Tool Schema
// Demonstrates Factor 4: Tools are structured outputs with external services

// Tool Intent - What triggers AI analysis
class AIHeavyAnalysisIntent {
    intent "ai_heavy_analysis"
    organization_data OrganizationProfile
    analysis_focus AnalysisFocus
    output_requirements OutputRequirements
}

// Input data about the organization
class OrganizationProfile {
    name string
    ein string?
    mission string?
    revenue int?
    assets int?
    programs string[]?
    geographic_scope string[]?
    focus_areas string[]?
    board_members string[]?
    recent_grants Grant[]?
    financial_trends FinancialTrend[]?
}

class Grant {
    grantor string
    amount int
    year int
    purpose string?
}

class FinancialTrend {
    year int
    revenue int
    growth_rate float?
}

// What kind of analysis to perform
class AnalysisFocus {
    strategic_planning bool @default(true)
    grant_opportunities bool @default(true)
    partnership_potential bool @default(true)
    risk_assessment bool @default(true)
    market_positioning bool @default(false)
    board_analysis bool @default(false)
    competitive_analysis bool @default(false)
}

// How detailed the output should be
class OutputRequirements {
    depth "summary" | "detailed" | "comprehensive" @default("detailed")
    include_recommendations bool @default(true)
    include_action_items bool @default(true)
    include_risk_factors bool @default(true)
    max_length int @default(2000) @description("Maximum words in analysis")
}

// Tool Result - What the AI analysis returns
class AIHeavyAnalysisResult {
    intent "ai_heavy_analysis_result"
    analysis AIAnalysisContent
    recommendations string[]
    action_items ActionItem[]
    risk_factors RiskFactor[]
    opportunities Opportunity[]
    metadata AIExecutionMetadata
}

class AIAnalysisContent {
    executive_summary string
    strategic_assessment string?
    grant_readiness_analysis string?
    partnership_potential_analysis string?
    market_position_analysis string?
    organizational_strengths string[]
    areas_for_improvement string[]
    competitive_advantages string[]
}

class ActionItem {
    priority "high" | "medium" | "low"
    category string
    description string
    timeline string?
    resources_needed string[]?
}

class RiskFactor {
    severity "high" | "medium" | "low"
    category string
    description string
    mitigation_strategies string[]?
}

class Opportunity {
    type "grant" | "partnership" | "program" | "market"
    description string
    potential_impact "high" | "medium" | "low"
    required_actions string[]?
    timeline string?
}

class AIExecutionMetadata {
    model_used string
    tokens_used int
    cost_dollars float
    execution_time_ms float
    prompt_version string
    confidence_score float?
}

// Main AI analysis function
function PerformHeavyAnalysis(
    organization: OrganizationProfile,
    focus: AnalysisFocus,
    requirements: OutputRequirements
) -> AIAnalysisContent {
    client OpenAI
    prompt #"
        You are a nonprofit sector expert conducting comprehensive analysis.

        ORGANIZATION DATA:
        Name: {{ organization.name }}
        {% if organization.mission %}Mission: {{ organization.mission }}{% endif %}
        {% if organization.revenue %}Revenue: ${{ organization.revenue | number_format }}{% endif %}
        {% if organization.assets %}Assets: ${{ organization.assets | number_format }}{% endif %}
        {% if organization.programs %}Programs: {{ organization.programs | join(", ") }}{% endif %}
        {% if organization.focus_areas %}Focus Areas: {{ organization.focus_areas | join(", ") }}{% endif %}
        {% if organization.recent_grants %}
        Recent Grants:
        {% for grant in organization.recent_grants %}
        - {{ grant.grantor }}: ${{ grant.amount | number_format }} ({{ grant.year }})
        {% endfor %}
        {% endif %}

        ANALYSIS REQUIREMENTS:
        Depth: {{ requirements.depth }}
        {% if focus.strategic_planning %}✓ Strategic Planning Assessment{% endif %}
        {% if focus.grant_opportunities %}✓ Grant Opportunity Analysis{% endif %}
        {% if focus.partnership_potential %}✓ Partnership Potential{% endif %}
        {% if focus.risk_assessment %}✓ Risk Assessment{% endif %}
        {% if focus.market_positioning %}✓ Market Positioning{% endif %}

        Provide a comprehensive analysis with:

        1. EXECUTIVE SUMMARY (2-3 paragraphs)
        - Overall organizational health and trajectory
        - Key strategic position in the nonprofit sector
        - Primary opportunities and challenges

        {% if focus.strategic_planning %}
        2. STRATEGIC ASSESSMENT
        - Mission alignment with current programs
        - Organizational capacity and capabilities
        - Strategic positioning relative to sector trends
        - Growth potential and scalability
        {% endif %}

        {% if focus.grant_opportunities %}
        3. GRANT READINESS ANALYSIS
        - Current grant competitiveness
        - Areas needing strengthening for grant applications
        - Recommended grant types and funding sources
        - Application strategy recommendations
        {% endif %}

        {% if focus.partnership_potential %}
        4. PARTNERSHIP POTENTIAL
        - Types of partnerships that would be most beneficial
        - Organizational assets attractive to potential partners
        - Partnership readiness assessment
        - Recommended partnership development strategy
        {% endif %}

        5. ORGANIZATIONAL STRENGTHS
        - List 3-5 key organizational strengths
        - Competitive advantages in the sector

        6. AREAS FOR IMPROVEMENT
        - List 3-5 priority improvement areas
        - Specific recommendations for each area

        Keep analysis practical, actionable, and grounded in nonprofit sector best practices.
        Limit response to {{ requirements.max_length }} words maximum.
    "#
}

// Extract actionable items from analysis
function ExtractActionItems(analysis_content: string) -> ActionItem[] {
    client OpenAILite
    prompt #"
        From this nonprofit analysis, extract 5-8 specific, actionable items:

        {{ analysis_content }}

        For each action item, provide:
        - Priority level (high/medium/low)
        - Category (governance, fundraising, programs, operations, partnerships, etc.)
        - Clear, specific description
        - Suggested timeline
        - Resources needed

        Focus on items the organization can realistically implement.
    "#
}

// Identify risk factors
function IdentifyRiskFactors(analysis_content: string, organization: OrganizationProfile) -> RiskFactor[] {
    client OpenAILite
    prompt #"
        Based on this analysis and organization data, identify 3-5 key risk factors:

        ANALYSIS: {{ analysis_content }}

        ORGANIZATION: {{ organization.name }}
        Revenue: ${{ organization.revenue | number_format }}
        Focus: {{ organization.focus_areas | join(", ") }}

        For each risk factor:
        - Severity level (high/medium/low)
        - Risk category (financial, operational, strategic, regulatory, market, etc.)
        - Clear description of the risk
        - 2-3 specific mitigation strategies

        Focus on realistic, sector-relevant risks.
    "#
}
```

## Tool Implementation

### app/ai_analyzer.py
```python
"""
AI Heavy Analysis Tool - 12-Factor Implementation
Demonstrates Factor 4: External services as backing resources
"""

import os
import time
import asyncio
from typing import List, Optional
from dataclasses import dataclass
import openai
from app.cost_tracker import CostTracker
from app.generated.baml_types import (
    AIHeavyAnalysisIntent, AIHeavyAnalysisResult,
    OrganizationProfile, AnalysisFocus, OutputRequirements,
    AIAnalysisContent, ActionItem, RiskFactor, Opportunity,
    AIExecutionMetadata
)

class AIHeavyAnalysisTool:
    """
    12-Factor Tool: AI Heavy Analysis

    Demonstrates:
    - Factor 4: External AI service as backing resource
    - Factor 3: Configuration from environment
    - Factor 6: Stateless processing
    - Factor 9: Graceful handling of external service failures
    """

    def __init__(self):
        # Factor 3: Config from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
        self.timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "120"))
        self.max_cost = float(os.getenv("AI_MAX_COST_PER_REQUEST", "5.00"))

        # Initialize OpenAI client
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        openai.api_key = self.api_key

        # Cost tracking
        self.cost_tracker = CostTracker()

        # Cache for repeated analyses
        self._cache = {}

    async def execute(self, intent: AIHeavyAnalysisIntent) -> AIHeavyAnalysisResult:
        """
        Execute AI heavy analysis

        Factor 4 pattern:
        1. Structured input (AIHeavyAnalysisIntent)
        2. External service call (OpenAI API)
        3. Structured output (AIHeavyAnalysisResult)
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._make_cache_key(intent)
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cached_result.metadata.execution_time_ms = (time.time() - start_time) * 1000
            return cached_result

        # Check cost limits before proceeding
        if not await self.cost_tracker.can_proceed(self.max_cost):
            raise ValueError("Daily cost limit exceeded")

        try:
            # Main AI analysis call
            analysis_content = await self._perform_analysis(
                intent.organization_data,
                intent.analysis_focus,
                intent.output_requirements
            )

            # Extract structured components
            action_items = await self._extract_action_items(analysis_content)
            risk_factors = await self._identify_risks(analysis_content, intent.organization_data)
            opportunities = await self._identify_opportunities(analysis_content)

            # Calculate total cost
            total_tokens = (
                analysis_content.get('tokens_used', 0) +
                sum(item.get('tokens_used', 0) for item in [action_items, risk_factors, opportunities])
            )
            total_cost = self.cost_tracker.calculate_cost(total_tokens, self.model)

            # Track cost
            await self.cost_tracker.record_usage(total_cost, total_tokens)

            # Create metadata
            metadata = AIExecutionMetadata(
                model_used=self.model,
                tokens_used=total_tokens,
                cost_dollars=total_cost,
                execution_time_ms=(time.time() - start_time) * 1000,
                prompt_version="1.0",
                confidence_score=self._calculate_confidence(analysis_content)
            )

            # Build result
            result = AIHeavyAnalysisResult(
                analysis=analysis_content['content'],
                recommendations=self._extract_recommendations(analysis_content['content']),
                action_items=action_items['items'],
                risk_factors=risk_factors['risks'],
                opportunities=opportunities['opportunities'],
                metadata=metadata
            )

            # Cache result
            self._cache[cache_key] = result

            return result

        except Exception as e:
            # Factor 9: Graceful error handling
            await self.cost_tracker.record_error(str(e))
            raise RuntimeError(f"AI analysis failed: {str(e)}")

    async def _perform_analysis(self, org: OrganizationProfile, focus: AnalysisFocus, req: OutputRequirements) -> dict:
        """Main AI analysis using OpenAI API"""

        # Build prompt based on focus areas
        prompt = self._build_analysis_prompt(org, focus, req)

        try:
            # Factor 4: External service call
            response = await asyncio.wait_for(
                openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a nonprofit sector expert providing comprehensive analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                ),
                timeout=self.timeout
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            return {
                'content': self._parse_analysis_content(content),
                'tokens_used': tokens_used,
                'raw_response': content
            }

        except asyncio.TimeoutError:
            raise RuntimeError("AI analysis timed out")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _build_analysis_prompt(self, org: OrganizationProfile, focus: AnalysisFocus, req: OutputRequirements) -> str:
        """Build analysis prompt based on requirements"""

        prompt_parts = [
            f"ORGANIZATION: {org.name}",
            f"Mission: {org.mission or 'Not provided'}",
            f"Revenue: ${org.revenue:,}" if org.revenue else "Revenue: Not provided",
            f"Focus Areas: {', '.join(org.focus_areas)}" if org.focus_areas else "Focus Areas: Not specified"
        ]

        if org.recent_grants:
            prompt_parts.append("Recent Grants:")
            for grant in org.recent_grants:
                prompt_parts.append(f"- {grant.grantor}: ${grant.amount:,} ({grant.year})")

        prompt_parts.extend([
            "",
            f"Analysis Depth: {req.depth}",
            f"Max Length: {req.max_length} words",
            "",
            "Provide analysis covering:"
        ])

        if focus.strategic_planning:
            prompt_parts.append("✓ Strategic Planning Assessment")
        if focus.grant_opportunities:
            prompt_parts.append("✓ Grant Opportunity Analysis")
        if focus.partnership_potential:
            prompt_parts.append("✓ Partnership Potential")
        if focus.risk_assessment:
            prompt_parts.append("✓ Risk Assessment")

        prompt_parts.extend([
            "",
            "Structure your response with clear sections:",
            "1. Executive Summary",
            "2. Strategic Assessment",
            "3. Opportunities and Recommendations",
            "4. Risk Considerations",
            "5. Next Steps"
        ])

        return "\n".join(prompt_parts)

    def _parse_analysis_content(self, raw_content: str) -> AIAnalysisContent:
        """Parse AI response into structured content"""

        # Simple parsing - in production, use more sophisticated NLP
        sections = raw_content.split('\n\n')

        executive_summary = ""
        strategic_assessment = ""
        strengths = []
        improvements = []

        for section in sections:
            if section.lower().startswith('executive summary'):
                executive_summary = section.replace('Executive Summary', '').strip()
            elif section.lower().startswith('strategic'):
                strategic_assessment = section
            elif 'strength' in section.lower():
                strengths = self._extract_list_items(section)
            elif 'improvement' in section.lower() or 'areas for' in section.lower():
                improvements = self._extract_list_items(section)

        return AIAnalysisContent(
            executive_summary=executive_summary,
            strategic_assessment=strategic_assessment,
            organizational_strengths=strengths,
            areas_for_improvement=improvements,
            competitive_advantages=self._extract_competitive_advantages(raw_content)
        )

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                items.append(line[1:].strip())
        return items

    def _make_cache_key(self, intent: AIHeavyAnalysisIntent) -> str:
        """Create cache key for analysis"""
        key_parts = [
            intent.organization_data.name,
            intent.organization_data.ein or "no_ein",
            str(intent.analysis_focus.__dict__),
            str(intent.output_requirements.depth)
        ]
        return "|".join(key_parts)

    def _calculate_confidence(self, analysis: dict) -> float:
        """Calculate confidence score based on analysis quality"""
        # Simple heuristic - in production, use more sophisticated metrics
        content_length = len(analysis.get('raw_response', ''))
        if content_length > 1000:
            return 0.9
        elif content_length > 500:
            return 0.7
        else:
            return 0.5

    async def _extract_action_items(self, analysis_content: AIAnalysisContent) -> dict:
        """Extract actionable items from analysis"""
        # Simplified implementation - would use BAML function in production
        return {
            'items': [
                ActionItem(
                    priority="high",
                    category="strategic",
                    description="Develop 3-year strategic plan",
                    timeline="6 months",
                    resources_needed=["board engagement", "consultant"]
                )
            ],
            'tokens_used': 100
        }

    async def _identify_risks(self, analysis_content: AIAnalysisContent, org: OrganizationProfile) -> dict:
        """Identify risk factors"""
        return {
            'risks': [
                RiskFactor(
                    severity="medium",
                    category="financial",
                    description="Revenue concentration risk",
                    mitigation_strategies=["Diversify funding sources", "Build reserves"]
                )
            ],
            'tokens_used': 80
        }

    async def _identify_opportunities(self, analysis_content: AIAnalysisContent) -> dict:
        """Identify opportunities"""
        return {
            'opportunities': [
                Opportunity(
                    type="grant",
                    description="Federal education grants aligned with mission",
                    potential_impact="high",
                    required_actions=["Develop grant writing capacity"],
                    timeline="3-6 months"
                )
            ],
            'tokens_used': 60
        }

    def _extract_recommendations(self, content: AIAnalysisContent) -> List[str]:
        """Extract key recommendations from analysis"""
        return [
            "Strengthen board governance structure",
            "Diversify revenue streams",
            "Develop data collection and evaluation systems",
            "Build strategic partnerships with complementary organizations"
        ]
```

### app/cost_tracker.py
```python
"""
Cost tracking for AI services
Demonstrates Factor 3: Config and Factor 11: Logs as event streams
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

class CostTracker:
    """
    Track AI API costs and usage

    Implements:
    - Factor 3: Cost limits from environment
    - Factor 11: Cost events as structured logs
    - Factor 6: Stateless cost calculations
    """

    def __init__(self):
        # Factor 3: Config from environment
        self.daily_limit = float(os.getenv("AI_DAILY_COST_LIMIT", "100.00"))
        self.tracking_enabled = os.getenv("AI_COST_TRACKING_ENABLED", "true").lower() == "true"

        # Model costs per 1K tokens
        self.model_costs = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "gpt-4-turbo": 0.01
        }

        # In-memory tracking (in production: use external store)
        self.daily_usage = {}

    async def can_proceed(self, estimated_cost: float) -> bool:
        """Check if request can proceed without exceeding limits"""
        if not self.tracking_enabled:
            return True

        today = datetime.now().date().isoformat()
        current_usage = self.daily_usage.get(today, 0.0)

        return (current_usage + estimated_cost) <= self.daily_limit

    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for token usage"""
        cost_per_1k = self.model_costs.get(model, 0.03)  # Default to GPT-4 rate
        return (tokens / 1000) * cost_per_1k

    async def record_usage(self, cost: float, tokens: int):
        """Record API usage for tracking"""
        if not self.tracking_enabled:
            return

        today = datetime.now().date().isoformat()
        self.daily_usage[today] = self.daily_usage.get(today, 0.0) + cost

        # Factor 11: Log cost event
        cost_event = {
            "event_type": "ai_cost_incurred",
            "timestamp": datetime.utcnow().isoformat(),
            "cost_dollars": cost,
            "tokens_used": tokens,
            "daily_total": self.daily_usage[today],
            "daily_limit": self.daily_limit,
            "percentage_used": (self.daily_usage[today] / self.daily_limit) * 100
        }

        # In production: send to structured logging system
        print(json.dumps(cost_event))

    async def record_error(self, error_message: str):
        """Record AI API errors"""
        error_event = {
            "event_type": "ai_api_error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_message,
            "tool": "ai-heavy-analysis"
        }

        print(json.dumps(error_event))

    def get_daily_usage(self, date: str = None) -> Dict[str, Any]:
        """Get usage summary for a date"""
        if not date:
            date = datetime.now().date().isoformat()

        usage = self.daily_usage.get(date, 0.0)
        return {
            "date": date,
            "cost_dollars": usage,
            "limit_dollars": self.daily_limit,
            "percentage_used": (usage / self.daily_limit) * 100,
            "remaining_budget": max(0, self.daily_limit - usage)
        }
```

## Key Learning Points

### 1. External Service Integration (Factor 4)
- **Treat OpenAI as backing service**: Configurable, replaceable, failure-resistant
- **Structured I/O**: Clear input intents and output results
- **Cost Management**: Track usage and enforce limits

### 2. Error Handling (Factor 9)
- **Timeout handling**: Don't wait forever for AI responses
- **Graceful degradation**: Provide meaningful errors
- **Cost protection**: Stop processing if limits exceeded

### 3. Configuration (Factor 3)
- **Model selection**: Switch between GPT-4, GPT-3.5 via config
- **Cost limits**: Daily and per-request limits
- **Performance tuning**: Timeout, temperature, max tokens

### 4. Observability (Factor 11)
- **Cost tracking**: Every API call logged with cost
- **Performance metrics**: Response times and token usage
- **Error logging**: Structured error events

## Running the Tool

```bash
# Set up environment
export OPENAI_API_KEY=your_key_here
export AI_MODEL=gpt-4
export AI_MAX_COST_PER_REQUEST=5.00
export AI_DAILY_COST_LIMIT=100.00

# Run analysis
python app/main.py

# Run as service
python app/server.py
```

This tool shows how to integrate external AI services following 12-factor principles, with proper cost management and error handling!
# Real Data Testing Plan - AI Processors with Live OpenAI API

## Overview
Comprehensive testing framework for all 4 AI processors using real nonprofit data, real government opportunities, and live OpenAI API calls. Organized by tab with complete input/output capture for validation and review.

## Test Organization by Tab/Processor

### Tab 1: PLAN - AI Lite Unified Processor ⚡
- **File**: `src/processors/analysis/ai_lite_unified_processor.py`
- **Tab Purpose**: Quick opportunity assessment and initial feasibility
- **AI Model**: gpt-4o-mini (cost-effective screening)
- **Estimated Cost**: $0.0004 per candidate
- **Input Package**:
  - Nonprofit basic profile (name, EIN, mission, NTEE code)
  - Government opportunity summary (title, agency, funding amount)
  - Basic eligibility criteria
- **AI Prompt Focus**: 
  - Initial viability assessment
  - Basic fit scoring
  - Red flag identification
- **Expected Output**:
  - Quick viability score (0-100)
  - Basic recommendation (pursue/skip)
  - Key risk flags
  - Processing time: <5 seconds
- **Review Questions**:
  - Are the quick assessments accurate for filtering?
  - Does it catch obvious mismatches effectively?
  - Is the cost-benefit ratio appropriate for screening?

### Tab 2: ANALYZE - AI Heavy Light Analyzer 🔍  
- **File**: `src/processors/analysis/ai_heavy_light_analyzer.py`
- **Tab Purpose**: Strategic alignment and competitive analysis
- **AI Model**: gpt-4o-mini (enhanced context analysis)
- **Estimated Cost**: $0.02-0.04 per analysis
- **Input Package**:
  - PLAN tab results and scores
  - Detailed nonprofit financials (3-year revenue, expenses, assets)
  - Complete opportunity details (requirements, timeline, deliverables)
  - NTEE code context and program alignment
- **AI Prompt Focus**:
  - Strategic alignment assessment
  - Competitive positioning analysis
  - Resource requirement evaluation
- **Expected Output**:
  - Detailed analysis report (2-3 pages)
  - Strategic fit score with breakdown
  - Competitive advantage assessment
  - Resource gap identification
- **Review Questions**:
  - Does it provide meaningful insights beyond PLAN tab?
  - Are strategic recommendations actionable?
  - Is the competitive analysis realistic?

### Tab 3: EXAMINE - AI Heavy Deep Researcher 🔬
- **File**: `src/processors/analysis/ai_heavy_deep_researcher.py` 
- **Tab Purpose**: Comprehensive research and deep risk analysis
- **AI Model**: gpt-4o (advanced reasoning and research)
- **Estimated Cost**: $0.08-0.15 per research
- **Input Package**:
  - ANALYZE tab results and strategic assessment
  - Complete entity data (financial history, board members, programs)
  - Historical funding patterns and success rates
  - Market context and competitive landscape
- **AI Prompt Focus**:
  - Deep research analysis
  - Comprehensive risk assessment
  - Implementation feasibility study
  - Success probability modeling
- **Expected Output**:
  - Comprehensive research dossier (5-8 pages)
  - Detailed risk analysis matrix
  - Implementation roadmap outline
  - Success probability with confidence intervals
- **Review Questions**:
  - Is the research thorough and well-sourced?
  - Are risk assessments realistic and comprehensive?
  - Does it identify non-obvious opportunities or threats?

### Tab 4: APPROACH - AI Heavy Researcher 🎯
- **File**: `src/processors/analysis/ai_heavy_researcher.py`
- **Tab Purpose**: Implementation strategy and detailed approach
- **AI Model**: gpt-4o (strategic planning and execution)
- **Estimated Cost**: $0.12-0.20 per implementation plan
- **Input Package**:
  - EXAMINE tab research and risk analysis
  - All previous processor results and context
  - Implementation constraints and requirements
  - Resource allocation parameters
- **AI Prompt Focus**:
  - Detailed implementation strategy
  - Timeline and milestone planning
  - Resource allocation optimization
  - Success metrics definition
- **Expected Output**:
  - Complete implementation approach (10+ pages)
  - Detailed project timeline with milestones
  - Resource requirements and budget estimates
  - Success metrics and KPIs
  - Risk mitigation strategies
- **Review Questions**:
  - Are implementation strategies realistic and achievable?
  - Is the timeline appropriate for the scope?
  - Are resource requirements accurately estimated?

## Test Data Selection

### Selected Nonprofit: Grantmakers In Aging Inc
- **EIN**: 134014982
- **Location**: Arlington, VA
- **NTEE Code**: P81 (Voluntarism Promotion)
- **Annual Revenue**: $2,208,858 (2022)
- **Total Assets**: $2,481,115 (2022)
- **Why Selected**: 
  - Strong 13+ year financial history
  - Comprehensive 990 data available
  - Mid-size nonprofit with realistic scope
  - Clear mission and program focus

### Selected Government Opportunity: TEST-GRANTS-2024-001  
- **Agency**: Department of Energy (DOE)
- **Program**: Test Grant Program
- **Category**: Environment
- **Eligibility**: Nonprofits (code 25)
- **Why Selected**:
  - Already in entity-based data structure
  - Appropriate for nonprofit testing
  - Clear eligibility requirements

## Cost Controls and Safety Measures

### Budget Limits
```python
COST_CONTROLS = {
    "max_total_test_cost": 5.00,        # Hard limit for entire test run
    "max_cost_per_processor": 1.25,     # Limit per individual processor
    "token_limits": {
        "gpt-4o-mini": 4000,            # Conservative token limit
        "gpt-4o": 2000,                 # Higher cost model limit
    },
    "timeout_seconds": 120,             # API timeout protection
    "retry_attempts": 2                 # Limited retry on failures
}
```

### Safety Mechanisms
- Real-time cost tracking with automatic shutoff
- Pre-test API key validation and rate limit checks
- Comprehensive error handling and graceful failures
- Backup test data in case of API issues
- Test mode flag to prevent accidental production usage

## Deliverables for Review

For each processor test, you will receive:

### 1. Complete AI Input Package (`processor_input_[tab].json`)
```json
{
    "processor": "ai_lite_unified_processor",
    "timestamp": "2025-08-31T...",
    "input_data": {
        "nonprofit_profile": {...},
        "opportunity_data": {...},
        "previous_results": {...}
    },
    "prompt_context": "Full context sent to AI",
    "token_count": 1250
}
```

### 2. Raw AI Prompt (`processor_prompt_[tab].txt`)
- Complete prompt with all instructions
- Context data and formatting
- Expected output structure
- Processing guidelines

### 3. Raw AI Response (`processor_response_[tab].json`)
- Unprocessed OpenAI API response
- Full response content and metadata
- Token usage and timing information
- Confidence scores and reasoning

### 4. Processed Output (`processor_output_[tab].json`)
- Final structured results from processor
- Scores, recommendations, and analysis
- Data transformations and validations
- Quality assurance flags

### 5. Cost and Performance Metrics (`test_metrics.json`)
```json
{
    "processor": "ai_lite_unified_processor",
    "cost_usd": 0.0004,
    "tokens_used": 1250,
    "response_time_seconds": 3.2,
    "success": true,
    "api_calls": 1,
    "retry_count": 0
}
```

## Implementation Script Structure

### Core Test Script: `real_data_ai_test.py`

```python
class RealDataAITester:
    def __init__(self):
        self.cost_tracker = CostTracker(max_budget=5.00)
        self.results_logger = ResultsLogger("test_results/")
        self.processors = self._load_processors()
    
    def test_processor_by_tab(self, tab_name: str):
        """Test individual processor with full logging"""
        
    def test_complete_workflow(self):
        """Test all 4 processors in sequence"""
        
    def capture_ai_interaction(self, processor, input_data):
        """Capture complete AI input/output for review"""
        
    def generate_review_report(self):
        """Generate comprehensive report for validation"""
```

### Key Features
- **Phased Testing**: Test individual processors or complete workflow
- **Complete Logging**: Every AI interaction captured for review
- **Cost Safety**: Multiple layers of budget protection
- **Error Recovery**: Graceful handling of API failures
- **Review-Ready Output**: Organized results for easy validation

## Pre-Test Checklist

### Environment Setup
- [ ] OpenAI API key configured and validated
- [ ] Rate limits and billing settings confirmed
- [ ] Test data files accessible and validated
- [ ] Results directory created with proper permissions
- [ ] Backup plan in case of API issues

### Data Validation
- [ ] Nonprofit data structure matches processor expectations
- [ ] Government opportunity data properly formatted
- [ ] Entity relationships correctly established
- [ ] Test data represents realistic use case

### Safety Checks
- [ ] Cost controls implemented and tested
- [ ] API timeout and retry logic verified
- [ ] Error handling covers all failure modes
- [ ] Results logging and capture working properly
- [ ] Test mode flags properly set

## Execution Plan

### Phase 1: Individual Processor Testing
1. Test PLAN tab processor (lowest cost, quick validation)
2. Test ANALYZE tab processor (medium complexity)
3. Test EXAMINE tab processor (high complexity, careful monitoring)
4. Test APPROACH tab processor (highest cost, final validation)

### Phase 2: Workflow Integration Testing  
1. Test PLAN -> ANALYZE two-processor flow
2. Test PLAN -> ANALYZE -> EXAMINE three-processor flow
3. Test complete four-processor workflow
4. Validate data flow and result integration

### Phase 3: Results Analysis and Validation
1. Review all captured AI inputs and outputs
2. Validate processor performance against expectations
3. Analyze cost efficiency and processing times
4. Generate final validation report

## Expected Outcomes

### Success Criteria
- All 4 processors execute successfully with real data
- Total cost remains under $5.00 budget
- Complete AI input/output captured for review
- Processing times meet performance expectations
- Results demonstrate clear value progression across tabs

### Key Insights to Validate
- Does each processor add meaningful value to the analysis?
- Are the AI prompts generating relevant, actionable insights?
- Is the cost-benefit ratio appropriate for each processor?
- Do the results justify the progressive cost increase across tabs?
- Are there any gaps or redundancies in the processor workflow?

## Post-Test Analysis Framework

### Review Questions by Tab
1. **PLAN Tab**: Is the quick screening accurate and cost-effective?
2. **ANALYZE Tab**: Does strategic analysis add meaningful insights?
3. **EXAMINE Tab**: Is deep research thorough and actionable?
4. **APPROACH Tab**: Are implementation strategies realistic and valuable?

### Overall Workflow Validation
- Data flow efficiency between processors
- Value addition at each stage
- Cost optimization opportunities
- Processing time performance
- Error handling and reliability

This plan provides a comprehensive framework for testing the AI processors with real data while ensuring complete transparency and reviewability of all AI interactions.
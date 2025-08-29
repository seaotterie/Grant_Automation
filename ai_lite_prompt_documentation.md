# AI-Lite System Prompt Documentation & Testing Guide

## Overview
The AI-Lite system consists of 3 core GPT-5 powered processors designed for cost-effective opportunity analysis:

1. **AI-Lite Validator** (GPT-5-nano) - Funding source verification & early filtering
2. **AI-Lite Scorer** (GPT-5-nano) - Compatibility scoring & research intelligence with integrated enhanced error recovery
3. **AI-Lite Strategic Scorer** (GPT-5-nano) - Strategic analysis & priority ranking

*Note: Enhanced error recovery features have been consolidated directly into the AI-Lite Scorer for simplified workflow integration.*

---

## 1. AI-Lite Validator

### Purpose
Enhanced opportunity validation with funding provider verification and early-stage intelligence filtering.

### Model Configuration
- **Model**: GPT-5-nano
- **Cost**: ~$0.00008 per candidate
- **Batch Size**: 20 candidates
- **Max Tokens**: 800

### Input Data Structure
```python
{
    "organization_context": {
        "name": "Advanced Healthcare Solutions",
        "mission": "Advancing medical research and healthcare technology",
        "focus_areas": ["healthcare", "medical_research", "AI"],
        "ntee_codes": ["E32", "U41"],
        "geographic_scope": "National"
    },
    "candidates": [
        {
            "opportunity_id": "NIH_R01_2025_001",
            "organization_name": "National Institutes of Health",
            "source_type": "government",
            "funding_amount": 500000,
            "geographic_location": "National",
            "description": "Research grant for innovative medical technologies..."
        }
    ]
}
```

### Prompt Template
```
ENHANCED OPPORTUNITY VALIDATION SPECIALIST (GPT-5 Phase 2A)

ANALYZING ORGANIZATION: {organization_name}
Mission: {mission_statement}
Focus Areas: {focus_areas}
NTEE Codes: {ntee_codes}
Geographic Scope: {geographic_scope}

VALIDATION MISSION: Perform comprehensive validation with enhanced intelligence to optimize downstream processing efficiency.

CANDIDATES FOR ENHANCED VALIDATION:
1. {opportunity_details}...

For each candidate, provide enhanced validation analysis in EXACT JSON format:
{
  "opportunity_id": {
    "validation_result": "valid_funding",
    "eligibility_status": "eligible", 
    "confidence_level": 0.85,
    "discovery_track": "foundation",
    "priority_level": "medium",
    "go_no_go": "go",
    
    "funding_provider_type": "actual_funder",
    "program_status": "active",
    "application_pathway": "clear_process",
    
    "competition_level": "moderate",
    "application_complexity": "moderate",
    "success_probability": 0.75,
    
    "deadline_indicators": ["March 15, 2025", "Annual cycle"],
    "contact_quality": "program_officer",
    "recent_activity": ["2024 awards announced", "Program guidelines updated"],
    
    "validation_reasoning": "Confirmed active foundation with clear application process...",
    "key_flags": ["application_deadline_approaching", "moderate_competition"],
    "next_actions": ["detailed_strategic_analysis", "contact_program_officer"]
  }
}

RESPONSE (JSON only):
```

### Expected Output Format
```json
{
  "NIH_R01_2025_001": {
    "validation_result": "valid_funding",
    "eligibility_status": "eligible",
    "confidence_level": 0.90,
    "discovery_track": "government",
    "priority_level": "high",
    "go_no_go": "go",
    "funding_provider_type": "actual_funder",
    "program_status": "active",
    "application_pathway": "clear_process",
    "competition_level": "high",
    "application_complexity": "complex",
    "success_probability": 0.65,
    "deadline_indicators": ["March 15, 2025", "Annual cycle"],
    "contact_quality": "program_officer",
    "recent_activity": ["2024 awards announced", "Program guidelines updated"],
    "validation_reasoning": "NIH R01 is premier research funding with established track record",
    "key_flags": ["high_competition", "extensive_requirements"],
    "next_actions": ["detailed_strategic_analysis", "preliminary_data_assessment"]
  }
}
```

---

## 2. AI-Lite Scorer

### Purpose
Dual-function scoring and research platform for comprehensive opportunity analysis.

### Model Configuration
- **Model**: GPT-5-nano
- **Cost**: ~$0.00005 per candidate (scoring), ~$0.0004 (research mode)
- **Batch Size**: 15 candidates
- **Max Tokens**: 150 (scoring), 800 (research)

### Prompt Template (Scoring Mode)
```
You are an expert grant strategist analyzing funding opportunities for optimal compatibility and risk assessment.

ANALYZING ORGANIZATION: {organization_name}
Mission: {mission_statement}
Focus Areas: {focus_areas}
NTEE Codes: {ntee_codes}

CANDIDATES FOR ANALYSIS:
1. {opportunity_details}...

For each candidate, provide analysis in this EXACT JSON format:
{
  "opportunity_id": {
    "compatibility_score": 0.85,
    "risk_flags": ["high_competition", "technical_requirements"],
    "priority_rank": 1,
    "quick_insight": "Strong mission alignment with excellent funding amount...",
    "confidence_level": 0.9
  }
}

RESPONSE (JSON only):
```

### Prompt Template (Research Mode)
```
RESEARCH ANALYST - COMPREHENSIVE OPPORTUNITY INTELLIGENCE

ANALYZING ORGANIZATION PROFILE:
Name: {organization_name}
Mission: {mission_statement}
Focus Areas: {focus_areas}

BATCH CANDIDATES FOR RESEARCH ({count} opportunities):
{candidate_summaries}

For each opportunity, conduct thorough research and provide analysis in EXACT JSON format:
{
  "opportunity_id": {
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "funding_likelihood": 0.75,
    "strategic_rationale": "2-sentence strategic analysis",
    "action_priority": "immediate",
    "confidence_level": 0.9,
    "research_report": {
      "executive_summary": "200-word executive summary for grant teams...",
      "opportunity_overview": "Detailed opportunity description...",
      "eligibility_analysis": ["Point 1: Specific eligibility requirement...", "Point 2: Additional requirement..."],
      "key_dates_timeline": ["Application deadline specifics", "Award notification timeline"],
      "funding_details": "Complete funding information including restrictions...",
      "strategic_considerations": ["Strategic factor 1", "Strategic factor 2"],
      "decision_factors": ["Go/no-go factor 1", "Go/no-go factor 2"]
    },
    "website_intelligence": {
      "primary_website_url": "https://funder-website.org",
      "key_contacts": ["Contact Name, Title, email"],
      "application_process_summary": "Step-by-step application process...",
      "eligibility_highlights": ["Key eligibility point 1", "Key eligibility point 2"],
      "deadline_information": "Complete deadline and timeline information"
    },
    "competitive_analysis": {
      "likely_competitors": ["Competitor organization 1", "Competitor organization 2"],
      "competitive_advantages": ["Our advantage 1", "Our advantage 2"],
      "application_volume_estimate": "Estimated number of applications",
      "success_probability_factors": ["Success factor 1", "Success factor 2"]
    }
  }
}

RESPONSE (JSON only):
```

---

## 3. AI-Lite Strategic Scorer

### Purpose
Strategic mission alignment analysis with priority ranking and resource assessment.

### Model Configuration
- **Model**: GPT-5-nano
- **Cost**: ~$0.000075 per candidate
- **Batch Size**: 15 candidates
- **Max Tokens**: 200

### Prompt Template
```
STRATEGIC GRANT ANALYSIS SPECIALIST

ANALYZING ORGANIZATION: {organization_name}
Mission Focus: {mission_statement}
Strategic Areas: {focus_areas}
Current Scope: {geographic_scope}

VALIDATED CANDIDATES FOR STRATEGIC ANALYSIS:
{candidate_summaries}

For each candidate, provide strategic analysis in EXACT JSON format:
{
  "opportunity_id": {
    "mission_alignment_score": 0.85,
    "strategic_value": "high",
    "strategic_rationale": "Strong alignment with core mission areas and strategic priorities",
    "priority_rank": 1,
    "action_priority": "immediate",
    "confidence_level": 0.9,
    "key_advantages": ["Mission alignment", "Geographic fit", "Funding size match"],
    "potential_concerns": ["High competition", "Technical requirements"],
    "resource_requirements": ["Technical expertise", "Administrative capacity"]
  }
}

STRATEGIC ANALYSIS CRITERIA:
- mission_alignment_score: 0.0-1.0 alignment with organizational mission and focus areas
- strategic_value: "high", "medium", "low" overall strategic importance to organization
- priority_rank: 1=highest priority, rank ALL candidates 1-{count}
- action_priority: "immediate" (pursue now), "planned" (future consideration), "monitor" (watch for changes)

RESPONSE (JSON only):
```

---

## 4. AI-Lite Scorer (Enhanced Features)

### Consolidated Enhanced Features
The AI-Lite Scorer now includes all enhanced error recovery and reliability features directly integrated:

### Enhanced Error Recovery Features
- **Comprehensive Retry Logic**: Exponential backoff with jitter for rate limits and timeouts
- **Error Classification**: Intelligent error type detection (rate limits, timeouts, network issues)
- **Graceful Degradation**: Enhanced fallback analysis when API calls fail
- **Production Reliability**: Circuit breaker patterns and comprehensive error handling
- **Enhanced Simulation**: Realistic error scenarios for testing and development

### API Integration
- **OpenAI Service Integration**: Uses centralized OpenAI service with proper error handling
- **Multi-Model Support**: Flexible model selection with cost optimization
- **Cost Tracking**: Detailed cost estimation and usage monitoring

---

## API Call Flow & Cost Analysis

### Typical Processing Pipeline
1. **Validator** processes 20 candidates → $0.0016 total
2. **Scorer** processes 15 valid candidates → $0.00075 total (includes enhanced error recovery)  
3. **Strategic Scorer** processes 15 candidates → $0.0011 total

### Sample Batch Costs (GPT-5-nano pricing)
- **Small batch (5 candidates)**: ~$0.0008 total
- **Medium batch (15 candidates)**: ~$0.0024 total  
- **Large batch (50 candidates)**: ~$0.008 total

### Performance Characteristics
- **Processing time**: 2-5 seconds per batch
- **Success rate**: 98%+ with error recovery
- **Token efficiency**: Optimized prompts for minimal token usage
- **Scalability**: Handles 100+ candidates per minute

---

## Testing Integration

### Required Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

### Sample Test Command
```python
# Test all 4 processors with sample data
python ai_lite_comprehensive_test.py --batch-size 10 --include-research-mode
```

This documentation provides complete visibility into AI-Lite prompt structures, expected outputs, and cost analysis for comprehensive testing and integration.
# ChatGPT App Testing Package for Catalynx AI Analysis

Generated on: 2025-08-23T19:22:06.747055

## Overview

This package contains extracted prompts from the Catalynx AI analysis systems for testing in ChatGPT web app before implementing full OpenAI API integration.

## Package Contents

### 1. AI Lite Scorer Testing (`ai_lite_chatgpt_test.json`)
- **Purpose**: Cost-effective candidate analysis for ANALYZE tab
- **Model**: GPT-3.5 Turbo recommended
- **Cost**: ~$0.001-0.003 per test
- **Processing**: Batch analysis of 3-15 opportunities

### 2. AI Heavy Researcher Testing (`ai_heavy_chatgpt_test.json`) 
- **Purpose**: Comprehensive strategic dossier for EXAMINE tab
- **Model**: GPT-4 required
- **Cost**: ~$0.15-0.30 per test
- **Processing**: Individual deep analysis with grant application intelligence

### 3. Test Scenarios (`test_scenarios.json`)
- Multiple testing scenarios for each AI system
- Covers various organization types and opportunity profiles
- Validation criteria for each scenario

## Quick Start Guide

### Step 1: AI Lite Testing
1. Open `ai_lite_prompt.txt`
2. Copy entire prompt to ChatGPT 3.5
3. Verify JSON response structure
4. Test with scenarios from `test_scenarios.json`

### Step 2: AI Heavy Testing  
1. Open `ai_heavy_prompt.txt`
2. Copy entire prompt to ChatGPT 4 (required)
3. Verify comprehensive dossier structure
4. Test grant application intelligence section

### Step 3: Validation
1. Use validation checklists in each JSON file
2. Verify response structure matches expected format
3. Test multiple scenarios for consistency
4. Document any prompt refinements needed

## Expected Response Structures

### AI Lite Response
```json
{
  "opportunity_id": {
    "compatibility_score": 0.85,
    "strategic_value": "high",
    "risk_assessment": ["competition_level", "capacity_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.75,
    "strategic_rationale": "Strong alignment with proven outcomes",
    "action_priority": "immediate",
    "confidence_level": 0.9
  }
}
```

### AI Heavy Response
```json
{
  "strategic_dossier": {
    "partnership_assessment": { ... },
    "funding_strategy": { ... },
    "grant_application_intelligence": { ... },
    ...
  },
  "action_plan": { ... }
}
```

## Testing Checklist

### AI Lite Testing
- [ ] Prompt generates valid JSON response
- [ ] All opportunities receive scores
- [ ] Compatibility scores between 0.0-1.0
- [ ] Strategic values are high/medium/low
- [ ] Risk assessments contain valid factors
- [ ] Priority rankings are unique
- [ ] Confidence levels are realistic

### AI Heavy Testing
- [ ] Comprehensive dossier generated
- [ ] Grant application intelligence detailed
- [ ] Partnership assessment scored
- [ ] Funding strategy specific
- [ ] Risk mitigation strategies provided
- [ ] Action plan actionable
- [ ] Recommended approach clear

## Troubleshooting

### Common Issues
1. **JSON Format Errors**: Ensure proper JSON syntax in response
2. **Missing Fields**: Verify all required fields present
3. **Invalid Values**: Check enum values match specifications
4. **Incomplete Analysis**: May need prompt refinement for thoroughness

### Prompt Refinement
- Document any ChatGPT response issues
- Note which sections need clarification
- Test prompt variations for optimization
- Validate refined prompts with multiple scenarios

## Integration Notes

After successful ChatGPT testing:
1. Incorporate refined prompts into AI processors
2. Implement proper error handling for API integration
3. Add response validation using Pydantic models
4. Test cost optimization with batch processing

## Test Results Documentation

Create test result files:
- `ai_lite_test_results.json`: AI Lite testing outcomes
- `ai_heavy_test_results.json`: AI Heavy testing outcomes  
- `prompt_refinements.md`: Notes on prompt improvements needed

## Support

For questions about this testing package:
- Review validation checklists in JSON files
- Check expected response formats
- Consult test scenarios for guidance
- Document issues for development team review

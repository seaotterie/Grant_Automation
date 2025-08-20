# Catalynx AI Lite Scorer - External Test Package

## Overview
This package contains a simplified version of the Catalynx AI Lite Scorer system for external testing and validation. The AI Lite Scorer is designed to provide cost-effective, rapid analysis of funding opportunities for grant-seeking organizations.

## Package Contents
- `ai_lite_test_package.py` - Main test script with sample data and prompt generation
- `ai_lite_test_prompt.txt` - Ready-to-use prompt for AI testing
- `AI_LITE_TEST_PACKAGE_README.md` - This documentation file

## Test Scenario
**Organization**: Community Tech Foundation  
**Focus**: Digital divide, technology education, community development  
**Budget**: $2.5M annually, seeking $750K in grants  
**Geography**: Mid-Atlantic region (VA, MD, DC)

**Candidates**: 5 funding opportunities ranging from $75K to $500K across private foundations, corporate funders, and state government.

## How to Test

### Step 1: Copy the Prompt
1. Open `ai_lite_test_prompt.txt`
2. Copy the entire contents
3. Paste into ChatGPT, Claude, or other AI system

### Step 2: Evaluate the Response
The AI should return a JSON object analyzing each of the 5 opportunities with:
- Compatibility scores (0.0-1.0)
- Strategic value classification (high/medium/low)
- Risk assessments
- Priority rankings (1-5, unique)
- Funding likelihood estimates
- Strategic rationale explanations
- Action priorities (immediate/planned/monitor)

### Step 3: Validate Quality
Check that the response includes:
- ✅ All 5 opportunity IDs present
- ✅ Scores within valid ranges
- ✅ Unique priority rankings 1-5
- ✅ Logical strategic reasoning
- ✅ Appropriate risk assessments

## Expected Performance Benchmarks

### High-Quality Response Should Show:
1. **Strong Mission Alignment Recognition**
   - Higher scores for digital literacy/community development opportunities
   - Geographic preference for Mid-Atlantic region
   - Appropriate funding size alignment

2. **Strategic Risk Assessment**
   - Competition level awareness
   - Capacity requirement analysis
   - Timeline pressure considerations

3. **Practical Priority Ranking**
   - Balance of strategic value vs. funding likelihood
   - Geographic advantage recognition
   - Organizational capacity alignment

## Sample Expected Analysis (Benchmark)

```json
{
  "rural_broadband_003": {
    "compatibility_score": 0.92,
    "strategic_value": "high", 
    "risk_assessment": ["government_partnerships", "infrastructure_requirements"],
    "priority_rank": 1,
    "funding_likelihood": 0.85,
    "strategic_rationale": "Excellent mission alignment with rural digital divide focus, strong geographic fit for Virginia operations, and lower competition for government funding.",
    "action_priority": "immediate",
    "confidence_level": 0.90
  },
  "tech_equity_001": {
    "compatibility_score": 0.88,
    "strategic_value": "high",
    "risk_assessment": ["moderate_competition", "sustainability_requirements"],
    "priority_rank": 2,
    "funding_likelihood": 0.78,
    "strategic_rationale": "Perfect mission alignment with digital literacy focus and Mid-Atlantic geographic advantage, optimal funding size for organization capacity.",
    "action_priority": "immediate", 
    "confidence_level": 0.85
  }
}
```

## Evaluation Criteria

### Technical Accuracy (25%)
- Valid JSON format
- All required fields present
- Scores within specified ranges
- Unique priority rankings

### Strategic Reasoning (40%)
- Mission alignment assessment
- Geographic considerations
- Competitive analysis
- Organizational capacity fit

### Risk Assessment (20%)
- Appropriate risk identification
- Competition level awareness
- Implementation challenges

### Practical Application (15%)
- Actionable recommendations
- Timeline considerations
- Resource allocation logic

## Common Issues to Watch For

### Poor Performance Indicators:
- Missing or duplicate priority rankings
- Scores outside valid ranges (0.0-1.0)
- Generic rationale not specific to organization
- Ignoring geographic advantages/mismatches
- Missing risk factors or inappropriate risk assessment

### Strong Performance Indicators:
- Clear mission alignment reasoning
- Geographic preference recognition
- Balanced competition vs. opportunity assessment
- Practical funding likelihood estimates
- Specific, actionable strategic rationale

## Cost-Effectiveness Analysis

The AI Lite system is designed for:
- **Speed**: Sub-minute analysis of 5-20 opportunities
- **Cost**: ~$0.0001 per candidate (using GPT-3.5-turbo)
- **Scale**: Batch processing for efficiency
- **Quality**: Strategic insights sufficient for pipeline management

Compare AI performance against manual analysis time (typically 15-30 minutes per opportunity) and consistency of strategic reasoning.

## Integration Notes

This test package simulates the production Catalynx AI Lite Scorer which:
- Processes real organization profiles and funding opportunities
- Integrates with 18 different discovery processors
- Supports multiple AI models (GPT-3.5-turbo, GPT-4, Claude)
- Provides cost tracking and budget management
- Enables batch processing for large candidate sets

## Contact Information
For questions about the Catalynx system or this test package, refer to the main project documentation or contact the development team.

---

**Test Package Version**: 1.0  
**Compatible with**: ChatGPT-4, Claude 3, GPT-3.5-turbo, and other modern LLMs  
**Last Updated**: January 2025
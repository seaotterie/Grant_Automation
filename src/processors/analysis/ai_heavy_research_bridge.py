#!/usr/bin/env python3
"""
AI-Heavy Research Bridge - Stage 3 of Optimized 5-Call Architecture
Intelligence gathering processor that bridges AI-Lite and AI-Heavy analysis

This processor:
1. Conducts web intelligence gathering (website scraping, contact research)
2. Performs basic document analysis and fact extraction
3. Maps application processes and requirements
4. Gathers raw intelligence data for AI-Heavy processors
5. Optimized for information extraction (~$0.05 per candidate)
6. Feeds clean, structured data to downstream AI-Heavy analysis
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.openai_service import get_openai_service
from src.processors.analysis.ai_lite_validator import ValidationAnalysis
from src.processors.analysis.ai_lite_strategic_scorer import StrategicAnalysis

logger = logging.getLogger(__name__)


class ResearchStatus(str, Enum):
    """Research completion status"""
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    NO_DATA = "no_data"


class WebsiteIntelligence(BaseModel):
    """Website and web-based intelligence gathering"""
    primary_website_url: Optional[str] = None
    website_accessible: bool = False
    
    # Contact Intelligence
    key_contacts: List[str] = Field(default_factory=list, description="Program staff and contacts")
    program_officers: List[str] = Field(default_factory=list, description="Specific program officers")
    contact_emails: List[str] = Field(default_factory=list, description="Contact email addresses")
    contact_phones: List[str] = Field(default_factory=list, description="Contact phone numbers")
    
    # Process Intelligence
    application_process_overview: str = ""
    application_materials_required: List[str] = Field(default_factory=list)
    submission_method: str = ""
    
    # Program Intelligence  
    active_programs: List[str] = Field(default_factory=list, description="Currently active grant programs")
    program_descriptions: List[str] = Field(default_factory=list, description="Program descriptions")
    eligibility_requirements: List[str] = Field(default_factory=list, description="Eligibility requirements found")


class FactExtraction(BaseModel):
    """Systematically extracted facts and requirements"""
    # Financial Information
    funding_amount_range: str = ""
    average_award_size: str = ""
    total_program_budget: str = ""
    indirect_cost_allowed: Optional[bool] = None
    matching_requirements: str = ""
    
    # Timeline Information
    application_deadline: str = ""
    award_notification_date: str = ""
    project_start_date: str = ""
    project_duration: str = ""
    
    # Requirements
    geographic_eligibility: List[str] = Field(default_factory=list)
    organizational_requirements: List[str] = Field(default_factory=list)
    project_requirements: List[str] = Field(default_factory=list)
    reporting_requirements: List[str] = Field(default_factory=list)
    
    # Documentation Requirements
    required_attachments: List[str] = Field(default_factory=list)
    application_components: List[str] = Field(default_factory=list)


class BasicCompetitiveData(BaseModel):
    """Basic competitive intelligence from research"""
    typical_applicant_types: List[str] = Field(default_factory=list)
    recent_grantees: List[str] = Field(default_factory=list, description="Recent grant recipients if available")
    application_volume_estimate: str = ""
    competition_level_indicator: str = ""  # "high", "medium", "low", "unknown"
    
    # Success Factors (basic level)
    stated_priorities: List[str] = Field(default_factory=list)
    selection_criteria: List[str] = Field(default_factory=list)
    success_indicators: List[str] = Field(default_factory=list)


class ResearchIntelligence(BaseModel):
    """Complete research intelligence package"""
    opportunity_id: str
    research_status: ResearchStatus
    research_confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Core Intelligence Components
    website_intelligence: WebsiteIntelligence = Field(default_factory=WebsiteIntelligence)
    fact_extraction: FactExtraction = Field(default_factory=FactExtraction)
    competitive_data: BasicCompetitiveData = Field(default_factory=BasicCompetitiveData)
    
    # Research Notes
    research_notes: List[str] = Field(default_factory=list, description="Key findings and observations")
    data_gaps: List[str] = Field(default_factory=list, description="Information still needed")
    research_challenges: List[str] = Field(default_factory=list, description="Research difficulties encountered")
    
    # Recommendations for Next Stage
    heavy_analysis_recommendations: List[str] = Field(default_factory=list, description="Suggestions for AI-Heavy analysis")
    priority_research_areas: List[str] = Field(default_factory=list, description="Focus areas for deeper analysis")
    
    # Metadata
    research_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    research_duration: Optional[float] = None


class ResearchBridgeRequest(BaseModel):
    """Request structure for research bridge analysis"""
    batch_id: str
    profile_context: Dict[str, Any]
    validated_opportunities: List[Dict[str, Any]]  # From AI-Lite validation
    strategic_analyses: Dict[str, StrategicAnalysis]  # From AI-Lite strategic scoring
    research_priority: str = "standard"


class ResearchBridgeBatchResult(BaseModel):
    """Complete results from research bridge batch"""
    batch_id: str
    processed_count: int
    processing_time: float
    total_cost: float
    research_intelligence: Dict[str, ResearchIntelligence]  # opportunity_id -> research


class AIHeavyResearchBridge(BaseProcessor):
    """AI-Heavy Stage 3: Research intelligence gathering bridge processor"""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ai_heavy_research_bridge",
            description="Stage 3: Intelligence gathering bridge for AI-Heavy analysis pipeline",
            version="1.0.0",
            dependencies=["ai_lite_validator", "ai_lite_strategic_scorer"],
            estimated_duration=90,  # 1.5 minutes for research gathering
            requires_network=True,
            requires_api_key=True,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Research bridge settings
        self.batch_size = 10  # Smaller batches for detailed research
        self.model = "gpt-4o"  # More capable model for research tasks
        self.max_tokens = 600  # Higher token limit for research gathering
        self.temperature = 0.4  # Moderate temperature for research accuracy
        
        # Cost tracking
        self.estimated_cost_per_candidate = 0.05  # Research gathering cost
        
        # Initialize OpenAI service
        self.openai_service = get_openai_service()
        
    async def execute(self, request_data: ResearchBridgeRequest) -> ResearchBridgeBatchResult:
        """Execute research intelligence gathering for strategic opportunities"""
        start_time = datetime.now()
        batch_id = request_data.batch_id
        
        logger.info(f"Starting AI-Heavy research bridge for {len(request_data.validated_opportunities)} opportunities (batch: {batch_id})")
        
        try:
            # Create research gathering prompt
            research_prompt = self._create_research_prompt(request_data)
            
            # Call OpenAI API
            response = await self._call_openai_api(research_prompt)
            
            # Parse research intelligence
            intelligence = self._parse_research_response(response, request_data)
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            estimated_cost = len(request_data.validated_opportunities) * self.estimated_cost_per_candidate
            
            result = ResearchBridgeBatchResult(
                batch_id=batch_id,
                processed_count=len(intelligence),
                processing_time=processing_time,
                total_cost=estimated_cost,
                research_intelligence=intelligence
            )
            
            logger.info(f"AI-Heavy research bridge completed: {len(intelligence)} opportunities, "
                       f"${estimated_cost:.4f} cost, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"AI-Heavy research bridge failed: {str(e)}")
            raise
    
    def _create_research_prompt(self, request_data: ResearchBridgeRequest) -> str:
        """Create research intelligence gathering prompt"""
        
        profile = request_data.profile_context
        opportunities = request_data.validated_opportunities
        strategic_analyses = request_data.strategic_analyses
        
        # Build organization context
        org_context = f"""ORGANIZATION CONTEXT:
Name: {profile.get('name', 'Unknown')}
Mission: {profile.get('mission_statement', 'Not specified')}
Focus Areas: {', '.join(profile.get('focus_areas', []))}
Geographic Scope: {profile.get('geographic_scope', 'Not specified')}
Typical Grant Size: {profile.get('typical_grant_size', 'Not specified')}"""

        # Build opportunity summaries with strategic context
        opportunity_summaries = []
        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get('opportunity_id', 'no_id')
            strategic = strategic_analyses.get(opp_id)
            
            strategic_info = ""
            if strategic:
                strategic_info = f"""
   Strategic Score: {strategic.mission_alignment_score:.2f} | Value: {strategic.strategic_value.value}
   Priority: {strategic.action_priority.value} | Rank: {strategic.priority_rank}
   Rationale: {strategic.strategic_rationale[:100]}..."""
            
            summary = f"""
{i}. {opp.get('organization_name', 'Unknown')} ({opp_id})
   Website: {opp.get('website', 'Not available')}
   Type: {opp.get('source_type', 'Unknown')}
   Basic Info: {opp.get('description', 'No description')[:150]}...{strategic_info}"""
            opportunity_summaries.append(summary)

        # Create research intelligence gathering prompt
        prompt = f"""RESEARCH INTELLIGENCE SPECIALIST

{org_context}

RESEARCH MISSION: Conduct comprehensive intelligence gathering for strategically prioritized opportunities. Extract concrete facts, contacts, and processes to feed downstream AI-Heavy analysis.

STRATEGIC OPPORTUNITIES FOR RESEARCH:
{''.join(opportunity_summaries)}

For each opportunity, conduct detailed research and provide intelligence in EXACT JSON format:

{{
  "opportunity_id": {{
    "research_status": "complete",
    "research_confidence": 0.85,
    "website_intelligence": {{
      "primary_website_url": "https://example.org",
      "website_accessible": true,
      "key_contacts": ["Dr. Sarah Johnson, Program Director", "Mike Chen, Program Officer"],
      "program_officers": ["Dr. Sarah Johnson, sjohnson@example.org"],
      "contact_emails": ["programs@example.org", "grants@example.org"],
      "contact_phones": ["555-123-4567"],
      "application_process_overview": "Online application through grants portal, pre-application recommended",
      "application_materials_required": ["Project proposal", "Budget", "Letters of support"],
      "submission_method": "Online portal",
      "active_programs": ["Community Health Initiative", "Rural Access Program"],
      "program_descriptions": ["Focuses on community health improvement projects", "Expands healthcare access in rural areas"],
      "eligibility_requirements": ["501(c)(3) status required", "Must serve underserved populations"]
    }},
    "fact_extraction": {{
      "funding_amount_range": "$50,000 - $200,000",
      "average_award_size": "$125,000",
      "total_program_budget": "$5M annually",
      "indirect_cost_allowed": true,
      "matching_requirements": "No matching funds required",
      "application_deadline": "March 15, 2025 at 5:00 PM EST",
      "award_notification_date": "June 1, 2025",
      "project_start_date": "September 1, 2025",
      "project_duration": "12-24 months",
      "geographic_eligibility": ["United States", "Preference for rural areas"],
      "organizational_requirements": ["501(c)(3) nonprofit", "2+ years operating history"],
      "project_requirements": ["Community health focus", "Measurable outcomes required"],
      "reporting_requirements": ["Quarterly progress reports", "Final evaluation report"],
      "required_attachments": ["IRS determination letter", "Audited financials", "Board resolution"],
      "application_components": ["Executive summary", "Project narrative", "Budget and justification"]
    }},
    "competitive_data": {{
      "typical_applicant_types": ["Community health centers", "Rural hospitals", "Nonprofit health organizations"],
      "recent_grantees": ["Rural Health Alliance of Ohio", "Community Care Network"],
      "application_volume_estimate": "150-200 applications annually",
      "competition_level_indicator": "medium",
      "stated_priorities": ["Health equity", "Rural access", "Community partnerships"],
      "selection_criteria": ["Impact potential", "Organizational capacity", "Sustainability plan"],
      "success_indicators": ["Strong community partnerships", "Clear evaluation plan", "Experienced team"]
    }},
    "research_notes": ["Foundation emphasizes measurable community impact", "Strong preference for collaborative approaches"],
    "data_gaps": ["Exact indirect cost rate not specified", "Multi-year funding possibility unclear"],
    "research_challenges": ["Limited recent annual report data", "Program officer contact information not current"],
    "heavy_analysis_recommendations": ["Deep dive into partnership requirements", "Competitive landscape analysis needed"],
    "priority_research_areas": ["Application success factors", "Evaluation criteria details"]
  }}
}}

CRITICAL RESEARCH TASKS:
1. WEBSITE INTELLIGENCE: Visit websites, extract contacts, processes, requirements
2. FACT EXTRACTION: Get specific amounts, dates, requirements, restrictions  
3. CONTACT RESEARCH: Find program officers, emails, phone numbers
4. PROCESS MAPPING: Understand application process, materials, deadlines
5. BASIC COMPETITIVE DATA: Identify typical applicants and success factors

RESEARCH QUALITY STANDARDS:
- Verify information from authoritative sources
- Extract specific facts, not generalizations
- Identify information gaps clearly
- Provide actionable intelligence for strategic analysis
- Flag research challenges encountered

If you cannot access a website or find specific information, clearly state this in research_challenges rather than making up data.

RESPONSE (JSON only):"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for research intelligence gathering"""
        try:
            response = await self.openai_service.create_completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_research_response(self, response: str, request_data: ResearchBridgeRequest) -> Dict[str, ResearchIntelligence]:
        """Parse and validate research intelligence response"""
        intelligence = {}
        
        try:
            # Parse JSON response
            response_data = json.loads(response)
            
            # Process each research intelligence package
            for opportunity_id, research_data in response_data.items():
                try:
                    # Create research intelligence with proper validation
                    research = ResearchIntelligence(
                        opportunity_id=opportunity_id,
                        **research_data
                    )
                    intelligence[opportunity_id] = research
                    
                except Exception as e:
                    logger.warning(f"Failed to parse research intelligence for {opportunity_id}: {str(e)}")
                    # Create fallback research intelligence
                    intelligence[opportunity_id] = ResearchIntelligence(
                        opportunity_id=opportunity_id,
                        research_status=ResearchStatus.FAILED,
                        research_confidence=0.1,
                        research_notes=["Failed to parse research response"],
                        data_gaps=["All information needs verification"],
                        research_challenges=["Response parsing error"],
                        heavy_analysis_recommendations=["Manual research required"],
                        priority_research_areas=["Complete opportunity assessment"]
                    )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            # Create fallback research intelligence for all opportunities
            for opp in request_data.validated_opportunities:
                opportunity_id = opp.get('opportunity_id', 'unknown')
                intelligence[opportunity_id] = ResearchIntelligence(
                    opportunity_id=opportunity_id,
                    research_status=ResearchStatus.FAILED,
                    research_confidence=0.1,
                    research_notes=["API response parsing failed"],
                    data_gaps=["All research data missing"],
                    research_challenges=["JSON parsing error"],
                    heavy_analysis_recommendations=["Retry research bridge"],
                    priority_research_areas=["Full opportunity research"]
                )
        
        return intelligence
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics and configuration"""
        return {
            "processor_name": "ai_heavy_research_bridge",
            "stage": "research_intelligence_gathering",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "estimated_cost_per_candidate": self.estimated_cost_per_candidate,
            "batch_size": self.batch_size,
            "processing_focus": "intelligence_extraction",
            "research_capabilities": [
                "website_intelligence_gathering",
                "contact_information_extraction",
                "fact_extraction_and_verification",
                "application_process_mapping",
                "basic_competitive_intelligence"
            ],
            "feeds_downstream": ["ai_heavy_analysis", "ai_heavy_strategic"],
            "optimization_target": "research_accuracy"
        }
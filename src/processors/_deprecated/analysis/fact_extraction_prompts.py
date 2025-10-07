"""
Fact Extraction Prompt Templates

Opportunity-type specific prompts designed to extract only factual information
without subjective analysis or scoring. This ensures repeatability and allows
local deterministic scoring algorithms to process the facts consistently.

Architecture: Facts → Local Scoring → Intelligence Synthesis
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

class FactExtractionTemplate(str, Enum):
    """Available fact extraction templates by opportunity type"""
    GOVERNMENT_DETAILED = "government_detailed"
    GOVERNMENT_STANDARD = "government_standard"
    GOVERNMENT_BASIC = "government_basic"
    NONPROFIT_COMPREHENSIVE = "nonprofit_comprehensive"
    NONPROFIT_STANDARD = "nonprofit_standard"
    NONPROFIT_MINIMAL = "nonprofit_minimal"
    CORPORATE_RELATIONSHIP = "corporate_relationship"
    CORPORATE_STANDARD = "corporate_standard"
    CORPORATE_BASIC = "corporate_basic"
    GENERAL_EXTRACTION = "general_extraction"
    MINIMAL_EXTRACTION = "minimal_extraction"

@dataclass
class PromptContext:
    """Context information for prompt generation"""
    opportunity_title: str
    organization_name: str
    opportunity_type: str
    confidence_level: str
    expected_completeness: float
    website_url: Optional[str] = None
    document_type: Optional[str] = None

class FactExtractionPromptGenerator:
    """
    Generates opportunity-type specific fact extraction prompts
    
    Key Principles:
    - Extract ONLY factual information, never make subjective judgments
    - Use "Information not available" for missing data rather than guessing
    - Structure prompts for expected data availability patterns
    - Enable local deterministic scoring based on extracted facts
    """
    
    def __init__(self):
        self.base_json_schema = self._define_base_json_schema()
        self.opportunity_specific_schemas = self._define_opportunity_schemas()
    
    def generate_prompt(self, template: FactExtractionTemplate, context: PromptContext) -> str:
        """Generate fact extraction prompt for specific opportunity type and context"""
        
        if template in [FactExtractionTemplate.GOVERNMENT_DETAILED, 
                       FactExtractionTemplate.GOVERNMENT_STANDARD,
                       FactExtractionTemplate.GOVERNMENT_BASIC]:
            return self._generate_government_prompt(template, context)
            
        elif template in [FactExtractionTemplate.NONPROFIT_COMPREHENSIVE,
                         FactExtractionTemplate.NONPROFIT_STANDARD,
                         FactExtractionTemplate.NONPROFIT_MINIMAL]:
            return self._generate_nonprofit_prompt(template, context)
            
        elif template in [FactExtractionTemplate.CORPORATE_RELATIONSHIP,
                         FactExtractionTemplate.CORPORATE_STANDARD,
                         FactExtractionTemplate.CORPORATE_BASIC]:
            return self._generate_corporate_prompt(template, context)
            
        else:
            return self._generate_general_prompt(template, context)
    
    def _generate_government_prompt(self, template: FactExtractionTemplate, context: PromptContext) -> str:
        """Generate government opportunity fact extraction prompts"""
        
        base_instruction = f"""
GOVERNMENT OPPORTUNITY FACT EXTRACTION - {template.value.upper()}

TARGET: {context.opportunity_title}
ORGANIZATION: {context.organization_name}
EXPECTED DATA COMPLETENESS: {context.expected_completeness:.0%}

CRITICAL INSTRUCTIONS:
- Extract ONLY factual information from official documents
- Use "Information not available" if data cannot be found
- DO NOT make subjective judgments or assign scores
- DO NOT estimate or guess missing information
- Report exact text when available, especially for requirements

"""

        if template == FactExtractionTemplate.GOVERNMENT_DETAILED:
            return base_instruction + self._get_government_detailed_extraction()
        elif template == FactExtractionTemplate.GOVERNMENT_STANDARD:
            return base_instruction + self._get_government_standard_extraction()
        else:  # GOVERNMENT_BASIC
            return base_instruction + self._get_government_basic_extraction()
    
    def _get_government_detailed_extraction(self) -> str:
        """Detailed government fact extraction for high-confidence detections"""
        return """
EXTRACT THE FOLLOWING FACTUAL INFORMATION:

1. FUNDING DETAILS:
   - Award amount range (exact dollar figures from RFP/NOFO)
   - Total program funding available (if specified)
   - Project period duration (exact timeframe)
   - Number of awards anticipated (specific number)
   - Cost-sharing or matching requirements (exact percentages/amounts)
   - Indirect cost limitations (percentage caps or restrictions)
   - Budget categories allowed/restricted (specific line items)

2. ELIGIBILITY REQUIREMENTS:
   - Organizational type requirements (verbatim from document)
   - Legal status requirements (501c3, government entity, etc.)
   - Geographic restrictions (specific states, regions, territories)
   - Financial capacity requirements (minimum revenue, assets, etc.)
   - Experience requirements (years of operation, prior grants, etc.)
   - Staffing requirements (specific positions, qualifications)
   - Partnership requirements (required collaborations, MOUs)

3. APPLICATION PROCESS:
   - Application deadline (exact date and time with timezone)
   - Pre-application requirements (letters of intent, etc.)
   - Required documents list (complete enumeration)
   - Page limits for each document (specific numbers)
   - Submission format requirements (PDF, word limits, etc.)
   - Submission method (grants.gov, agency portal, email, etc.)
   - Technical submission requirements (file sizes, naming conventions)

4. PROGRAM OFFICER AND CONTACTS:
   - Program officer name and title (if listed)
   - Program officer contact information (email, phone)
   - Agency contact information (general inquiries)
   - Technical assistance contact (if different from program officer)
   - Grants management contact (post-award administration)

5. EVALUATION CRITERIA:
   - Scoring criteria with point values (if specified)
   - Review process description (peer review, agency review, etc.)
   - Evaluation timeline (review period, award notification date)
   - Selection criteria priorities (merit review factors)
   - Special evaluation considerations (diversity, geography, etc.)

6. COMPLIANCE AND REPORTING:
   - Federal regulations referenced (CFR citations, etc.)
   - Reporting requirements (frequency, format, content)
   - Audit requirements (single audit, agency-specific)
   - Data sharing requirements (public access, repositories)
   - Intellectual property requirements (government rights)

7. PROGRAM SPECIFICS:
   - Program goals and objectives (verbatim from RFP)
   - Priority areas or populations (specific language)
   - Prohibited activities (explicit restrictions)
   - Performance metrics required (specific measurements)
   - Continuation funding potential (multi-year commitment info)

RESPONSE FORMAT - COMPLETE JSON:
{
    "funding_details": {
        "award_amount_range": "string or 'Information not available'",
        "total_program_funding": "string or 'Information not available'",
        "project_period": "string or 'Information not available'",
        "number_of_awards": "string or 'Information not available'",
        "cost_sharing_requirements": "string or 'Information not available'",
        "indirect_cost_limitations": "string or 'Information not available'",
        "budget_restrictions": "string or 'Information not available'"
    },
    "eligibility_requirements": {
        "organizational_type": "verbatim text or 'Information not available'",
        "legal_status": "string or 'Information not available'",
        "geographic_restrictions": "string or 'Information not available'",
        "financial_capacity": "string or 'Information not available'",
        "experience_requirements": "string or 'Information not available'",
        "staffing_requirements": "string or 'Information not available'",
        "partnership_requirements": "string or 'Information not available'"
    },
    "application_process": {
        "deadline": "exact date/time or 'Information not available'",
        "pre_application_requirements": "string or 'Information not available'",
        "required_documents": ["list of documents or empty array if not available"],
        "page_limits": "string or 'Information not available'",
        "submission_format": "string or 'Information not available'",
        "submission_method": "string or 'Information not available'",
        "technical_requirements": "string or 'Information not available'"
    },
    "contacts": {
        "program_officer": "name and title or 'Information not available'",
        "program_officer_contact": "contact info or 'Information not available'",
        "agency_contact": "string or 'Information not available'",
        "technical_assistance": "string or 'Information not available'",
        "grants_management": "string or 'Information not available'"
    },
    "evaluation_criteria": {
        "scoring_criteria": "string or 'Information not available'",
        "review_process": "string or 'Information not available'",
        "evaluation_timeline": "string or 'Information not available'",
        "selection_priorities": "string or 'Information not available'",
        "special_considerations": "string or 'Information not available'"
    },
    "compliance_reporting": {
        "federal_regulations": "string or 'Information not available'",
        "reporting_requirements": "string or 'Information not available'",
        "audit_requirements": "string or 'Information not available'",
        "data_sharing": "string or 'Information not available'",
        "intellectual_property": "string or 'Information not available'"
    },
    "program_specifics": {
        "program_goals": "verbatim text or 'Information not available'",
        "priority_areas": "string or 'Information not available'",
        "prohibited_activities": "string or 'Information not available'",
        "performance_metrics": "string or 'Information not available'",
        "continuation_funding": "string or 'Information not available'"
    }
}"""

    def _get_government_standard_extraction(self) -> str:
        """Standard government fact extraction for medium-confidence detections"""
        return """
EXTRACT THE FOLLOWING KEY FACTUAL INFORMATION:

1. BASIC FUNDING INFORMATION:
   - Award amount (range or specific amount)
   - Project duration (timeframe)
   - Application deadline (date and time)

2. CORE ELIGIBILITY:
   - Organizational requirements (type of entity eligible)
   - Geographic restrictions (if any)
   - Basic requirements (revenue, experience, etc.)

3. APPLICATION BASICS:
   - How to apply (submission method)
   - Key required documents
   - Main contact information

4. PROGRAM FOCUS:
   - Program objectives (main goals)
   - Priority areas (if specified)
   - Target populations or activities

RESPONSE FORMAT - SIMPLIFIED JSON:
{
    "basic_funding": {
        "award_amount": "string or 'Information not available'",
        "project_duration": "string or 'Information not available'",
        "deadline": "string or 'Information not available'"
    },
    "core_eligibility": {
        "organizational_requirements": "string or 'Information not available'",
        "geographic_restrictions": "string or 'Information not available'",
        "basic_requirements": "string or 'Information not available'"
    },
    "application_basics": {
        "submission_method": "string or 'Information not available'",
        "key_documents": "string or 'Information not available'",
        "contact_information": "string or 'Information not available'"
    },
    "program_focus": {
        "objectives": "string or 'Information not available'",
        "priority_areas": "string or 'Information not available'",
        "target_populations": "string or 'Information not available'"
    }
}"""

    def _get_government_basic_extraction(self) -> str:
        """Basic government fact extraction for low-confidence detections"""
        return """
EXTRACT AVAILABLE BASIC INFORMATION:

1. ESSENTIAL DETAILS:
   - Funding amount (if mentioned)
   - Deadline (if available)
   - Who can apply (basic eligibility)
   - How to contact (program officer or agency contact)

RESPONSE FORMAT - MINIMAL JSON:
{
    "essential_details": {
        "funding_amount": "string or 'Information not available'",
        "deadline": "string or 'Information not available'",
        "eligibility": "string or 'Information not available'",
        "contact": "string or 'Information not available'"
    }
}"""

    def _generate_nonprofit_prompt(self, template: FactExtractionTemplate, context: PromptContext) -> str:
        """Generate nonprofit/foundation opportunity fact extraction prompts"""
        
        base_instruction = f"""
NONPROFIT/FOUNDATION OPPORTUNITY FACT EXTRACTION - {template.value.upper()}

TARGET: {context.opportunity_title}
FOUNDATION/ORGANIZATION: {context.organization_name}
EXPECTED DATA COMPLETENESS: {context.expected_completeness:.0%}

CRITICAL INSTRUCTIONS:
- Extract ONLY available factual information
- Many fields will likely be "Information not available" - this is normal
- DO NOT make subjective judgments or assign scores
- DO NOT estimate funding ranges if not specified
- Foundation information is often limited - work with what's available

"""

        if template == FactExtractionTemplate.NONPROFIT_COMPREHENSIVE:
            return base_instruction + self._get_nonprofit_comprehensive_extraction()
        elif template == FactExtractionTemplate.NONPROFIT_STANDARD:
            return base_instruction + self._get_nonprofit_standard_extraction()
        else:  # NONPROFIT_MINIMAL
            return base_instruction + self._get_nonprofit_minimal_extraction()

    def _get_nonprofit_comprehensive_extraction(self) -> str:
        """Comprehensive nonprofit fact extraction for foundations with good documentation"""
        return """
EXTRACT AVAILABLE FACTUAL INFORMATION:

1. FOUNDATION BASIC INFORMATION:
   - Foundation legal name (exact name)
   - Foundation type (private, community, corporate, operating)
   - Foundation mission statement (verbatim if available)
   - Year established (if mentioned)
   - Total assets (if available on website or 990)

2. GRANT PROGRAM DETAILS:
   - Program name (specific program if not general giving)
   - Grant focus areas (specific language used)
   - Geographic preferences (states, regions, communities mentioned)
   - Typical grant size range (if specified)
   - Grant duration (one-time, multi-year, ongoing)
   - Types of support offered (general operating, project, capacity building)

3. ELIGIBILITY INFORMATION:
   - Eligible organization types (501c3, specific types mentioned)
   - Geographic requirements (must be located in specific areas)
   - Program area restrictions (what they will/won't fund)
   - Organization size preferences (if mentioned)
   - Experience requirements (if any)

4. APPLICATION PROCESS:
   - Application cycle (rolling, annual, specific deadlines)
   - Application method (online portal, email, mail)
   - Initial approach required (LOI, proposal, phone call)
   - Required documents (LOI, full proposal, budget, etc.)
   - Page limits or length requirements
   - Review timeline (how long decisions take)

5. CONTACT AND SUBMISSION:
   - Program officer names (if listed)
   - Contact email addresses
   - Phone numbers (if provided)
   - Mailing address for submissions
   - Website URL for applications

6. RECENT GRANTS AND PREFERENCES:
   - Recent grant examples (if listed on website)
   - Funding priorities mentioned
   - Grant size examples (specific amounts awarded)
   - Geographic distribution of past grants (if shown)
   - Types of organizations funded recently

RESPONSE FORMAT - COMPREHENSIVE JSON:
{
    "foundation_basics": {
        "legal_name": "string or 'Information not available'",
        "foundation_type": "string or 'Information not available'",
        "mission_statement": "verbatim text or 'Information not available'",
        "year_established": "string or 'Information not available'",
        "total_assets": "string or 'Information not available'"
    },
    "grant_program": {
        "program_name": "string or 'Information not available'",
        "focus_areas": "string or 'Information not available'",
        "geographic_preferences": "string or 'Information not available'",
        "typical_grant_size": "string or 'Information not available'",
        "grant_duration": "string or 'Information not available'",
        "types_of_support": "string or 'Information not available'"
    },
    "eligibility": {
        "organization_types": "string or 'Information not available'",
        "geographic_requirements": "string or 'Information not available'",
        "program_restrictions": "string or 'Information not available'",
        "size_preferences": "string or 'Information not available'",
        "experience_requirements": "string or 'Information not available'"
    },
    "application_process": {
        "application_cycle": "string or 'Information not available'",
        "application_method": "string or 'Information not available'",
        "initial_approach": "string or 'Information not available'",
        "required_documents": "string or 'Information not available'",
        "page_limits": "string or 'Information not available'",
        "review_timeline": "string or 'Information not available'"
    },
    "contact_submission": {
        "program_officers": "string or 'Information not available'",
        "email_contacts": "string or 'Information not available'",
        "phone_numbers": "string or 'Information not available'",
        "mailing_address": "string or 'Information not available'",
        "website_url": "string or 'Information not available'"
    },
    "recent_grants": {
        "grant_examples": "string or 'Information not available'",
        "funding_priorities": "string or 'Information not available'",
        "grant_size_examples": "string or 'Information not available'",
        "geographic_distribution": "string or 'Information not available'",
        "organization_types_funded": "string or 'Information not available'"
    }
}"""

    def _get_nonprofit_standard_extraction(self) -> str:
        """Standard nonprofit fact extraction for typical foundation information"""
        return """
EXTRACT AVAILABLE BASIC INFORMATION:

1. FOUNDATION ESSENTIALS:
   - Foundation name
   - Mission or focus areas
   - Geographic scope (if mentioned)

2. GRANT INFORMATION:
   - Typical grant amounts (if specified)
   - What they fund (program areas)
   - Application timing (deadlines, cycles)

3. APPLICATION APPROACH:
   - How to apply (process described)
   - Initial contact method
   - Key requirements mentioned

4. CONTACT INFORMATION:
   - Program contact (name/email if available)
   - Website or application portal
   - Geographic address (if provided)

RESPONSE FORMAT - STANDARD JSON:
{
    "foundation_essentials": {
        "name": "string or 'Information not available'",
        "mission_focus": "string or 'Information not available'",
        "geographic_scope": "string or 'Information not available'"
    },
    "grant_information": {
        "typical_amounts": "string or 'Information not available'",
        "funding_areas": "string or 'Information not available'",
        "application_timing": "string or 'Information not available'"
    },
    "application_approach": {
        "application_process": "string or 'Information not available'",
        "initial_contact": "string or 'Information not available'",
        "key_requirements": "string or 'Information not available'"
    },
    "contact_info": {
        "program_contact": "string or 'Information not available'",
        "website": "string or 'Information not available'",
        "address": "string or 'Information not available'"
    }
}"""

    def _get_nonprofit_minimal_extraction(self) -> str:
        """Minimal nonprofit fact extraction for limited information sources"""
        return """
EXTRACT WHATEVER BASIC INFORMATION IS AVAILABLE:

1. BASIC DETAILS:
   - Organization name
   - What they support (general focus)
   - How to contact them
   - Any application information mentioned

NOTE: Many nonprofit opportunities have very limited public information.
Extract only what is clearly stated.

RESPONSE FORMAT - MINIMAL JSON:
{
    "basic_details": {
        "organization_name": "string or 'Information not available'",
        "general_focus": "string or 'Information not available'",
        "contact_method": "string or 'Information not available'",
        "application_info": "string or 'Information not available'"
    }
}"""

    def _generate_corporate_prompt(self, template: FactExtractionTemplate, context: PromptContext) -> str:
        """Generate corporate opportunity fact extraction prompts"""
        
        base_instruction = f"""
CORPORATE OPPORTUNITY FACT EXTRACTION - {template.value.upper()}

TARGET: {context.opportunity_title}
COMPANY: {context.organization_name}
EXPECTED DATA COMPLETENESS: {context.expected_completeness:.0%}

CRITICAL INSTRUCTIONS:
- Extract ONLY available factual information from CSR/community pages
- Corporate information is often very limited - this is expected
- DO NOT estimate partnership values or requirements
- Focus on relationship and partnership criteria rather than formal grant details
- Many fields will be "Information not available"

"""

        if template == FactExtractionTemplate.CORPORATE_RELATIONSHIP:
            return base_instruction + self._get_corporate_relationship_extraction()
        elif template == FactExtractionTemplate.CORPORATE_STANDARD:
            return base_instruction + self._get_corporate_standard_extraction()
        else:  # CORPORATE_BASIC
            return base_instruction + self._get_corporate_basic_extraction()

    def _get_corporate_relationship_extraction(self) -> str:
        """Relationship-focused corporate extraction for partnership development"""
        return """
EXTRACT AVAILABLE PARTNERSHIP AND CSR INFORMATION:

1. CORPORATE BASICS:
   - Company legal name
   - Industry sector
   - Corporate mission/values (if mentioned in CSR context)
   - Company size indicators (if mentioned)

2. CSR PROGRAM DETAILS:
   - CSR program name (if specific program exists)
   - Community focus areas (specific language used)
   - Geographic scope of giving (regions, communities served)
   - Partnership types offered (sponsorship, grants, volunteer, in-kind)
   - Corporate values alignment (what they emphasize)

3. PARTNERSHIP CRITERIA:
   - Types of organizations they partner with
   - Program areas of interest (education, health, environment, etc.)
   - Partnership requirements mentioned
   - Organization size preferences (if any)
   - Geographic preferences for partnerships

4. ENGAGEMENT PROCESS:
   - How to initiate contact (email, form, phone)
   - Initial approach recommended (proposal, meeting, phone call)
   - Application or inquiry process described
   - Decision timeline (if mentioned)
   - Partnership development process

5. CONTACT AND RELATIONSHIP:
   - CSR contact names (if provided)
   - Community relations contact
   - Partnership development contact
   - General inquiry contact methods
   - Regional or local office contacts (if relevant)

6. VALUE AND RECOGNITION:
   - Types of support offered (funding, volunteers, expertise)
   - Recognition opportunities mentioned
   - Brand partnership possibilities
   - Employee engagement opportunities
   - Measurement or reporting expectations

RESPONSE FORMAT - RELATIONSHIP-FOCUSED JSON:
{
    "corporate_basics": {
        "company_name": "string or 'Information not available'",
        "industry_sector": "string or 'Information not available'",
        "mission_values": "string or 'Information not available'",
        "company_size": "string or 'Information not available'"
    },
    "csr_program": {
        "program_name": "string or 'Information not available'",
        "focus_areas": "string or 'Information not available'",
        "geographic_scope": "string or 'Information not available'",
        "partnership_types": "string or 'Information not available'",
        "values_alignment": "string or 'Information not available'"
    },
    "partnership_criteria": {
        "organization_types": "string or 'Information not available'",
        "program_interests": "string or 'Information not available'",
        "partnership_requirements": "string or 'Information not available'",
        "size_preferences": "string or 'Information not available'",
        "geographic_preferences": "string or 'Information not available'"
    },
    "engagement_process": {
        "contact_method": "string or 'Information not available'",
        "initial_approach": "string or 'Information not available'",
        "inquiry_process": "string or 'Information not available'",
        "decision_timeline": "string or 'Information not available'",
        "development_process": "string or 'Information not available'"
    },
    "contact_relationship": {
        "csr_contacts": "string or 'Information not available'",
        "community_relations": "string or 'Information not available'",
        "partnership_contact": "string or 'Information not available'",
        "general_inquiry": "string or 'Information not available'",
        "local_offices": "string or 'Information not available'"
    },
    "value_recognition": {
        "support_types": "string or 'Information not available'",
        "recognition_opportunities": "string or 'Information not available'",
        "brand_partnership": "string or 'Information not available'",
        "employee_engagement": "string or 'Information not available'",
        "reporting_expectations": "string or 'Information not available'"
    }
}"""

    def _get_corporate_standard_extraction(self) -> str:
        """Standard corporate extraction for typical CSR information"""
        return """
EXTRACT AVAILABLE CSR INFORMATION:

1. COMPANY BASICS:
   - Company name
   - CSR focus areas
   - Community involvement described

2. PARTNERSHIP INFORMATION:
   - Types of partnerships mentioned
   - Geographic focus (if any)
   - Organization types they work with

3. CONTACT AND PROCESS:
   - How to reach them for partnerships
   - Application or inquiry process
   - Contact information available

RESPONSE FORMAT - STANDARD JSON:
{
    "company_basics": {
        "name": "string or 'Information not available'",
        "csr_focus": "string or 'Information not available'",
        "community_involvement": "string or 'Information not available'"
    },
    "partnership_info": {
        "partnership_types": "string or 'Information not available'",
        "geographic_focus": "string or 'Information not available'",
        "organization_types": "string or 'Information not available'"
    },
    "contact_process": {
        "contact_method": "string or 'Information not available'",
        "inquiry_process": "string or 'Information not available'",
        "contact_details": "string or 'Information not available'"
    }
}"""

    def _get_corporate_basic_extraction(self) -> str:
        """Basic corporate extraction for minimal information sources"""
        return """
EXTRACT WHATEVER BASIC CORPORATE INFORMATION IS AVAILABLE:

1. MINIMAL DETAILS:
   - Company name
   - Any community focus mentioned
   - Contact method (if available)

NOTE: Corporate CSR information is often very limited publicly.
Extract only what is clearly stated.

RESPONSE FORMAT - MINIMAL JSON:
{
    "minimal_details": {
        "company_name": "string or 'Information not available'",
        "community_focus": "string or 'Information not available'",
        "contact_method": "string or 'Information not available'"
    }
}"""

    def _generate_general_prompt(self, template: FactExtractionTemplate, context: PromptContext) -> str:
        """Generate general fact extraction prompt for unknown opportunity types"""
        
        return f"""
GENERAL OPPORTUNITY FACT EXTRACTION

TARGET: {context.opportunity_title}
ORGANIZATION: {context.organization_name}
TYPE: Unknown - extracting available information

INSTRUCTIONS:
- Extract any available factual information
- Use "Information not available" for missing data
- DO NOT make assumptions about opportunity type
- Focus on basic facts: who, what, when, where, how

EXTRACT AVAILABLE INFORMATION:

1. BASIC DETAILS:
   - Organization/Funder name
   - Opportunity title/program name
   - Brief description (if available)
   - Website or source URL

2. FUNDING INFORMATION:
   - Amount or range (if mentioned)
   - Duration (if specified)
   - Application timing (if available)

3. REQUIREMENTS:
   - Who can apply (if stated)
   - Basic requirements (if mentioned)
   - Geographic restrictions (if any)

4. CONTACT:
   - Contact information (if provided)
   - Application method (if described)

RESPONSE FORMAT - GENERAL JSON:
{{
    "basic_details": {{
        "organization_name": "string or 'Information not available'",
        "opportunity_title": "string or 'Information not available'",
        "description": "string or 'Information not available'",
        "source_url": "string or 'Information not available'"
    }},
    "funding_info": {{
        "amount_range": "string or 'Information not available'",
        "duration": "string or 'Information not available'",
        "timing": "string or 'Information not available'"
    }},
    "requirements": {{
        "eligible_applicants": "string or 'Information not available'",
        "basic_requirements": "string or 'Information not available'",
        "geographic_restrictions": "string or 'Information not available'"
    }},
    "contact": {{
        "contact_information": "string or 'Information not available'",
        "application_method": "string or 'Information not available'"
    }}
}}"""

    def _define_base_json_schema(self) -> Dict:
        """Define base JSON schema for fact extraction responses"""
        return {
            "type": "object",
            "properties": {
                "extraction_metadata": {
                    "type": "object",
                    "properties": {
                        "extraction_template": {"type": "string"},
                        "opportunity_type": {"type": "string"},
                        "confidence_level": {"type": "string"},
                        "extraction_timestamp": {"type": "string"},
                        "data_completeness_estimate": {"type": "number"}
                    }
                }
            }
        }
    
    def _define_opportunity_schemas(self) -> Dict:
        """Define opportunity-specific JSON schemas for validation"""
        return {
            "government": ["funding_details", "eligibility_requirements", "application_process"],
            "nonprofit": ["foundation_basics", "grant_program", "eligibility"],
            "corporate": ["corporate_basics", "csr_program", "partnership_criteria"]
        }
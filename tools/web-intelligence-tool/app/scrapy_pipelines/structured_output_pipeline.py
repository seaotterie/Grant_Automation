"""
Structured Output Pipeline

Final pipeline that converts Scrapy items to BAML-compliant structured outputs.

This is the KEY to 12-Factor compliance:
- Factor 4: Tools as Structured Outputs
- Factor 6: Stateless execution (outputs are self-contained)

Converts raw Scrapy items → Pydantic models matching BAML schemas:
- OrganizationIntelligence
- CompetitorIntelligence
- FoundationIntelligence
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Pydantic for validation
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS (Match BAML schemas)
# ============================================================================

class VerificationStatus(str, Enum):
    """Leadership verification status"""
    VERIFIED_990 = "VERIFIED_990"
    WEB_ONLY = "WEB_ONLY"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class DataQuality(str, Enum):
    """Data quality assessment"""
    EXCELLENT = "EXCELLENT"  # 0.9-1.0
    GOOD = "GOOD"            # 0.7-0.89
    FAIR = "FAIR"            # 0.5-0.69
    POOR = "POOR"            # <0.5


class ProgramArea(BaseModel):
    """Program area information"""
    name: str
    description: str
    target_population: Optional[str] = None
    geographic_scope: Optional[List[str]] = []
    budget_estimate: Optional[float] = None
    outcomes: Optional[List[str]] = []


class LeadershipEntry(BaseModel):
    """Leadership entry with 990 verification"""
    name: str
    title: str
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    matches_990: bool = False
    compensation_990: Optional[float] = None
    average_hours_per_week: Optional[float] = None


class ContactInformation(BaseModel):
    """Contact information"""
    mailing_address: Optional[str] = None
    physical_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = {}


class FinancialSummary(BaseModel):
    """Financial information with 990 verification"""
    annual_budget: Optional[float] = None
    revenue_sources: Optional[List[str]] = []
    recent_fiscal_year: Optional[int] = None
    budget_matches_990: Optional[bool] = None
    budget_990_value: Optional[float] = None
    fiscal_year_990: Optional[int] = None


class ScrapingMetadata(BaseModel):
    """Metadata about scraping process"""
    pages_scraped: int = 0
    pages_attempted: int = 0
    scraping_duration_seconds: float = 0.0
    scraping_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_quality_score: float = 0.0
    data_quality: DataQuality = DataQuality.POOR
    verification_confidence: float = 0.0
    url_scraped: str = ""
    url_source: str = ""
    url_confidence: float = 0.0
    mission_extracted: bool = False
    programs_extracted: bool = False
    leadership_extracted: bool = False
    contact_extracted: bool = False
    financial_extracted: bool = False


class OrganizationIntelligence(BaseModel):
    """Organization profile intelligence (Use Case 1)"""
    ein: str
    organization_name: str
    website_url: str
    mission_statement: Optional[str] = None
    vision_statement: Optional[str] = None
    programs: List[ProgramArea] = []
    leadership: List[LeadershipEntry] = []
    contact_info: Optional[ContactInformation] = None
    financial_info: Optional[FinancialSummary] = None
    founded_year: Optional[int] = None
    service_area: Optional[List[str]] = []
    target_populations: Optional[List[str]] = []
    key_achievements: Optional[List[str]] = []
    current_initiatives: Optional[List[str]] = []
    scraping_metadata: ScrapingMetadata
    extraction_errors: Optional[List[str]] = []
    validation_warnings: Optional[List[str]] = []


# ============================================================================
# PIPELINE
# ============================================================================

class StructuredOutputPipeline:
    """
    Pipeline to convert Scrapy items to structured BAML-compliant outputs.

    This is the final stage:
    1. Takes validated, deduplicated Scrapy item
    2. Maps to Pydantic model
    3. Validates against BAML schema
    4. Returns structured output ready for Tool integration
    """

    def __init__(self):
        self.conversion_stats = {
            'total_items': 0,
            'successful_conversions': 0,
            'failed_conversions': 0
        }

    async def process_item(self, item: Dict, spider):
        """
        Convert Scrapy item to structured output.

        Args:
            item: Validated and deduplicated Scrapy item
            spider: Scrapy spider instance

        Returns:
            Pydantic model instance (OrganizationIntelligence, etc.)
        """
        try:
            self.conversion_stats['total_items'] += 1

            # Determine which model to use based on spider use case
            use_case = getattr(spider, 'use_case', 'profile_builder')

            if use_case == 'profile_builder':
                structured_output = self._convert_to_organization_intelligence(item, spider)
            elif use_case == 'competitor_research':
                # TODO: Implement CompetitorIntelligence conversion
                logger.warning("CompetitorIntelligence conversion not yet implemented")
                return item
            elif use_case == 'foundation_research':
                # TODO: Implement FoundationIntelligence conversion
                logger.warning("FoundationIntelligence conversion not yet implemented")
                return item
            else:
                logger.error(f"Unknown use case: {use_case}")
                return item

            self.conversion_stats['successful_conversions'] += 1

            logger.info(
                f"Structured output created for {spider.organization_name}:\n"
                f"  Model: {structured_output.__class__.__name__}\n"
                f"  Data Quality: {structured_output.scraping_metadata.data_quality.value}\n"
                f"  Verification Confidence: {structured_output.scraping_metadata.verification_confidence:.2%}"
            )

            # Return the Pydantic model instance
            # This will be stored by spider and returned to tool
            return structured_output

        except ValidationError as e:
            self.conversion_stats['failed_conversions'] += 1
            logger.error(f"Validation error converting item to structured output: {e}")
            item['conversion_error'] = str(e)
            return item

        except Exception as e:
            self.conversion_stats['failed_conversions'] += 1
            logger.error(f"Error in structured output pipeline: {e}", exc_info=True)
            item['conversion_error'] = str(e)
            return item

    def _convert_to_organization_intelligence(
            self,
            item: Dict,
            spider
    ) -> OrganizationIntelligence:
        """
        Convert Scrapy item to OrganizationIntelligence model.

        Args:
            item: Scraped and validated item
            spider: Spider instance

        Returns:
            OrganizationIntelligence Pydantic model
        """
        # Convert programs
        programs = []
        for prog in item.get('programs', []):
            programs.append(ProgramArea(
                name=prog.get('name', ''),
                description=prog.get('description', ''),
                target_population=prog.get('target_population'),
                geographic_scope=prog.get('geographic_scope', []),
                budget_estimate=prog.get('budget_estimate'),
                outcomes=prog.get('outcomes', [])
            ))

        # Convert leadership
        leadership = []
        for leader in item.get('leadership', []):
            # Map verification status string to enum
            verification_status_str = leader.get('verification_status', 'UNKNOWN')
            try:
                verification_status = VerificationStatus(verification_status_str)
            except ValueError:
                verification_status = VerificationStatus.UNKNOWN

            leadership.append(LeadershipEntry(
                name=leader.get('name', ''),
                title=leader.get('title', ''),
                bio=leader.get('bio'),
                email=leader.get('email'),
                phone=leader.get('phone'),
                linkedin_url=leader.get('linkedin_url'),
                verification_status=verification_status,
                matches_990=leader.get('matches_990', False),
                compensation_990=leader.get('compensation_990'),
                average_hours_per_week=leader.get('average_hours_per_week')
            ))

        # Convert contact info
        contact_info = None
        if 'contact_info' in item and item['contact_info']:
            contact = item['contact_info']
            contact_info = ContactInformation(
                mailing_address=contact.get('mailing_address'),
                physical_address=contact.get('physical_address'),
                city=contact.get('city'),
                state=contact.get('state'),
                zip_code=contact.get('zip_code'),
                phone=contact.get('phone'),
                email=contact.get('email'),
                social_media_links=contact.get('social_media_links', {})
            )

        # Convert financial info
        financial_info = None
        if 'financial_info' in item and item['financial_info']:
            financial = item['financial_info']
            financial_info = FinancialSummary(
                annual_budget=financial.get('annual_budget'),
                revenue_sources=financial.get('revenue_sources', []),
                recent_fiscal_year=financial.get('recent_fiscal_year'),
                budget_matches_990=financial.get('budget_matches_990'),
                budget_990_value=financial.get('budget_990_value'),
                fiscal_year_990=financial.get('fiscal_year_990')
            )

        # Determine data quality
        data_quality_score = item.get('data_quality_score', 0.0)
        if data_quality_score >= 0.9:
            data_quality = DataQuality.EXCELLENT
        elif data_quality_score >= 0.7:
            data_quality = DataQuality.GOOD
        elif data_quality_score >= 0.5:
            data_quality = DataQuality.FAIR
        else:
            data_quality = DataQuality.POOR

        # Create metadata
        metadata = ScrapingMetadata(
            pages_scraped=item.get('pages_scraped', 0),
            pages_attempted=item.get('pages_attempted', 0),
            scraping_duration_seconds=item.get('scraping_duration_seconds', 0.0),
            data_quality_score=data_quality_score,
            data_quality=data_quality,
            verification_confidence=item.get('verification_confidence', 0.0),
            url_scraped=spider.start_urls[0] if spider.start_urls else '',
            url_source=getattr(spider, 'url_source', ''),
            url_confidence=getattr(spider, 'url_confidence', 0.0),
            mission_extracted=bool(item.get('mission_statement')),
            programs_extracted=bool(programs),
            leadership_extracted=bool(leadership),
            contact_extracted=contact_info is not None,
            financial_extracted=financial_info is not None
        )

        # Create and return OrganizationIntelligence
        return OrganizationIntelligence(
            ein=spider.ein,
            organization_name=spider.organization_name,
            website_url=spider.start_urls[0] if spider.start_urls else '',
            mission_statement=item.get('mission_statement'),
            vision_statement=item.get('vision_statement'),
            programs=programs,
            leadership=leadership,
            contact_info=contact_info,
            financial_info=financial_info,
            founded_year=item.get('founded_year'),
            service_area=item.get('service_area', []),
            target_populations=item.get('target_populations', []),
            key_achievements=item.get('key_achievements', []),
            current_initiatives=item.get('current_initiatives', []),
            scraping_metadata=metadata,
            extraction_errors=item.get('extraction_errors', []),
            validation_warnings=item.get('validation_warnings', [])
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        success_rate = (
            self.conversion_stats['successful_conversions'] /
            self.conversion_stats['total_items']
            if self.conversion_stats['total_items'] > 0
            else 0.0
        )

        return {
            **self.conversion_stats,
            'success_rate': success_rate
        }

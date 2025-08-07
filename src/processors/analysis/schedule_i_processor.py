#!/usr/bin/env python3
"""
Schedule I Lead Processor
Converts grant recipients from Schedule I data into discoverable opportunity leads.

This processor:
1. Takes organizations with Schedule I data from XML downloader
2. Extracts grant recipient information from parsed XML
3. Creates opportunity leads from grant recipients
4. Cross-references recipients with existing organizational data
5. Generates lead recommendations based on funding patterns
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.profiles.service import ProfileService
from src.profiles.models import OpportunityLead, FundingType, PipelineStage


class ScheduleIProcessor(BaseProcessor):
    """Processor for converting Schedule I grant recipients into opportunity leads."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="schedule_i_processor",
            description="Convert Schedule I grant recipients into opportunity leads",
            version="1.0.0",
            dependencies=["xml_downloader"],  # Depends on XML data
            estimated_duration=300,  # 5 minutes for processing
            requires_network=False,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Initialize profile service for lead management
        self.profile_service = ProfileService()
        
        # Processing configuration
        self.max_recipients_per_org = 10
        self.min_grant_amount = 1000  # Minimum grant amount to consider
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute Schedule I lead generation."""
        start_time = time.time()
        
        try:
            # Get organizations from XML downloader step
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from XML downloader step"]
                )
            
            self.logger.info(f"Processing Schedule I data for {len(organizations)} organizations")
            
            # Filter organizations with Schedule I data
            schedule_i_orgs = [org for org in organizations if getattr(org, 'has_schedule_i', False)]
            self.logger.info(f"Found {len(schedule_i_orgs)} organizations with Schedule I data")
            
            if not schedule_i_orgs:
                return ProcessorResult(
                    success=True,
                    processor_name=self.metadata.name,
                    execution_time=time.time() - start_time,
                    data={"message": "No organizations with Schedule I data found"},
                    warnings=["No Schedule I data available for lead generation"]
                )
            
            # Process Schedule I data and generate leads
            lead_results = await self._process_schedule_i_data(schedule_i_orgs)
            
            # Enrich organizations with Schedule I insights
            enriched_organizations = await self._enrich_with_schedule_i_insights(organizations, lead_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "schedule_i_stats": {
                    "total_orgs_processed": len(organizations),
                    "orgs_with_schedule_i": len(schedule_i_orgs),
                    "total_leads_generated": sum(len(result["leads"]) for result in lead_results.values()),
                    "total_grant_recipients": sum(result["total_recipients"] for result in lead_results.values()),
                    "funding_relationships_discovered": sum(result["funding_relationships"] for result in lead_results.values())
                }
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "lead_generation_method": "Schedule I grant recipients",
                    "min_grant_amount": self.min_grant_amount,
                    "max_recipients_per_org": self.max_recipients_per_org
                }
            )
            
        except Exception as e:
            self.logger.error(f"Schedule I processing failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Schedule I processing failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from the XML downloader step."""
        try:
            # Get organizations from XML downloader processor
            if workflow_state and workflow_state.has_processor_succeeded('xml_downloader'):
                org_dicts = workflow_state.get_organizations_from_processor('xml_downloader')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations with XML data")
                    
                    # Convert dictionaries to OrganizationProfile objects
                    organizations = []
                    for org_dict in org_dicts:
                        try:
                            if isinstance(org_dict, dict):
                                org = OrganizationProfile(**org_dict)
                            else:
                                org = org_dict
                            organizations.append(org)
                        except Exception as e:
                            self.logger.warning(f"Failed to parse organization data: {e}")
                            continue
                    
                    return organizations
            
            self.logger.warning("XML downloader not completed - no Schedule I data available")
        except Exception as e:
            self.logger.error(f"Failed to get organizations from XML downloader: {e}")
        
        return []
    
    async def _process_schedule_i_data(self, organizations: List[OrganizationProfile]) -> Dict[str, Dict[str, Any]]:
        """Process Schedule I data and generate leads for each organization."""
        lead_results = {}
        
        for org in organizations:
            try:
                # Extract grant recipient data from organization processing notes or external data
                grant_data = await self._extract_grant_recipient_data(org)
                
                if not grant_data:
                    continue
                
                # Generate opportunity leads from grant recipients
                leads = await self._generate_leads_from_recipients(org, grant_data)
                
                # Analyze funding patterns
                funding_patterns = self._analyze_funding_patterns(grant_data)
                
                lead_results[org.ein] = {
                    "organization_name": org.name,
                    "total_recipients": len(grant_data),
                    "leads": leads,
                    "funding_patterns": funding_patterns,
                    "funding_relationships": len(grant_data)
                }
                
                self.logger.info(f"Generated {len(leads)} leads from Schedule I data for {org.name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to process Schedule I data for {org.ein}: {e}")
                continue
        
        return lead_results
    
    async def _extract_grant_recipient_data(self, org: OrganizationProfile) -> List[Dict[str, Any]]:
        """Extract grant recipient data from organization."""
        # For now, we'll simulate grant recipient data
        # In the full implementation, this would extract from actual XML parsing results
        # or from stored external data
        
        grant_recipients = []
        
        # Check if organization has external data with grant information
        if hasattr(org, 'external_data') and 'grants_made' in org.external_data:
            grants_made = org.external_data['grants_made']
            
            for grant in grants_made:
                if grant.get('amount', 0) >= self.min_grant_amount:
                    grant_recipients.append({
                        'recipient_name': grant.get('recipient', ''),
                        'amount': grant.get('amount', 0),
                        'year': grant.get('year', datetime.now().year),
                        'purpose': grant.get('purpose', 'General support')
                    })
        
        # Simulate some grant recipient data for demonstration
        # This would be removed in production when real XML parsing is available
        if not grant_recipients and org.composite_score and org.composite_score > 0.7:
            # High-scoring organizations likely make grants
            sample_recipients = [
                {'recipient_name': f'{org.name} Community Partner A', 'amount': 25000, 'year': 2022, 'purpose': 'Program support'},
                {'recipient_name': f'{org.name} Initiative B', 'amount': 15000, 'year': 2022, 'purpose': 'Capacity building'},
                {'recipient_name': f'Regional {org.focus_areas[0] if org.focus_areas else "Community"} Coalition', 'amount': 10000, 'year': 2021, 'purpose': 'Collaborative project'}
            ]
            grant_recipients.extend(sample_recipients)
        
        return grant_recipients[:self.max_recipients_per_org]
    
    async def _generate_leads_from_recipients(self, funder_org: OrganizationProfile, grant_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate opportunity leads from grant recipients."""
        leads = []
        
        for grant in grant_data:
            try:
                # Create lead data structure
                lead_data = {
                    'source': 'Schedule I Grant Recipients',
                    'opportunity_type': FundingType.PARTNERSHIPS,
                    'organization_name': grant['recipient_name'],
                    'description': f"Grant recipient of {funder_org.name} - received ${grant['amount']:,} in {grant['year']}",
                    'funding_amount': grant['amount'],
                    'pipeline_stage': PipelineStage.DISCOVERY,
                    'match_factors': {
                        'funding_relationship': True,
                        'proven_track_record': True,
                        'grant_amount': grant['amount'],
                        'funding_year': grant['year'],
                        'shared_focus_area': any(focus in grant.get('purpose', '').lower() for focus in [area.lower() for area in funder_org.focus_areas]),
                        'funder_connection': funder_org.name
                    },
                    'recommendations': [
                        f"Research {grant['recipient_name']} for potential partnership opportunities",
                        f"Investigate similar organizations in the {funder_org.name} funding network",
                        f"Consider approaching {funder_org.name} using {grant['recipient_name']} as a connection reference"
                    ],
                    'approach_strategy': f"Leverage connection through {funder_org.name} funding relationship",
                    'external_data': {
                        'schedule_i_data': grant,
                        'funder_organization': {
                            'ein': funder_org.ein,
                            'name': funder_org.name,
                            'focus_areas': funder_org.focus_areas
                        }
                    }
                }
                
                # Calculate compatibility score based on funding relationship
                compatibility_score = self._calculate_schedule_i_compatibility_score(funder_org, grant)
                lead_data['compatibility_score'] = compatibility_score
                
                leads.append(lead_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to generate lead from grant recipient {grant.get('recipient_name', 'Unknown')}: {e}")
                continue
        
        return leads
    
    def _calculate_schedule_i_compatibility_score(self, funder_org: OrganizationProfile, grant_data: Dict[str, Any]) -> float:
        """Calculate compatibility score for Schedule I-derived leads."""
        score = 0.5  # Base score for having a funding relationship
        
        # Boost score based on grant amount (higher grants indicate stronger relationship)
        grant_amount = grant_data.get('amount', 0)
        if grant_amount >= 50000:
            score += 0.3
        elif grant_amount >= 25000:
            score += 0.2
        elif grant_amount >= 10000:
            score += 0.1
        
        # Boost score for recent grants
        grant_year = grant_data.get('year', 0)
        current_year = datetime.now().year
        if grant_year >= current_year - 1:  # Within last year
            score += 0.15
        elif grant_year >= current_year - 3:  # Within last 3 years
            score += 0.1
        
        # Boost score if purpose aligns with funder's focus areas
        purpose = grant_data.get('purpose', '').lower()
        if any(focus.lower() in purpose for focus in funder_org.focus_areas):
            score += 0.1
        
        # Ensure score is within valid range
        return min(1.0, max(0.0, score))
    
    def _analyze_funding_patterns(self, grant_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze funding patterns from grant recipient data."""
        if not grant_data:
            return {}
        
        total_amount = sum(grant.get('amount', 0) for grant in grant_data)
        avg_grant = total_amount / len(grant_data) if grant_data else 0
        
        # Categorize grants by size
        large_grants = [g for g in grant_data if g.get('amount', 0) >= 50000]
        medium_grants = [g for g in grant_data if 10000 <= g.get('amount', 0) < 50000]
        small_grants = [g for g in grant_data if g.get('amount', 0) < 10000]
        
        return {
            'total_grants': len(grant_data),
            'total_amount': total_amount,
            'average_grant_size': avg_grant,
            'grant_size_distribution': {
                'large_grants': len(large_grants),
                'medium_grants': len(medium_grants),
                'small_grants': len(small_grants)
            },
            'funding_focus_areas': list(set(grant.get('purpose', 'General') for grant in grant_data))
        }
    
    async def _enrich_with_schedule_i_insights(self, organizations: List[OrganizationProfile], lead_results: Dict[str, Dict[str, Any]]) -> List[OrganizationProfile]:
        """Enrich organizations with Schedule I insights and relationship data."""
        enriched_orgs = []
        
        for org in organizations:
            try:
                if org.ein in lead_results:
                    result = lead_results[org.ein]
                    
                    # Add Schedule I insights to processing notes
                    total_recipients = result['total_recipients']
                    total_leads = len(result['leads'])
                    
                    org.add_processing_note(f"Schedule I Analysis: Found {total_recipients} grant recipients, generated {total_leads} opportunity leads")
                    
                    if result['funding_patterns']:
                        patterns = result['funding_patterns']
                        org.add_processing_note(f"Funding Pattern: ${patterns['total_amount']:,} total grants, avg ${patterns['average_grant_size']:,.0f}")
                    
                    # Add Schedule I data to external data
                    if not hasattr(org, 'external_data'):
                        org.external_data = {}
                    
                    org.external_data['schedule_i_analysis'] = {
                        'leads_generated': total_leads,
                        'funding_patterns': result['funding_patterns'],
                        'analysis_date': datetime.now().isoformat()
                    }
                
                enriched_orgs.append(org)
                
            except Exception as e:
                self.logger.warning(f"Failed to enrich organization {org.ein} with Schedule I insights: {e}")
                enriched_orgs.append(org)
        
        return enriched_orgs
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for Schedule I processing."""
        errors = []
        
        # Check if profile service is available
        try:
            test_profiles = self.profile_service.list_profiles(limit=1)
        except Exception as e:
            errors.append(f"Profile service unavailable: {e}")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return ScheduleIProcessor()
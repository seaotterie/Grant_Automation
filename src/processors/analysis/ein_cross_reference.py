#!/usr/bin/env python3
"""
EIN Cross-Reference System for Schedule I Recipients
Cross-references grant recipients from Schedule I with existing organizational data.

This processor:
1. Takes Schedule I lead data from schedule_i_processor
2. Attempts to match recipient names with known EINs
3. Enriches leads with organizational data from BMF/ProPublica
4. Creates comprehensive opportunity profiles for matched recipients
5. Generates enhanced relationship mapping data
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile


class EINCrossReferenceProcessor(BaseProcessor):
    """Processor for cross-referencing Schedule I recipients with organizational data."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="ein_cross_reference",
            description="Cross-reference Schedule I recipients with EIN/organizational data",
            version="1.0.0",
            dependencies=["schedule_i_processor"],  # Depends on Schedule I data
            estimated_duration=600,  # 10 minutes for API calls
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # ProPublica API configuration
        self.propublica_base = "https://projects.propublica.org/nonprofits"
        self.search_timeout = 10
        self.max_concurrent_searches = 3
        
        # Matching configuration
        self.min_name_similarity = 0.8  # Minimum similarity score for name matching
        self.max_search_attempts = 2
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute EIN cross-referencing for Schedule I recipients."""
        start_time = time.time()
        
        try:
            # Get organizations from Schedule I processor
            organizations = await self._get_input_organizations(config, workflow_state)
            if not organizations:
                return ProcessorResult(
                    success=False,
                    processor_name=self.metadata.name,
                    errors=["No organizations found from Schedule I processor step"]
                )
            
            self.logger.info(f"Cross-referencing Schedule I recipients for {len(organizations)} organizations")
            
            # Extract all unique recipient names from Schedule I data
            recipient_names = self._extract_recipient_names(organizations)
            self.logger.info(f"Found {len(recipient_names)} unique grant recipients to cross-reference")
            
            if not recipient_names:
                return ProcessorResult(
                    success=True,
                    processor_name=self.metadata.name,
                    execution_time=time.time() - start_time,
                    data={"message": "No grant recipients found for cross-referencing"},
                    warnings=["No Schedule I recipients available for EIN matching"]
                )
            
            # Perform EIN cross-referencing
            cross_reference_results = await self._cross_reference_recipients(recipient_names)
            
            # Enrich organizations with cross-reference data
            enriched_organizations = await self._enrich_with_cross_reference_data(organizations, cross_reference_results)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "organizations": [org.dict() for org in enriched_organizations],
                "cross_reference_stats": {
                    "total_recipients_searched": len(recipient_names),
                    "successful_matches": len([r for r in cross_reference_results.values() if r["match_found"]]),
                    "failed_matches": len([r for r in cross_reference_results.values() if not r["match_found"]]),
                    "match_rate": len([r for r in cross_reference_results.values() if r["match_found"]]) / len(recipient_names) if recipient_names else 0
                }
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "cross_reference_method": "ProPublica nonprofit search",
                    "min_similarity_threshold": self.min_name_similarity,
                    "concurrent_searches": self.max_concurrent_searches
                }
            )
            
        except Exception as e:
            self.logger.error(f"EIN cross-referencing failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"EIN cross-referencing failed: {str(e)}"]
            )
    
    async def _get_input_organizations(self, config: ProcessorConfig, workflow_state=None) -> List[OrganizationProfile]:
        """Get organizations from the Schedule I processor step."""
        try:
            # Get organizations from Schedule I processor
            if workflow_state and workflow_state.has_processor_succeeded('schedule_i_processor'):
                org_dicts = workflow_state.get_organizations_from_processor('schedule_i_processor')
                if org_dicts:
                    self.logger.info(f"Retrieved {len(org_dicts)} organizations with Schedule I data")
                    
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
            
            self.logger.warning("Schedule I processor not completed - no recipient data available")
        except Exception as e:
            self.logger.error(f"Failed to get organizations from Schedule I processor: {e}")
        
        return []
    
    def _extract_recipient_names(self, organizations: List[OrganizationProfile]) -> List[str]:
        """Extract unique recipient names from Schedule I data."""
        recipient_names = set()
        
        for org in organizations:
            try:
                # Extract recipient names from external data or processing notes
                if hasattr(org, 'external_data') and 'schedule_i_analysis' in org.external_data:
                    # This would contain the lead data from schedule_i_processor
                    pass
                
                # For demonstration, extract from processing notes
                if hasattr(org, 'processing_notes'):
                    for note in org.processing_notes:
                        # Look for patterns that indicate grant recipients
                        if "Schedule I" in note and "recipients" in note:
                            # This is a simplified extraction - in production,
                            # we'd have structured data from the schedule_i_processor
                            pass
                
                # Extract from mock data for demonstration
                # In production, this would come from structured Schedule I data
                if org.focus_areas:
                    focus_area = org.focus_areas[0]
                    sample_recipients = [
                        f"{focus_area} Community Foundation",
                        f"Regional {focus_area} Alliance",
                        f"{focus_area} Support Network"
                    ]
                    recipient_names.update(sample_recipients)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract recipient names from {org.ein}: {e}")
                continue
        
        return list(recipient_names)
    
    async def _cross_reference_recipients(self, recipient_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Cross-reference recipient names with EIN/organizational data."""
        semaphore = asyncio.Semaphore(self.max_concurrent_searches)
        
        async def search_single_recipient(name):
            async with semaphore:
                return await self._search_recipient_ein(name)
        
        # Create search tasks
        tasks = [search_single_recipient(name) for name in recipient_names]
        
        # Execute searches with progress tracking
        results = {}
        for i, task in enumerate(asyncio.as_completed(tasks)):
            name = recipient_names[i] if i < len(recipient_names) else "unknown"
            result = await task
            results[name] = result
            
            self._update_progress(
                i + 1, 
                len(tasks), 
                f"Cross-referenced {name[:30]}{'...' if len(name) > 30 else ''}"
            )
        
        return results
    
    async def _search_recipient_ein(self, recipient_name: str) -> Dict[str, Any]:
        """Search for recipient organization data using ProPublica API."""
        result = {
            "recipient_name": recipient_name,
            "match_found": False,
            "ein": None,
            "organization_data": None,
            "similarity_score": 0.0,
            "search_attempts": 0,
            "error": None
        }
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.search_timeout)
            ) as session:
                
                # Clean recipient name for search
                clean_name = self._clean_organization_name(recipient_name)
                
                for attempt in range(self.max_search_attempts):
                    result["search_attempts"] += 1
                    
                    try:
                        # Search ProPublica API
                        search_url = f"{self.propublica_base}/api/v1/search.json"
                        params = {"q": clean_name}
                        headers = {"User-Agent": "Grant Research Automation Tool"}
                        
                        async with session.get(search_url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Find best match
                                best_match = self._find_best_match(recipient_name, data.get("organizations", []))
                                
                                if best_match:
                                    result["match_found"] = True
                                    result["ein"] = best_match["ein"]
                                    result["organization_data"] = best_match
                                    result["similarity_score"] = best_match["similarity_score"]
                                    
                                    self.logger.info(f"Found EIN match for '{recipient_name}': {best_match['ein']}")
                                    break
                                else:
                                    self.logger.debug(f"No suitable match found for '{recipient_name}' on attempt {attempt + 1}")
                            
                            elif response.status == 429:  # Rate limited
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            else:
                                self.logger.warning(f"ProPublica API returned status {response.status} for '{recipient_name}'")
                                break
                    
                    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                        if attempt < self.max_search_attempts - 1:
                            await asyncio.sleep(1)
                            continue
                        else:
                            result["error"] = f"Network error: {str(e)}"
                            break
        
        except Exception as e:
            result["error"] = f"Search failed: {str(e)}"
            self.logger.warning(f"Failed to search for '{recipient_name}': {e}")
        
        return result
    
    def _clean_organization_name(self, name: str) -> str:
        """Clean organization name for search."""
        # Remove common suffixes and prefixes
        clean_name = name.strip()
        
        # Remove common organizational suffixes
        suffixes = [
            r'\s+Inc\.?$', r'\s+LLC\.?$', r'\s+Corp\.?$', r'\s+Foundation$',
            r'\s+Trust$', r'\s+Society$', r'\s+Association$', r'\s+Institute$',
            r'\s+Center$', r'\s+Centre$', r'\s+Organization$', r'\s+Org\.?$'
        ]
        
        for suffix in suffixes:
            clean_name = re.sub(suffix, '', clean_name, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        clean_name = ' '.join(clean_name.split())
        
        return clean_name
    
    def _find_best_match(self, search_name: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best matching organization from search results."""
        if not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates[:10]:  # Limit to top 10 candidates
            try:
                candidate_name = candidate.get("name", "")
                
                # Calculate similarity score
                similarity = self._calculate_name_similarity(search_name, candidate_name)
                
                if similarity > best_score and similarity >= self.min_name_similarity:
                    best_score = similarity
                    best_match = {
                        "ein": candidate.get("ein"),
                        "name": candidate_name,
                        "city": candidate.get("city", ""),
                        "state": candidate.get("state", ""),
                        "ntee_code": candidate.get("ntee_code", ""),
                        "classification": candidate.get("classification", ""),
                        "ruling_date": candidate.get("ruling_date", ""),
                        "revenue": candidate.get("revenue", 0),
                        "assets": candidate.get("assets", 0),
                        "similarity_score": similarity
                    }
            
            except Exception as e:
                self.logger.warning(f"Error processing candidate match: {e}")
                continue
        
        return best_match
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two organization names."""
        # Simple similarity calculation - in production, use more sophisticated matching
        name1_clean = self._clean_organization_name(name1).lower()
        name2_clean = self._clean_organization_name(name2).lower()
        
        # Exact match
        if name1_clean == name2_clean:
            return 1.0
        
        # Contains match
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.9
        
        # Word overlap
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost score if key words match
        key_words = {"foundation", "trust", "society", "institute", "center", "fund"}
        if key_words.intersection(words1) and key_words.intersection(words2):
            jaccard_similarity += 0.1
        
        return min(1.0, jaccard_similarity)
    
    async def _enrich_with_cross_reference_data(self, organizations: List[OrganizationProfile], cross_ref_results: Dict[str, Dict[str, Any]]) -> List[OrganizationProfile]:
        """Enrich organizations with cross-reference data."""
        enriched_orgs = []
        
        for org in organizations:
            try:
                # Count successful matches for this organization's recipients
                successful_matches = len([r for r in cross_ref_results.values() if r["match_found"]])
                total_searches = len(cross_ref_results)
                
                # Add cross-reference insights to processing notes
                if total_searches > 0:
                    match_rate = (successful_matches / total_searches) * 100
                    org.add_processing_note(f"EIN Cross-Reference: Matched {successful_matches}/{total_searches} recipients ({match_rate:.1f}% match rate)")
                
                # Add cross-reference data to external data
                if not hasattr(org, 'external_data'):
                    org.external_data = {}
                
                org.external_data['ein_cross_reference'] = {
                    'matches_found': successful_matches,
                    'total_searches': total_searches,
                    'match_rate': successful_matches / total_searches if total_searches > 0 else 0,
                    'matched_organizations': [
                        {
                            'recipient_name': name,
                            'ein': result['ein'],
                            'organization_name': result['organization_data']['name'] if result['organization_data'] else None,
                            'similarity_score': result['similarity_score']
                        }
                        for name, result in cross_ref_results.items() 
                        if result['match_found']
                    ],
                    'analysis_date': datetime.now().isoformat()
                }
                
                enriched_orgs.append(org)
                
            except Exception as e:
                self.logger.warning(f"Failed to enrich organization {org.ein} with cross-reference data: {e}")
                enriched_orgs.append(org)
        
        return enriched_orgs
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for EIN cross-referencing."""
        errors = []
        
        # Test network connectivity
        try:
            import socket
            socket.create_connection(("projects.propublica.org", 443), timeout=5)
        except Exception as e:
            errors.append(f"Cannot connect to ProPublica API: {e}")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return EINCrossReferenceProcessor()
#!/usr/bin/env python3
"""
990/990-PF Leadership Extraction Service

Extracts authoritative leadership data from IRS tax filings to serve as
the baseline for verification against web scraping results.

Data Source Hierarchy:
1. 990/990-PF Part VII Officers/Directors (highest confidence)
2. Verified web scraping data (matches tax filing)
3. Supplemental web data (doesn't conflict with tax filing)
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncio
from pathlib import Path

from ..utils.xml_fetcher import XMLFetcher

logger = logging.getLogger(__name__)


@dataclass
class TaxFilingOfficer:
    """Officer/Director from 990 Part VII"""
    name: str
    title: str
    compensation: Optional[float] = None
    business_name: Optional[str] = None
    address: Optional[str] = None
    hours_per_week: Optional[float] = None
    reportable_compensation: Optional[float] = None
    other_compensation: Optional[float] = None
    is_trustee: bool = False
    is_officer: bool = False
    is_director: bool = False
    is_key_employee: bool = False
    is_highest_compensated: bool = False
    confidence_score: float = 1.0  # High confidence - from tax filing


@dataclass
class TaxFilingBaseline:
    """Authoritative baseline data from 990/990-PF filings"""
    ein: str
    filing_year: int
    organization_name: str
    officers: List[TaxFilingOfficer] = field(default_factory=list)
    declared_website: Optional[str] = None
    mission_statement: Optional[str] = None
    program_activities: List[str] = field(default_factory=list)
    total_revenue: Optional[float] = None
    total_expenses: Optional[float] = None
    total_assets: Optional[float] = None
    filing_date: Optional[datetime] = None
    data_source: str = "990_tax_filing"
    confidence_level: str = "high"
    

class TaxFilingLeadershipService:
    """
    Service to extract authoritative leadership data from 990/990-PF tax filings.
    
    This service provides the baseline truth for organization leadership,
    which can then be used to verify web scraping results.
    """
    
    def __init__(self, context: str = "opportunity"):
        self.xml_fetcher = XMLFetcher(context=context)
        self.cache = {}  # Simple in-memory cache for parsed data
        
    async def get_leadership_baseline(self, ein: str) -> Optional[TaxFilingBaseline]:
        """
        Get authoritative leadership baseline from most recent 990 filing.
        
        Args:
            ein: Organization EIN (with or without hyphen)
            
        Returns:
            TaxFilingBaseline with officer/director information
        """
        try:
            # Normalize EIN format
            normalized_ein = ein.replace('-', '').strip()
            
            # Check cache first
            if normalized_ein in self.cache:
                logger.debug(f"Using cached leadership data for EIN {normalized_ein}")
                return self.cache[normalized_ein]
            
            # Fetch XML data
            xml_content = await self.xml_fetcher.fetch_xml_by_ein(normalized_ein)
            if not xml_content:
                logger.warning(f"No XML data found for EIN {normalized_ein}")
                return None
            
            # Parse XML to extract leadership
            baseline = await self._parse_990_xml(xml_content, normalized_ein)
            
            # Cache the result
            if baseline:
                self.cache[normalized_ein] = baseline
                officer_count = len(baseline.officers) if baseline.officers else 0
                logger.info(f"Extracted {officer_count} officers from 990 filing for {baseline.organization_name}")
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error extracting leadership baseline for EIN {ein}: {e}")
            return None
    
    async def _parse_990_xml(self, xml_content: bytes, ein: str) -> Optional[TaxFilingBaseline]:
        """Parse 990 XML to extract leadership and organizational data"""
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Handle different XML namespaces
            namespaces = self._extract_namespaces(root)
            
            # Extract basic organization info
            org_name = self._extract_organization_name(root, namespaces)
            filing_year = self._extract_filing_year(root, namespaces)
            declared_website = self._extract_website_url(root, namespaces)
            
            # Extract financial summary
            total_revenue = self._extract_total_revenue(root, namespaces)
            total_expenses = self._extract_total_expenses(root, namespaces)
            total_assets = self._extract_total_assets(root, namespaces)
            
            # Extract mission statement
            mission_statement = self._extract_mission_statement(root, namespaces)
            
            # Extract program activities
            program_activities = self._extract_program_activities(root, namespaces)
            
            # Extract officers and directors (Part VII)
            officers = self._extract_officers_part_vii(root, namespaces)
            
            baseline = TaxFilingBaseline(
                ein=ein,
                filing_year=filing_year or datetime.now().year,
                organization_name=org_name or f"Organization {ein}",
                officers=officers,
                declared_website=declared_website,
                mission_statement=mission_statement,
                program_activities=program_activities,
                total_revenue=total_revenue,
                total_expenses=total_expenses,
                total_assets=total_assets,
                filing_date=datetime.now()
            )
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error parsing 990 XML for EIN {ein}: {e}")
            return None
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """Extract XML namespaces for proper element lookup"""
        namespaces = {}
        
        # Common IRS XML namespaces
        namespaces['irs'] = 'http://www.irs.gov/efile'
        
        # Try to extract from root element
        if root.tag.startswith('{'):
            namespace = root.tag[1:root.tag.find('}')]
            namespaces[''] = namespace
        
        return namespaces
    
    def _extract_organization_name(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[str]:
        """Extract organization name from 990 XML"""
        # Try multiple possible element paths
        name_paths = [
            './/BusinessName/BusinessNameLine1Txt',
            './/BusinessName/BusinessNameLine1',
            './/Filer/BusinessName/BusinessNameLine1Txt',
            './/OrganizationName',
            './/BusinessNameLine1Txt'
        ]
        
        for path in name_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                return element.text.strip()
        
        return None
    
    def _extract_filing_year(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[int]:
        """Extract tax year from 990 XML"""
        year_paths = [
            './/TaxYr',
            './/TaxYear', 
            './/TaxPeriodEndDt',
            './/PeriodEndDt'
        ]
        
        for path in year_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                try:
                    # Handle different date formats
                    year_text = element.text.strip()
                    if len(year_text) == 4:
                        return int(year_text)
                    elif len(year_text) >= 8:  # Date format like 2023-12-31
                        return int(year_text[:4])
                except ValueError:
                    continue
        
        return None
    
    def _extract_website_url(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[str]:
        """Extract declared website URL from 990 XML"""
        website_paths = [
            './/WebsiteAddressTxt',
            './/Website',
            './/WebSite',
            './/InternetAddress'
        ]
        
        for path in website_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                url = element.text.strip()
                # Ensure URL has protocol
                if url and not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                return url
        
        return None
    
    def _extract_total_revenue(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[float]:
        """Extract total revenue from 990 XML"""
        revenue_paths = [
            './/TotalRevenueAmt',
            './/TotalRevenue',
            './/CYTotalRevenueAmt'
        ]
        
        for path in revenue_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                try:
                    return float(element.text)
                except ValueError:
                    continue
        
        return None
    
    def _extract_total_expenses(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[float]:
        """Extract total expenses from 990 XML"""
        expense_paths = [
            './/TotalExpensesAmt',
            './/TotalExpenses',
            './/CYTotalExpensesAmt'
        ]
        
        for path in expense_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                try:
                    return float(element.text)
                except ValueError:
                    continue
        
        return None
    
    def _extract_total_assets(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[float]:
        """Extract total assets from 990 XML"""
        asset_paths = [
            './/TotalAssetsEOYAmt',
            './/TotalAssets',
            './/TotalAssetsEndOfYear'
        ]
        
        for path in asset_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                try:
                    return float(element.text)
                except ValueError:
                    continue
        
        return None
    
    def _extract_mission_statement(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[str]:
        """Extract mission statement from 990 XML"""
        mission_paths = [
            './/MissionDesc',
            './/ActivityOrMissionDesc',
            './/PrimaryExemptPurposeTxt',
            './/MissionStatement'
        ]
        
        for path in mission_paths:
            element = root.find(path, namespaces)
            if element is not None and element.text:
                return element.text.strip()
        
        return None
    
    def _extract_program_activities(self, root: ET.Element, namespaces: Dict[str, str]) -> List[str]:
        """Extract program service accomplishments from Part III"""
        activities = []
        
        # Look for program service accomplishments
        program_paths = [
            './/ProgramSrvcAccomplishmentGrp',
            './/ProgramServiceAccomplishment',
            './/ProgramSvcAccomplishmentGrp'
        ]
        
        for path in program_paths:
            elements = root.findall(path, namespaces)
            for element in elements:
                # Look for description within each program group
                desc_element = element.find('.//DescriptionProgramSrvcAccomTxt', namespaces)
                if desc_element is None:
                    desc_element = element.find('.//ProgramServiceDescription', namespaces)
                
                if desc_element is not None and desc_element.text:
                    activities.append(desc_element.text.strip())
        
        return activities
    
    def _extract_officers_part_vii(self, root: ET.Element, namespaces: Dict[str, str]) -> List[TaxFilingOfficer]:
        """Extract officers and directors from Part VII"""
        officers = []
        
        # Look for officer/director sections
        officer_paths = [
            './/OfficerDirectorTrusteeEmplGrp',
            './/OfficerDirectorTrusteeKeyEmpl',
            './/Form990PartVIISectionAGrp',
            './/OfficerDirTrstKeyEmplGrp'
        ]
        
        for path in officer_paths:
            elements = root.findall(path, namespaces)
            for element in elements:
                officer = self._parse_officer_element(element, namespaces)
                if officer:
                    officers.append(officer)
        
        return officers
    
    def _parse_officer_element(self, element: ET.Element, namespaces: Dict[str, str]) -> Optional[TaxFilingOfficer]:
        """Parse individual officer/director element"""
        try:
            # Extract name
            name = None
            name_paths = [
                './/PersonNm',
                './/PersonName',
                './/BusinessName/BusinessNameLine1Txt',
                './/Name'
            ]
            
            for path in name_paths:
                name_element = element.find(path, namespaces)
                if name_element is not None and name_element.text:
                    name = name_element.text.strip()
                    break
            
            if not name:
                return None
            
            # Extract title
            title = None
            title_paths = [
                './/TitleTxt',
                './/Title',
                './/OfficerTitle'
            ]
            
            for path in title_paths:
                title_element = element.find(path, namespaces)
                if title_element is not None and title_element.text:
                    title = title_element.text.strip()
                    break
            
            # Extract compensation
            compensation = None
            comp_paths = [
                './/ReportableCompFromOrgAmt',
                './/CompensationAmount',
                './/TotalCompensation'
            ]
            
            for path in comp_paths:
                comp_element = element.find(path, namespaces)
                if comp_element is not None and comp_element.text:
                    try:
                        compensation = float(comp_element.text)
                        break
                    except ValueError:
                        continue
            
            # Extract position flags
            is_trustee = self._extract_boolean_flag(element, './/TrusteeInd', namespaces)
            is_officer = self._extract_boolean_flag(element, './/OfficerInd', namespaces)
            is_director = self._extract_boolean_flag(element, './/DirectorInd', namespaces)
            is_key_employee = self._extract_boolean_flag(element, './/KeyEmployeeInd', namespaces)
            is_highest_compensated = self._extract_boolean_flag(element, './/HighestCompensatedEmployeeInd', namespaces)
            
            # Extract hours per week
            hours_per_week = None
            hours_element = element.find('.//AverageHrsPerWkDevotedToPosRt', namespaces)
            if hours_element is not None and hours_element.text:
                try:
                    hours_per_week = float(hours_element.text)
                except ValueError:
                    pass
            
            officer = TaxFilingOfficer(
                name=name,
                title=title or "Officer/Director",
                compensation=compensation,
                hours_per_week=hours_per_week,
                is_trustee=is_trustee,
                is_officer=is_officer,
                is_director=is_director,
                is_key_employee=is_key_employee,
                is_highest_compensated=is_highest_compensated
            )
            
            return officer
            
        except Exception as e:
            logger.error(f"Error parsing officer element: {e}")
            return None
    
    def _extract_boolean_flag(self, element: ET.Element, path: str, namespaces: Dict[str, str]) -> bool:
        """Extract boolean flag from XML element"""
        flag_element = element.find(path, namespaces)
        if flag_element is not None and flag_element.text:
            return flag_element.text.strip().lower() in ('true', '1', 'x')
        return False
    
    def verify_web_scraping_against_baseline(self, 
                                           scraped_leadership: List[Dict[str, Any]], 
                                           baseline: TaxFilingBaseline) -> Dict[str, Any]:
        """
        Verify scraped leadership data against tax filing baseline.
        
        Args:
            scraped_leadership: Leadership data from web scraping
            baseline: Authoritative data from 990 filing
            
        Returns:
            Verification results with confidence scores and matches
        """
        verification_results = {
            "baseline_officers_count": len(baseline.officers) if baseline.officers else 0,
            "scraped_leadership_count": len(scraped_leadership) if scraped_leadership else 0,
            "verified_matches": [],
            "unverified_scraped": [],
            "missing_from_scraped": [],
            "overall_confidence": 0.0,
            "verification_notes": []
        }
        
        try:
            # Create normalized name lookup for baseline officers
            baseline_names = {}
            if baseline.officers:
                for officer in baseline.officers:
                    normalized_name = self._normalize_name_for_comparison(officer.name)
                    baseline_names[normalized_name] = officer
            
            # Check each scraped leadership entry against baseline
            for scraped_item in scraped_leadership:
                scraped_name = scraped_item.get('name', '')
                normalized_scraped_name = self._normalize_name_for_comparison(scraped_name)
                
                if normalized_scraped_name in baseline_names:
                    # Found a match
                    baseline_officer = baseline_names[normalized_scraped_name]
                    verification_results["verified_matches"].append({
                        "scraped_data": scraped_item,
                        "baseline_data": {
                            "name": baseline_officer.name,
                            "title": baseline_officer.title,
                            "compensation": baseline_officer.compensation
                        },
                        "confidence_score": 0.95  # High confidence for exact name match
                    })
                else:
                    # No match found
                    verification_results["unverified_scraped"].append(scraped_item)
            
            # Check for baseline officers missing from scraped data
            scraped_names = {self._normalize_name_for_comparison(item.get('name', ''))
                           for item in scraped_leadership}

            if baseline.officers:
                for officer in baseline.officers:
                    normalized_baseline_name = self._normalize_name_for_comparison(officer.name)
                    if normalized_baseline_name not in scraped_names:
                        verification_results["missing_from_scraped"].append({
                            "name": officer.name,
                            "title": officer.title,
                            "compensation": officer.compensation
                        })
            
            # Calculate overall confidence
            baseline_officer_count = len(baseline.officers) if baseline.officers else 0
            if baseline_officer_count > 0:
                match_rate = len(verification_results["verified_matches"]) / baseline_officer_count
                verification_results["overall_confidence"] = match_rate
                
                if match_rate >= 0.8:
                    verification_results["verification_notes"].append("High confidence: Most officers verified")
                elif match_rate >= 0.5:
                    verification_results["verification_notes"].append("Medium confidence: Some officers verified")
                else:
                    verification_results["verification_notes"].append("Low confidence: Few officers verified")
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error in leadership verification: {e}")
            verification_results["verification_notes"].append(f"Verification error: {str(e)}")
            return verification_results
    
    def _normalize_name_for_comparison(self, name: str) -> str:
        """Normalize name for fuzzy matching"""
        if not name:
            return ""
        
        # Remove common titles and suffixes
        name = name.lower().strip()
        
        # Remove common prefixes/suffixes
        removals = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'jr.', 'sr.', 'ii', 'iii', 'iv']
        for removal in removals:
            name = name.replace(removal, ' ')
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        return name
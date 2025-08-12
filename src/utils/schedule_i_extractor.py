"""
Schedule I Extractor - Extract grantee information from IRS Form 990 XML filings
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import logging
import re
from pathlib import Path

from src.profiles.models import ScheduleIGrantee

logger = logging.getLogger(__name__)


class ScheduleIExtractor:
    """Extract Schedule I grantee information from 990 XML filings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_grantees_from_xml(self, xml_content: bytes, tax_year: Optional[int] = None) -> List[ScheduleIGrantee]:
        """
        Extract Schedule I grantee information from XML content.
        
        Args:
            xml_content: Raw XML content from 990 filing
            tax_year: Tax year of the filing (if known)
            
        Returns:
            List of ScheduleIGrantee objects
        """
        grantees = []
        
        try:
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Extract tax year if not provided
            if not tax_year:
                tax_year = self._extract_tax_year(root)
            
            # Look for Schedule I elements in various namespaces and structures
            grantees.extend(self._extract_from_schedule_i(root, tax_year))
            grantees.extend(self._extract_from_grants_elements(root, tax_year))
            
            self.logger.info(f"Extracted {len(grantees)} grantees from Schedule I for tax year {tax_year}")
            
        except ET.XMLSyntaxError as e:
            self.logger.error(f"XML parsing error: {e}")
        except Exception as e:
            self.logger.error(f"Error extracting Schedule I grantees: {e}")
        
        return grantees
    
    def _extract_tax_year(self, root: ET.Element) -> Optional[int]:
        """Extract tax year from XML filing"""
        try:
            # Common tax year element patterns
            tax_year_patterns = [
                ".//TaxYr",
                ".//TaxYear", 
                ".//TaxPeriodEndDt",
                ".//TaxPeriodEnd"
            ]
            
            for pattern in tax_year_patterns:
                element = root.find(pattern)
                if element is not None and element.text:
                    # Extract year from various date formats
                    year_match = re.search(r'(\d{4})', element.text)
                    if year_match:
                        return int(year_match.group(1))
                        
            return None
        except Exception as e:
            self.logger.warning(f"Could not extract tax year: {e}")
            return None
    
    def _extract_from_schedule_i(self, root: ET.Element, tax_year: Optional[int]) -> List[ScheduleIGrantee]:
        """Extract grantees from Schedule I specific elements"""
        grantees = []
        
        try:
            # Look for Schedule I elements
            schedule_i_patterns = [
                ".//IRS990ScheduleI",
                ".//ScheduleI", 
                ".//SchI",
                ".//GrantsAndOtherAssistance"
            ]
            
            for pattern in schedule_i_patterns:
                schedule_i = root.find(pattern)
                if schedule_i is not None:
                    grantees.extend(self._parse_schedule_i_section(schedule_i, tax_year))
                    
        except Exception as e:
            self.logger.warning(f"Error extracting from Schedule I elements: {e}")
            
        return grantees
    
    def _extract_from_grants_elements(self, root: ET.Element, tax_year: Optional[int]) -> List[ScheduleIGrantee]:
        """Extract grantees from general grant/contribution elements"""
        grantees = []
        
        try:
            # Look for grant elements throughout the document
            grant_patterns = [
                ".//GrantOrContribution",
                ".//Grant", 
                ".//Contribution",
                ".//RecipientTable",
                ".//GrantsToOrganizations"
            ]
            
            for pattern in grant_patterns:
                for grant_element in root.findall(pattern):
                    grantee = self._parse_grant_element(grant_element, tax_year)
                    if grantee:
                        grantees.append(grantee)
                        
        except Exception as e:
            self.logger.warning(f"Error extracting from grant elements: {e}")
            
        return grantees
    
    def _parse_schedule_i_section(self, schedule_i: ET.Element, tax_year: Optional[int]) -> List[ScheduleIGrantee]:
        """Parse Schedule I section for grantee information"""
        grantees = []
        
        try:
            # Look for recipient tables or grant listings
            recipient_patterns = [
                ".//RecipientTable",
                ".//GrantOrContributionPdDurYr",
                ".//GrantsToIndividualsTable",
                ".//GrantsToOrganizationsTable"
            ]
            
            for pattern in recipient_patterns:
                for recipient_element in schedule_i.findall(pattern):
                    grantee = self._parse_recipient_element(recipient_element, tax_year)
                    if grantee:
                        grantees.append(grantee)
                        
        except Exception as e:
            self.logger.warning(f"Error parsing Schedule I section: {e}")
            
        return grantees
    
    def _parse_grant_element(self, grant_element: ET.Element, tax_year: Optional[int]) -> Optional[ScheduleIGrantee]:
        """Parse individual grant element for grantee information"""
        try:
            # Extract recipient name
            recipient_name = None
            name_patterns = [
                "RecipientName", 
                "RecipientNm",
                "RecipientBusinessName",
                "RecipientPersonNm",
                "OrganizationName"
            ]
            
            for pattern in name_patterns:
                name_elem = grant_element.find(f".//{pattern}")
                if name_elem is not None and name_elem.text:
                    recipient_name = name_elem.text.strip()
                    break
            
            if not recipient_name:
                return None
            
            # Extract grant amount
            grant_amount = None
            amount_patterns = [
                "Amount", 
                "Amt",
                "CashGrantAmt",
                "TotalAmt"
            ]
            
            for pattern in amount_patterns:
                amount_elem = grant_element.find(f".//{pattern}")
                if amount_elem is not None and amount_elem.text:
                    try:
                        grant_amount = float(amount_elem.text)
                        break
                    except ValueError:
                        continue
            
            if grant_amount is None:
                return None
            
            # Extract recipient EIN if available
            recipient_ein = None
            ein_patterns = ["RecipientEIN", "EIN", "RecipientTIN"]
            for pattern in ein_patterns:
                ein_elem = grant_element.find(f".//{pattern}")
                if ein_elem is not None and ein_elem.text:
                    recipient_ein = ein_elem.text.strip()
                    break
            
            # Extract grant purpose if available
            grant_purpose = None
            purpose_patterns = [
                "PurposeOfGrant", 
                "Purpose",
                "GrantPurpose",
                "Description"
            ]
            
            for pattern in purpose_patterns:
                purpose_elem = grant_element.find(f".//{pattern}")
                if purpose_elem is not None and purpose_elem.text:
                    grant_purpose = purpose_elem.text.strip()
                    break
            
            return ScheduleIGrantee(
                recipient_name=recipient_name,
                recipient_ein=recipient_ein,
                grant_amount=grant_amount,
                grant_year=tax_year or 2023,  # Default to recent year if unknown
                grant_purpose=grant_purpose
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing grant element: {e}")
            return None
    
    def _parse_recipient_element(self, recipient_element: ET.Element, tax_year: Optional[int]) -> Optional[ScheduleIGrantee]:
        """Parse recipient table element for grantee information"""
        # Use same logic as grant element parsing
        return self._parse_grant_element(recipient_element, tax_year)


def extract_schedule_i_grantees(xml_content: bytes, tax_year: Optional[int] = None) -> List[ScheduleIGrantee]:
    """
    Convenience function to extract Schedule I grantees from XML content.
    
    Args:
        xml_content: Raw XML content from 990 filing
        tax_year: Tax year of the filing (if known)
        
    Returns:
        List of ScheduleIGrantee objects
    """
    extractor = ScheduleIExtractor()
    return extractor.extract_grantees_from_xml(xml_content, tax_year)
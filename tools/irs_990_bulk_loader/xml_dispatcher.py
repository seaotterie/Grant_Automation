"""
Self-contained IRS 990 XML parser for the bulk loader.

Handles 990, 990-PF, and 990-EZ forms without importing any other tools/
module. All XML paths are derived from the existing parser tools.

Returns a normalized dict ready for db_writer.py.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_xml_bytes(xml_bytes: bytes) -> Optional[dict]:
    """
    Parse a 990 XML blob and return a normalised dict:

    {
      "ein":        str,
      "tax_year":   int,
      "form_type":  str,   # "990" | "990-PF" | "990-EZ"
      "officers": [
          {"normalized_name": str, "raw_name": str,
           "title": str|None, "compensation": float|None}
      ],
      "grants": [
          {"recipient_name": str, "recipient_ein": str|None,
           "recipient_city": str|None, "recipient_state": str|None,
           "grant_amount": float, "grant_purpose": str|None,
           "assistance_type": str|None}
      ],
      "financials": {
          "total_assets": float|None, "assets_fmv": float|None,
          "grants_paid_total": float|None, "total_revenue": float|None,
          "distributable_amount": float|None,
          "qualifying_distributions": float|None,
      },
      "narrative": {
          "mission_statement": str|None,
          "accepts_applications": str|None,   # 'yes'|'no'|'invitation_only'|'unknown'
          "geographic_limitations": str|None,
      },
      "is_operating_foundation": bool,
    }

    Returns None if the XML cannot be parsed or form type is unknown.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        logger.debug(f"XML parse error: {e}")
        return None

    # Build namespace prefix used throughout this document
    ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    pfx = f"{{{ns}}}" if ns else ""

    form_type = _detect_form_type(root, pfx)
    if not form_type:
        return None

    ein      = _extract_ein(root, pfx)
    tax_year = _extract_tax_year(root, pfx)

    result: dict = {
        "ein":        ein,
        "tax_year":   tax_year,
        "form_type":  form_type,
        "officers":   [],
        "grants":     [],
        "financials": _empty_financials(),
        "narrative":  _empty_narrative(),
        "is_operating_foundation": False,
        "website_url": None,
    }

    if form_type == "990":
        _parse_990(root, pfx, result)
    elif form_type == "990-PF":
        _parse_990pf(root, pfx, result)
    elif form_type == "990-EZ":
        _parse_990ez(root, pfx, result)

    return result


# ---------------------------------------------------------------------------
# Form type detection
# ---------------------------------------------------------------------------

def _detect_form_type(root: ET.Element, pfx: str) -> Optional[str]:
    """Return '990', '990-PF', '990-EZ', or None."""
    # Check for dedicated form elements (most reliable)
    for tag, form in (
        ("IRS990PF", "990-PF"),
        ("IRS990EZ", "990-EZ"),
        ("IRS990",   "990"),
    ):
        if root.find(f".//{pfx}{tag}") is not None:
            return form
        if root.find(f".//{tag}") is not None:
            return form

    # Fallback: ReturnTypeCd in header
    for path in (f".//{pfx}ReturnTypeCd", ".//ReturnTypeCd"):
        val = (root.findtext(path) or "").strip().upper()
        if val == "990PF":
            return "990-PF"
        if val == "990EZ":
            return "990-EZ"
        if val == "990":
            return "990"

    # Last resort: scan all element tags
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "IRS990PF":
            return "990-PF"
        if tag == "IRS990EZ":
            return "990-EZ"
        if tag == "IRS990":
            return "990"

    return None


# ---------------------------------------------------------------------------
# Shared header extraction
# ---------------------------------------------------------------------------

def _extract_ein(root: ET.Element, pfx: str) -> str:
    for path in (f".//{pfx}EIN", ".//EIN"):
        val = (root.findtext(path) or "").strip().replace("-", "")
        if val:
            return val
    return ""


def _extract_tax_year(root: ET.Element, pfx: str) -> int:
    # Try TaxPeriodEndDt / TaxPeriodEndDate first (YYYY-MM-DD → take year)
    for tag in ("TaxPeriodEndDt", "TaxPeriodEndDate"):
        for path in (f".//{pfx}{tag}", f".//{tag}"):
            val = (root.findtext(path) or "").strip()
            if val and len(val) >= 4:
                try:
                    return int(val[:4])
                except ValueError:
                    pass

    # TaxYear element
    for path in (f".//{pfx}TaxYear", ".//TaxYear"):
        val = (root.findtext(path) or "").strip()
        if val:
            try:
                return int(val)
            except ValueError:
                pass

    # TaxPeriodBeginDate — take year (covers edge cases)
    for tag in ("TaxPeriodBeginDt", "TaxPeriodBeginDate"):
        for path in (f".//{pfx}{tag}", f".//{tag}"):
            val = (root.findtext(path) or "").strip()
            if val and len(val) >= 4:
                try:
                    return int(val[:4])
                except ValueError:
                    pass

    return 0


# ---------------------------------------------------------------------------
# Form 990 (regular nonprofits)
# ---------------------------------------------------------------------------

def _parse_990(root: ET.Element, pfx: str, result: dict) -> None:
    # Officers — Part VII Section A
    for grp in _iter(root, pfx, "Form990PartVIISectionAGrp"):
        name = _txt(grp, pfx, "PersonNm")
        if not name:
            continue
        result["officers"].append({
            "normalized_name": _normalize(name),
            "raw_name":        name.strip(),
            "title":           _txt(grp, pfx, "TitleTxt") or None,
            "compensation":    _flt(grp, pfx, "ReportableCompFromOrgAmt"),
        })

    # Grants — Schedule I: RecipientTable rows
    for grp in _iter(root, pfx, "RecipientTable"):
        name = _txt(grp, pfx, "BusinessNameLine1Txt", "RecipientPersonNm")
        if not name:
            continue
        addr = grp.find(f".//{pfx}RecipientUSAddress") or grp.find(".//RecipientUSAddress")
        city, state = None, None
        if addr is not None:
            city  = _txt(addr, pfx, "CityNm")
            state = _txt(addr, pfx, "StateAbbreviationCd")
        result["grants"].append({
            "recipient_name":  name.strip(),
            "recipient_ein":   _clean_ein(_txt(grp, pfx, "RecipientEIN")),
            "recipient_city":  city,
            "recipient_state": state,
            "grant_amount":    _flt(grp, pfx, "CashGrantAmt") or 0.0,
            "grant_purpose":   _txt(grp, pfx, "PurposeOfGrantTxt") or None,
            "assistance_type": _txt(grp, pfx, "AssistanceTypeCd") or None,
        })

    # Also catch older GrantOrContribution format
    for grp in _iter(root, pfx, "GrantOrContribution"):
        name = _txt(grp, pfx, "BusinessNameLine1Txt", "RecipientPersonNm")
        if not name:
            continue
        result["grants"].append({
            "recipient_name":  name.strip(),
            "recipient_ein":   _clean_ein(_txt(grp, pfx, "RecipientEIN")),
            "recipient_city":  None,
            "recipient_state": None,
            "grant_amount":    _flt(grp, pfx, "Amount", "CashGrant") or 0.0,
            "grant_purpose":   _txt(grp, pfx, "PurposeOfGrantTxt", "PurposeTxt") or None,
            "assistance_type": None,
        })

    # Financials — from IRS990 element
    irs990 = root.find(f".//{pfx}IRS990") or root.find(".//IRS990")
    if irs990 is not None:
        result["financials"]["total_revenue"]           = _flt(irs990, pfx, "CYTotalRevenueAmt")
        result["financials"]["total_assets"]            = _flt(irs990, pfx, "TotalAssetsEOYAmt")
        result["financials"]["total_expenses"]          = _flt(irs990, pfx, "CYTotalFunctionalExpensesAmt")
        result["financials"]["program_expenses"]        = _flt(irs990, pfx, "CYProgramServiceExpensesAmt")
        result["financials"]["admin_expenses"]          = _flt(irs990, pfx, "CYManagementAndGeneralExpensesAmt")
        result["financials"]["fundraising_expenses"]    = _flt(irs990, pfx, "CYFundraisingExpensesAmt")
        result["financials"]["total_liabilities"]       = _flt(irs990, pfx, "TotalLiabilitiesEOYAmt")
        result["financials"]["net_assets"]              = _flt(irs990, pfx, "TotalNetAssetsOrFundBalancesEOYAmt")
        result["financials"]["contributions_grants"]    = _flt(irs990, pfx, "CYContributionsGrantsAmt")
        result["financials"]["program_service_revenue"] = _flt(irs990, pfx, "CYProgramServiceRevenueAmt")
        result["financials"]["investment_income"]       = _flt(irs990, pfx, "CYInvestmentIncomeAmt")
        result["financials"]["other_revenue"]           = _flt(irs990, pfx, "CYOtherRevenueAmt")
        result["financials"]["employee_count"]          = _int(irs990, pfx, "TotalEmployeeCnt")

    # Website URL and mission statement
    result["website_url"] = _normalize_url(_txt(root, pfx, "WebsiteAddressTxt")) or None
    result["narrative"]["mission_statement"] = (
        _txt(root, pfx, "ActivityOrMissionDesc")
        or _txt(root, pfx, "MissionDesc")
        or None
    )


# ---------------------------------------------------------------------------
# Form 990-PF (private foundations)
# ---------------------------------------------------------------------------

def _parse_990pf(root: ET.Element, pfx: str, result: dict) -> None:
    irs990pf = root.find(f".//{pfx}IRS990PF") or root.find(".//IRS990PF")

    # Officers — Part VIII: OfficerDirTrstKeyEmplGrp
    for grp in _iter(root, pfx, "OfficerDirTrstKeyEmplGrp"):
        name = _txt(grp, pfx, "PersonNm")
        if not name:
            continue
        result["officers"].append({
            "normalized_name": _normalize(name),
            "raw_name":        name.strip(),
            "title":           _txt(grp, pfx, "TitleTxt") or None,
            "compensation":    _flt(grp, pfx, "CompensationAmt"),
        })

    # Grants — Part XV: multiple possible group names
    grant_group_tags = (
        "GrantOrContributionPdDurYrGrp",
        "GrantOrContributionPdGrp",
        "GrantOrContribution",
    )
    for tag in grant_group_tags:
        for grp in _iter(root, pfx, tag):
            name = (
                _txt(grp, pfx, "RecipientBusinessName", "BusinessNameLine1Txt")
                or _txt(grp, pfx, "RecipientPersonNm")
            )
            if not name:
                continue
            amount = (
                _flt(grp, pfx, "Amt")
                or _flt(grp, pfx, "Amount")
                or _flt(grp, pfx, "GrantOrContributionAmt")
                or 0.0
            )
            result["grants"].append({
                "recipient_name":  name.strip(),
                "recipient_ein":   _clean_ein(_txt(grp, pfx, "RecipientEIN")),
                "recipient_city":  None,
                "recipient_state": None,
                "grant_amount":    amount,
                "grant_purpose":   _txt(grp, pfx, "GrantOrContributionPurposeTxt", "PurposeTxt") or None,
                "assistance_type": None,
            })

    # Financials (all from IRS990PF element)
    if irs990pf is not None:
        result["financials"]["total_revenue"]             = _flt(irs990pf, pfx, "TotalRevenueAmt")
        result["financials"]["total_assets"]              = _flt(irs990pf, pfx, "TotalAssetsAmt")
        result["financials"]["grants_paid_total"]         = _flt(irs990pf, pfx, "QualifyingDistributionsAmt")
        result["financials"]["distributable_amount"]      = _flt(irs990pf, pfx, "DistributableAmountAmt")
        result["financials"]["qualifying_distributions"]  = _flt(irs990pf, pfx, "QualifyingDistributionsAmt")

        # Fair market value of assets (used for capacity tier)
        result["financials"]["assets_fmv"] = (
            _flt(irs990pf, pfx, "FMVAssetsEndOfYearAmt")
            or _flt(irs990pf, pfx, "TotalAssetsAmt")
        )

        # Governance / narrative
        result["is_operating_foundation"] = _bool(irs990pf, pfx, "OperatingFoundationInd")

        accepts_flag = _txt(irs990pf, pfx, "AcceptsApplicationsInd")
        procedures   = _txt(irs990pf, pfx, "GrantMakingProceduresTxt") or ""
        result["narrative"]["accepts_applications"] = _infer_accepts(accepts_flag, procedures)

        result["narrative"]["geographic_limitations"] = (
            _txt(irs990pf, pfx, "GeographicLimitationsTxt")
            or _txt(irs990pf, pfx, "DistributionLimitationsTxt")
        )

        result["narrative"]["mission_statement"] = (
            _txt(irs990pf, pfx, "MissionDescriptionTxt")
            or _txt(irs990pf, pfx, "ActivityOrMissionDesc")
            or _txt(irs990pf, pfx, "PurposeOfGrantOrContributionTxt")
        )

    # Website URL (searched outside irs990pf scope to catch ReturnHeader location)
    result["website_url"] = _normalize_url(_txt(root, pfx, "WebsiteAddressTxt")) or None


# ---------------------------------------------------------------------------
# Form 990-EZ (small nonprofits)
# ---------------------------------------------------------------------------

def _parse_990ez(root: ET.Element, pfx: str, result: dict) -> None:
    # Officers — Part V: two possible group names
    officers_found = False
    for tag in ("Form990EZPartVOfcrDirTrstKeyEmplGrp", "OfficerDirectorTrusteeGrp"):
        for grp in _iter(root, pfx, tag):
            name = _txt(grp, pfx, "PersonNm") or _txt(grp, pfx, "PersonFullNm")
            if not name:
                continue
            result["officers"].append({
                "normalized_name": _normalize(name),
                "raw_name":        name.strip(),
                "title":           _txt(grp, pfx, "TitleTxt") or None,
                "compensation":    _flt(grp, pfx, "CompensationAmt"),
            })
            officers_found = True

    # Financials
    result["financials"]["total_revenue"]        = _first_flt(root, pfx, "TotalRevenueAmt")
    result["financials"]["total_assets"]         = _first_flt(root, pfx, "TotalAssetsEOYAmt")
    result["financials"]["total_expenses"]       = _first_flt(root, pfx, "TotalExpensesAmt")
    result["financials"]["net_assets"]           = _first_flt(root, pfx, "NetAssetsOrFundBalancesEOYAmt")
    result["financials"]["contributions_grants"] = _first_flt(root, pfx, "TotalContributionsAmt")

    # Website URL and mission statement
    result["website_url"] = _normalize_url(_txt(root, pfx, "WebsiteAddressTxt")) or None
    result["narrative"]["mission_statement"] = _txt(root, pfx, "ActivityOrMissionDesc") or None


# ---------------------------------------------------------------------------
# XML helper utilities
# ---------------------------------------------------------------------------

def _iter(parent: ET.Element, pfx: str, tag: str):
    """Iterate elements by tag, trying namespaced then non-namespaced."""
    found = list(parent.iter(f"{pfx}{tag}")) if pfx else []
    if not found:
        found = list(parent.iter(tag))
    return found


def _txt(parent: ET.Element, pfx: str, *tags: str) -> str:
    """
    Return text of the first matching tag (tried in order), searching anywhere
    in the subtree. Each tag is a simple element name, not a path.
    """
    for tag in tags:
        val = parent.findtext(f".//{pfx}{tag}") or parent.findtext(f".//{tag}") or ""
        val = val.strip()
        if val:
            return val
    return ""


def _flt(parent: ET.Element, pfx: str, *tags: str) -> Optional[float]:
    """Return float value of first matching tag."""
    for tag in tags:
        val = parent.findtext(f".//{pfx}{tag}") or parent.findtext(f".//{tag}") or ""
        val = val.strip()
        if val:
            try:
                return float(val)
            except ValueError:
                pass
    return None


def _first_flt(root: ET.Element, pfx: str, tag: str) -> Optional[float]:
    """Find the first element with this tag anywhere in the document."""
    elem = root.find(f".//{pfx}{tag}") or root.find(f".//{tag}")
    if elem is not None and elem.text:
        try:
            return float(elem.text.strip())
        except ValueError:
            pass
    return None


def _bool(parent: ET.Element, pfx: str, tag: str) -> bool:
    val = (parent.findtext(f".//{pfx}{tag}") or parent.findtext(f".//{tag}") or "").strip().lower()
    return val in ("1", "true", "x", "yes")


def _normalize(name: str) -> str:
    """Lowercase-normalised name matching board_network_index PK convention."""
    import re
    # Strip punctuation runs, collapse whitespace, lowercase
    cleaned = re.sub(r"[^\w\s]", " ", name)
    return " ".join(cleaned.lower().split())


def _clean_ein(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    cleaned = str(val).strip().replace("-", "")
    return cleaned if cleaned.isdigit() and len(cleaned) == 9 else None


def _infer_accepts(accepts_flag: Optional[str], procedures_text: str) -> str:
    if accepts_flag is not None:
        flag = accepts_flag.strip().lower()
        if flag in ("1", "true", "x", "yes"):
            return "yes"
        if flag in ("0", "false", "no"):
            return "no"

    text = (procedures_text or "").lower()
    if any(kw in text for kw in ("invitation only", "by invitation", "unsolicited not")):
        return "invitation_only"
    if any(kw in text for kw in ("accept application", "accept unsolicited", "letter of inquiry")):
        return "yes"
    if any(kw in text for kw in ("does not accept", "not accept", "no unsolicited")):
        return "no"
    return "unknown"


def _normalize_url(url: str) -> Optional[str]:
    """Normalize a raw URL string from 990 XML to a usable https:// URL."""
    if not url:
        return None
    import re
    # Collapse whitespace first (catches "https: //..." or "http: www...")
    url = re.sub(r"\s+", "", url).lower()
    invalid = {"none", "n/a", "na", "null", "unknown", "www", "http://", "https://", ""}
    if url in invalid or "." not in url:
        return None
    # Strip malformed double-protocol (e.g. "https://https://...")
    url = re.sub(r"^(https?://)+(https?://)", r"\2", url)
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def _int(parent: ET.Element, pfx: str, *tags: str) -> Optional[int]:
    """Return int value of first matching tag."""
    for tag in tags:
        val = parent.findtext(f".//{pfx}{tag}") or parent.findtext(f".//{tag}") or ""
        val = val.strip()
        if val:
            try:
                return int(float(val))
            except ValueError:
                pass
    return None


def _empty_financials() -> dict:
    return {
        # All form types
        "total_revenue":            None,
        "total_expenses":           None,
        "total_assets":             None,
        "net_assets":               None,
        "total_liabilities":        None,
        # Revenue breakdown (990, 990-EZ)
        "contributions_grants":     None,
        "program_service_revenue":  None,
        "investment_income":        None,
        "other_revenue":            None,
        # Expense breakdown (990)
        "program_expenses":         None,
        "admin_expenses":           None,
        "fundraising_expenses":     None,
        # 990-PF specific
        "assets_fmv":               None,
        "grants_paid_total":        None,
        "distributable_amount":     None,
        "qualifying_distributions": None,
        # Workforce
        "employee_count":           None,
    }


def _empty_narrative() -> dict:
    return {
        "mission_statement":      None,
        "accepts_applications":   None,
        "geographic_limitations": None,
    }

"""
Unit tests for XML 990 Parser Tool — pure XML parsing logic (no network).
"""

import xml.etree.ElementTree as ET
import pytest
from app.xml_990_parser import XML990ParserTool


# ---------------------------------------------------------------------------
# Helpers — build minimal valid 990 XML strings
# ---------------------------------------------------------------------------

def _make_990_xml(form_tag: str = "IRS990", tax_year: str = "2023") -> ET.Element:
    """Return an in-memory XML tree with the given form element."""
    xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<Return>
  <ReturnHeader>
    <TaxYear>{tax_year}</TaxYear>
    <TaxPeriodBeginDate>{tax_year}-01-01</TaxPeriodBeginDate>
    <Filer>
      <EIN>123456789</EIN>
    </Filer>
  </ReturnHeader>
  <ReturnData>
    <{form_tag}/>
  </ReturnData>
</Return>"""
    return ET.fromstring(xml_str)


def _make_990_with_officers() -> ET.Element:
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<Return>
  <ReturnHeader>
    <TaxYear>2023</TaxYear>
    <Filer><EIN>123456789</EIN></Filer>
  </ReturnHeader>
  <ReturnData>
    <IRS990>
      <Form990PartVIISectionAGrp>
        <PersonNm>Jane Smith</PersonNm>
        <TitleTxt>Executive Director</TitleTxt>
        <AverageHoursPerWeekRt>40.00</AverageHoursPerWeekRt>
        <ReportableCompFromOrgAmt>95000</ReportableCompFromOrgAmt>
        <OfficerInd>true</OfficerInd>
      </Form990PartVIISectionAGrp>
      <Form990PartVIISectionAGrp>
        <PersonNm>Bob Jones</PersonNm>
        <TitleTxt>Board Chair</TitleTxt>
        <AverageHoursPerWeekRt>2.00</AverageHoursPerWeekRt>
        <ReportableCompFromOrgAmt>0</ReportableCompFromOrgAmt>
        <DirectorTrusteeInd>true</DirectorTrusteeInd>
      </Form990PartVIISectionAGrp>
    </IRS990>
  </ReturnData>
</Return>"""
    return ET.fromstring(xml_str)


# ---------------------------------------------------------------------------
# Form type detection tests
# ---------------------------------------------------------------------------

def test_detect_form_990():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990")
    assert parser._extract_form_type(root) == "990"


def test_detect_form_990pf():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990PF")
    assert parser._extract_form_type(root) == "990-PF"


def test_detect_form_990ez():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990EZ")
    assert parser._extract_form_type(root) == "990-EZ"


def test_unknown_form_type():
    parser = XML990ParserTool()
    root = ET.fromstring("<Return><ReturnData/></Return>")
    assert parser._extract_form_type(root) == "Unknown"


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

def test_validate_990_accepts_990():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990")
    assert parser._validate_990_schema(root, validate=True) is True


def test_validate_990_rejects_990pf():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990PF")
    assert parser._validate_990_schema(root, validate=True) is False


def test_validate_990_rejects_990ez():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990EZ")
    assert parser._validate_990_schema(root, validate=True) is False


def test_validate_990_disabled_passes_all():
    """When validate=False, any form type should pass."""
    parser = XML990ParserTool()
    for form_tag in ("IRS990PF", "IRS990EZ"):
        root = _make_990_xml(form_tag)
        assert parser._validate_990_schema(root, validate=False) is True


# ---------------------------------------------------------------------------
# Tax year extraction tests
# ---------------------------------------------------------------------------

def test_extract_tax_year():
    parser = XML990ParserTool()
    root = _make_990_xml(tax_year="2022")
    assert parser._extract_tax_year(root) == 2022


def test_extract_tax_year_default_on_missing():
    parser = XML990ParserTool()
    root = ET.fromstring("<Return/>")
    # Should return the default year, not crash
    year = parser._extract_tax_year(root)
    assert isinstance(year, int)
    assert year > 2000


# ---------------------------------------------------------------------------
# Officer extraction tests
# ---------------------------------------------------------------------------

def test_extract_officers():
    parser = XML990ParserTool()
    root = _make_990_with_officers()
    officers = parser._extract_990_officers(root, ein="123456789", tax_year=2023)

    assert len(officers) == 2
    names = {o.person_name for o in officers}
    assert "Jane Smith" in names
    assert "Bob Jones" in names


def test_extract_officers_empty_990():
    parser = XML990ParserTool()
    root = _make_990_xml("IRS990")
    officers = parser._extract_990_officers(root, ein="123456789", tax_year=2023)
    assert isinstance(officers, list)
    assert len(officers) == 0


# ---------------------------------------------------------------------------
# Object ID extraction tests
# ---------------------------------------------------------------------------

def test_extract_object_id_from_filename():
    parser = XML990ParserTool()
    from pathlib import Path
    path = Path("/data/irs/202312340000_public.xml")
    obj_id = parser._extract_object_id_from_filename(path)
    # Should return the stem or something non-empty
    assert obj_id


# ---------------------------------------------------------------------------
# Namespace handling tests
# ---------------------------------------------------------------------------

def test_form_type_with_namespace():
    xml_str = """<Return xmlns="http://www.irs.gov/efile">
      <ReturnData>
        <IRS990/>
      </ReturnData>
    </Return>"""
    parser = XML990ParserTool()
    root = ET.fromstring(xml_str)
    form_type = parser._extract_form_type(root)
    assert form_type == "990"

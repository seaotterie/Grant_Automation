"""
Unit tests for XML 990-PF Parser Tool — pure XML parsing logic (no network).
"""

import xml.etree.ElementTree as ET
import pytest
from app.xml_990pf_parser import XML990PFParserTool


def _make_xml(form_tag: str = "IRS990PF", tax_year: str = "2023") -> ET.Element:
    xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<Return>
  <ReturnHeader>
    <TaxYear>{tax_year}</TaxYear>
    <Filer><EIN>987654321</EIN></Filer>
  </ReturnHeader>
  <ReturnData>
    <{form_tag}/>
  </ReturnData>
</Return>"""
    return ET.fromstring(xml_str)


# ---------------------------------------------------------------------------
# Form type detection
# ---------------------------------------------------------------------------

def test_detect_990pf():
    assert XML990PFParserTool()._extract_form_type(_make_xml("IRS990PF")) == "990-PF"


def test_detect_990_not_990pf():
    assert XML990PFParserTool()._extract_form_type(_make_xml("IRS990")) == "990"


def test_detect_990ez_not_990pf():
    assert XML990PFParserTool()._extract_form_type(_make_xml("IRS990EZ")) == "990-EZ"


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_validate_accepts_990pf():
    parser = XML990PFParserTool()
    root = _make_xml("IRS990PF")
    assert parser._validate_990pf_schema(root, validate=True) is True


def test_validate_rejects_990():
    parser = XML990PFParserTool()
    root = _make_xml("IRS990")
    assert parser._validate_990pf_schema(root, validate=True) is False


def test_validate_disabled_passes_all():
    parser = XML990PFParserTool()
    for form_tag in ("IRS990", "IRS990EZ"):
        root = _make_xml(form_tag)
        assert parser._validate_990pf_schema(root, validate=False) is True


# ---------------------------------------------------------------------------
# Tax year extraction
# ---------------------------------------------------------------------------

def test_extract_tax_year():
    parser = XML990PFParserTool()
    assert parser._extract_tax_year(_make_xml(tax_year="2021")) == 2021


def test_extract_tax_year_missing_defaults():
    parser = XML990PFParserTool()
    year = parser._extract_tax_year(ET.fromstring("<Return/>"))
    assert isinstance(year, int) and year > 2000

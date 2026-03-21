"""
Unit tests for XML 990-EZ Parser Tool — pure XML parsing logic (no network).
"""

import xml.etree.ElementTree as ET
import pytest
from app.xml_990ez_parser import XML990EZParserTool


def _make_xml(form_tag: str = "IRS990EZ", tax_year: str = "2023") -> ET.Element:
    xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<Return>
  <ReturnHeader>
    <TaxYear>{tax_year}</TaxYear>
    <Filer><EIN>555555555</EIN></Filer>
  </ReturnHeader>
  <ReturnData>
    <{form_tag}/>
  </ReturnData>
</Return>"""
    return ET.fromstring(xml_str)


# ---------------------------------------------------------------------------
# Form type detection
# ---------------------------------------------------------------------------

def test_detect_990ez():
    assert XML990EZParserTool()._extract_form_type(_make_xml("IRS990EZ")) == "990-EZ"


def test_detect_990_not_990ez():
    assert XML990EZParserTool()._extract_form_type(_make_xml("IRS990")) == "990"


def test_detect_990pf_not_990ez():
    assert XML990EZParserTool()._extract_form_type(_make_xml("IRS990PF")) == "990-PF"


def test_unknown_form_returns_unknown():
    parser = XML990EZParserTool()
    root = ET.fromstring("<Return><ReturnData/></Return>")
    assert parser._extract_form_type(root) == "Unknown"


# ---------------------------------------------------------------------------
# Tax year extraction
# ---------------------------------------------------------------------------

def test_extract_tax_year():
    parser = XML990EZParserTool()
    assert parser._extract_tax_year(_make_xml(tax_year="2020")) == 2020


def test_extract_tax_year_default_on_empty():
    parser = XML990EZParserTool()
    year = parser._extract_tax_year(ET.fromstring("<Return/>"))
    assert isinstance(year, int) and year > 2000


# ---------------------------------------------------------------------------
# Namespace handling
# ---------------------------------------------------------------------------

def test_form_type_with_namespace():
    xml_str = """<Return xmlns="http://www.irs.gov/efile">
      <ReturnData>
        <IRS990EZ/>
      </ReturnData>
    </Return>"""
    parser = XML990EZParserTool()
    root = ET.fromstring(xml_str)
    assert parser._extract_form_type(root) == "990-EZ"

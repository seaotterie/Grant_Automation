"""
Analysis Processors

This package contains processors responsible for analyzing and scoring organizations:
- PDF OCR extraction
- GPT-powered URL discovery
- Other analytical functions

NOTE: Most analysis processors have been migrated to 12-factor tools:
- FinancialScorerProcessor → Financial Intelligence Tool (tools/financial-intelligence-tool/)
- RiskAssessor → Risk Intelligence Tool (tools/risk-intelligence-tool/)
- BoardNetworkAnalyzer → Network Intelligence Tool (tools/network-intelligence-tool/)
- AI processors → Opportunity Screening + Deep Intelligence Tools

See: src/processors/_deprecated/README.md for full migration map
"""

from .pdf_ocr import PDFOCRProcessor

__all__ = [
    "PDFOCRProcessor"
]
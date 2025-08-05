"""
Data Collection Processors

This package contains processors responsible for collecting data from external sources:
- ProPublica Nonprofit Explorer API
- IRS XML and PDF filing downloads
- Other external data sources
"""

from .propublica_fetch import ProPublicaFetchProcessor
from .xml_downloader import XMLDownloaderProcessor
from .pdf_downloader import PDFDownloaderProcessor

__all__ = [
    "ProPublicaFetchProcessor",
    "XMLDownloaderProcessor", 
    "PDFDownloaderProcessor"
]
"""
Data Collection Processors

This package contains processors responsible for collecting data from external sources:
- ProPublica Nonprofit Explorer API
- IRS XML and PDF filing downloads
- Other external data sources
"""

from .propublica_fetch import ProPublicaFetchProcessor
# XMLDownloaderProcessor deprecated - XML tools handle downloads
# from .xml_downloader import XMLDownloaderProcessor
from .pdf_downloader import PDFDownloaderProcessor

__all__ = [
    "ProPublicaFetchProcessor",
    # "XMLDownloaderProcessor",  # Deprecated - XML tools handle downloads
    "PDFDownloaderProcessor"
]
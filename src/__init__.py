"""RAG Crawler - Sistema de crawling e extração de texto para RAG"""
__version__ = '1.0.0'
__author__ = 'Your Name'

from .crawler import WebCrawler
from .pdf_extractor import PDFExtractor
from .scraper import HTMLScraper
from .storage import URLStorage, TextStorage

__all__ = [
    'WebCrawler',
    'HTMLScraper',
    'PDFExtractor',
    'URLStorage',
    'TextStorage'
]

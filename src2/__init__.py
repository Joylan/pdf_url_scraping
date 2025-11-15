"""
RAG Crawler - Sistema de crawling e extração de texto para RAG
"""

__version__ = '1.0.0'
__author__ = 'Your Name'

from src.crawler import WebCrawler
from src.pdf_extractor import PDFExtractor
from src.scraper import HTMLScraper
from src.storage import URLStorage, TextStorage

__all__ = [
    'WebCrawler',
    'HTMLScraper',
    'PDFExtractor',
    'URLStorage',
    'TextStorage'
]

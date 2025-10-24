"""Módulo de scraping de conteúdo HTML"""
import logging
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

from config.settings import HEADERS, TIMEOUT
from src.utils import clean_text

logger = logging.getLogger(__name__)


class HTMLScraper:
    """Extrai conteúdo textual de páginas HTML"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, url: str) -> Optional[Tuple[str, str]]:
        """Busca o conteúdo de uma página"""
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()

            return response.content, content_type

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar {url}: {str(e)}")
            return None

    def extract_text(self, html_content: bytes, url: str) -> str:
        """Extrai texto útil de conteúdo HTML"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            for element in soup(['script', 'style', 'nav', 'footer',
                                 'header', 'aside', 'noscript', 'iframe']):
                element.decompose()

            text = soup.get_text(separator='\n')
            text = clean_text(text)

            logger.info(f"Texto extraído de {url}: {len(text)} caracteres")
            return text

        except Exception as e:
            logger.error(f"Erro ao extrair texto de {url}: {str(e)}")
            return ""

    def scrape(self, url: str) -> Optional[str]:
        """Realiza scraping completo de uma URL"""
        result = self.fetch_page(url)

        if not result:
            return None

        content, content_type = result

        if 'text/html' not in content_type:
            logger.warning(f"Conteúdo não é HTML: {url} ({content_type})")
            return None

        return self.extract_text(content, url)

    def close(self):
        """Fecha a sessão"""
        self.session.close()

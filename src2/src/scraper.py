"""Módulo de scraping HTML com logs enxutos para RAG"""

import logging
from typing import Optional, Tuple, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config.settings import HEADERS, TIMEOUT
from .utils import clean_text

logger = logging.getLogger(__name__)


class HTMLScraper:
    """Classe para extrair texto e links de páginas HTML"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, url: str) -> Optional[Tuple[bytes, str]]:
        """Busca o conteúdo HTML de uma URL

        Args:
            url: URL da página a ser buscada

        Returns:
            Tupla (conteúdo_bytes, tipo_conteúdo) ou None se falhar
        """
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()
            return response.content, content_type
        except requests.exceptions.RequestException as e:
            logger.debug(f"Falha ao acessar: {url} - Erro: {str(e)}")
            return None

    def extract_text(self, html_content: bytes, url: str) -> str:
        """Extrai e limpa texto de HTML

        Args:
            html_content: Conteúdo HTML em bytes
            url: URL da página (para logging)

        Returns:
            Texto limpo extraído do HTML
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove elementos indesejados
            for element in soup(['script', 'style', 'nav', 'footer', 'header',
                                 'aside', 'noscript', 'iframe']):
                element.decompose()

            text = clean_text(soup.get_text(separator='\n'))
            return text
        except Exception as e:
            logger.debug(f"Erro ao extrair texto: {url} - {str(e)}")
            return ""

    def extract_links(self, html_content: bytes, base_url: str) -> Set[str]:
        """Extrai links válidos do HTML

        Args:
            html_content: Conteúdo HTML em bytes
            base_url: URL base para resolver links relativos

        Returns:
            Conjunto de URLs absolutas encontradas
        """
        links = set()
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                # Converter para URL absoluta
                absolute_url = urljoin(base_url, href)
                # Remover fragmentos (#)
                absolute_url = absolute_url.split('#')[0]
                if absolute_url:
                    links.add(absolute_url)
            return links
        except Exception as e:
            logger.debug(f"Erro ao extrair links: {base_url} - {str(e)}")
            return set()

    def scrape_with_links(self, url: str) -> Optional[Tuple[str, Set[str]]]:
        """Busca HTML, extrai texto e links

        Args:
            url: URL da página a ser processada

        Returns:
            Tupla (texto, conjunto_de_links) ou None se falhar
        """
        result = self.fetch_page(url)
        if not result:
            return None

        content, content_type = result
        if 'text/html' not in content_type:
            logger.debug(f"Conteúdo não-HTML ignorado: {url} (tipo: {content_type})")
            return None

        text = self.extract_text(content, url)
        links = self.extract_links(content, url)
        return text, links

    def close(self):
        """Fecha a sessão HTTP"""
        self.session.close()

"""Módulo de crawling de páginas web"""
import logging
import time
from collections import deque
from typing import Set

from config.settings import (
    DELAY_BETWEEN_REQUESTS, MAX_DEPTH, MAX_PAGES,
    IGNORED_EXTENSIONS
)
from src.pdf_extractor import PDFExtractor
from src.scraper import HTMLScraper
from src.storage import URLStorage, TextStorage
from src.utils import (
    normalize_url, is_same_domain, is_valid_url,
    extract_links_from_text
)

logger = logging.getLogger(__name__)


class WebCrawler:
    """Crawler para extrair conteúdo de sites"""

    def __init__(self, url_storage: URLStorage, text_storage: TextStorage,
                 max_depth: int = MAX_DEPTH, max_pages: int = MAX_PAGES):
        self.url_storage = url_storage
        self.text_storage = text_storage
        self.max_depth = max_depth
        self.max_pages = max_pages

        self.scraper = HTMLScraper()
        self.pdf_extractor = PDFExtractor()

        self.visited_urls: Set[str] = set()
        self.pages_processed = 0

    def crawl(self, start_url: str):
        """Inicia o crawling a partir de uma URL"""
        start_url = normalize_url(start_url)
        from urllib.parse import urlparse
        parsed = urlparse(start_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        base_path = parsed.path.rstrip('/')

        logger.info(f"Iniciando crawling de: {start_url}")
        logger.info(f"Profundidade máxima: {self.max_depth}")
        logger.info(f"Páginas máximas: {self.max_pages}")

        self.visited_urls = set(self.url_storage.get_all_processed_urls())
        logger.info(f"URLs já processadas: {len(self.visited_urls)}")

        queue = deque([(start_url, 0)])

        while queue and self.pages_processed < self.max_pages:
            url, depth = queue.popleft()

            if url in self.visited_urls:
                continue

            if depth > self.max_depth:
                continue

            self.visited_urls.add(url)

            success, new_links = self._process_url(url, base_domain, base_path)

            if success:
                self.pages_processed += 1
                logger.info(f"Progresso: {self.pages_processed}/{self.max_pages} páginas")

            if depth < self.max_depth and new_links:
                for link in new_links:
                    if link not in self.visited_urls:
                        queue.append((link, depth + 1))

            time.sleep(DELAY_BETWEEN_REQUESTS)

        logger.info(f"Crawling finalizado. Total processado: {self.pages_processed} páginas")
        self._print_summary()

    def _process_url(self, url: str, base_domain: str, base_path: str) -> tuple:
        """Processa uma URL específica"""
        logger.info(f"Processando: {url}")

        if not url.startswith(f"{base_domain}{base_path}"):
            logger.debug(f"Ignorando URL fora do escopo: {url}")
            return False, set()

        if not is_valid_url(url, IGNORED_EXTENSIONS):
            logger.debug(f"URL inválida ou ignorada: {url}")
            return False, set()

        if url.lower().endswith('.pdf'):
            return self._process_pdf(url), set()
        else:
            return self._process_html(url, base_domain, base_path)

    def _process_html(self, url: str, base_domain: str, base_path: str) -> tuple:
        """Processa uma página HTML"""
        try:
            result = self.scraper.fetch_page(url)
            if not result:
                self.url_storage.mark_as_processed(url, 'failed', 'html', 'Fetch failed')
                return False, set()

            content, content_type = result

            if 'application/pdf' in content_type:
                return self._process_pdf(url), set()

            if 'text/html' not in content_type:
                self.url_storage.mark_as_processed(url, 'skipped', 'other',
                                                   f'Content-Type: {content_type}')
                return False, set()

            text = self.scraper.extract_text(content, url)

            if text:
                self.text_storage.append_text(url, text, 'html')
                self.url_storage.mark_as_processed(url, 'success', 'html')

                links = extract_links_from_text(content, url)
                valid_links = {
                    link for link in links
                    if link.startswith(f"{base_domain}{base_path}") and
                       is_valid_url(link, IGNORED_EXTENSIONS)
                }

                logger.debug(f"Links encontrados: {len(valid_links)}")
                return True, valid_links
            else:
                self.url_storage.mark_as_processed(url, 'failed', 'html',
                                                   'No text extracted')
                return False, set()

        except Exception as e:
            logger.error(f"Erro ao processar HTML {url}: {str(e)}")
            self.url_storage.mark_as_processed(url, 'failed', 'html', str(e))
            return False, set()

    def _process_pdf(self, url: str) -> bool:
        """Processa um arquivo PDF"""
        try:
            text = self.pdf_extractor.extract(url)

            if text:
                self.text_storage.append_text(url, text, 'pdf')
                self.url_storage.mark_as_processed(url, 'success', 'pdf')
                return True
            else:
                self.url_storage.mark_as_processed(url, 'failed', 'pdf',
                                                   'No text extracted')
                return False

        except Exception as e:
            logger.error(f"Erro ao processar PDF {url}: {str(e)}")
            self.url_storage.mark_as_processed(url, 'failed', 'pdf', str(e))
            return False

    def _print_summary(self):
        """Imprime resumo do crawling"""
        from src.utils import format_file_size

        total_urls = self.url_storage.get_processed_count()
        file_size = self.text_storage.get_file_size()

        print("\n" + "=" * 60)
        print("RESUMO DO CRAWLING")
        print("=" * 60)
        print(f"Total de URLs processadas: {total_urls}")
        print(f"Páginas processadas nesta execução: {self.pages_processed}")
        print(f"Tamanho do arquivo de texto: {format_file_size(file_size)}")
        print("=" * 60 + "\n")

    def close(self):
        """Fecha recursos"""
        self.scraper.close()
        self.pdf_extractor.close()
        self.url_storage.close()

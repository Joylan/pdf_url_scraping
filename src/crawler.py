import logging
import time
from collections import deque
from typing import Set
from urllib.parse import urlparse

from config.settings import (
    DELAY_BETWEEN_REQUESTS, MAX_DEPTH, MAX_PAGES,
    IGNORED_EXTENSIONS
)
from src.pdf_extractor import PDFExtractor
from src.scraper import HTMLScraper
from src.storage import URLStorage, TextStorage
from src.utils import normalize_url, is_same_domain, is_valid_url, format_file_size

logger = logging.getLogger(__name__)


class WebCrawler:
    """Crawler principal com logs simplificados"""

    def __init__(self, url_storage: URLStorage, text_storage: TextStorage,
                 max_depth: int = MAX_DEPTH, max_pages: int = MAX_PAGES):
        self.url_storage = url_storage
        self.text_storage = text_storage
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.html_scraper = HTMLScraper()
        self.pdf_extractor = PDFExtractor()
        self.pages_processed = 0
        self.pdfs_processed = 0

    def crawl(self, start_url: str):
        start_url = normalize_url(start_url)
        parsed_start = urlparse(start_url)
        start_domain = parsed_start.netloc

        queue = deque([(start_url, 0)])
        visited = set()

        # Calcular páginas restantes baseado no total já processado
        total_processed = self.pages_processed + self.pdfs_processed
        remaining_pages = self.max_pages - total_processed

        logger.info(f"🚀 Iniciando crawl: {start_url}")
        logger.info(f"📊 Limite: {remaining_pages} páginas restantes | Profundidade: {self.max_depth}\n")

        while queue and len(visited) < remaining_pages:
            current_url, depth = queue.popleft()
            normalized_url = normalize_url(current_url)

            if normalized_url in visited or depth > self.max_depth:
                continue

            if self.url_storage.is_processed(normalized_url):
                continue

            # Verificar se está no mesmo domínio
            if not is_same_domain(normalized_url, start_url):
                continue

            success, links = self._process_url(normalized_url, start_domain, depth)

            if success:
                visited.add(normalized_url)

                for link in links:
                    normalized_link = normalize_url(link)
                    if normalized_link not in visited and is_same_domain(normalized_link, start_url):
                        queue.append((normalized_link, depth + 1))

            time.sleep(DELAY_BETWEEN_REQUESTS)

            # Verificar se atingiu o limite global
            total_processed = self.pages_processed + self.pdfs_processed
            if total_processed >= self.max_pages:
                logger.info(f"\n⚠️  Limite de {self.max_pages} páginas atingido")
                break

        self._print_summary()

    def _process_url(self, url: str, start_domain: str, depth: int) -> (bool, Set[str]):
        """Processa uma URL (HTML ou PDF)"""
        if url.lower().endswith('.pdf'):
            return self._process_pdf(url, depth), set()
        else:
            return self._process_html(url, start_domain, depth)

    def _process_html(self, url: str, start_domain: str, depth: int) -> (bool, Set[str]):
        if self.url_storage.is_processed(url):
            return False, set()

        result = self.html_scraper.scrape_with_links(url)
        if result is None:
            self.url_storage.mark_as_processed(url, status='error', content_type='html')
            return False, set()

        text, links = result
        if not text.strip():
            self.url_storage.mark_as_processed(url, status='empty', content_type='html')
            return False, links

        self.text_storage.append_text(url, text, 'html')
        self.url_storage.mark_as_processed(url, status='success', content_type='html')
        self.pages_processed += 1

        # Extrair nome da página para log mais limpo
        path = urlparse(url).path.strip('/')
        page_name = path.split('/')[-1] if path else 'index'

        logger.info(f"✓ [{self.pages_processed:3d}] HTML | D{depth} | {len(text):>6,} chars | /{page_name}")

        # Filtrar links válidos
        valid_links = set()
        for link in links:
            # Aceitar PDFs explicitamente
            if link.lower().endswith('.pdf'):
                valid_links.add(link)
            # Validar outros links normalmente
            elif is_valid_url(link, IGNORED_EXTENSIONS):
                valid_links.add(link)

        return True, valid_links

    def _process_pdf(self, url: str, depth: int) -> bool:
        if self.url_storage.is_processed(url):
            return False

        text = self.pdf_extractor.extract(url)
        if text is None or not text.strip():
            self.url_storage.mark_as_processed(url, status='empty', content_type='pdf')
            return False

        self.text_storage.append_text(url, text, 'pdf')
        self.url_storage.mark_as_processed(url, status='success', content_type='pdf')
        self.pdfs_processed += 1

        # Extrair nome do arquivo PDF
        path = urlparse(url).path
        pdf_name = path.split('/')[-1]

        logger.info(f"✓ [{self.pdfs_processed:3d}] PDF  | D{depth} | {len(text):>6,} chars | {pdf_name}")
        return True

    def _print_summary(self):
        total_urls = self.url_storage.get_processed_count()
        file_size = self.text_storage.get_file_size()

        print()
        logger.info("─" * 70)
        logger.info(
            f"📄 Páginas HTML: {self.pages_processed} | 📑 PDFs: {self.pdfs_processed} | 🔗 Total URLs: {total_urls}")
        logger.info(f"💾 Tamanho: {format_file_size(file_size)}")
        logger.info("─" * 70)

    def close(self):
        self.html_scraper.close()
        self.pdf_extractor.close()
        self.url_storage.close()

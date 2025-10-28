"""Crawler principal com scraping incremental e validação de URL completa"""

import logging
import time
from collections import deque
from typing import Set, Tuple, Optional, Callable
from urllib.parse import urlparse

from config.settings import (
    DELAY_BETWEEN_REQUESTS, MAX_DEPTH, MAX_PAGES,
    IGNORED_EXTENSIONS
)
from src.pdf_extractor import PDFExtractor
from src.scraper import HTMLScraper
from src.storage import URLStorage, TextStorage
from src.utils import normalize_url, is_valid_url, format_file_size

logger = logging.getLogger(__name__)


def url_starts_with_base(url: str, base_url: str) -> bool:
    """Verifica se a URL começa com a URL base completa (incluindo subdomínio e caminho)"""
    url_normalized = normalize_url(url)
    base_normalized = normalize_url(base_url)
    return url_normalized.startswith(base_normalized)


class WebCrawler:
    """Crawler principal com logs simplificados e scraping incremental"""

    def __init__(self, url_storage: URLStorage, text_storage: TextStorage,
                 max_depth: int = MAX_DEPTH, max_pages: int = MAX_PAGES):
        self.url_storage = url_storage
        self.text_storage = text_storage
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.html_scraper = HTMLScraper()
        self.pdf_extractor = PDFExtractor()

        # Contadores incrementais
        self.pages_processed = self._count_processed_by_type('html')
        self.pdfs_processed = self._count_processed_by_type('pdf')

    def _count_processed_by_type(self, content_type: str) -> int:
        """Conta quantas URLs de um tipo específico já foram processadas"""
        try:
            from tinydb import Query
            q = Query()
            count = len(self.url_storage.urls_table.search(
                (q.content_type == content_type) & (q.status == 'success')
            ))
            return count
        except Exception:
            return 0

    # ==========================================================
    # MÉTODO CORRIGIDO COM SUPORTE A 'url_filter'
    # ==========================================================
    def crawl(self, start_url: str, url_filter: Optional[Callable[[str], bool]] = None):
        """Inicia o crawling a partir de uma URL inicial.

        O crawling é incremental e restrito à base da URL informada,
        mas também aceita um filtro de URL personalizado.
        """
        start_url = normalize_url(start_url)
        parsed_start = urlparse(start_url)
        start_domain = parsed_start.netloc

        queue = deque([(start_url, 0)])
        visited = set()

        # Calcular páginas já processadas
        initial_html_count = self.pages_processed
        initial_pdf_count = self.pdfs_processed
        total_processed = initial_html_count + initial_pdf_count
        remaining_pages = self.max_pages - total_processed

        logger.info(f"🚀 Iniciando crawl: {start_url}")
        logger.info(f"📊 Já processadas: {initial_html_count} HTMLs, {initial_pdf_count} PDFs")
        logger.info(f"📊 Limite: {remaining_pages} páginas restantes | Profundidade: {self.max_depth}\n")

        # Processa URL inicial
        if not self.url_storage.is_processed(start_url):
            logger.info(f"📍 Processando URL inicial: {start_url}")
            success, links = self._process_url(start_url, start_url, 0)
            if success:
                visited.add(start_url)
                for link in links:
                    normalized_link = normalize_url(link)
                    if (normalized_link not in visited and
                            url_starts_with_base(normalized_link, start_url) and
                            (url_filter(normalized_link) if url_filter else True)):
                        queue.append((normalized_link, 1))
            if queue and queue[0][0] == start_url:
                queue.popleft()
        else:
            logger.info(f"ℹ️  URL inicial já foi processada anteriormente: {start_url}")
            visited.add(start_url)
            result = self.html_scraper.scrape_with_links(start_url)
            if result:
                _, links = result
                for link in links:
                    normalized_link = normalize_url(link)
                    if (normalized_link not in visited and
                            url_starts_with_base(normalized_link, start_url) and
                            (url_filter(normalized_link) if url_filter else True)):
                        queue.append((normalized_link, 1))

        # Processar a fila
        while queue and len(visited) < remaining_pages:
            current_url, depth = queue.popleft()
            normalized_url = normalize_url(current_url)

            if normalized_url in visited or depth > self.max_depth:
                continue
            if self.url_storage.is_processed(normalized_url):
                visited.add(normalized_url)
                continue
            if not url_starts_with_base(normalized_url, start_url):
                continue
            if url_filter and not url_filter(normalized_url):
                continue

            success, links = self._process_url(normalized_url, start_url, depth)

            if success:
                visited.add(normalized_url)
                for link in links:
                    normalized_link = normalize_url(link)
                    if (normalized_link not in visited and
                            url_starts_with_base(normalized_link, start_url) and
                            (url_filter(normalized_link) if url_filter else True)):
                        queue.append((normalized_link, depth + 1))

            time.sleep(DELAY_BETWEEN_REQUESTS)
            total_processed = self.pages_processed + self.pdfs_processed
            if total_processed >= self.max_pages:
                logger.info(f"\n⚠️  Limite de {self.max_pages} páginas atingido")
                break

        self._print_summary(initial_html_count, initial_pdf_count)

    # ==========================================================
    # MÉTODOS AUXILIARES
    # ==========================================================
    def _process_url(self, url: str, base_url: str, depth: int) -> Tuple[bool, Set[str]]:
        """Processa uma URL (HTML ou PDF)."""
        if url.lower().endswith('.pdf'):
            return self._process_pdf(url, depth), set()
        else:
            return self._process_html(url, base_url, depth)

    def _process_html(self, url: str, base_url: str, depth: int) -> Tuple[bool, Set[str]]:
        """Processa uma página HTML."""
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

        display_url = url if len(url) <= 80 else url[:77] + "..."
        logger.info(f"✓ [{self.pages_processed:3d}] HTML | D{depth} | {len(text):>6,} chars | {display_url}")

        valid_links = set()
        for link in links:
            if link.lower().endswith('.pdf') and url_starts_with_base(link, base_url):
                valid_links.add(link)
            elif (is_valid_url(link, IGNORED_EXTENSIONS) and
                  url_starts_with_base(link, base_url)):
                valid_links.add(link)
        return True, valid_links

    def _process_pdf(self, url: str, depth: int) -> bool:
        """Processa um arquivo PDF."""
        if self.url_storage.is_processed(url):
            return False

        text = self.pdf_extractor.extract(url)
        if text is None or not text.strip():
            self.url_storage.mark_as_processed(url, status='empty', content_type='pdf')
            return False

        self.text_storage.append_text(url, text, 'pdf')
        self.url_storage.mark_as_processed(url, status='success', content_type='pdf')
        self.pdfs_processed += 1

        display_url = url if len(url) <= 80 else url[:77] + "..."
        logger.info(f"✓ [{self.pdfs_processed:3d}] PDF  | D{depth} | {len(text):>6,} chars | {display_url}")
        return True

    def _print_summary(self, initial_html: int, initial_pdf: int):
        """Exibe resumo do crawling."""
        total_urls = self.url_storage.get_processed_count()
        file_size = self.text_storage.get_file_size()
        new_html = self.pages_processed - initial_html
        new_pdf = self.pdfs_processed - initial_pdf

        print()
        logger.info("─" * 70)
        logger.info(f"📄 Neste crawl -> HTML: {new_html} | PDF: {new_pdf}")
        logger.info(
            f"📊 Total acumulado -> HTML: {self.pages_processed} | PDF: {self.pdfs_processed} | URLs: {total_urls}")
        logger.info(f"💾 Tamanho total: {format_file_size(file_size)}")
        logger.info("─" * 70)

    def export_text(self, export_path: str) -> bool:
        """Exporta todo o texto coletado para um arquivo externo em UTF-8."""
        try:
            if not self.text_storage.output_file.exists():
                logger.warning("⚠️  Nenhum texto disponível para exportar.")
                return False

            with open(self.text_storage.output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning("⚠️  Arquivo de texto está vazio.")
                return False

            with open(export_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("RESULTADOS DO CRAWLING / SCRAPING\n")
                f.write(f"Exportado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total de páginas HTML: {self.pages_processed}\n")
                f.write(f"Total de PDFs: {self.pdfs_processed}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)

            file_size = format_file_size(len(content.encode('utf-8')))
            logger.info(f"✅ Texto exportado com sucesso para: {export_path}")
            logger.info(f"📦 Tamanho do arquivo: {file_size}")
            return True
        except Exception as e:
            logger.error(f"❌ Falha ao exportar texto: {e}")
            return False

    def close(self):
        """Fecha todas as conexões e recursos."""
        self.html_scraper.close()
        self.pdf_extractor.close()
        self.url_storage.close()

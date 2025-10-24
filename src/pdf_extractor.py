"""Módulo de extração de texto de PDFs"""
import logging
from pathlib import Path
from typing import Optional

import pdfplumber
import requests

from config.settings import HEADERS, TIMEOUT, PDF_DIR, MAX_PDF_SIZE_MB
from src.utils import clean_text

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extrai texto de arquivos PDF"""

    def __init__(self, pdf_dir: Path = PDF_DIR):
        self.pdf_dir = pdf_dir
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def download_pdf(self, url: str) -> Optional[Path]:
        """Baixa um PDF da URL"""
        try:
            response = self.session.get(url, timeout=TIMEOUT, stream=True,
                                        allow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                logger.warning(f"URL não é um PDF: {url} ({content_type})")
                return None

            content_length = response.headers.get('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > MAX_PDF_SIZE_MB:
                    logger.warning(f"PDF muito grande: {url} ({size_mb:.2f}MB)")
                    return None

            filename = self._generate_filename(url)
            filepath = self.pdf_dir / filename

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"PDF baixado: {filepath}")
            return filepath

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar PDF {url}: {str(e)}")
            return None

    def extract_text_from_file(self, pdf_path: Path) -> str:
        """Extrai texto de um arquivo PDF local"""
        text_parts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Erro ao extrair página {page_num}: {str(e)}")

            full_text = '\n\n'.join(text_parts)
            full_text = clean_text(full_text)

            logger.info(f"Texto extraído do PDF {pdf_path.name}: "
                        f"{len(full_text)} caracteres")
            return full_text

        except Exception as e:
            logger.error(f"Erro ao processar PDF {pdf_path}: {str(e)}")
            return ""

    def extract(self, url: str) -> Optional[str]:
        """Extrai texto de um PDF a partir de URL"""
        pdf_path = self.download_pdf(url)

        if not pdf_path:
            return None

        text = self.extract_text_from_file(pdf_path)

        return text if text else None

    def _generate_filename(self, url: str) -> str:
        """Gera um nome de arquivo único baseado na URL"""
        from urllib.parse import urlparse
        import hashlib

        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        path = urlparse(url).path
        original_name = Path(path).stem

        if original_name and len(original_name) < 50:
            return f"{original_name}_{url_hash}.pdf"
        else:
            return f"document_{url_hash}.pdf"

    def close(self):
        """Fecha a sessão"""
        self.session.close()

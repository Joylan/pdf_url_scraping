"""Módulo simplificado de extração de texto de PDFs"""
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
            response = self.session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()

            if 'application/pdf' not in content_type:
                logger.debug(f"Conteúdo não-PDF ignorado: {url}")
                return None

            size_mb = int(response.headers.get('Content-Length', 0)) / (1024 * 1024)
            if size_mb > MAX_PDF_SIZE_MB:
                logger.debug(f"PDF muito grande ({size_mb:.1f}MB): {url}")
                return None

            filename = self._generate_filename(url)
            filepath = self.pdf_dir / filename

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return filepath
        except requests.exceptions.RequestException:
            logger.debug(f"Falha ao baixar PDF: {url}")
            return None

    def extract_text_from_file(self, pdf_path: Path) -> str:
        """Extrai texto de arquivo PDF"""
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            text = clean_text("\n\n".join(text_parts))
            return text
        except Exception:
            logger.debug(f"Erro ao ler PDF: {pdf_path.name}")
            return ""

    def extract(self, url: str) -> Optional[str]:
        """Extrai texto diretamente de uma URL PDF"""
        pdf_path = self.download_pdf(url)
        if not pdf_path:
            return None
        return self.extract_text_from_file(pdf_path)

    def _generate_filename(self, url: str) -> str:
        from urllib.parse import urlparse
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        path = Path(urlparse(url).path).stem
        base_name = path if path and len(path) < 50 else "document"
        return f"{base_name}_{url_hash}.pdf"

    def close(self):
        self.session.close()

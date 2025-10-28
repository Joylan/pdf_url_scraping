"""Módulo simplificado de extração de texto de PDFs"""
import hashlib
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import pdfplumber
import requests

from config.settings import HEADERS, TIMEOUT, PDF_DIR, MAX_PDF_SIZE_MB
from .utils import clean_text

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extrai texto de arquivos PDF"""

    def __init__(self, pdf_dir: Path = PDF_DIR):
        self.pdf_dir = pdf_dir
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def download_pdf(self, url: str) -> Optional[Path]:
        """Baixa um PDF da URL

        Args:
            url: URL do PDF a ser baixado

        Returns:
            Path do arquivo baixado ou None se falhar
        """
        try:
            response = self.session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()

            if 'application/pdf' not in content_type:
                logger.debug(f"Conteúdo não-PDF ignorado: {url} (tipo: {content_type})")
                return None

            # Verificar tamanho do arquivo
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > MAX_PDF_SIZE_MB:
                    logger.debug(f"PDF muito grande ({size_mb:.1f}MB): {url}")
                    return None

            filename = self._generate_filename(url)
            filepath = self.pdf_dir / filename

            # Salvar PDF
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return filepath
        except requests.exceptions.RequestException as e:
            logger.debug(f"Falha ao baixar PDF: {url} - Erro: {str(e)}")
            return None
        except Exception as e:
            logger.debug(f"Erro inesperado ao baixar PDF: {url} - {str(e)}")
            return None

    def extract_text_from_file(self, pdf_path: Path) -> str:
        """Extrai texto de arquivo PDF

        Args:
            pdf_path: Caminho do arquivo PDF

        Returns:
            Texto extraído do PDF
        """
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            text = clean_text("\n\n".join(text_parts))
            return text
        except Exception as e:
            logger.debug(f"Erro ao ler PDF: {pdf_path.name} - {str(e)}")
            return ""

    def extract(self, url: str) -> Optional[str]:
        """Extrai texto diretamente de uma URL PDF

        Args:
            url: URL do PDF

        Returns:
            Texto extraído ou None se falhar
        """
        pdf_path = self.download_pdf(url)
        if not pdf_path:
            return None

        text = self.extract_text_from_file(pdf_path)
        return text if text else None

    def _generate_filename(self, url: str) -> str:
        """Gera nome de arquivo único para o PDF

        Args:
            url: URL do PDF

        Returns:
            Nome de arquivo único
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        path = Path(urlparse(url).path).stem
        base_name = path if path and len(path) < 50 else "document"
        # Sanitizar nome do arquivo
        base_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_'))
        return f"{base_name}_{url_hash}.pdf"

    def close(self):
        """Fecha a sessão HTTP"""
        self.session.close()

"""Módulo de persistência para rastrear URLs processadas"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from tinydb import TinyDB, Query

logger = logging.getLogger(__name__)


class URLStorage:
    """Gerencia o armazenamento e rastreamento de URLs processadas"""

    def __init__(self, db_path: Path):
        self.db = TinyDB(db_path)
        self.urls_table = self.db.table('urls')

    def is_processed(self, url: str) -> bool:
        """Verifica se uma URL já foi processada"""
        URLQuery = Query()
        return self.urls_table.search(URLQuery.url == url) != []

    def mark_as_processed(self, url: str, status: str = 'success',
                          content_type: str = 'html', error: Optional[str] = None):
        """Marca uma URL como processada"""
        URLQuery = Query()

        data = {
            'url': url,
            'status': status,
            'content_type': content_type,
            'processed_at': datetime.now().isoformat(),
            'error': error
        }

        if self.is_processed(url):
            self.urls_table.update(data, URLQuery.url == url)
        else:
            self.urls_table.insert(data)

        logger.info(f"URL marcada como processada: {url} [{status}]")

    def get_processed_count(self) -> int:
        """Retorna o número de URLs processadas"""
        return len(self.urls_table)

    def get_all_processed_urls(self) -> list:
        """Retorna todas as URLs processadas"""
        return [item['url'] for item in self.urls_table.all()]

    def close(self):
        """Fecha a conexão com o banco de dados"""
        self.db.close()


class TextStorage:
    """Gerencia o armazenamento incremental de texto extraído"""

    def __init__(self, output_file: Path):
        self.output_file = output_file

    def append_text(self, url: str, text: str, content_type: str = 'html'):
        """Adiciona texto extraído ao arquivo de saída"""
        if not text or not text.strip():
            logger.warning(f"Texto vazio para {url}")
            return

        with open(self.output_file, 'a', encoding='utf-8') as f:
            separator = "\n" + "=" * 80 + "\n"
            f.write(separator)
            f.write(f"URL: {url}\n")
            f.write(f"Tipo: {content_type}\n")
            f.write(f"Extraído em: {datetime.now().isoformat()}\n")
            f.write(separator)
            f.write(text.strip())
            f.write("\n\n")

        logger.info(f"Texto adicionado ao arquivo: {len(text)} caracteres de {url}")

    def get_file_size(self) -> int:
        """Retorna o tamanho do arquivo de texto em bytes"""
        if self.output_file.exists():
            return self.output_file.stat().st_size
        return 0

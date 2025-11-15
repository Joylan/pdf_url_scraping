"""Funções utilitárias"""
import logging
import re
from pathlib import Path
from typing import Set
from urllib.parse import urlparse, urljoin, urldefrag

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normaliza uma URL removendo fragmentos e trailing slashes

    Args:
        url: URL a ser normalizada

    Returns:
        URL normalizada
    """
    url, _ = urldefrag(url)
    url = url.rstrip('/')
    return url


def is_valid_url(url: str, ignored_extensions: Set[str]) -> bool:
    """Verifica se a URL é válida e não deve ser ignorada

    Args:
        url: URL a ser validada
        ignored_extensions: Conjunto de extensões a ignorar

    Returns:
        True se a URL for válida, False caso contrário
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False

    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in ignored_extensions):
        return False

    return True


def clean_text(text: str) -> str:
    """Limpa e normaliza o texto extraído

    Args:
        text: Texto a ser limpo

    Returns:
        Texto limpo e normalizado
    """
    if not text:
        return ""

    # Substituir múltiplos espaços por um único espaço
    text = re.sub(r'\s+', ' ', text)
    # Substituir múltiplas quebras de linha por no máximo duas
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remover espaços no início e fim
    text = text.strip()

    return text


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo para leitura humana

    Args:
        size_bytes: Tamanho em bytes

    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def setup_logging(log_file: Path, level: int = logging.INFO):
    """Configura o sistema de logging com formato limpo

    Args:
        log_file: Caminho do arquivo de log
        level: Nível de logging (padrão: INFO)
    """
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formato simplificado
    formatter = logging.Formatter('%(message)s')

    # Handler para arquivo (com mais detalhes)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Handler para console (simplificado)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Configurar logger raiz
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Silenciar logs verbosos de bibliotecas externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('connectionpool').setLevel(logging.WARNING)


def extract_links_from_text(html: str, base_url: str) -> Set[str]:
    """Extrai links de HTML usando BeautifulSoup

    Args:
        html: Conteúdo HTML
        base_url: URL base para resolver links relativos

    Returns:
        Conjunto de URLs normalizadas
    """
    soup = BeautifulSoup(html, 'lxml')
    links = set()

    for tag in soup.find_all('a', href=True):
        href = tag['href']
        absolute_url = urljoin(base_url, href)
        normalized = normalize_url(absolute_url)
        links.add(normalized)

    return links

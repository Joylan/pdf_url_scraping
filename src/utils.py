"""Funções utilitárias"""
import logging
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normaliza uma URL removendo fragmentos e trailing slashes"""
    url, _ = urldefrag(url)
    url = url.rstrip('/')
    return url


def is_same_domain(url: str, base_domain: str) -> bool:
    """Verifica se a URL pertence ao mesmo domínio ou subdomínio"""
    url_domain = urlparse(url).netloc
    base_domain_parsed = urlparse(base_domain).netloc

    url_domain = url_domain.replace('www.', '')
    base_domain_parsed = base_domain_parsed.replace('www.', '')

    return url_domain == base_domain_parsed or url_domain.endswith('.' + base_domain_parsed)


def is_valid_url(url: str, ignored_extensions: set) -> bool:
    """Verifica se a URL é válida e não deve ser ignorada"""
    if not url or not url.startswith(('http://', 'https://')):
        return False

    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in ignored_extensions):
        return False

    return True


def clean_text(text: str) -> str:
    """Limpa e normaliza o texto extraído"""
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = text.strip()

    return text


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo para leitura humana"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def setup_logging(log_file: Path, level=logging.INFO):
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def extract_links_from_text(html: str, base_url: str) -> set:
    """Extrai links de HTML usando regex simples"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'lxml')
    links = set()

    for tag in soup.find_all('a', href=True):
        href = tag['href']
        absolute_url = urljoin(base_url, href)
        normalized = normalize_url(absolute_url)
        links.add(normalized)

    return links

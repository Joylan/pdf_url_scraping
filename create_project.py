"""
Script para criar toda a estrutura do projeto RAG Crawler
Execute: python create_project.py
"""
from pathlib import Path


def create_file(filepath, content):
    """Cria arquivo com conteúdo"""
    Path(filepath).parent.mkdir(exist_ok=True, parents=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ {filepath}")


def create_project():
    print("=" * 70)
    print(" " * 20 + "CRIANDO PROJETO RAG CRAWLER")
    print("=" * 70 + "\n")

    # Criar diretórios
    print("Criando diretórios...")
    dirs = ['config', 'src', 'data', 'data/pdfs', 'logs']
    for d in dirs:
        Path(d).mkdir(exist_ok=True, parents=True)
        print(f"  ✓ {d}/")

    print("\nCriando arquivos...\n")

    # ==================== requirements.txt ====================
    create_file('requirements.txt', '''requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
PyPDF2==3.0.1
pdfplumber==0.10.3
urllib3==2.1.0
tinydb==4.8.0
python-dotenv==1.0.0
colorama==0.4.6''')

    # ==================== config/__init__.py ====================
    create_file('config/__init__.py', '')

    # ==================== config/settings.py ====================
    create_file('config/settings.py', '''"""Configurações do projeto"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
PDF_DIR = DATA_DIR / "pdfs"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

CRAWLED_URLS_DB = DATA_DIR / "crawled_urls.json"
TEXT_OUTPUT_FILE = DATA_DIR / "text_output.txt"
LOG_FILE = LOGS_DIR / "crawler.log"

MAX_DEPTH = 3
MAX_PAGES = 100
DELAY_BETWEEN_REQUESTS = 1
TIMEOUT = 10

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

IGNORED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
    '.mp4', '.avi', '.mov', '.mp3', '.wav',
    '.zip', '.tar', '.gz', '.rar'
}

ACCEPTED_CONTENT_TYPES = {
    'text/html',
    'application/pdf',
    'text/plain'
}

MAX_PDF_SIZE_MB = 50''')

    # ==================== src/__init__.py ====================
    create_file('src/__init__.py', '''"""RAG Crawler - Sistema de crawling para RAG"""
__version__ = '1.0.0'
__author__ = 'Your Name'

from src.crawler import WebCrawler
from src.scraper import HTMLScraper
from src.pdf_extractor import PDFExtractor
from src.storage import URLStorage, TextStorage

__all__ = [
    'WebCrawler',
    'HTMLScraper', 
    'PDFExtractor',
    'URLStorage',
    'TextStorage'
]''')

    # ==================== src/utils.py ====================
    create_file('src/utils.py', '''"""Funções utilitárias"""
from urllib.parse import urlparse, urljoin, urldefrag
from pathlib import Path
import logging
import re

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
    
    text = re.sub(r'\\s+', ' ', text)
    text = re.sub(r'\\n\\s*\\n\\s*\\n+', '\\n\\n', text)
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
    
    return links''')

    # ==================== src/storage.py ====================
    create_file('src/storage.py', '''"""Módulo de persistência para rastrear URLs processadas"""
from tinydb import TinyDB, Query
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

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
            separator = "\\n" + "="*80 + "\\n"
            f.write(separator)
            f.write(f"URL: {url}\\n")
            f.write(f"Tipo: {content_type}\\n")
            f.write(f"Extraído em: {datetime.now().isoformat()}\\n")
            f.write(separator)
            f.write(text.strip())
            f.write("\\n\\n")
        
        logger.info(f"Texto adicionado ao arquivo: {len(text)} caracteres de {url}")
    
    def get_file_size(self) -> int:
        """Retorna o tamanho do arquivo de texto em bytes"""
        if self.output_file.exists():
            return self.output_file.stat().st_size
        return 0''')

    # ==================== src/scraper.py ====================
    create_file('src/scraper.py', '''"""Módulo de scraping de conteúdo HTML"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
import logging
from config.settings import HEADERS, TIMEOUT
from src.utils import clean_text

logger = logging.getLogger(__name__)

class HTMLScraper:
    """Extrai conteúdo textual de páginas HTML"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def fetch_page(self, url: str) -> Optional[Tuple[str, str]]:
        """Busca o conteúdo de uma página"""
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            return response.content, content_type
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar {url}: {str(e)}")
            return None
    
    def extract_text(self, html_content: bytes, url: str) -> str:
        """Extrai texto útil de conteúdo HTML"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            for element in soup(['script', 'style', 'nav', 'footer', 
                                'header', 'aside', 'noscript', 'iframe']):
                element.decompose()
            
            text = soup.get_text(separator='\\n')
            text = clean_text(text)
            
            logger.info(f"Texto extraído de {url}: {len(text)} caracteres")
            return text
        
        except Exception as e:
            logger.error(f"Erro ao extrair texto de {url}: {str(e)}")
            return ""
    
    def scrape(self, url: str) -> Optional[str]:
        """Realiza scraping completo de uma URL"""
        result = self.fetch_page(url)
        
        if not result:
            return None
        
        content, content_type = result
        
        if 'text/html' not in content_type:
            logger.warning(f"Conteúdo não é HTML: {url} ({content_type})")
            return None
        
        return self.extract_text(content, url)
    
    def close(self):
        """Fecha a sessão"""
        self.session.close()''')

    # ==================== src/pdf_extractor.py (PARTE 1) ====================
    pdf_content_part1 = '''"""Módulo de extração de texto de PDFs"""
    import requests
    import pdfplumber
    from pathlib import Path
    from typing import Optional
    import logging
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

                full_text = '\\n\\n'.join(text_parts)
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
            self.session.close()'''

    # ==================== src/crawler.py ====================
    create_file('src/crawler.py', '''"""Módulo de crawling de páginas web"""
import time
from urllib.parse import urlparse
from typing import Set
import logging
from collections import deque

from src.scraper import HTMLScraper
from src.pdf_extractor import PDFExtractor
from src.storage import URLStorage, TextStorage
from src.utils import (
    normalize_url, is_same_domain, is_valid_url, 
    extract_links_from_text
)
from config.settings import (
    DELAY_BETWEEN_REQUESTS, MAX_DEPTH, MAX_PAGES,
    IGNORED_EXTENSIONS
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
        base_domain = start_url
        
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
            
            success, new_links = self._process_url(url, base_domain)
            
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
    
    def _process_url(self, url: str, base_domain: str) -> tuple:
        """Processa uma URL específica"""
        logger.info(f"Processando: {url}")
        
        if not is_same_domain(url, base_domain):
            logger.debug(f"Ignorando URL externa: {url}")
            return False, set()
        
        if not is_valid_url(url, IGNORED_EXTENSIONS):
            logger.debug(f"URL inválida ou ignorada: {url}")
            return False, set()
        
        if url.lower().endswith('.pdf'):
            return self._process_pdf(url), set()
        else:
            return self._process_html(url, base_domain)
    
    def _process_html(self, url: str, base_domain: str) -> tuple:
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
                    if is_same_domain(link, base_domain) and 
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
        
        print("\\n" + "="*60)
        print("RESUMO DO CRAWLING")
        print("="*60)
        print(f"Total de URLs processadas: {total_urls}")
        print(f"Páginas processadas nesta execução: {self.pages_processed}")
        print(f"Tamanho do arquivo de texto: {format_file_size(file_size)}")
        print("="*60 + "\\n")
    
    def close(self):
        """Fecha recursos"""
        self.scraper.close()
        self.pdf_extractor.close()
        self.url_storage.close()''')

    # ==================== main.py ====================
    create_file('main.py', '''"""Script principal para executar o crawler"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.crawler import WebCrawler
from src.storage import URLStorage, TextStorage
from src.utils import setup_logging
from config.settings import (
    CRAWLED_URLS_DB, TEXT_OUTPUT_FILE, LOG_FILE,
    MAX_DEPTH, MAX_PAGES
)

def main():
    """Função principal"""
    
    parser = argparse.ArgumentParser(
        description='Web Crawler para extração de texto para RAG'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='URL inicial para começar o crawling'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=MAX_DEPTH,
        help=f'Profundidade máxima de crawling (padrão: {MAX_DEPTH})'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=MAX_PAGES,
        help=f'Número máximo de páginas a processar (padrão: {MAX_PAGES})'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Limpa o histórico de URLs processadas e recomeça do zero'
    )
    
    args = parser.parse_args()
    
    setup_logging(LOG_FILE)
    
    if args.reset:
        if CRAWLED_URLS_DB.exists():
            CRAWLED_URLS_DB.unlink()
            print("✓ Histórico de URLs limpo")
        if TEXT_OUTPUT_FILE.exists():
            TEXT_OUTPUT_FILE.unlink()
            print("✓ Arquivo de texto limpo")
    
    url_storage = URLStorage(CRAWLED_URLS_DB)
    text_storage = TextStorage(TEXT_OUTPUT_FILE)
    
    crawler = WebCrawler(
        url_storage=url_storage,
        text_storage=text_storage,
        max_depth=args.max_depth,
        max_pages=args.max_pages
    )
    
    try:
        crawler.crawl(args.url)
        
        print(f"\\n✓ Crawling concluído!")
        print(f"✓ Arquivo de saída: {TEXT_OUTPUT_FILE}")
        print(f"✓ Banco de URLs: {CRAWLED_URLS_DB}")
        
    except KeyboardInterrupt:
        print("\\n\\n⚠ Crawling interrompido pelo usuário")
    
    except Exception as e:
        print(f"\\n✗ Erro durante execução: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        crawler.close()

if __name__ == '__main__':
    main()''')

    # ==================== .gitignore ====================
    create_file('.gitignore', '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Projeto
data/
logs/
*.log
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Vector stores
vectorstore/
vectorstore_faiss/
storage_llamaindex/
chroma_db/''')

    # ==================== README.md ====================
    create_file('README.md', '''# RAG Crawler - Web Scraping para RAG com LLM

Sistema modular de crawling, scraping e extração de texto de páginas web e PDFs, otimizado para preparar dados para sistemas RAG (Retrieval-Augmented Generation) com LLMs.

## 🚀 Instalação Rápida

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\\Scripts\\activate no Windows

# 2. Instalar dependências
pip install -r requirements.txt
```

## 📖 Uso Básico

```bash
# Executar crawler
python main.py --url https://example.com

# Com opções
python main.py --url https://example.com --max-depth 3 --max-pages 50

# Resetar e recomeçar
python main.py --url https://example.com --reset
```

## 📁 Estrutura

```
rag-crawler/
├── config/settings.py      # Configurações
├── src/
│   ├── crawler.py         # Motor de crawling
│   ├── scraper.py         # Extração HTML
│   ├── pdf_extractor.py   # Extração PDF
│   ├── storage.py         # Persistência
│   └── utils.py           # Utilidades
├── data/
│   ├── text_output.txt    # Texto extraído (SAÍDA)
│   └── crawled_urls.json  # URLs processadas
└── main.py                # Script principal
```

## ✨ Características

- ✅ Crawling inteligente com controle de profundidade
- ✅ Scraping incremental (não reprocessa URLs)
- ✅ Suporte a PDFs
- ✅ Texto limpo e estruturado para RAG
- ✅ Logging completo
- ✅ Modular e reutilizável

## 📚 Documentação

O texto extraído fica em `data/text_output.txt` no formato:

```
================================================================================
URL: https://example.com/pagina1
Tipo: html
Extraído em: 2025-10-18T10:30:00
================================================================================
[Texto extraído...]
```

Pronto para uso com LangChain, LlamaIndex ou qualquer sistema RAG!

## ⚙️ Configuração

Edite `config/settings.py` para ajustar:
- MAX_DEPTH: Profundidade máxima de crawling
- MAX_PAGES: Número máximo de páginas
- DELAY_BETWEEN_REQUESTS: Delay entre requisições
- IGNORED_EXTENSIONS: Extensões para ignorar

## 🐛 Solução de Problemas

- **Erro de importação**: Verifique se todas as dependências estão instaladas
- **PDFs vazios**: Alguns PDFs podem ser imagens escaneadas
- **Muitas URLs ignoradas**: Verifique IGNORED_EXTENSIONS e max-depth

## 📄 Licença

Projeto open-source usando bibliotecas MIT/Apache 2.0.''')

    print("\\n" + "=" * 70)
    print(" " * 25 + "✓ PROJETO CRIADO!")
    print("=" * 70)
    print("\\nPróximos passos:")
    print("\\n1. Instale as dependências:")
    print("   pip install -r requirements.txt")
    print("\\n2. Execute o crawler:")
    print("   python main.py --url https://example.com")
    print("\\n3. Verifique o resultado:")
    print("   cat data/text_output.txt")
    print("\\n" + "=" * 70 + "\\n")


if __name__ == '__main__':
    create_project()

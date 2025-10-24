"""Configurações do projeto"""
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

MAX_PDF_SIZE_MB = 50

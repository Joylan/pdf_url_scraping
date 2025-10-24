"""Script principal para executar o crawler"""
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

        print(f"\n✓ Crawling concluído!")
        print(f"✓ Arquivo de saída: {TEXT_OUTPUT_FILE}")
        print(f"✓ Banco de URLs: {CRAWLED_URLS_DB}")

    except KeyboardInterrupt:
        print("\n\n⚠ Crawling interrompido pelo usuário")

    except Exception as e:
        print(f"\n✗ Erro durante execução: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        crawler.close()


if __name__ == '__main__':
    main()

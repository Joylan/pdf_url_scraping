# domain_counter.py

import logging
from urllib.parse import urljoin

import requests
import tldextract
import urllib3
from bs4 import BeautifulSoup

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def crawl_subdomains(base_url, max_pages=10000, max_depth=6):
    """
    Faz crawling a partir da URL base e retorna todos os subdomínios encontrados.
    """
    visited = set()
    queue = [(base_url, 0)]
    subdomains = set()

    parsed_base = tldextract.extract(base_url)
    base_domain = f"{parsed_base.domain}.{parsed_base.suffix}"

    logger.info(f"Iniciando crawl na URL base: {base_url}")
    logger.info(f"Domínio base identificado: {base_domain}")
    logger.info(f"Máx. páginas: {max_pages}, Máx. profundidade: {max_depth}")

    while queue and len(visited) < max_pages:
        url, depth = queue.pop(0)
        if url in visited or depth > max_depth:
            continue
        visited.add(url)
        logger.info(f"[Depth {depth}] Processando URL: {url}")

        # Extrair subdomínio
        parsed = tldextract.extract(url)
        if parsed.subdomain:
            subdomains.add(parsed.subdomain)
            logger.info(f"  → Subdomínio encontrado: {parsed.subdomain}")

        # Baixar conteúdo da página
        try:
            resp = requests.get(url, timeout=5, verify=False)
            if "text/html" not in resp.headers.get("Content-Type", ""):
                logger.debug(f"  → URL não é HTML, ignorando: {url}")
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # Extrair links
            for link_tag in soup.find_all("a", href=True):
                href = link_tag["href"]
                href_full = urljoin(url, href)
                href_parsed = tldextract.extract(href_full)
                domain = f"{href_parsed.domain}.{href_parsed.suffix}"
                if domain == base_domain and href_full not in visited:
                    queue.append((href_full, depth + 1))
                    logger.debug(f"  → Link adicionado à fila: {href_full}")
        except Exception as e:
            logger.warning(f"  ❌ Erro ao processar {url}: {e}")
            continue

    logger.info(f"Crawl finalizado. Total URLs visitadas: {len(visited)}")
    logger.info(f"Total de subdomínios encontrados: {len(subdomains)}")

    return subdomains


def save_subdomains_to_file(subdomains, filename="subdomains.txt"):
    """Grava todos os subdomínios em um arquivo, um por linha"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for sub in sorted(subdomains):
                f.write(sub + "\n")
        logger.info(f"Subdomínios salvos em: {filename}")
    except Exception as e:
        logger.error(f"Erro ao salvar subdomínios em arquivo: {e}")


if __name__ == "__main__":
    url_base = "https://unila.edu.br"
    subs = crawl_subdomains(url_base, max_pages=10000, max_depth=1)
    logger.info(f"Subdomínios encontrados em {url_base}:")
    for s in sorted(subs):
        logger.info(f"  - {s}")
    logger.info(f"Total: {len(subs)} subdomínio(s)")

    # Salvar subdomínios em arquivo texto
    save_subdomains_to_file(subs, filename="subdomains.txt")

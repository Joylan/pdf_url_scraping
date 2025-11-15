import hashlib
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import pandas as pd
import scrapy
import seaborn as sns


# ============================
# SISTEMA DE LOGS COLORIDOS
# ============================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg):
    print(f"{Colors.OKCYAN}[{datetime.now().strftime('%H:%M:%S')}] ℹ️  {msg}{Colors.ENDC}")


def log_success(msg):
    print(f"{Colors.OKGREEN}[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}{Colors.ENDC}")


def log_warning(msg):
    print(f"{Colors.WARNING}[{datetime.now().strftime('%H:%M:%S')}] ⚠️  {msg}{Colors.ENDC}")


def log_error(msg):
    print(f"{Colors.FAIL}[{datetime.now().strftime('%H:%M:%S')}] ❌ {msg}{Colors.ENDC}")


def log_progress(msg):
    print(f"{Colors.OKBLUE}[{datetime.now().strftime('%H:%M:%S')}] 🔄 {msg}{Colors.ENDC}")


def log_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}\n  {msg}\n{'=' * 70}{Colors.ENDC}\n")


# ============================
# ARMAZENAMENTO GLOBAL DE RESULTADOS
# ============================
class ResultsStorage:
    results = []

    @classmethod
    def add_result(cls, data):
        cls.results.append(data)

    @classmethod
    def get_results(cls):
        return cls.results

    @classmethod
    def clear(cls):
        cls.results = []


# ============================
# SPIDER OTIMIZADO
# ============================
class UnilaDepthSpider(scrapy.Spider):
    name = "unila_depth"
    allowed_domains = ["unila.edu.br"]
    start_urls = ["https://portal.unila.edu.br"]

    custom_settings = {
        "LOG_LEVEL": "WARNING",
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 8,
        "ROBOTSTXT_OBEY": True,
        "HTTPERROR_ALLOWED_CODES": [404, 500, 502, 503],
        "RETRY_ENABLED": False,
        "COOKIES_ENABLED": False,
        "DOWNLOAD_TIMEOUT": 20,
    }

    def __init__(self, max_depth=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_depth = int(max_depth)
        self.visited = set()
        self.relevant = set()
        self.content_hashes = set()
        self.url_types = Counter()
        self.content_sizes = []
        self.errors = 0
        self.duplicates = 0
        self.start_time = time.time()
        self.last_log_time = time.time()
        self.urls_since_last_log = 0

        # Métricas por profundidade
        self.depth_metrics = defaultdict(lambda: {
            'urls': 0,
            'relevant': 0,
            'content_size': [],
        })

        # Keywords otimizadas e categorizadas
        self.relevant_patterns = [
            r'curso[s]?', r'gradua[cç][aã]o', r'p[oó]s-gradua[cç][aã]o',
            r'mestrado', r'doutorado', r'disciplina[s]?', r'ementa[s]?',
            r'matr[ií]cula', r'calend[aá]rio', r'hor[aá]rio', r'aula[s]?',
            r'pesquisa', r'laborat[oó]rio', r'projeto', r'publica[cç][õo][ee]s',
            r'revista', r'ci[eê]nt[ií]fic[oa]', r'extens[aã]o',
            r'edital', r'editais', r'processo[- ]seletivo', r'resolu[cç][aã]o',
            r'portaria', r'normativa', r'regulamento', r'documento',
            r'biblioteca', r'ru\b', r'restaurante', r'assist[eê]ncia',
            r'bolsa[s]?', r'aux[ií]lio', r'apoio', r'atendimento',
            r'docente', r'professor', r'servidor', r'coordena[cç][aã]o'
        ]

        # Compilar regex para performance
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.relevant_patterns]

        log_info(f"Spider inicializado - Profundidade máxima: {max_depth}")

    def is_relevant_url(self, url):
        """Verifica relevância usando regex otimizado"""
        url_lower = url.lower()
        return any(pattern.search(url_lower) for pattern in self.compiled_patterns)

    def extract_clean_text(self, response):
        """Extração otimizada de texto limpo"""
        text_parts = response.css(
            'p::text, h1::text, h2::text, h3::text, h4::text, '
            'li::text, td::text, div::text'
        ).getall()

        clean_text = ' '.join(t.strip() for t in text_parts if t.strip())
        return clean_text

    def parse(self, response, depth=0):
        url = response.url

        # Log de progresso
        self.urls_since_last_log += 1
        current_time = time.time()

        if self.urls_since_last_log >= 50 or (current_time - self.last_log_time) >= 5:
            elapsed = current_time - self.start_time
            rate = len(self.visited) / elapsed if elapsed > 0 else 0
            log_progress(
                f"D{self.max_depth}: {len(self.visited)} URLs | "
                f"{len(self.relevant)} relevantes | "
                f"Prof. atual: {depth}/{self.max_depth} | "
                f"Taxa: {rate:.1f} URLs/s"
            )
            self.last_log_time = current_time
            self.urls_since_last_log = 0

        # Tratamento de erros
        if response.status >= 400:
            self.errors += 1
            log_warning(f"Erro {response.status}: {url[:60]}...")
            return

        if url in self.visited:
            self.duplicates += 1
            return

        self.visited.add(url)

        # Análise de tipo de URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip('/').split('/') if p]
        if path_parts:
            self.url_types[path_parts[0]] += 1

        # Verificar tipo de conteúdo
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        if not any(t in content_type for t in ['text', 'html', 'xml']):
            return

        # Verificar relevância da URL
        is_relevant = self.is_relevant_url(url)

        # Análise de conteúdo
        content = response.text
        content_hash = hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()

        if content_hash in self.content_hashes:
            self.duplicates += 1
            return

        self.content_hashes.add(content_hash)

        # Extrair e analisar texto
        clean_text = self.extract_clean_text(response)
        content_size = len(clean_text)
        self.content_sizes.append(content_size)

        # Atualizar métricas por profundidade
        self.depth_metrics[depth]['urls'] += 1
        self.depth_metrics[depth]['content_size'].append(content_size)

        # Marcar como relevante se tem conteúdo significativo
        if is_relevant and content_size > 300:
            self.relevant.add(url)
            self.depth_metrics[depth]['relevant'] += 1

        # Seguir links se não atingiu profundidade máxima
        if depth < self.max_depth:
            # Extensões de arquivo a ignorar
            ignore_extensions = {
                '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip',
                '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.mp3', '.mp4', '.avi', '.mov', '.rar', '.7z'
            }

            for link in response.css("a::attr(href)").getall():
                # Filtros otimizados
                if not link or any([
                    link.startswith(('mailto:', 'tel:', 'javascript:', '#')),
                    any(link.lower().endswith(ext) for ext in ignore_extensions)
                ]):
                    continue

                # Seguir link com profundidade incrementada
                yield response.follow(link, callback=self.parse, cb_kwargs={'depth': depth + 1})

    def closed(self, reason):
        elapsed = round(time.time() - self.start_time, 2)
        avg_content = sum(self.content_sizes) / len(self.content_sizes) if self.content_sizes else 0
        relevance_ratio = len(self.relevant) / len(self.visited) * 100 if self.visited else 0

        log_success(f"Spider finalizado - D{self.max_depth}")
        log_info(
            f"Tempo: {elapsed}s | URLs: {len(self.visited)} | Relevantes: {len(self.relevant)} ({relevance_ratio:.1f}%)")

        if self.duplicates > 0:
            log_warning(f"Duplicatas: {self.duplicates}")
        if self.errors > 0:
            log_warning(f"Erros: {self.errors}")

        # Calcular métricas
        urls_per_sec = len(self.visited) / elapsed if elapsed > 0 else 0
        relevant_per_sec = len(self.relevant) / elapsed if elapsed > 0 else 0
        duplicate_ratio = (self.duplicates / len(self.visited) * 100) if len(self.visited) > 0 else 0
        error_ratio = (self.errors / len(self.visited) * 100) if len(self.visited) > 0 else 0

        # ROI Score
        quality_factor = (1 - duplicate_ratio / 100) * (1 - error_ratio / 100)
        roi_score = (len(self.relevant) * quality_factor) / (elapsed + 1) if elapsed > 0 else 0

        # Eficiência de conteúdo
        content_efficiency = (len(self.relevant) * avg_content) / (elapsed * 1024) if elapsed > 0 else 0

        # Armazenar resultado
        result = {
            "depth": self.max_depth,
            "total_urls": len(self.visited),
            "relevant_urls": len(self.relevant),
            "unique_content": len(self.content_hashes),
            "duplicates": self.duplicates,
            "errors": self.errors,
            "time_sec": round(elapsed, 2),
            "relevance_ratio": round(relevance_ratio, 2),
            "urls_per_sec": round(urls_per_sec, 2),
            "relevant_per_sec": round(relevant_per_sec, 3),
            "duplicate_ratio": round(duplicate_ratio, 2),
            "error_ratio": round(error_ratio, 2),
            "avg_content_size": round(avg_content, 2),
            "roi_score": round(roi_score, 3),
            "content_efficiency": round(content_efficiency, 2),
            "quality_factor": round(quality_factor, 3)
        }

        ResultsStorage.add_result(result)

        log_success(f"Resultado salvo: ROI={roi_score:.3f}\n")


# ============================
# ANÁLISE E RECOMENDAÇÕES
# ============================
def analyze_and_recommend(df):
    """Análise avançada com recomendações otimizadas"""

    log_header("📊 ANÁLISE COMPLETA E RECOMENDAÇÕES")

    # Salvar CSV
    csv_path = "unila_depth_analysis.csv"
    df.to_csv(csv_path, index=False)
    log_success(f"Dados salvos: {csv_path}")

    # Calcular métricas derivadas
    df['marginal_gain'] = df['relevant_urls'].diff()
    df['marginal_gain_pct'] = df['relevant_urls'].pct_change() * 100
    df['efficiency_ratio'] = df['relevant_urls'] / df['total_urls'].replace(0, 1)
    df['cost_per_relevant'] = df['time_sec'] / df['relevant_urls'].replace(0, 1)

    # Identificar pontos ótimos
    max_roi_idx = df['roi_score'].idxmax()
    max_efficiency_idx = df['relevant_per_sec'].idxmax()
    max_relevant_idx = df['relevant_urls'].idxmax()

    # Ponto de retornos decrescentes
    diminishing_idx = df[df['marginal_gain_pct'] < 15].index.min() if len(
        df[df['marginal_gain_pct'] < 15]) > 0 else None

    print("\n" + "🎯 " + Colors.BOLD + "CONFIGURAÇÕES RECOMENDADAS PARA RAG:" + Colors.ENDC)
    print("=" * 70)

    # Recomendação 1: Melhor ROI
    best_roi = df.loc[max_roi_idx]
    print(f"\n{Colors.OKGREEN}1️⃣  RECOMENDADO - MELHOR CUSTO-BENEFÍCIO{Colors.ENDC}")
    print(f"   Profundidade: {Colors.BOLD}{int(best_roi['depth'])}{Colors.ENDC}")
    print(f"   URLs relevantes: {int(best_roi['relevant_urls'])} páginas")
    print(f"   Taxa de relevância: {best_roi['relevance_ratio']:.1f}%")
    print(f"   Tempo estimado: {best_roi['time_sec']:.0f}s (~{best_roi['time_sec'] / 60:.1f} min)")
    print(f"   ROI Score: {best_roi['roi_score']:.3f}")

    # Recomendação 2: Scraping rápido
    best_eff = df.loc[max_efficiency_idx]
    print(f"\n{Colors.OKBLUE}2️⃣  SCRAPING RÁPIDO{Colors.ENDC}")
    print(f"   Profundidade: {Colors.BOLD}{int(best_eff['depth'])}{Colors.ENDC}")
    print(f"   URLs relevantes: {int(best_eff['relevant_urls'])} páginas")
    print(f"   Tempo: {best_eff['time_sec']:.0f}s")

    # Recomendação 3: Máxima cobertura
    best_cov = df.loc[max_relevant_idx]
    print(f"\n{Colors.OKCYAN}3️⃣  MÁXIMA COBERTURA{Colors.ENDC}")
    print(f"   Profundidade: {Colors.BOLD}{int(best_cov['depth'])}{Colors.ENDC}")
    print(f"   URLs relevantes: {int(best_cov['relevant_urls'])} páginas")
    print(f"   Tempo: {best_cov['time_sec']:.0f}s")

    # Estatísticas gerais
    print("\n📈 " + Colors.BOLD + "ESTATÍSTICAS GERAIS:" + Colors.ENDC)
    print("=" * 70)
    print(f"Total máximo de URLs: {df['total_urls'].max()}")
    print(f"URLs relevantes máximas: {df['relevant_urls'].max()}")
    print(f"Taxa média de relevância: {df['relevance_ratio'].mean():.1f}%")
    print(f"Tamanho médio de conteúdo: {df['avg_content_size'].mean():.0f} caracteres")

    # Recomendação final
    print("\n💡 " + Colors.BOLD + Colors.OKGREEN + "CONFIGURAÇÃO FINAL:" + Colors.ENDC)
    print("=" * 70)

    recommended_depth = int(best_roi['depth'])
    recommended_pages = int(best_roi['total_urls'] * 1.2)

    print(f"\n✅ Use {Colors.BOLD}PROFUNDIDADE {recommended_depth}{Colors.ENDC} "
          f"com limite de {Colors.BOLD}{recommended_pages} URLs{Colors.ENDC}")

    print(f"\n   {Colors.BOLD}Configurações Scrapy:{Colors.ENDC}")
    print(f"   DEPTH_LIMIT = {recommended_depth}")
    print(f"   CLOSESPIDER_PAGECOUNT = {recommended_pages}")
    print(f"   DOWNLOAD_DELAY = 0.5")
    print(f"   CONCURRENT_REQUESTS = 8")

    create_visualizations(df)


# ============================
# VISUALIZAÇÕES
# ============================
def create_visualizations(df):
    """Cria visualizações completas"""

    log_progress("Gerando visualizações...")

    sns.set_style("whitegrid")
    fig = plt.figure(figsize=(18, 12))

    # 1. URLs Totais vs Relevantes
    ax1 = plt.subplot(3, 3, 1)
    width = 0.35
    x = df['depth']
    ax1.bar(x - width / 2, df['total_urls'], width, label='Total', alpha=0.8)
    ax1.bar(x + width / 2, df['relevant_urls'], width, label='Relevantes', alpha=0.8)
    ax1.set_xlabel('Profundidade', fontweight='bold')
    ax1.set_ylabel('Número de URLs', fontweight='bold')
    ax1.set_title('URLs Coletadas', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Taxa de Relevância
    ax2 = plt.subplot(3, 3, 2)
    ax2.plot(df['depth'], df['relevance_ratio'], 'o-', linewidth=2, markersize=8)
    ax2.fill_between(df['depth'], 0, df['relevance_ratio'], alpha=0.3)
    ax2.set_xlabel('Profundidade', fontweight='bold')
    ax2.set_ylabel('Taxa (%)', fontweight='bold')
    ax2.set_title('Taxa de Relevância', fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 3. ROI Score
    ax3 = plt.subplot(3, 3, 3)
    colors = plt.cm.RdYlGn(df['roi_score'] / df['roi_score'].max())
    ax3.bar(df['depth'], df['roi_score'], color=colors, edgecolor='black')
    best_idx = df['roi_score'].idxmax()
    ax3.set_xlabel('Profundidade', fontweight='bold')
    ax3.set_ylabel('ROI Score', fontweight='bold')
    ax3.set_title('⭐ Custo-Benefício (ROI)', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.text(df.loc[best_idx, 'depth'], df.loc[best_idx, 'roi_score'] * 1.05,
             '★', ha='center', fontsize=20, color='red')

    # 4. Tempo
    ax4 = plt.subplot(3, 3, 4)
    ax4.plot(df['depth'], df['time_sec'], 'o-', linewidth=2, markersize=8)
    ax4.fill_between(df['depth'], 0, df['time_sec'], alpha=0.2)
    ax4.set_xlabel('Profundidade', fontweight='bold')
    ax4.set_ylabel('Tempo (s)', fontweight='bold')
    ax4.set_title('Tempo de Execução', fontweight='bold')
    ax4.grid(True, alpha=0.3)

    # 5. Eficiência
    ax5 = plt.subplot(3, 3, 5)
    ax5.plot(df['depth'], df['relevant_per_sec'], 'o-', linewidth=2, markersize=8)
    ax5.set_xlabel('Profundidade', fontweight='bold')
    ax5.set_ylabel('Páginas/s', fontweight='bold')
    ax5.set_title('Eficiência', fontweight='bold')
    ax5.grid(True, alpha=0.3)

    # 6. Duplicatas e Erros
    ax6 = plt.subplot(3, 3, 6)
    width = 0.35
    ax6.bar(df['depth'] - width / 2, df['duplicate_ratio'], width, label='Duplicatas', alpha=0.8)
    ax6.bar(df['depth'] + width / 2, df['error_ratio'], width, label='Erros', alpha=0.8)
    ax6.set_xlabel('Profundidade', fontweight='bold')
    ax6.set_ylabel('Taxa (%)', fontweight='bold')
    ax6.set_title('Problemas', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)

    # 7. Ganho Marginal
    ax7 = plt.subplot(3, 3, 7)
    marginal = df['marginal_gain'].fillna(0)
    colors_mg = ['green' if x > 0 else 'red' for x in marginal]
    ax7.bar(df['depth'], marginal, color=colors_mg, alpha=0.7)
    ax7.set_xlabel('Profundidade', fontweight='bold')
    ax7.set_ylabel('Páginas Adicionais', fontweight='bold')
    ax7.set_title('Ganho Marginal', fontweight='bold')
    ax7.grid(True, alpha=0.3)

    # 8. Ratio Eficiência
    ax8 = plt.subplot(3, 3, 8)
    efficiency = (df['relevant_urls'] / df['total_urls'] * 100).fillna(0)
    ax8.plot(df['depth'], efficiency, 'o-', linewidth=2, markersize=8)
    ax8.fill_between(df['depth'], 0, efficiency, alpha=0.2)
    ax8.set_xlabel('Profundidade', fontweight='bold')
    ax8.set_ylabel('Ratio (%)', fontweight='bold')
    ax8.set_title('Relevantes/Total', fontweight='bold')
    ax8.grid(True, alpha=0.3)

    # 9. Score Composto
    ax9 = plt.subplot(3, 3, 9)
    metrics = ['roi_score', 'relevance_ratio', 'relevant_per_sec', 'quality_factor']
    normalized = df[metrics].copy()
    for col in metrics:
        max_val = df[col].max()
        if max_val > 0:
            normalized[col] = df[col] / max_val
    df['composite'] = normalized.mean(axis=1) * 100

    colors_comp = plt.cm.viridis(df['composite'] / 100)
    ax9.bar(df['depth'], df['composite'], color=colors_comp, edgecolor='black')
    ax9.set_xlabel('Profundidade', fontweight='bold')
    ax9.set_ylabel('Score', fontweight='bold')
    ax9.set_title('Score Global', fontweight='bold')
    ax9.grid(True, alpha=0.3)

    plt.tight_layout()

    output = 'unila_analysis.png'
    plt.savefig(output, dpi=300, bbox_inches='tight', facecolor='white')
    log_success(f"Gráficos salvos: {output}")
    plt.close()


# ============================
# EXECUÇÃO PRINCIPAL
# ============================
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer


def run_analysis(max_depth=6):
    """Executa análise sequencial de profundidades sem reiniciar o reactor"""
    log_header("🚀 ANÁLISE DE PROFUNDIDADE - PORTAL UNILA")
    log_info(f"Testando profundidades de 1 a {max_depth}")

    ResultsStorage.clear()
    runner = CrawlerRunner(settings={'LOG_LEVEL': 'WARNING', 'ROBOTSTXT_OBEY': True})

    @defer.inlineCallbacks
    def crawl_all():
        for depth in range(1, max_depth + 1):
            log_header(f"TESTE {depth}/{max_depth} - PROFUNDIDADE {depth}")
            yield runner.crawl(UnilaDepthSpider, max_depth=depth)
        reactor.stop()

    crawl_all()
    reactor.run()  # ✅ executa apenas uma vez

    # Análise dos resultados
    results = ResultsStorage.get_results()
    if not results:
        log_error("Nenhum resultado coletado!")
        return

    log_success(f"Coletados {len(results)} conjuntos de resultados")
    df = pd.DataFrame(results)
    analyze_and_recommend(df)


if __name__ == "__main__":
    run_analysis(max_depth=6)

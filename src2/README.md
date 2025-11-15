# RAG Crawler - Sistema de Crawling e Extração de Texto

Sistema robusto de web crawling para extração de texto de páginas HTML e arquivos PDF, otimizado para uso em sistemas
RAG (Retrieval-Augmented Generation).

## 🆕 Novidades da Versão Atualizada

### ✅ Correções Implementadas

1. **Garantia de Processamento da URL Inicial**
    - A URL inicial passada pelo usuário **sempre** é processada primeiro
    - Mesmo que já exista no banco de dados, o sistema verifica e processa se necessário
    - Garante que sites com subdomínios e subpáginas sempre incluam a página raiz

2. **Botão de Exportação Completo**
    - Nova opção no menu principal (opção 3)
    - Interface interativa para exportar todo o texto coletado
    - Formato UTF-8 com cabeçalho informativo
    - Verificação de arquivos existentes antes de sobrescrever
    - Estatísticas incluídas no arquivo exportado

3. **Logs Aprimorados**
    - URLs completas exibidas nos logs (limitadas a 80 caracteres para legibilidade)
    - Formato: `✓ [001] HTML | D0 | 12,345 chars | https://example.com/page`
    - Mais informativo e fácil de rastrear o progresso

4. **Correções de Avisos**
    - Type hints completos em todas as funções
    - Tratamento adequado de exceções com mensagens específicas
    - Documentação (docstrings) em todos os métodos
    - Validação de entrada de dados

## 📋 Características Principais

- ✅ Crawling recursivo com controle de profundidade
- ✅ Suporte para HTML e PDF
- ✅ Logs limpos e informativos
- ✅ Armazenamento incremental
- ✅ Exportação de dados em UTF-8
- ✅ Interface interativa via menu
- ✅ Controle de domínio e subdomínios
- ✅ Filtros de extensões indesejadas
- ✅ Estatísticas detalhadas

## 🚀 Instalação

### Requisitos

- Python 3.8+
- pip

### Dependências

```bash
pip install requests beautifulsoup4 lxml pdfplumber tinydb
```

## 📖 Como Usar

### Executar o Programa

```bash
python main.py
```

### Menu Principal

```
══════════════════════════════════════════════════════════════════════
MENU DE OPÇÕES:
──────────────────────────────────────────────────────────────────────
1. Iniciar novo crawling
2. Continuar crawling existente
3. Exportar texto coletado          ← NOVO!
4. Ver estatísticas
5. Limpar dados e reiniciar
0. Sair
──────────────────────────────────────────────────────────────────────
```

### Opção 1: Novo Crawling

1. Digite a URL inicial (ex: `https://example.com`)
2. Configure profundidade e limite de páginas (ou use padrões)
3. O sistema processará:
    - **Primeiro**: A URL inicial informada
    - **Depois**: Todas as subpáginas e PDFs encontrados
4. Progresso mostrado em tempo real com URLs completas

### Opção 3: Exportar Texto 🆕

1. Selecione a opção 3 no menu
2. Digite o nome do arquivo de exportação (padrão: `export_text_output.txt`)
3. Confirme se deseja sobrescrever arquivo existente
4. O sistema cria um arquivo UTF-8 com:
    - Cabeçalho com estatísticas
    - Todo o texto coletado
    - URLs de origem de cada conteúdo
    - Timestamps de extração

**Exemplo de Saída:**

```
================================================================================
RESULTADOS DO CRAWLING / SCRAPING
Exportado em: 2025-10-27 14:30:00
Total de páginas HTML: 45
Total de PDFs: 3
================================================================================

================================================================================
URL: https://example.com
Tipo: html
Extraído em: 2025-10-27T14:25:00
================================================================================
[Conteúdo extraído...]

================================================================================
URL: https://example.com/documento.pdf
Tipo: pdf
Extraído em: 2025-10-27T14:26:30
================================================================================
[Conteúdo do PDF...]
```

## 🔧 Configurações

Edite `config/settings.py` para personalizar:

```python
MAX_DEPTH = 5  # Profundidade máxima de crawling
MAX_PAGES = 100  # Número máximo de páginas
DELAY_BETWEEN_REQUESTS = 0.8  # Delay entre requisições (segundos)
TIMEOUT = 10  # Timeout de requisições
MAX_PDF_SIZE_MB = 50  # Tamanho máximo de PDF

# Extensões ignoradas
IGNORED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.svg',
    '.css', '.js', '.mp4', '.zip', ...
}
```

## 📊 Exemplo de Log

```
🚀 Iniciando crawl: https://example.com
📊 Limite: 100 páginas restantes | Profundidade: 5

📍 Processando URL inicial: https://example.com
✓ [  1] HTML | D0 | 15,234 chars | https://example.com
✓ [  2] HTML | D1 |  8,456 chars | https://example.com/about
✓ [  3] HTML | D1 | 12,789 chars | https://example.com/services
✓ [  1] PDF  | D2 | 45,123 chars | https://example.com/docs/manual.pdf

──────────────────────────────────────────────────────────────────────
📄 Páginas HTML: 3 | 📑 PDFs: 1 | 🔗 Total URLs: 4
💾 Tamanho: 156.78 KB
──────────────────────────────────────────────────────────────────────
```

## 📁 Estrutura de Diretórios

```
rag-crawler/
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Configurações do projeto
│
├── src/
│   ├── __init__.py
│   ├── crawler.py            # ✨ ATUALIZADO - Lógica principal
│   ├── scraper.py            # ✨ ATUALIZADO - Extração HTML
│   ├── pdf_extractor.py      # ✨ ATUALIZADO - Extração PDF
│   ├── storage.py            # ✨ ATUALIZADO - Armazenamento
│   └── utils.py              # ✨ ATUALIZADO - Funções auxiliares
│
├── data/
│   ├── crawled_urls.json     # Banco de URLs processadas
│   ├── text_output.txt       # Texto extraído
│   └── pdfs/                 # PDFs baixados
│
├── logs/
│   └── crawler.log           # Arquivo de log detalhado
│
├── main.py                   # ✨ ATUALIZADO - Script principal com menu
└── README.md                 # ✨ ATUALIZADO - Este arquivo
```

## 🎯 Fluxo de Trabalho

1. **Inicialização**: URL inicial é normalizada e validada
2. **Processamento da URL Inicial**: Garante que a página raiz seja sempre incluída
3. **Descoberta de Links**: Extrai todos os links da página
4. **Filtragem**: Remove links externos e extensões indesejadas
5. **Processamento Recursivo**: Processa subpáginas respeitando profundidade
6. **Extração de Texto**: Limpa e formata o conteúdo
7. **Armazenamento**: Salva incrementalmente em arquivo UTF-8
8. **Exportação**: Gera arquivo final com todos os dados coletados

## 🛡️ Tratamento de Erros

- ✅ Timeouts de requisição configuráveis
- ✅ Validação de tipo de conteúdo
- ✅ Verificação de tamanho de PDF
- ✅ Logs de debug para diagnóstico
- ✅ Recuperação de falhas individuais
- ✅ Modo de continuação preserva progresso

## 📝 Notas Importantes

### Garantia de URL Inicial

O sistema **sempre** processa a URL inicial antes de qualquer outra página, garantindo que:

- Sites com subdomínios incluam a página raiz
- O conteúdo principal seja sempre capturado
- Subpáginas sejam processadas na ordem correta

### Exportação de Dados

- Arquivo gerado em **UTF-8** para compatibilidade universal
- Inclui metadados de cada extração
- Formato otimizado para sistemas RAG
- Preserva estrutura e URLs de origem

### Performance

- Delay entre requisições evita sobrecarga
- Processamento incremental economiza memória
- Cache de URLs evita reprocessamento
- Logs otimizados para não poluir console

## 🤝 Contribuições

Melhorias e sugestões são bem-vindas!

## 📄 Licença

Este projeto está sob licença MIT.

---

**Versão**: 1.1.0  
**Última Atualização**: Outubro 2025  
**Autor**: Joylan Nunes Maciel
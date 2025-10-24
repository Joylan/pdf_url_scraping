# RAG Crawler - Web Scraping para RAG com LLM

Sistema modular de crawling, scraping e extração de texto de páginas web e PDFs, otimizado para preparar dados para
sistemas RAG (Retrieval-Augmented Generation) com LLMs.

## 🚀 Instalação Rápida

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate no Windows

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

Projeto open-source usando bibliotecas MIT/Apache 2.0.
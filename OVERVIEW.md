# 📘 Visão Geral do Projeto - RAG Crawler

## 🎯 Objetivo

Sistema modular e reutilizável para **crawling**, **scraping** e **extração de texto** de páginas web e PDFs,
especificamente otimizado para preparar dados para sistemas **RAG (Retrieval-Augmented Generation)** com LLMs.

## ✨ Características Principais

### 1. **Crawling Inteligente**

- Navega automaticamente por domínios e subdomínios
- Controle de profundidade e limite de páginas
- Respeita estrutura de links do site
- Delay configurável entre requisições

### 2. **Scraping Eficiente**

- Extrai apenas texto útil (remove scripts, estilos, etc)
- Limpeza e normalização automática
- Suporte a diferentes tipos de conteúdo
- Headers personalizáveis

### 3. **Processamento de PDFs**

- Download e extração automática
- Suporte a múltiplas páginas
- Limite de tamanho configurável
- Armazenamento organizado

### 4. **Persistência Incremental**

- Não reprocessa URLs já extraídas
- Banco de dados leve (TinyDB)
- Append incremental ao arquivo de texto
- Rastreamento de status e erros

### 5. **Preparado para RAG**

- Formato estruturado de saída
- Metadados preservados
- Fácil integração com LangChain, LlamaIndex
- Compatível com vector stores populares

## 🏗️ Arquitetura

```
┌─────────────┐
│   main.py   │  ← Script principal CLI
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   WebCrawler        │  ← Orquestra todo o processo
└──────┬──────────────┘
       │
       ├──► HTMLScraper      (extrai texto de HTML)
       ├──► PDFExtractor     (extrai texto de PDFs)
       ├──► URLStorage       (rastreia URLs processadas)
       └──► TextStorage      (salva texto incrementalmente)
```

### Módulos Principais

| Módulo             | Responsabilidade                             |
|--------------------|----------------------------------------------|
| `crawler.py`       | Motor de crawling, gerencia fila e navegação |
| `scraper.py`       | Extração de texto de páginas HTML            |
| `pdf_extractor.py` | Download e extração de texto de PDFs         |
| `storage.py`       | Persistência de URLs e texto                 |
| `utils.py`         | Funções auxiliares (normalização, validação) |
| `settings.py`      | Configurações centralizadas                  |

## 📊 Fluxo de Dados

```
URL Inicial
    │
    ▼
┌───────────────┐
│  Normalização │
└───────┬───────┘
        │
        ▼
┌───────────────┐     Sim     ┌──────────┐
│ Já processada?├─────────────►│  Pula    │
└───────┬───────┘              └──────────┘
        │ Não
        ▼
┌───────────────┐
│ Mesmo domínio?│
└───────┬───────┘
        │ Sim
        ▼
┌───────────────┐
│  Buscar HTML  │
└───────┬───────┘
        │
        ├──► HTML ──► Extrair Texto ──► Salvar
        │
        └──► PDF  ──► Baixar/Extrair ──► Salvar
        │
        ▼
┌───────────────┐
│ Extrair Links │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Adicionar à   │
│     Fila      │
└───────────────┘
```

## 📁 Estrutura de Arquivos

```
rag-crawler/
│
├── 📄 main.py                  # CLI principal
├── 📄 setup.py                 # Script de instalação
├── 📄 example_usage.py         # Exemplos práticos
├── 📄 requirements.txt         # Dependências
├── 📄 Makefile                 # Comandos úteis
│
├── 📖 README.md                # Documentação completa
├── 📖 QUICKSTART.md            # Guia rápido
├── 📖 RAG_INTEGRATION.md       # Integração RAG
├── 📖 OVERVIEW.md              # Este arquivo
│
├── 📂 config/
│   ├── __init__.py
│   └── settings.py             # Configurações
│
├── 📂 src/
│   ├── __init__.py
│   ├── crawler.py              # Motor de crawling
│   ├── scraper.py              # Scraping HTML
│   ├── pdf_extractor.py        # Extração PDF
│   ├── storage.py              # Persistência
│   └── utils.py                # Utilidades
│
├── 📂 data/                    # Gerado em runtime
│   ├── crawled_urls.json       # Histórico de URLs
│   ├── text_output.txt         # Texto extraído (SAÍDA)
│   └── pdfs/                   # PDFs baixados
│
└── 📂 logs/                    # Gerado em runtime
    └── crawler.log             # Logs detalhados
```

## 🔧 Tecnologias Utilizadas

### Core

- **Python 3.8+**: Linguagem base
- **Requests**: HTTP requests
- **BeautifulSoup4**: Parsing HTML
- **lxml**: Parser rápido

### Extração

- **PyPDF2**: Manipulação de PDFs
- **pdfplumber**: Extração avançada de PDFs

### Armazenamento

- **TinyDB**: Banco NoSQL leve (JSON)
- **Arquivos texto**: Saída simples e portável

### Utilities

- **colorama**: Output colorido
- **python-dotenv**: Variáveis de ambiente

## 🚀 Casos de Uso

### 1. Documentação Técnica

```bash
# Extrair docs de bibliotecas Python
python main.py --url https://docs.python.org --max-depth 3
```

### 2. Base de Conhecimento Corporativa

```bash
# Extrair conteúdo interno
python main.py --url https://wiki.empresa.com --max-depth 4
```

### 3. Pesquisa e Análise

```bash
# Coletar artigos de blog
python main.py --url https://blog.exemplo.com --max-pages 100
```

### 4. Treinamento de Chatbots

```bash
# Extrair FAQs e suporte
python main.py --url https://suporte.empresa.com
```

## 🎨 Diferenciais

### ✅ Modularidade

- Cada componente funciona independentemente
- Fácil de estender e customizar
- Reutilizável em outros projetos

### ✅ Simplicidade

- Código limpo e bem documentado
- Configuração via arquivo centralizado
- CLI intuitivo

### ✅ Eficiência

- Não reprocessa URLs
- Append incremental
- Controle de recursos

### ✅ Produção Ready

- Logging completo
- Tratamento de erros
- Configurações flexíveis
- Testes incluídos

## 📈 Pipeline RAG Completo

```
┌──────────────┐
│   Crawler    │
│              │
│  1. Navega   │
│  2. Extrai   │
│  3. Salva    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ text_output  │
│    .txt      │ ← Arquivo de saída
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Chunking    │
│              │
│ - Divide     │
│ - Overlap    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Embeddings  │
│              │
│ - OpenAI     │
│ - Local      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Vector Store │
│              │
│ - FAISS      │
│ - Pinecone   │
│ - Chroma     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     RAG      │
│              │
│ - Retrieval  │
│ - Generation │
└──────────────┘
```

## 🔐 Boas Práticas Implementadas

### Segurança

- ✅ Validação de URLs
- ✅ Timeout em requisições
- ✅ Limite de tamanho de arquivos
- ✅ Sanitização de input

### Performance

- ✅ Reuso de sessões HTTP
- ✅ Streaming de PDFs grandes
- ✅ Cache de URLs processadas
- ✅ Delay entre requisições

### Manutenibilidade

- ✅ Código modular
- ✅ Configuração centralizada
- ✅ Logging estruturado
- ✅ Documentação completa

### Ética

- ✅ Respeita robots.txt (responsabilidade do usuário)
- ✅ User-Agent identificável
- ✅ Delay configurável
- ✅ Limite de páginas

## 🛠️ Extensibilidade

### Fácil Adicionar

**Novo Formato de Arquivo**

```python
# Em src/, criar novo módulo: docx_extractor.py
class DocxExtractor:
    def extract(self, url):
        # Implementação
        pass
```

**Novo Storage Backend**

```python
# Substituir TinyDB por PostgreSQL, MongoDB, etc
class PostgresStorage(URLStorage):
    def __init__(self, connection_string):
        # Implementação
        pass
```

**Filtros Customizados**

```python
# Em utils.py, adicionar validações
def should_process_url(url, custom_rules):
    # Lógica customizada
    pass
```

## 📊 Métricas e Monitoramento

O sistema rastreia automaticamente:

- ✅ URLs processadas (sucesso/falha)
- ✅ Tipos de conteúdo encontrados
- ✅ Tempo de processamento
- ✅ Tamanho de dados extraídos
- ✅ Erros e exceções

## 🎓 Aprendizados do Projeto

### Design Patterns Utilizados

- **Strategy**: Diferentes extractors (HTML, PDF)
- **Factory**: Criação de storage backends
- **Observer**: Sistema de logging
- **Singleton**: Configurações

### Princípios SOLID

- **S**: Cada módulo tem responsabilidade única
- **O**: Fácil estender sem modificar código base
- **L**: Interfaces consistentes
- **I**: Interfaces específicas por tipo
- **D**: Depende de abstrações, não implementações

## 🚦 Status do Projeto

| Componente     | Status             | Notas               |
|----------------|--------------------|---------------------|
| Crawling       | ✅ Completo         | Funcional e testado |
| HTML Scraping  | ✅ Completo         | BeautifulSoup4      |
| PDF Extraction | ✅ Completo         | PyPDF2 + pdfplumber |
| Storage        | ✅ Completo         | TinyDB              |
| Logging        | ✅ Completo         | Python logging      |
| CLI            | ✅ Completo         | argparse            |
| Documentação   | ✅ Completo         | README, guias       |
| Testes         | ⚠️ Básico          | example_usage.py    |
| CI/CD          | ❌ Não implementado | -                   |

## 🔮 Roadmap Futuro

### Curto Prazo

- [ ] Suporte a JavaScript/SPA (Selenium)
- [ ] OCR para PDFs escaneados
- [ ] Mais tipos de arquivo (DOCX, XLSX)
- [ ] Testes unitários completos

### Médio Prazo

- [ ] Interface web (Flask/FastAPI)
- [ ] Paralelização (asyncio/multiprocessing)
- [ ] Cache inteligente
- [ ] Suporte a sitemaps

### Longo Prazo

- [ ] Scraping distribuído
- [ ] ML para detecção de conteúdo relevante
- [ ] Suporte a autenticação
- [ ] Plugin system

## 📚 Recursos de Aprendizado

Para entender melhor o projeto, estude:

1. **Web Scraping**: BeautifulSoup, requests
2. **Crawling**: BFS/DFS em grafos
3. **RAG**: Retrieval-Augmented Generation
4. **Vector Databases**: Embeddings, similaridade
5. **LLMs**: LangChain, LlamaIndex

## 🤝 Contribuindo

Este é um projeto educacional e open-source. Contribuições são bem-vindas!

---

**Desenvolvido com ❤️ para facilitar a construção de sistemas RAG**

*Versão: 1.0.0*  
*Última atualização: Outubro 2025*
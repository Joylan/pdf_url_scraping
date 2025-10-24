# 🚀 Guia Rápido de Início

Comece a usar o RAG Crawler em 5 minutos!

## ⚡ Instalação Rápida

```bash
# 1. Clone ou crie o diretório
mkdir rag-crawler && cd rag-crawler

# 2. Crie os arquivos do projeto
# (cole todos os arquivos fornecidos na estrutura correta)

# 3. Crie ambiente virtual
python -m venv venv

# 4. Ative o ambiente
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 5. Instale dependências
pip install -r requirements.txt
```

## 🎯 Uso Básico

### Executar Crawler

```bash
# Crawling simples
python main.py --url https://python.org

# Com mais controle
python main.py --url https://python.org --max-depth 2 --max-pages 50

# Recomeçar do zero
python main.py --url https://python.org --reset
```

### Ver Resultados

```bash
# Texto extraído
cat data/text_output.txt

# ou no Windows
type data\text_output.txt

# URLs processadas
cat data/crawled_urls.json
```

## 📚 Exemplos Práticos

### Exemplo 1: Documentação de Biblioteca

```bash
# Extrair documentação do Requests
python main.py --url https://requests.readthedocs.io --max-depth 3
```

### Exemplo 2: Blog ou Site de Notícias

```bash
# Extrair artigos
python main.py --url https://realpython.com --max-depth 2 --max-pages 30
```

### Exemplo 3: Site Corporativo

```bash
# Extrair conteúdo institucional
python main.py --url https://suaempresa.com.br --max-depth 4
```

## 🧪 Testar Módulos

```bash
# Executar exemplos interativos
python example_usage.py
```

Escolha opções:

- **1**: Crawler completo (faz requisições reais)
- **2**: Scraping de página única
- **3**: Extração de PDF
- **4**: Ver URLs processadas
- **5**: Ler texto extraído
- **6**: Preparar para RAG

## 🤖 Integrar com RAG

### Opção 1: LangChain (Recomendado)

```bash
pip install langchain langchain-openai faiss-cpu
```

```python
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

os.environ['OPENAI_API_KEY'] = 'sua-chave'

# Carregar texto
with open('data/text_output.txt') as f:
    text = f.read()

# Criar vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([text], embeddings)

# Buscar
docs = vectorstore.similarity_search("sua pergunta", k=3)
print(docs[0].page_content)
```

### Opção 2: LlamaIndex

```bash
pip install llama-index
```

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
import os

os.environ['OPENAI_API_KEY'] = 'sua-chave'

# Carregar
with open('data/text_output.txt') as f:
    text = f.read()

# Criar índice
doc = Document(text=text)
index = VectorStoreIndex.from_documents([doc])

# Query
query_engine = index.as_query_engine()
response = query_engine.query("sua pergunta")
print(response)
```

### Opção 3: Local (Sem API)

```bash
pip install sentence-transformers chromadb
```

```python
from sentence_transformers import SentenceTransformer
import chromadb

# Modelo local
model = SentenceTransformer('all-MiniLM-L6-v2')

# ChromaDB local
client = chromadb.Client()
collection = client.create_collection("docs")

# Carregar e indexar
with open('data/text_output.txt') as f:
    text = f.read()

collection.add(
    documents=[text],
    ids=["doc1"]
)

# Buscar
results = collection.query(
    query_texts=["sua pergunta"],
    n_results=1
)
print(results['documents'][0])
```

## ⚙️ Configurações Comuns

### Ajustar Velocidade

Edite `config/settings.py`:

```python
# Mais rápido (use com cuidado!)
DELAY_BETWEEN_REQUESTS = 0.5

# Mais devagar (mais respeitoso)
DELAY_BETWEEN_REQUESTS = 2
```

### Aumentar Limite de Páginas

```python
MAX_PAGES = 500  # Padrão: 100
MAX_DEPTH = 5  # Padrão: 3
```

### Ignorar Mais Tipos de Arquivo

```python
IGNORED_EXTENSIONS = {
    '.jpg', '.png', '.gif',  # Imagens
    '.mp4', '.avi',  # Vídeos
    '.zip', '.rar',  # Arquivos
    '.xml', '.json'  # Adicione mais conforme necessário
}
```

## 🐛 Solução de Problemas

### Erro: "No module named 'lxml'"

```bash
pip install lxml
```

### Erro: "SSL Certificate Verify Failed"

```python
# Em config/settings.py, adicione:
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
```

### PDFs não são extraídos

- Verifique se o PDF não está protegido
- Alguns PDFs são imagens escaneadas (sem texto)
- Tente reduzir `MAX_PDF_SIZE_MB`

### Muitas URLs ignoradas

- Verifique se são do mesmo domínio
- Revise `IGNORED_EXTENSIONS`
- Use `--max-depth` maior

### Texto estranho no output

- Alguns sites têm muito JavaScript
- Tente adicionar mais tags para remover em `scraper.py`:

```python
for element in soup(['script', 'style', 'nav', 'footer',
                     'header', 'aside', 'noscript', 'iframe',
                     'button', 'form']):  # Adicione mais aqui
    element.decompose()
```

## 📊 Monitoramento

### Ver Progresso em Tempo Real

```bash
# Em outro terminal
tail -f logs/crawler.log
```

### Estatísticas

```python
from src.storage import URLStorage, TextStorage
from config.settings import CRAWLED_URLS_DB, TEXT_OUTPUT_FILE

url_storage = URLStorage(CRAWLED_URLS_DB)
text_storage = TextStorage(TEXT_OUTPUT_FILE)

print(f"URLs processadas: {url_storage.get_processed_count()}")
print(f"Tamanho do arquivo: {text_storage.get_file_size() / 1024:.2f} KB")
```

## 🎓 Próximos Passos

1. ✅ Execute o crawler no seu site alvo
2. ✅ Verifique o texto extraído em `data/text_output.txt`
3. ✅ Escolha uma biblioteca RAG (LangChain, LlamaIndex, etc)
4. ✅ Crie embeddings e vector store
5. ✅ Configure seu LLM
6. ✅ Construa sua aplicação RAG!

## 📚 Documentação Completa

- **README.md**: Documentação completa
- **RAG_INTEGRATION.md**: Guia detalhado de integração RAG
- **example_usage.py**: Exemplos de código

## 💡 Dicas Rápidas

- **Comece pequeno**: Use `--max-pages 10` para testar
- **Respeite robots.txt**: Sempre verifique permissões
- **Use delays**: Evite sobrecarregar servidores
- **Monitore logs**: Acompanhe o progresso
- **Teste incremental**: Não precisa resetar sempre

## 🆘 Precisa de Ajuda?

1. Revise os logs em `logs/crawler.log`
2. Execute `python example_usage.py` para testar módulos
3. Verifique a seção de Troubleshooting acima
4. Consulte o README.md completo

---

**Pronto! Você está preparado para começar! 🎉**
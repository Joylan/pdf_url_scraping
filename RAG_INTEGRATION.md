# Guia de Integração com RAG

Este guia mostra como integrar o texto extraído pelo crawler com sistemas RAG (Retrieval-Augmented Generation).

## 📋 Índice

1. [Preparação dos Dados](#preparação-dos-dados)
2. [Integração com LangChain](#integração-com-langchain)
3. [Integração com LlamaIndex](#integração-com-llamaindex)
4. [Vetorização Custom](#vetorização-custom)
5. [Melhores Práticas](#melhores-práticas)

---

## Preparação dos Dados

### 1. Carregar e Parsear o Texto Extraído

```python
from pathlib import Path


def load_documents(text_file='data/text_output.txt'):
    """Carrega e parseia documentos do arquivo de texto"""

    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Divide por separador
    separator = "=" * 80
    raw_docs = content.split(separator)

    documents = []
    for doc in raw_docs:
        if 'URL:' not in doc or not doc.strip():
            continue

        lines = doc.strip().split('\n')

        # Parse metadados
        metadata = {}
        metadata['url'] = lines[0].replace('URL:', '').strip()
        metadata['type'] = lines[1].replace('Tipo:', '').strip()
        metadata['timestamp'] = lines[2].replace('Extraído em:', '').strip()

        # Extrai texto
        text = '\n'.join(lines[3:]).strip()

        if text:
            documents.append({
                'text': text,
                'metadata': metadata
            })

    return documents


# Usar
docs = load_documents()
print(f"Carregados {len(docs)} documentos")
```

---

## Integração com LangChain

### Instalação

```bash
pip install langchain langchain-openai faiss-cpu
# ou para GPU: faiss-gpu
```

### Exemplo Completo

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import os

# Configurar API key
os.environ['OPENAI_API_KEY'] = 'sua-chave-aqui'


def create_vectorstore_langchain(text_file='data/text_output.txt'):
    """Cria vector store com LangChain"""

    # 1. Carregar documentos
    raw_docs = load_documents(text_file)

    # 2. Converter para formato LangChain
    langchain_docs = []
    for doc in raw_docs:
        langchain_docs.append(
            Document(
                page_content=doc['text'],
                metadata=doc['metadata']
            )
        )

    # 3. Dividir em chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    splits = text_splitter.split_documents(langchain_docs)
    print(f"Documentos divididos em {len(splits)} chunks")

    # 4. Criar embeddings e vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)

    # 5. Salvar para uso posterior
    vectorstore.save_local("vectorstore_faiss")
    print("✓ Vector store salvo em: vectorstore_faiss/")

    return vectorstore


# Criar vector store
vectorstore = create_vectorstore_langchain()

# Usar para busca
query = "Como fazer crawling de páginas?"
docs = vectorstore.similarity_search(query, k=3)

for i, doc in enumerate(docs, 1):
    print(f"\n--- Resultado {i} ---")
    print(f"URL: {doc.metadata.get('url', 'N/A')}")
    print(f"Texto: {doc.page_content[:200]}...")
```

### RAG Completo com LangChain

```python
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA


def setup_rag_chain(vectorstore):
    """Configura cadeia RAG completa"""

    # Configurar LLM
    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0
    )

    # Criar retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    # Criar cadeia RAG
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain


# Usar
vectorstore = FAISS.load_local("vectorstore_faiss", OpenAIEmbeddings())
qa_chain = setup_rag_chain(vectorstore)

# Fazer perguntas
result = qa_chain({"query": "Como extrair texto de PDFs?"})
print(f"Resposta: {result['result']}")
print(f"\nFontes: {[doc.metadata['url'] for doc in result['source_documents']]}")
```

---

## Integração com LlamaIndex

### Instalação

```bash
pip install llama-index llama-index-embeddings-openai
```

### Exemplo Completo

```python
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import os

os.environ['OPENAI_API_KEY'] = 'sua-chave-aqui'


def create_index_llamaindex(text_file='data/text_output.txt'):
    """Cria índice com LlamaIndex"""

    # 1. Carregar documentos
    raw_docs = load_documents(text_file)

    # 2. Converter para formato LlamaIndex
    llamaindex_docs = []
    for doc in raw_docs:
        llamaindex_docs.append(
            Document(
                text=doc['text'],
                metadata=doc['metadata']
            )
        )

    print(f"Carregados {len(llamaindex_docs)} documentos")

    # 3. Configurar embeddings e LLM
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model="gpt-4", temperature=0)

    # 4. Criar índice
    index = VectorStoreIndex.from_documents(
        llamaindex_docs,
        show_progress=True
    )

    # 5. Persistir
    index.storage_context.persist(persist_dir="./storage_llamaindex")
    print("✓ Índice salvo em: storage_llamaindex/")

    return index


# Criar índice
index = create_index_llamaindex()

# Criar query engine
query_engine = index.as_query_engine(
    similarity_top_k=3,
    response_mode="compact"
)

# Fazer pergunta
response = query_engine.query("Qual a profundidade máxima de crawling?")
print(f"Resposta: {response}")

# Ver fontes
for node in response.source_nodes:
    print(f"\nFonte: {node.metadata['url']}")
    print(f"Score: {node.score:.3f}")
```

### Chat Engine com LlamaIndex

```python
from llama_index.core.memory import ChatMemoryBuffer

# Criar chat engine com memória
memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    similarity_top_k=3
)

# Conversa interativa
print("Chat iniciado. Digite 'sair' para encerrar.\n")

while True:
    user_input = input("Você: ")
    if user_input.lower() in ['sair', 'exit', 'quit']:
        break

    response = chat_engine.chat(user_input)
    print(f"\nAssistente: {response}\n")
```

---

## Vetorização Custom

### Com Sentence Transformers (Local)

```bash
pip install sentence-transformers chromadb
```

```python
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings


def create_chroma_db(text_file='data/text_output.txt'):
    """Cria banco vetorial local com ChromaDB"""

    # 1. Carregar modelo de embeddings local
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 2. Inicializar ChromaDB
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_db"
    ))

    collection = client.get_or_create_collection(
        name="rag_crawler_docs",
        metadata={"hnsw:space": "cosine"}
    )

    # 3. Carregar e processar documentos
    raw_docs = load_documents(text_file)

    # 4. Dividir em chunks
    chunks = []
    metadatas = []
    ids = []

    for idx, doc in enumerate(raw_docs):
        text = doc['text']

        # Chunk simples por tamanho
        chunk_size = 1000
        for i in range(0, len(text), chunk_size - 200):  # overlap de 200
            chunk = text[i:i + chunk_size]
            if len(chunk.strip()) > 100:  # Ignora chunks muito pequenos
                chunks.append(chunk)
                metadatas.append(doc['metadata'])
                ids.append(f"doc{idx}_chunk{i}")

    print(f"Processando {len(chunks)} chunks...")

    # 5. Criar embeddings
    embeddings = model.encode(chunks, show_progress_bar=True)

    # 6. Adicionar ao ChromaDB
    collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

    print(f"✓ {len(chunks)} chunks indexados em ChromaDB")

    return collection, model


# Usar
collection, model = create_chroma_db()

# Buscar
query = "Como funciona o scraping de PDF?"
query_embedding = model.encode([query])

results = collection.query(
    query_embeddings=query_embedding.tolist(),
    n_results=3
)

for i, (doc, metadata) in enumerate(zip(results['documents'][0],
                                        results['metadatas'][0]), 1):
    print(f"\n--- Resultado {i} ---")
    print(f"URL: {metadata['url']}")
    print(f"Texto: {doc[:200]}...")
```

### Com Pinecone (Cloud)

```bash
pip install pinecone-client openai
```

```python
from pinecone import Pinecone, ServerlessSpec
import openai
import os

os.environ['PINECONE_API_KEY'] = 'sua-chave-aqui'
os.environ['OPENAI_API_KEY'] = 'sua-chave-aqui'


def create_pinecone_index(text_file='data/text_output.txt'):
    """Cria índice no Pinecone"""

    # 1. Inicializar Pinecone
    pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

    index_name = "rag-crawler"

    # 2. Criar índice se não existir
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI ada-002
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )

    index = pc.Index(index_name)

    # 3. Carregar documentos
    raw_docs = load_documents(text_file)

    # 4. Processar e fazer upload
    client = openai.OpenAI()

    vectors = []
    for idx, doc in enumerate(raw_docs):
        # Criar embedding
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc['text'][:8000]  # Limite de tokens
        )

        embedding = response.data[0].embedding

        # Preparar vetor
        vectors.append({
            'id': f'doc_{idx}',
            'values': embedding,
            'metadata': {
                **doc['metadata'],
                'text': doc['text'][:1000]  # Limite de metadata
            }
        })

        # Upload em batches
        if len(vectors) >= 100:
            index.upsert(vectors=vectors)
            vectors = []
            print(f"Processados {idx + 1} documentos...")

    # Upload restante
    if vectors:
        index.upsert(vectors=vectors)

    print(f"✓ Índice criado no Pinecone: {index_name}")

    return index


# Usar
index = create_pinecone_index()

# Buscar
query = "Como configurar o crawler?"
client = openai.OpenAI()

query_embedding = client.embeddings.create(
    model="text-embedding-ada-002",
    input=query
).data[0].embedding

results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)

for match in results['matches']:
    print(f"\nScore: {match['score']:.3f}")
    print(f"URL: {match['metadata']['url']}")
    print(f"Texto: {match['metadata']['text'][:200]}...")
```

---

## Melhores Práticas

### 1. Chunking Inteligente

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter


def smart_chunking(documents, chunk_size=1000, chunk_overlap=200):
    """Chunking com preservação de contexto"""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",  # Parágrafos
            "\n",  # Linhas
            ". ",  # Sentenças
            "! ",
            "? ",
            ", ",
            " ",
            ""
        ]
    )

    all_chunks = []
    for doc in documents:
        chunks = splitter.split_text(doc['text'])

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'text': chunk,
                'metadata': {
                    **doc['metadata'],
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                }
            })

    return all_chunks
```

### 2. Enriquecimento de Metadados

```python
def enrich_metadata(documents):
    """Adiciona metadados úteis"""

    for doc in documents:
        text = doc['text']
        metadata = doc['metadata']

        # Adicionar estatísticas
        metadata['char_count'] = len(text)
        metadata['word_count'] = len(text.split())

        # Extrair domínio
        from urllib.parse import urlparse
        domain = urlparse(metadata['url']).netloc
        metadata['domain'] = domain

        # Identificar tipo de conteúdo
        if 'documentation' in text.lower() or 'docs' in metadata['url']:
            metadata['content_category'] = 'documentation'
        elif 'tutorial' in text.lower() or 'guide' in text.lower():
            metadata['content_category'] = 'tutorial'
        else:
            metadata['content_category'] = 'general'

    return documents
```

### 3. Filtros de Busca

```python
def search_with_filters(vectorstore, query, filters=None):
    """Busca com filtros de metadados"""

    # Exemplo com LangChain FAISS
    if filters:
        # Filtrar por tipo
        if 'type' in filters:
            docs = vectorstore.similarity_search(
                query,
                k=10,
                filter=lambda metadata: metadata.get('type') == filters['type']
            )

        # Filtrar por domínio
        elif 'domain' in filters:
            docs = vectorstore.similarity_search(
                query,
                k=10,
                filter=lambda metadata: filters['domain'] in metadata.get('url', '')
            )
    else:
        docs = vectorstore.similarity_search(query, k=4)

    return docs


# Usar
results = search_with_filters(
    vectorstore,
    "Como fazer crawling?",
    filters={'type': 'html'}
)
```

### 4. Re-ranking

```bash
pip install sentence-transformers
```

```python
from sentence_transformers import CrossEncoder


def rerank_results(query, documents, top_k=3):
    """Re-ranking com cross-encoder para melhor relevância"""

    model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    # Preparar pares query-documento
    pairs = [[query, doc['text']] for doc in documents]

    # Calcular scores
    scores = model.predict(pairs)

    # Ordenar por score
    ranked = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [doc for doc, score in ranked[:top_k]]


# Usar
initial_results = vectorstore.similarity_search(query, k=10)
final_results = rerank_results(query, initial_results, top_k=3)
```

### 5. Atualização Incremental

```python
def incremental_update(vectorstore, text_file='data/text_output.txt'):
    """Atualiza vector store com novos documentos"""

    # Carregar documentos processados
    current_docs = load_documents(text_file)

    # Verificar quais são novos (baseado em timestamp ou URL)
    # ... lógica para identificar novos documentos ...

    # Adicionar apenas novos
    new_docs = [doc for doc in current_docs if is_new(doc)]

    if new_docs:
        # Converter e adicionar
        langchain_docs = [
            Document(page_content=doc['text'], metadata=doc['metadata'])
            for doc in new_docs
        ]

        # Adicionar ao vector store existente
        vectorstore.add_documents(langchain_docs)

        print(f"✓ Adicionados {len(new_docs)} novos documentos")
    else:
        print("✓ Nenhum documento novo")
```

---

## Pipeline Completo Exemplo

```python
# pipeline_rag.py
"""Pipeline completo: Crawler → Vector Store → RAG"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.crawler import WebCrawler
from src.storage import URLStorage, TextStorage
from config.settings import CRAWLED_URLS_DB, TEXT_OUTPUT_FILE
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document


def full_pipeline(url, max_pages=50):
    """Pipeline completo end-to-end"""

    print("=" * 60)
    print("PIPELINE RAG COMPLETO")
    print("=" * 60)

    # 1. CRAWLING
    print("\n[1/4] Executando crawling...")
    url_storage = URLStorage(CRAWLED_URLS_DB)
    text_storage = TextStorage(TEXT_OUTPUT_FILE)

    crawler = WebCrawler(url_storage, text_storage, max_pages=max_pages)
    try:
        crawler.crawl(url)
    finally:
        crawler.close()

    # 2. PREPARAÇÃO DOS DADOS
    print("\n[2/4] Preparando dados...")
    docs = load_documents(TEXT_OUTPUT_FILE)
    print(f"✓ {len(docs)} documentos carregados")

    # 3. VETORIZAÇÃO
    print("\n[3/4] Criando vector store...")
    langchain_docs = [
        Document(page_content=doc['text'], metadata=doc['metadata'])
        for doc in docs
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(langchain_docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local("vectorstore")
    print(f"✓ {len(splits)} chunks indexados")

    # 4. RAG
    print("\n[4/4] Configurando RAG...")
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True
    )

    print("\n" + "=" * 60)
    print("✓ Pipeline completo!")
    print("=" * 60)

    return qa_chain


# Executar
if __name__ == '__main__':
    qa_chain = full_pipeline('https://example.com', max_pages=20)

    # Testar
    result = qa_chain({"query": "Resuma o conteúdo principal do site"})
    print(f"\n{result['result']}")
```

---

## Recursos Adicionais

- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Pinecone Docs](https://docs.pinecone.io/)
- [ChromaDB Docs](https://docs.trychroma.com/)

---

**Pronto para RAG! 🚀**
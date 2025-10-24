# Makefile para RAG Crawler
# Facilita comandos comuns do projeto

.PHONY: help install setup clean test crawl reset stats

# Variáveis
PYTHON := python
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Comando padrão
help:
	@echo "RAG Crawler - Comandos Disponíveis:"
	@echo ""
	@echo "  make install    - Cria venv e instala dependências"
	@echo "  make setup      - Executa script de setup"
	@echo "  make clean      - Remove arquivos temporários"
	@echo "  make reset      - Limpa dados e logs"
	@echo "  make test       - Executa exemplos de teste"
	@echo "  make crawl URL=<url> - Executa crawler"
	@echo "  make stats      - Mostra estatísticas"
	@echo "  make logs       - Mostra logs em tempo real"
	@echo ""

# Instalação
install:
	@echo "Criando ambiente virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "Instalando dependências..."
	$(PIP) install -r requirements.txt
	@echo "✓ Instalação concluída!"

# Setup do projeto
setup:
	$(PYTHON) setup.py

# Limpeza
clean:
	@echo "Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "✓ Limpeza concluída!"

# Reset completo
reset:
	@echo "⚠ ATENÇÃO: Isso vai apagar todos os dados extraídos!"
	@read -p "Tem certeza? (s/N): " confirm && [ "$$confirm" = "s" ]
	rm -rf data/crawled_urls.json
	rm -rf data/text_output.txt
	rm -rf data/pdfs/*
	rm -rf logs/*
	@echo "✓ Dados resetados!"

# Testes
test:
	$(PYTHON_VENV) example_usage.py

# Crawling
crawl:
ifndef URL
	@echo "✗ Erro: URL não especificada"
	@echo "Uso: make crawl URL=https://example.com"
else
	$(PYTHON_VENV) main.py --url $(URL) $(ARGS)
endif

# Estatísticas
stats:
	@echo "=== Estatísticas do Crawler ==="
	@echo ""
	@if [ -f data/crawled_urls.json ]; then \
		echo "URLs processadas: $$(cat data/crawled_urls.json | grep -o '"url"' | wc -l)"; \
	else \
		echo "URLs processadas: 0"; \
	fi
	@if [ -f data/text_output.txt ]; then \
		echo "Tamanho do texto: $$(wc -c < data/text_output.txt | numfmt --to=iec-i --suffix=B)"; \
		echo "Linhas: $$(wc -l < data/text_output.txt)"; \
	else \
		echo "Nenhum texto extraído ainda"; \
	fi
	@echo ""

# Logs em tempo real
logs:
	tail -f logs/crawler.log

# Exemplos de uso
example-basic:
	$(PYTHON_VENV) main.py --url https://example.com --max-pages 5

example-docs:
	$(PYTHON_VENV) main.py --url https://docs.python.org --max-depth 2 --max-pages 20

# Desenvolvimento
dev-install:
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 pytest

lint:
	$(VENV)/bin/flake8 src/ --max-line-length=100
	$(VENV)/bin/black --check src/

format:
	$(VENV)/bin/black src/
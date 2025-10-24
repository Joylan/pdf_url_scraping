"""
Script de setup e verificação do ambiente
"""
import platform
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Verifica versão do Python"""
    print("Verificando versão do Python...")
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ é necessário")
        print(f"  Versão atual: {version.major}.{version.minor}.{version.micro}")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_directories():
    """Cria estrutura de diretórios"""
    print("Criando estrutura de diretórios...")

    directories = [
        Path("config"),
        Path("src"),
        Path("data"),
        Path("data/pdfs"),
        Path("logs")
    ]

    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"✓ {directory}/")

    return True


def create_init_files():
    """Cria arquivos __init__.py"""
    print("\nCriando arquivos __init__.py...")

    init_files = [
        Path("config/__init__.py"),
        Path("src/__init__.py")
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"✓ {init_file}")
        else:
            print(f"○ {init_file} (já existe)")

    return True


def check_requirements():
    """Verifica se requirements.txt existe"""
    print("\nVerificando requirements.txt...")

    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("✗ requirements.txt não encontrado")
        return False

    print("✓ requirements.txt encontrado")
    return True


def install_dependencies():
    """Instala dependências"""
    print("\nDeseja instalar as dependências agora? (s/n): ", end="")
    response = input().strip().lower()

    if response != 's':
        print("⚠ Pule esta etapa por enquanto")
        print("  Execute manualmente: pip install -r requirements.txt")
        return True

    print("\nInstalando dependências...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError:
        print("✗ Erro ao instalar dependências")
        print("  Tente manualmente: pip install -r requirements.txt")
        return False


def verify_imports():
    """Verifica se os módulos principais podem ser importados"""
    print("\nVerificando importações...")

    modules = [
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("PyPDF2", "PyPDF2"),
        ("pdfplumber", "pdfplumber"),
        ("tinydb", "tinydb"),
    ]

    all_ok = True
    for module_name, package_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} não encontrado")
            all_ok = False

    return all_ok


def check_project_files():
    """Verifica se os arquivos principais do projeto existem"""
    print("\nVerificando arquivos do projeto...")

    required_files = [
        "main.py",
        "config/settings.py",
        "src/crawler.py",
        "src/scraper.py",
        "src/pdf_extractor.py",
        "src/storage.py",
        "src/utils.py"
    ]

    all_ok = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} não encontrado")
            all_ok = False

    return all_ok


def create_env_file():
    """Cria arquivo .env se não existir"""
    print("\nVerificando arquivo .env...")

    env_file = Path(".env")
    if env_file.exists():
        print("○ .env já existe")
        return True

    print("Criando .env de exemplo...")
    env_content = """# Configurações do RAG Crawler
MAX_DEPTH=3
MAX_PAGES=100
DELAY_BETWEEN_REQUESTS=1
TIMEOUT=10
MAX_PDF_SIZE_MB=50
"""

    env_file.write_text(env_content)
    print("✓ .env criado")
    return True


def create_gitignore():
    """Cria .gitignore se não existir"""
    print("\nVerificando .gitignore...")

    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        print("○ .gitignore já existe")
        return True

    print("Criando .gitignore...")
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Projeto
data/
logs/
*.log
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Vector stores
vectorstore/
vectorstore_faiss/
storage_llamaindex/
chroma_db/
"""

    gitignore_file.write_text(gitignore_content)
    print("✓ .gitignore criado")
    return True


def run_test_import():
    """Testa importação dos módulos do projeto"""
    print("\nTestando importação dos módulos do projeto...")

    try:
        from config import settings
        print("✓ config.settings")

        from src import crawler, scraper, pdf_extractor, storage, utils
        print("✓ src.crawler")
        print("✓ src.scraper")
        print("✓ src.pdf_extractor")
        print("✓ src.storage")
        print("✓ src.utils")

        return True
    except ImportError as e:
        print(f"✗ Erro ao importar: {e}")
        return False


def print_next_steps():
    """Imprime próximos passos"""
    print_header("SETUP CONCLUÍDO!")

    print("Próximos passos:")
    print("\n1. Ative o ambiente virtual (se ainda não estiver ativo):")

    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")

    print("\n2. Execute o crawler:")
    print("   python main.py --url https://example.com")

    print("\n3. Veja os exemplos:")
    print("   python example_usage.py")

    print("\n4. Consulte a documentação:")
    print("   - README.md: Documentação completa")
    print("   - QUICKSTART.md: Guia rápido")
    print("   - RAG_INTEGRATION.md: Integração com RAG")

    print("\n" + "=" * 60)
    print("Boa sorte com seu projeto RAG! 🚀")
    print("=" * 60 + "\n")


def main():
    """Função principal do setup"""
    print_header("RAG CRAWLER - SETUP")

    print("Este script vai verificar e preparar o ambiente.\n")

    checks = [
        ("Versão do Python", check_python_version),
        ("Estrutura de diretórios", create_directories),
        ("Arquivos __init__.py", create_init_files),
        ("Requirements.txt", check_requirements),
    ]

    # Executar verificações básicas
    for name, check_func in checks:
        if not check_func():
            print(f"\n✗ Falha em: {name}")
            print("Por favor, corrija os problemas acima e execute novamente.")
            return False

    # Instalar dependências
    if not install_dependencies():
        print("\n⚠ Continue mesmo sem instalar as dependências agora")

    # Verificações adicionais
    verify_imports()
    check_project_files()
    create_env_file()
    create_gitignore()

    # Teste final
    print("\n" + "-" * 60)
    run_test_import()
    print("-" * 60)

    # Próximos passos
    print_next_steps()

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Setup interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

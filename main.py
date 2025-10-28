"""Script principal do crawler com interface gráfica"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import logging
import shutil
import threading
from urllib.parse import urlparse

# PyQt6 Imports
from PyQt6 import QtWidgets, QtCore, QtGui

# Tentativa de importar de config.settings, se falhar, usa valores padrão
try:
    from config.settings import (
        CRAWLED_URLS_DB, TEXT_OUTPUT_FILE, LOG_FILE, PDF_DIR,
        MAX_DEPTH as DEFAULT_MAX_DEPTH, MAX_PAGES as DEFAULT_MAX_PAGES
    )
except ImportError:
    # Fallback se config.settings não for encontrado (ex: rodando standalone)
    from pathlib import Path

    print("Aviso: config/settings.py não encontrado. Usando valores padrão.")
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    PDF_DIR = DATA_DIR / "pdfs"

    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    PDF_DIR.mkdir(exist_ok=True)

    CRAWLED_URLS_DB = DATA_DIR / "crawled_urls.json"
    TEXT_OUTPUT_FILE = DATA_DIR / "text_output.txt"
    LOG_FILE = LOGS_DIR / "crawler.log"

# Tentativa de importar os módulos src
try:
    from src.crawler import WebCrawler
    from src.storage import URLStorage, TextStorage
    from src.utils import setup_logging
except ImportError:
    print("ERRO CRÍTICO: Módulos 'src' não encontrados. Verifique a estrutura do projeto.")


    def setup_logging(file, level):
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        print(f"Logging 'dummy' configurado para {file}")

# Configurar logging ANTES de qualquer outra coisa
setup_logging(LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__)


class TextHandler(logging.Handler, QtCore.QObject):
    """Handler customizado para redirecionar logs para widget de texto (Qt)"""
    log_signal = QtCore.pyqtSignal(str)

    def __init__(self, text_widget):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.log_signal.connect(self.append_log)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

    def append_log(self, msg):
        self.text_widget.setReadOnly(False)
        self.text_widget.append(msg)
        self.text_widget.setReadOnly(True)
        self.text_widget.moveCursor(QtGui.QTextCursor.MoveOperation.End)


class CrawlerGUI(QtWidgets.QWidget):
    """Interface gráfica para o crawler (PyQt6)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Web Crawler RAG - Multi URL")
        self.resize(1100, 800)
        self.setMinimumSize(800, 600)

        # Temas
        self.colors = {
            'bg_light': '#f0f8ff',  # Fundo principal (AliceBlue)
            'bg_medium': '#ffffff',  # Fundo de campos (Branco)
            'bg_dark': '#d4eaf7',  # Cor de calha / borda sutil
            'accent': '#007bff',  # Azul primário (Bootstrap)
            'accent_light': '#5cadff',  # Azul mais claro
            'text': '#052c65',  # Texto (Azul escuro)
            'text_dark': '#4a6984'  # Texto secundário (Azul acinzentado)
        }

        self.crawler_thread = None
        self.crawler = None
        self.is_running = False
        self.urls_list = []

        self.setup_ui()
        self.setup_logging_handler()

    def setup_ui(self):
        """Configura a interface gráfica (PyQt6)"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {self.colors['bg_light']};
                color: {self.colors['text']};
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 13pt;
            }}
            QGroupBox {{
                border: 2px solid {self.colors['accent']};
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 15pt;
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 3px 0 3px;
                color: {self.colors['accent']};
                background: {self.colors['bg_light']};
            }}
            QPushButton {{
                background: {self.colors['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background: {self.colors['bg_light']};
                color: {self.colors['text_dark']};
            }}
            QPushButton:hover {{
                background: {self.colors['accent_light']};
            }}
            QLineEdit, QSpinBox {{
                background: {self.colors['bg_medium']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                border-radius: 4px;
                font-size: 13pt;
            }}
            QListWidget {{
                background: {self.colors['bg_medium']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                font-size: 13pt;
            }}
            QProgressBar {{
                background: {self.colors['bg_dark']};
                border-radius: 5px;
                text-align: center;
                height: 18px;
            }}
            QProgressBar::chunk {{
                background: {self.colors['accent']};
                border-radius: 5px;
            }}
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Frame de URLs
        url_group = QtWidgets.QGroupBox("URLs para Crawling")
        url_layout = QtWidgets.QVBoxLayout(url_group)
        main_layout.addWidget(url_group)

        # Lista de URLs
        self.urls_listbox = QtWidgets.QListWidget()
        self.urls_listbox.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.urls_listbox.setMinimumHeight(40)
        url_layout.addWidget(self.urls_listbox)

        # Botões de gerenciamento de URLs
        url_btns = QtWidgets.QHBoxLayout()
        url_layout.addLayout(url_btns)
        btn_add = QtWidgets.QPushButton("➕ Adicionar URL")
        btn_add.clicked.connect(self.add_url)
        url_btns.addWidget(btn_add)
        btn_load = QtWidgets.QPushButton("📄 Carregar Arquivo")
        btn_load.clicked.connect(self.load_urls_from_file)
        url_btns.addWidget(btn_load)
        btn_remove = QtWidgets.QPushButton("🗑 Remover Selecionadas")
        btn_remove.clicked.connect(self.remove_urls)
        url_btns.addWidget(btn_remove)
        btn_clear_db = QtWidgets.QPushButton("🧹 Limpar Base de Dados")
        btn_clear_db.clicked.connect(self.clear_database)
        url_btns.addWidget(btn_clear_db)

        # Frame de configurações
        config_group = QtWidgets.QGroupBox("Configurações")
        config_layout = QtWidgets.QGridLayout(config_group)
        main_layout.addWidget(config_group)

        label_maxpages = QtWidgets.QLabel("Máx. Páginas:")
        label_maxpages.setFont(QtGui.QFont("Segoe UI", 13, QtGui.QFont.Weight.Bold))
        config_layout.addWidget(label_maxpages, 0, 0)
        self.max_pages_spinbox = QtWidgets.QSpinBox()
        self.max_pages_spinbox.setMinimum(1)
        self.max_pages_spinbox.setMaximum(1000000)
        self.max_pages_spinbox.setValue(DEFAULT_MAX_PAGES)
        config_layout.addWidget(self.max_pages_spinbox, 0, 1)
        label_depth = QtWidgets.QLabel("Profundidade:")
        label_depth.setFont(QtGui.QFont("Segoe UI", 13, QtGui.QFont.Weight.Bold))
        config_layout.addWidget(label_depth, 0, 2)
        self.max_depth_spinbox = QtWidgets.QSpinBox()
        self.max_depth_spinbox.setMinimum(1)
        self.max_depth_spinbox.setMaximum(10)
        self.max_depth_spinbox.setValue(DEFAULT_MAX_DEPTH)
        config_layout.addWidget(self.max_depth_spinbox, 0, 3)

        # Botões de controle
        btns_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btns_layout)
        self.start_button = QtWidgets.QPushButton("▶ Iniciar Crawling")
        self.start_button.clicked.connect(self.start_crawling)
        btns_layout.addWidget(self.start_button)
        self.stop_button = QtWidgets.QPushButton("⏹ Parar")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_crawling)
        btns_layout.addWidget(self.stop_button)
        self.clear_button = QtWidgets.QPushButton("🗑 Limpar Log")
        self.clear_button.clicked.connect(self.clear_log)
        btns_layout.addWidget(self.clear_button)
        self.export_button = QtWidgets.QPushButton("💾 Exportar Texto Raspado")
        self.export_button.clicked.connect(self.export_text_output)
        btns_layout.addWidget(self.export_button)

        # Área de log
        log_group = QtWidgets.QGroupBox("Log de Execução")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        main_layout.addWidget(log_group, stretch=1)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QtGui.QFont("Consolas", 13))
        log_layout.addWidget(self.log_text)

        # Barra de progresso e label
        self.progress_label = QtWidgets.QLabel("Aguardando início...")
        self.progress_label.setFont(QtGui.QFont("Segoe UI", 11))
        main_layout.addWidget(self.progress_label)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)  # Indeterminate
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Status bar
        self.status_bar = QtWidgets.QLabel("Pronto | 0 URLs carregadas")
        self.status_bar.setStyleSheet(
            f"background: {self.colors['bg_dark']}; color: {self.colors['text_dark']}; padding: 2px 6px; font-size: 12pt;"
        )
        self.status_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.status_bar)

    def setup_logging_handler(self):
        """Configura handler para redirecionar logs para a GUI (Qt)"""
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(text_handler)

    def add_url(self):
        """Adiciona uma URL à lista (PyQt6)"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Adicionar URL")
        dialog.setFixedSize(550, 140)
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel("URL:")
        label.setFont(QtGui.QFont("Segoe UI", 13, QtGui.QFont.Weight.Bold))
        layout.addWidget(label)
        url_entry = QtWidgets.QLineEdit()
        url_entry.setText("https://divulga.unila.edu.br/laca")
        url_entry.setFont(QtGui.QFont("Segoe UI", 13))
        layout.addWidget(url_entry)
        btns = QtWidgets.QHBoxLayout()
        layout.addLayout(btns)
        btn_add = QtWidgets.QPushButton("Adicionar")
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btns.addWidget(btn_add)
        btns.addWidget(btn_cancel)
        url_entry.setFocus()

        def on_add():
            url = url_entry.text().strip()
            if url and url != "https://" and url.startswith(('http://', 'https://')):
                if url not in self.urls_list:
                    self.urls_list.append(url)
                    self.urls_listbox.addItem(url)
                    self.update_status()
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.warning(dialog, "Aviso", "Esta URL já está na lista!")
            else:
                QtWidgets.QMessageBox.critical(dialog, "Erro", "URL inválida!")

        btn_add.clicked.connect(on_add)
        btn_cancel.clicked.connect(dialog.reject)
        url_entry.returnPressed.connect(on_add)
        dialog.exec()

    def load_urls_from_file(self):
        """Carrega URLs de um arquivo de texto (PyQt6)"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Selecionar arquivo com URLs", "", "Arquivos de texto (*.txt);;Todos os arquivos (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                added = 0
                for line in lines:
                    url = line.strip()
                    if url and url.startswith(('http://', 'https://')) and url not in self.urls_list:
                        self.urls_list.append(url)
                        self.urls_listbox.addItem(url)
                        added += 1
                self.update_status()
                QtWidgets.QMessageBox.information(self, "Sucesso", f"{added} URLs adicionadas!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo:\n{e}")

    def remove_urls(self):
        """Remove URLs selecionadas (PyQt6)"""
        selected = self.urls_listbox.selectedIndexes()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Selecione URLs para remover!")
            return
        for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
            url = self.urls_listbox.item(idx.row()).text()
            self.urls_list.remove(url)
            self.urls_listbox.takeItem(idx.row())
        self.update_status()

    def clear_urls(self):
        """Limpa todas as URLs da lista (PyQt6)"""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirmar", "Limpar todas as URLs da lista?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.urls_list.clear()
            self.urls_listbox.clear()
            self.update_status()

    def clear_database(self):
        """Limpa toda a base de dados do crawling (PyQt6)"""
        msg = (
            "⚠️ ATENÇÃO ⚠️\n\n"
            "Esta ação irá DELETAR:\n"
            "• Banco de dados de URLs processadas\n"
            "• Arquivo de texto extraído\n"
            "• Todos os PDFs baixados\n"
            "• Arquivos de log\n\n"
            "Esta ação NÃO pode ser desfeita!\n\n"
            "Deseja continuar?"
        )
        reply = QtWidgets.QMessageBox.question(
            self, "⚠️ Confirmar Limpeza de Base de Dados", msg,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                deleted_items = []
                # Deletar banco de dados
                if CRAWLED_URLS_DB.exists():
                    CRAWLED_URLS_DB.unlink()
                    deleted_items.append("✓ Banco de dados de URLs")
                # Deletar arquivo de texto
                if TEXT_OUTPUT_FILE.exists():
                    TEXT_OUTPUT_FILE.unlink()
                    deleted_items.append("✓ Arquivo de texto extraído")
                # Deletar PDFs
                if PDF_DIR.exists():
                    pdf_count = len(list(PDF_DIR.glob("*.pdf")))
                    shutil.rmtree(PDF_DIR)
                    PDF_DIR.mkdir(exist_ok=True)
                    deleted_items.append(f"✓ {pdf_count} arquivo(s) PDF")
                # Deletar logs
                if LOG_FILE.exists():
                    LOG_FILE.unlink()
                    deleted_items.append("✓ Arquivos de log")
                # Reconfigurar logging após deletar o arquivo
                setup_logging(LOG_FILE, level=logging.INFO)
                self.setup_logging_handler()
                logger.info("=" * 70)
                logger.info("🗑️ BASE DE DADOS LIMPA COM SUCESSO")
                logger.info("=" * 70)
                for item in deleted_items:
                    logger.info(item)
                logger.info("=" * 70)
                QtWidgets.QMessageBox.information(
                    self, "Sucesso", f"Base de dados limpa com sucesso!\n\n" + "\n".join(deleted_items)
                )
            except Exception as e:
                logger.error(f"❌ Erro ao limpar base de dados: {e}")
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao limpar base de dados:\n{e}")

    def update_status(self):
        """Atualiza a barra de status (PyQt6)"""
        count = len(self.urls_list)
        self.status_bar.setText(
            f"Pronto | {count} URL{'s' if count != 1 else ''} carregada{'s' if count != 1 else ''}"
        )

    def start_crawling(self):
        """Inicia o processo de crawling (PyQt6)"""
        if not self.urls_list:
            QtWidgets.QMessageBox.critical(self, "Erro", "Adicione pelo menos uma URL para crawling!")
            return
        # Verificar se as classes 'dummy' estão sendo usadas
        if 'WebCrawler' not in globals() or WebCrawler.__module__ == '__main__':
            QtWidgets.QMessageBox.critical(self, "Erro Crítico",
                                           "Módulos 'src' não encontrados. A aplicação não pode iniciar o crawl.")
            return
        # Desabilitar controles
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.max_pages_spinbox.setEnabled(False)
        self.max_depth_spinbox.setEnabled(False)
        self.progress_label.setText(f"Crawling em andamento... ({len(self.urls_list)} URLs)")
        self.status_bar.setText("Executando...")
        self.progress.setVisible(True)
        # Iniciar crawler em thread separada
        self.is_running = True
        self.crawler_thread = threading.Thread(target=self.run_crawler, daemon=True)
        self.crawler_thread.start()

    def run_crawler(self):
        """Executa o crawler em thread separada (PyQt6)"""
        try:
            # Obter configurações
            max_pages = self.max_pages_spinbox.value()
            max_depth = self.max_depth_spinbox.value()
            # Inicializar storage (compartilhado entre todas as URLs)
            url_storage = URLStorage(CRAWLED_URLS_DB)
            text_storage = TextStorage(TEXT_OUTPUT_FILE)
            # Criar crawler
            self.crawler = WebCrawler(
                url_storage=url_storage,
                text_storage=text_storage,
                max_depth=max_depth,
                max_pages=max_pages
            )
            logger.info("=" * 70)
            logger.info(f"🚀 Iniciando crawling de {len(self.urls_list)} URLs")
            logger.info(f"📊 Limite global: {max_pages} páginas | Profundidade: {max_depth}")
            logger.info("=" * 70 + "\n")
            # Executar crawling para cada URL
            for idx, url in enumerate(self.urls_list, 1):
                if not self.is_running:
                    logger.info("\n⚠️  Crawling interrompido pelo usuário")
                    break
                # Verificar se ainda há páginas disponíveis
                total_processed = self.crawler.pages_processed + self.crawler.pdfs_processed
                if total_processed >= max_pages:
                    logger.info(f"\n⚠️  Limite global de {max_pages} páginas atingido")
                    break
                logger.info(f"\n{'─' * 70}")
                logger.info(f"📍 [{idx}/{len(self.urls_list)}] {url}")
                logger.info(f"{'─' * 70}")
                try:
                    # Restrinja crawling ao mesmo domínio/subdomínio da URL inicial
                    parsed_url = urlparse(url)
                    allowed_netloc = parsed_url.netloc

                    def url_filter(candidate):
                        return urlparse(candidate).netloc == allowed_netloc

                    self.crawler.crawl(url, url_filter=url_filter)
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {url}: {e}")
                    continue
            # Resumo final consolidado
            if self.is_running:
                logger.info("\n" + "=" * 70)
                logger.info("✅ CRAWLING COMPLETO")
                logger.info("=" * 70)
            # Chamar o 'on_crawling_complete' apenas se o loop terminou naturalmente
            if self.is_running:
                QtCore.QMetaObject.invokeMethod(self, "on_crawling_complete", QtCore.Qt.ConnectionType.QueuedConnection,
                                                QtCore.Q_ARG(bool, True), QtCore.Q_ARG(str, None))
        except Exception as e:
            logger.error(f"❌ Erro fatal durante o crawling: {e}")
            QtCore.QMetaObject.invokeMethod(self, "on_crawling_complete", QtCore.Qt.ConnectionType.QueuedConnection,
                                            QtCore.Q_ARG(bool, False), QtCore.Q_ARG(str, str(e)))
        finally:
            if self.crawler:
                self.crawler.close()
            if self.is_running:
                # Isso pode acontecer se houver um erro antes do loop principal
                QtCore.QMetaObject.invokeMethod(self, "on_crawling_complete", QtCore.Qt.ConnectionType.QueuedConnection,
                                                QtCore.Q_ARG(bool, False),
                                                QtCore.Q_ARG(str, "Erro na inicialização do crawler"))

    def stop_crawling(self):
        """Para o crawling (PyQt6)"""
        if self.is_running:
            self.is_running = False
            logger.info("\n⏹ Parando o crawling... Aguarde a finalização da tarefa atual.")
            self.stop_button.setEnabled(False)
            QtCore.QTimer.singleShot(100, lambda: self.on_crawling_complete(False, "Interrompido pelo usuário"))

    @QtCore.pyqtSlot(bool, str)
    def on_crawling_complete(self, success, error_msg):
        """Callback quando o crawling termina (PyQt6)"""
        if self.start_button.isEnabled():
            return  # Já foi finalizado e reabilitado
        self.is_running = False
        self.progress.setVisible(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.max_pages_spinbox.setEnabled(True)
        self.max_depth_spinbox.setEnabled(True)
        if success:
            self.progress_label.setText("✅ Crawling concluído com sucesso!")
            self.status_bar.setText(f"Concluído | {len(self.urls_list)} URLs processadas")
            QtWidgets.QMessageBox.information(self, "Sucesso", "Crawling concluído com sucesso!")
        else:
            self.progress_label.setText("❌ Crawling interrompido ou com erro")
            self.status_bar.setText("Interrompido/Erro")
            if error_msg == "Interrompido pelo usuário":
                logger.info("=" * 70)
                logger.info("⏹ Crawling interrompido pelo usuário.")
                logger.info("=" * 70)
            elif error_msg:
                if error_msg not in ("Erro ou Interrupção", "Erro na inicialização do crawler"):
                    QtWidgets.QMessageBox.critical(self, "Erro", f"Erro durante crawling:\n{error_msg}")
                elif error_msg == "Erro na inicialização do crawler":
                    logger.error(f"❌ {error_msg}")

    def clear_log(self):
        """Limpa o log da interface (PyQt6)"""
        self.log_text.setReadOnly(False)
        self.log_text.clear()
        self.log_text.setReadOnly(True)

    def export_text_output(self):
        """Exporta o conteúdo de TEXT_OUTPUT_FILE para um arquivo .txt escolhido pelo usuário"""
        if not TEXT_OUTPUT_FILE.exists():
            QtWidgets.QMessageBox.warning(self, "Aviso", "Nenhum texto raspado foi encontrado para exportar!")
            return
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Exportar Texto Raspado", "texto_raspado.txt", "Arquivos de texto (*.txt)"
        )
        if file_path:
            try:
                with open(TEXT_OUTPUT_FILE, "r", encoding="utf-8") as fin:
                    data = fin.read()
                with open(file_path, "w", encoding="utf-8") as fout:
                    fout.write(data)
                QtWidgets.QMessageBox.information(self, "Exportação concluída", f"Texto exportado para:\n{file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao exportar texto:\n{e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    gui = CrawlerGUI()
    main_window.setCentralWidget(gui)
    main_window.setWindowTitle(gui.windowTitle())
    main_window.resize(gui.width(), gui.height())
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

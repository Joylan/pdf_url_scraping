"""Script principal do crawler com interface gráfica"""
import logging
import shutil
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from config.settings import (
    CRAWLED_URLS_DB, TEXT_OUTPUT_FILE, LOG_FILE, PDF_DIR,
    MAX_DEPTH, MAX_PAGES
)
from src.crawler import WebCrawler
from src.storage import URLStorage, TextStorage
from src.utils import setup_logging

# Configurar logging ANTES de qualquer outra coisa
setup_logging(LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__)


class TextHandler(logging.Handler):
    """Handler customizado para redirecionar logs para widget de texto"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.see(tk.END)

        self.text_widget.after(0, append)


class CrawlerGUI:
    """Interface gráfica para o crawler"""

    def __init__(self, root):
        self.root = root
        self.root.title("Web Crawler RAG - Multi URL")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)

        # Configurar tema azul
        self.colors = {
            'bg_dark': '#0a1929',
            'bg_medium': '#1e3a5f',
            'bg_light': '#2d5a8c',
            'accent': '#3b82f6',
            'accent_light': '#60a5fa',
            'text': '#dbeafe',
            'text_dark': '#93c5fd'
        }

        self.root.configure(bg=self.colors['bg_dark'])

        self.crawler_thread = None
        self.crawler = None
        self.is_running = False
        self.urls_list = []

        self.setup_styles()
        self.setup_ui()
        self.setup_logging_handler()

    def setup_styles(self):
        """Configura estilos personalizados"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configurar cores do tema
        style.configure('.',
                        background=self.colors['bg_medium'],
                        foreground=self.colors['text'],
                        bordercolor=self.colors['accent'],
                        darkcolor=self.colors['bg_dark'],
                        lightcolor=self.colors['bg_light'],
                        troughcolor=self.colors['bg_dark'],
                        focuscolor=self.colors['accent'],
                        selectbackground=self.colors['accent'],
                        selectforeground='white',
                        fieldbackground=self.colors['bg_light'],
                        font=('Segoe UI', 13))

        # Frame
        style.configure('TFrame', background=self.colors['bg_dark'])

        # LabelFrame
        style.configure('TLabelframe',
                        background=self.colors['bg_dark'],
                        bordercolor=self.colors['accent'],
                        borderwidth=2)
        style.configure('TLabelframe.Label',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['accent_light'],
                        font=('Segoe UI', 14, 'bold'))

        # Label
        style.configure('TLabel',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['text'],
                        font=('Segoe UI', 13))

        # Button
        style.configure('TButton',
                        background=self.colors['accent'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        padding=10,
                        font=('Segoe UI', 13, 'bold'))
        style.map('TButton',
                  background=[('active', self.colors['accent_light']),
                              ('disabled', self.colors['bg_light'])],
                  foreground=[('disabled', self.colors['text_dark'])])

        # Entry
        style.configure('TEntry',
                        fieldbackground=self.colors['bg_light'],
                        foreground=self.colors['text'],
                        borderwidth=1,
                        insertcolor=self.colors['text'],
                        font=('Segoe UI', 13))

        # Spinbox
        style.configure('TSpinbox',
                        fieldbackground=self.colors['bg_light'],
                        foreground=self.colors['text'],
                        borderwidth=1,
                        arrowcolor=self.colors['accent'],
                        font=('Segoe UI', 13))

        # Progressbar
        style.configure('TProgressbar',
                        background=self.colors['accent'],
                        troughcolor=self.colors['bg_light'],
                        borderwidth=0,
                        thickness=10)

    def setup_ui(self):
        """Configura a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(5, weight=2)

        # Frame de URLs
        url_frame = ttk.LabelFrame(main_frame, text="URLs para Crawling", padding="15")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=1)

        # Lista de URLs
        urls_list_frame = ttk.Frame(url_frame)
        urls_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        urls_list_frame.columnconfigure(0, weight=1)
        urls_list_frame.rowconfigure(0, weight=1)

        self.urls_listbox = tk.Listbox(
            urls_list_frame, height=6, font=('Segoe UI', 13),
            selectmode=tk.EXTENDED,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            highlightbackground=self.colors['bg_medium']
        )
        self.urls_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(urls_list_frame, orient=tk.VERTICAL, command=self.urls_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.urls_listbox.config(yscrollcommand=scrollbar.set)

        # Botões de gerenciamento de URLs
        url_buttons_frame = ttk.Frame(url_frame)
        url_buttons_frame.grid(row=1, column=0, pady=10)

        ttk.Button(url_buttons_frame, text="➕ Adicionar URL", command=self.add_url, width=18).pack(side=tk.LEFT, padx=3)
        ttk.Button(url_buttons_frame, text="📄 Carregar Arquivo", command=self.load_urls_from_file, width=18).pack(
            side=tk.LEFT, padx=3)
        ttk.Button(url_buttons_frame, text="🗑 Remover Selecionadas", command=self.remove_urls, width=20).pack(
            side=tk.LEFT, padx=3)
        ttk.Button(url_buttons_frame, text="🧹 Limpar Base de Dados", command=self.clear_database, width=20).pack(
            side=tk.LEFT, padx=3)

        # Frame de configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="15")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)

        # Max páginas
        ttk.Label(config_frame, text="Máx. Páginas:", font=('Segoe UI', 13, 'bold')).grid(row=0, column=0, sticky=tk.W,
                                                                                          padx=8)
        self.max_pages_var = tk.IntVar(value=MAX_PAGES)
        self.max_pages_spinbox = ttk.Spinbox(
            config_frame, from_=1, to=1000, textvariable=self.max_pages_var, width=12
        )
        self.max_pages_spinbox.grid(row=0, column=1, sticky=tk.W, padx=8)

        # Max profundidade
        ttk.Label(config_frame, text="Profundidade:", font=('Segoe UI', 13, 'bold')).grid(row=0, column=2, sticky=tk.W,
                                                                                          padx=8)
        self.max_depth_var = tk.IntVar(value=MAX_DEPTH)
        self.max_depth_spinbox = ttk.Spinbox(
            config_frame, from_=1, to=10, textvariable=self.max_depth_var, width=12
        )
        self.max_depth_spinbox.grid(row=0, column=3, sticky=tk.W, padx=8)

        # Botões de controle
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=15)

        self.start_button = ttk.Button(
            button_frame, text="▶ Iniciar Crawling", command=self.start_crawling, width=22
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame, text="⏹ Parar", command=self.stop_crawling, width=22, state='disabled'
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(
            button_frame, text="🗑 Limpar Log", command=self.clear_log, width=22
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Barra de progresso
        self.progress_var = tk.StringVar(value="Aguardando início...")
        ttk.Label(main_frame, textvariable=self.progress_var, font=('Segoe UI', 11)).grid(
            row=4, column=0, sticky=tk.W, pady=5
        )

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(25, 5))

        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="Log de Execução", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, width=90, height=22,
            font=('Consolas', 13),
            bg='#0d1b2a',
            fg=self.colors['text'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            borderwidth=0,
            relief=tk.FLAT,
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar(value="Pronto | 0 URLs carregadas")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
            background=self.colors['bg_medium'],
            foreground=self.colors['text_dark'],
            font=('Segoe UI', 12)
        )
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def setup_logging_handler(self):
        """Configura handler para redirecionar logs para a GUI"""
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(text_handler)

    def add_url(self):
        """Adiciona uma URL à lista"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar URL")
        dialog.geometry("550x140")
        dialog.configure(bg=self.colors['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="URL:", font=('Segoe UI', 13, 'bold')).pack(pady=15, padx=15, anchor=tk.W)
        url_entry = ttk.Entry(dialog, width=65, font=('Segoe UI', 13))
        url_entry.pack(pady=5, padx=15, fill=tk.X)
        url_entry.insert(0, "https://divulga.unila.edu.br/laca")
        url_entry.focus()

        def on_add():
            url = url_entry.get().strip()
            if url and url != "https://" and url.startswith(('http://', 'https://')):
                if url not in self.urls_list:
                    self.urls_list.append(url)
                    self.urls_listbox.insert(tk.END, url)
                    self.update_status()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Aviso", "Esta URL já está na lista!")
            else:
                messagebox.showerror("Erro", "URL inválida!")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="Adicionar", command=on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        url_entry.bind('<Return>', lambda e: on_add())

    def load_urls_from_file(self):
        """Carrega URLs de um arquivo de texto"""
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo com URLs",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
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
                        self.urls_listbox.insert(tk.END, url)
                        added += 1

                self.update_status()
                messagebox.showinfo("Sucesso", f"{added} URLs adicionadas!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo:\n{e}")

    def remove_urls(self):
        """Remove URLs selecionadas"""
        selected = self.urls_listbox.curselection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione URLs para remover!")
            return

        for index in reversed(selected):
            url = self.urls_listbox.get(index)
            self.urls_list.remove(url)
            self.urls_listbox.delete(index)

        self.update_status()

    def clear_urls(self):
        """Limpa todas as URLs da lista"""
        if messagebox.askyesno("Confirmar", "Limpar todas as URLs da lista?"):
            self.urls_list.clear()
            self.urls_listbox.delete(0, tk.END)
            self.update_status()

    def clear_database(self):
        """Limpa toda a base de dados do crawling"""
        msg = "⚠️ ATENÇÃO ⚠️\n\n"
        msg += "Esta ação irá DELETAR:\n"
        msg += "• Banco de dados de URLs processadas\n"
        msg += "• Arquivo de texto extraído\n"
        msg += "• Todos os PDFs baixados\n"
        msg += "• Arquivos de log\n\n"
        msg += "Esta ação NÃO pode ser desfeita!\n\n"
        msg += "Deseja continuar?"

        if messagebox.askyesno("⚠️ Confirmar Limpeza de Base de Dados", msg, icon='warning'):
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

                messagebox.showinfo("Sucesso",
                                    f"Base de dados limpa com sucesso!\n\n" + "\n".join(deleted_items))

            except Exception as e:
                logger.error(f"❌ Erro ao limpar base de dados: {e}")
                messagebox.showerror("Erro", f"Erro ao limpar base de dados:\n{e}")

    def update_status(self):
        """Atualiza a barra de status"""
        count = len(self.urls_list)
        self.status_var.set(f"Pronto | {count} URL{'s' if count != 1 else ''} carregada{'s' if count != 1 else ''}")

    def start_crawling(self):
        """Inicia o processo de crawling"""
        if not self.urls_list:
            messagebox.showerror("Erro", "Adicione pelo menos uma URL para crawling!")
            return

        # Desabilitar controles
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.max_pages_spinbox.config(state='disabled')
        self.max_depth_spinbox.config(state='disabled')

        # Iniciar progress bar
        self.progress.start(10)
        self.progress_var.set(f"Crawling em andamento... ({len(self.urls_list)} URLs)")
        self.status_var.set("🔄 Executando...")

        # Iniciar crawler em thread separada
        self.is_running = True
        self.crawler_thread = threading.Thread(target=self.run_crawler, daemon=True)
        self.crawler_thread.start()

    def run_crawler(self):
        """Executa o crawler em thread separada"""
        try:
            # Obter configurações
            max_pages = self.max_pages_var.get()
            max_depth = self.max_depth_var.get()

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
                    self.crawler.crawl(url)
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {url}: {e}")
                    continue

            # Resumo final consolidado
            if self.is_running:
                logger.info("\n" + "=" * 70)
                logger.info("✅ CRAWLING COMPLETO")
                logger.info("=" * 70)
                self.crawler._print_summary()
                logger.info("=" * 70 + "\n")

            if self.is_running:
                self.root.after(0, self.on_crawling_complete, True, None)

        except Exception as e:
            logger.error(f"❌ Erro fatal durante o crawling: {e}")
            self.root.after(0, self.on_crawling_complete, False, str(e))
        finally:
            if self.crawler:
                self.crawler.close()

    def stop_crawling(self):
        """Para o crawling"""
        self.is_running = False
        self.on_crawling_complete(False, "Interrompido pelo usuário")

    def on_crawling_complete(self, success, error_msg):
        """Callback quando o crawling termina"""
        # Parar progress bar
        self.progress.stop()

        # Reabilitar controles
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.max_pages_spinbox.config(state='normal')
        self.max_depth_spinbox.config(state='normal')

        if success:
            self.progress_var.set("✅ Crawling concluído com sucesso!")
            self.status_var.set(f"✅ Concluído | {len(self.urls_list)} URLs processadas")
            messagebox.showinfo("Sucesso", "Crawling concluído com sucesso!")
        else:
            self.progress_var.set("❌ Crawling interrompido ou com erro")
            self.status_var.set("❌ Erro")
            if error_msg and error_msg != "Interrompido pelo usuário":
                messagebox.showerror("Erro", f"Erro durante crawling:\n{error_msg}")

    def clear_log(self):
        """Limpa o log da interface"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')


def main():
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

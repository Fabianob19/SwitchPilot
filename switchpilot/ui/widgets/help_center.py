import markdown
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QTextBrowser,
    QDialogButtonBox, QSplitter, QWidget
)
from PyQt5.QtCore import Qt
from switchpilot.utils.paths import get_resource_path


class HelpCenterDialog(QDialog):
    def __init__(self, parent=None, initial_topic="tutorial"):
        super().__init__(parent)
        self.setWindowTitle("Central de Ajuda - SwitchPilot")
        self.resize(1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from switchpilot.ui.widgets.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, None, height=32)
        # Help Center might be resizable, but let's hide max/min to be safe
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        main_layout.addWidget(self.title_bar)

        content_container = QWidget(self)
        self.layout = QVBoxLayout(content_container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(content_container)

        # Splitter Layout: Menu (Left) | Content (Right)
        self.splitter = QSplitter(Qt.Horizontal)

        # 1. Menu Lateral
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(220)
        self.menu_list.setObjectName("helpCenterMenu")
        self._populate_menu()
        self.menu_list.currentItemChanged.connect(self._on_topic_changed)

        # 2. Área de Conteúdo
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setObjectName("helpCenterContent")

        self.splitter.addWidget(self.menu_list)
        self.splitter.addWidget(self.content_browser)
        self.splitter.setStretchFactor(1, 1)  # Content expands

        self.layout.addWidget(self.splitter)

        # Botões
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        # Selecionar tópico inicial
        self._select_topic(initial_topic)

    def _populate_menu(self):
        """Define e adiciona os itens do menu."""
        self.topics = {
            "tutorial": ("📖 Tutorial Completo", "docs/help/tutorial.md"),
            "quick_guide": ("🚀 Guia Rápido", "docs/help/quick_guide.md"),
            "shortcuts": ("⌨️ Atalhos de Teclado", "docs/help/shortcuts.md"),
            "faq": ("❓ Perguntas Frequentes", "docs/help/faq.md"),
            "nsfw": ("🔞 Filtro NSFW (IA)", "docs/help/nsfw_filter.md"),
            "troubleshooting": ("🔧 Solução de Problemas", "docs/help/troubleshooting.md"),
            "requirements": ("💻 Requisitos", "docs/help/requirements.md"),
            "about": ("ℹ️ Sobre", "docs/help/about.md"),
        }

        for key, (label, _) in self.topics.items():
            # Armazena a chave (ex: 'tutorial') como dado oculto do item
            self.menu_list.addItem(label)
            item = self.menu_list.item(self.menu_list.count() - 1)
            item.setData(Qt.UserRole, key)

    def _select_topic(self, topic_key):
        """Seleciona programaticamente um tópico."""
        for i in range(self.menu_list.count()):
            item = self.menu_list.item(i)
            if item.data(Qt.UserRole) == topic_key:
                self.menu_list.setCurrentItem(item)
                break

    def _on_topic_changed(self, current, previous):
        if not current:
            return

        topic_key = current.data(Qt.UserRole)
        _, file_path = self.topics.get(topic_key)

        self._load_markdown(file_path)

    def _load_markdown(self, relative_path):
        """Lê o arquivo .md e converte para HTML."""
        try:
            # Resolve caminho absoluto baseado na raiz do projeto e PyInstaller
            full_path = get_resource_path(relative_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                md_text = f.read()

            # Converter Markdown para HTML
            html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])

            # Determinar se o tema atual é claro
            is_light = False
            if self.parent() and hasattr(self.parent(), 'current_theme_name'):
                is_light = self.parent().current_theme_name == "modern_light.qss"

            if is_light:
                css = """
                    body { font-family: 'Segoe UI', sans-serif; color: #1f2937; padding: 10px; }
                    h1 { color: #1e3a8a; font-size: 24px; margin-bottom: 20px; font-weight: 700; }
                    h2 { color: #2563eb; font-size: 18px; margin-top: 24px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
                    h3 { color: #16a34a; font-size: 16px; margin-top: 16px; font-weight: 600; }
                    p { line-height: 1.6; margin-bottom: 12px; font-size: 14px; }
                    li { margin-bottom: 6px; line-height: 1.5; font-size: 14px; }
                    code { background-color: #f3f4f6; color: #7f1d1d; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 13px; border: 1px solid #e5e7eb; }
                    pre { background-color: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e5e7eb; overflow-x: auto; }
                    pre code { background-color: transparent; color: #334155; border: none; padding: 0; }
                    strong { color: #0f172a; font-weight: 700; }
                    a { color: #2563eb; text-decoration: none; font-weight: 500; }
                    a:hover { text-decoration: underline; }
                    blockquote { border-left: 4px solid #3b82f6; padding-left: 14px; color: #4b5563; font-style: italic; background-color: #eff6ff; padding: 12px; border-radius: 0 6px 6px 0; margin: 16px 0; }
                """
            else:
                css = """
                    body { font-family: 'Segoe UI', sans-serif; color: #e2e8f0; padding: 10px; }
                    h1 { color: #60a5fa; font-size: 24px; margin-bottom: 20px; font-weight: 700; }
                    h2 { color: #93c5fd; font-size: 18px; margin-top: 24px; border-bottom: 2px solid #334155; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
                    h3 { color: #a7f3d0; font-size: 16px; margin-top: 16px; font-weight: 600; }
                    p { line-height: 1.6; margin-bottom: 12px; font-size: 14px; }
                    li { margin-bottom: 6px; line-height: 1.5; font-size: 14px; }
                    code { background-color: #1e293b; color: #fca5a5; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 13px; border: 1px solid #334155; }
                    pre { background-color: #0f172a; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; overflow-x: auto; }
                    pre code { background-color: transparent; color: #e2e8f0; border: none; padding: 0; }
                    strong { color: #f8fafc; font-weight: 700; }
                    a { color: #60a5fa; text-decoration: none; font-weight: 500; }
                    a:hover { text-decoration: underline; }
                    blockquote { border-left: 4px solid #3b82f6; padding-left: 14px; color: #cbd5e1; font-style: italic; background-color: #1e293b; padding: 12px; border-radius: 0 6px 6px 0; margin: 16px 0; }
                """

            # Estilização CSS baseada no tema
            styled_html = f"""
            <html>
            <head>
                <style>
                    {css}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            self.content_browser.setHtml(styled_html)

        except Exception as e:
            self.content_browser.setHtml(f"<h1>Erro ao carregar ajuda</h1><p>Não foi possível ler o arquivo: {relative_path}</p><p>Detalhe: {str(e)}</p>")

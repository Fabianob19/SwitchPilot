import os
import markdown
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QTextBrowser, 
    QDialogButtonBox, QSplitter
)
from PyQt5.QtCore import Qt
from switchpilot.utils.paths import get_resource_path


class HelpCenterDialog(QDialog):
    def __init__(self, parent=None, initial_topic="tutorial"):
        super().__init__(parent)
        self.setWindowTitle("Central de Ajuda - SwitchPilot")
        self.resize(1000, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Enable custom title bar integration check if needed, strictly minimal here

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Splitter Layout: Menu (Left) | Content (Right)
        self.splitter = QSplitter(Qt.Horizontal)

        # 1. Menu Lateral
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(220)
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: #2e3440;
                color: #d8dee9;
                border: 1px solid #3b4252;
                border-radius: 4px;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #5e81ac;
                color: #eceff4;
            }
            QListWidget::item:hover {
                background-color: #434c5e;
            }
        """)
        self._populate_menu()
        self.menu_list.currentItemChanged.connect(self._on_topic_changed)

        # 2. Área de Conteúdo
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #3b4252;
                color: #eceff4;
                border: 1px solid #4c566a;
                border-radius: 4px;
                padding: 20px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
        """)

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
            html_content = markdown.markdown(md_text)

            # Estilização CSS básica para o HTML renderizado
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; color: #eceff4; }}
                    h1 {{ color: #88c0d0; font-size: 24px; margin-bottom: 20px; }}
                    h2 {{ color: #81a1c1; font-size: 20px; margin-top: 20px; border-bottom: 1px solid #4c566a; padding-bottom: 5px; }}
                    h3 {{ color: #a3be8c; font-size: 18px; margin-top: 15px; }}
                    p {{ line-height: 1.6; margin-bottom: 10px; }}
                    li {{ margin-bottom: 5px; }}
                    code {{ background-color: #2e3440; padding: 2px 5px; border-radius: 3px; font-family: 'Consolas', monospace; color: #d8dee9; }}
                    strong {{ color: #ebcb8b; }}
                    a {{ color: #88c0d0; text-decoration: none; }}
                    blockquote {{ border-left: 4px solid #5e81ac; padding-left: 10px; color: #d8dee9; font-style: italic; background-color: #2e3440; padding: 10px; }}
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

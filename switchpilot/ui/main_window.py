import sys
import os  # Adicionado para construir caminhos de tema
import json
import shutil
import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDockWidget, QWidget,
                             QVBoxLayout, QLabel, QTextEdit, QMenuBar, QStatusBar, QAction, QSizePolicy, QActionGroup, QTabBar, QSystemTrayIcon, QMenu, QStyle, QPushButton, QFileDialog, QMessageBox, QDialog, QDialogButtonBox)
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QDesktopServices
from PyQt5.QtCore import Qt, QFile, QTextStream, QDir, QRect, QSettings, QTimer, QUrl, QPoint
# Importar os widgets
from switchpilot.ui.widgets.obs_config import OBSConfigWidget
from switchpilot.ui.widgets.vmix_config import VMixConfigWidget
from switchpilot.ui.widgets.reference_manager import ReferenceManagerWidget
from switchpilot.ui.widgets.monitoring_control_widget import MonitoringControlWidget
from switchpilot.ui.widgets.threshold_config_dialog import ThresholdConfigDialog
from switchpilot.ui.themes import THEME_LIGHT, THEME_DARK_DEFAULT, THEME_VERY_DARK
from switchpilot.ui.widgets.custom_title_bar import CustomTitleBar

# Configurações padrão da janela
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 700
DEFAULT_WINDOW_X = 100
DEFAULT_WINDOW_Y = 100

# --- Utilitário: Dark Title Bar no Windows ---


def enable_dark_title_bar_for_window(widget):
    try:
        if sys.platform != 'win32':
            return
        hwnd = int(widget.winId())
        # Tentar preferências de app escuras via uxtheme (não documentado, mas comum)
        try:
            uxtheme = ctypes.WinDLL('uxtheme')
            # SetPreferredAppMode(AllowDark=1)
            try:
                SetPreferredAppMode = uxtheme.SetPreferredAppMode
                SetPreferredAppMode.argtypes = [ctypes.c_int]
                SetPreferredAppMode.restype = ctypes.c_int
                SetPreferredAppMode(1)
            except Exception:
                pass
            # AllowDarkModeForWindow(hwnd, TRUE)
            try:
                from ctypes import wintypes as _wt
                AllowDarkModeForWindow = uxtheme.AllowDarkModeForWindow
                AllowDarkModeForWindow.argtypes = [_wt.HWND, _wt.BOOL]
                AllowDarkModeForWindow.restype = _wt.BOOL
                AllowDarkModeForWindow(hwnd, True)
            except Exception:
                pass
        except Exception:
            pass
        # DWM attribute (Win10 1809+/Win11)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        dwmapi = ctypes.WinDLL('dwmapi')
        DwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, wintypes.LPCVOID, wintypes.DWORD]
        DwmSetWindowAttribute.restype = wintypes.HRESULT
        hr = DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        if hr != 0:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 19
            DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        # Silencioso: se falhar, apenas ignora (sem crash)
        pass


def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com PyInstaller."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CaptureAreaOverlay(QWidget):
    def __init__(self, roi, kind, capture_id, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.roi = roi
        self.kind = kind
        self.capture_id = capture_id
        self._update_geometry()
        self.show()

    def _update_geometry(self):
        import mss
        import pyautogui
        if self.kind == 'monitor':
            with mss.mss() as sct:
                monitor = sct.monitors[self.capture_id]
                x = monitor['left'] + self.roi[0]
                y = monitor['top'] + self.roi[1]
                w = self.roi[2]
                h = self.roi[3]
                self.setGeometry(x, y, w, h)
        elif self.kind == 'window':
            win = self.capture_id
            if win:
                x = win.left + self.roi[0]
                y = win.top + self.roi[1]
                w = self.roi[2]
                h = self.roi[3]
                self.setGeometry(x, y, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(255, 0, 0, 180))  # Vermelho semi-transparente
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class MainWindow(QMainWindow):
    def __init__(self, version=None):
        super().__init__()
        self._version = version or ""
        title = "SwitchPilot"
        if self._version:
            title += f" - {self._version}"
        self.setWindowTitle(title)

        # Carregar configurações da janela
        self._load_window_settings()

        self.setWindowIcon(QIcon(resource_path('ICONE.ico')))  # Ícone da Janela

        self._is_quitting_via_tray = False  # Flag para controlar o fechamento real

        # Carregar tema padrão inicial (ou o último salvo no futuro)
        self.current_theme_name = THEME_VERY_DARK
        self._apply_theme_qss(self.current_theme_name)
        self._setup_ui()
        self._create_tray_icon()  # Configurar o ícone da bandeja

        # Ativar barra de título escura (Windows 10/11)
        enable_dark_title_bar_for_window(self)

    def _load_window_settings(self):
        """Carrega as configurações salvas da janela ou usa valores padrão"""
        try:
            config_path = "switchpilot_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                window_config = config.get('window_settings', {})
                x = window_config.get('x', DEFAULT_WINDOW_X)
                y = window_config.get('y', DEFAULT_WINDOW_Y)
                width = window_config.get('width', DEFAULT_WINDOW_WIDTH)
                height = window_config.get('height', DEFAULT_WINDOW_HEIGHT)

                # Validar valores para evitar janela fora da tela
                if width < 400:
                    width = DEFAULT_WINDOW_WIDTH
                if height < 300:
                    height = DEFAULT_WINDOW_HEIGHT
                if x < 0:
                    x = DEFAULT_WINDOW_X
                if y < 0:
                    y = DEFAULT_WINDOW_Y

                self.setGeometry(x, y, width, height)
                print(f"Configurações da janela carregadas: {width}x{height} na posição ({x}, {y})")
            else:
                # Primeira execução - usar tamanho otimizado
                self.setGeometry(DEFAULT_WINDOW_X, DEFAULT_WINDOW_Y, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
                print(f"Primeira execução - usando tamanho padrão: {DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        except Exception as e:
            print(f"Erro ao carregar configurações da janela: {e}")
            # Fallback para tamanho padrão
            self.setGeometry(DEFAULT_WINDOW_X, DEFAULT_WINDOW_Y, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    def _save_window_settings(self):
        """Salva as configurações atuais da janela"""
        try:
            config_path = "switchpilot_config.json"
            config = {}

            # Carregar configurações existentes
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # Atualizar configurações da janela
            geometry = self.geometry()
            config['window_settings'] = {
                'x': geometry.x(),
                'y': geometry.y(),
                'width': geometry.width(),
                'height': geometry.height()
            }

            # Salvar de volta
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"Configurações da janela salvas: {geometry.width()}x{geometry.height()} na posição ({geometry.x()}, {geometry.y()})")
        except Exception as e:
            print(f"Erro ao salvar configurações da janela: {e}")

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)

        icon_path = resource_path('ICONE.ico')
        if not os.path.exists(icon_path):
            print(f"Alerta: Ícone da bandeja não encontrado em {icon_path}. Usando ícone padrão do sistema.")
            # Tenta usar um ícone padrão do estilo atual do sistema se o arquivo não for encontrado
            standard_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)  # Exemplo, pode ser outro
            self.tray_icon.setIcon(standard_icon)
        else:
            self.tray_icon.setIcon(QIcon(icon_path))

        self.tray_icon.setToolTip("SwitchPilot")

        tray_menu = QMenu(self)  # Parent para garantir que o menu seja coletado pelo garbage collector

        self.toggle_visibility_action = QAction("Restaurar", self)
        self.toggle_visibility_action.triggered.connect(self._toggle_visibility)
        tray_menu.addAction(self.toggle_visibility_action)

        tray_menu.addSeparator()

        quit_action = QAction("Sair do SwitchPilot", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()

    def _on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visibility()
        elif reason == QSystemTrayIcon.Trigger:  # Clique simples
            # Poderia abrir o menu aqui também, ou fazer outra ação.
            # Por enquanto, o clique simples não fará nada além do menu de contexto já disponível.
            pass

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_visibility_action.setText("Restaurar")
            self.tray_icon.showMessage(
                "SwitchPilot",
                "O aplicativo foi minimizado para a bandeja.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.showNormal()
            self.activateWindow()  # Garante que a janela venha para frente
            self.raise_()      # Para macOS e alguns WMs Linux
            self.toggle_visibility_action.setText("Minimizar para Bandeja")

    def _quit_application(self):
        self._is_quitting_via_tray = True
        self.tray_icon.hide()  # Ocultar o ícone antes de sair
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self._is_quitting_via_tray:
            # Se estamos saindo explicitamente pelo menu da bandeja,
            # paramos o monitoramento e chamamos o closeEvent original.
            if hasattr(self, 'main_controller') and self.main_controller:
                if hasattr(self.main_controller, 'stop_monitoring_if_running'):
                    print("Parando monitoramento antes de sair...")
                    self.main_controller.stop_monitoring_if_running()

            # Salvar configurações da janela antes de sair
            self._save_window_settings()

            # Salvar configurações, etc.
            print("Saindo da aplicação...")
            super().closeEvent(event)
        else:
            # Se o usuário clicou no "X" da janela, minimizamos para a bandeja.
            event.ignore()
            self._toggle_visibility()  # Reutiliza a lógica de minimizar e mostrar mensagem

    def resizeEvent(self, event):
        """Salva configurações da janela quando redimensionada"""
        super().resizeEvent(event)
        # Salvar configurações após redimensionar (com pequeno delay para evitar muitas escritas)
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._save_window_settings)
        self._resize_timer.start(1000)  # Salva após 1 segundo de inatividade

    def moveEvent(self, event):
        """Salva configurações da janela quando movida"""
        super().moveEvent(event)
        # Salvar configurações após mover (com pequeno delay para evitar muitas escritas)
        if hasattr(self, '_move_timer'):
            self._move_timer.stop()
        else:
            self._move_timer = QTimer()
            self._move_timer.setSingleShot(True)
            self._move_timer.timeout.connect(self._save_window_settings)
        self._move_timer.start(1000)  # Salva após 1 segundo de inatividade

    def _get_theme_path(self, theme_name):
        base_path = "switchpilot/ui/themes/"
        if theme_name == THEME_LIGHT:
            return resource_path(os.path.join(base_path, "modern_light.qss"))
        elif theme_name == THEME_VERY_DARK:
            return resource_path(os.path.join(base_path, "modern_very_dark.qss"))
        elif theme_name == THEME_DARK_DEFAULT:
            return resource_path(os.path.join(base_path, "modern_dark_obs.qss"))
        return None

    def _apply_theme_qss(self, theme_name):
        """Carrega e aplica o arquivo QSS do tema especificado."""
        qss_path = self._get_theme_path(theme_name)
        if not qss_path:
            print(f"Erro: Nome do tema desconhecido '{theme_name}'")
            return False

        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            self.current_theme_name = theme_name
            print(f"Tema '{theme_name}' aplicado de '{qss_path}'.")
            return True
        except Exception as e:
            print(f"Erro ao carregar stylesheet do tema '{theme_name}': {qss_path}")
            print(f"Exceção: {e}")
            # Tentar recarregar o tema padrão como fallback se o tema atual falhar?
            if theme_name != THEME_DARK_DEFAULT:
                print("Tentando carregar tema padrão como fallback...")
                default_qss_path = self._get_theme_path(THEME_DARK_DEFAULT)
                try:
                    with open(default_qss_path, 'r', encoding='utf-8') as f:
                        self.setStyleSheet(f.read())
                    self.current_theme_name = THEME_DARK_DEFAULT
                    print(f"Tema padrão '{THEME_DARK_DEFAULT}' aplicado como fallback.")
                except Exception as e2:
                    print(f"Erro ao carregar fallback: {e2}")
            return False

    def _setup_ui(self):
        # Barra de Menu (custom, para integrar na barra personalizada)
        self._custom_menubar = QMenuBar(self)
        self._custom_menubar.setObjectName("TopMenuBar")
        file_menu = self._custom_menubar.addMenu("&Arquivo")
        view_menu = self._custom_menubar.addMenu("&Visualizar")

        # --- Menu Configurações e Aparência ---
        settings_menu = self._custom_menubar.addMenu("&Configurações")
        appearance_menu = settings_menu.addMenu("&Aparência")

        # Adicionar ação para limiares
        self.thresholds_action = QAction("Limiar de Similaridade...", self)
        self.thresholds_action.triggered.connect(self._open_thresholds_dialog)
        settings_menu.addAction(self.thresholds_action)
        settings_menu.addSeparator()

        theme_action_group = QActionGroup(self)  # Para garantir que apenas um tema seja "checado"
        theme_action_group.setExclusive(True)

        def create_theme_action(theme_name):
            action = QAction(theme_name, self, checkable=True)
            action.triggered.connect(lambda checked, tn=theme_name: self._on_theme_selected(tn) if checked else None)
            if theme_name == self.current_theme_name:
                action.setChecked(True)
            theme_action_group.addAction(action)
            appearance_menu.addAction(action)
            return action

        self.theme_light_action = create_theme_action(THEME_LIGHT)
        self.theme_dark_default_action = create_theme_action(THEME_DARK_DEFAULT)
        self.theme_very_dark_action = create_theme_action(THEME_VERY_DARK)
        # --- Fim Menu Configurações e Aparência ---

        help_menu = self._custom_menubar.addMenu("A&juda")

        # Itens de Arquivo
        import_action = QAction("Importar Configurações...", self)
        import_action.triggered.connect(self._import_config)
        export_action = QAction("Exportar Configurações...", self)
        export_action.triggered.connect(self._export_config)
        open_folder_action = QAction("Abrir Pasta do Aplicativo", self)
        open_folder_action.triggered.connect(self._open_app_folder)
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()

        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Itens de Ajuda
        quick_guide_action = QAction("Guia Rápido", self)
        quick_guide_action.triggered.connect(self._show_quick_guide)
        shortcuts_action = QAction("Atalhos de Teclado", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        changelog_action = QAction("Ver Changelog", self)
        changelog_action.triggered.connect(self._show_changelog)
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(quick_guide_action)
        help_menu.addAction(shortcuts_action)
        help_menu.addAction(changelog_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto")

        # Aplicar barra custom: tornar janela frameless e usar setMenuWidget
        try:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            # Remover menubar nativa da barra do sistema
            self.setMenuBar(None)
            # Container vertical com barra de título e menubar abaixo
            container = QWidget(self)
            v = QVBoxLayout(container)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(0)
            self._custom_title_bar = CustomTitleBar(self, None, height=32)
            v.addWidget(self._custom_title_bar)
            v.addWidget(self._custom_menubar)
            self.setMenuWidget(container)
        except Exception as e:
            print(f"[WARN] Falha ao aplicar barra personalizada: {e}")

        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)

        obs_config_dock = QDockWidget("Configuração OBS", self)
        self.obs_config_widget = OBSConfigWidget()
        obs_config_dock.setWidget(self.obs_config_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, obs_config_dock)
        view_menu.addAction(obs_config_dock.toggleViewAction())

        vmix_config_dock = QDockWidget("Configuração vMix", self)
        self.vmix_config_widget = VMixConfigWidget()
        vmix_config_dock.setWidget(self.vmix_config_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, vmix_config_dock)
        view_menu.addAction(vmix_config_dock.toggleViewAction())

        self.tabifyDockWidget(obs_config_dock, vmix_config_dock)
        obs_config_dock.raise_()

        # Tentar encontrar e nomear o QTabBar dos docks tabificados
        try:
            # Os QDockWidgets são agrupados em um QMainWindowPrivate::DockAreaTabBar
            # que é um QTabBar. Vamos procurar por QTabBar que são filhos diretos
            # de um contêiner de dock ou da própria QMainWindow.
            # Isso pode ser um pouco frágil dependendo da implementação interna do Qt.

            found_dock_tab_bar = False
            # É importante importar QTabBar se ainda não estiver no escopo local
            from PyQt5.QtWidgets import QTabBar

            for tab_bar in self.findChildren(QTabBar):
                parent_widget = tab_bar.parentWidget()
                # print(f"DEBUG: Encontrado QTabBar: {tab_bar}, Parent: {parent_widget}, Parent type: {type(parent_widget)}")

                is_likely_dock_tab_bar = False
                if parent_widget:
                    parent_class_name = parent_widget.metaObject().className()
                    # print(f"DEBUG: Parent class name: {parent_class_name}")
                    # Verificamos se o pai é um QDockWidget (quando apenas um dock está na área, antes de ser tabificado com outro)
                    # ou se é uma área de dock interna. A classe 'QMainWindowDockArea' não é exposta diretamente em PyQt.
                    # A classe 'DockAreaTabBar' também é interna.
                    # Uma heurística é verificar se o pai NÃO é um QTabWidget (para não pegar tab bars de QTabWidgets comuns)
                    # e se o tab_bar está diretamente sob a QMainWindow ou um widget genérico que serve de container para docks.
                    if not isinstance(parent_widget, QTextEdit) and not isinstance(parent_widget, QLabel):  # Evitar pegar QTabBar de widgets que não são containers de dock
                        # Se o parent_widget for um QDockWidget, significa que o QTabBar é o título do próprio dock,
                        # o que não é o que queremos aqui (já é estilizado por QDockWidget::title).
                        # O QTabBar que gerencia múltiplos docks agrupados geralmente não tem um QDockWidget como pai direto.
                        # Ele é filho de um widget interno da QMainWindow.
                        # Vamos tentar uma verificação mais simples: se o parent não é um QTabWidget e
                        # se este tab_bar tem um número de abas correspondente aos docks que acabamos de agrupar (2 neste caso)
                        # e não é um QTabBar que já tem um objectName (para evitar re-nomear multiplas vezes).
                        if not parent_widget.metaObject().className() == "QTabWidget" and tab_bar.objectName() == "":
                            # Esta é a verificação mais crítica:
                            # O QTabBar dos docks tabificados geralmente NÃO é filho direto dos QDockWidgets.
                            # Ele é filho de um widget interno da QMainWindow (frequentemente um QAbstractScrollArea ou similar,
                            # ou um widget privado como QMainWindowDockArea).
                            # Vamos assumir que o primeiro QTabBar sem nome de objeto e que não é de um QTabWidget é o candidato.
                            # Para o nosso caso específico, após tabifyDockWidget(obs_config_dock, vmix_config_dock),
                            # deve haver um QTabBar gerenciando estas duas abas.

                            # Verificando os filhos da QMainWindow
                            if parent_widget == self or parent_widget.parentWidget() == self:  # Um pouco mais direto
                                tab_bar.setObjectName("CentralDockTabBar")
                                print(f"DEBUG: QTabBar dos docks (possivelmente) encontrado e nomeado 'CentralDockTabBar': {tab_bar} com pai {parent_widget}")
                                self._apply_theme_qss(self.current_theme_name)
                                found_dock_tab_bar = True
                                break
                            else:  # Tentar uma busca mais genérica se a anterior falhar
                                # Se o QTabBar não tem um QTabWidget como pai, é um bom candidato
                                if tab_bar.parentWidget() and tab_bar.parentWidget().metaObject().className() != "QTabWidget":
                                    tab_bar.setObjectName("CentralDockTabBar")
                                    print(f"DEBUG: QTabBar dos docks (heurística genérica) encontrado e nomeado 'CentralDockTabBar': {tab_bar} com pai {parent_widget}")
                                    self._apply_theme_qss(self.current_theme_name)
                                    found_dock_tab_bar = True
                                    break

            if not found_dock_tab_bar:
                print("DEBUG: QTabBar dos docks não foi encontrado programaticamente com as heurísticas atuais.")

        except Exception as e:
            print(f"DEBUG: Erro ao tentar encontrar/nomear QTabBar dos docks: {e}")

        self.reference_manager_dock_widget = QDockWidget("Gerenciador de Referências", self)
        self.reference_manager_widget = ReferenceManagerWidget(main_controller=None)
        self.reference_manager_dock_widget.setWidget(self.reference_manager_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.reference_manager_dock_widget)
        view_menu.addAction(self.reference_manager_dock_widget.toggleViewAction())

        self.monitoring_control_dock_panel = QDockWidget("Monitoramento & Controle", self)
        self.monitoring_control_dock_panel.setObjectName("monitoringControlDock")
        self.monitoring_control_widget = MonitoringControlWidget(self.monitoring_control_dock_panel)
        self.monitoring_control_dock_panel.setWidget(self.monitoring_control_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.monitoring_control_dock_panel)
        view_menu.addAction(self.monitoring_control_dock_panel.toggleViewAction())

        # Garante que o MainController use sempre a instância correta do MonitoringControlWidget
        if hasattr(self, 'main_controller') and self.main_controller:
            self.main_controller.mon_control_widget = self.monitoring_control_widget
            self.main_controller._connect_ui_signals()

        # Ação para exibir área de captura
        self.show_capture_area_action = QAction("Exibir Área de Captura", self, checkable=True)
        self.show_capture_area_action.setChecked(False)
        self.show_capture_area_action.toggled.connect(self._toggle_capture_area_overlay)
        view_menu.addAction(self.show_capture_area_action)

        # Restaurar layout padrão
        view_menu.addSeparator()
        self.restore_layout_action = QAction("Restaurar Layout Padrão", self)
        self.restore_layout_action.triggered.connect(self._restore_default_layout)
        view_menu.addAction(self.restore_layout_action)

        # Salva estado inicial do layout para restauração futura
        try:
            self._default_dock_state = self.saveState()
        except Exception:
            self._default_dock_state = None

    def _on_theme_selected(self, theme_name):
        if self._apply_theme_qss(theme_name):
            # Desmarcar a ação do tema antigo e marcar a nova se o apply_theme_qss for bem-sucedido
            # A lógica do QActionGroup já deve cuidar disso se setChecked for chamado no apply bem-sucedido,
            # mas podemos garantir aqui.
            # O QActionGroup já garante que apenas uma ação é checada.
            # Precisamos apenas garantir que a ação correta esteja checada se a aplicação do tema for bem-sucedida.
            if theme_name == THEME_LIGHT:
                self.theme_light_action.setChecked(True)
            elif theme_name == THEME_DARK_DEFAULT:
                self.theme_dark_default_action.setChecked(True)
            elif theme_name == THEME_VERY_DARK:
                self.theme_very_dark_action.setChecked(True)
            print(f"Ação do menu para o tema '{theme_name}' marcada.")
        else:
            # Se a aplicação do novo tema falhar, reverter para o tema anterior visualmente no menu
            print(f"Falha ao aplicar tema '{theme_name}'. Revertendo seleção do menu para '{self.current_theme_name}'.")
            if self.current_theme_name == THEME_LIGHT:
                self.theme_light_action.setChecked(True)
            elif self.current_theme_name == THEME_DARK_DEFAULT:
                self.theme_dark_default_action.setChecked(True)
            elif self.current_theme_name == THEME_VERY_DARK:
                self.theme_very_dark_action.setChecked(True)

    def set_main_controller_for_widgets(self, main_controller):
        self.main_controller = main_controller  # <--- ESSENCIAL para funcionamento dos slots!
        if hasattr(self.reference_manager_widget, 'set_main_controller'):
            self.reference_manager_widget.set_main_controller(main_controller)
        if hasattr(self.obs_config_widget, 'set_main_controller'):
            self.obs_config_widget.set_main_controller(main_controller)
        if hasattr(self.vmix_config_widget, 'set_main_controller'):
            self.vmix_config_widget.set_main_controller(main_controller)
        if hasattr(self.monitoring_control_widget, 'set_main_controller'):
            self.monitoring_control_widget.set_main_controller(main_controller)

    def _open_thresholds_dialog(self):
        # Pega os valores atuais do MainController se possível
        static_val = 0.90
        seq_val = 0.90
        interval_val = 0.5
        if hasattr(self, 'main_controller') and self.main_controller:
            static_val = getattr(self.main_controller, 'current_static_threshold', 0.90)
            seq_val = getattr(self.main_controller, 'current_sequence_threshold', 0.90)
            interval_val = getattr(self.main_controller, 'current_monitor_interval', 0.5)
        dialog = ThresholdConfigDialog(static_value=static_val, sequence_value=seq_val, interval_value=interval_val, parent=self)
        # Conectar o sinal para atualizar os limiares imediatamente ao clicar OK
        print("[DEBUG] Conectando sinal thresholds_updated do diálogo ao slot on_thresholds_updated")

        def on_thresholds_updated(static_new, seq_new, interval_new):
            print(f"[DEBUG] Sinal thresholds_updated recebido: static={static_new}, seq={seq_new}, interval={interval_new}")
            if hasattr(self, 'main_controller') and self.main_controller:
                self.main_controller.update_static_threshold(static_new)
                self.main_controller.update_sequence_threshold(seq_new)
                self.main_controller.update_monitor_interval(interval_new)
        dialog.thresholds_updated.connect(on_thresholds_updated)
        dialog.exec_()

    def _toggle_capture_area_overlay(self, checked):
        if checked:
            # Pega a ROI e detalhes do MainController
            if hasattr(self, 'main_controller') and self.main_controller and getattr(self.main_controller, 'pgm_details', None):
                pgm = self.main_controller.pgm_details
                roi = pgm.get('roi')
                kind = pgm.get('kind')
                capture_id = pgm.get('id')
                if roi and kind and capture_id is not None:
                    self._capture_area_overlay = CaptureAreaOverlay(roi, kind, capture_id)
                else:
                    self.show_capture_area_action.setChecked(False)
        else:
            if hasattr(self, '_capture_area_overlay') and self._capture_area_overlay:
                self._capture_area_overlay.close()
                self._capture_area_overlay = None

    def _restore_default_layout(self):
        if getattr(self, '_default_dock_state', None):
            try:
                self.restoreState(self._default_dock_state)
                self.statusBar().showMessage("Layout restaurado.", 2000)
            except Exception as e:
                QMessageBox.warning(self, "Restaurar Layout", f"Falha ao restaurar layout: {e}")
        else:
            QMessageBox.information(self, "Restaurar Layout", "Estado padrão do layout não disponível nesta sessão.")

    def _import_config(self):
        src, _ = QFileDialog.getOpenFileName(self, "Importar Configurações", "", "JSON (*.json)")
        if not src:
            return
        try:
            shutil.copyfile(src, "switchpilot_config.json")
            QMessageBox.information(self, "Importar Configurações", "Configurações importadas com sucesso. Algumas alterações podem exigir reiniciar.")
        except Exception as e:
            QMessageBox.critical(self, "Importar Configurações", f"Falha ao importar: {e}")

    def _export_config(self):
        dst, _ = QFileDialog.getSaveFileName(self, "Exportar Configurações", "switchpilot_config.json", "JSON (*.json)")
        if not dst:
            return
        try:
            if os.path.exists("switchpilot_config.json"):
                shutil.copyfile("switchpilot_config.json", dst)
            else:
                # Se não existir, cria um mínimo com janela atual
                geometry = self.geometry()
                config = {
                    'window_settings': {
                        'x': geometry.x(), 'y': geometry.y(), 'width': geometry.width(), 'height': geometry.height()
                    }
                }
                with open(dst, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Exportar Configurações", "Arquivo exportado com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Exportar Configurações", f"Falha ao exportar: {e}")

    def _open_app_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath('.')))

    def _show_quick_guide(self):
        text = (
            "Como funciona a detecção:\n"
            "- S (0–1) é média ponderada de Hist, NCC e LBP.\n"
            "- Dispara quando S ≥ Limiar.\n\n"
            "Dicas rápidas:\n"
            "- Aumente o limiar para mais precisão; diminua para mais sensibilidade.\n"
            "- Intervalo menor = resposta mais rápida (maior uso de CPU).\n"
        )
        QMessageBox.information(self, "Guia Rápido", text)

    def _show_shortcuts(self):
        text = (
            "Atalhos úteis:\n"
            "- Limiar de Similaridade…: menu Configurações\n"
            "- Exibir Área de Captura: menu Visualizar\n"
            "- Sair: Arquivo → Sair\n"
        )
        QMessageBox.information(self, "Atalhos de Teclado", text)

    def _show_changelog(self):
        path = resource_path('CHANGELOG.md') if os.path.exists('CHANGELOG.md') else None
        if not path:
            QMessageBox.information(self, "Changelog", "Arquivo CHANGELOG.md não encontrado.")
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Janela simples de leitura
            dlg = QDialog(self)
            dlg.setWindowTitle("Changelog")
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            enable_dark_title_bar_for_window(dlg)
            layout = QVBoxLayout(dlg)
            te = QTextEdit(dlg)
            te.setReadOnly(True)
            te.setPlainText(content)
            layout.addWidget(te)
            buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dlg)
            buttons.rejected.connect(dlg.reject)
            buttons.accepted.connect(dlg.accept)
            layout.addWidget(buttons)
            dlg.resize(700, 500)
            dlg.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Changelog", f"Falha ao abrir changelog: {e}")

    def _show_about(self):
        version = self._version or ""
        text = f"SwitchPilot {version}\n© Seu time.\nPasta do app: {os.path.abspath('.')}"
        QMessageBox.information(self, "Sobre", text)

    def nativeEvent(self, eventType, message):
        try:
            if sys.platform == 'win32':
                import ctypes
                from ctypes import wintypes
                msg = ctypes.wintypes.MSG.from_address(message.__int__())
                WM_NCHITTEST = 0x0084
                if msg.message == WM_NCHITTEST:
                    pos = self.mapFromGlobal(QPoint(int(ctypes.c_short(msg.lParam & 0xFFFF).value), int(ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value)))
                    x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
                    margin = 6
                    if x < margin and y < margin:
                        return True, 13  # HTTOPLEFT
                    if x > w - margin and y < margin:
                        return True, 14  # HTTOPRIGHT
                    if x < margin and y > h - margin:
                        return True, 16  # HTBOTTOMLEFT
                    if x > w - margin and y > h - margin:
                        return True, 17  # HTBOTTOMRIGHT
                    if y < margin:
                        return True, 12  # HTTOP
                    if y > h - margin:
                        return True, 15  # HTBOTTOM
                    if x < margin:
                        return True, 10  # HTLEFT
                    if x > w - margin:
                        return True, 11  # HTRIGHT
                    # Área de arrasto: barra personalizada, exceto sobre botões
                    if hasattr(self, '_custom_title_bar') and self._custom_title_bar:
                        bar = self._custom_title_bar
                        top_left = bar.mapTo(self, QPoint(0, 0))
                        bar_rect = QRect(top_left, bar.size())
                        if bar_rect.contains(pos):
                            local = pos - top_left
                            try:
                                for btn in (bar.btn_min, bar.btn_max, bar.btn_close):
                                    if btn.geometry().contains(local):
                                        return True, 1  # HTCLIENT
                            except Exception:
                                pass
                            return True, 2  # HTCAPTION
        except Exception:
            pass
        return super().nativeEvent(eventType, message)


# Para teste rápido
if __name__ == '__main__':
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # Criar arquivos QSS de placeholder se não existirem para teste
    themes_dir = "switchpilot/ui/themes"
    os.makedirs(themes_dir, exist_ok=True)
    placeholder_qss_content = "/* Placeholder QSS File */\nQWidget { background-color: #cccccc; color: black; }\nQDockWidget::title { background-color: #aaaaaa; color: black; }"
    default_dark_qss_content = (
        "/* modern_dark_obs.qss - Conteúdo Padrão */\n"
        "QWidget { background-color: #2e3440; color: #eceff4; font-family: \"Segoe UI\"; font-size: 10pt; }\n"
        "QMainWindow { background-color: #2e3440; }\n"
        "QDockWidget::title { background-color: #3b4252; color: #eceff4; padding: 6px; border: 1px solid #4c566a; border-bottom: 1px solid #2e3440; font-weight: bold; font-size: 10pt; }\n"
        "QDockWidget > QWidget { background-color: #3b4252; border: 1px solid #4c566a; border-top: none; }\n"
        "QPushButton { background-color: #4c566a; color: #eceff4; border: 1px solid #5e81ac; padding: 8px 16px; border-radius: 4px; font-size: 10pt; }\n"
        "QPushButton:hover { background-color: #5e81ac; border: 1px solid #81a1c1; }\n"
        "QPushButton:pressed { background-color: #81a1c1; }\n"
        "QLineEdit { background-color: #2e3440; color: #eceff4; border: 1px solid #4c566a; border-radius: 3px; padding: 6px; font-size: 10pt; }\n"
        "QLabel { color: #eceff4; background-color: transparent; font-size: 10pt; }\n"
    )

    qss_files_to_check = {
        os.path.join(themes_dir, "modern_light.qss"): placeholder_qss_content.replace("#cccccc", "#f0f0f0").replace("#aaaaaa", "#d0d0d0"),  # Light theme
        os.path.join(themes_dir, "modern_dark_obs.qss"): default_dark_qss_content,
        os.path.join(themes_dir, "modern_very_dark.qss"): placeholder_qss_content.replace("#cccccc", "#1a1a1a").replace("#aaaaaa", "#101010").replace("black", "white")  # Very dark theme
    }

    for qss_file_path, content in qss_files_to_check.items():
        if not os.path.exists(qss_file_path):
            try:
                with open(qss_file_path, 'w') as f:
                    f.write(content)
                print(f"Arquivo QSS de placeholder criado: {qss_file_path}")
            except Exception as e:
                print(f"Falha ao criar QSS de placeholder '{qss_file_path}': {e}")

    main_win = MainWindow()
    main_win.show()

    class MockMainController:
        def __init__(self):
            self.obs_controller = None
            self.vmix_controller = None
            print("MockMainController instanciado para teste da UI.")

        def check_obs_connection(self): print("Mock OBS check"); return False, "Não conectado"
        def check_vmix_connection(self): print("Mock vMix check"); return False, "Não conectado"

    mock_controller = MockMainController()
    main_win.set_main_controller_for_widgets(mock_controller)

    if app is QApplication.instance() and sys.argv[0] == __file__ and not hasattr(sys, 'frozen'):
        sys.exit(app.exec_())

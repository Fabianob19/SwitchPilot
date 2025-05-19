import sys
import os # Adicionado para construir caminhos de tema
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDockWidget, QWidget, 
                             QVBoxLayout, QLabel, QTextEdit, QMenuBar, QStatusBar, QAction, QSizePolicy, QActionGroup, QTabBar, QSystemTrayIcon, QMenu, QStyle)
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QFile, QTextStream, QDir, QRect
# Importar os widgets
from switchpilot.ui.widgets.obs_config import OBSConfigWidget
from switchpilot.ui.widgets.vmix_config import VMixConfigWidget
from switchpilot.ui.widgets.reference_manager import ReferenceManagerWidget
from switchpilot.ui.widgets.monitoring_control_widget import MonitoringControlWidget
from switchpilot.ui.widgets.threshold_config_dialog import ThresholdConfigDialog

# Constantes para nomes de tema (para evitar strings mágicas)
THEME_LIGHT = "Claro"
THEME_DARK_DEFAULT = "Escuro (Padrão)"
THEME_VERY_DARK = "Muito Escuro"

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
        pen = QPen(QColor(255, 0, 0, 180)) # Vermelho semi-transparente
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwitchPilot")
        self.setGeometry(100, 100, 1024, 768)
        self.setWindowIcon(QIcon(resource_path('ICONE.ico'))) # Ícone da Janela

        self._is_quitting_via_tray = False # Flag para controlar o fechamento real

        # Carregar tema padrão inicial (ou o último salvo no futuro)
        self.current_theme_name = THEME_DARK_DEFAULT 
        self._apply_theme_qss(self.current_theme_name)
        self._setup_ui()
        self._create_tray_icon() # Configurar o ícone da bandeja

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = resource_path('ICONE.ico')
        if not os.path.exists(icon_path):
            print(f"Alerta: Ícone da bandeja não encontrado em {icon_path}. Usando ícone padrão do sistema.")
            # Tenta usar um ícone padrão do estilo atual do sistema se o arquivo não for encontrado
            standard_icon = self.style().standardIcon(QStyle.SP_ComputerIcon) # Exemplo, pode ser outro
            self.tray_icon.setIcon(standard_icon)
        else:
            self.tray_icon.setIcon(QIcon(icon_path))

        self.tray_icon.setToolTip("SwitchPilot")

        tray_menu = QMenu(self) # Parent para garantir que o menu seja coletado pelo garbage collector
        
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
        elif reason == QSystemTrayIcon.Trigger: # Clique simples
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
            self.activateWindow() # Garante que a janela venha para frente
            self.raise_()      # Para macOS e alguns WMs Linux
            self.toggle_visibility_action.setText("Minimizar para Bandeja")

    def _quit_application(self):
        self._is_quitting_via_tray = True
        self.tray_icon.hide() # Ocultar o ícone antes de sair
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self._is_quitting_via_tray:
            # Se estamos saindo explicitamente pelo menu da bandeja,
            # paramos o monitoramento e chamamos o closeEvent original.
            if hasattr(self, 'main_controller') and self.main_controller:
                if hasattr(self.main_controller, 'stop_monitoring_if_running'):
                    print("Parando monitoramento antes de sair...")
                    self.main_controller.stop_monitoring_if_running()
            
            # Salvar configurações, etc.
            print("Saindo da aplicação...")
            super().closeEvent(event)
        else:
            # Se o usuário clicou no "X" da janela, minimizamos para a bandeja.
            event.ignore()
            self._toggle_visibility() # Reutiliza a lógica de minimizar e mostrar mensagem

    def _get_theme_path(self, theme_name):
        base_path = "switchpilot/ui/themes/"
        if theme_name == THEME_LIGHT:
            return os.path.join(base_path, "modern_light.qss")
        elif theme_name == THEME_VERY_DARK:
            return os.path.join(base_path, "modern_very_dark.qss")
        elif theme_name == THEME_DARK_DEFAULT:
            return os.path.join(base_path, "modern_dark_obs.qss")
        return None # Ou lançar erro

    def _apply_theme_qss(self, theme_name):
        """Carrega e aplica o arquivo QSS do tema especificado."""
        qss_path = self._get_theme_path(theme_name)
        if not qss_path:
            print(f"Erro: Nome do tema desconhecido '{theme_name}'")
            return False

        file = QFile(qss_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            self.setStyleSheet(stream.readAll())
            file.close()
            self.current_theme_name = theme_name # Atualizar tema atual
            print(f"Tema '{theme_name}' aplicado de '{qss_path}'.")
            return True
        else:
            print(f"Erro ao carregar stylesheet do tema '{theme_name}': {qss_path}")
            print(f"Caminho absoluto tentado: {file.fileName()}")
            print(f"Erro: {file.errorString()}")
            # Tentar recarregar o tema padrão como fallback se o tema atual falhar?
            if theme_name != THEME_DARK_DEFAULT:
                print("Tentando carregar tema padrão como fallback...")
                # self._apply_theme_qss(THEME_DARK_DEFAULT) # Evitar recursão infinita se o padrão também falhar
                default_qss_path = self._get_theme_path(THEME_DARK_DEFAULT)
                default_file = QFile(default_qss_path)
                if default_file.open(QFile.ReadOnly | QFile.Text):
                    stream = QTextStream(default_file)
                    self.setStyleSheet(stream.readAll())
                    default_file.close()
                    self.current_theme_name = THEME_DARK_DEFAULT
                    print(f"Tema padrão '{THEME_DARK_DEFAULT}' aplicado como fallback.")
            return False

    def _setup_ui(self):
        # Barra de Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Arquivo")
        view_menu = menubar.addMenu("&Visualizar")
        
        # --- Menu Configurações e Aparência ---
        settings_menu = menubar.addMenu("&Configurações")
        appearance_menu = settings_menu.addMenu("&Aparência")

        # Adicionar ação para limiares
        self.thresholds_action = QAction("Limiar de Similaridade...", self)
        self.thresholds_action.triggered.connect(self._open_thresholds_dialog)
        settings_menu.addAction(self.thresholds_action)
        settings_menu.addSeparator()

        theme_action_group = QActionGroup(self) # Para garantir que apenas um tema seja "checado"
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
        
        help_menu = menubar.addMenu("A&juda")

        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto")

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
                    if not isinstance(parent_widget, QTextEdit) and not isinstance(parent_widget, QLabel): # Evitar pegar QTabBar de widgets que não são containers de dock
                        # Se o parent_widget for um QDockWidget, significa que o QTabBar é o título do próprio dock,
                        # o que não é o que queremos aqui (já é estilizado por QDockWidget::title).
                        # O QTabBar que gerencia múltiplos docks agrupados geralmente não tem um QDockWidget como pai direto.
                        # Ele é filho de um widget container interno da QMainWindow.
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
                            if parent_widget == self or parent_widget.parentWidget() == self: # Um pouco mais direto
                                tab_bar.setObjectName("CentralDockTabBar")
                                print(f"DEBUG: QTabBar dos docks (possivelmente) encontrado e nomeado 'CentralDockTabBar': {tab_bar} com pai {parent_widget}")
                                self._apply_theme_qss(self.current_theme_name) 
                                found_dock_tab_bar = True
                                break 
                            else: # Tentar uma busca mais genérica se a anterior falhar
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
        os.path.join(themes_dir, "modern_light.qss"): placeholder_qss_content.replace("#cccccc", "#f0f0f0").replace("#aaaaaa", "#d0d0d0"), # Light theme
        os.path.join(themes_dir, "modern_dark_obs.qss"): default_dark_qss_content,
        os.path.join(themes_dir, "modern_very_dark.qss"): placeholder_qss_content.replace("#cccccc", "#1a1a1a").replace("#aaaaaa", "#101010").replace("black", "white") # Very dark theme
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
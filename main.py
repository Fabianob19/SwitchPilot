import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSharedMemory
from switchpilot.ui.main_window import MainWindow  # Nova MainWindow
from switchpilot.core.main_controller import MainController  # Importar MainController
import subprocess

# Definir AppUserModelID e ícone no Windows para evitar ícone do Python na barra de tarefas
try:
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SwitchPilot.App")
        # Ativar DPI awareness (Per-Monitor v2) para coordenadas reais
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
except Exception:
    pass


def get_git_version():
    try:
        version = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.STDOUT,
        ).decode().strip()
        return version
    except Exception:
        return "v1.3.0"


if __name__ == "__main__":
    # Ativar atributos de High DPI do Qt ANTES do QApplication
    try:
        from PyQt5 import QtCore
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Impede que a app feche ao ocultar a janela

    # Aplicar ícone global do app
    try:
        app.setWindowIcon(QIcon("ICONE.ico"))
    except Exception:
        pass

    # Verificação de instância única
    shared_memory = QSharedMemory("SwitchPilot_SingleInstance")
    
    # Tentar criar memória compartilhada
    if not shared_memory.create(1):
        # Se já existe, significa que outra instância está rodando
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("SwitchPilot - Já está rodando")
        msg.setText("⚠️ O SwitchPilot já está em execução!")
        msg.setInformativeText(
            "Uma instância do SwitchPilot já está rodando.\n\n"
            "Verifique a bandeja do sistema (ao lado do relógio) "
            "para restaurar a janela.\n\n"
            "Deseja fechar esta segunda instância?"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        yes_button = msg.button(QMessageBox.Yes)
        yes_button.setText("Sim, Fechar")
        no_button = msg.button(QMessageBox.No)
        no_button.setText("Não, Continuar Mesmo Assim")
        
        result = msg.exec_()
        
        if result == QMessageBox.Yes:
            sys.exit(0)
        # Se escolher "Não", continua normalmente (permite múltiplas instâncias para debug)

    version = "v1.5.1"  # Otimizações de detecção NCC
    main_win = MainWindow(version=version)
    main_win.show()

    # Obter as instâncias dos widgets da MainWindow
    # É crucial que os nomes dos atributos em MainWindow (ex: main_win.reference_manager_widget)
    # correspondam aos nomes usados ao criar/atribuir esses widgets dentro de MainWindow._setup_ui()
    ref_manager = main_win.reference_manager_widget
    mon_control = main_win.monitoring_control_widget
    obs_cfg_widget = main_win.obs_config_widget
    vmix_cfg_widget = main_win.vmix_config_widget

    # Verificar se os widgets foram encontrados (para depuração)
    if not ref_manager:
        print("[main.py CRITICAL] main_win.reference_manager_widget não encontrado!")
    if not mon_control:
        print("[main.py CRITICAL] main_win.monitoring_control_widget não encontrado!")
    if not obs_cfg_widget:
        print("[main.py CRITICAL] main_win.obs_config_widget não encontrado!")
    if not vmix_cfg_widget:
        print("[main.py CRITICAL] main_win.vmix_config_widget não encontrado!")

    # 2. Criar o Controlador Principal (Core)
    # Passar a instância da MainWindow para o controller para que ele possa acessá-la
    # se necessário, ou acessar seus widgets diretamente.
    main_controller = MainController(
        ref_manager_widget=ref_manager,
        mon_control_widget=mon_control,
        obs_config_widget=obs_cfg_widget,
        vmix_config_widget=vmix_cfg_widget
    )

    # Conectar o sinal de log do controller ao painel de log da UI
    main_controller.new_log_message.connect(mon_control.add_log_message)

    # Passar a instância do main_controller para a MainWindow, para que ela possa
    # distribuí-la para widgets que precisam dela (ex: ReferenceManagerWidget para ActionConfigDialog)
    main_win.set_main_controller_for_widgets(main_controller)

    # 3. Conectar sinais do Core aos slots da UI
    # (Esta é uma forma de fazer isso. Outra seria o controller se conectar diretamente
    #  aos widgets através da referência main_win, o que já está sendo feito para
    #  sinais da UI para o Core dentro do __init__ do MainController)
    main_controller.connect_to_ui_slots()  # Conecta sinais do core para a UI

    # 4. Conectar o sinal de aboutToQuit da aplicação ao método de cleanup do controller
    app.aboutToQuit.connect(main_controller.cleanup)

    sys.exit(app.exec_())

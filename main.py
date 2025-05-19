import sys
from PyQt5.QtWidgets import QApplication
from switchpilot.ui.main_window import MainWindow # Nova MainWindow
from switchpilot.core.main_controller import MainController # Importar MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Impede que a app feche ao ocultar a janela

    main_win = MainWindow() # Usando a nova MainWindow
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

    # Passar a instância do main_controller para a MainWindow, para que ela possa
    # distribuí-la para widgets que precisam dela (ex: ReferenceManagerWidget para ActionConfigDialog)
    main_win.set_main_controller_for_widgets(main_controller)

    # 3. Conectar sinais do Core aos slots da UI
    # (Esta é uma forma de fazer isso. Outra seria o controller se conectar diretamente
    #  aos widgets através da referência main_win, o que já está sendo feito para
    #  sinais da UI para o Core dentro do __init__ do MainController)
    main_controller.connect_to_ui_slots() # Conecta sinais do core para a UI

    # 4. Conectar o sinal de aboutToQuit da aplicação ao método de cleanup do controller
    app.aboutToQuit.connect(main_controller.cleanup)

    sys.exit(app.exec_())
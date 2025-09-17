from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QHBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt


class VMixConfigWidget(QWidget):
    """Widget para configurar a conexão com o vMix."""
    config_changed = pyqtSignal(dict)
    test_connection = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VMixConfigWidget")
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Frame de Configuração ---
        config_frame = QFrame()
        config_frame.setObjectName("configFormFrame")
        # config_frame.setFrameShape(QFrame.StyledPanel) # Removido

        form_layout = QFormLayout(config_frame)
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)  # Alinha labels à direita

        self.host_input = QLineEdit("localhost")
        self.host_input.setPlaceholderText("Ex: 127.0.0.1 ou vmix_pc")
        form_layout.addRow(QLabel("Host vMix:"), self.host_input)

        self.port_input = QLineEdit("8088")
        self.port_input.setPlaceholderText("Ex: 8088")
        form_layout.addRow(QLabel("Porta vMix:"), self.port_input)

        layout.addWidget(config_frame)

        # --- Botões ---
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Testar Conexão vMix")
        self.test_button.setObjectName("testVMixButton")
        self.test_button.clicked.connect(self.test_connection.emit)

        # Centralizar o botão
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.test_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(button_layout)

        # Spacer para empurrar tudo para cima
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

    def _setup_connections(self):
        """Configura as conexões de sinais e slots."""
        self.test_button.clicked.connect(self.test_connection.emit)
        self.host_input.textChanged.connect(self._on_config_changed)
        self.port_input.textChanged.connect(self._on_config_changed)

    def _on_config_changed(self):
        """Chamado quando qualquer campo de configuração muda, emite o sinal com os dados."""
        config_data = self.get_config()
        self.config_changed.emit(config_data)

    def get_config(self):
        """Retorna a configuração atual como um dicionário."""
        return {
            "host": self.host_input.text().strip(),
            "port": self.port_input.text().strip(),
        }

    def set_config(self, config):
        """Define a configuração do widget a partir de um dicionário."""
        if isinstance(config, dict):  # Verificar se config é um dicionário
            self.host_input.setText(config.get('host', 'localhost'))
            self.port_input.setText(config.get('port', '8088'))
        else:
            # Opcional: Logar um aviso ou erro se config não for um dict
            print(f"[VMixConfigWidget] set_config: Esperava um dict, recebeu {type(config)}")
            # Resetar para padrões para evitar estado inconsistente
            self.host_input.setText('localhost')
            self.port_input.setText('8088')

# REMOVIDO BLOCO if __name__ == '__main__':

    # Para aplicar o estilo (opcional, mas bom para visualização)
    # QSS_PATH = "../themes/modern_dark_obs.qss" 
    # try:
    #     with open(QSS_PATH, "r") as f:
    #         app.setStyleSheet(f.read())
    # except FileNotFoundError:
    #     print(f"Stylesheet não encontrado em: {QSS_PATH}")

    # widget = VMixConfigWidget()
    # widget.setWindowTitle("Teste VMixConfigWidget")
    # widget.resize(400, 200)
    # widget.show()
    # sys.exit(app.exec_()) 
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal


class OBSConfigWidget(QWidget):
    """Widget de configuração do OBS com melhor controle de visibilidade e estilos."""

    # Sinais
    config_changed = pyqtSignal(dict)
    test_connection = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OBSConfigWidget")

        # Configurar UI
        self.setup_ui()

        # Conectar sinais
        self.setup_connections()

    def setup_ui(self):
        """Configura a interface do usuário."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Frame de Configuração ---
        config_frame = QFrame()
        config_frame.setObjectName("configFormFrame")

        form_layout = QFormLayout(config_frame)
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Campos de entrada
        self.host_input = QLineEdit("localhost")
        self.host_input.setPlaceholderText("Ex: 127.0.0.1 ou obs_pc")

        self.port_input = QLineEdit("4455")
        self.port_input.setPlaceholderText("Ex: 4455")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Senha (opcional)")

        form_layout.addRow(QLabel("Host OBS:"), self.host_input)
        form_layout.addRow(QLabel("Porta OBS:"), self.port_input)
        form_layout.addRow(QLabel("Senha OBS:"), self.password_input)

        main_layout.addWidget(config_frame)

        # --- Botão de teste ---
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Testar Conexão OBS")
        self.test_button.setObjectName("testOBSButton")

        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.test_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(button_layout)

        # Spacer para empurrar tudo para cima
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def setup_connections(self):
        """Configura as conexões de sinais e slots."""
        self.test_button.clicked.connect(self.test_connection.emit)

        # Conectar mudanças nos campos de entrada
        for widget in [self.host_input, self.port_input, self.password_input]:
            widget.textChanged.connect(self.on_config_changed)

    def on_config_changed(self):
        """Emite o sinal de configuração alterada com os novos valores."""
        config = {
            'host': self.host_input.text(),
            'port': self.port_input.text(),
            'password': self.password_input.text()
        }
        self.config_changed.emit(config)

    def get_config(self):
        """Retorna a configuração atual."""
        return {
            'host': self.host_input.text(),
            'port': self.port_input.text(),
            'password': self.password_input.text()
        }

    def set_config(self, config):
        """Define a configuração do widget."""
        self.host_input.setText(config.get('host', 'localhost'))
        self.port_input.setText(config.get('port', '4455'))
        self.password_input.setText(config.get('password', ''))

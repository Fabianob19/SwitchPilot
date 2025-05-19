from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QSizePolicy, QFrame, QSpacerItem, QDoubleSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor

class MonitoringControlWidget(QWidget):
    # Sinais para iniciar/parar o processo de monitoramento (a serem conectados no core)
    start_monitoring_requested = pyqtSignal()
    stop_monitoring_requested = pyqtSignal(str)
    static_threshold_changed = pyqtSignal(float)    # Novo sinal
    sequence_threshold_changed = pyqtSignal(float)  # Novo sinal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Seção de Controles ---
        controls_frame = QFrame()
        controls_frame.setObjectName("monitoringControlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        
        self.start_button = QPushButton("Iniciar Monitoramento")
        self.start_button.setIcon(self.style().standardIcon(getattr(self.style(), "SP_MediaPlay", None))) # Ícone de Play
        self.start_button.setStyleSheet("padding: 5px;")

        self.stop_button = QPushButton("Parar Monitoramento")
        self.stop_button.setIcon(self.style().standardIcon(getattr(self.style(), "SP_MediaStop", None))) # Ícone de Stop
        self.stop_button.setStyleSheet("padding: 5px;")
        self.stop_button.setEnabled(False)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        main_layout.addWidget(controls_frame)

        # --- Seção de Status ---
        status_frame = QFrame()
        status_frame.setObjectName("monitoringStatusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5,2,5,2)

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet("background-color: grey;")

        self.status_label = QLabel("Status: Parado")
        self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #d8dee9;")
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)

        # --- Seção de Log ---
        log_label = QLabel("Log de Eventos:")
        log_label.setProperty("heading", True)
        main_layout.addWidget(log_label)

        self.log_output_text = QTextEdit()
        self.log_output_text.setReadOnly(True)
        self.log_output_text.setLineWrapMode(QTextEdit.WidgetWidth) # Quebra de linha
        self.log_output_text.setFixedHeight(150) # Altura inicial, pode ser ajustado
        self.log_output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        main_layout.addWidget(self.log_output_text, 1) # O 1 faz com que expanda verticalmente

        # Conectar sinais dos botões
        self.start_button.clicked.connect(self._handle_start_monitoring)
        self.stop_button.clicked.connect(self._handle_stop_monitoring)
        
    def _handle_start_monitoring(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_status("Iniciando monitoramento...")
        self.add_log_message("Solicitação para iniciar monitoramento enviada.")
        self.start_monitoring_requested.emit()

    def _handle_stop_monitoring(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_status("Parando monitoramento...")
        self.add_log_message("Solicitação para parar monitoramento enviada.")
        self.stop_monitoring_requested.emit("Processo finalizado.")

    # Slots públicos para serem chamados pelo core/controller
    def monitoring_started(self):
        self.update_status("Monitoramento Ativo")
        self.add_log_message("Monitoramento iniciado com sucesso.")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # Proteção para status_indicator
        if hasattr(self, 'status_indicator') and self.status_indicator is not None:
            try:
                self.status_indicator.setStyleSheet("background-color: green;")
            except RuntimeError:
                print("[MonitoringControlWidget] Tentativa de acessar status_indicator já deletado. Ignorando.")
        else:
            print("[MonitoringControlWidget] status_indicator não existe mais. Ignorando.")

    def monitoring_stopped(self, reason="Processo finalizado."):
        self.update_status(f"Parado. {reason}")
        self.add_log_message(f"Monitoramento parado. Razão: {reason}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # Proteção para status_indicator
        if hasattr(self, 'status_indicator') and self.status_indicator is not None:
            try:
                self.status_indicator.setStyleSheet("background-color: grey;")
            except RuntimeError:
                print("[MonitoringControlWidget] Tentativa de acessar status_indicator já deletado. Ignorando.")
        else:
            print("[MonitoringControlWidget] status_indicator não existe mais. Ignorando.")

    def monitoring_error(self, error_message):
        self.update_status("Erro no Monitoramento!")
        self.add_log_message(f"ERRO: {error_message}", level="error")
        # Manter o estado dos botões ou resetar? Depende da gravidade do erro.
        # Por agora, vamos permitir que o usuário tente parar ou reiniciar.
        # self.start_button.setEnabled(True) 
        # self.stop_button.setEnabled(False)

    def update_status(self, message):
        # Proteção extra para evitar acessar QLabel destruído
        if not hasattr(self, 'status_label') or self.status_label is None:
            print("[MonitoringControlWidget] status_label não existe mais. Ignorando update_status.")
            return
        try:
            self.status_label.setText(f"Status: {message}")
        except RuntimeError:
            print("[MonitoringControlWidget] Tentativa de acessar status_label já deletado. Ignorando.")
            return
        # Mudar cor com base no status poderia ser uma melhoria futura
        if "Erro" in message:
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #bf616a;") # Vermelho
        elif "Ativo" in message or "Iniciando" in message:
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #a3be8c;") # Verde
        else: # Parado, etc.
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #d8dee9;") # Normal

    def add_log_message(self, message, level="info"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        if level == "error":
            self.log_output_text.setTextColor(QColor("#bf616a")) # Vermelho
        elif level == "warning":
            self.log_output_text.setTextColor(QColor("#ebcb8b")) # Amarelo
        else: # info
            self.log_output_text.setTextColor(QColor("#e5e9f0")) # Cinza claro
            
        self.log_output_text.append(f"[{timestamp}] {message.strip()}")
        self.log_output_text.ensureCursorVisible() # Auto-scroll para a última mensagem

    def get_thresholds(self):
        """Retorna os valores atuais dos limiares da UI."""
        return {
            'static': 0.90, # Valor padrão, pois não está mais na UI
            'sequence': 0.90
        }

    def closeEvent(self, event):
        try:
            self.start_button.clicked.disconnect()
            self.stop_button.clicked.disconnect()
            # Desconectar sinais customizados se necessário
            # self.static_threshold_changed.disconnect()
            # self.sequence_threshold_changed.disconnect()
        except Exception as e:
            print(f"[MonitoringControlWidget] Erro ao desconectar sinais no closeEvent: {e}")
        event.accept()

# Para teste individual do widget
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    try:
        with open('../themes/modern_dark_obs.qss', 'r') as f: # Ajuste o caminho se necessário
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("QSS de tema não encontrado para teste (../themes/modern_dark_obs.qss)")

    widget = MonitoringControlWidget()
    widget.setWindowTitle("Teste MonitoringControlWidget")
    widget.setGeometry(100, 100, 400, 300)
    widget.show()
    
    # Teste dos slots
    def test_slots():
        widget.add_log_message("Uma mensagem de informação.")
        widget.add_log_message("Um aviso importante!", level="warning")
        widget.add_log_message("Algo deu muito errado!", level="error")
        widget.update_status("Testando Status Ativo")
        widget.monitoring_started()

    from PyQt5.QtCore import QTimer
    QTimer.singleShot(2000, test_slots) # Chamar após 2 segundos

    sys.exit(app.exec_()) 
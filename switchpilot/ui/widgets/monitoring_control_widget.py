from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QPlainTextEdit, QSizePolicy, QFrame, QSpacerItem, QDoubleSpinBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTimer
from PyQt5.QtGui import QColor, QTextCursor, QFont

class MonitoringControlWidget(QFrame):
    # Sinais para iniciar/parar o processo de monitoramento (a serem conectados no core)
    start_monitoring_requested = pyqtSignal()
    stop_monitoring_requested = pyqtSignal(str)
    static_threshold_changed = pyqtSignal(float)    # Novo sinal
    sequence_threshold_changed = pyqtSignal(float)  # Novo sinal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("monitoringControlWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("")
        self._is_shutting_down = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

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

        # Painel de Log Aprimorado
        log_panel_layout = QVBoxLayout()
        log_panel_layout.setSpacing(2)
        log_panel_layout.setContentsMargins(0, 0, 0, 0)

        # Filtros
        filter_layout = QHBoxLayout()
        self.filter_info = QCheckBox("Info")
        self.filter_info.setChecked(True)
        self.filter_success = QCheckBox("Sucesso")
        self.filter_success.setChecked(True)
        self.filter_warning = QCheckBox("Aviso")
        self.filter_warning.setChecked(True)
        self.filter_error = QCheckBox("Erro")
        self.filter_error.setChecked(True)
        self.filter_debug = QCheckBox("Debug")
        self.filter_debug.setChecked(False)
        for cb in [self.filter_info, self.filter_success, self.filter_warning, self.filter_error, self.filter_debug]:
            cb.setStyleSheet("QCheckBox { font-size: 9pt; color: #bbb; } QCheckBox::indicator { width: 12px; height: 12px; }")
            filter_layout.addWidget(cb)
        filter_layout.addStretch()
        log_panel_layout.addLayout(filter_layout)

        # QTextEdit para log
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #232323; color: #cccccc; border: 1px solid #333; border-radius: 4px;")
        self.log_text.setMaximumBlockCount(2000)
        log_panel_layout.addWidget(self.log_text)

        # Botões discretos
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Limpar")
        self.btn_copy = QPushButton("Copiar")
        self.btn_save = QPushButton("Salvar")
        for btn in [self.btn_clear, self.btn_copy, self.btn_save]:
            btn.setFixedHeight(22)
            btn.setStyleSheet("QPushButton { font-size: 9pt; padding: 2px 10px; border-radius: 4px; background: #333; color: #bbb; border: 1px solid #444; } QPushButton:hover { background: #444; color: #fff; }")
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        log_panel_layout.addLayout(btn_layout)

        main_layout.addLayout(log_panel_layout)

        # Conexão dos botões
        self.btn_clear.clicked.connect(self.log_text.clear)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.log_text.toPlainText()))
        self.btn_save.clicked.connect(self._save_log_to_file)

        # Filtros
        for cb in [self.filter_info, self.filter_success, self.filter_warning, self.filter_error, self.filter_debug]:
            cb.stateChanged.connect(self._on_filter_changed)

        # Buffer de logs (nível, mensagem)
        self._log_buffer = []
        self._log_queue = []
        self._rebuild_needed = False
        self._log_flush_timer = QTimer(self)
        self._log_flush_timer.setInterval(100)
        self._log_flush_timer.timeout.connect(self._flush_log_queue)
        self._log_flush_timer.start()

        # Conectar sinais dos botões
        self.start_button.clicked.connect(self._handle_start_monitoring)
        self.stop_button.clicked.connect(self._handle_stop_monitoring)
        
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
        if getattr(self, '_is_shutting_down', False):
            return
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_status("Iniciando monitoramento...")
        self.add_log_message("Solicitação para iniciar monitoramento enviada.")
        self.start_monitoring_requested.emit()

    def _handle_stop_monitoring(self):
        if getattr(self, '_is_shutting_down', False):
            return
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_status("Parando monitoramento...")
        self.add_log_message("Solicitação para parar monitoramento enviada.")
        self.stop_monitoring_requested.emit("Processo finalizado.")

    # Slots públicos para serem chamados pelo core/controller
    def monitoring_started(self):
        if getattr(self, '_is_shutting_down', False):
            return
        self.update_status("Monitoramento Ativo")
        self.add_log_message("Monitoramento iniciado com sucesso.")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # Proteção para status_indicator
        if hasattr(self, 'status_indicator') and self.status_indicator is not None:
            try:
                self.status_indicator.setStyleSheet("background-color: green;")
            except RuntimeError:
                return
        else:
            return

    def monitoring_stopped(self, reason="Processo finalizado."):
        if getattr(self, '_is_shutting_down', False):
            return
        self.update_status(f"Parado. {reason}")
        self.add_log_message(f"Monitoramento parado. Razão: {reason}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # Proteção para status_indicator
        if hasattr(self, 'status_indicator') and self.status_indicator is not None:
            try:
                self.status_indicator.setStyleSheet("background-color: grey;")
            except RuntimeError:
                return
        else:
            return

    def monitoring_error(self, error_message):
        if getattr(self, '_is_shutting_down', False):
            return
        self.update_status("Erro no Monitoramento!")
        self.add_log_message(f"ERRO: {error_message}", level="error")
        # Manter o estado dos botões ou resetar? Depende da gravidade do erro.
        # Por agora, vamos permitir que o usuário tente parar ou reiniciar.
        # self.start_button.setEnabled(True) 
        # self.stop_button.setEnabled(False)

    def update_status(self, message):
        if getattr(self, '_is_shutting_down', False):
            return
        # Proteção extra para evitar acessar QLabel destruído
        if not hasattr(self, 'status_label') or self.status_label is None:
            return
        try:
            self.status_label.setText(f"Status: {message}")
        except RuntimeError:
            return
        # Mudar cor com base no status poderia ser uma melhoria futura
        if "Erro" in message:
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #bf616a;") # Vermelho
        elif "Ativo" in message or "Iniciando" in message:
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #a3be8c;") # Verde
        else: # Parado, etc.
            self.status_label.setStyleSheet("font-weight: bold; padding: 3px; color: #d8dee9;") # Normal

    def add_log_message(self, message, level="info"):
        self._log_buffer.append((level, message))
        # Limitar o buffer a 1000 mensagens
        if len(self._log_buffer) > 1000:
            self._log_buffer = self._log_buffer[-1000:]
        # Enfileirar para flush assíncrono, evitando travamentos de UI
        self._log_queue.append((level, message))

    def _append_log_to_textedit(self, level, message):
        prefix_map = {
            "info": "[INFO]",
            "success": "[SUCESSO]",
            "warning": "[AVISO]",
            "error": "[ERRO]",
            "debug": "[DEBUG]"
        }
        prefix = prefix_map.get(level, "[INFO]")
        self.log_text.appendPlainText(f'{prefix} {message}')

    def _apply_log_filter(self):
        # Apenas marca para reconstruir no próximo flush
        self._rebuild_needed = True

    def _get_prefix(self, level):
        prefix_map = {
            "info": "[INFO]",
            "success": "[SUCESSO]",
            "warning": "[AVISO]",
            "error": "[ERRO]",
            "debug": "[DEBUG]"
        }
        return prefix_map.get(level, "[INFO]")

    def _save_log_to_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Log", "log_switchpilot.txt", "Text Files (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())

    def get_thresholds(self):
        """Retorna os valores atuais dos limiares da UI."""
        return {
            'static': 0.90, # Valor padrão, pois não está mais na UI
            'sequence': 0.90
        }

    def closeEvent(self, event):
        self._is_shutting_down = True
        try:
            self.start_button.clicked.disconnect()
            self.stop_button.clicked.disconnect()
            for cb in [self.filter_info, self.filter_success, self.filter_warning, self.filter_error, self.filter_debug]:
                try:
                    cb.stateChanged.disconnect()
                except Exception:
                    pass
        except Exception:
            pass
        event.accept()

    def _on_filter_changed(self, state):
        # Quando filtro mudar, marcamos rebuild e limpamos a fila para evitar duplicação
        self._rebuild_needed = True

    def _flush_log_queue(self):
        if not self._log_queue and not self._rebuild_needed:
            return
        show = {
            "info": self.filter_info.isChecked(),
            "success": self.filter_success.isChecked(),
            "warning": self.filter_warning.isChecked(),
            "error": self.filter_error.isChecked(),
            "debug": self.filter_debug.isChecked()
        }
        if self._rebuild_needed:
            # Reconstruir do zero conforme filtros
            self.log_text.blockSignals(True)
            self.log_text.clear()
            for level, msg in self._log_buffer:
                if show.get(level, True):
                    self.log_text.appendPlainText(f"{self._get_prefix(level)} {msg}")
            self.log_text.blockSignals(False)
            self._rebuild_needed = False
        # Acrescentar apenas novos itens que passam no filtro
        if self._log_queue:
            self.log_text.blockSignals(True)
            for level, msg in self._log_queue:
                if show.get(level, True):
                    self.log_text.appendPlainText(f"{self._get_prefix(level)} {msg}")
            self.log_text.blockSignals(False)
            self._log_queue.clear()

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
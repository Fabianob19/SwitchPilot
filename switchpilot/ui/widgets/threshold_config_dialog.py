from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QDialogButtonBox
from PyQt5.QtCore import pyqtSignal, Qt

class ThresholdConfigDialog(QDialog):
    thresholds_updated = pyqtSignal(float, float, float)  # static, sequence, interval

    def __init__(self, static_value=0.90, sequence_value=0.90, interval_value=0.5, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Limiares de Similaridade")
        # Remover botão de ajuda ('?') do título
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # Tentar aplicar dark title bar quando suportado (MainWindow expõe utilitário via import tardio)
        try:
            from switchpilot.ui.main_window import enable_dark_title_bar_for_window
            enable_dark_title_bar_for_window(self)
        except Exception:
            pass
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        # Valores recomendados (baseados nos logs atuais)
        self._recommended_static = 0.90
        self._recommended_sequence = 0.90
        self._recommended_interval = 0.50

        # Limiar Estático
        static_layout = QHBoxLayout()
        static_label = QLabel("Limiar Estático:")
        self.static_spin = QDoubleSpinBox()
        self.static_spin.setRange(0.0, 1.0)
        self.static_spin.setSingleStep(0.01)
        self.static_spin.setValue(static_value)
        self.static_spin.setToolTip(
            "Limiar de similaridade para uma única imagem de referência (0.00–1.00).\n"
            "Aumentar = mais rigor (menos falsos positivos). Diminuir = mais sensível."
        )
        static_layout.addWidget(static_label)
        static_layout.addWidget(self.static_spin)
        layout.addLayout(static_layout)

        # Limiar Sequência
        seq_layout = QHBoxLayout()
        seq_label = QLabel("Limiar Sequência:")
        self.seq_spin = QDoubleSpinBox()
        self.seq_spin.setRange(0.0, 1.0)
        self.seq_spin.setSingleStep(0.01)
        self.seq_spin.setValue(sequence_value)
        self.seq_spin.setToolTip(
            "Limiar de similaridade para referências com vários frames (usa a média) (0.00–1.00).\n"
            "Aumentar = mais rigor. Diminuir = mais sensível."
        )
        seq_layout.addWidget(seq_label)
        seq_layout.addWidget(self.seq_spin)
        layout.addLayout(seq_layout)

        # Intervalo de Captura
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Intervalo de Captura (s):")
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 5.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(interval_value)
        self.interval_spin.setToolTip(
            "Tempo entre verificações. Menor = mais rápido e mais comandos/CPU; Maior = mais leve e mais lento."
        )
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # Texto de ajuda compacto
        help_label = QLabel(
            "\nComo funciona: S (0–1) é uma média ponderada de 3 métricas (Hist+NCC+LBP).\n"
            "Dispara quando S ≥ Limiar. Com K=1, se S ficar acima do limiar, envia em todo ciclo.\n\n"
            "Dicas rápidas:\n"
            "- Aumente o limiar para mais precisão (menos falsos positivos).\n"
            "- Diminua o limiar para mais sensibilidade.\n"
            "- Reduza o intervalo para resposta mais rápida (maior carga).\n"
            "- Recomendados (padrão seguro): 0,90 / 0,90 / 0,50s."
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Botão "Restaurar recomendados"
        restore_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Restaurar recomendados")
        self.restore_btn.setToolTip("Define 0,90 / 0,90 / 0,50s (padrão seguro).")
        self.restore_btn.clicked.connect(self._restore_recommended)
        restore_layout.addWidget(self.restore_btn)

        # Botões OK/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._accept_and_emit)
        self.button_box.rejected.connect(self.reject)
        restore_layout.addWidget(self.button_box)
        layout.addLayout(restore_layout)

    def _restore_recommended(self):
        self.static_spin.setValue(self._recommended_static)
        self.seq_spin.setValue(self._recommended_sequence)
        self.interval_spin.setValue(self._recommended_interval)

    def _accept_and_emit(self):
        self.thresholds_updated.emit(self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value())
        self.accept()

    def get_thresholds(self):
        return self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value()

    def accept(self):
        # Emite o sinal com os valores atuais antes de fechar
        self.thresholds_updated.emit(self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value())
        super().accept() 
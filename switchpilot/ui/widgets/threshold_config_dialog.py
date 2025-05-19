from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QDialogButtonBox
from PyQt5.QtCore import pyqtSignal

class ThresholdConfigDialog(QDialog):
    thresholds_updated = pyqtSignal(float, float, float)  # static, sequence, interval

    def __init__(self, static_value=0.90, sequence_value=0.90, interval_value=0.5, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Limiares de Similaridade")
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        # Limiar Estático
        static_layout = QHBoxLayout()
        static_label = QLabel("Limiar Estático:")
        self.static_spin = QDoubleSpinBox()
        self.static_spin.setRange(0.0, 1.0)
        self.static_spin.setSingleStep(0.01)
        self.static_spin.setValue(static_value)
        self.static_spin.setToolTip("Limiar de similaridade para imagens estáticas (0.0 - 1.0). Recomenda-se 0.85 a 0.95.")
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
        self.seq_spin.setToolTip("Limiar de similaridade para cada frame de uma sequência (0.0 - 1.0). Recomenda-se 0.80 a 0.95.")
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
        self.interval_spin.setToolTip("Intervalo entre capturas de imagem para monitoramento (em segundos). Valores menores aumentam a responsividade, mas consomem mais CPU.")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # Botões OK/Cancelar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_thresholds(self):
        return self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value()

    def accept(self):
        # Emite o sinal com os valores atuais antes de fechar
        self.thresholds_updated.emit(self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value())
        super().accept() 
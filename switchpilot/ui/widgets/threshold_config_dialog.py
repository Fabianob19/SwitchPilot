from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QDoubleSpinBox, QSpinBox, QPushButton,
                             QDialogButtonBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class ThresholdConfigDialog(QDialog):
    thresholds_updated = pyqtSignal(float, float, float)  # static, sequence, interval
    nsfw_thresholds_updated = pyqtSignal(float, dict)  # general, min_confidence dict

    def __init__(self, static_value=0.90, sequence_value=0.90, interval_value=0.5,
                 nsfw_general=55, nsfw_breast=60, nsfw_anus=40, nsfw_genitalia=0,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Limiares")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMinimumWidth(420)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        from switchpilot.ui.widgets.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, None, height=32)
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        main_layout.addWidget(self.title_bar)

        content_container = QFrame(self)
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addWidget(content_container)

        # === SEÇÃO: Similaridade de Cena ===
        section_font = QFont()
        section_font.setBold(True)
        section_font.setPointSize(10)

        sim_label = QLabel("Similaridade de Cena")
        sim_label.setProperty("heading", True)
        layout.addWidget(sim_label)

        # Valores recomendados
        self._rec_static = 0.90
        self._rec_sequence = 0.90
        self._rec_interval = 0.50

        # Limiar Estático
        static_layout = QHBoxLayout()
        static_label = QLabel("Limiar Estático:")
        self.static_spin = QDoubleSpinBox()
        self.static_spin.setRange(0.0, 1.0)
        self.static_spin.setSingleStep(0.01)
        self.static_spin.setValue(static_value)
        self.static_spin.setToolTip(
            "Nível de semelhança para uma imagem de referência única.\n"
            "Quanto maior, mais parecida a tela precisa estar. (Padrão: 0,90)"
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
            "Nível de semelhança para referências com vários frames (usa média).\n"
            "Quanto maior, mais parecida a tela precisa estar. (Padrão: 0,90)"
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
            "Tempo entre cada verificação da tela (em segundos).\n"
            "Menor = mais rápido, porém maior uso de CPU/GPU. (Padrão: 0,50s)"
        )
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # === SEPARADOR ===
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addSpacing(6)
        layout.addWidget(separator)
        layout.addSpacing(6)

        # === SEÇÃO: Detecção NSFW ===
        nsfw_label = QLabel("Detecção NSFW")
        nsfw_label.setProperty("heading", True)
        layout.addWidget(nsfw_label)

        # Valores recomendados NSFW
        self._rec_nsfw_general = 55
        self._rec_nsfw_breast = 60
        self._rec_nsfw_anus = 40
        self._rec_nsfw_genitalia = 0

        # Sensibilidade Geral
        gen_layout = QHBoxLayout()
        gen_label = QLabel("Sensibilidade Geral (%):")
        self.nsfw_general_spin = QSpinBox()
        self.nsfw_general_spin.setRange(0, 100)
        self.nsfw_general_spin.setSingleStep(5)
        self.nsfw_general_spin.setValue(nsfw_general)
        self.nsfw_general_spin.setToolTip(
            "Score mínimo para disparar a detecção NSFW.\n"
            "Se a IA tiver certeza acima deste valor, considera NSFW.\n"
            "Menor = mais sensível (detecta mais). Maior = mais rigoroso. (Padrão: 55%)"
        )
        gen_layout.addWidget(gen_label)
        gen_layout.addWidget(self.nsfw_general_spin)
        layout.addLayout(gen_layout)

        # Confiança Mín. — Seios
        breast_layout = QHBoxLayout()
        breast_label = QLabel("Confiança Mín. — Seios (%):")
        self.nsfw_breast_spin = QSpinBox()
        self.nsfw_breast_spin.setRange(0, 100)
        self.nsfw_breast_spin.setSingleStep(5)
        self.nsfw_breast_spin.setValue(nsfw_breast)
        self.nsfw_breast_spin.setToolTip(
            "Certeza mínima para considerar 'seio feminino exposto'.\n"
            "Valor alto evita confundir peitorais masculinos com seios.\n"
            "0% = sem filtro extra. (Padrão: 60%)"
        )
        breast_layout.addWidget(breast_label)
        breast_layout.addWidget(self.nsfw_breast_spin)
        layout.addLayout(breast_layout)

        # Confiança Mín. — Ânus
        anus_layout = QHBoxLayout()
        anus_label = QLabel("Confiança Mín. — Ânus (%):")
        self.nsfw_anus_spin = QSpinBox()
        self.nsfw_anus_spin.setRange(0, 100)
        self.nsfw_anus_spin.setSingleStep(5)
        self.nsfw_anus_spin.setValue(nsfw_anus)
        self.nsfw_anus_spin.setToolTip(
            "Certeza mínima para considerar 'ânus exposto'.\n"
            "0% = sem filtro extra. (Padrão: 40%)"
        )
        anus_layout.addWidget(anus_label)
        anus_layout.addWidget(self.nsfw_anus_spin)
        layout.addLayout(anus_layout)

        # Confiança Mín. — Genitálias
        gen2_layout = QHBoxLayout()
        gen2_label = QLabel("Confiança Mín. — Genitálias (%):")
        self.nsfw_genitalia_spin = QSpinBox()
        self.nsfw_genitalia_spin.setRange(0, 100)
        self.nsfw_genitalia_spin.setSingleStep(5)
        self.nsfw_genitalia_spin.setValue(nsfw_genitalia)
        self.nsfw_genitalia_spin.setToolTip(
            "Certeza mínima para considerar genitália exposta (masculina ou feminina).\n"
            "0% = sem filtro extra, usa apenas a Sensibilidade Geral. (Padrão: 0%)"
        )
        gen2_layout.addWidget(gen2_label)
        gen2_layout.addWidget(self.nsfw_genitalia_spin)
        layout.addLayout(gen2_layout)

        # Texto de ajuda NSFW
        nsfw_help = QLabel(
            "A IA verifica a tela e dá uma nota de certeza para cada parte.\n"
            "Se a nota for maior que a Sensibilidade Geral, dispara a ação.\n"
            "A Confiança Mínima filtra partes específicas antes da avaliação final."
        )
        nsfw_help.setWordWrap(True)
        nsfw_help.setStyleSheet("color: #888; font-size: 11px; margin-top: 4px;")
        layout.addWidget(nsfw_help)

        # === BOTÕES ===
        layout.addSpacing(8)
        btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Restaurar padrão")
        self.restore_btn.setToolTip("Restaura todos os valores recomendados.")
        self.restore_btn.clicked.connect(self._restore_recommended)
        btn_layout.addWidget(self.restore_btn)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._accept_and_emit)
        self.button_box.rejected.connect(self.reject)
        btn_layout.addWidget(self.button_box)
        layout.addLayout(btn_layout)

    def _restore_recommended(self):
        self.static_spin.setValue(self._rec_static)
        self.seq_spin.setValue(self._rec_sequence)
        self.interval_spin.setValue(self._rec_interval)
        self.nsfw_general_spin.setValue(self._rec_nsfw_general)
        self.nsfw_breast_spin.setValue(self._rec_nsfw_breast)
        self.nsfw_anus_spin.setValue(self._rec_nsfw_anus)
        self.nsfw_genitalia_spin.setValue(self._rec_nsfw_genitalia)

    def _accept_and_emit(self):
        self.thresholds_updated.emit(
            self.static_spin.value(),
            self.seq_spin.value(),
            self.interval_spin.value()
        )
        self.nsfw_thresholds_updated.emit(
            self.nsfw_general_spin.value() / 100.0,
            self.get_nsfw_min_confidence()
        )
        self.accept()

    def get_thresholds(self):
        return self.static_spin.value(), self.seq_spin.value(), self.interval_spin.value()

    def get_nsfw_min_confidence(self) -> dict:
        result = {}
        breast_val = self.nsfw_breast_spin.value() / 100.0
        anus_val = self.nsfw_anus_spin.value() / 100.0
        genitalia_val = self.nsfw_genitalia_spin.value() / 100.0
        if breast_val > 0:
            result['FEMALE_BREAST_EXPOSED'] = breast_val
        if anus_val > 0:
            result['ANUS_EXPOSED'] = anus_val
        if genitalia_val > 0:
            result['FEMALE_GENITALIA_EXPOSED'] = genitalia_val
            result['MALE_GENITALIA_EXPOSED'] = genitalia_val
        return result

    def accept(self):
        self.thresholds_updated.emit(
            self.static_spin.value(),
            self.seq_spin.value(),
            self.interval_spin.value()
        )
        self.nsfw_thresholds_updated.emit(
            self.nsfw_general_spin.value() / 100.0,
            self.get_nsfw_min_confidence()
        )
        super().accept()

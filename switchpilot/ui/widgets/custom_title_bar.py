from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QSizePolicy, QMenuBar
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon

class CustomTitleBar(QWidget):
    def __init__(self, window, menubar: QMenuBar, height: int = 32):
        super().__init__(window)
        self._window = window
        self._menubar = menubar
        self._height = height
        self._mouse_pos = None
        self.setFixedHeight(self._height)
        self.setObjectName("CustomTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 6, 0)
        layout.setSpacing(8)

        # Ícone + título
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(self._window.windowTitle())
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.title_label)

        # Menubar integrado
        if self._menubar is not None:
            self._menubar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(self._menubar, 10)
        else:
            spacer = QLabel("")
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(spacer, 10)

        # Botões window control
        self.btn_min = QToolButton(self)
        self.btn_max = QToolButton(self)
        self.btn_close = QToolButton(self)
        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.setAutoRaise(True)
            btn.setFixedSize(28, 24)
        self.btn_min.setText("–")
        self.btn_max.setText("□")
        self.btn_close.setText("✕")

        self.btn_min.clicked.connect(self._window.showMinimized)
        self.btn_max.clicked.connect(self._toggle_max_restore)
        self.btn_close.clicked.connect(self._window.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        self._sync_from_window()
        self._window.windowTitleChanged.connect(self._on_title_changed)
        self._window.windowIconChanged.connect(self._on_icon_changed)

        # Estilo básico (integra com temas escuros)
        self.setStyleSheet(
            """
            #CustomTitleBar { background-color: #202225; }
            #CustomTitleBar QLabel { color: #e6e6e6; }
            QToolButton { color: #e6e6e6; border: none; background: transparent; }
            QToolButton:hover { background-color: rgba(255,255,255,0.10); }
            QToolButton:pressed { background-color: rgba(255,255,255,0.18); }
            QToolButton:last-of-type:hover { background-color: #e81123; color: white; }
            """
        )

    def _sync_from_window(self):
        self.title_label.setText(self._window.windowTitle())
        icon = self._window.windowIcon()
        if not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(16, 16))

    def _on_title_changed(self, title):
        self.title_label.setText(title)

    def _on_icon_changed(self, icon: QIcon):
        if icon and not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(16, 16))

    def _toggle_max_restore(self):
        if self._window.isMaximized():
            self._window.showNormal()
            self.btn_max.setText("□")
        else:
            self._window.showMaximized()
            self.btn_max.setText("❐")

    # Drag para mover janela
    def mousePressEvent(self, event):
        if event.button() == 1:
            self._mouse_pos = event.globalPos() - self._window.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._mouse_pos is not None and event.buttons() & 1:
            self._window.move(event.globalPos() - self._mouse_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._mouse_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Maximizar/restaurar ao dar duplo clique
        if event.button() == 1:
            self._toggle_max_restore()
        super().mouseDoubleClickEvent(event) 
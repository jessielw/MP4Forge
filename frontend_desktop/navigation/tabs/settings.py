from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lbl = QLabel("This is the Settings Window", self)

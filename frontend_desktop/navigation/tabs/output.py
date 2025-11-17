from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OutputTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lbl = QLabel("This is the Output Window", self)

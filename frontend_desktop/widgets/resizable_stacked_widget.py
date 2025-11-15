from PySide6.QtCore import QSize
from PySide6.QtWidgets import QStackedWidget, QWidget


class ResizableStackedWidget(QStackedWidget):
    """QStackedWidget that dynamically shrinks as needed to fit the contents."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def sizeHint(self) -> QSize:
        if not self.currentWidget():
            return super().sizeHint()
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self) -> QSize:
        if not self.currentWidget():
            return super().minimumSizeHint()
        return self.currentWidget().minimumSizeHint()

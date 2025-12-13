import sys

from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frontend_desktop.widgets.basic_code_editor import CodeEditor


class ScrollableErrorDialog(QDialog):
    DEFAULT_SIZE = (400, 500)

    def __init__(
        self,
        error_message: str,
        title: str = "Error",
        parent_percentage: int = 75,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.resize(*self.DEFAULT_SIZE)

        # if parent update size
        if parent:
            self.resize(*self._calculate_size(parent_percentage, parent))

        self.text_edit = CodeEditor(
            line_numbers=False, wrap_text=True, mono_font=True, parent=self
        )
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(error_message)

        copy_button = QPushButton("Copy to Clipboard", self)
        copy_button.clicked.connect(self.copy_to_clipboard)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit, stretch=1)
        layout.addLayout(button_layout)

    def copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    @staticmethod
    def _calculate_size(percentage: int, parent: QWidget) -> tuple[int, int]:
        geometry = parent.geometry()
        width = geometry.width()
        height = geometry.height()
        return int((percentage / 100) * width), int((percentage / 100) * height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    error_msg = "This is a very long error message...\n" * 40
    dlg = ScrollableErrorDialog(error_msg)
    dlg.exec()

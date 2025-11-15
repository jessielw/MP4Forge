from PySide6.QtCore import QTimer
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox, QCompleter


class CustomComboBox(QComboBox):
    def __init__(
        self,
        completer: bool = False,
        completer_strict: bool = True,
        max_items: int = 10,
        disable_mouse_wheel: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.timer = None
        self.completer_strict = completer_strict
        self.disable_mouse_wheel = disable_mouse_wheel

        self.setEditable(True)
        self.setMaxVisibleItems(max_items)

        _line_edit = self.lineEdit()
        _completer = self.completer()
        if not completer:
            if _line_edit:
                _line_edit.setFrame(False)
                _line_edit.setReadOnly(True)
        else:
            self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            if _completer:
                _completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            if _line_edit:
                _line_edit.editingFinished.connect(self.checkEnteredText)

    def checkEnteredText(self):
        entered_text = self.currentText()
        if entered_text not in [self.itemText(i) for i in range(self.count())]:
            if self.timer:
                self.timer.stop()
            self.timer = QTimer(self)
            self.timer.start(1000)
            if self.completer_strict:
                self.setCurrentIndex(0)

    def wheelEvent(self, e: QWheelEvent) -> None:
        if self.disable_mouse_wheel:
            e.ignore()
        else:
            super().wheelEvent(e)

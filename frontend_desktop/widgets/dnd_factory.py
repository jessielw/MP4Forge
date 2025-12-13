from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QToolButton


class DNDMixin:
    accept_dir = False
    accept_text = False
    supported_extensions = None
    dropped = Signal(list)
    text_dropped = Signal(str)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handles drag enter events. Ensures drag is accepted for valid files, directories, or text."""
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                drop = Path(urls[0].toLocalFile())
                if drop.is_file() and drop.exists():
                    if self.supported_extensions:
                        if (
                            "*" in self.supported_extensions
                            or drop.suffix in self.supported_extensions
                        ):
                            event.acceptProposedAction()
                elif drop.is_dir() and self.accept_dir:
                    event.acceptProposedAction()
        elif mime.hasText() and self.accept_text:
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handles drag move events (can be extended to accept moving elements)."""
        pass

    def dropEvent(self, event: QDropEvent):
        """Handles drop events, emitting the dropped signal with file paths."""
        mime = event.mimeData()
        if mime.hasUrls():
            file_urls = [Path(url.toLocalFile()) for url in mime.urls()]
            self.dropped.emit(file_urls)  # pyright: ignore [reportAttributeAccessIssue]
        elif mime.hasText() and self.accept_text:
            self.text_dropped.emit(mime.text())  # pyright: ignore [reportAttributeAccessIssue]

    def set_extensions(self, supported_extensions: Iterable):
        """Sets the supported file extensions for drag-and-drop."""
        self.supported_extensions = supported_extensions

    def set_accept_dir(self, drop_accepted: bool):
        """Sets whether directories are accepted during the drag-and-drop."""
        self.accept_dir = drop_accepted

    def set_accept_text(self, accept: bool):
        """Enables or disables text dropping."""
        self.accept_text = accept


class DNDLineEdit(DNDMixin, QLineEdit):  # pyright: ignore [reportIncompatibleMethodOverride]
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setAcceptDrops(True)


class DNDButton(DNDMixin, QPushButton):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setAcceptDrops(True)


class DNDToolButton(DNDMixin, QToolButton):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setAcceptDrops(True)


class DNDPushButton(DNDMixin, QPushButton):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setAcceptDrops(True)


class DNDPlainTextEdit(DNDMixin, QPlainTextEdit):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setAcceptDrops(True)

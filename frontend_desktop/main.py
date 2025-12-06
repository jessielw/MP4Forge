import sys
import traceback

from PySide6.QtCore import Qt, QtMsgType, Slot, qInstallMessageHandler
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QProgressBar,
    QStatusBar,
    QWidget,
)

from core.config import Conf
from core.logger import LOG
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.nav import NavigationTabs
from frontend_desktop.navigation.tabs.base import BaseTab
from frontend_desktop.tab_registry import get_tab_widget_class
from frontend_desktop.types.nav import Tabs
from frontend_desktop.widgets.resizable_stacked_widget import ResizableStackedWidget
from frontend_desktop.widgets.scrollable_error_dialog import ScrollableErrorDialog
from frontend_desktop.widgets.utils import build_v_line


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mp4Forge")

        # initialize exception handling
        self._setup_exception_hooks()

        # config
        self.conf = Conf

        # hook up signals
        GSigs().main_window_update_status_tip.connect(self.update_status_tip)
        GSigs().main_window_clear_status_tip.connect(self.clear_status_tip)
        GSigs().main_window_set_disabled.connect(self._on_main_window_set_disabled)
        GSigs().main_window_progress_bar_busy.connect(
            self._on_main_window_progress_bar_busy
        )

        # setup status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_progress_bar = QProgressBar(self)
        self.status_progress_bar.setFixedWidth(170)
        self.status_progress_bar.hide()
        self.status_bar.addPermanentWidget(self.status_progress_bar)

        # left nav (buttons only)
        self.nav = NavigationTabs(self)
        self.tabs = {}

        # right: stacked widget built/owned by MainWindow
        self.stacked_widget = ResizableStackedWidget(self)
        self.stacked_widget.setMinimumWidth(500)
        for tab in Tabs:
            WidgetClass = get_tab_widget_class(tab)
            tab_widget: BaseTab = WidgetClass(parent=self)
            self.stacked_widget.addWidget(tab_widget)
            self.tabs[tab] = tab_widget

        # wire nav -> pages
        self.nav.tabRequested.connect(self.stacked_widget.setCurrentIndex)

        # layout
        central = QHBoxLayout()
        central.addWidget(self.nav, stretch=1)
        central.addWidget(build_v_line((1, 1, 1, 1)))
        central.addWidget(self.stacked_widget, stretch=5)

        container = QWidget()
        container.setLayout(central)
        self.setCentralWidget(container)

        # apply config settings after UI is fully initialized
        self._apply_config_on_startup()

    def _apply_config_on_startup(self) -> None:
        """Apply saved configuration settings on application startup"""
        # apply theme
        theme = self.conf.theme
        app = QApplication.instance()
        if theme != "Auto":
            app.styleHints().setColorScheme(  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
                Qt.ColorScheme.Light if theme == "Light" else Qt.ColorScheme.Dark
            )
        else:
            app.styleHints().unsetColorScheme()  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

        # apply log level
        LOG.set_log_level(self.conf.log_level)
        LOG.info(
            f"Applied config - Theme: {theme}, Log Level: {self.conf.log_level.name}"
        )

    def _setup_exception_hooks(self) -> None:
        sys.excepthook = self.exception_handler
        qInstallMessageHandler(self.qt_message_handler)

    def exception_handler(self, exc_type, exc_value, exc_traceback) -> None:
        """Global exception handler for unhandled Python exceptions."""
        full_traceback = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        error_message = f"Unhandled exception:\n{exc_value}\n\n{full_traceback}"
        self._error_message_box("Unhandled Exception", error_message)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def qt_message_handler(self, mode, _context, message) -> None:
        """Handler for Qt-specific warnings and errors."""
        if mode in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ):
            self._error_message_box("QtError", message)

    def _error_message_box(
        self, title: str, message: str, traceback: str | None = None
    ) -> None:
        if traceback:
            traceback = f"\n{traceback}"
        err_msg_box = ScrollableErrorDialog(
            f"{message}{traceback if traceback else ''}",
            title=title,
            parent=self,
        )
        err_msg_box.exec()

    def _on_main_window_set_disabled(self, disabled: bool) -> None:
        self.setDisabled(disabled)

    @Slot(str, int)
    def update_status_tip(self, message: str, timer: int) -> None:
        message = message if message else ""
        if timer > 0:
            self.status_bar.showMessage(message, timer)
        else:
            self.status_bar.showMessage(message)

    @Slot()
    def clear_status_tip(self) -> None:
        self.status_bar.clearMessage()

    @Slot(bool)
    def _on_main_window_progress_bar_busy(self, busy: bool) -> None:
        if busy:
            self.status_progress_bar.setRange(0, 0)
            self.status_progress_bar.show()
        else:
            self.status_progress_bar.hide()
            self.status_progress_bar.setRange(0, 100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

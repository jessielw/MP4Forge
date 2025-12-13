from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from frontend_desktop.navigation.tabs.settings import SettingsTab
from frontend_desktop.tab_registry import get_tab_widget_class
from frontend_desktop.types.nav import Tabs
from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import build_h_line


class NavigationTabs(QWidget):
    """Navigation tab buttons on the left side."""

    tabRequested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.tab_button_group = QButtonGroup(self, exclusive=True)
        self.tab_button_group.idClicked.connect(self.tabRequested)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # loop tabs and build out widgets
        for tab in Tabs:
            info = tab.get_info()
            btn = self._build_tab_btn(info.name, info.icon, True)

            # separate Settings visually
            widget_class = get_tab_widget_class(tab)
            if widget_class is SettingsTab:
                self.main_layout.addWidget(build_h_line((1, 1, 1, 1)))

            self.main_layout.addWidget(btn)
            self.tab_button_group.addButton(btn, tab.value - 1)

        # push all tabs to top
        self.main_layout.addStretch()

        # set default to first tab
        self.tab_button_group.button(0).setChecked(True)

        self.setLayout(self.main_layout)

    def _build_tab_btn(self, text: str, icon_name: str, checkable: bool) -> QToolButton:
        """Build a tab button with the given text, icon, and checkable state."""

        btn = QToolButton(
            parent=self, toolButtonStyle=Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        btn.setCheckable(checkable)
        btn.setText(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        QTAThemeSwap().register(btn, icon_name, icon_size=QSize(32, 32))
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return btn

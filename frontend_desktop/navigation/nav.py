from enum import Enum, auto
from typing import NamedTuple

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from frontend_desktop.navigation.tabs.audio import MultiAudioTab
from frontend_desktop.navigation.tabs.chapters import ChapterTab
from frontend_desktop.navigation.tabs.output import OutputTab
from frontend_desktop.navigation.tabs.settings import SettingsTab
from frontend_desktop.navigation.tabs.subtitles import MultiSubtitleTab
from frontend_desktop.navigation.tabs.video import VideoTab
from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import build_h_line


class TabData(NamedTuple):
    """Data structure for tab information."""

    name: str
    icon: str
    widget_class: type[QWidget]


class Tabs(Enum):
    """Enumeration of the different tabs in the application."""

    Video = auto()
    Audio = auto()
    Subtitles = auto()
    Chapters = auto()
    Output = auto()
    Settings = auto()

    def get_tab_info(self) -> TabData:
        """Returns the tab display name, icon name, and associated widget class."""
        specs = {
            Tabs.Video: TabData("Video", "mdi.video-outline", VideoTab),
            Tabs.Audio: TabData("Audio", "mdi.music-note", MultiAudioTab),
            Tabs.Subtitles: TabData(
                "Subtitles", "mdi.card-text-outline", MultiSubtitleTab
            ),
            Tabs.Chapters: TabData(
                "Chapters", "mdi.bookmark-minus-outline", ChapterTab
            ),
            Tabs.Output: TabData("Output", "mdi.page-next-outline", OutputTab),
            Tabs.Settings: TabData("Settings", "mdi.cog-outline", SettingsTab),
        }
        return specs[self]


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
            text, icon_name, WidgetClass = tab.get_tab_info()
            btn = self._build_tab_btn(text, icon_name, True)

            # separate Settings visually
            if WidgetClass is SettingsTab:
                self.main_layout.addStretch()
                self.main_layout.addSpacing(8)
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

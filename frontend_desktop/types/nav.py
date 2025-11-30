from enum import Enum, auto
from typing import NamedTuple


class TabInfo(NamedTuple):
    """Static tab information (no widget dependencies)."""

    name: str
    icon: str


class Tabs(Enum):
    """Enumeration of the different tabs in the application."""

    Video = auto()
    Audio = auto()
    Subtitles = auto()
    Chapters = auto()
    Output = auto()
    Settings = auto()

    def get_info(self) -> TabInfo:
        """Returns the tab display name and icon."""
        specs = {
            Tabs.Video: TabInfo("Video", "mdi.video-outline"),
            Tabs.Audio: TabInfo("Audio", "mdi.music-note"),
            Tabs.Subtitles: TabInfo("Subtitles", "mdi.card-text-outline"),
            Tabs.Chapters: TabInfo("Chapters", "mdi.bookmark-minus-outline"),
            Tabs.Output: TabInfo("Output", "mdi.page-next-outline"),
            Tabs.Settings: TabInfo("Settings", "mdi.cog-outline"),
        }
        return specs[self]

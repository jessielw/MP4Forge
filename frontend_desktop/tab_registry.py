"""Central registry for tab widget classes.

Prevents circular dependency by keeping widget class references
separate from the Tabs enum.
"""

from frontend_desktop.navigation.tabs.base import BaseTab
from frontend_desktop.types.nav import Tabs


def get_tab_widget_class(tab: Tabs) -> type[BaseTab]:
    """Get the widget class for a given tab.

    Import happens here at runtime, avoiding circular dependencies.
    """
    from frontend_desktop.navigation.tabs.audio import MultiAudioTab
    from frontend_desktop.navigation.tabs.chapters import ChapterTab
    from frontend_desktop.navigation.tabs.output import OutputTab
    from frontend_desktop.navigation.tabs.settings import SettingsTab
    from frontend_desktop.navigation.tabs.subtitles import MultiSubtitleTab
    from frontend_desktop.navigation.tabs.video import VideoTab

    registry = {
        Tabs.Video: VideoTab,
        Tabs.Audio: MultiAudioTab,
        Tabs.Subtitles: MultiSubtitleTab,
        Tabs.Chapters: ChapterTab,
        Tabs.Output: OutputTab,
        Tabs.Settings: SettingsTab,
    }

    return registry[tab]

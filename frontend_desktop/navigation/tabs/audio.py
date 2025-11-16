import re
from dataclasses import dataclass
from pathlib import Path

from iso639 import Language
from pymediainfo import MediaInfo
from PySide6.QtWidgets import QTreeWidgetItem, QVBoxLayout, QWidget
from typing_extensions import override

from core.utils.language import get_full_language_str
from frontend_desktop.navigation.tabs.base import BaseTab, BaseTabState
from frontend_desktop.widgets.multi_tabbed_widget import MultiTabbedTabWidget


@dataclass(frozen=True, slots=True)
class AudioTabState(BaseTabState):
    """Data structure for exporting the state of the Audio tab."""

    input_file: Path
    language: Language | None
    title: str
    delay_ms: int


class AudioTab(BaseTab[AudioTabState]):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("AudioTab")

    @override
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        lang = media_info.audio_tracks[0].language if media_info.audio_tracks else None
        if lang:
            full_lang = get_full_language_str(lang)
            if full_lang:
                # find index in combo box
                index = self.lang_combo.findText(full_lang)
                if index != -1:
                    self.lang_combo.setCurrentIndex(index)
        else:
            self.lang_combo.setCurrentIndex(0)

    @override
    def _load_title(self, media_info: MediaInfo) -> None:
        """Loads title from media info into the title entry."""
        title = ""
        if media_info.audio_tracks:
            title = media_info.audio_tracks[0].title or ""
        self.title_entry.setText(title)

    @override
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        self.media_info_tree.clear()
        if not media_info.audio_tracks:
            no_item = QTreeWidgetItem(self.media_info_tree)
            no_item.setText(0, "No audio track found")
            no_item.setText(1, "")
            return

        track = media_info.audio_tracks[0]
        for key, value in track.to_data().items():
            # skip 'other_' keys
            if "track_type" == key or key.startswith("other_"):
                continue
            row = QTreeWidgetItem(self.media_info_tree)
            row.setText(0, str(key))
            row.setText(1, "" if value is None else str(value))

        self.media_info_tree.resizeColumnToContents(0)

    @override
    def _load_delay(self, media_info: MediaInfo, file_path: Path) -> None:
        """
        Loads delay from filename pattern (e.g., 'audio_DELAY_100ms.aac')
        or falls back to mediainfo.
        """
        delay = 0

        # Try parsing delay from filename first (common pattern: DELAY 100ms or similar)
        filename = file_path.stem
        delay_match = re.search(r"DELAY[_\s]+(-?\d+)ms", filename, re.IGNORECASE)
        if delay_match:
            delay = int(delay_match.group(1))
        elif media_info.audio_tracks:
            # Fallback to mediainfo
            src_delay = media_info.audio_tracks[0].source_delay
            reg_delay = media_info.audio_tracks[0].delay
            if src_delay is not None:
                delay = int(src_delay)
            elif reg_delay is not None:
                delay = int(reg_delay)

        self.delay_spinbox.setValue(delay)

    @override
    def export_state(self) -> AudioTabState:
        """Exports the current state."""
        return AudioTabState(
            input_file=Path(self.input_entry.text().strip()),
            language=self.lang_combo.currentData(),
            title=self.title_entry.text().strip(),
            delay_ms=self.delay_spinbox.value(),
        )

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether ready for muxing."""
        return bool(self.input_entry.text().strip())


class MultiAudioTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MultiAudioTab")

        self.multi_track = MultiTabbedTabWidget(
            parent=self, widget_class=AudioTab, tab_name="Track", initial_count=1
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.multi_track)

    def export_all_audio_states(self) -> list[AudioTabState]:
        """Export states from all audio track tabs."""
        states = []
        for widget in self.multi_track.get_all_tab_widgets():
            if hasattr(widget, "export_state"):
                states.append(getattr(widget, "export_state")())
        return states

    def are_all_tabs_ready(self) -> bool:
        """Check if all audio track tabs are ready."""
        for widget in self.multi_track.get_all_tab_widgets():
            if hasattr(widget, "is_tab_ready"):
                if not getattr(widget, "is_tab_ready")():
                    return False
        return True

    def reset_all_tabs(self) -> None:
        """Reset all tab widgets to default state."""
        for widget in self.multi_track.get_all_tab_widgets():
            if hasattr(widget, "reset_tab"):
                widget.reset_tab()  # type: ignore

from dataclasses import dataclass
from pathlib import Path

from iso639 import Language
from pymediainfo import MediaInfo
from PySide6.QtWidgets import QTreeWidgetItem
from typing_extensions import override

from core.utils.language import get_full_language_str
from frontend_desktop.navigation.tabs.base import BaseTab, BaseTabState


@dataclass(frozen=True, slots=True)
class VideoTabState(BaseTabState):
    """Data structure for exporting the state of the Video tab."""

    input_file: Path
    language: Language | None
    title: str
    delay_ms: int


class VideoTab(BaseTab[VideoTabState]):
    """Tab for video file input and settings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("VideoTab")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addStretch()

    @override
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        lang = media_info.video_tracks[0].language if media_info.video_tracks else None
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
        if media_info.video_tracks:
            title = media_info.video_tracks[0].title or ""
        self.title_entry.setText(title)

    @override
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        self.media_info_tree.clear()
        if not media_info.video_tracks:
            no_item = QTreeWidgetItem(self.media_info_tree)
            no_item.setText(0, "No video track found")
            no_item.setText(1, "")
            return

        track = media_info.video_tracks[0]
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
        """Loads delay from media info into the delay entry."""
        delay = 0
        if media_info and media_info.video_tracks:
            # mp4 delay
            src_delay = media_info.video_tracks[0].source_delay
            # delay in every other container
            reg_delay = media_info.video_tracks[0].delay
            if src_delay is not None:
                delay = int(src_delay)
            elif reg_delay is not None:
                delay = int(reg_delay)
        self.delay_spinbox.setValue(delay)

    @override
    def export_state(self) -> VideoTabState:
        """Exports the current state of the tab as a VideoTabState."""
        state = VideoTabState(
            input_file=Path(self.input_entry.text().strip()),
            language=self.lang_combo.currentData(),
            title=self.title_entry.text().strip(),
            delay_ms=self.delay_spinbox.value(),
        )
        return state

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether the tab is ready for muxing."""
        return bool(self.input_entry.text().strip())

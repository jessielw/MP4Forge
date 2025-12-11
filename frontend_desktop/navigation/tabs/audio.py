import re
from pathlib import Path
from typing import Any

from pymediainfo import MediaInfo
from PySide6.QtWidgets import (
    QMessageBox,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import override

from core.job_states import AudioState
from core.utils.language import get_full_language_str
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.tabs.base import BaseTab
from frontend_desktop.widgets.multi_tabbed_widget import MultiTabbedTabWidget
from frontend_desktop.widgets.track_selector_dialog import TrackSelectorDialog


class AudioTab(BaseTab[AudioState]):
    def __init__(self, parent=None):
        super().__init__(
            file_dialog_filters="Audio Files (*.ac3 *.aac *.mp4 *.m4a *.mp2 *.mp3 *.opus *.ogg *.eac3 *.ec3)",
            dnd_extensions=(
                ".ac3",
                ".aac",
                ".mp4",
                ".m4a",
                ".mp2",
                ".mp3",
                ".opus",
                ".ogg",
                ".eac3",
                ".ec3",
            ),
            parent=parent,
        )
        self.setObjectName("AudioTab")

        # audio tracks only have default flag, not forced
        self.forced_checkbox.hide()

        # track_id: MediaInfo track ID (e.g., 1, 2, 3) - used for MP4Box #N selector
        # for MediaInfo array access: iterate audio_tracks directly (already filtered)
        self.selected_track_id: int | None = None

    @override
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        # find track by track_id in audio_tracks array
        lang = None
        if self.selected_track_id is not None:
            for track in media_info.audio_tracks:
                if track.track_id == self.selected_track_id:
                    lang = track.language
                    break

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
        # find track by track_id in audio_tracks array
        if self.selected_track_id is not None:
            for track in media_info.audio_tracks:
                if track.track_id == self.selected_track_id:
                    title = track.title or ""
                    break
        self.title_entry.setText(title)

    def _load_default_flag(self, media_info: MediaInfo) -> None:
        """Load default flag from media info."""
        is_default = False
        if self.selected_track_id is not None:
            for track in media_info.audio_tracks:
                if track.track_id == self.selected_track_id:
                    # check if track is marked as default
                    default_val = getattr(track, "default", None)
                    if default_val and str(default_val).lower() in ("yes", "true", "1"):
                        is_default = True
                    break
        self.default_checkbox.setChecked(is_default)

    @override
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        self.media_info_tree.clear()
        if not media_info.audio_tracks:
            no_item = QTreeWidgetItem(self.media_info_tree)
            no_item.setText(0, "No audio track found")
            no_item.setText(1, "")
            QMessageBox.warning(
                self,
                "No Audio Track Found",
                "The selected file does not contain any audio tracks.",
            )
            self.reset_tab()
            return

        # check if MP4 with multiple audio tracks
        file_path = Path(self.input_entry.text().strip())
        is_mp4 = file_path.suffix.lower() in (".mp4", ".m4a")

        if (
            is_mp4
            and len(media_info.audio_tracks) > 1
            and self.selected_track_id is None
        ):
            # show track selector dialog only if track not already selected
            dialog = TrackSelectorDialog(file_path, parent=self)
            if dialog.exec():
                # returns MediaInfo track_id (used for MP4Box #N)
                self.selected_track_id = dialog.get_selected_track_id()
                # find track by track_id in audio_tracks array
                track = media_info.audio_tracks[0]  # default
                if self.selected_track_id is not None:
                    for audio_track in media_info.audio_tracks:
                        if audio_track.track_id == self.selected_track_id:
                            track = audio_track
                            break
            else:
                # user cancelled
                self.reset_tab()
                return
        elif (
            is_mp4
            and len(media_info.audio_tracks) > 1
            and self.selected_track_id is not None
        ):
            # track already selected (from video auto-population), find it
            track = media_info.audio_tracks[0]  # default
            for audio_track in media_info.audio_tracks:
                if audio_track.track_id == self.selected_track_id:
                    track = audio_track
                    break
        else:
            # single track or non-MP4 - use first track
            track = media_info.audio_tracks[0]
            self.selected_track_id = track.track_id or 1

        # populate tree with selected track info
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

        # check if file is an elementary file
        gen_track = media_info.general_tracks[0]
        v_count = self._parse_mi_count(gen_track.count_of_video_streams)
        a_count = self._parse_mi_count(gen_track.count_of_audio_streams)
        s_count = self._parse_mi_count(gen_track.count_of_text_streams)
        m_count = self._parse_mi_count(gen_track.count_of_menu_streams)
        track_count = sum((v_count, a_count, s_count, m_count))
        if track_count == 1:
            filename = file_path.stem
            delay_match = re.search(r"DELAY[_\s]+(-?\d+)ms", filename, re.IGNORECASE)
            if delay_match:
                delay = int(delay_match.group(1))

        # if not an elementary file, only use delay if a specific track was selected
        elif track_count > 1 and self.selected_track_id is not None:
            # find track by track_id in audio_tracks array
            for track in media_info.audio_tracks:
                if track.track_id == self.selected_track_id:
                    src_delay = track.source_delay
                    reg_delay = track.delay
                    if src_delay is not None:
                        delay = int(src_delay)
                    elif reg_delay is not None:
                        delay = int(reg_delay)
                    break

        self.delay_spinbox.setValue(delay)

    @override
    def export_state(self) -> AudioState | None:
        """Exports the current state."""
        return (
            AudioState(
                input_file=Path(self.input_entry.text().strip()),
                language=self.lang_combo.currentData(),
                title=self.title_entry.text().strip(),
                delay_ms=self.delay_spinbox.value(),
                default=self.default_checkbox.isChecked(),
                track_id=self.selected_track_id,
            )
            if self.is_tab_ready()
            else None
        )

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether ready for muxing."""
        return bool(self.input_entry.text().strip())

    @staticmethod
    def _parse_mi_count(val: Any, default: int = 0) -> int:
        """Parse media info count value to int, defaulting to 0."""
        try:
            return int(val)
        except (TypeError, ValueError):
            return default


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

        # connect to video audio tracks signal
        GSigs().video_audio_tracks_detected.connect(self._handle_video_audio_tracks)

    def export_all_audio_states(self) -> list[AudioState]:
        """Export states from all audio track tabs (only tabs with input files)."""
        states = []
        for widget in self.multi_track.get_all_tab_widgets():
            export_state = getattr(widget, "export_state", None)
            if export_state:
                state = export_state()
                if state:  # only include tabs with actual input
                    states.append(state)
        return states

    def reset_all_tabs(self) -> None:
        """Reset all tab widgets to default state."""
        for widget in self.multi_track.get_all_tab_widgets():
            if hasattr(widget, "reset_tab"):
                widget.reset_tab()  # type: ignore

    def _handle_video_audio_tracks(
        self, media_info: MediaInfo, file_path: Path, selected_track_ids: list[int]
    ) -> None:
        """Handle audio tracks detected in video file."""
        # filter to only selected tracks
        selected_tracks = [
            track
            for track in media_info.audio_tracks
            if track.track_id in selected_track_ids
        ]

        if not selected_tracks:
            return

        # reset to single tab first
        self.multi_track.reset_to_single_tab()

        # create tabs for each selected audio track
        for idx, track in enumerate(selected_tracks):
            if idx > 0:  # first tab already exists
                self.multi_track.add_new_tab()

            # get the tab widget (we know it's an AudioTab)
            tab_widget: AudioTab = self.multi_track.get_all_tab_widgets()[idx]  # type: ignore

            # simulate file drop to populate the tab
            tab_widget._handle_dropped_file([str(file_path)])

            # set the selected track ID for this specific track
            tab_widget.selected_track_id = track.track_id

from pathlib import Path

from pymediainfo import MediaInfo
from PySide6.QtWidgets import (
    QMessageBox,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import override

from core.job_states import SubtitleState
from core.utils.language import get_full_language_str
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.tabs.base import BaseTab
from frontend_desktop.widgets.multi_tabbed_widget import MultiTabbedTabWidget
from frontend_desktop.widgets.track_selector_dialog import TrackSelectorDialog


class SubtitleTab(BaseTab[SubtitleState]):
    def __init__(self, parent=None):
        super().__init__(
            file_dialog_filters="Subtitle Files (*.srt *.idx *.ttxt *.mp4 *.m4v)",
            dnd_extensions=(".srt", ".idx", ".ttxt", ".mp4", ".m4v"),
            parent=parent,
        )
        self.setObjectName("SubtitleTab")

        # track_id: MediaInfo track ID - used for MP4Box #N selector
        self.selected_track_id: int | None = None

    @override
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        lang = None
        if self.selected_track_id is not None:
            for track in media_info.text_tracks:
                if track.track_id == self.selected_track_id:
                    lang = track.language
                    break

        if lang:
            full_lang = get_full_language_str(lang)
            if full_lang:
                index = self.lang_combo.findText(full_lang)
                if index != -1:
                    self.lang_combo.setCurrentIndex(index)
        else:
            self.lang_combo.setCurrentIndex(0)

    @override
    def _load_title(self, media_info: MediaInfo) -> None:
        """Loads title from media info into the title entry."""
        title = ""
        if self.selected_track_id is not None:
            for track in media_info.text_tracks:
                if track.track_id == self.selected_track_id:
                    title = track.title or ""
                    break
        self.title_entry.setText(title)

    @override
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        self.media_info_tree.clear()
        if not media_info.text_tracks:
            no_item = QTreeWidgetItem(self.media_info_tree)
            no_item.setText(0, "No subtitle track found")
            no_item.setText(1, "")
            QMessageBox.warning(
                self,
                "No Subtitle Track Found",
                "The selected file does not contain any subtitle tracks.",
            )
            self.reset_tab()
            return

        # check if MP4 with multiple subtitle tracks
        file_path = Path(self.input_entry.text().strip())
        is_mp4 = file_path.suffix.lower() in (".mp4", ".m4v")

        if (
            is_mp4
            and len(media_info.text_tracks) > 1
            and self.selected_track_id is None
        ):
            # show track selector dialog only if track not already selected
            dialog = TrackSelectorDialog(file_path, track_type="text", parent=self)
            if dialog.exec():
                self.selected_track_id = dialog.get_selected_track_id()
                # find track by track_id
                track = media_info.text_tracks[0]  # default
                if self.selected_track_id is not None:
                    for text_track in media_info.text_tracks:
                        if text_track.track_id == self.selected_track_id:
                            track = text_track
                            break
            else:
                # user cancelled
                self.reset_tab()
                return
        elif (
            is_mp4
            and len(media_info.text_tracks) > 1
            and self.selected_track_id is not None
        ):
            # track already selected (from video auto-population), find it
            track = media_info.text_tracks[0]  # default
            for text_track in media_info.text_tracks:
                if text_track.track_id == self.selected_track_id:
                    track = text_track
                    break
        else:
            # single track or non-MP4 - use first track
            track = media_info.text_tracks[0]
            self.selected_track_id = track.track_id or 1

        # populate tree with selected track info
        for key, value in track.to_data().items():
            if "track_type" == key or key.startswith("other_"):
                continue
            row = QTreeWidgetItem(self.media_info_tree)
            row.setText(0, str(key))
            row.setText(1, "" if value is None else str(value))

        self.media_info_tree.resizeColumnToContents(0)

    @override
    def _load_delay(self, media_info: MediaInfo, file_path: Path) -> None:
        """Subtitle tracks don't use delay."""
        pass

    def _load_default_flag(self, media_info: MediaInfo) -> None:
        """Load default flag from media info."""
        is_default = False
        if self.selected_track_id is not None:
            for track in media_info.text_tracks:
                if track.track_id == self.selected_track_id:
                    # check if track is marked as default
                    default_val = getattr(track, "default", None)
                    if default_val and str(default_val).lower() in ("yes", "true", "1"):
                        is_default = True
                    break
        self.default_checkbox.setChecked(is_default)

    def _load_forced_flag(self, media_info: MediaInfo) -> None:
        """Load forced flag from media info."""
        is_forced = False
        if self.selected_track_id is not None:
            for track in media_info.text_tracks:
                if track.track_id == self.selected_track_id:
                    # check if track is marked as forced
                    forced_val = getattr(track, "forced", None)
                    if forced_val and str(forced_val).lower() in ("yes", "true", "1"):
                        is_forced = True
                    break
        self.forced_checkbox.setChecked(is_forced)

    @override
    def export_state(self) -> SubtitleState | None:
        """Exports the current state."""
        return (
            SubtitleState(
                input_file=Path(self.input_entry.text().strip()),
                language=self.lang_combo.currentData(),
                title=self.title_entry.text().strip(),
                default=self.default_checkbox.isChecked(),
                forced=self.forced_checkbox.isChecked(),
                track_id=self.selected_track_id,
            )
            if self.is_tab_ready()
            else None
        )

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether ready for muxing."""
        return bool(self.input_entry.text().strip())


class MultiSubtitleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MultiSubtitleTab")

        self.multi_track = MultiTabbedTabWidget(
            parent=self,
            widget_class=SubtitleTab,
            tab_name="Track",
            initial_count=1,
            add_widget_cb=self._on_new_subtitle_widget_added,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.multi_track)

        # connect to video subtitle tracks signal
        GSigs().video_subtitle_tracks_detected.connect(
            self._handle_video_subtitle_tracks
        )

    def _on_new_subtitle_widget_added(self, widget: QWidget) -> None:
        """Hide delay controls in all subtitle tabs."""
        sub_tab: SubtitleTab = widget  # type: ignore
        sub_tab.delay_lbl.hide()
        sub_tab.delay_spinbox.hide()
        sub_tab.media_info_tree_lbl.hide()
        sub_tab.media_info_tree.hide()
        sub_tab.main_layout.addStretch()

    def export_all_subtitle_states(self) -> list[SubtitleState]:
        """Export states from all subtitle track tabs (only tabs with input files)."""
        states = []
        for widget in self.multi_track.get_all_tab_widgets():
            export_state = getattr(widget, "export_state", None)
            if export_state:
                state = export_state()
                if state:  # only include tabs with actual input
                    states.append(state)
        return states

    def _handle_video_subtitle_tracks(
        self, media_info: MediaInfo, file_path: Path, selected_track_ids: list[int]
    ) -> None:
        """Handle subtitle tracks detected in video file."""
        # filter to only selected tracks
        selected_tracks = [
            track
            for track in media_info.text_tracks
            if track.track_id in selected_track_ids
        ]

        if not selected_tracks:
            return

        # reset to single tab first
        self.multi_track.reset_to_single_tab()

        # create tabs for each selected subtitle track
        for idx, track in enumerate(selected_tracks):
            if idx > 0:  # first tab already exists
                self.multi_track.add_new_tab()

            # get the tab widget (we know it's a SubtitleTab)
            tab_widget: SubtitleTab = self.multi_track.get_all_tab_widgets()[idx]  # type: ignore

            # simulate file drop to populate the tab
            tab_widget._handle_dropped_file([str(file_path)])

            # set the selected track ID for this specific track
            tab_widget.selected_track_id = track.track_id

    def reset_all_tabs(self) -> None:
        """Reset all tab widgets to default state."""
        for widget in self.multi_track.get_all_tab_widgets():
            if hasattr(widget, "reset_tab"):
                widget.reset_tab()  # type: ignore

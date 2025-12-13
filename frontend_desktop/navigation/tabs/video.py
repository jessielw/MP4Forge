from pathlib import Path

from pymediainfo import MediaInfo
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox, QTreeWidgetItem
from typing_extensions import override

from core.job_states import VideoState
from core.logger import LOG
from core.utils.autoqpf import auto_gen_chapters
from core.utils.language import get_full_language_str
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.tabs.base import BaseTab
from frontend_desktop.widgets.track_import_dialog import TrackImportDialog


class VideoTab(BaseTab[VideoState]):
    """Tab for video file input and settings."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            file_dialog_filters="Video Files (*.avi *.mp4 *.m1v *.m2v *.m4v *.264 *.h264 *.hevc *.h265 *.avc)",
            dnd_extensions=(
                ".avi",
                ".mp4",
                ".m1v",
                ".m2v",
                ".m4v",
                ".264",
                ".h264",
                ".hevc",
                ".h265",
                ".avc",
            ),
            parent=parent,
        )
        self.setObjectName("VideoTab")

        # video tracks don't use default/forced flags
        self.default_checkbox.hide()
        self.forced_checkbox.hide()

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addStretch()

    @override
    @Slot(tuple)
    def _on_media_info_finished(self, result: tuple[MediaInfo, Path]) -> None:
        media_info, file_path = result

        # detect title if exists in the mediainfo
        v_track = media_info.video_tracks[0] if media_info.video_tracks else None

        # if no video track found show error and return
        if not v_track:
            failure_msg = f"No video track found in file: {file_path}"
            LOG.critical(failure_msg, LOG.SRC.FE)
            QMessageBox.critical(
                self,
                "No Video Track Found",
                failure_msg,
            )
            self._parse_file_done()
            self.reset_tab()
            return

        # load title if exists
        if v_track and v_track.title:
            self.title_entry.setText(v_track.title)

        # show track import dialog only for mp4/m4v files with audio/subtitle/chapter tracks
        is_mp4 = file_path.suffix.lower() in (".mp4", ".m4v")
        has_audio = bool(media_info.audio_tracks)
        has_subs = bool(media_info.text_tracks)
        has_chapters = bool(media_info.menu_tracks)

        if is_mp4 and (has_audio or has_subs or has_chapters):
            dialog = TrackImportDialog(file_path, media_info, parent=self)
            if dialog.exec():
                selected = dialog.get_selected_tracks()

                # emit signals for selected tracks
                if selected["audio"]:
                    GSigs().video_audio_tracks_detected.emit(
                        media_info, file_path, selected["audio"]
                    )

                if selected["subtitle"]:
                    GSigs().video_subtitle_tracks_detected.emit(
                        media_info, file_path, selected["subtitle"]
                    )

                # extract and emit chapters only if selected
                if selected["chapters"]:
                    try:
                        chapters = auto_gen_chapters(media_info)
                        if chapters:
                            GSigs().chapters_updated.emit(chapters)
                    except Exception:
                        pass

                # show status tip about imported tracks
                LOG.info(
                    f"Imported {selected['imported_track_count']} tracks from video file: {file_path}",
                    LOG.SRC.FE,
                )
                LOG.debug(f"Imported tracks detail: {selected}", LOG.SRC.FE)

            # if user cancels, we just don't import audio/subs/chapters
        else:
            # non-MP4 or no extra tracks - just try to extract chapters anyway
            try:
                chapters = auto_gen_chapters(media_info)
                if chapters:
                    GSigs().chapters_updated.emit(chapters)
            except Exception:
                LOG.debug(
                    "Failed to auto-generate chapters from video file", LOG.SRC.FE
                )

        # emit signal to suggest output filepath generation
        GSigs().video_generate_output_filepath.emit(
            Path(str(file_path.with_suffix("")) + "_new.mp4")
        )

        self._update_ui(media_info, file_path)
        self._parse_file_done()

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
    def export_state(self) -> VideoState | None:
        """Exports the current state of the tab as a VideoState."""
        return (
            VideoState(
                input_file=Path(self.input_entry.text().strip()),
                language=self.lang_combo.currentData(),
                title=self.title_entry.text().strip(),
                delay_ms=self.delay_spinbox.value(),
            )
            if self.is_tab_ready()
            else None
        )

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether the tab is ready for muxing."""
        return bool(self.input_entry.text().strip())

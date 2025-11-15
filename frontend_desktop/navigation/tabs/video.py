from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from iso639 import Language
from pymediainfo import MediaInfo
from PySide6.QtCore import QSize, Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)
from typing_extensions import override

from core.utils.language import get_full_language_str
from core.utils.mediainfo import get_media_info
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.tabs.base import BaseTab, BaseTabState
from frontend_desktop.utils.general_worker import GeneralWorker
from frontend_desktop.widgets.dnd_factory import DNDLineEdit, DNDPushButton
from frontend_desktop.widgets.lang_combo import get_language_combo_box
from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import cancel_scroll_event


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
        super().__init__(parent)
        self.setObjectName("VideoTab")

        # media info worker
        self._media_info_worker: GeneralWorker | None = None

        # open file button
        self.open_file_btn = DNDPushButton(self)
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.setToolTip("Open file")
        QTAThemeSwap().register(
            self.open_file_btn, "ph.file-arrow-up", icon_size=QSize(24, 24)
        )
        self.open_file_btn.clicked.connect(self._open_file_dialog)

        # input file entry
        self.input_entry = DNDLineEdit(self, readOnly=True)
        self.input_entry.setToolTip("Open file...")
        self.input_entry.setPlaceholderText(self.input_entry.toolTip())

        # enable drag and drop for input widgets
        for dnd_widget in (self.open_file_btn, self.input_entry):
            dnd_widget.set_extensions(("*",))
            dnd_widget.dropped.connect(self._handle_dropped_file)

        # timer for resetting UI after another click
        self._reset_timer = QTimer(self, interval=3000)
        self._reset_timer.timeout.connect(self._reset_tab_clicked)

        # reset tab button
        self.reset_tab_btn = QPushButton(self)
        self.reset_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_tab_btn.setToolTip("Reset tab")
        QTAThemeSwap().register(self.reset_tab_btn, "ph.trash", icon_size=QSize(24, 24))
        self.reset_tab_btn.clicked.connect(self._reset_tab_clicked)

        row_1_layout = QHBoxLayout()
        row_1_layout.setContentsMargins(0, 0, 0, 0)
        row_1_layout.addWidget(self.open_file_btn)
        row_1_layout.addWidget(self.input_entry, stretch=1)
        row_1_layout.addWidget(self.reset_tab_btn)

        # language selection
        lang_lbl = QLabel("Language", self)
        self.lang_combo = get_language_combo_box(self)

        # title entry
        title_lbl = QLabel("Title", self)
        self.title_entry = QLineEdit(self, placeholderText="Enter title...")

        # delay entry
        delay_lbl = QLabel("Delay (ms)", self)
        self.delay_spinbox = QSpinBox(self, minimum=-999999, maximum=999999, value=0)
        self.delay_spinbox.wheelEvent = cancel_scroll_event

        # media info tree
        media_info_tree_lbl = QLabel("MediaInfo", self)
        self.media_info_tree = QTreeWidget(self, columnCount=2)
        self.media_info_tree.setFrameShape(QFrame.Shape.Box)
        self.media_info_tree.setFrameShadow(QFrame.Shadow.Sunken)
        self.media_info_tree.setHeaderLabels(["Property", "Value"])
        self.media_info_tree.setRootIsDecorated(False)
        self.media_info_tree.setIndentation(0)

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(row_1_layout)
        self.main_layout.addWidget(lang_lbl)
        self.main_layout.addWidget(self.lang_combo)
        self.main_layout.addWidget(title_lbl)
        self.main_layout.addWidget(self.title_entry)
        self.main_layout.addWidget(delay_lbl)
        self.main_layout.addWidget(self.delay_spinbox)
        self.main_layout.addWidget(media_info_tree_lbl)
        self.main_layout.addWidget(self.media_info_tree, stretch=1)
        self.main_layout.addStretch()

    @Slot()
    def _open_file_dialog(self) -> None:
        """Opens a file dialog to select a video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Media Files (*)",
        )
        if file_path:
            self._handle_dropped_file((file_path,))

    @Slot(list)
    def _handle_dropped_file(self, file_paths: Sequence[str]) -> None:
        """Handles a dropped file."""
        self._stop_reset_timer()
        drop_path = Path(file_paths[0]).resolve()
        str_drop = str(drop_path)
        self.input_entry.setText(str_drop)
        self.input_entry.setToolTip(str_drop)

        # run media info worker
        self._media_info_worker = GeneralWorker(
            func=get_media_info, parent=self, file_path=drop_path
        )
        self._media_info_worker.job_finished.connect(self._on_media_info_finished)
        self._media_info_worker.job_failed.connect(self._on_media_info_failed)
        GSigs().main_window_update_status_tip.emit("Parsing input...", 0)
        GSigs().main_window_set_disabled.emit(True)
        GSigs().main_window_progress_bar_busy.emit(True)
        self._media_info_worker.start()

    @Slot(object)
    def _on_media_info_finished(self, media_info: MediaInfo) -> None:
        """ "Handles the media info worker finished signal."""
        self._update_ui(media_info)
        self._parse_file_done()

    @Slot(str)
    def _on_media_info_failed(self, error_message: str) -> None:
        """Handles the media info worker failed signal."""
        # handle media info error
        # TODO: display the error in the UI either via a GSIG global or per widget?
        print("Media info retrieval failed:", error_message)
        self._parse_file_done()

    def _update_ui(self, media_info: MediaInfo) -> None:
        """Updates the UI with the provided media info."""
        self._load_language(media_info)
        self._load_title(media_info)
        self._load_media_info_into_tree(media_info)
        self._load_delay(media_info)

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

    def _load_title(self, media_info: MediaInfo) -> None:
        """Loads title from media info into the title entry."""
        title = ""
        if media_info.video_tracks:
            title = media_info.video_tracks[0].title or ""
        self.title_entry.setText(title)

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

    def _load_delay(self, media_info: MediaInfo) -> None:
        """Loads delay from media info into the delay entry."""
        delay = 0
        if media_info.video_tracks:
            # mp4 delay
            src_delay = media_info.video_tracks[0].source_delay
            # delay in every other container
            reg_delay = media_info.video_tracks[0].delay
            if src_delay is not None:
                delay = int(src_delay)
            elif reg_delay is not None:
                delay = int(reg_delay)
        self.delay_spinbox.setValue(delay)

    def _parse_file_done(self) -> None:
        """Cleans up UI after file parsing is done."""
        GSigs().main_window_clear_status_tip.emit()
        GSigs().main_window_set_disabled.emit(False)
        GSigs().main_window_progress_bar_busy.emit(False)

    @Slot()
    def _reset_tab_clicked(self) -> None:
        """
        Calls `reset_tab` if the timer is active,
        otherwise it starts the timer and calls the children
        method `apply_defaults`
        """
        if self._reset_timer.isActive():
            self.reset_tab()
            self._stop_reset_timer()
        else:
            self.reset_tab_btn.setText("Confirm?")
            self._reset_timer.start(3000)

    def _stop_reset_timer(self) -> None:
        """Stops the reset timer if active."""
        if self._reset_timer.isActive():
            self._reset_timer.stop()
        self.reset_tab_btn.setText("")

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

    @Slot()
    @override
    def reset_tab(self) -> None:
        """Resets all input fields to default state."""
        self.input_entry.clear()
        self.input_entry.setToolTip("Open file...")
        self.lang_combo.setCurrentIndex(0)
        self.title_entry.clear()
        self.delay_spinbox.setValue(0)
        self.media_info_tree.clear()

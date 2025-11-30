from abc import abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Generic, Protocol, TypeVar

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
    QVBoxLayout,
    QWidget,
)

from core.utils.mediainfo import get_media_info
from frontend_desktop.global_signals import GSigs
from frontend_desktop.utils.general_worker import GeneralWorker
from frontend_desktop.widgets.dnd_factory import DNDLineEdit, DNDPushButton
from frontend_desktop.widgets.lang_combo import get_language_combo_box
from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import cancel_scroll_event


class TabState(Protocol):
    """Protocol for tab state objects (duck typing)."""

    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        ...


TState = TypeVar("TState", bound=TabState)


class BaseTab(QWidget, Generic[TState]):
    """Base class for all tabs."""

    def __init__(
        self,
        file_dialog_filters: str = "Media Files (*)",
        dnd_extensions: tuple[str, ...] = ("*",),
        parent=None,
    ) -> None:
        super().__init__(parent)

        # instance variables for file filtering (subclasses can override)
        self._file_dialog_filter = file_dialog_filters
        self._dnd_extensions = dnd_extensions

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
        self._configure_file_filters()

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
        self.lang_lbl = QLabel("Language", self)
        self.lang_combo = get_language_combo_box(self)

        # title entry
        self.title_lbl = QLabel("Title", self)
        self.title_entry = QLineEdit(self, placeholderText="Enter title...")

        # delay entry
        self.delay_lbl = QLabel("Delay (ms)", self)
        self.delay_spinbox = QSpinBox(self, minimum=-999999, maximum=999999, value=0)
        self.delay_spinbox.wheelEvent = cancel_scroll_event

        # media info tree
        self.media_info_tree_lbl = QLabel("MediaInfo", self)
        self.media_info_tree = QTreeWidget(self, columnCount=2)
        self.media_info_tree.setFrameShape(QFrame.Shape.Box)
        self.media_info_tree.setFrameShadow(QFrame.Shadow.Sunken)
        self.media_info_tree.setHeaderLabels(["Property", "Value"])
        self.media_info_tree.setRootIsDecorated(False)
        self.media_info_tree.setIndentation(0)

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(row_1_layout)
        self.main_layout.addWidget(self.lang_lbl)
        self.main_layout.addWidget(self.lang_combo)
        self.main_layout.addWidget(self.title_lbl)
        self.main_layout.addWidget(self.title_entry)
        self.main_layout.addWidget(self.delay_lbl)
        self.main_layout.addWidget(self.delay_spinbox)
        self.main_layout.addWidget(self.media_info_tree_lbl)
        self.main_layout.addWidget(self.media_info_tree, stretch=1)

    def _configure_file_filters(self) -> None:
        """Configure file filters for drag-and-drop and file dialog."""
        for dnd_widget in (self.open_file_btn, self.input_entry):
            dnd_widget.set_extensions(self._dnd_extensions)
            dnd_widget.dropped.connect(self._handle_dropped_file)

    def set_file_filters(
        self, dialog_filter: str, dnd_extensions: tuple[str, ...]
    ) -> None:
        """
        Update file filters for this tab.

        Args:
            dialog_filter: Filter string for QFileDialog (e.g., "Video Files (*.mp4 *.mkv)")
            dnd_extensions: Tuple of extensions for drag-and-drop (e.g., (".mp4", ".mkv"))
        """
        self._file_dialog_filter = dialog_filter
        self._dnd_extensions = dnd_extensions

        # update existing widgets
        for dnd_widget in (self.open_file_btn, self.input_entry):
            dnd_widget.set_extensions(dnd_extensions)

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

    @Slot(tuple)
    def _on_media_info_finished(self, result: tuple[MediaInfo, Path]) -> None:
        """Handles the media info worker finished signal."""
        media_info, file_path = result
        self._update_ui(media_info, file_path)
        self._parse_file_done()

    @Slot(str)
    def _on_media_info_failed(self, error_message: str) -> None:
        """Handles the media info worker failed signal."""
        # handle media info error
        # TODO: display the error in the UI either via a GSIG global or per widget?
        print("Media info retrieval failed:", error_message)
        self._parse_file_done()

    def _update_ui(self, media_info: MediaInfo, file_path: Path) -> None:
        """Updates the UI with the provided media info and file path."""
        self._load_language(media_info)
        self._load_title(media_info)
        self._load_media_info_into_tree(media_info)
        self._load_delay(media_info, file_path)

    def _parse_file_done(self) -> None:
        """Cleans up UI after file parsing is done."""
        GSigs().main_window_clear_status_tip.emit()
        GSigs().main_window_set_disabled.emit(False)
        GSigs().main_window_progress_bar_busy.emit(False)

    @abstractmethod
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        raise NotImplementedError("Must be implemented by subclasses.")

    @abstractmethod
    def _load_title(self, media_info: MediaInfo) -> None:
        """Loads title from media info into the title entry."""
        raise NotImplementedError("Must be implemented by subclasses.")

    @abstractmethod
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        raise NotImplementedError("Must be implemented by subclasses.")

    @abstractmethod
    def _load_delay(self, media_info: MediaInfo, file_path: Path) -> None:
        """Loads delay from media info into the delay entry."""
        raise NotImplementedError("Must be implemented by subclasses.")

    @Slot()
    def _open_file_dialog(self) -> None:
        """Opens a file dialog to select a media file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            self._file_dialog_filter,
        )
        if file_path:
            self._handle_dropped_file((file_path,))

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

    @abstractmethod
    def is_tab_ready(self) -> bool:
        """Returns whether the tab is ready for muxing."""
        raise NotImplementedError("is_tab_ready must be implemented by subclasses.")

    @abstractmethod
    def export_state(self) -> TState | None:
        """Exports the current state of the tab as a BaseTabState (concrete subtype)."""
        raise NotImplementedError("export_state must be implemented by subclasses.")

    def reset_tab(self) -> None:
        """Resets all input fields to default state."""
        self.input_entry.clear()
        self.input_entry.setToolTip("Open file...")
        self.lang_combo.setCurrentIndex(0)
        self.title_entry.clear()
        self.delay_spinbox.setValue(0)
        self.media_info_tree.clear()

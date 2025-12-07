from pathlib import Path

from pymediainfo import MediaInfo
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from frontend_desktop.widgets.utils import set_top_parent_geometry


class TrackSelectorDialog(QDialog):
    """Dialog to select an audio track from a multi-track MP4."""

    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.selected_track_id: int | None = None
        self._setup_ui()
        self._load_tracks()

    def _setup_ui(self) -> None:
        """Initialize the UI."""
        set_top_parent_geometry(self)
        self.setWindowTitle("Select Audio Track")

        # info label
        info_label = QLabel(
            f"The file <b>{self.file_path.name}</b> contains multiple audio tracks.\n"
            "Please select one to import:",
            self,
            wordWrap=True,
        )

        # track table
        self.track_table = QTableWidget(self, columnCount=8)
        self.track_table.setHorizontalHeaderLabels(
            (
                "Track ID",
                "Format",
                "Channels",
                "Bitrate",
                "Sample Rate",
                "Language",
                "Title",
                "Delay",
            )
        )
        self.track_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.track_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.track_table.horizontalHeader().setStretchLastSection(True)
        self.track_table.itemDoubleClicked.connect(self.accept)

        # buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info_label)
        layout.addWidget(self.track_table)
        layout.addWidget(button_box)

    def _load_tracks(self) -> None:
        """Load audio tracks from file into table."""
        media_info = MediaInfo.parse(str(self.file_path))
        audio_tracks = media_info.audio_tracks

        self.track_table.setRowCount(len(audio_tracks))

        for row, track in enumerate(audio_tracks):
            # track ID (1-based from MediaInfo)
            track_id = track.track_id if track.track_id is not None else row + 1
            track_id_item = QTableWidgetItem(str(track_id))
            # store MediaInfo track_id for matching
            track_id_item.setData(Qt.ItemDataRole.UserRole, track_id)
            self.track_table.setItem(row, 0, track_id_item)

            # format
            format_str = track.format or ""
            self.track_table.setItem(row, 1, QTableWidgetItem(format_str))

            # channels
            channels = track.channel_s or ""
            self.track_table.setItem(row, 2, QTableWidgetItem(str(channels)))

            # bitrate
            bitrate = track.other_bit_rate[0] if track.other_bit_rate else ""
            self.track_table.setItem(row, 3, QTableWidgetItem(bitrate))

            # sample rate
            sample_rate = (
                track.other_sampling_rate[0] if track.other_sampling_rate else ""
            )
            self.track_table.setItem(row, 4, QTableWidgetItem(sample_rate))

            # language
            language = track.other_language[0] if track.other_language else ""
            self.track_table.setItem(row, 5, QTableWidgetItem(language))

            # title
            title = track.title or ""
            if len(title) > 50:
                title = title[:50] + "..."
            self.track_table.setItem(row, 6, QTableWidgetItem(title))

            # delay
            delay = track.delay if track.delay else ""
            self.track_table.setItem(row, 7, QTableWidgetItem(str(delay)))

        # auto-select first row
        if self.track_table.rowCount() > 0:
            self.track_table.selectRow(0)

        # stretch all columns to fill available space
        for col in range(8):  # all columns
            self.track_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Stretch
            )

    def accept(self) -> None:
        """Override accept to capture selected track ID."""
        selected_items = self.track_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            track_id_item = self.track_table.item(row, 0)
            if track_id_item:
                self.selected_track_id = track_id_item.data(Qt.ItemDataRole.UserRole)
        super().accept()

    def get_selected_track_id(self) -> int | None:
        """Return the selected track ID (1-based, for MP4Box)."""
        return self.selected_track_id

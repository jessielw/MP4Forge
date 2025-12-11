from pathlib import Path

from pymediainfo import MediaInfo
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.utils.autoqpf import determine_chapter_type
from frontend_desktop.widgets.utils import set_top_parent_geometry


class TrackImportDialog(QDialog):
    """Dialog to select which tracks to import from a video file."""

    def __init__(self, file_path: Path, media_info: MediaInfo, parent=None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self.media_info = media_info
        self.selected_tracks = {
            "video": [],
            "audio": [],
            "subtitle": [],
            "chapters": False,  # boolean since there's only one chapters track
            "imported_track_count": 0,
        }
        self._setup_ui()
        self._load_tracks()

    def _setup_ui(self) -> None:
        """Initialize the UI."""
        set_top_parent_geometry(self)
        self.setWindowTitle("Import Tracks")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        # info label
        info_label = QLabel(
            f"Select which tracks to import from <b>{self.file_path.name}</b>:",
            self,
            wordWrap=True,
        )

        # track table
        self.track_table = QTableWidget(self, columnCount=7)
        self.track_table.setHorizontalHeaderLabels(
            ("Import", "Type", "ID", "Format", "Language", "Flags", "Title")
        )
        self.track_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.track_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.track_table.verticalScrollBar().setSingleStep(20)
        self.track_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.track_table.horizontalScrollBar().setSingleStep(20)

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
        """Load all tracks from media info into table."""
        row = 0

        # check if file has chapters
        has_chapters = bool(self.media_info.menu_tracks)

        total_tracks = (
            len(self.media_info.video_tracks)
            + len(self.media_info.audio_tracks)
            + len(self.media_info.text_tracks)
            + (1 if has_chapters else 0)  # add row for chapters
        )
        self.track_table.setRowCount(total_tracks)

        # video tracks
        for track in self.media_info.video_tracks:
            self._add_track_row(row, "Video", track)
            row += 1

        # audio tracks
        for track in self.media_info.audio_tracks:
            self._add_track_row(row, "Audio", track)
            row += 1

        # subtitle tracks
        for track in self.media_info.text_tracks:
            self._add_track_row(row, "Subtitle", track)
            row += 1

        # chapters (if present)
        if has_chapters:
            self._add_chapters_row(row)
            row += 1

        # configure column resize modes
        for col in range(self.track_table.columnCount()):
            # columns 0 (Import checkbox) and 2 (ID) should resize to contents
            if col == 0 or col == 2:
                self.track_table.horizontalHeader().setSectionResizeMode(
                    col, QHeaderView.ResizeMode.ResizeToContents
                )
            # all other columns should stretch
            else:
                self.track_table.horizontalHeader().setSectionResizeMode(
                    col, QHeaderView.ResizeMode.Stretch
                )

    def _add_track_row(self, row: int, track_type: str, track) -> None:
        """Add a track row to the table."""
        # checkbox for import
        checkbox = QCheckBox()
        checkbox.setChecked(True)  # default checked
        checkbox.setProperty("track_type", track_type.lower())
        checkbox.setProperty("track_id", track.track_id)
        self.track_table.setCellWidget(row, 0, checkbox)

        # track type
        self.track_table.setItem(row, 1, QTableWidgetItem(track_type))

        # track ID
        track_id = str(track.track_id) if track.track_id else "?"
        self.track_table.setItem(row, 2, QTableWidgetItem(track_id))

        # format
        format_str = track.format or ""
        if track_type == "Video" and hasattr(track, "width") and track.width:
            format_str += f" ({track.width}x{track.height})" if track.height else ""
        elif track_type == "Audio" and hasattr(track, "channel_s") and track.channel_s:
            format_str += f" ({track.channel_s}ch)"
        self.track_table.setItem(row, 3, QTableWidgetItem(format_str))

        # language
        language = ""
        if hasattr(track, "other_language") and track.other_language:
            language = track.other_language[0]
        self.track_table.setItem(row, 4, QTableWidgetItem(language))

        # flags (default/forced)
        flags = []
        if track_type in ("Audio", "Subtitle"):
            default_val = getattr(track, "default", None)
            if default_val and str(default_val).lower() in ("yes", "true", "1"):
                flags.append("Default")
            if track_type == "Subtitle":
                forced_val = getattr(track, "forced", None)
                if forced_val and str(forced_val).lower() in ("yes", "true", "1"):
                    flags.append("Forced")
        flags_str = ", ".join(flags) if flags else ""
        self.track_table.setItem(row, 5, QTableWidgetItem(flags_str))

        # title
        title = track.title or ""
        if len(title) > 40:
            title = title[:40] + "..."
        self.track_table.setItem(row, 6, QTableWidgetItem(title))

    def _add_chapters_row(self, row: int) -> None:
        """Add chapters row to the table."""
        # checkbox for import
        checkbox = QCheckBox()
        checkbox.setChecked(True)  # default checked
        checkbox.setProperty("track_type", "chapters")
        self.track_table.setCellWidget(row, 0, checkbox)

        # track type
        self.track_table.setItem(row, 1, QTableWidgetItem("Chapters"))

        # ID (chapters don't have a track ID)
        self.track_table.setItem(row, 2, QTableWidgetItem("-"))

        # format (get chapter count if available)
        chap_type = determine_chapter_type(self.media_info)
        format_str = chap_type if chap_type else ""
        self.track_table.setItem(row, 3, QTableWidgetItem(format_str))

        # language (chapters typically don't have language)
        self.track_table.setItem(row, 4, QTableWidgetItem(""))

        # flags (chapters don't have flags)
        self.track_table.setItem(row, 5, QTableWidgetItem(""))

        # title
        self.track_table.setItem(row, 6, QTableWidgetItem(""))

    def accept(self) -> None:
        """Collect selected tracks before accepting."""
        imported_track_count = 0
        for row in range(self.track_table.rowCount()):
            checkbox = self.track_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                track_type = checkbox.property("track_type")
                if track_type == "chapters":
                    self.selected_tracks["chapters"] = True
                else:
                    track_id = checkbox.property("track_id")
                    self.selected_tracks[track_type].append(track_id)
                imported_track_count += 1
        self.selected_tracks["imported_track_count"] = imported_track_count
        super().accept()

    def get_selected_tracks(self) -> dict[str, list[int]]:
        """Return dictionary of selected track IDs by type."""
        return self.selected_tracks

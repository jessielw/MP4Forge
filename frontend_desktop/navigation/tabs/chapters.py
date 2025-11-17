from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pymediainfo import MediaInfo
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel
from typing_extensions import override

from core.utils.autoqpf import auto_gen_chapters
from frontend_desktop.global_signals import GSigs
from frontend_desktop.navigation.tabs.base import BaseTab, BaseTabState
from frontend_desktop.widgets.basic_code_editor import CodeEditor


@dataclass(frozen=True, slots=True)
class ChapterTabState(BaseTabState):
    """Data structure for exporting the state of the Audio tab."""

    chapters: str | None


class ChapterTab(BaseTab[ChapterTabState]):
    def __init__(self, parent=None):
        super().__init__(
            file_dialog_filters="Text Files (*.txt);;All Files (*)",
            dnd_extensions=(".txt",),
            parent=parent,
        )
        self.setObjectName("ChapterTab")

        GSigs().chapters_updated.connect(self.on_chapters_updated)

        # hide un-needed widgets
        self.lang_lbl.hide()
        self.lang_combo.hide()
        self.title_lbl.hide()
        self.title_entry.hide()
        self.delay_lbl.hide()
        self.delay_spinbox.hide()
        self.media_info_tree_lbl.hide()
        self.media_info_tree.hide()

        # chapter editor
        self.editor_lbl = QLabel("Editor", self)
        self.editor = CodeEditor(
            line_numbers=True,
            mono_font=True,
            pop_out_expansion=True,
            parent=self,
        )

        self.main_layout.addWidget(self.editor_lbl)
        self.main_layout.addWidget(self.editor, stretch=1)

    @override
    @Slot(list)
    def _handle_dropped_file(self, file_paths: Sequence[str]) -> None:
        """Handles a dropped file."""
        self._stop_reset_timer()
        drop_path = Path(file_paths[0]).resolve()
        if drop_path.suffix == ".txt":
            str_drop = str(drop_path)
            self.input_entry.setText(str_drop)
            self.input_entry.setToolTip(str_drop)
            with open(drop_path, encoding="utf-8") as f:
                chapters = f.read()
                if chapters.strip():
                    self.editor.setPlainText(chapters)
        else:
            super()._handle_dropped_file(file_paths)

    @override
    @Slot(tuple)
    def _on_media_info_finished(self, result: tuple[MediaInfo, Path]) -> None:
        media_info, file_path = result
        chapters = auto_gen_chapters(media_info)
        if chapters:
            GSigs().chapters_updated.emit(chapters)
        self._update_ui(media_info, file_path)
        self._parse_file_done()

    @Slot(str)
    def on_chapters_updated(self, chapters: str) -> None:
        """Handle chapters updated signal."""
        if not chapters.strip():
            return
        self.editor.setPlainText(chapters)

    @override
    def _load_language(self, media_info: MediaInfo) -> None:
        """Loads language from media info into the language combo box."""
        pass

    @override
    def _load_title(self, media_info: MediaInfo) -> None:
        """Loads title from media info into the title entry."""
        pass

    @override
    def _load_media_info_into_tree(self, media_info: MediaInfo) -> None:
        """Loads media info into the tree widget."""
        pass

    @override
    def _load_delay(self, media_info: MediaInfo, file_path: Path) -> None:
        """Loads delay from media info into the delay entry."""
        pass

    @override
    def export_state(self) -> ChapterTabState:
        """Exports the current state of the tab as a VideoTabState."""
        state = ChapterTabState(chapters=self.editor.toPlainText() or None)
        return state

    @override
    def is_tab_ready(self) -> bool:
        """Returns whether the tab is ready for muxing."""
        return True

    @override
    def reset_tab(self) -> None:
        super().reset_tab()
        self.editor.clear()

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PresetTitleEditor(QWidget):
    """Widget for managing preset title lists with add/edit/remove/reorder functionality."""

    titles_changed = Signal(list)  # list[str]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the UI components."""
        # list widget to display titles
        self.title_list = QListWidget(self)
        self.title_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.title_list.itemDoubleClicked.connect(self._edit_selected_title)

        # buttons for list management
        self.add_btn = QPushButton("Add", self)
        self.add_btn.clicked.connect(self._add_title)

        self.edit_btn = QPushButton("Edit", self)
        self.edit_btn.clicked.connect(self._edit_selected_title)

        self.remove_btn = QPushButton("Remove", self)
        self.remove_btn.clicked.connect(self._remove_selected_title)

        self.move_up_btn = QPushButton("↑ Move Up", self)
        self.move_up_btn.clicked.connect(self._move_up)

        self.move_down_btn = QPushButton("↓ Move Down", self)
        self.move_down_btn.clicked.connect(self._move_down)

        self.clear_btn = QPushButton("Clear All", self)
        self.clear_btn.clicked.connect(self._clear_all)

        # button layout
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        # main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.title_list)
        self.main_layout.addLayout(button_layout)

        # update button states
        self._update_button_states()

        # connect selection change to update button states
        self.title_list.itemSelectionChanged.connect(self._update_button_states)

    @Slot()
    def _add_title(self) -> None:
        """Add a new title to the list."""
        title, ok = QInputDialog.getText(
            self,
            "Add Title",
            "Enter title preset:",
            text="",
        )
        if ok and title.strip():
            title = title.strip()
            # check for duplicates
            if self._title_exists(title):
                QMessageBox.warning(
                    self, "Duplicate Title", f"Title '{title}' already exists."
                )
                return
            self.title_list.addItem(title)
            self._emit_changes()

    @Slot()
    def _edit_selected_title(self) -> None:
        """Edit the selected title."""
        current_item = self.title_list.currentItem()
        if not current_item:
            return

        old_title = current_item.text()
        title, ok = QInputDialog.getText(
            self,
            "Edit Title",
            "Edit title preset:",
            text=old_title,
        )
        if ok and title.strip():
            title = title.strip()
            # check for duplicates (excluding current item)
            if title != old_title and self._title_exists(title):
                QMessageBox.warning(
                    self, "Duplicate Title", f"Title '{title}' already exists."
                )
                return
            current_item.setText(title)
            self._emit_changes()

    @Slot()
    def _remove_selected_title(self) -> None:
        """Remove the selected title."""
        current_row = self.title_list.currentRow()
        if current_row >= 0:
            self.title_list.takeItem(current_row)
            self._emit_changes()

    @Slot()
    def _move_up(self) -> None:
        """Move selected item up in the list."""
        current_row = self.title_list.currentRow()
        if current_row > 0:
            item = self.title_list.takeItem(current_row)
            self.title_list.insertItem(current_row - 1, item)
            self.title_list.setCurrentRow(current_row - 1)
            self._emit_changes()

    @Slot()
    def _move_down(self) -> None:
        """Move selected item down in the list."""
        current_row = self.title_list.currentRow()
        if current_row >= 0 and current_row < self.title_list.count() - 1:
            item = self.title_list.takeItem(current_row)
            self.title_list.insertItem(current_row + 1, item)
            self.title_list.setCurrentRow(current_row + 1)
            self._emit_changes()

    @Slot()
    def _clear_all(self) -> None:
        """Clear all titles after confirmation."""
        if self.title_list.count() == 0:
            return

        reply = QMessageBox.question(
            self,
            "Clear All Titles",
            "Are you sure you want to remove all preset titles?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.title_list.clear()
            self._emit_changes()

    @Slot()
    def _update_button_states(self) -> None:
        """Update button enabled/disabled states based on selection."""
        has_selection = self.title_list.currentRow() >= 0
        current_row = self.title_list.currentRow()
        count = self.title_list.count()

        self.edit_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
        self.move_up_btn.setEnabled(has_selection and current_row > 0)
        self.move_down_btn.setEnabled(has_selection and current_row < count - 1)
        self.clear_btn.setEnabled(count > 0)

    def _title_exists(self, title: str) -> bool:
        """Check if a title already exists in the list."""
        for i in range(self.title_list.count()):
            if self.title_list.item(i).text() == title:
                return True
        return False

    def _emit_changes(self) -> None:
        """Emit signal with updated title list."""
        titles = self.get_titles()
        self.titles_changed.emit(titles)

    def set_titles(self, titles: list[str]) -> None:
        """Set the title list from a list of strings."""
        self.title_list.clear()
        for title in titles:
            if title.strip():  # skip empty strings
                self.title_list.addItem(title.strip())
        self._update_button_states()

    def get_titles(self) -> list[str]:
        """Get the current title list as a list of strings."""
        return [self.title_list.item(i).text() for i in range(self.title_list.count())]

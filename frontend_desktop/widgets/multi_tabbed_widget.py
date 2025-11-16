import qtawesome as qta
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QTabBar, QTabWidget, QVBoxLayout, QWidget

from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap


class MultiTabbedTabWidget(QWidget):
    """
    A reusable tab widget for managing multiple tabs.

    Features:
    - Dynamically add new tab tabs via a plus tab
    - Close tabs with automatic renumbering
    - Prevent plus tab from being closed or moved
    - Disable mouse wheel scrolling on tab bar
    - Auto-focus previous tab when closing
    """

    def __init__(
        self,
        parent=None,
        widget_class: type[QWidget] | None = None,
        tab_name: str = "Tab",
        initial_count: int = 1,
    ):
        """
        Args:
            parent: Parent widget
            widget_class: Class to instantiate for each tab tab
            tab_name: Display name for tabs
            initial_count: Number of initial tab tabs to create
        """
        super().__init__(parent)
        self.setObjectName("MultiTabbedTabWidget")

        self._plus_tab_idx = -1
        self.widget_class = widget_class or QWidget
        self.tab_name = tab_name

        # create tab widget
        self.tabs = QTabWidget(self, tabsClosable=True, movable=True)
        self.tabs.tabCloseRequested.connect(self._remove_tab)
        self.tabs.currentChanged.connect(self._handle_tab_changed)
        self.tabs.tabBar().tabMoved.connect(self._handle_tab_moved)

        # disable mouse wheel scrolling on tab bar
        self.tabs.tabBar().installEventFilter(self)

        # add initial tab tabs
        for _ in range(initial_count):
            self.add_new_tab()

        # add plus tab
        self._add_plus_tab()

        # connect to theme change signal to update plus tab icon
        app = QApplication.instance()
        if app:
            app.styleHints().colorSchemeChanged.connect(self._update_plus_tab_icon)  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.tabs)

    def eventFilter(self, obj, event) -> bool:
        """Block mouse wheel events on tab bar to prevent accidental tab switching."""
        if obj is self.tabs.tabBar() and event.type() == QEvent.Type.Wheel:
            return True
        return super().eventFilter(obj, event)

    def add_new_tab(self, switch_to: bool = False) -> QWidget:
        """
        Add a new tab tab before the plus tab.

        Args:
            switch_to: If True, switch to the newly created tab

        Returns:
            The newly created tab widget
        """
        tab_widget = self.widget_class(self)

        # insert before the plus tab
        idx = self._plus_tab_idx if self._plus_tab_idx >= 0 else self.tabs.count()
        self.tabs.insertTab(idx, tab_widget, f"{self.tab_name} {idx + 1}")

        # update plus tab index since we inserted before it
        self._plus_tab_idx = self.tabs.count() - 1

        if switch_to:
            self.tabs.setCurrentIndex(idx)

        return tab_widget

    def _add_plus_tab(self) -> None:
        """Add the special plus tab for creating new tabs."""
        plus_widget = QWidget()
        self._plus_tab_idx = self.tabs.addTab(plus_widget, "")

        # Set initial icon
        self._update_plus_tab_icon()

        # hide close button on the plus tab
        plus_btn = self.tabs.tabBar().tabButton(
            self._plus_tab_idx, QTabBar.ButtonPosition.RightSide
        )
        if plus_btn:
            plus_btn.resize(0, 0)

    def _update_plus_tab_icon(self, color_scheme=None) -> None:
        """Update the plus tab icon color based on current theme."""

        if self._plus_tab_idx < 0:
            return

        # determine color based on scheme
        if color_scheme is None:
            app = QApplication.instance()
            color_scheme = (
                app.styleHints().colorScheme() if app else Qt.ColorScheme.Light  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]
            )

        color = (
            QTAThemeSwap.DARK_COLOR
            if color_scheme == Qt.ColorScheme.Dark
            else QTAThemeSwap.LIGHT_COLOR
        )

        # update icon with new color
        icon = qta.icon("ph.plus-bold", color=color)
        self.tabs.setTabIcon(self._plus_tab_idx, icon)

    def _handle_tab_changed(self, idx: int) -> None:
        """Handle tab selection changes. Create a new tab when plus is clicked."""
        if idx >= 0 and idx == self._plus_tab_idx:
            # block signals temporarily to prevent recursion
            self.tabs.blockSignals(True)
            self.add_new_tab(switch_to=False)
            # switch to the newly created tab (which is now at _plus_tab_idx - 1)
            self.tabs.setCurrentIndex(self._plus_tab_idx - 1)
            self.tabs.blockSignals(False)

    def _handle_tab_moved(self, from_idx: int, to_idx: int) -> None:
        """Prevent plus tab from being moved and update tab numbers."""
        plus_idx = self.tabs.count() - 1

        # if plus tab was moved, restore it to the end
        if from_idx == self._plus_tab_idx:
            self.tabs.tabBar().blockSignals(True)
            self.tabs.tabBar().moveTab(to_idx, plus_idx)
            self.tabs.tabBar().blockSignals(False)
            # plus tab is now at the end again
            self._plus_tab_idx = plus_idx

        # update all tab labels to reflect new order
        self._update_tab_labels()

    def _remove_tab(self, idx: int) -> None:
        """
        Remove a tab and update numbering.

        Args:
            idx: Index of tab to remove
        """
        # don't remove if it's the plus tab
        if idx == self._plus_tab_idx:
            return

        # must keep at least one tab (plus the plus tab)
        if self.tabs.count() <= 2:
            return

        # block signals to prevent unwanted tab changes during removal
        self.tabs.blockSignals(True)
        self.tabs.removeTab(idx)
        self.tabs.blockSignals(False)

        # update plus tab index after removal
        self._plus_tab_idx = self.tabs.count() - 1

        # focus the tab to the right if possible, otherwise left
        new_idx = idx if idx < self.tabs.count() - 1 else idx - 1
        # ensure we don't focus the plus tab
        if new_idx >= self.tabs.count() - 1:
            new_idx = self.tabs.count() - 2
        self.tabs.setCurrentIndex(new_idx)

        # update tab labels
        self._update_tab_labels()

    def _update_tab_labels(self) -> None:
        """Update all tab labels to show correct tab numbers."""
        for i in range(self.tabs.count() - 1):  # Exclude plus tab
            self.tabs.setTabText(i, f"{self.tab_name} {i + 1}")

    def get_all_tab_widgets(self) -> list[QWidget]:
        """
        Get all tab widgets (excluding the plus tab).

        Returns:
            List of tab widgets
        """
        return [self.tabs.widget(i) for i in range(self.tabs.count() - 1)]

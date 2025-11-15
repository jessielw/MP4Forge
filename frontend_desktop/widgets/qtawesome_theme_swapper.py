from functools import partial

import qtawesome as qta
from PySide6.QtCore import QObject, QSize, Qt, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QToolButton


class QTAwesomeThemeSwapper(QObject):
    """Singleton used to keep up with icon widgets"""

    LIGHT_COLOR = "#000000"
    DARK_COLOR = "#FFFFFF"

    _instance = None

    def __new__(cls, *args, **kwargs) -> "QTAwesomeThemeSwapper":
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        # ensure we've only initialized once
        if not hasattr(self, "_initialized"):
            super().__init__()
            # list of (widget, icon_name, icon_kwargs)
            self._icon_widgets = []
            self._initialized = True

            # connect to color scheme change signal
            self.app = QApplication.instance()
            self.app.styleHints().colorSchemeChanged.connect(self.update_icon)  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]

            # set the initial icon based on the current color scheme
            self.update_icon(self.app.styleHints().colorScheme())  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]

    @Slot(Qt.ColorScheme)
    def update_icon(self, color_scheme: Qt.ColorScheme) -> None:
        """Updates the SVG icon based on the color scheme."""
        if color_scheme == Qt.ColorScheme.Dark:
            self.swap_all_icons(self.DARK_COLOR)
        else:
            self.swap_all_icons(self.LIGHT_COLOR)

    def register(
        self,
        widget: QToolButton | QPushButton | qta.IconWidget,
        icon_name: str,
        icon_size: QSize | None = None,
        **icon_kwargs,
    ) -> None:
        """Register a widget and its icon info for theme swapping."""
        self._icon_widgets.append((widget, icon_name, icon_kwargs))
        icon_args = dict(icon_kwargs)
        if "color" not in icon_args:
            icon_args["color"] = self.LIGHT_COLOR
        widget.setIcon(qta.icon(icon_name, **icon_kwargs))
        if icon_size:
            widget.setIconSize(icon_size)
            # we must call update on IconWidgets to correctly update the size
            if isinstance(widget, qta.IconWidget):
                widget.update()

        # connect to widget's destroyed signal to de register automatically
        widget.destroyed.connect(partial(self.deregister, widget))

    def deregister(self, widget):
        """Remove a widget from icon management."""
        self._icon_widgets = [
            (w, icon_name, icon_kwargs)
            for (w, icon_name, icon_kwargs) in self._icon_widgets
            if w is not widget
        ]

    def swap_all_icons(self, color):
        """Update all registered icons to the new color."""
        for widget, icon_name, icon_kwargs in self._icon_widgets:
            icon_args = dict(icon_kwargs)
            icon_args["color"] = color
            widget.setIcon(qta.icon(icon_name, **icon_args))
            if "icon_size" in icon_args and icon_args["icon_size"]:
                widget.setIconSize(icon_args["icon_size"])


QTAThemeSwap = QTAwesomeThemeSwapper

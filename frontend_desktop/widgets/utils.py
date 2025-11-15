from functools import partial

from PySide6.QtCore import QTimer
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLayout,
    QStackedWidget,
    QWidget,
)


def build_h_line(values: tuple[int, int, int, int]) -> QFrame:
    """
    Accepts a tuple of int to control the margins.

    (left, top, right, bottom)
    """
    h_line = QFrame()
    h_line.setFrameShape(QFrame.Shape.HLine)
    h_line.setFrameShadow(QFrame.Shadow.Sunken)
    h_line.setContentsMargins(*values)
    return h_line


def build_v_line(values: tuple[int, int, int, int]) -> QFrame:
    """
    Accepts a tuple of int to control the margins.

    (left, top, right, bottom)
    """
    h_line = QFrame()
    h_line.setFrameShape(QFrame.Shape.VLine)
    h_line.setFrameShadow(QFrame.Shadow.Sunken)
    h_line.setContentsMargins(*values)
    return h_line


def recursively_clear_layout(layout: QLayout) -> None:
    """Recursively clears layouts and deletes widgets as needed"""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()

        if widget is not None:
            widget.deleteLater()
        elif item.layout() is not None:
            recursively_clear_layout(item.layout())


def clear_stacked_widget(stacked_widget: QStackedWidget) -> None:
    """Recursively clears QStackedWidgets and deletes widgets as needed"""
    while stacked_widget.count():
        widget = stacked_widget.widget(0)
        stacked_widget.removeWidget(widget)
        widget.deleteLater()


def create_form_layout(
    widget1: QWidget,
    widget2: QWidget | None = None,
    margins: tuple[int, int, int, int] | None = None,
):
    """margins (tuple[int, int, int, int] | None, optional): Left, top, right, bottom"""
    form_layout = QFormLayout()
    if margins:
        form_layout.setContentsMargins(*margins)
    form_layout.addWidget(widget1)
    if widget2:
        form_layout.addWidget(widget2)
    return form_layout


def block_all_signals(widget: QWidget, block: bool) -> None:
    """Recursively block/unblock signals for parent and all child widgets."""

    def block_signals_recursive(w: QWidget) -> None:
        w.blockSignals(block)
        for child in w.findChildren(QWidget):
            block_signals_recursive(child)

    block_signals_recursive(widget)


def set_top_parent_geometry(widget: QWidget, delay: int = 1) -> None:
    """Find the topmost parent widget and set geometry for the given widget based on that."""

    def do_the_stuff(widget: QWidget) -> None:
        parent_widget = widget
        last_valid_parent = widget
        while True:
            next_parent = parent_widget.parentWidget()
            if next_parent is None:
                break
            last_valid_parent = next_parent
            parent_widget = next_parent

        if last_valid_parent:
            widget.setGeometry(last_valid_parent.geometry())

    QTimer.singleShot(delay, partial(do_the_stuff, widget))


def cancel_scroll_event(event: QWheelEvent) -> None:
    """Cancels a scroll event to prevent changing values in spinboxes, combo boxes, etc."""
    event.ignore()

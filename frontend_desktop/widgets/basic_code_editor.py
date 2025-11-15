import re
import sys
from typing import NamedTuple

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt, Signal, Slot
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextOption,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import set_top_parent_geometry

HighlightKeywords = NamedTuple(
    "HighlightKeywords",
    (("pattern", re.Pattern), ("color", str), ("first_occurrence_only", bool)),
)


class CustomHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument | None = None):
        super().__init__(parent)  # pyright: ignore [reportCallIssue, reportArgumentType]
        self.patterns_colors = []

    def set_patterns(self, patterns_colors: list[HighlightKeywords]) -> None:
        self.patterns_colors = patterns_colors
        self.rehighlight()

    def remove_patterns(self) -> None:
        self.patterns_colors.clear()
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        for highlight_keyword in self.patterns_colors:
            found = False
            for match in re.finditer(highlight_keyword.pattern, text):
                if found and highlight_keyword.first_occurrence_only:
                    break

                # get all the groups from the match (this will be a tuple)
                groups = match.groups()

                # if there are any groups
                if groups:
                    # iterate over each group and highlight them individually
                    # enumerate to get the group number (starting at 1)
                    for i, group in enumerate(groups, 1):
                        # make sure the group isn't None (it could be if there was no match in that group)
                        # get the span for the i-th group
                        if group:
                            start, end = match.span(i)
                            text_format = QTextCharFormat()
                            text_format.setFontWeight(QFont.Weight.Bold)
                            text_format.setForeground(QColor(highlight_keyword.color))
                            self.setFormat(start, end - start, text_format)
                else:
                    # if no groups exist, highlight the entire match
                    start, end = match.span()
                    text_format = QTextCharFormat()
                    text_format.setFontWeight(QFont.Weight.Bold)
                    text_format.setForeground(QColor(highlight_keyword.color))
                    self.setFormat(start, end - start, text_format)

                # if `first_occurrence_only` is True, stop after the first match
                if highlight_keyword.first_occurrence_only:
                    found = True
                    break


class LineNumberArea(QWidget):
    def __init__(self, editor) -> None:
        QWidget.__init__(self, editor)
        self._code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._code_editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:
        self._code_editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    # vars
    TAB_WIDTH = 4
    LINE_AREA_STARTING_DIGIT_WIDTH = 2
    THEMES = {
        "dark": {"box_color": "#626262", "font_color": "#a5a5a5"},
        "light": {"box_color": "#e6e6e6", "font_color": "#A9A9A9"},
    }

    # signals
    save_contents = Signal(str)

    def __init__(
        self,
        line_numbers: bool = True,
        wrap_text: bool = False,
        mono_font: bool = True,
        pop_out_expansion: bool = False,
        pop_out_name: str = "Editor",
        pop_out_geometry: QRect | None = None,
        parent=None,
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)

        self.line_numbers = line_numbers
        self.wrap_text = wrap_text
        self.mono_font = mono_font
        self.pop_out_expansion = pop_out_expansion
        self.pop_out_name = pop_out_name
        self.pop_out_geometry = pop_out_geometry
        self.kwargs = kwargs

        self.highlighter = CustomHighlighter(self.document())

        if mono_font:
            self.set_monospace_font()

        if not wrap_text:
            self.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        self.box_color, self.font_color = self.get_theme_colors()

        if self.line_numbers:
            self.line_number_area = LineNumberArea(self)
            self.blockCountChanged.connect(self.update_line_number_area_width)
            self.updateRequest.connect(self.update_line_number_area)
            self.cursorPositionChanged.connect(self.highlight_current_line)

            self.update_line_number_area_width(0)
            self.highlight_current_line()

        self._save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self._save_shortcut.activated.connect(self._emit_save)

        # expansion
        self.pop_out_name = pop_out_name
        self.pop_out_geometry = pop_out_geometry
        if pop_out_expansion:
            self.expand_icon = QPushButton(parent=self)
            self.expand_icon.setFixedSize(20, 20)
            self.expand_icon.setToolTip("Expand Editor")
            self.expand_icon.setCursor(Qt.CursorShape.PointingHandCursor)
            self.expand_icon.setStyleSheet(
                "QPushButton { border: none; }"
                "QPushButton:hover { background-color: rgba(31, 123, 228, 0.95); "
                "border-radius: 2px; border: 1px solid #5f5f5fc9; }"
            )

            QTAThemeSwap().register(
                self.expand_icon,
                "ph.arrows-out-light",
                icon_size=QSize(20, 20),
            )
            self.expand_icon.clicked.connect(self.expand_editor_popup)
            self.expand_icon.hide()
            self.installEventFilter(self)

    def set_monospace_font(self):
        if "Fira Mono" in QFontDatabase().families():
            self.setFont(QFont("Fira Mono"))
        else:
            self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

    def highlight_keywords(self, patterns_colors: list[HighlightKeywords]) -> None:
        self.highlighter.set_patterns(patterns_colors)

    def clear_keyword_highlights(self) -> None:
        self.highlighter.remove_patterns()

    def line_number_area_width(self) -> int:
        # calculate digits based on actual block count
        digits = max(
            self.LINE_AREA_STARTING_DIGIT_WIDTH, len(str(max(1, self.blockCount())))
        )

        # calculate the width based on the number of digits
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        if self.line_numbers:
            cr = self.contentsRect()
            width = self.line_number_area_width()
            rect = QRect(cr.left(), cr.top(), width, cr.height())
            self.line_number_area.setGeometry(rect)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.Type.PaletteChange:
            self.box_color, self.font_color = self.get_theme_colors()
            self.highlight_current_line()
            if self.line_numbers:
                self.line_number_area.update()
        return super().event(e)

    def get_theme_colors(self):
        app = QApplication.instance()
        if app:
            color_scheme = app.styleHints().colorScheme()  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]
            scheme = "dark" if color_scheme == Qt.ColorScheme.Dark else "light"
            return self.THEMES[scheme]["box_color"], self.THEMES[scheme]["font_color"]
        return "#e6e6e6", "#A9A9A9"

    def lineNumberAreaPaintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(self.line_number_area.rect(), QColor(self.box_color))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                number = str(block_number + 1)
                painter.setPen(QColor(self.font_color))
                painter.drawText(
                    QRect(
                        0,
                        int(top),
                        self.line_number_area.width(),
                        self.fontMetrics().height(),
                    ),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            top += self.blockBoundingRect(block).height()
            block_number += 1

    @Slot(int)
    def update_line_number_area_width(self, _newBlockCount) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    @Slot(QRect, int)
    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            width = self.line_number_area.width()
            self.line_number_area.update(0, rect.y(), width, rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    @Slot()
    def highlight_current_line(self) -> None:
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(self.box_color)
            selection.format.setBackground(line_color)  # pyright: ignore [reportAttributeAccessIssue]

            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # pyright: ignore [reportAttributeAccessIssue]

            selection.cursor = self.textCursor()  # pyright: ignore [reportAttributeAccessIssue]
            selection.cursor.clearSelection()  # pyright: ignore [reportAttributeAccessIssue]

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        cursor = self.textCursor()

        # tab
        if e.key() == Qt.Key.Key_Tab:
            if cursor.hasSelection():
                self.modify_indentation(self.TAB_WIDTH)
            # Insert a tab at the current cursor position
            else:
                cursor.insertText(" " * self.TAB_WIDTH)

        # Shift + Tab
        elif e.key() == Qt.Key.Key_Backtab:
            if cursor.hasSelection():
                self.modify_indentation(-self.TAB_WIDTH)
            else:
                self.modify_indentation(-self.TAB_WIDTH)

        else:
            super().keyPressEvent(e)

    def modify_indentation(self, amount: int) -> None:
        cursor = self.textCursor()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()

        cursor.beginEditBlock()

        # select whole lines
        cursor.setPosition(selection_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.MoveAnchor
        )
        start_pos = cursor.position()

        cursor.setPosition(selection_end)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        end_pos = cursor.position()

        # adjust selected lines
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)

        selected_text = cursor.selection().toPlainText()
        lines = selected_text.splitlines()

        modified_lines = []
        for line in lines:
            # indent: Add spaces
            if amount > 0:
                modified_lines.append(" " * amount + line)
            # Un-indent: Remove spaces
            elif amount < 0:
                spaces_to_remove = min(-amount, len(line) - len(line.lstrip()))
                modified_lines.append(line[spaces_to_remove:])
            else:
                modified_lines.append(line)

        cursor.insertText("\n".join(modified_lines))

        # adjust the selection range to reflect the changes
        new_selection_start = start_pos
        new_selection_end = cursor.position()

        # ensure new selection is within bounds
        document_length = len(self.toPlainText())
        new_selection_start = max(0, min(new_selection_start, document_length))
        new_selection_end = max(0, min(new_selection_end, document_length))

        # restore the selection
        cursor.setPosition(new_selection_start)
        cursor.setPosition(new_selection_end, QTextCursor.MoveMode.KeepAnchor)

        cursor.endEditBlock()
        self.setTextCursor(cursor)

    @Slot()
    def _emit_save(self) -> None:
        self.save_contents.emit(self.toPlainText())

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self:
            if event.type() == QEvent.Type.Resize:
                self.expand_icon.move(1, 1)
            elif event.type() == QEvent.Type.Enter:
                self.expand_icon.show()
            elif event.type() == QEvent.Type.Leave:
                self.expand_icon.hide()
        return super().eventFilter(obj, event)

    def expand_editor_popup(self):
        # build dialog
        dlg = QDialog(self)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        dlg.setWindowTitle(self.pop_out_name if self.pop_out_name else "Editor")

        # set geometry
        if self.pop_out_geometry:
            dlg.setGeometry(self.pop_out_geometry)
        # attempt to use the last valid parents geometry if no geometry is set
        set_top_parent_geometry(dlg)

        large_editor = CodeEditor(
            line_numbers=self.line_numbers,
            wrap_text=self.wrap_text,
            mono_font=self.mono_font,
            **self.kwargs,
        )
        large_editor.setPlainText(self.toPlainText())

        cancel_btn = QPushButton("Cancel", dlg)
        cancel_btn.setFixedWidth(150)
        cancel_btn.clicked.connect(dlg.reject)

        ok_btn = QPushButton("Okay", dlg)
        ok_btn.setFixedWidth(150)
        ok_btn.clicked.connect(dlg.accept)

        btns = QHBoxLayout()
        btns.addWidget(cancel_btn)
        btns.addStretch()
        btns.addWidget(ok_btn)

        layout = QVBoxLayout(dlg)
        layout.addWidget(large_editor)
        layout.addLayout(btns)

        # apply changes to text if accepted
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.setPlainText(large_editor.toPlainText())


if __name__ == "__main__":
    data = """\
testing here
    <ul id="navigation">
    {% for item in navigation %}
        <li><a href="{{ item.href }}">{{ item.caption }}</a></li>
    {% endfor %}
    </ul>

    <h1>My Webpage</h1>
    {{ a_variable }}
bobby"""

    patterns_colors = [
        # Highlight "Crop(...)" in red, first occurrence only
        HighlightKeywords(re.compile(r"Crop\([^)]*\)"), "#e1401d", True),
        # Highlight all occurrences of "keyword1" in blue
        HighlightKeywords(re.compile(r"\bkeyword1\b"), "blue", False),
        # Highlight all occurrences of "keyword2" in green
        HighlightKeywords(re.compile(r"\bkeyword2\b"), "green", False),
        # Highlight all occurrences of "keyword3" in purple
        HighlightKeywords(re.compile(r"\bkeyword3\b"), "purple", False),
    ]

    app = QApplication([])
    font = QFont("Courier New", 10)
    editor = CodeEditor()
    editor.setFont(font)
    editor.resize(800, 600)
    editor.highlight_keywords(patterns_colors)
    editor.show()
    editor.setPlainText(data)
    sys.exit(app.exec())

import keyword
import re
from pathlib import Path

from PySide6.QtCore import (
    QIODevice,
    QPoint,
    QRect,
    QSaveFile,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFontDatabase,
    QKeySequence,
    QPainter,
    QPalette,
    QPolygon,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.icons import system_icon


class StatusLabel(QLabel):
    def __init__(self, text=""):
        super().__init__(text)
        self.setWordWrap(True)
        self.setTextFormat(Qt.PlainText)
        self.set_status(text)

    def set_status(self, text, state="neutral"):
        if self.text() != text:
            self.setText(text)
        if self.property("state") != state:
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)


class JsonHighlighter(QSyntaxHighlighter):
    pattern = re.compile(
        r'(?P<key>"(?:\\.|[^"\\])*")(?=\s*:)|"(?:\\.|[^"\\])*"|\b(?:true|false|null)\b|-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    )

    def highlightBlock(self, text):
        if len(text) > 16384:
            return
        dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        if getattr(self, "dark", None) != dark:
            self.dark = dark
            colors = (
                ("#8db0ff", "#88d8b0", "#c6a0ec", "#f0b276") if dark else ("#315ee8", "#177b5a", "#9154b2", "#ba641b")
            )
            self.formats = []
            for color in colors:
                style = QTextCharFormat()
                style.setForeground(QColor(color))
                self.formats.append(style)
        previous_end = 0
        position = 0
        for match in self.pattern.finditer(text):
            value = match.group()
            if value.startswith('"'):
                style = self.formats[0 if match.group("key") is not None else 1]
            else:
                style = self.formats[2 if value in ("true", "false", "null") else 3]
            position += len(text[previous_end : match.start()].encode("utf-16-le", "surrogatepass")) // 2
            length = len(value.encode("utf-16-le", "surrogatepass")) // 2
            self.setFormat(position, length, style)
            position += length
            previous_end = match.end()


class PythonHighlighter(QSyntaxHighlighter):
    pattern = re.compile(
        r"(?P<comment>\#.*$)|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')|(?P<word>\b[A-Za-z_]\w*\b)|(?P<number>\b\d+(?:\.\d+)?)"
    )

    def highlightBlock(self, text):
        dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        for match in self.pattern.finditer(text):
            if match.group("comment") is not None:
                color = "#8795ad"
            elif match.group("string") is not None:
                color = "#88d8b0" if dark else "#177b5a"
            elif match.group("word") in keyword.kwlist:
                color = "#c6a0ec" if dark else "#9154b2"
            elif match.group("number"):
                color = "#f0b276" if dark else "#ba641b"
            else:
                continue
            style = QTextCharFormat()
            style.setForeground(QColor(color))
            start = len(text[: match.start()].encode("utf-16-le", "surrogatepass")) // 2
            length = len(match.group().encode("utf-16-le", "surrogatepass")) // 2
            self.setFormat(start, length, style)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)

    def mousePressEvent(self, event):
        self.editor.toggle_fold_at(event.position().y())


class CodeEditor(QPlainTextEdit):
    composition_changed = Signal(bool)
    content_inserted = Signal()

    def __init__(self, placeholder="", read_only=False, json_mode=False):
        super().__init__()
        self.is_composing = False
        self.history_navigation = False
        self.fold_regions = {}
        self.collapsed_blocks = set()
        self.folding_enabled = False
        self.error_line = None
        self.setPlaceholderText(placeholder)
        self.setReadOnly(read_only)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(12)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.line_numbers = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_numbers)
        self.update_line_number_width()
        self.known_block_count = self.blockCount()
        self.document().contentsChange.connect(self.document_changed)
        if json_mode:
            self.highlighter = JsonHighlighter(self.document())

    def inputMethodEvent(self, event):
        composing = bool(event.preeditString())
        if composing != self.is_composing:
            self.is_composing = composing
            self.composition_changed.emit(composing)
        super().inputMethodEvent(event)

    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.content_inserted.emit()

    def setPlainText(self, text):
        super().setPlainText(text)
        self.content_inserted.emit()

    def document_changed(self, position, removed, added):
        if not removed and not added:
            return
        blocks = self.blockCount()
        if blocks != self.known_block_count or max(removed, added) > 16384:
            self.known_block_count = blocks
            self.reset_folding()
        elif self.error_line is not None:
            self.set_error(None)

    def undo(self):
        self.history_navigation = True
        try:
            super().undo()
        finally:
            self.history_navigation = False

    def redo(self):
        self.history_navigation = True
        try:
            super().redo()
        finally:
            self.history_navigation = False

    def keyPressEvent(self, event):
        if self.is_composing:
            super().keyPressEvent(event)
            return
        if event.matches(QKeySequence.Undo):
            self.undo()
            return
        if event.matches(QKeySequence.Redo):
            self.redo()
            return
        if not self.isReadOnly() and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            cursor = self.textCursor()
            if not cursor.hasSelection() and event.key() == Qt.Key_Tab:
                cursor.insertText("    ")
                return
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            selection_end = self.document().findBlock(end)
            last = selection_end.blockNumber()
            if end > start and end == selection_end.position():
                last -= 1
            block = self.document().findBlock(start)
            cursor.beginEditBlock()
            while block.isValid() and block.blockNumber() <= last:
                edit = QTextCursor(block)
                if event.key() == Qt.Key_Backtab:
                    spaces = min(4, len(block.text()) - len(block.text().lstrip(" ")))
                    edit.setPosition(block.position() + spaces, QTextCursor.KeepAnchor)
                    edit.removeSelectedText()
                else:
                    edit.insertText("    ")
                block = block.next()
            cursor.endEditBlock()
            return
        if not self.isReadOnly() and event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers():
            line = self.textCursor().block().text()
            indent = re.match(r"[ \t]*", line).group()
            if getattr(self, "python_mode", False) and line.rstrip().endswith(":"):
                indent += "    "
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
        super().keyPressEvent(event)

    def line_number_width(self):
        return (34 if self.folding_enabled else 18) + self.fontMetrics().horizontalAdvance("9") * len(
            str(self.blockCount())
        )

    def update_line_number_width(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_numbers(self, rect, dy):
        if dy:
            self.line_numbers.scroll(0, dy)
        else:
            self.line_numbers.update(0, rect.y(), self.line_numbers.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.line_numbers.setGeometry(QRect(rect.left(), rect.top(), self.line_number_width(), rect.height()))

    def visible_blocks(self):
        block = self.firstVisibleBlock()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        while block.isValid() and top <= self.viewport().height():
            height = round(self.blockBoundingRect(block).height())
            if block.isVisible():
                yield block, top, height
                top += height
            number = block.blockNumber()
            if number in self.collapsed_blocks and number in self.fold_regions:
                block = self.document().findBlockByNumber(self.fold_regions[number] + 1)
            else:
                block = block.next()

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_numbers)
        dark = QApplication.palette().color(QPalette.Window).lightness() < 128
        painter.fillRect(event.rect(), QColor("#242426" if dark else "#fafafa"))
        painter.setFont(self.font())
        for block, top, height in self.visible_blocks():
            if top + height < event.rect().top():
                continue
            painter.setPen(QColor("#e76f7a" if block.blockNumber() == self.error_line else "#8795ad"))
            painter.drawText(
                0,
                top,
                self.line_numbers.width() - 8,
                self.fontMetrics().height(),
                Qt.AlignRight,
                str(block.blockNumber() + 1),
            )
            if self.folding_enabled and block.blockNumber() in self.fold_regions:
                y = top + self.fontMetrics().height() // 2
                points = (
                    [QPoint(5, y - 4), QPoint(5, y + 4), QPoint(11, y)]
                    if block.blockNumber() in self.collapsed_blocks
                    else [QPoint(3, y - 2), QPoint(11, y - 2), QPoint(7, y + 3)]
                )
                painter.setBrush(QColor("#8e8e93"))
                painter.drawPolygon(QPolygon(points))

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.collapsed_blocks:
            return
        painter = QPainter(self.viewport())
        painter.setPen(QColor("#8e8e93"))
        painter.setFont(self.font())
        for block, top, height in self.visible_blocks():
            line = block.blockNumber()
            if line not in self.collapsed_blocks:
                continue
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.EndOfBlock)
            rect = self.cursorRect(cursor)
            end = self.fold_regions.get(line, line)
            closing = self.document().findBlockByNumber(end).text().strip()
            painter.drawText(
                rect.right() + 6, rect.top() + self.fontMetrics().ascent(), f" ⋯ {closing}  ({end-line} 行)"
            )

    def reset_folding(self):
        if not self.folding_enabled:
            return
        had_collapsed = bool(self.collapsed_blocks)
        self.collapsed_blocks.clear()
        self.fold_regions.clear()
        if had_collapsed:
            block = self.document().firstBlock()
            while block.isValid():
                block.setVisible(True)
                block = block.next()
            self.document().markContentsDirty(0, self.document().characterCount())
        self.set_error(None)
        self.line_numbers.update()

    def update_json_folds(self, regions=None):
        from app.utils.json_tools import json_fold_regions

        regions = json_fold_regions(self.toPlainText()) if regions is None else regions
        if self.folding_enabled and regions == self.fold_regions:
            return
        self.folding_enabled = True
        had_collapsed = bool(self.collapsed_blocks)
        self.fold_regions = regions
        self.collapsed_blocks.intersection_update(self.fold_regions)
        if had_collapsed:
            self.apply_folding()
        self.update_line_number_width()
        self.line_numbers.update()

    def toggle_fold_at(self, y):
        if not self.folding_enabled:
            return
        for block, top, height in self.visible_blocks():
            if top <= y < top + height:
                line = block.blockNumber()
                if line in self.fold_regions:
                    if line in self.collapsed_blocks:
                        self.collapsed_blocks.remove(line)
                    else:
                        self.collapsed_blocks.add(line)
                    self.apply_folding()
                return

    def reveal_cursor(self):
        line = self.textCursor().blockNumber()
        ancestors = {start for start in self.collapsed_blocks if start < line <= self.fold_regions.get(start, start)}
        if ancestors:
            self.collapsed_blocks.difference_update(ancestors)
            self.apply_folding()
        self.ensureCursorVisible()

    def apply_folding(self):
        hidden_until = -1
        block = self.document().firstBlock()
        cursor = self.textCursor()
        while block.isValid():
            line = block.blockNumber()
            visible = line > hidden_until
            block.setVisible(visible)
            if visible and line in self.collapsed_blocks:
                end = self.fold_regions.get(line, line)
                if line < cursor.blockNumber() <= end:
                    cursor.setPosition(block.position() + len(block.text().encode("utf-16-le", "surrogatepass")) // 2)
                hidden_until = end
            block = block.next()
        self.setTextCursor(cursor)
        self.document().markContentsDirty(0, self.document().characterCount())
        self.viewport().update()
        self.line_numbers.update()

    def collapse_all(self):
        self.collapsed_blocks = set(self.fold_regions)
        self.apply_folding()

    def expand_all(self):
        self.collapsed_blocks.clear()
        self.apply_folding()

    def set_error(self, line, column=0, message=""):
        self.error_line = line
        selections = []
        if line is not None:
            block = self.document().findBlockByNumber(line)
            if block.isValid():
                cursor = QTextCursor(block)
                cursor.setPosition(min(block.position() + column, block.position() + block.length() - 1))
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor("#f8d7da"))
                selection.format.setForeground(QColor("#9e2438"))
                selections.append(selection)
        self.setExtraSelections(selections)
        self.setToolTip(message)
        self.line_numbers.update()

    def replace_text(self, text):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(text)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.content_inserted.emit()


class EditorPanel(QWidget):
    file_limit = 10 * 1024 * 1024

    def __init__(self, title, placeholder="", read_only=False, json_mode=False):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.heading = QHBoxLayout()
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        self.heading.addWidget(label)
        self.heading.addStretch()
        self.copy_button = QToolButton()
        self.copy_button.setText("复制")
        self.copy_button.setAccessibleName("复制全部内容")
        self.copy_button.setAutoRaise(True)
        self.copy_button.clicked.connect(self.copy_text)
        self.heading.addWidget(self.copy_button)
        self.menu = QMenu(self)
        if not read_only:
            self.menu.addAction("从剪贴板替换", self.paste_text)
            self.menu.addAction("打开 UTF-8 文件…", self.open_file)
        self.menu.addAction("保存为 UTF-8 文件…", self.save_file)
        self.menu.addSeparator()
        self.menu.addAction("查找 / 替换", self.show_search)
        self.wrap_action = self.menu.addAction("自动换行")
        self.wrap_action.setCheckable(True)
        self.wrap_action.toggled.connect(self.set_wrap)
        self.menu.addSeparator()
        self.menu.addAction("清空", lambda: self.editor.replace_text(""))
        self.more_button = QToolButton()
        self.more_button.setText("更多")
        self.more_button.setAutoRaise(True)
        self.more_button.setAccessibleName("更多操作")
        self.more_button.setToolTip("文件、查找、换行等操作")
        self.more_button.setPopupMode(QToolButton.InstantPopup)
        self.more_button.setMenu(self.menu)
        self.heading.addWidget(self.more_button)
        self.update_icons()
        self.layout.addLayout(self.heading)
        self.search_bar = QWidget()
        search_container = QVBoxLayout(self.search_bar)
        search_container.setContentsMargins(0, 0, 0, 0)
        search_layout = QHBoxLayout()
        search_container.addLayout(search_layout)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("查找文本")
        self.find_input.setClearButtonEnabled(True)
        self.find_input.returnPressed.connect(self.find_next)
        self.case_sensitive = QCheckBox("Aa")
        self.case_sensitive.setToolTip("区分大小写")
        search_layout.addWidget(self.find_input, 1)
        search_layout.addWidget(self.case_sensitive)
        next_button = QPushButton("下一个")
        next_button.clicked.connect(self.find_next)
        search_layout.addWidget(next_button)
        if not read_only:
            self.replace_input = QLineEdit()
            self.replace_input.setPlaceholderText("替换为")
            replace_layout = QHBoxLayout()
            replace_layout.addWidget(self.replace_input, 1)
            search_container.addLayout(replace_layout)
            replace = QPushButton("全部替换")
            replace.clicked.connect(self.replace_all)
            replace_layout.addWidget(replace)
        close = QToolButton()
        close.setText("×")
        close.clicked.connect(self.close_search)
        search_layout.addWidget(close)
        self.layout.addWidget(self.search_bar)
        self.search_bar.hide()
        self.editor = CodeEditor(placeholder, read_only, json_mode)
        self.layout.addWidget(self.editor, 1)
        self.info = StatusLabel()
        self.info.setObjectName("editorInfo")
        self.layout.addWidget(self.info)
        self.editor.textChanged.connect(self.update_info)
        self.editor.cursorPositionChanged.connect(self.update_info)
        shortcut = QShortcut(QKeySequence.Find, self)
        shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.show_search)
        self.update_info()

    def update_info(self):
        self.copy_button.setEnabled(not self.editor.document().isEmpty())
        cursor = self.editor.textCursor()
        self.info.set_status(
            f"{self.editor.document().characterCount() - 1:,} 字符 · {self.editor.blockCount():,} 行 · 行 {cursor.blockNumber()+1}，列 {cursor.positionInBlock()+1}"
        )

    def copy_text(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.copy_button.setToolTip("已复制")
        icon = system_icon("checkmark", QApplication.palette().color(QPalette.Text).name())
        if not icon.isNull():
            self.copy_button.setIcon(icon)
        QTimer.singleShot(1200, self.update_icons)

    def update_icons(self):
        color = QApplication.palette().color(QPalette.Text).name()
        for button, name, tooltip in (
            (self.copy_button, "doc.on.doc", "复制全部内容"),
            (self.more_button, "ellipsis.circle", "更多操作"),
        ):
            icon = system_icon(name, color)
            button.setIcon(icon)
            button.setToolButtonStyle(Qt.ToolButtonTextOnly if icon.isNull() else Qt.ToolButtonIconOnly)
            button.setToolTip(tooltip)
            button.setMinimumSize(28, 28)

    def paste_text(self):
        self.editor.replace_text(QApplication.clipboard().text())

    def set_wrap(self, checked):
        self.editor.setLineWrapMode(QPlainTextEdit.WidgetWidth if checked else QPlainTextEdit.NoWrap)

    def show_search(self):
        self.search_bar.show()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def close_search(self):
        self.search_bar.hide()
        self.editor.setFocus()

    def find_next(self):
        query = self.find_input.text()
        if not query:
            return
        flags = QTextDocument.FindCaseSensitively if self.case_sensitive.isChecked() else QTextDocument.FindFlags()
        if self.editor.find(query, flags):
            self.editor.reveal_cursor()
            return
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        found = self.editor.document().find(query, cursor, flags)
        if not found.isNull():
            self.editor.setTextCursor(found)
            self.editor.reveal_cursor()
        else:
            self.info.set_status("未找到匹配文本", "error")

    def replace_all(self):
        query = self.find_input.text()
        if not query:
            return
        flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE
        result, count = re.subn(
            re.escape(query), lambda match: self.replace_input.text(), self.editor.toPlainText(), flags=flags
        )
        self.editor.replace_text(result)
        self.info.set_status(f"已替换 {count} 处")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文本文件", "", "文本文件 (*.json *.py *.txt *.jwt);;所有文件 (*)"
        )
        if path:
            self.read_file(path)

    def read_file(self, path):
        try:
            with Path(path).open("rb") as file:
                data = file.read(self.file_limit + 1)
            if len(data) > self.file_limit:
                raise ValueError("文件超过 10 MB，请截取需要处理的部分")
            text = data.decode("utf-8-sig")
        except (OSError, UnicodeError, ValueError) as error:
            self.info.set_status(f"打开失败：{error}", "error")
            return False
        self.editor.replace_text(text)
        self.info.set_status(f"已打开 {Path(path).name}")
        return True

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存文本文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if path:
            try:
                data = self.editor.toPlainText().encode("utf-8")
                file = QSaveFile(path)
                if not file.open(QIODevice.WriteOnly):
                    raise OSError(file.errorString())
                if file.write(data) != len(data):
                    file.cancelWriting()
                    raise OSError(file.errorString())
                if not file.commit():
                    raise OSError(file.errorString())
            except (OSError, UnicodeError) as error:
                self.info.set_status(f"保存失败：{error}", "error")
                return
            self.info.set_status(f"已保存 {Path(path).name}")

import difflib

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QTextCursor, QTextFormat
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QSplitter, QTextEdit, QVBoxLayout

from app.core.components import EditorPanel, StatusLabel
from app.widgets import BaseWidget


class DiffWidget(BaseWidget):
    name = "diff"
    line_limit = 5000

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.status = StatusLabel("粘贴两份文本，自动按行比较")
        toolbar.addWidget(self.status, 1)
        self.ignore_space = QCheckBox("忽略行尾空格")
        self.ignore_space.toggled.connect(self.schedule)
        toolbar.addWidget(self.ignore_space)
        layout.addLayout(toolbar)
        self.before = EditorPanel("原文", "粘贴原文")
        self.after = EditorPanel("新文本", "粘贴新文本")
        columns = QSplitter(Qt.Horizontal)
        columns.addWidget(self.before)
        columns.addWidget(self.after)
        columns.setChildrenCollapsible(False)
        self.patch = EditorPanel("Unified diff", read_only=True)
        vertical = QSplitter(Qt.Vertical)
        vertical.addWidget(columns)
        vertical.addWidget(self.patch)
        vertical.setSizes([400, 180])
        vertical.setChildrenCollapsible(False)
        layout.addWidget(vertical, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(400)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.compare)
        self.before.editor.textChanged.connect(self.schedule)
        self.after.editor.textChanged.connect(self.schedule)

    def schedule(self):
        self.patch.editor.clear()
        self.before.editor.setExtraSelections([])
        self.after.editor.setExtraSelections([])
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def compare(self):
        self.timer.stop()
        before, after = (panel.editor.toPlainText() for panel in (self.before, self.after))
        old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
        if (
            max(len(before.encode("utf-8")), len(after.encode("utf-8"))) > 1_000_000
            or max(len(old), len(new)) > self.line_limit
        ):
            self.status.set_status("单侧最多比较 1 MB / 5,000 行，请缩小比较范围", "error")
            return
        if self.ignore_space.isChecked():
            old = [line.rstrip(" \t\r\n") + ("\n" if line.endswith("\n") else "") for line in old]
            new = [line.rstrip(" \t\r\n") + ("\n" if line.endswith("\n") else "") for line in new]
        matcher = difflib.SequenceMatcher(None, old, new, autojunk=True)
        removed = added = 0
        old_marks, new_marks = [], []
        for tag, i, j, x, y in matcher.get_opcodes():
            if tag == "equal":
                continue
            removed += j - i
            added += y - x
            old_marks.extend(range(i, j))
            new_marks.extend(range(x, y))
        self.mark_lines(self.before.editor, old_marks, "#f8d7da")
        self.mark_lines(self.after.editor, new_marks, "#d3efdf")
        patch = []
        for line in difflib.unified_diff(old, new, fromfile="before", tofile="after"):
            patch.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
        self.patch.editor.setPlainText("".join(patch))
        self.status.set_status(f"新增 {added} 行 · 删除 {removed} 行" if removed or added else "文本一致", "success")

    @staticmethod
    def mark_lines(editor, lines, color):
        selections = []
        for line in lines:
            block = editor.document().findBlockByNumber(line)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(block)
            selection.format.setBackground(QColor(color))
            selection.format.setForeground(QColor("#243047"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selections.append(selection)
        editor.setExtraSelections(selections)

    def switch_in(self):
        self.before.editor.setFocus()

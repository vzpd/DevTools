import json

from PySide6.QtCore import QSignalBlocker, Qt, QThreadPool, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout

from app.core.components import EditorPanel, StatusLabel
from app.core.json_task import JsonRequest, JsonTask
from app.utils.json_tools import map_json_positions, parse_json
from app.widgets import BaseWidget


class JsonWidget(BaseWidget):
    name = "json"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.status = StatusLabel("粘贴 JSON 后自动校验、格式化；点击行号旁的三角折叠")
        toolbar.addWidget(self.status, 1)
        toolbar.addWidget(QLabel("缩进"))
        self.indent = QComboBox()
        self.indent.addItems(["2 空格", "4 空格"])
        toolbar.addWidget(self.indent)
        self.escape_unicode = QCheckBox("转义 Unicode")
        toolbar.addWidget(self.escape_unicode)
        layout.addLayout(toolbar)
        self.input_panel = EditorPanel("JSON", "粘贴 JSON，自动格式化并支持折叠", json_mode=True)
        self.json_pte = self.input_panel.editor
        self.json_pte.folding_enabled = True
        self.json_pte.update_line_number_width()
        self.input_panel.menu.addSeparator()
        self.input_panel.menu.addAction("立即格式化", self.format_json_input)
        self.input_panel.menu.addAction("压缩", self.minify)
        self.input_panel.menu.addAction("全部折叠", self.json_pte.collapse_all)
        self.input_panel.menu.addAction("全部展开", self.json_pte.expand_all)
        self.input_panel.menu.addSeparator()
        self.input_panel.menu.addAction("JSON → 转义字符串", self.escape_string)
        self.input_panel.menu.addAction("转义字符串 → JSON", self.unescape_string)
        layout.addWidget(self.input_panel, 1)
        self.parse_timer = QTimer(self)
        self.parse_timer.setSingleShot(True)
        self.parse_timer.setInterval(650)
        self.revision = 0
        self.active_task = None
        self.pending_request = None
        self.format_on_idle = False
        self.parse_timer.timeout.connect(self.process_pending)
        self.json_pte.textChanged.connect(self.schedule_parse)
        self.json_pte.content_inserted.connect(self.schedule_paste)
        self.json_pte.composition_changed.connect(self.composition_changed)
        self.indent.currentIndexChanged.connect(self.auto_format)
        self.escape_unicode.toggled.connect(self.auto_format)

    def schedule_parse(self):
        self.revision += 1
        self.pending_request = None
        self.format_on_idle = not self.json_pte.history_navigation
        self.parse_timer.stop()
        if not self.json_pte.is_composing:
            self.parse_timer.start()

    def schedule_paste(self):
        self.format_on_idle = True
        if not self.json_pte.is_composing:
            self.parse_timer.start()

    def composition_changed(self, composing):
        self.revision += 1
        self.pending_request = None
        self.parse_timer.stop()
        if not composing:
            self.format_on_idle = True
            self.parse_timer.start()

    def process_pending(self):
        indent = (2 if self.indent.currentIndex() == 0 else 4) if self.format_on_idle else None
        self.format_on_idle = False
        self.transform(indent)

    def auto_format(self):
        self.transform(2 if self.indent.currentIndex() == 0 else 4)

    def format_json_input(self, json_data=None):
        self.transform(2 if self.indent.currentIndex() == 0 else 4, json_data, locate=True)

    def minify(self):
        self.transform(0, locate=True)

    def transform(self, indent, text=None, locate=False):
        self.parse_timer.stop()
        if self.json_pte.is_composing:
            return
        if isinstance(text, str) and text != self.json_pte.toPlainText():
            self.json_pte.replace_text(text)
            self.parse_timer.stop()
        source = self.json_pte.toPlainText()
        if not source.strip():
            self.status.set_status("粘贴 JSON 后自动校验、格式化；点击行号旁的三角折叠")
            self.json_pte.set_error(None)
            return
        self.revision += 1
        cursor = self.json_pte.textCursor()
        request = JsonRequest(
            source, self.revision, indent, self.escape_unicode.isChecked(), (cursor.anchor(), cursor.position()), locate
        )
        if self.active_task is not None:
            self.pending_request = request
        else:
            self.start_task(request)

    def start_task(self, request):
        self.active_task = JsonTask(request)
        self.active_task.signals.finished.connect(self.task_finished, Qt.QueuedConnection)
        self.status.set_status("正在后台处理…")
        QThreadPool.globalInstance().start(self.active_task)

    def task_finished(self, result):
        self.active_task = None
        request = result.request
        if request.revision == self.revision and not self.json_pte.is_composing:
            if result.error is not None:
                self.show_error(result.error, request.locate)
            else:
                folded = {
                    line
                    for line in self.json_pte.collapsed_blocks
                    if self.json_pte.fold_regions.get(line) == result.folds.get(line)
                }
                if result.text is not None and result.text != request.source:
                    self.replace_preserving_cursor(request.source, result.text, request.positions, result.positions)
                self.json_pte.update_json_folds(result.folds)
                if folded and folded != self.json_pte.collapsed_blocks:
                    self.json_pte.collapsed_blocks = folded
                    self.json_pte.apply_folding()
                message = "JSON 有效"
                if request.indent is not None:
                    message += " · 已压缩" if request.indent == 0 else " · 已格式化"
                self.status.set_status(message, "success")
        pending, self.pending_request = self.pending_request, None
        if pending is not None and pending.revision == self.revision and not self.json_pte.is_composing:
            self.start_task(pending)

    def replace_preserving_cursor(self, source, result, original_positions=None, mapped_positions=None):
        cursor = self.json_pte.textCursor()
        current = (cursor.anchor(), cursor.position())
        positions = mapped_positions if current == original_positions else map_json_positions(source, result, current)
        blocker = QSignalBlocker(self.json_pte)
        self.json_pte.replace_text(result)
        self.json_pte.reset_folding()
        del blocker
        cursor = self.json_pte.textCursor()
        cursor.setPosition(positions[0])
        cursor.setPosition(positions[1], QTextCursor.KeepAnchor)
        self.json_pte.setTextCursor(cursor)
        self.input_panel.update_info()

    def show_error(self, error, locate=False):
        if isinstance(error, json.JSONDecodeError):
            descriptions = {
                "Expecting property name enclosed in double quotes": "对象键必须使用双引号，请检查多余的逗号",
                "Expecting value": "缺少值，请检查逗号、冒号或是否使用了单引号",
                "Expecting ',' delimiter": "缺少逗号，或括号未正确闭合",
                "Expecting ':' delimiter": "键后缺少冒号",
                "Extra data": "存在多个根值或多余内容",
                "Unterminated string starting at": "字符串缺少结束双引号",
            }
            description = descriptions.get(error.msg, error.msg)
            message = f"第 {error.lineno} 行，第 {error.colno} 列：{description}"
            text = self.json_pte.toPlainText()
            start = text.rfind("\n", 0, error.pos) + 1
            column = len(text[start : error.pos].encode("utf-16-le", "surrogatepass")) // 2
            self.json_pte.set_error(error.lineno - 1, column, message)
            if locate:
                cursor = self.json_pte.textCursor()
                cursor.setPosition(len(text[: error.pos].encode("utf-16-le", "surrogatepass")) // 2)
                self.json_pte.setTextCursor(cursor)
                self.json_pte.centerCursor()
        else:
            message = "嵌套层级过深" if isinstance(error, RecursionError) else str(error)
        self.status.set_status(message, "error")

    def escape_string(self):
        self.parse_timer.stop()
        self.json_pte.replace_text(json.dumps(self.json_pte.toPlainText(), ensure_ascii=False))
        self.auto_format()

    def unescape_string(self):
        try:
            value = json.loads(self.json_pte.toPlainText())
            if not isinstance(value, str):
                raise ValueError("当前内容不是 JSON 字符串")
        except (ValueError, RecursionError) as error:
            self.show_error(error)
            return
        try:
            parse_json(value)
        except (ValueError, RecursionError):
            self.status.set_status("解码后的字符串不是合法 JSON，已保留原文", "error")
            return
        self.json_pte.replace_text(value)
        self.auto_format()

    def load_example(self):
        self.json_pte.replace_text(
            '{"项目":"DevTools","enabled":true,"version":1.0,"tools":["JSON","JWT"],"note":null}'
        )
        self.auto_format()

    def switch_in(self):
        self.json_pte.setFocus()

import base64
import binascii
import html
import json
import re
from urllib.parse import quote, unquote_to_bytes

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

from app.core.components import EditorPanel, StatusLabel
from app.widgets import BaseWidget


def convert_text(text, mode, encode):
    if mode == "Base64":
        return (
            base64.b64encode(text.encode()).decode()
            if encode
            else base64.b64decode("".join(text.split()), validate=True).decode("utf-8")
        )
    if mode == "Base64URL":
        return (
            base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
            if encode
            else base64.b64decode(
                "".join(text.split()) + "=" * (-len("".join(text.split())) % 4), altchars=b"-_", validate=True
            ).decode("utf-8")
        )
    if mode == "URL":
        if not encode and re.search(r"%(?![0-9A-Fa-f]{2})", text):
            raise ValueError("URL 中存在不完整的百分号编码")
        return quote(text, safe="") if encode else unquote_to_bytes(text).decode("utf-8")
    if mode == "HTML":
        return html.escape(text, quote=True) if encode else html.unescape(text)
    if mode == "Hex":
        return text.encode().hex() if encode else bytes.fromhex(text).decode("utf-8")
    if encode:
        return json.dumps(text, ensure_ascii=False)
    value = json.loads(text)
    if not isinstance(value, str):
        raise ValueError("请输入包含双引号的 JSON 字符串")
    return value


class CodecWidget(BaseWidget):
    name = "codec"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Base64", "Base64URL", "URL", "HTML", "Hex", "JSON 字符串"])
        self.direction = QComboBox()
        self.direction.addItems(["编码", "解码"])
        toolbar.addWidget(self.mode)
        toolbar.addWidget(self.direction)
        swap = QPushButton("交换输入与结果")
        swap.clicked.connect(self.swap)
        toolbar.addWidget(swap)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.source = EditorPanel("输入", "输入文本，自动转换")
        self.result = EditorPanel("结果", read_only=True)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.source)
        splitter.addWidget(self.result)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)
        self.status = StatusLabel("UTF-8 文本转换 · URL 编码按单个组件处理")
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.convert)
        self.source.editor.textChanged.connect(self.schedule)
        self.mode.currentIndexChanged.connect(self.convert)
        self.direction.currentIndexChanged.connect(self.convert)

    def schedule(self):
        self.result.editor.clear()
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def convert(self):
        self.timer.stop()
        text = self.source.editor.toPlainText()
        try:
            result = convert_text(text, self.mode.currentText(), self.direction.currentIndex() == 0) if text else ""
        except (ValueError, UnicodeError, binascii.Error, RecursionError) as error:
            self.result.editor.clear()
            self.status.set_status(f"无法转换：{error}", "error")
            return
        self.result.editor.setPlainText(result)
        self.status.set_status(
            "转换完成 · UTF-8 文本" if text else "UTF-8 文本转换 · URL 编码按单个组件处理",
            "success" if text else "neutral",
        )

    def swap(self):
        if self.status.property("state") == "error":
            return
        value = self.result.editor.toPlainText()
        self.direction.setCurrentIndex(1 - self.direction.currentIndex())
        self.source.editor.replace_text(value)
        self.convert()

    def switch_in(self):
        self.source.editor.setFocus()

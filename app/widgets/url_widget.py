import json
import re
from urllib.parse import parse_qs, unquote, urlsplit

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout

from app.core.components import EditorPanel, StatusLabel
from app.widgets import BaseWidget


def parse_url(text):
    text = text.strip()
    if len(text) > 16384:
        raise ValueError("URL 最多 16,384 个字符")
    if not text:
        return ""
    if re.search(r"[\x00-\x20\x7f]", text):
        raise ValueError("URL 中的空格和控制字符需要先进行百分号编码")
    if re.search(r"%(?![0-9a-fA-F]{2})", text):
        raise ValueError("URL 中存在不完整的百分号编码")
    url = urlsplit(text)
    if not url.scheme or not url.netloc or not url.hostname:
        raise ValueError("请输入包含协议和主机名的完整 URL，例如 https://example.com/path?a=1")
    return json.dumps(
        {
            "scheme": url.scheme,
            "hostname": url.hostname,
            "port": url.port,
            "path": unquote(url.path, errors="strict"),
            "query": parse_qs(url.query, keep_blank_values=True, errors="strict", max_num_fields=1000),
            "fragment": unquote(url.fragment, errors="strict"),
        },
        ensure_ascii=False,
        indent=2,
    )


class UrlWidget(BaseWidget):
    name = "url"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.source = EditorPanel("URL", "https://example.com/path?name=DevTools&tag=a&tag=b#section")
        self.source.editor.setMaximumHeight(140)
        self.result = EditorPanel("解析结果", read_only=True, json_mode=True)
        layout.addWidget(self.source)
        layout.addWidget(self.result, 1)
        self.status = StatusLabel("不发起网络请求；重复参数保留为数组，空值保留；查询中的 + 解码为空格")
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.convert)
        self.source.editor.textChanged.connect(self.schedule)

    def schedule(self):
        self.result.editor.clear()
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def convert(self):
        self.timer.stop()
        try:
            result = parse_url(self.source.editor.toPlainText())
        except (ValueError, UnicodeError) as error:
            self.result.editor.clear()
            self.status.set_status(f"无法解析：{error}", "error")
            return
        self.result.editor.setPlainText(result)
        self.status.set_status("不发起网络请求；重复参数保留为数组，空值保留；查询中的 + 解码为空格")

    def switch_in(self):
        self.source.editor.setFocus()

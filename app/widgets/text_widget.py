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

TEXT_OPERATIONS = ("按行去重", "升序排序", "降序排序", "去除空行", "去除行首尾空白", "转为大写", "转为小写")


def transform_text(text, operation):
    if len(text.encode("utf-8")) > 1_000_000:
        raise ValueError("最多处理 1 MB 文本")
    if operation == "转为大写":
        return text.upper()
    if operation == "转为小写":
        return text.lower()
    lines = text.splitlines()
    if operation == "按行去重":
        lines = list(dict.fromkeys(lines))
    elif operation == "升序排序":
        lines = sorted(lines)
    elif operation == "降序排序":
        lines = sorted(lines, reverse=True)
    elif operation == "去除空行":
        lines = [line for line in lines if line.strip()]
    elif operation == "去除行首尾空白":
        lines = [line.strip() for line in lines]
    else:
        raise ValueError("请选择有效的整理方式")
    result = "\n".join(lines)
    return result + "\n" if lines and text.endswith(("\n", "\r")) else result


class TextWidget(BaseWidget):
    name = "text"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.operation = QComboBox()
        self.operation.addItems(TEXT_OPERATIONS)
        toolbar.addWidget(self.operation)
        use_result = QPushButton("用结果继续整理")
        use_result.clicked.connect(self.use_result)
        toolbar.addWidget(use_result)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.source = EditorPanel("原始文本", "粘贴多行文本，选择整理方式")
        self.result = EditorPanel("整理结果", read_only=True)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.source)
        splitter.addWidget(self.result)
        layout.addWidget(splitter, 1)
        self.status = StatusLabel("去重保留首次出现的行；排序区分大小写，按 Unicode 顺序；行操作输出统一为 LF")
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.convert)
        self.source.editor.textChanged.connect(self.schedule)
        self.operation.currentIndexChanged.connect(self.convert)

    def schedule(self):
        self.result.editor.clear()
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def convert(self):
        self.timer.stop()
        try:
            result = transform_text(self.source.editor.toPlainText(), self.operation.currentText())
        except (ValueError, UnicodeError) as error:
            self.result.editor.clear()
            self.status.set_status(str(error), "error")
            return
        self.result.editor.setPlainText(result)
        self.status.set_status("去重保留首次出现的行；排序区分大小写，按 Unicode 顺序；行操作输出统一为 LF")

    def use_result(self):
        if self.status.property("state") != "error" and not self.timer.isActive():
            self.source.editor.replace_text(self.result.editor.toPlainText())
            self.convert()

    def switch_in(self):
        self.source.editor.setFocus()

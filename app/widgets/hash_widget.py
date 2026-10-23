import hashlib
import uuid

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
)

from app.core.components import EditorPanel, StatusLabel
from app.widgets import BaseWidget


class HashWidget(BaseWidget):
    name = "hash"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("文本摘要"))
        self.algorithm = QComboBox()
        self.algorithm.addItems(["SHA-256", "SHA-512", "SHA-1", "MD5"])
        toolbar.addWidget(self.algorithm)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.source = EditorPanel("输入文本（UTF-8）", "输入文本，自动计算摘要")
        self.result = EditorPanel("摘要", read_only=True)
        self.result.wrap_action.setChecked(True)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.source)
        splitter.addWidget(self.result)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)
        self.status = StatusLabel("摘要用于内容校验；MD5 / SHA-1 不适合安全用途")
        layout.addWidget(self.status)
        uuid_panel = EditorPanel("UUID v4", read_only=True)
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(1)
        self.count.setToolTip("生成数量")
        generate = QPushButton("生成")
        generate.clicked.connect(self.generate)
        uuid_panel.heading.insertWidget(1, self.count)
        uuid_panel.heading.insertWidget(2, generate)
        self.uuid_output = uuid_panel.editor
        self.uuid_output.setMaximumHeight(110)
        self.uuid_output.setPlaceholderText("选择数量后生成，结果可以直接复制为多行")
        layout.addWidget(uuid_panel)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.calculate)
        self.source.editor.textChanged.connect(self.schedule)
        self.algorithm.currentIndexChanged.connect(self.calculate)
        self.calculate()

    def schedule(self):
        self.result.editor.clear()
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def calculate(self):
        self.timer.stop()
        try:
            algorithm = self.algorithm.currentText().replace("-", "").lower()
            digest = hashlib.new(
                algorithm, self.source.editor.toPlainText().encode("utf-8"), usedforsecurity=False
            ).hexdigest()
        except (ValueError, UnicodeError) as error:
            self.result.editor.clear()
            self.status.set_status(f"无法计算：{error}", "error")
            return
        self.result.editor.setPlainText(digest)
        self.status.set_status("按 UTF-8 字节计算，包含换行和空格 · MD5 / SHA-1 不适合安全用途")

    def generate(self):
        self.uuid_output.setPlainText("\n".join(str(uuid.uuid4()) for _ in range(self.count.value())))

    def switch_in(self):
        self.source.editor.setFocus()

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
)

from app.core.components import StatusLabel
from app.widgets import BaseWidget

BASES = (("二进制", 2), ("八进制", 8), ("十进制", 10), ("十六进制", 16))


def convert_integer(text, base):
    text = text.strip()
    if base not in (2, 8, 10, 16):
        raise ValueError("不支持的进制")
    if len(text) > 1024:
        raise ValueError("输入最多 1,024 个字符")
    if not text:
        return ("", "", "", "")
    try:
        value = int(text, base)
    except ValueError:
        raise ValueError("请输入符合所选进制的整数，不支持小数") from None
    return (format(value, "b"), format(value, "o"), str(value), format(value, "X"))


class RadixWidget(BaseWidget):
    name = "radix"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("输入整数")
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.base = QComboBox()
        for label, base in BASES:
            self.base.addItem(label, base)
        self.base.setCurrentIndex(2)
        form.addRow("输入进制", self.base)
        self.source = QLineEdit()
        self.source.setPlaceholderText("输入整数，支持负数及对应的 0b / 0o / 0x 前缀")
        self.source.setMaxLength(8192)
        form.addRow("数值", self.source)
        layout.addWidget(group)
        output = QGroupBox("转换结果")
        results = QFormLayout(output)
        results.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.outputs = []
        for label, _ in BASES:
            field = QLineEdit()
            field.setReadOnly(True)
            field.setMaxLength(8192)
            self.outputs.append(field)
            row = QHBoxLayout()
            row.addWidget(field, 1)
            copy = QToolButton()
            copy.setText("复制")
            copy.setAccessibleName(f"复制{label}")
            copy.clicked.connect(lambda checked=False, field=field: QApplication.clipboard().setText(field.text()))
            row.addWidget(copy)
            results.addRow(label, row)
        layout.addWidget(output)
        self.status = StatusLabel("整数精确转换，不受 JavaScript 安全整数范围限制")
        layout.addWidget(self.status)
        layout.addStretch()
        self.source.textChanged.connect(self.convert)
        self.base.currentIndexChanged.connect(self.convert)

    def convert(self):
        try:
            values = convert_integer(self.source.text(), self.base.currentData())
        except ValueError as error:
            for field in self.outputs:
                field.clear()
            self.status.set_status(str(error), "error")
            return
        for field, value in zip(self.outputs, values):
            field.setText(value)
        self.status.set_status("整数精确转换；负数使用负号表示，不使用补码")

    def switch_in(self):
        self.source.setFocus()

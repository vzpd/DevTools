from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from app.core.components import StatusLabel
from app.core.icons import system_icon
from app.core.timezone_selector import TimezoneSelector
from app.utils.time_tools import parse_datetime
from app.widgets import BaseWidget


class TimestampWidget(BaseWidget):
    name = "timestamp"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("时区"))
        self.timezone = TimezoneSelector()
        toolbar.addWidget(self.timezone)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        now_group = QGroupBox("当前时间")
        now_layout = QFormLayout(now_group)
        now_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.time_le = self.add_output(now_layout, "日期时间")
        self.ts_le = self.add_output(now_layout, "Unix 秒")
        self.ts_ms_le = self.add_output(now_layout, "Unix 毫秒")
        layout.addWidget(now_group)
        timestamp_group = QGroupBox("时间戳 → 日期时间")
        timestamp_layout = QFormLayout(timestamp_group)
        timestamp_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        input_row = QHBoxLayout()
        self.ts_input = QLineEdit()
        self.ts_input.setPlaceholderText("例如 1729166400，支持负数及小数")
        self.unit = QComboBox()
        self.unit.addItems(["秒", "毫秒", "自动识别"])
        self.unit.setCurrentIndex(2)
        now_button = QPushButton("填入当前值")
        now_button.clicked.connect(self.fill_now)
        input_row.addWidget(self.ts_input, 1)
        input_row.addWidget(self.unit)
        input_row.addWidget(now_button)
        timestamp_layout.addRow("时间戳", input_row)
        self.date_output = self.add_output(timestamp_layout, "转换结果")
        layout.addWidget(timestamp_group)
        date_group = QGroupBox("日期时间 → 时间戳")
        date_layout = QFormLayout(date_group)
        date_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.dt_input_le = QLineEdit()
        self.dt_input_le.setPlaceholderText("YYYY-MM-DD HH:mm:ss.SSS 或 ISO 8601（可带时区）")
        date_layout.addRow("日期时间", self.dt_input_le)
        self.seconds_output = self.add_output(date_layout, "Unix 秒")
        self.millis_output = self.add_output(date_layout, "Unix 毫秒")
        layout.addWidget(date_group)
        self.status = StatusLabel("无时区的日期按所选时区解析；带时区的 ISO 8601 按自身时区解析")
        layout.addWidget(self.status)
        layout.addStretch()
        self.ts_input.textChanged.connect(self.convert)
        self.dt_input_le.textChanged.connect(self.convert)
        self.unit.currentIndexChanged.connect(self.convert)
        self.timezone.currentTextChanged.connect(self.convert)
        self.timezone.currentTextChanged.connect(self.update_time)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(100)
        self.update_time()

    @staticmethod
    def add_output(layout, label):
        field = QLineEdit()
        field.setReadOnly(True)
        row = QHBoxLayout()
        row.addWidget(field, 1)
        button = QToolButton()
        button.setAutoRaise(True)
        button.setIcon(system_icon("doc.on.doc"))
        button.setProperty("systemSymbol", "doc.on.doc")
        button.setToolTip(f"复制{label}")
        button.setAccessibleName(f"复制{label}")
        button.setMinimumSize(28, 28)
        if button.icon().isNull():
            button.setText("复制")
        button.clicked.connect(lambda: QApplication.clipboard().setText(field.text()))
        row.addWidget(button)
        layout.addRow(label, row)
        return field

    def get_tz(self):
        return self.timezone.timezone()

    def display_datetime(self, value):
        return value.astimezone(self.get_tz()).isoformat(sep=" ", timespec="milliseconds")

    def update_time(self):
        now = datetime.now(UTC)
        micros = self.epoch_microseconds(now)
        try:
            self.time_le.setText(self.display_datetime(now))
        except ValueError:
            self.time_le.clear()
        self.ts_le.setText(str(micros // 1_000_000))
        self.ts_ms_le.setText(str(micros // 1000))

    @staticmethod
    def epoch_microseconds(value):
        delta = value.astimezone(UTC) - datetime(1970, 1, 1, tzinfo=UTC)
        return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds

    def fill_now(self):
        self.ts_input.setText(self.ts_le.text() if self.unit.currentIndex() == 0 else self.ts_ms_le.text())

    def convert(self):
        errors = []
        try:
            zone = self.get_tz()
        except ValueError as error:
            self.date_output.clear()
            self.seconds_output.clear()
            self.millis_output.clear()
            self.status.set_status(str(error), "error")
            return
        self.date_output.clear()
        self.seconds_output.clear()
        self.millis_output.clear()
        if text := self.ts_input.text().strip():
            try:
                number = Decimal(text)
                if not number.is_finite() or number.copy_abs() > Decimal("1e16"):
                    raise ValueError("时间戳超出支持范围")
                is_millis = self.unit.currentIndex() == 1 or (
                    self.unit.currentIndex() == 2 and number.copy_abs() >= Decimal("1e11")
                )
                micros = number * (1000 if is_millis else 1_000_000)
                value = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=int(micros))
                self.date_output.setText(self.display_datetime(value))
            except (ValueError, OverflowError, InvalidOperation):
                errors.append("时间戳无效或超出日期范围")
        if text := self.dt_input_le.text().strip():
            try:
                value = parse_datetime(text, zone)
                micros = self.epoch_microseconds(value)
                self.seconds_output.setText(format(Decimal(micros) / 1_000_000, "f"))
                self.millis_output.setText(str(micros // 1000))
            except (ValueError, OverflowError, OSError) as error:
                errors.append(f"日期无法解析：{error}")
        self.status.set_status(
            "；".join(errors) if errors else "自动模式按数值绝对值 ≥ 10¹¹ 识别毫秒；不确定时请手动选择单位",
            "error" if errors else "neutral",
        )

    def switch_in(self):
        self.ts_input.setFocus()

from datetime import UTC, datetime

from croniter import CroniterBadCronError, CroniterBadDateError, croniter
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core.components import StatusLabel
from app.core.timezone_selector import TimezoneSelector
from app.utils.time_tools import parse_datetime
from app.widgets import BaseWidget


class CronWidget(BaseWidget):
    name = "cron"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        expression_group = QGroupBox("Cron 表达式")
        form = QFormLayout(expression_group)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.cron_le_input = QLineEdit()
        self.cron_le_input.setPlaceholderText("*/5 * * * *")
        form.addRow("表达式", self.cron_le_input)
        self.presets = QComboBox()
        self.presets.addItem("选择常用表达式…", None)
        for label, value in (
            ("每 5 分钟", "*/5 * * * *"),
            ("每小时", "0 * * * *"),
            ("每天 09:00", "0 9 * * *"),
            ("工作日 09:00", "0 9 * * 1-5"),
            ("每月 1 日", "0 0 1 * *"),
        ):
            self.presets.addItem(label, value)
        self.presets.activated.connect(self.use_preset)
        form.addRow("常用规则", self.presets)
        base_row = QHBoxLayout()
        self.use_now = QCheckBox("从当前时间起算")
        self.use_now.setChecked(True)
        self.base_time = QLineEdit()
        self.base_time.setPlaceholderText("YYYY-MM-DD HH:mm:ss 或 ISO 8601")
        self.base_time.setEnabled(False)
        self.use_now.toggled.connect(lambda checked: self.base_time.setEnabled(not checked))
        base_row.addWidget(self.use_now)
        base_row.addWidget(self.base_time, 1)
        form.addRow("起算时间", base_row)
        layout.addWidget(expression_group)
        hint = QLabel(
            "分 0–59    时 0–23    日 1–31    月 1–12    周 0–6（周日=0）\n支持 * 任意值、, 列表、- 范围、/ 步长；日与周同时指定时按 OR 匹配。"
        )
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("预览时区"))
        self.timezone = TimezoneSelector()
        toolbar.addWidget(self.timezone)
        toolbar.addWidget(QLabel("次数"))
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(10)
        toolbar.addWidget(self.count)
        refresh = QPushButton("刷新预览")
        refresh.setObjectName("primary")
        refresh.setDefault(True)
        refresh.clicked.connect(self.cal_cron)
        toolbar.addWidget(refresh)
        toolbar.addStretch()
        copy = QPushButton("复制结果")
        copy.clicked.connect(self.copy_results)
        toolbar.addWidget(copy)
        layout.addLayout(toolbar)
        self.status = StatusLabel("输入标准五字段 Cron 表达式")
        layout.addWidget(self.status)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["序号", "执行时间（含 UTC 偏移）", "距上次间隔"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.cal_cron)
        self.cron_le_input.textChanged.connect(self.schedule_preview)
        self.timezone.currentTextChanged.connect(self.schedule_preview)
        self.base_time.textChanged.connect(self.schedule_preview)
        self.use_now.toggled.connect(self.schedule_preview)
        self.count.valueChanged.connect(self.cal_cron)

    def use_preset(self):
        value = self.presets.currentData()
        if value:
            self.cron_le_input.setText(value)

    def schedule_preview(self):
        self.table.setRowCount(0)
        self.status.set_status("等待输入完成…")
        self.timer.start()

    def cal_cron(self):
        self.timer.stop()
        self.table.setRowCount(0)
        text = self.cron_le_input.text().strip()
        if not text:
            self.status.set_status("输入标准五字段 Cron 表达式")
            return
        try:
            if len(text.split()) != 5:
                raise ValueError("请使用五字段格式：分 时 日 月 周")
            zone = self.timezone.timezone()
            now = (
                datetime.now(zone)
                if self.use_now.isChecked()
                else parse_datetime(self.base_time.text().strip(), zone).astimezone(zone)
            )
            iterator = croniter(text, now, max_years_between_matches=5)
            values = [
                iterator.get_next(datetime).isoformat(sep=" ", timespec="seconds") for _ in range(self.count.value())
            ]
        except (CroniterBadCronError, CroniterBadDateError, ValueError, OverflowError) as error:
            self.status.set_status(f"无法生成执行时间：{error}", "error")
            return
        self.table.setRowCount(len(values))
        previous = now
        for row, value in enumerate(values):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(value))
            current = datetime.fromisoformat(value)
            seconds = int((current.astimezone(UTC) - previous.astimezone(UTC)).total_seconds())
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            interval = (
                f"{days}天 {hours:02}:{minutes:02}:{seconds:02}" if days else f"{hours:02}:{minutes:02}:{seconds:02}"
            )
            self.table.setItem(row, 2, QTableWidgetItem(interval))
            previous = current
        self.status.set_status(
            f"表达式有效 · 从 {now.strftime('%Y-%m-%d %H:%M:%S %Z')} 起的 {len(values)} 次执行", "success"
        )

    def copy_results(self):
        QApplication.clipboard().setText(
            "\n".join(self.table.item(row, 1).text() for row in range(self.table.rowCount()))
        )

    def switch_in(self):
        self.cron_le_input.setFocus()

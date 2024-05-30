import time
from datetime import UTC, datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from ..core.customer_line_edit import SingleClickCopyLineEdit
from . import BaseWidget


class TimestampWidget(BaseWidget):
    name = "timestamp"

    def __init__(self):
        super().__init__()
        self.local_tz = datetime.fromtimestamp(time.time()).astimezone().tzinfo
        self.utc_tz_radio = QRadioButton("utc+0")
        self.local_tz_radio = QRadioButton("local")
        self.ts_ms_le = SingleClickCopyLineEdit()
        self.ts_le = SingleClickCopyLineEdit()
        self.time_le = SingleClickCopyLineEdit()
        self.dt_input_le = QLineEdit()
        self.set_ui()
        self.set_value()

    def set_ui(self):
        self.update()
        v_box = QVBoxLayout()

        tz_h_box = QHBoxLayout()
        tz_radio_group = QButtonGroup()
        self.local_tz_radio.click()
        self.local_tz_radio.clicked.connect(lambda: self.clear_all_line_edits())
        self.utc_tz_radio.clicked.connect(lambda: self.clear_all_line_edits())
        tz_radio_group.addButton(self.local_tz_radio)
        tz_radio_group.addButton(self.utc_tz_radio)
        tz_h_box.addWidget(self.local_tz_radio)
        tz_h_box.addWidget(self.utc_tz_radio)
        tz_h_box.addStretch()
        v_box.addLayout(tz_h_box)
        v_box.addWidget(QLabel("只读输入框可左键点击复制值"))

        time_h_box = QHBoxLayout()
        self.time_le.setReadOnly(True)
        time_h_box.addWidget(QLabel("当前时间:"))
        time_h_box.addWidget(self.time_le)
        time_h_box.addStretch()
        v_box.addLayout(time_h_box)

        dt_to_ts_h_box = QHBoxLayout()

        dt_ret_le = SingleClickCopyLineEdit()
        dt_ret_le.setReadOnly(True)
        self.dt_input_le.textChanged.connect(lambda: self.dt_to_ts_set_result(self.dt_input_le, dt_ret_le))
        dt_to_ts_h_box.addWidget(QLabel("时间转时间戳"))
        dt_to_ts_h_box.addWidget(self.dt_input_le)
        dt_to_ts_h_box.addWidget(QLabel(" -> "))
        dt_to_ts_h_box.addWidget(dt_ret_le)

        dt_to_ts_h_box.addStretch()
        v_box.addLayout(dt_to_ts_h_box)

        ts_h_box = QHBoxLayout()
        self.ts_le.setReadOnly(True)
        ts_h_box.addWidget(QLabel("当前时间戳:"))
        ts_h_box.addWidget(self.ts_le)
        ts_h_box.addStretch()
        v_box.addLayout(ts_h_box)

        ts_to_dt_h_box = QHBoxLayout()
        ts_to_dt_input_le = QLineEdit()
        ts_to_dt_le_result = SingleClickCopyLineEdit()
        ts_to_dt_le_result.setReadOnly(True)
        ts_to_dt_input_le.textChanged.connect(lambda: self.ts_to_dt_set_result(ts_to_dt_input_le, ts_to_dt_le_result))
        ts_to_dt_h_box.addWidget(QLabel("时间戳转时间:"))
        ts_to_dt_h_box.addWidget(ts_to_dt_input_le)
        ts_to_dt_h_box.addWidget(QLabel(" -> "))
        ts_to_dt_h_box.addWidget(ts_to_dt_le_result)
        ts_to_dt_h_box.addStretch()
        v_box.addLayout(ts_to_dt_h_box)

        ts_ms_h_box = QHBoxLayout()
        self.ts_ms_le.setReadOnly(True)
        ts_ms_h_box.addWidget(QLabel("时间戳(毫秒):"))
        ts_ms_h_box.addWidget(self.ts_ms_le)
        ts_ms_h_box.addStretch()
        v_box.addLayout(ts_ms_h_box)

        ts_ms_to_dt_h_box = QHBoxLayout()
        ts_ms_to_dt_input_le = QLineEdit()
        ts_ms_to_dt_le_result = SingleClickCopyLineEdit()
        ts_ms_to_dt_le_result.setReadOnly(True)
        ts_ms_to_dt_input_le.textChanged.connect(
            lambda: self.ts_ms_to_dt_set_result(ts_ms_to_dt_input_le, ts_ms_to_dt_le_result)
        )
        ts_ms_to_dt_h_box.addWidget(QLabel("时间戳转时间(毫秒):"))
        ts_ms_to_dt_h_box.addWidget(ts_ms_to_dt_input_le)
        ts_ms_to_dt_h_box.addWidget(QLabel(" -> "))
        ts_ms_to_dt_h_box.addWidget(ts_ms_to_dt_le_result)
        ts_ms_to_dt_h_box.addStretch()
        v_box.addLayout(ts_ms_to_dt_h_box)

        v_box.addStretch()
        self.setLayout(v_box)

    def clear_all_line_edits(self):
        for child_widget in self.findChildren(QLineEdit):
            child_widget.clear()

    def dt_to_ts_set_result(self, dt_le: QLineEdit, result_le: QLineEdit):
        text = dt_le.text()
        if not text:
            return
        try:

            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.get_tz())
            ts = int(dt.timestamp())
            result_le.setText(str(ts))
        except ValueError:
            result_le.setText("value error")

    def ts_to_dt_set_result(self, le_input: QLineEdit, result_le: QLineEdit) -> None:
        text = le_input.text()
        if not text:
            return
        try:
            ts = int(text)
            dt = datetime.fromtimestamp(ts, tz=self.get_tz()).strftime("%Y-%m-%d %H:%M:%S")
            result_le.setText(dt)
        except ValueError as e:
            result_le.setText(str(e))

    def ts_ms_to_dt_set_result(self, le_input: QLineEdit, result_le: QLineEdit):
        text = le_input.text()
        if not text:
            return
        try:
            ts = int(text) // 1000
            dt = datetime.fromtimestamp(ts, tz=self.get_tz()).strftime("%Y-%m-%d %H:%M:%S")
            result_le.setText(dt)
        except ValueError as e:
            result_le.setText(str(e))

    def get_tz(self):
        return self.local_tz if self.local_tz_radio.isChecked() else UTC

    def update_time(self):
        now = datetime.now(self.get_tz())

        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        ts = str(int(now.timestamp()))
        ts_ms = str(int(now.timestamp() * 1000))

        self.time_le.setText(time_str)
        self.ts_le.setText(ts)
        self.ts_ms_le.setText(ts_ms)

    def set_value(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(50)

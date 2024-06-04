import time
from datetime import UTC, datetime

import croniter
from croniter import CroniterBadCronError
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from . import BaseWidget


class CronWidget(BaseWidget):
    name = "cron"

    def __init__(self):
        super().__init__()
        self.cron_ret_te = QTextEdit()
        self.cron_le_input = QLineEdit()
        self.time_le = QLineEdit()
        self.local_tz = datetime.fromtimestamp(time.time()).astimezone().tzinfo
        self.set_ui()
        self.set_time()

    def set_ui(self):
        v_box = QVBoxLayout()

        tz_h_box = QHBoxLayout()
        tz_radio_group = QButtonGroup()
        self.local_tz_radio = QRadioButton("local")
        self.local_tz_radio.click()
        self.local_tz_radio.clicked.connect(self.cal_cron)
        self.utc_tz_radio = QRadioButton("utc+0")
        self.utc_tz_radio.clicked.connect(self.cal_cron)
        tz_radio_group.addButton(self.local_tz_radio)
        tz_radio_group.addButton(self.utc_tz_radio)
        tz_h_box.addWidget(self.local_tz_radio)
        tz_h_box.addWidget(self.utc_tz_radio)
        tz_h_box.addStretch()
        v_box.addLayout(tz_h_box)

        cal_v_box = QVBoxLayout()
        cal_v_box.addWidget(self.time_le)
        self.time_le.setFixedWidth(300)
        self.time_le.setReadOnly(True)
        self.cron_le_input.setFixedWidth(300)
        self.cron_le_input.setPlaceholderText("input cron express")
        self.cron_le_input.textChanged.connect(self.cal_cron)
        cal_v_box.addWidget(self.cron_le_input)
        # self.cron_ret_te.setFixedSize(600, 600)
        self.cron_ret_te.setReadOnly(True)
        cal_v_box.addWidget(self.cron_ret_te)
        v_box.addLayout(cal_v_box)

        self.setLayout(v_box)

    def get_tz(self):
        return self.local_tz if self.local_tz_radio.isChecked() else UTC

    def cal_cron(self):
        cron_expression = self.cron_le_input.text()
        if not cron_expression:
            return
        base = datetime.now(self.get_tz())

        try:
            cron = croniter.croniter(cron_expression, base)
        except CroniterBadCronError:
            self.cron_ret_te.setPlainText("wrong cron expression")
            return
        ret = ""
        for i in range(30):
            ret += f"{cron.get_next(datetime).strftime('%Y-%m-%d %H:%M:%S')}\n"
        self.cron_ret_te.setPlainText(ret)

    def set_time_le(self):
        now = datetime.now(self.get_tz())
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.time_le.setText(time_str)

    def set_time(self):
        timer = QTimer(self)
        timer.timeout.connect(self.set_time_le)
        timer.start(50)

    def switch_in(self):
        self.cron_le_input.setFocus()

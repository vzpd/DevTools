from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter

from app.utils.time_tools import local_timezone


class TimezoneSelector(QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.addItems(
            [
                "本地时区",
                "UTC",
                "Asia/Shanghai",
                "Asia/Tokyo",
                "America/New_York",
                "America/Los_Angeles",
                "Europe/London",
                "Europe/Berlin",
            ]
        )
        completer = QCompleter(["本地时区"] + sorted(available_timezones()), self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)
        self.setMinimumWidth(170)
        self.setToolTip("输入 IANA 时区名称，例如 Asia/Shanghai")

    def timezone(self):
        name = self.currentText().strip()
        if name == "本地时区":
            return local_timezone()
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("无效时区，请使用 UTC 或 Asia/Shanghai 等 IANA 名称") from None

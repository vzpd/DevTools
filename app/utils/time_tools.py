import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def local_timezone():
    name = os.environ.get("TZ", "").removeprefix(":")
    if not name:
        path = str(Path("/etc/localtime").resolve())
        if "zoneinfo/" in path:
            name = path.split("zoneinfo/", 1)[1]
    if name:
        try:
            return ZoneInfo(name)
        except (KeyError, ValueError):
            pass
    return datetime.now().astimezone().tzinfo


def parse_datetime(text, zone):
    from datetime import UTC

    value = datetime.fromisoformat(text)
    if value.tzinfo is not None:
        return value
    first = value.replace(tzinfo=zone, fold=0)
    second = value.replace(tzinfo=zone, fold=1)
    if first.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != value:
        raise ValueError("该时间因夏令时切换而不存在，请明确输入 UTC 偏移")
    if first.utcoffset() != second.utcoffset():
        raise ValueError("该时间存在两种夏令时偏移，请在输入中明确 +HH:mm / -HH:mm")
    return first

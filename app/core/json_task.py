from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QRunnable, Signal

from app.utils.json_tools import (
    format_json,
    json_fold_regions,
    map_json_positions,
    parse_json,
)


@dataclass(frozen=True)
class JsonRequest:
    source: str
    revision: int
    indent: int | None
    ensure_ascii: bool
    positions: tuple[int, int]
    locate: bool = False


@dataclass
class JsonResult:
    request: JsonRequest
    text: str | None = None
    folds: dict[int, int] = field(default_factory=dict)
    positions: tuple[int, int] = (0, 0)
    error: Exception | None = None


class JsonTaskSignals(QObject):
    finished = Signal(object)


class JsonTask(QRunnable):
    def __init__(self, request):
        super().__init__()
        self.request = request
        self.signals = JsonTaskSignals()

    def run(self):
        result = JsonResult(self.request)
        try:
            source = self.request.source
            if self.request.indent is None:
                parse_json(source)
            else:
                result.text = format_json(source, self.request.indent, self.request.ensure_ascii)
                if result.text != source:
                    result.positions = map_json_positions(source, result.text, self.request.positions)
            result.folds = json_fold_regions(result.text if result.text is not None else source)
        except Exception as error:
            result.error = error
        self.signals.finished.emit(result)

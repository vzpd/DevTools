from . import AppException


class WidgetNoNameException(AppException):
    def __init__(self, code: int = 10001, message: str = ""):
        super().__init__(code, message)


class WidgetNameRepeatException(AppException):
    def __init__(self, code: int = 10002, message: str = ""):
        super().__init__(code, message)

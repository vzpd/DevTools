from PySide6.QtWidgets import QWidget

from app.exceptions.run_exception import (
    WidgetNameRepeatException,
    WidgetNoNameException,
)

widget_names = []


class CustomWidgetMetaClass(QWidget.__class__):

    def __call__(self, *args, **kwargs):
        if not hasattr(self, "name"):
            raise WidgetNoNameException()
        widget_name = getattr(self, "name")
        if widget_name in widget_names:
            raise WidgetNameRepeatException
        widget_names.append(widget_name)
        return super().__call__(*args, **kwargs)


class BaseWidget(QWidget, metaclass=CustomWidgetMetaClass):
    def __init__(self):
        super().__init__()

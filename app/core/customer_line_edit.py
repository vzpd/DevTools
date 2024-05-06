import pyperclip
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLineEdit

from app.core.toast import Toast


class SingleClickCopyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.isReadOnly():
            pyperclip.copy(self.text())
            Toast("copy success", parent=self).show()

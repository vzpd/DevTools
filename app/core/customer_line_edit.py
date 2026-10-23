from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QLineEdit

from app.core.toast import Toast


class SingleClickCopyLineEdit(QLineEdit):
    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self.isReadOnly():
            QApplication.clipboard().setText(self.text())
            Toast("复制成功", parent=self).show()

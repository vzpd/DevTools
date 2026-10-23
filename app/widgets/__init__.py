from PySide6.QtWidgets import QWidget


class BaseWidget(QWidget):
    def switch_in(self):
        self.setFocus()

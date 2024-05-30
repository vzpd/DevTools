from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Toast(QWidget):
    def __init__(self, text, text_color="white", parent=None, show_time: int = 1000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.8)

        self.layout = QVBoxLayout(self)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 20))
        self.label.setStyleSheet(f"color: {text_color};")
        self.layout.addWidget(self.label)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 0); border-radius: 10px;")

        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.setInterval(show_time)
        self.auto_close_timer.timeout.connect(self.close)

    def show(self):
        super().show()
        self.auto_close_timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0, 0, 0, 127)))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

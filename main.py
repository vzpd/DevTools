import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
import qdarkstyle
from app.home import HomeWindow
from qdarkstyle.light.palette import LightPalette

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle._load_stylesheet(qt_api="pyside6", palette=LightPalette))

    font = QFont("Courier New")
    app.setFont(font)

    home_window = HomeWindow()
    home_window.show()
    app.applicationStateChanged.connect(home_window.onApplicationStateChanged)

    sys.exit(app.exec())

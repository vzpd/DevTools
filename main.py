import sys
from PySide6.QtWidgets import QApplication
import qdarkstyle
from app.home import HomeWindow
from qdarkstyle.light.palette import LightPalette

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle._load_stylesheet(qt_api='pyside6', palette=LightPalette))
    home_window = HomeWindow()
    home_window.show()

    sys.exit(app.exec())

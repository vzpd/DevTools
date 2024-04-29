import sys
from PySide6.QtWidgets import QApplication

from app.home import HomeWindow

if __name__ == "__main__":
    app = QApplication([])
    home_window = HomeWindow()
    home_window.show()

    sys.exit(app.exec())

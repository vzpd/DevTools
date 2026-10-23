import sys

from PySide6.QtWidgets import QApplication

from app.core.theme import apply_theme
from app.home import HomeWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DevTools")
    app.setOrganizationName("DevTools")
    apply_theme(app)
    home_window = HomeWindow()
    home_window.show_home()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.utils.static import get_static_file
from app.widgets.calculate_widget import CalculateWidget
from app.widgets.cron_widget import CronWidget
from app.widgets.json_widget import JsonWidget
from app.widgets.jwt_widget import JwtWidget
from app.widgets.timestamp_widget import TimestampWidget


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stacked_layout = None
        self.tabs = [JsonWidget(), TimestampWidget(), CronWidget(), CalculateWidget(), JwtWidget()]
        self.tab_dict = {tab.name: tab for tab in self.tabs}
        self.set_ui()
        self.tray_icon = QSystemTrayIcon(self)
        self.set_toolbar()

    def set_ui(self):
        vbox_layout = QVBoxLayout()

        stacked_layout = QStackedLayout()
        for tab in self.tabs:
            stacked_layout.addWidget(tab)
        self.stacked_layout = stacked_layout

        navigate_box_layout = QHBoxLayout()
        for tab in self.tabs:
            button = QPushButton(tab.name)
            button.clicked.connect(self.switch_tab)
            navigate_box_layout.addWidget(button)

        vbox_layout.addLayout(navigate_box_layout)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        vbox_layout.addWidget(separator)
        vbox_layout.addLayout(stacked_layout)

        central_widget = QWidget()
        central_widget.setLayout(vbox_layout)

        self.setCentralWidget(central_widget)
        self.resize(1200, 600)

    def switch_tab(self):
        button = self.sender()
        tab = self.tab_dict[button.text()]
        self.stacked_layout.setCurrentWidget(tab)
        tab.switch_in()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def set_toolbar(self):
        icon = get_static_file("assets", "toolbar", "icon.jpeg")
        self.tray_icon.setIcon(QIcon(icon))
        self.tray_icon.activated.connect(self.show_home)
        self.tray_icon.show()

    def exit_app(self):
        self.tray_icon.hide()
        QApplication.instance().quit()

    def show_home(self):
        current_screen = QApplication.primaryScreen()

        screen_geometry = current_screen.geometry()
        self.move(screen_geometry.center() - self.rect().center())
        self.show()
        self.raise_()

    def onApplicationStateChanged(self, state):
        if state == Qt.ApplicationActive:
            self.show_home()

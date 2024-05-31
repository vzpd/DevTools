from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget, QSystemTrayIcon, QMenu, QApplication,
)

from app.utils.static import get_static_file
from app.widgets.calculate_widget import CalculateWidget
from app.widgets.cron_widget import CronWidget
from app.widgets.json_widget import JsonWidget
from app.widgets.timestamp_widget import TimestampWidget


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stacked_layout = None
        self.tabs = [JsonWidget(), TimestampWidget(), CronWidget(), CalculateWidget()]
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
        self.resize(700, 600)

    def switch_tab(self):
        button = self.sender()
        tab = self.tab_dict[button.text()]
        self.stacked_layout.setCurrentWidget(tab)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def set_toolbar(self):
        icon = get_static_file("assets", "toolbar", "icon.jpeg")
        self.tray_icon.setIcon(QIcon(icon))

        tray_menu = QMenu()
        restore_action = QAction("显示窗口", self)
        quit_action = QAction("退出", self)

        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        restore_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.exit_app)

        self.tray_icon.show()

    def exit_app(self):
        self.tray_icon.hide()
        QApplication.instance().quit()

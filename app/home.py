from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from app.widgets.json_widget import JsonWidget
from app.widgets.timestamp_widget import TimestampWidget


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stacked_layout = None
        self.tabs = [TimestampWidget(), JsonWidget()]
        self.tab_dict = {tab.name: tab for tab in self.tabs}
        self.set_ui()

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
        vbox_layout.addLayout(stacked_layout)

        central_widget = QWidget()
        central_widget.setLayout(vbox_layout)

        self.setCentralWidget(central_widget)
        self.resize(700, 600)

    def switch_tab(self):
        button = self.sender()
        tab = self.tab_dict[button.text()]
        self.stacked_layout.setCurrentWidget(tab)

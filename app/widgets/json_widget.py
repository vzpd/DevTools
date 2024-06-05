import json
import numbers
import re
from json import JSONDecodeError
from typing import AnyStr

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from app.core.toast import Toast
from app.widgets import BaseWidget


class JsonWidget(BaseWidget):
    name = "json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Tree Viewer")
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.json_pte = QPlainTextEdit()
        self.set_ui()

    def set_ui(self):

        expand_button = QPushButton("Expand All")
        expand_button.clicked.connect(self.expand_all)
        collapse_button = QPushButton("Collapse All")
        collapse_button.clicked.connect(self.collapse_all)

        parse_layout = QVBoxLayout()

        parse_layout.addWidget(expand_button)
        parse_layout.addWidget(collapse_button)
        regex_input = QLineEdit()
        regex_input.setPlaceholderText("input regex")
        regex_input.textChanged.connect(self.match_regex)
        parse_layout.addWidget(regex_input)
        parse_layout.addWidget(self.tree_view)

        input_layout = QVBoxLayout()

        self.json_pte.setFixedWidth(300)
        self.json_pte.setPlaceholderText("input json data")
        self.json_pte.textChanged.connect(lambda: self.populate_tree(self.json_pte.toPlainText()))
        format_button = QPushButton("format json")
        input_layout.addWidget(format_button)
        format_button.clicked.connect(lambda: self.format_json_input(self.json_pte.toPlainText()))
        input_layout.addWidget(self.json_pte)

        h_box = QHBoxLayout()
        h_box.addLayout(input_layout)
        h_box.addLayout(parse_layout)

        self.setLayout(h_box)

    def populate_tree(self, json_data: str):
        self.model.clear()
        if not json_data:
            return
        try:
            json_obj = json.loads(json_data)
            self.add_json_to_model(self.model.invisibleRootItem(), json_obj)
            self.tree_view.expandAll()
        except JSONDecodeError as e:
            self.model.invisibleRootItem().appendRow(QStandardItem(f"{e}"))

    def add_json_to_model(self, parent, obj, name=None):
        def get_obj_str(obj_value):
            if isinstance(obj_value, numbers.Number):
                return f"{obj_value}"
            else:
                return f'"{obj_value}"'

        if isinstance(obj, dict):
            start_item = QStandardItem(f'"{name}": {{') if name else QStandardItem("{")

            parent.appendRow(start_item)
            for key, value in obj.items():
                self.add_json_to_model(start_item, value, key)
            end_item = QStandardItem("}")
            parent.appendRow(end_item)
        elif isinstance(obj, list):
            start_item = QStandardItem(f'"{name}": [') if name else QStandardItem("[")
            parent.appendRow(start_item)
            for _, value in enumerate(obj):
                self.add_json_to_model(start_item, value)
            end_item = QStandardItem("]")
            parent.appendRow(end_item)
        else:
            item = QStandardItem(f'"{name}": {get_obj_str(obj)}') if name else QStandardItem(get_obj_str(obj))
            parent.appendRow(item)

    def expand_all(self):
        self.tree_view.expandAll()

    def collapse_all(self):
        self.tree_view.collapseAll()

    def format_json_input(self, json_data: str):
        try:
            json_obj = json.loads(json_data)
            format_json = json.dumps(json_obj, indent=4)
            self.json_pte.setPlainText(format_json)
            Toast("format success!", parent=self).show()
        except JSONDecodeError:
            Toast("json error!", parent=self, text_color="red").show()

    def match_regex(self, regex_str: str):
        try:
            regex = re.compile(regex_str, re.IGNORECASE) if regex_str else None
        except re.error:
            regex = None

        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            self.highlight_item(item, regex)

    def highlight_item(self, item, regex: re.Pattern[AnyStr]):
        if regex and regex.search(item.text()):
            item.setBackground(QBrush(Qt.green))
        else:
            item.setBackground(QBrush(Qt.transparent))
        for i in range(item.rowCount()):
            child = item.child(i)
            self.highlight_item(child, regex)

    def switch_in(self):
        self.json_pte.setFocus()

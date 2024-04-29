from json import JSONDecodeError
import json
from PySide6.QtWidgets import QTreeView, QVBoxLayout, QPushButton, QPlainTextEdit, \
    QHBoxLayout
from PySide6.QtGui import QStandardItem, QStandardItemModel

from app.widgets import BaseWidget


class JsonWidget(BaseWidget):
    name = 'json'

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Tree Viewer")

        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)

        expand_button = QPushButton("Expand All")
        expand_button.clicked.connect(self.expand_all)
        collapse_button = QPushButton("Collapse All")
        collapse_button.clicked.connect(self.collapse_all)

        parse_layout = QVBoxLayout()
        parse_layout.addWidget(expand_button)
        parse_layout.addWidget(collapse_button)
        parse_layout.addWidget(self.tree_view)

        input_layout = QVBoxLayout()
        json_pte = QPlainTextEdit()

        json_pte.setPlaceholderText('input json data')
        json_pte.textChanged.connect(lambda: self.populate_tree(json_pte.toPlainText()))
        input_layout.addWidget(json_pte)

        h_box = QHBoxLayout()
        h_box.addLayout(input_layout)
        h_box.addLayout(parse_layout)

        self.setLayout(h_box)

    def populate_tree(self, json_data: str):
        self.model.clear()
        try:
            json_obj = json.loads(json_data)
            self.add_json_to_model(json_obj, self.model.invisibleRootItem(), "")
            self.tree_view.expandAll()
        except JSONDecodeError as e:
            self.model.invisibleRootItem().appendRow(QStandardItem(f"{e}"))

    def add_json_to_model(self, json_obj, parent_item, name):
        if isinstance(json_obj, dict):
            if name:
                item = QStandardItem(f"{name}: {{")
            else:
                item = QStandardItem("{")
            parent_item.appendRow(item)
            for key, value in json_obj.items():
                self.add_json_to_model(value, item, key)
            item2 = QStandardItem("}")
            parent_item.appendRow(item2)
        elif isinstance(json_obj, list):
            if name:
                item = QStandardItem(f"{name}: [{len(json_obj)}]")
            else:
                item = QStandardItem(f"[{len(json_obj)}]")
            parent_item.appendRow(item)
            for i, value in enumerate(json_obj):
                label = f"[{i}]"
                self.add_json_to_model(value, item, label)
        else:
            if name:
                parent_item.appendRow([QStandardItem(f"{name}: {json_obj}")])
            else:
                parent_item.appendRow([QStandardItem(str(json_obj))])

    def expand_all(self):
        self.tree_view.expandAll()

    def collapse_all(self):
        self.tree_view.collapseAll()

import re
from string import Template

from PySide6.QtGui import QColor, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication, QPushButton, QStyleFactory

LIGHT = {
    "window": "#f5f5f7",
    "sidebar": "#ededf0",
    "surface": "#ffffff",
    "alternate": "#f9f9fb",
    "text": "#1d1d1f",
    "secondary": "#6e6e73",
    "line": "#dedee3",
    "hover": "#e4e4e9",
    "accent": "#007aff",
    "selection": "#d6e8ff",
    "success": "#24814b",
    "error": "#c93434",
}
DARK = {
    "window": "#202022",
    "sidebar": "#29292c",
    "surface": "#1c1c1e",
    "alternate": "#262628",
    "text": "#f5f5f7",
    "secondary": "#a1a1a6",
    "line": "#424245",
    "hover": "#3a3a3c",
    "accent": "#0a84ff",
    "selection": "#263f61",
    "success": "#63c981",
    "error": "#ff8d88",
}
STYLE = Template(
    """
QWidget { color: $text; font-size: 13px; font-weight: 400; }
QMainWindow, QWidget#workspace { background: $window; }
QFrame#sidebar { background: $sidebar; border-right: 1px solid $line; }
QLabel#brand { font-size: 15px; font-weight: 600; }
QLabel#pageTitle { font-size: 22px; font-weight: 600; }
QLabel#muted, QLabel#sidebarSection { color: $secondary; font-size: 12px; }
QLabel#sidebarSection { font-weight: 600; padding: 8px 8px 0; }
QLabel#sectionTitle { font-size: 12px; font-weight: 600; color: $secondary; }
QLabel#editorInfo { color: $secondary; font-size: 11px; padding: 2px; }
QListWidget#navigation { background: transparent; border: none; outline: none; }
QListWidget#navigation::item { padding: 8px 10px; margin: 2px 0; border-radius: 7px; }
QListWidget#navigation::item:selected { background: $accent; color: #ffffff; }
QListWidget#navigation::item:hover:!selected { background: $hover; }
QGroupBox { background: $surface; border: 1px solid $line; border-radius: 10px;
    margin-top: 15px; padding: 18px 14px 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QPlainTextEdit, QTextEdit { background: $surface; border: 1px solid $line;
    border-radius: 8px; padding: 8px; selection-background-color: $selection; selection-color: $text; }
QPlainTextEdit:focus, QTextEdit:focus { border-color: $line; }
QLineEdit, QComboBox, QSpinBox, QDateTimeEdit { background: $surface; border: 1px solid $line;
    border-radius: 6px; padding: 5px 7px; min-height: 18px;
    selection-background-color: $selection; selection-color: $text; }
QLineEdit:focus { border-color: $accent; }
QLineEdit:read-only { background: $alternate; }
QLineEdit#toolSearch { background: $hover; border: none; padding: 7px 9px; border-radius: 7px; }
QPushButton { background: $surface; border: 1px solid $line; border-radius: 6px;
    padding: 4px 12px; min-height: 19px; }
QPushButton:hover { background: $alternate; }
QPushButton:pressed { background: $hover; }
QPushButton:disabled { color: $secondary; background: $window; }
QPushButton#primary { background: $accent; border-color: $accent; color: #ffffff; }
QPushButton#primary:disabled { background: $hover; border-color: $line; color: $secondary; }
QPushButton#editorCopy, QToolButton { background: transparent; border: none;
    border-radius: 5px; padding: 4px 7px; min-height: 18px; }
QPushButton#editorCopy:hover, QToolButton:hover { background: $hover; }
QPushButton#editorCopy:disabled { color: $secondary; }
QToolButton::menu-indicator { image: none; width: 0px; }
QTableWidget, QTreeView { background: $surface; alternate-background-color: $alternate;
    border: 1px solid $line; border-radius: 8px; gridline-color: $line; }
QHeaderView::section { background: $alternate; color: $secondary; border: none; padding: 8px; }
QSplitter::handle { background: $window; width: 8px; height: 8px; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: $hover; padding: 5px 12px; border-radius: 6px; margin: 2px; }
QTabBar::tab:selected { background: $surface; }
QMenu { background: $surface; border: 1px solid $line; border-radius: 8px; padding: 5px; }
QMenu::item { padding: 6px 20px; border-radius: 4px; }
QMenu::item:selected { background: $accent; color: #ffffff; }
QMenu::separator { height: 1px; background: $line; margin: 4px; }
QLabel[state="error"] { color: $error; }
QLabel[state="success"] { color: $success; }
QLabel[state="neutral"] { color: $secondary; }
QToolTip { background: $surface; color: $text; border: 1px solid $line; padding: 5px; }
"""
)


def apply_theme(app, dark=False):
    native = "macOS" if "macOS" in QStyleFactory.keys() and app.platformName() == "cocoa" else "Fusion"
    app.setStyle(native)
    font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    font.setPointSize(12)
    app.setFont(font)
    colors = DARK if dark else LIGHT
    palette = app.style().standardPalette()
    for role, key in (
        (QPalette.Window, "window"),
        (QPalette.Base, "surface"),
        (QPalette.AlternateBase, "alternate"),
        (QPalette.Text, "text"),
        (QPalette.WindowText, "text"),
        (QPalette.Button, "surface"),
        (QPalette.ButtonText, "text"),
        (QPalette.Highlight, "accent"),
        (QPalette.ToolTipBase, "surface"),
        (QPalette.ToolTipText, "text"),
        (QPalette.PlaceholderText, "secondary"),
    ):
        palette.setColor(role, QColor(colors[key]))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    style = STYLE.substitute(colors)
    if native == "macOS":
        controls = r"Q(?:LineEdit|ComboBox|SpinBox|DateTimeEdit|PushButton|ToolButton)"
        style = re.sub(
            r"([^{}]+)\{[^{}]*\}", lambda match: "" if re.search(controls, match.group(1)) else match.group(), style
        )
        style = re.sub(r"(?m)^QWidget\s*\{[^}]*\}", "", style)
        style += Template(
            """
QLineEdit, QComboBox, QSpinBox, QDateTimeEdit { min-height: 24px; }
QToolButton::menu-indicator { image: none; width: 0px; }
QLineEdit#toolSearch { border: none; border-radius: 6px; padding: 4px 8px; background: $hover; }
"""
        ).substitute(colors)
    app.setStyleSheet(style)
    if native == "macOS":
        for widget in QApplication.allWidgets():
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(26)

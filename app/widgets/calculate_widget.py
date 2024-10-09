import code
import contextlib
import io
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QTextEdit, QVBoxLayout

from . import BaseWidget


class CommandHistoryManager:
    def __init__(self, length=50):
        self.commands: List[str] = []
        self.length = length
        self.cursor = 0

    def add_command(self, command):

        if self.commands and command == self.commands[0]:
            return
        else:
            self.commands.append(command)

        if len(self.commands) > self.length:
            self.commands.pop(0)

        self.cursor = len(self.commands) - 1

    def check_cursor(self):
        if not self.commands:
            return 0

        if self.cursor < 0:
            self.cursor = 0
        if self.cursor >= len(self.commands):
            self.cursor = len(self.commands) - 1

        return self.cursor

    def get_next_command(self) -> None | str:

        cursor = self.check_cursor()
        command = None
        if self.commands:
            command = self.commands[cursor]

        self.cursor += 1
        return command

    def get_previous_command(self):
        cursor = self.check_cursor()
        command = None
        if self.commands:
            command = self.commands[cursor]
        self.cursor -= 1
        return command


class CommandLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs) -> None:
        self.command_manager = CommandHistoryManager()
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Up:
            command = self.command_manager.get_previous_command()
            command and self.setText(command)
        elif key == Qt.Key_Down:
            command = self.command_manager.get_next_command()
            command and self.setText(command)
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            self.command_manager.add_command(self.text())
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class CalculateWidget(BaseWidget):
    name = "calculate"

    def __init__(self):
        super().__init__()
        self.command_list = []
        self.ret_te = QTextEdit()
        self.code_le = CommandLineEdit()
        self.interpreter = code.InteractiveInterpreter()
        self.namespace = {}
        self.set_ui()

    def set_ui(self):

        v_box = QVBoxLayout()

        self.ret_te.setReadOnly(True)
        v_box.addWidget(self.ret_te)

        self.code_le.setPlaceholderText("input code")
        self.code_le.returnPressed.connect(self.execute_command)
        v_box.addWidget(self.code_le)

        self.setLayout(v_box)

    def execute_command(self):
        command = self.code_le.text()
        self.code_le.clear()

        with contextlib.redirect_stdout(io.StringIO()) as f_out, contextlib.redirect_stderr(io.StringIO()) as f_err:
            self.interpreter.runsource(command)
            output = f_out.getvalue() + f_err.getvalue()

        self.ret_te.append(f">>> {command}\n{output}")

    def switch_in(self):
        self.code_le.setFocus()

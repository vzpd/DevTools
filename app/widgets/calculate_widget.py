import code
import contextlib
import io

from PySide6.QtWidgets import QLineEdit, QTextEdit, QVBoxLayout

from . import BaseWidget


class CalculateWidget(BaseWidget):
    name = "calculate"

    def __init__(self):
        super().__init__()
        self.ret_te = QTextEdit()
        self.code_le = QLineEdit()
        self.interpreter = code.InteractiveInterpreter()
        self.namespace = {}
        self.buffer = ""
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
            more = self.interpreter.runsource(command)
            if more:
                self.buffer = command + "\n"
            else:
                self.buffer = ""
            output = f_out.getvalue() + f_err.getvalue()

        self.ret_te.append(f">>> {command}\n{output}")

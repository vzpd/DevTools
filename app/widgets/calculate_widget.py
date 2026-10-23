import codecs
import os
import shutil
import sys
import time
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
)

from app.core.components import EditorPanel, PythonHighlighter, StatusLabel
from app.widgets import BaseWidget


class CalculateWidget(BaseWidget):
    name = "calculate"
    output_limit = 1_000_000

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.run_button = QPushButton("运行代码")
        self.run_button.setObjectName("primary")
        self.run_button.setDefault(True)
        self.run_button.setShortcut("Ctrl+Return")
        self.run_button.setToolTip("运行 · Ctrl+Enter")
        self.run_button.clicked.connect(self.execute_command)
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(lambda: self.stop("已停止运行"))
        toolbar.addWidget(self.run_button)
        toolbar.addWidget(self.stop_button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        hint = QLabel("独立进程执行，变量不跨运行保留；支持末尾表达式。运行配置在代码编辑器的 ⋯ 菜单中。")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        source = EditorPanel("Python 代码", "输入 Python 代码…")
        output = EditorPanel("运行结果", "输出与错误会显示在这里", read_only=True)
        self.code_le = source.editor
        self.code_le.python_mode = True
        self.code_le.highlighter = PythonHighlighter(self.code_le.document())
        source.menu.addSeparator()
        source.menu.addAction("运行配置…", self.configure_run)
        self.interpreter_path = ""
        self.working_directory = str(Path.home() if getattr(sys, "frozen", False) else Path.cwd())
        self.timeout_seconds = 30
        self.started_at = 0
        self.ret_te = output.editor
        split = QSplitter(Qt.Vertical)
        split.addWidget(source)
        split.addWidget(output)
        split.setChildrenCollapsible(False)
        split.setSizes([300, 250])
        layout.addWidget(split, 1)
        self.status = StatusLabel("就绪 · 执行的代码具有当前用户权限")
        layout.addWidget(self.status)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.setInterval(30_000)
        self.timeout.timeout.connect(lambda: self.stop(f"运行超过 {self.timeout_seconds} 秒，已停止"))
        self.received = 0
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.stop_reason = None

    def execute_command(self):
        if self.process.state() != QProcess.NotRunning or not self.code_le.toPlainText().strip():
            return
        interpreter = self.interpreter_path or (
            sys.executable if not getattr(sys, "frozen", False) else shutil.which("python3")
        )
        if not interpreter:
            self.status.set_status("未找到 Python 3，请先安装并加入 PATH", "error")
            return
        self.ret_te.clear()
        self.received = 0
        self.decoder.reset()
        self.stop_reason = None
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONIOENCODING", "utf-8")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(self.working_directory)
        runner = (
            "import ast, sys\n"
            "source = sys.stdin.read()\n"
            "tree = ast.parse(source, filename='<DevTools>')\n"
            "scope = {'__name__': '__main__'}\n"
            "if tree.body and isinstance(tree.body[-1], ast.Expr):\n"
            "    last = tree.body.pop()\n"
            "    exec(compile(tree, '<DevTools>', 'exec'), scope)\n"
            "    result = eval(compile(ast.Expression(last.value), '<DevTools>', 'eval'), scope)\n"
            "    if result is not None: print(repr(result))\n"
            "else:\n"
            "    exec(compile(tree, '<DevTools>', 'exec'), scope)\n"
        )
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.set_status(f"运行中 · {interpreter}")
        self.process.start(interpreter, ["-u", "-c", runner])
        self.process.write(self.code_le.toPlainText().encode("utf-8"))
        self.process.closeWriteChannel()
        self.started_at = time.monotonic()
        self.timeout.start()

    def read_output(self):
        data = bytes(self.process.readAllStandardOutput())
        remaining = max(0, self.output_limit - self.received)
        self.received += len(data)
        text = self.decoder.decode(data[:remaining])
        if text:
            cursor = self.ret_te.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(text)
            self.ret_te.setTextCursor(cursor)
        if self.received > self.output_limit and self.stop_reason is None:
            self.stop("输出超过 1 MB，已停止；结果已截断")

    def stop(self, reason):
        if self.process.state() != QProcess.NotRunning:
            self.stop_reason = reason
            self.process.kill()

    def finished(self, exit_code, exit_status):
        self.read_output()
        self.timeout.stop()
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.stop_reason:
            self.status.set_status(self.stop_reason, "error")
        elif exit_status == QProcess.NormalExit and exit_code == 0:
            self.status.set_status(f"运行完成 · {time.monotonic() - self.started_at:.3f} 秒 · 退出码 0", "success")
        else:
            self.status.set_status(f"运行失败 · 退出码 {exit_code}", "error")

    def process_error(self, error):
        if error == QProcess.FailedToStart:
            self.timeout.stop()
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status.set_status("无法启动 Python 进程", "error")

    def configure_run(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Python 运行配置")
        dialog.resize(560, 200)
        layout = QFormLayout(dialog)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        interpreter = QLineEdit(self.interpreter_path)
        interpreter.setPlaceholderText("留空使用默认 Python 3；可填虚拟环境解释器的绝对路径")
        directory = QLineEdit(self.working_directory)
        timeout = QSpinBox()
        timeout.setRange(1, 600)
        timeout.setValue(self.timeout_seconds)
        timeout.setSuffix(" 秒")
        layout.addRow("解释器", interpreter)
        layout.addRow("工作目录", directory)
        layout.addRow("运行时限", timeout)
        status = StatusLabel()
        layout.addRow(status)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        buttons.rejected.connect(dialog.reject)

        def accept():
            candidate = interpreter.text().strip()
            path = Path(candidate).expanduser() if candidate else None
            folder = Path(directory.text()).expanduser()
            if path is not None and (not path.is_file() or not os.access(path, os.X_OK)):
                status.set_status("解释器必须指向可执行文件", "error")
                return
            if not folder.is_dir():
                status.set_status("工作目录不存在", "error")
                return
            self.interpreter_path = str(path.resolve()) if path else ""
            self.working_directory = str(folder.resolve())
            self.timeout_seconds = timeout.value()
            self.timeout.setInterval(self.timeout_seconds * 1000)
            dialog.accept()

        buttons.accepted.connect(accept)
        dialog.exec()

    def shutdown(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)

    def switch_in(self):
        self.code_le.setFocus()

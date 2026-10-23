from PySide6.QtCore import QEvent, QSettings, QSignalBlocker, QSize, Qt
from PySide6.QtGui import QAction, QCursor, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QStackedWidget,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.components import CodeEditor, EditorPanel, StatusLabel
from app.core.global_hotkey import GlobalHotkey
from app.core.icons import system_icon
from app.core.macos_window import (
    bring_to_front,
    configure_panel,
    is_window_active,
    prepare_panel,
    set_native_appearance,
)
from app.core.theme import apply_theme
from app.utils.static import get_static_file
from app.widgets.calculate_widget import CalculateWidget
from app.widgets.codec_widget import CodecWidget
from app.widgets.cron_widget import CronWidget
from app.widgets.diff_widget import DiffWidget
from app.widgets.hash_widget import HashWidget
from app.widgets.json_widget import JsonWidget
from app.widgets.jwt_widget import JwtWidget
from app.widgets.timestamp_widget import TimestampWidget

TOOLS = (
    ("JSON", "粘贴即校验、自动格式化，直接在编辑器内折叠", "curlybraces", JsonWidget),
    ("时间戳转换", "在 Unix 时间戳与日期之间转换，明确时区与单位", "clock", TimestampWidget),
    ("Cron 表达式", "编辑调度规则，预览未来执行时间", "calendar", CronWidget),
    ("Python 控制台", "编写多行 Python，查看输出并控制运行", "terminal", CalculateWidget),
    ("JWT 解码", "查看内容，按指定算法验证签名与声明", "key", JwtWidget),
    ("编码转换", "Base64 / URL / HTML / Hex / JSON 字符串", "arrow.left.arrow.right", CodecWidget),
    ("文本对比", "按行标出变更，生成可复制的 Unified diff", "doc.on.doc", DiffWidget),
    ("摘要与 UUID", "计算文本摘要，生成随机 UUID v4", "number", HashWidget),
)


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        prepare_panel(self)
        self.setWindowTitle("DevTools")
        self.setMinimumSize(980, 700)
        self.resize(1280, 820)
        self.tabs = [tool[3]() for tool in TOOLS]
        self.tab_dict = {tab.name: tab for tab in self.tabs}
        self.tray_icon = QSystemTrayIcon(self)
        self.settings = QSettings()
        self.set_ui()
        self.set_toolbar()
        self.hotkey = GlobalHotkey(self)
        self.hotkey.activated.connect(self.toggle_visibility, Qt.QueuedConnection)
        self.hotkey_status.set_status("启动后可用全局快捷键唤起")
        self.hotkey_started = False
        QApplication.instance().installEventFilter(self)
        QApplication.instance().aboutToQuit.connect(self.hotkey.close)
        QApplication.instance().aboutToQuit.connect(self.tab_dict["calculate"].shutdown)

    def set_ui(self):
        central = QWidget()
        central.setObjectName("workspace")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(196)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 18, 12, 16)
        brand = QLabel("DevTools")
        brand.setObjectName("brand")
        side.addWidget(brand)

        side.addSpacing(10)
        self.tool_search = QLineEdit()
        self.tool_search.setPlaceholderText("搜索")
        self.tool_search.setObjectName("toolSearch")
        self.tool_search.setClearButtonEnabled(True)
        self.tool_search.addAction(system_icon("magnifyingglass"), QLineEdit.LeadingPosition)
        self.tool_search.textChanged.connect(self.filter_tools)
        side.addWidget(self.tool_search)
        side.addSpacing(10)
        section = QLabel("开发工具")
        section.setObjectName("sidebarSection")
        side.addWidget(section)
        self.navigation = QListWidget()
        self.navigation.setIconSize(QSize(17, 17))
        self.navigation.setObjectName("navigation")
        for index, (title, _, symbol, _) in enumerate(TOOLS):
            item = QListWidgetItem(title)
            item.setIcon(system_icon(symbol))
            self.navigation.addItem(item)
        side.addWidget(self.navigation, 1)
        self.appearance = QComboBox()
        self.appearance.addItems(["浅色外观", "深色外观"])
        self.appearance.setCurrentIndex(1 if self.settings.value("darkMode", False, type=bool) else 0)
        self.appearance.currentIndexChanged.connect(self.change_appearance)
        side.addWidget(self.appearance)
        footer = QLabel("本地处理")
        footer.setObjectName("muted")
        side.addWidget(footer)
        self.hotkey_status = StatusLabel()
        side.addWidget(self.hotkey_status)
        layout.addWidget(sidebar)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 18, 22, 14)
        content_layout.setSpacing(10)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.description = QLabel()
        self.description.setObjectName("muted")
        self.description.setWordWrap(True)
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.description)
        content_layout.addSpacing(6)
        self.stack = QStackedWidget()
        for tab in self.tabs:
            self.stack.addWidget(tab)
        content_layout.addWidget(self.stack, 1)
        layout.addWidget(content, 1)
        self.setCentralWidget(central)
        self.navigation.currentRowChanged.connect(self.switch_tab)
        self.navigation.setCurrentRow(0)
        self.change_appearance(self.appearance.currentIndex())

    def change_appearance(self, index):
        dark = index == 1
        self.settings.setValue("darkMode", dark)
        editors = self.findChildren(CodeEditor)
        blockers = [QSignalBlocker(editor) for editor in editors]
        try:
            apply_theme(QApplication.instance(), dark)
            set_native_appearance(self, dark)
            for row, tool in enumerate(TOOLS):
                self.navigation.item(row).setIcon(system_icon(tool[2], "#a1a1a6" if dark else "#6e6e73"))
            for panel in self.findChildren(EditorPanel):
                panel.update_icons()
            for button in self.findChildren(QToolButton):
                if symbol := button.property("systemSymbol"):
                    button.setIcon(system_icon(symbol, "#f5f5f7" if dark else "#1d1d1f"))
            for editor in editors:
                if hasattr(editor, "highlighter"):
                    editor.highlighter.rehighlight()
                editor.update_line_number_width()
                if editor.collapsed_blocks:
                    editor.apply_folding()
                editor.line_numbers.update()
        finally:
            blockers.clear()

    def select_tool(self, row):
        self.tool_search.clear()
        self.navigation.setCurrentRow(row)

    def filter_tools(self, text):
        query = text.strip().casefold()
        for row, tool in enumerate(TOOLS):
            self.navigation.item(row).setHidden(query not in (tool[0] + tool[1] + self.tabs[row].name).casefold())

    def switch_tab(self, row):
        if row < 0:
            return
        self.stack.setCurrentIndex(row)
        self.page_title.setText(TOOLS[row][0])
        self.description.setText(TOOLS[row][1])
        self.tabs[row].switch_in()

    def closeEvent(self, event):
        if self.tray_icon.isVisible() and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
        else:
            self.tab_dict["calculate"].shutdown()
            event.accept()

    def set_toolbar(self):
        icon = QIcon(get_static_file("assets", "toolbar", "icon.jpeg"))
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("DevTools")
        menu = QMenu(self)
        show = QAction("打开 DevTools · ⌃⌥Space", self)
        show.triggered.connect(self.show_home)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.exit_app)
        menu.addAction(show)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_home()

    def exit_app(self):
        self.tray_icon.hide()
        QApplication.instance().quit()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.hotkey_started:
            self.hotkey_started = True
            panel_error = configure_panel(self)
            hotkey_error = self.hotkey.start()
            message = panel_error or hotkey_error
            self.hotkey_status.set_status(
                message or "⌃⌥Space 唤起 / 隐藏\nEsc 收起窗口", "error" if message else "neutral"
            )

    def eventFilter(self, watched, event):
        if isinstance(event, QKeyEvent) and event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            focus = QApplication.focusWidget()
            if isinstance(focus, CodeEditor) and focus.is_composing:
                return False
            if isinstance(watched, QWidget) and watched.window() is self:
                self.hide_or_minimize()
                return True
        return super().eventFilter(watched, event)

    def hide_or_minimize(self):
        focus = QApplication.focusWidget()
        for panel in self.findChildren(EditorPanel):
            if panel.search_bar.isVisible() and focus is not None and panel.isAncestorOf(focus):
                panel.close_search()
                return
        if self.tray_icon.isVisible() or self.hotkey.hotkey_ref.value:
            self.hide()
        else:
            self.showMinimized()

    def toggle_visibility(self):
        if self.isVisible() and is_window_active(self):
            self.hide()
        else:
            self.show_home()

    def show_home(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.resize(min(self.width(), geometry.width()), min(self.height(), geometry.height()))
        self.move(geometry.center() - self.rect().center())
        bring_to_front(self)
        self.stack.currentWidget().switch_in()

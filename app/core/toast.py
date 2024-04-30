from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QTimer, Qt, QSize, QPropertyAnimation
from PySide6.QtGui import QGuiApplication, QPaintEvent, QPainter, QBrush


class Toast(QWidget):
    style = """#LabelMessage{color:white;font-family:Microsoft YaHei;}"""

    def __init__(self, message='', timeout=1500, parent=None):
        """
        @param message: 提示信息
        @param timeout: 窗口显示时长
        @param parent: 父窗口控件
        """
        super().__init__(parent)
        self.parent = parent
        self.timer = QTimer()
        # 由于不知道动画结束的事件，所以借助QTimer来关闭窗口，动画结束就关闭窗口，所以这里的事件要和动画时间一样
        self.timer.singleShot(timeout, self.close)  # singleShot表示timer只会启动一次
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口透明
        self.setMinimumSize(QSize(220, 100))
        self.setMaximumSize(QSize(220, 180))
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(20, -1, 20, -1)
        self.setLayout(self.layout)
        self.animation = None
        self.init_ui(message)
        self.create_animation(timeout)
        self.setStyleSheet(Toast.style)
        # 调整位置
        self.center()

    def center(self):
        if self.parent is not None:
            toast_x = self.parent.window().x() + int((self.parent.window().width() - self.width()) / 2)
            toast_y = self.parent.window().y() + int((self.parent.window().height() - self.height()) / 2 + 40)
            self.move(toast_x, toast_y)
        else:
            screen = QGuiApplication.primaryScreen().size()
            size = self.geometry()
            self.move(int((screen.width() - size.width()) / 2),
                      int((screen.height() - size.height()) / 2) + 40)

    def init_ui(self, message):
        message_label = QLabel()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(message_label.sizePolicy().hasHeightForWidth())
        message_label.setSizePolicy(size_policy)
        message_label.setWordWrap(True)
        message_label.setText(message)
        message_label.setTextFormat(Qt.AutoText)
        message_label.setScaledContents(True)
        message_label.setObjectName("LabelMessage")
        message_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(message_label)

    def create_animation(self, timeout):
        # 1.定义一个动画
        self.animation = QPropertyAnimation(self, b'windowOpacity')
        self.animation.setTargetObject(self)
        # 2.设置属性值
        self.animation.setStartValue(0)
        self.animation.setKeyValueAt(0.2, 0.7)  # 设置插值0.3 表示单本次动画时间的0.3处的时间点
        self.animation.setKeyValueAt(0.8, 0.7)  # 设置插值0.8 表示单本次动画时间的0.3处的时间点
        self.animation.setEndValue(0)
        # 3.设置时长
        self.animation.setDuration(timeout)
        # 4.启动动画
        self.animation.start()

    def paintEvent(self, a0: QPaintEvent):
        qp = QPainter()
        qp.begin(self)  # 不能掉，不然没效果
        qp.setRenderHints(QPainter.Antialiasing, True)  # 抗锯齿
        qp.setBrush(QBrush(Qt.black))
        qp.setPen(Qt.transparent)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        qp.drawRoundedRect(rect, 15, 15)
        qp.end()

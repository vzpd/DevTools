import ctypes
import sys

from PySide6.QtCore import QObject, Signal


class EventType(ctypes.Structure):
    _fields_ = [("event_class", ctypes.c_uint32), ("event_kind", ctypes.c_uint32)]


class HotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("identifier", ctypes.c_uint32)]


class GlobalHotkey(QObject):
    activated = Signal()
    label = "Control + Option + Space"
    signature = int.from_bytes(b"DvTl", "big")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.carbon = None
        self.hotkey_ref = ctypes.c_void_p()
        self.handler_ref = ctypes.c_void_p()
        self.callback = None
        self.pressed = False

    def start(self):
        if sys.platform != "darwin":
            return "全局快捷键目前仅支持 macOS"
        if self.hotkey_ref.value:
            return None
        try:
            self.carbon = ctypes.CDLL("/System/Library/Frameworks/Carbon.framework/Carbon")
        except OSError:
            return "无法载入 macOS 快捷键接口"
        callback_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
        self.carbon.GetApplicationEventTarget.argtypes = []
        self.carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
        self.carbon.GetEventKind.argtypes = [ctypes.c_void_p]
        self.carbon.GetEventKind.restype = ctypes.c_uint32
        self.carbon.GetEventParameter.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        self.carbon.GetEventParameter.restype = ctypes.c_int32
        self.carbon.InstallEventHandler.argtypes = [
            ctypes.c_void_p,
            callback_type,
            ctypes.c_ulong,
            ctypes.POINTER(EventType),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.carbon.InstallEventHandler.restype = ctypes.c_int32
        self.carbon.RegisterEventHotKey.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            HotKeyID,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.carbon.RegisterEventHotKey.restype = ctypes.c_int32
        self.carbon.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
        self.carbon.UnregisterEventHotKey.restype = ctypes.c_int32
        self.carbon.RemoveEventHandler.argtypes = [ctypes.c_void_p]
        self.carbon.RemoveEventHandler.restype = ctypes.c_int32
        self.callback = callback_type(self.handle_event)
        types = (EventType * 2)(
            EventType(int.from_bytes(b"keyb", "big"), 5), EventType(int.from_bytes(b"keyb", "big"), 6)
        )
        target = self.carbon.GetApplicationEventTarget()
        status = self.carbon.InstallEventHandler(target, self.callback, 2, types, None, ctypes.byref(self.handler_ref))
        if status:
            self.close()
            return f"快捷键事件注册失败（{status}）"
        status = self.carbon.RegisterEventHotKey(
            49, (1 << 12) | (1 << 11), HotKeyID(self.signature, 1), target, 1, ctypes.byref(self.hotkey_ref)
        )
        if status:
            self.close()
            return f"{self.label} 注册失败（{status}），可能被其他应用占用；可使用菜单栏入口"
        return None

    def handle_event(self, handler, event, user_data):
        identifier = HotKeyID()
        status = self.carbon.GetEventParameter(
            event,
            int.from_bytes(b"----", "big"),
            int.from_bytes(b"hkid", "big"),
            None,
            ctypes.sizeof(identifier),
            None,
            ctypes.byref(identifier),
        )
        if status or identifier.signature != self.signature or identifier.identifier != 1:
            return -9874
        if self.carbon.GetEventKind(event) == 6:
            self.pressed = False
        elif not self.pressed:
            self.pressed = True
            self.activated.emit()
        return 0

    def close(self):
        if self.carbon is not None:
            if self.hotkey_ref.value:
                self.carbon.UnregisterEventHotKey(self.hotkey_ref)
            if self.handler_ref.value:
                self.carbon.RemoveEventHandler(self.handler_ref)
        self.hotkey_ref = ctypes.c_void_p()
        self.handler_ref = ctypes.c_void_p()
        self.callback = None
        self.pressed = False

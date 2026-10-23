import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


def prepare_panel(window):
    if sys.platform == "darwin":
        window.setWindowFlags(
            Qt.Tool
            | Qt.WindowCloseButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowTitleHint
            | Qt.CustomizeWindowHint
        )
        window.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        window.setAttribute(Qt.WA_ShowWithoutActivating, True)


def configure_panel(window):
    if sys.platform != "darwin" or QApplication.platformName() != "cocoa":
        return None
    try:
        import AppKit
        import objc
    except ImportError:
        return "缺少 macOS 窗口依赖，无法启用全屏空间唤起；请安装 pyobjc-framework-Cocoa"
    AppKit.NSApplication.sharedApplication().setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    view = objc.objc_object(c_void_p=int(window.winId()))
    native = view.window()
    if native is None:
        return "未获取到 macOS 原生窗口，全屏空间支持未启用"
    native.setCollectionBehavior_(
        AppKit.NSWindowCollectionBehaviorManaged | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
    )
    native.setStyleMask_(native.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel)
    native.setLevel_(AppKit.NSFloatingWindowLevel)
    native.setTitlebarAppearsTransparent_(True)
    native.setHidesOnDeactivate_(False)
    native.setBecomesKeyOnlyIfNeeded_(False)
    return None


def bring_to_front(window):
    if sys.platform == "darwin" and QApplication.platformName() == "cocoa":
        try:
            import objc
        except ImportError:
            window.showNormal()
            window.raise_()
            window.activateWindow()
            return
        native = objc.objc_object(c_void_p=int(window.winId())).window()
        if native is not None:
            if not native.isOnActiveSpace():
                window.hide()
                window.destroy(True, True)
                configure_panel(window)
                set_native_appearance(window, QApplication.palette().color(QPalette.Window).lightness() < 128)
                native = objc.objc_object(c_void_p=int(window.winId())).window()
            window.showNormal()
            native.makeKeyAndOrderFront_(None)
            native.orderFrontRegardless()
            window.windowHandle().requestActivate()
            return
    window.showNormal()
    window.raise_()
    window.activateWindow()


def is_window_active(window):
    if sys.platform == "darwin" and QApplication.platformName() == "cocoa":
        try:
            import objc
        except ImportError:
            return window.isActiveWindow()
        native = objc.objc_object(c_void_p=int(window.winId())).window()
        return native is not None and native.isOnActiveSpace() and native.isKeyWindow()
    return window.isActiveWindow()


def set_native_appearance(window, dark):
    if sys.platform != "darwin" or QApplication.platformName() != "cocoa":
        return
    try:
        import AppKit
        import objc
    except ImportError:
        return
    native = objc.objc_object(c_void_p=int(window.winId())).window()
    if native is not None:
        name = AppKit.NSAppearanceNameDarkAqua if dark else AppKit.NSAppearanceNameAqua
        native.setAppearance_(AppKit.NSAppearance.appearanceNamed_(name))

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


def system_icon(name, color="#6e6e73"):
    if sys.platform != "darwin":
        return QIcon()
    try:
        import AppKit

        native = AppKit.NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
        if native is None:
            return QIcon()
        configuration = AppKit.NSImageSymbolConfiguration.configurationWithPointSize_weight_(
            16, AppKit.NSFontWeightRegular
        )
        native = native.imageWithSymbolConfiguration_(configuration)
        pixmap = QPixmap()
        if not pixmap.loadFromData(bytes(native.TIFFRepresentation())):
            return QIcon()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()
        icon = QIcon(pixmap)
        selected = QPixmap(pixmap.size())
        selected.fill(Qt.transparent)
        painter = QPainter(selected)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(selected.rect(), Qt.white)
        painter.end()
        icon.addPixmap(selected, QIcon.Selected)
        return icon
    except ImportError:
        return QIcon()

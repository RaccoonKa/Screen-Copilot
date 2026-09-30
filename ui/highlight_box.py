from PyQt6 import QtWidgets, QtCore, QtGui


class HighlightBox(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def show_at(self, rect: QtCore.QRect):
        padding = 6
        glow_space = 12
        total_margin = padding + glow_space

        self.setGeometry(
            rect.x() - total_margin,
            rect.y() - total_margin,
            rect.width() + total_margin * 2,
            rect.height() + total_margin * 2
        )
        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        glow_space = 12.0
        draw_rect = QtCore.QRectF(
            glow_space, glow_space,
            self.width() - 2 * glow_space,
            self.height() - 2 * glow_space
        )

        for i in range(4):
            alpha = int(35 - i * 8)
            glow_color = QtGui.QColor(0, 242, 255, max(0, alpha))
            pen = QtGui.QPen(glow_color, 2.0 + i * 2.0)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            spread = i * 1.5
            painter.drawRoundedRect(draw_rect.adjusted(-spread, -spread, spread, spread), 6 + spread, 6 + spread)

        painter.setBrush(QtGui.QColor(0, 242, 255, 18))
        border_pen = QtGui.QPen(QtGui.QColor(0, 242, 255, 230), 1.8)
        painter.setPen(border_pen)
        painter.drawRoundedRect(draw_rect, 6, 6)

        corner_len = 10.0
        accent_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 240), 2.2)
        painter.setPen(accent_pen)

        tl = draw_rect.topLeft()
        painter.drawLine(QtCore.QPointF(tl.x(), tl.y()), QtCore.QPointF(tl.x() + corner_len, tl.y()))
        painter.drawLine(QtCore.QPointF(tl.x(), tl.y()), QtCore.QPointF(tl.x(), tl.y() + corner_len))

        tr = draw_rect.topRight()
        painter.drawLine(QtCore.QPointF(tr.x(), tr.y()), QtCore.QPointF(tr.x() - corner_len, tr.y()))
        painter.drawLine(QtCore.QPointF(tr.x(), tr.y()), QtCore.QPointF(tr.x(), tr.y() + corner_len))

        bl = draw_rect.bottomLeft()
        painter.drawLine(QtCore.QPointF(bl.x(), bl.y()), QtCore.QPointF(bl.x() + corner_len, bl.y()))
        painter.drawLine(QtCore.QPointF(bl.x(), bl.y()), QtCore.QPointF(bl.x(), bl.y() - corner_len))

        br = draw_rect.bottomRight()
        painter.drawLine(QtCore.QPointF(br.x(), br.y()), QtCore.QPointF(br.x() - corner_len, br.y()))
        painter.drawLine(QtCore.QPointF(br.x(), br.y()), QtCore.QPointF(br.x(), br.y() - corner_len))
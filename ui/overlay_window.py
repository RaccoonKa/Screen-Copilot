import sys
import math
from PyQt6 import QtWidgets, QtCore, QtGui
from ui.styles import (
    OVERLAY_BG,
    BORDER_COLOR_START,
    BORDER_COLOR_MID,
    BORDER_COLOR_END,
    SELECTION_BORDER_WIDTH,
    CORNER_RADIUS,
    SelectionMode
)


class ScreenOverlay(QtWidgets.QWidget):
    snippet_captured = QtCore.pyqtSignal(QtGui.QImage, QtCore.QRect)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.current_mode = SelectionMode.LASSO
        self.is_drawing = False
        self.start_pos = None
        self.current_pos = None
        self.path_points = []
        self.full_screen_shot = None
        self.hud_rect = QtCore.QRect()

        self.anim_progress = 0.0
        self.fade_anim = QtCore.QVariantAnimation(self)
        self.fade_anim.setDuration(240)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.fade_anim.valueChanged.connect(self._on_fade_frame)

        self.pill_offset_x = 112.0
        self.pill_start_x = 112.0
        self.pill_target_x = 112.0
        self.pill_anim = QtCore.QVariantAnimation(self)
        self.pill_anim.setDuration(320)
        self.pill_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutQuart)
        self.pill_anim.valueChanged.connect(self._on_pill_frame)

    def _on_fade_frame(self, val: float):
        self.anim_progress = val
        self.update()

    def _on_pill_frame(self, val: float):
        self.pill_offset_x = val
        self.update()

    def set_mode(self, mode: SelectionMode):
        if self.current_mode == mode:
            return
        self.current_mode = mode
        self.pill_start_x = self.pill_offset_x
        self.pill_target_x = 4.0 if mode == SelectionMode.RECT else 112.0

        self.pill_anim.stop()
        self.pill_anim.setStartValue(self.pill_start_x)
        self.pill_anim.setEndValue(self.pill_target_x)
        self.pill_anim.start()

    def capture_and_show(self):
        screen = QtWidgets.QApplication.primaryScreen()
        if not screen:
            return

        pix = screen.grabWindow(0)
        pix.setDevicePixelRatio(screen.devicePixelRatio())
        self.full_screen_shot = pix

        self.is_drawing = False
        self.path_points = []
        self.start_pos = None
        self.current_pos = None

        self.pill_offset_x = 4.0 if self.current_mode == SelectionMode.RECT else 112.0
        self.pill_start_x = self.pill_offset_x
        self.pill_target_x = self.pill_offset_x

        self.setGeometry(screen.geometry())
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

        self.fade_anim.stop()
        self.fade_anim.start()

    def draw_screen_border(self, painter: QtGui.QPainter):
        if self.anim_progress <= 0:
            return

        painter.save()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        grad = QtGui.QLinearGradient(0, 0, w, h)
        alpha = int(255 * self.anim_progress)
        grad.setColorAt(0.0,
                        QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(), BORDER_COLOR_START.blue(),
                                     alpha))
        grad.setColorAt(0.5,
                        QtGui.QColor(BORDER_COLOR_MID.red(), BORDER_COLOR_MID.green(), BORDER_COLOR_MID.blue(), alpha))
        grad.setColorAt(1.0,
                        QtGui.QColor(BORDER_COLOR_END.red(), BORDER_COLOR_END.green(), BORDER_COLOR_END.blue(), alpha))

        main_pen = QtGui.QPen(QtGui.QBrush(grad), 3)
        painter.setPen(main_pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(QtCore.QRectF(1.5, 1.5, w - 3, h - 3))

        glow_alpha = int(50 * self.anim_progress)
        for i in range(1, 4):
            glow_grad = QtGui.QLinearGradient(0, 0, w, h)
            a = int(glow_alpha / i)
            glow_grad.setColorAt(0.0, QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(),
                                                   BORDER_COLOR_START.blue(), a))
            glow_grad.setColorAt(0.5,
                                 QtGui.QColor(BORDER_COLOR_MID.red(), BORDER_COLOR_MID.green(), BORDER_COLOR_MID.blue(),
                                              a))
            glow_grad.setColorAt(1.0,
                                 QtGui.QColor(BORDER_COLOR_END.red(), BORDER_COLOR_END.green(), BORDER_COLOR_END.blue(),
                                              a))

            painter.setPen(QtGui.QPen(QtGui.QBrush(glow_grad), 1))
            painter.drawRect(QtCore.QRectF(1.5 + i, 1.5 + i, w - 3 - 2 * i, h - 3 - 2 * i))

        painter.restore()

    def draw_bottom_hud(self, painter: QtGui.QPainter):
        hud_w, hud_h = 330, 42
        slide_offset = int((1.0 - self.anim_progress) * 35)
        base_y = self.height() - hud_h - 35 + slide_offset
        self.hud_rect = QtCore.QRect((self.width() - hud_w) // 2, base_y, hud_w, hud_h)

        painter.save()

        glow_alpha = int(45 * self.anim_progress)
        for r in (14, 10, 6, 2):
            expanded = QtCore.QRectF(self.hud_rect).adjusted(-r, -r, r, r)
            grad = QtGui.QLinearGradient(expanded.topLeft(), expanded.bottomRight())
            factor = (15 - r) / 15.0
            grad.setColorAt(0.0, QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(),
                                              BORDER_COLOR_START.blue(), int(glow_alpha * factor)))
            grad.setColorAt(1.0, QtGui.QColor(BORDER_COLOR_END.red(), BORDER_COLOR_END.green(), BORDER_COLOR_END.blue(),
                                              int(glow_alpha * factor)))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawRoundedRect(expanded, 21 + r, 21 + r)

        hud_bg = QtGui.QColor(16, 18, 24, int(235 * self.anim_progress))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(hud_bg)
        painter.drawRoundedRect(self.hud_rect, 21, 21)

        border_col = QtGui.QColor(60, 65, 80, int(180 * self.anim_progress))
        painter.setPen(QtGui.QPen(border_col, 1))
        painter.drawRoundedRect(self.hud_rect, 21, 21)

        span = abs(self.pill_target_x - self.pill_start_x)
        if span > 1.0:
            progress = abs(self.pill_offset_x - self.pill_start_x) / span
            stretch = math.sin(progress * math.pi) * 14.0
        else:
            stretch = 0.0

        pill_base_w = 105.0
        pill_current_w = pill_base_w + stretch
        pill_current_x = self.pill_offset_x - (stretch * 0.5)

        pill_rect = QtCore.QRectF(
            self.hud_rect.x() + pill_current_x,
            self.hud_rect.y() + 4,
            pill_current_w,
            hud_h - 8
        )
        pill_bg = QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(), BORDER_COLOR_START.blue(),
                               int(35 * self.anim_progress))
        pill_border = QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(), BORDER_COLOR_START.blue(),
                                   int(150 * self.anim_progress))
        painter.setBrush(pill_bg)
        painter.setPen(QtGui.QPen(pill_border, 1.2))
        painter.drawRoundedRect(pill_rect, 17, 17)

        rect_zone = QtCore.QRect(self.hud_rect.x() + 4, self.hud_rect.y() + 4, 105, hud_h - 8)
        lasso_zone = QtCore.QRect(self.hud_rect.x() + 112, self.hud_rect.y() + 4, 105, hud_h - 8)
        esc_zone = QtCore.QRect(self.hud_rect.x() + 220, self.hud_rect.y() + 4, 105, hud_h - 8)

        painter.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Weight.DemiBold))

        blend_lasso = max(0.0, min(1.0, (self.pill_offset_x - 4.0) / 108.0))
        blend_rect = 1.0 - blend_lasso

        def lerp_color(factor: float) -> QtGui.QColor:
            r = int(150 + (BORDER_COLOR_START.red() - 150) * factor)
            g = int(155 + (BORDER_COLOR_START.green() - 155) * factor)
            b = int(170 + (BORDER_COLOR_START.blue() - 170) * factor)
            c = QtGui.QColor(r, g, b)
            c.setAlpha(int(255 * self.anim_progress))
            return c

        painter.setPen(lerp_color(blend_rect))
        painter.drawText(rect_zone, QtCore.Qt.AlignmentFlag.AlignCenter, "[R] Frame")

        painter.setPen(lerp_color(blend_lasso))
        painter.drawText(lasso_zone, QtCore.Qt.AlignmentFlag.AlignCenter, "[L] Lasso")

        esc_text_col = QtGui.QColor(220, 90, 90, int(220 * self.anim_progress))
        painter.setPen(esc_text_col)
        painter.drawText(esc_zone, QtCore.Qt.AlignmentFlag.AlignCenter, "[Esc] Exit")

        painter.restore()

    def paintEvent(self, event):
        if not self.full_screen_shot:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.drawPixmap(0, 0, self.full_screen_shot)

        dim_color = QtGui.QColor(OVERLAY_BG)
        dim_color.setAlpha(int(OVERLAY_BG.alpha() * self.anim_progress))
        painter.fillRect(self.rect(), dim_color)

        self.draw_screen_border(painter)

        if self.is_drawing:
            if self.current_mode == SelectionMode.RECT and self.start_pos and self.current_pos:
                rect = QtCore.QRect(self.start_pos, self.current_pos).normalized()

                painter.save()
                painter.setClipRect(rect)
                painter.drawPixmap(0, 0, self.full_screen_shot)
                painter.restore()

                grad = QtGui.QLinearGradient(rect.topLeft().toPointF(), rect.bottomRight().toPointF())
                grad.setColorAt(0.0, BORDER_COLOR_START)
                grad.setColorAt(1.0, BORDER_COLOR_END)

                pen = QtGui.QPen(QtGui.QBrush(grad), SELECTION_BORDER_WIDTH)
                painter.setPen(pen)
                painter.drawRoundedRect(rect, CORNER_RADIUS, CORNER_RADIUS)

            elif self.current_mode == SelectionMode.LASSO and len(self.path_points) > 1:
                path = QtGui.QPainterPath()
                path.setFillRule(QtCore.Qt.FillRule.WindingFill)
                path.moveTo(QtCore.QPointF(self.path_points[0]))
                for pt in self.path_points[1:]:
                    path.lineTo(QtCore.QPointF(pt))

                painter.save()
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, self.full_screen_shot)
                painter.fillRect(self.rect(), QtGui.QColor(BORDER_COLOR_START.red(), BORDER_COLOR_START.green(),
                                                           BORDER_COLOR_START.blue(), 30))
                painter.restore()

                pen = QtGui.QPen(BORDER_COLOR_START, SELECTION_BORDER_WIDTH)
                pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)

        self.draw_bottom_hud(painter)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = event.pos()

            if self.hud_rect.contains(pos):
                rel_x = pos.x() - self.hud_rect.x()
                if rel_x < 110:
                    self.set_mode(SelectionMode.RECT)
                elif rel_x < 220:
                    self.set_mode(SelectionMode.LASSO)
                else:
                    self.hide()
                return

            self.is_drawing = True
            self.start_pos = pos
            self.current_pos = pos
            self.path_points = [pos]
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_pos = event.pos()
            if self.current_mode == SelectionMode.LASSO:
                if (self.current_pos - self.path_points[-1]).manhattanLength() > 3:
                    self.path_points.append(self.current_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.hide()

            if self.current_mode == SelectionMode.RECT:
                self.process_rect_selection()
            elif self.current_mode == SelectionMode.LASSO:
                self.process_lasso_selection()

    def process_rect_selection(self):
        if not self.start_pos or not self.current_pos:
            return

        selection_rect = QtCore.QRect(self.start_pos, self.current_pos).normalized()
        if selection_rect.width() > 15 and selection_rect.height() > 15:
            dpr = self.full_screen_shot.devicePixelRatio()
            out_image = QtGui.QImage(
                int(selection_rect.width() * dpr),
                int(selection_rect.height() * dpr),
                QtGui.QImage.Format.Format_ARGB32_Premultiplied
            )
            out_image.setDevicePixelRatio(dpr)
            out_image.fill(QtCore.Qt.GlobalColor.transparent)

            painter = QtGui.QPainter(out_image)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.drawPixmap(-selection_rect.x(), -selection_rect.y(), self.full_screen_shot)
            painter.end()

            self.snippet_captured.emit(out_image, selection_rect)

    def process_lasso_selection(self):
        if len(self.path_points) < 4:
            return

        path = QtGui.QPainterPath()
        path.setFillRule(QtCore.Qt.FillRule.WindingFill)
        path.moveTo(QtCore.QPointF(self.path_points[0]))
        for pt in self.path_points[1:]:
            path.lineTo(QtCore.QPointF(pt))
        path.closeSubpath()

        logic_box = path.boundingRect().toRect()
        if logic_box.width() < 15 or logic_box.height() < 15:
            return

        dpr = self.full_screen_shot.devicePixelRatio()
        out_image = QtGui.QImage(
            int(logic_box.width() * dpr),
            int(logic_box.height() * dpr),
            QtGui.QImage.Format.Format_ARGB32_Premultiplied
        )
        out_image.setDevicePixelRatio(dpr)
        out_image.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(out_image)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        shifted_path = path.translated(-logic_box.topLeft().toPointF())
        shifted_path.setFillRule(QtCore.Qt.FillRule.WindingFill)

        painter.setClipPath(shifted_path)
        painter.drawPixmap(-logic_box.x(), -logic_box.y(), self.full_screen_shot)
        painter.end()

        self.snippet_captured.emit(out_image, logic_box)

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text().lower()

        if key == QtCore.Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        elif key == QtCore.Qt.Key.Key_R or text in ('r', 'к'):
            self.set_mode(SelectionMode.RECT)
            event.accept()
        elif key == QtCore.Qt.Key.Key_L or text in ('l', 'д'):
            self.set_mode(SelectionMode.LASSO)
            event.accept()
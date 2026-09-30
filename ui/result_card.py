import re
from PyQt6 import QtWidgets, QtCore, QtGui
from ui.styles import (
    RESULT_CARD_STYLE,
    BORDER_COLOR_START,
    BORDER_COLOR_MID,
    BORDER_COLOR_END
)


class ResultCard(QtWidgets.QWidget):
    closed = QtCore.pyqtSignal()
    question_submitted = QtCore.pyqtSignal(str)
    translate_requested = QtCore.pyqtSignal(str)
    bbox_found = QtCore.pyqtSignal(QtCore.QRect)
    paste_fix_requested = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(RESULT_CARD_STYLE)

        self.setFixedWidth(540)
        self.setMinimumHeight(380)

        self.drag_position = None
        self.current_en_text = ""
        self.current_ru_text = ""
        self.latest_code_fix = ""
        self.is_showing_russian = False
        self.current_image = None
        self.init_ui()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(22, 18, 22, 18)
        main_layout.setSpacing(10)

        header_layout = QtWidgets.QHBoxLayout()

        self.title_label = QtWidgets.QLabel("✦ Screen Copilot", self)
        self.title_label.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #00F2FF; border: none;")

        self.status_label = QtWidgets.QLabel("Analysis...", self)
        self.status_label.setFont(QtGui.QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #888899; border: none;")

        self.translate_btn = QtWidgets.QPushButton("Translate", self)
        self.translate_btn.setObjectName("TranslateBtn")
        self.translate_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.translate_btn.clicked.connect(self._on_translate_clicked)
        self.translate_btn.setEnabled(False)

        self.close_btn = QtWidgets.QPushButton("✕", self)
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.hide_card)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.translate_btn)
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        self.text_browser = QtWidgets.QTextBrowser(self)
        self.text_browser.setOpenExternalLinks(True)
        main_layout.addWidget(self.text_browser)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_field = QtWidgets.QLineEdit(self)
        self.input_field.setPlaceholderText("Ask or clarify the code.... (Enter)")
        self.input_field.returnPressed.connect(self._on_send_clicked)

        self.send_btn = QtWidgets.QPushButton("➤", self)
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.setFixedSize(34, 30)
        self.send_btn.clicked.connect(self._on_send_clicked)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        main_layout.addLayout(input_layout)

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(8)

        self.copy_fix_btn = QtWidgets.QPushButton("Copy fix", self)
        self.copy_fix_btn.setObjectName("ActionBtn")
        self.copy_fix_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.copy_fix_btn.clicked.connect(self.copy_code_fix)
        self.copy_fix_btn.setEnabled(False)

        self.paste_fix_btn = QtWidgets.QPushButton("⚡ Paste in IDE", self)
        self.paste_fix_btn.setObjectName("PrimaryActionBtn")
        self.paste_fix_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.paste_fix_btn.clicked.connect(self.paste_code_fix)
        self.paste_fix_btn.setEnabled(False)

        bottom_layout.addWidget(self.copy_fix_btn)
        bottom_layout.addWidget(self.paste_fix_btn)
        bottom_layout.addStretch()

        self.copy_btn = QtWidgets.QPushButton("Copy all", self)
        self.copy_btn.setObjectName("ActionBtn")
        self.copy_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        bottom_layout.addWidget(self.copy_btn)

        main_layout.addLayout(bottom_layout)

    def _clean_markdown(self, raw_text: str) -> str:
        text = re.sub(r"<bbox>.*?</bbox>", "", raw_text)
        text = text.replace("<code_start>", "").replace("<code_end>", "")
        text = text.replace("<error_start>", "").replace("<error_end>", "")
        text = text.replace("<fix_start>", "").replace("<fix_end>", "")
        return text.strip()

    def _extract_code_fix(self, text: str) -> str:
        blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", text)
        if blocks:
            code = blocks[-1].strip()
            if code:
                return code

        parts = re.split(r"(?:look like this|should be|corrected code|fixed code|here is the fix)[^\n]*:\s*\n?", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            raw_chunk = parts[-1].strip()
            code_lines = []
            for line in raw_chunk.split("\n"):
                stripped = line.strip()
                if not stripped:
                    if code_lines:
                        code_lines.append("")
                    continue
                if line.startswith(" ") or line.startswith("\t") or any(stripped.startswith(k) for k in ["def ", "class ", "if ", "for ", "while ", "return", "import ", "from ", "self.", "try:", "except"]):
                    code_lines.append(line)
                elif code_lines:
                    break
            if code_lines:
                return "\n".join(code_lines).strip()

        lines = [l for l in text.strip().split("\n") if l.strip()]
        if lines:
            first_line = lines[0].strip()
            code_starters = ("def ", "class ", "import ", "from ", "if ", "for ", "while ", "return", "self.", "try:", "@")
            if any(first_line.startswith(k) for k in code_starters) or first_line.endswith(":"):
                return text.strip()

        return ""

    def _detect_ide_error_region(self, image: QtGui.QImage) -> QtCore.QRect:
        if not image or image.isNull():
            return None

        w = image.width()
        h = image.height()
        dpr = image.devicePixelRatio() or 1.0

        red_pts = []
        step_x = max(1, w // 300)
        step_y = max(1, h // 200)

        for y in range(0, h, step_y):
            for x in range(0, w, step_x):
                col = QtGui.QColor(image.pixel(x, y))
                r, g, b = col.red(), col.green(), col.blue()
                if r > 145 and g < 90 and b < 90:
                    red_pts.append((x, y))

        if len(red_pts) < 4:
            return None

        red_pts.sort(key=lambda p: p[1])
        line_threshold = int(18 * dpr)

        lines = []
        current_cluster = [red_pts[0]]

        for pt in red_pts[1:]:
            if pt[1] - current_cluster[-1][1] <= line_threshold:
                current_cluster.append(pt)
            else:
                if len(current_cluster) >= 4:
                    lines.append(current_cluster)
                current_cluster = [pt]
        if len(current_cluster) >= 4:
            lines.append(current_cluster)

        if not lines:
            return None

        top_line = lines[0]
        xs = [p[0] for p in top_line]
        ys = [p[1] for p in top_line]

        pad_x = int(6 * dpr)
        pad_y = int(8 * dpr)

        min_x = max(0, min(xs) - pad_x)
        max_x = min(w, max(xs) + pad_x)
        min_y = max(0, min(ys) - pad_y)
        max_y = min(h, max(ys) + pad_y)

        lx = int(min_x / dpr)
        ly = int(min_y / dpr)
        lw = int((max_x - min_x) / dpr)
        lh = int((max_y - min_y) / dpr)

        return QtCore.QRect(lx, ly, lw, lh)

    def _extract_and_emit_bbox(self, text: str):
        if self.current_image:
            auto_box = self._detect_ide_error_region(self.current_image)
            if auto_box:
                self.bbox_found.emit(auto_box)
                return

        match = re.search(r"<bbox>\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*</bbox>", text)
        if match:
            try:
                x1, y1, x2, y2 = map(int, match.groups())
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                if w > 5 and h > 5:
                    self.bbox_found.emit(QtCore.QRect(x, y, w, h))
            except Exception:
                pass

    def _on_translate_clicked(self):
        if self.is_showing_russian:
            self.text_browser.setMarkdown(self._clean_markdown(self.current_en_text))
            self.is_showing_russian = False
            self.translate_btn.setText("Translate")
        else:
            if self.current_ru_text:
                self.text_browser.setMarkdown(self._clean_markdown(self.current_ru_text))
                self.is_showing_russian = True
                self.translate_btn.setText("Original")
            else:
                self.translate_btn.setEnabled(False)
                self.status_label.setText("Translation...")
                clean_for_trans = self._clean_markdown(self.current_en_text)
                self.translate_requested.emit(clean_for_trans)

        sb = self.text_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def apply_translation(self, translated_text: str):
        self.current_ru_text = translated_text
        self.text_browser.setMarkdown(self._clean_markdown(self.current_ru_text))
        self.is_showing_russian = True
        self.translate_btn.setText("Original")
        self.translate_btn.setEnabled(True)
        self.status_label.setText("Done")
        sb = self.text_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_send_clicked(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.translate_btn.setEnabled(False)
        self.copy_fix_btn.setEnabled(False)
        self.paste_fix_btn.setEnabled(False)

        self.current_en_text += f"\n\n---\n**You:** {text}\n\n**Copilot:** "
        self.current_ru_text = ""
        self.is_showing_russian = False
        self.translate_btn.setText("Translate")

        self.text_browser.setMarkdown(self._clean_markdown(self.current_en_text))
        self.status_label.setText("Generation...")

        self.question_submitted.emit(text)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        margin = 10.0
        card_rect = QtCore.QRectF(
            margin, margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )

        shadow_color = QtGui.QColor(0, 0, 0)
        for i in range(5):
            alpha = int(18 - i * 3.5)
            shadow_color.setAlpha(max(0, alpha))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)
            offset_y = 2.0 + i * 1.2
            spread = i * 1.5
            s_rect = card_rect.adjusted(-spread, -spread + offset_y, spread, spread + offset_y)
            painter.drawRoundedRect(s_rect, 14 + spread, 14 + spread)

        painter.setBrush(QtGui.QColor(18, 20, 26, 250))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(card_rect, 14, 14)

        grad = QtGui.QLinearGradient(card_rect.topLeft(), card_rect.bottomRight())
        grad.setColorAt(0.0, BORDER_COLOR_START)
        grad.setColorAt(0.5, BORDER_COLOR_MID)
        grad.setColorAt(1.0, BORDER_COLOR_END)

        pen = QtGui.QPen(QtGui.QBrush(grad), 1.5)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

        inner_rect = card_rect.adjusted(0.75, 0.75, -0.75, -0.75)
        painter.drawRoundedRect(inner_rect, 13.5, 13.5)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()

    def show_at(self, target_rect: QtCore.QRect, image: QtGui.QImage = None):
        self.current_image = image
        self.current_en_text = ""
        self.current_ru_text = ""
        self.latest_code_fix = ""
        self.is_showing_russian = False
        self.translate_btn.setText("Translate")
        self.translate_btn.setEnabled(False)
        self.copy_fix_btn.setEnabled(False)
        self.paste_fix_btn.setEnabled(False)

        self.text_browser.setMarkdown("*Analyzing the image...*")
        self.status_label.setText("Preparation...")
        self.copy_btn.setText("Copy all")
        self.copy_fix_btn.setText("Copy fix")
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        card_w = self.width()
        card_h = self.height()

        target_x = target_rect.right() + 15
        target_y = target_rect.top()

        if target_x + card_w > screen.right():
            target_x = target_rect.left() - card_w - 15

        if target_x < screen.left():
            target_x = max(screen.left() + 10, target_rect.left())
            target_y = target_rect.bottom() + 15

        if target_y + card_h > screen.bottom():
            target_y = screen.bottom() - card_h - 20

        self.move(target_x, max(screen.top() + 20, target_y))
        self.show()
        self.raise_()
        self.activateWindow()

    def set_status_text(self, text: str):
        self.status_label.setText(text)

    def append_stream_token(self, token: str):
        self.current_en_text += token
        self.text_browser.setMarkdown(self._clean_markdown(self.current_en_text))
        sb = self.text_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def finish_stream(self, final_text: str):
        self.status_label.setText("Done")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.translate_btn.setEnabled(True)
        self.input_field.setFocus()

        if final_text and not self.current_en_text.strip():
            self.current_en_text = final_text

        self.text_browser.setMarkdown(self._clean_markdown(self.current_en_text))
        self._extract_and_emit_bbox(self.current_en_text)

        self.latest_code_fix = self._extract_code_fix(self.current_en_text)
        has_fix = bool(self.latest_code_fix)
        self.copy_fix_btn.setEnabled(has_fix)
        self.paste_fix_btn.setEnabled(has_fix)

        sb = self.text_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_error(self, err_msg: str):
        self.status_label.setText("Error")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.translate_btn.setEnabled(True)
        self.text_browser.setMarkdown(f"**An error has occurred:**\n`{err_msg}`")

    def copy_code_fix(self):
        if self.latest_code_fix:
            QtWidgets.QApplication.clipboard().setText(self.latest_code_fix)
            self.copy_fix_btn.setText("Copied!")
            QtCore.QTimer.singleShot(1500, lambda: self.copy_fix_btn.setText("Copy fix"))

    def paste_code_fix(self):
        if self.latest_code_fix:
            QtWidgets.QApplication.clipboard().setText(self.latest_code_fix)
            self.paste_fix_requested.emit(self.latest_code_fix)

    def copy_to_clipboard(self):
        text = self.text_browser.toPlainText()
        QtWidgets.QApplication.clipboard().setText(text)
        self.copy_btn.setText("Copied!")
        QtCore.QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy all"))

    def hide_card(self):
        self.hide()
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.hide_card()
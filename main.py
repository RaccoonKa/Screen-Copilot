import sys
import ctypes
from PyQt6 import QtWidgets, QtCore, QtGui
from ui.overlay_window import ScreenOverlay
from ui.result_card import ResultCard
from ui.highlight_box import HighlightBox
from core.hotkey_listener import HotkeyListener
from core.process_watcher import is_ide_focused
from core.ai_engine import AIEngine
from config import HOTKEY

user32 = ctypes.windll.user32


class AppController(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.overlay = ScreenOverlay()
        self.card = ResultCard()
        self.highlight_box = HighlightBox()
        self.ai_engine = AIEngine()
        self.current_worker = None
        self.trans_worker = None
        self.last_snippet_rect = QtCore.QRect()
        self.box_suspended = False
        self.ide_hwnd = None

        self.hotkey_listener = HotkeyListener(HOTKEY)
        self.hotkey_listener.triggered.connect(self.trigger_capture)

        self.overlay.snippet_captured.connect(self.on_snippet_captured)
        self.card.question_submitted.connect(self.on_followup_question)
        self.card.translate_requested.connect(self.on_translate_requested)
        self.card.bbox_found.connect(self.on_bbox_found)
        self.card.paste_fix_requested.connect(self.on_paste_fix_requested)
        self.card.closed.connect(self.highlight_box.hide)

        self.focus_timer = QtCore.QTimer(self)
        self.focus_timer.setInterval(150)
        self.focus_timer.timeout.connect(self.check_focus_state)
        self.focus_timer.start()

        self.hotkey_listener.start()

    def check_focus_state(self):
        ide_active = is_ide_focused()
        if not ide_active:
            if self.highlight_box.isVisible():
                self.highlight_box.hide()
                self.box_suspended = True
        else:
            if self.box_suspended and self.card.isVisible():
                self.highlight_box.show()
                self.box_suspended = False

    def trigger_capture(self):
        if not is_ide_focused():
            return

        if self.overlay.isVisible():
            return

        self.ide_hwnd = user32.GetForegroundWindow()

        self.box_suspended = False
        self.highlight_box.hide()
        self.card.hide()
        self.overlay.capture_and_show()

    def on_snippet_captured(self, image: QtGui.QImage, rect: QtCore.QRect):
        self.last_snippet_rect = rect
        self.box_suspended = False
        self.highlight_box.hide()
        self.card.show_at(rect, image)

        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        self.current_worker = self.ai_engine.create_worker(image)
        self.current_worker.status_changed.connect(self.card.set_status_text)
        self.current_worker.token_generated.connect(self.card.append_stream_token)
        self.current_worker.finished.connect(self.card.finish_stream)
        self.current_worker.error_occurred.connect(self.card.set_error)
        self.current_worker.start()

    def on_followup_question(self, question: str):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        self.current_worker = self.ai_engine.create_worker(None, prompt=question)
        self.current_worker.status_changed.connect(self.card.set_status_text)
        self.current_worker.token_generated.connect(self.card.append_stream_token)
        self.current_worker.finished.connect(self.card.finish_stream)
        self.current_worker.error_occurred.connect(self.card.set_error)
        self.current_worker.start()

    def on_translate_requested(self, text: str):
        if self.trans_worker and self.trans_worker.isRunning():
            self.trans_worker.terminate()
            self.trans_worker.wait()

        self.trans_worker = self.ai_engine.create_translation_worker(text)
        self.trans_worker.finished.connect(self.card.apply_translation)
        self.trans_worker.error_occurred.connect(self.card.set_error)
        self.trans_worker.start()

    def on_bbox_found(self, local_rect: QtCore.QRect):
        if self.last_snippet_rect.isNull():
            return

        global_x = self.last_snippet_rect.x() + local_rect.x()
        global_y = self.last_snippet_rect.y() + local_rect.y()
        target_rect = QtCore.QRect(global_x, global_y, local_rect.width(), local_rect.height())

        self.highlight_box.show_at(target_rect)

    def on_paste_fix_requested(self, code_text: str):
        self.card.hide()
        self.highlight_box.hide()
        self.box_suspended = False

        QtWidgets.QApplication.clipboard().setText(code_text)

        def do_paste():
            if self.ide_hwnd:
                user32.SetForegroundWindow(self.ide_hwnd)

            def send_paste():
                user32.keybd_event(0x11, 0, 0, 0)
                user32.keybd_event(0x56, 0, 0, 0)
                user32.keybd_event(0x56, 0, 2, 0)
                user32.keybd_event(0x11, 0, 2, 0)

            QtCore.QTimer.singleShot(80, send_paste)

        QtCore.QTimer.singleShot(150, do_paste)

    def cleanup(self):
        self.hotkey_listener.stop()
        self.highlight_box.hide()
        if self.focus_timer.isActive():
            self.focus_timer.stop()
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()
        if self.trans_worker and self.trans_worker.isRunning():
            self.trans_worker.terminate()
            self.trans_worker.wait()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = AppController()
    app.aboutToQuit.connect(controller.cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
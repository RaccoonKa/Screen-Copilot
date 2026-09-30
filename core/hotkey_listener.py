import ctypes
from ctypes import wintypes
from PyQt6 import QtCore, QtWidgets
from config import HOTKEY

HOTKEY_ID = 9001
MOD_MAP = {
    "ctrl": 0x0002,
    "control": 0x0002,
    "alt": 0x0001,
    "shift": 0x0004,
    "win": 0x0008
}

def parse_hotkey(hotkey_str: str):
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    mods = 0x4000
    key_code = 0
    for part in parts:
        if part in MOD_MAP:
            mods |= MOD_MAP[part]
        elif len(part) == 1:
            key_code = ord(part.upper())
        elif part.startswith("f") and part[1:].isdigit():
            key_code = 0x70 + int(part[1:]) - 1
    return mods, key_code

class HotkeyFilter(QtCore.QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return False, 0

class HotkeyListener(QtCore.QObject):
    triggered = QtCore.pyqtSignal()

    def __init__(self, hotkey: str = HOTKEY):
        super().__init__()
        self.hotkey = hotkey
        self.filter = None
        self.is_registered = False

    def start(self):
        if not self.is_registered:
            mods, vk = parse_hotkey(self.hotkey)
            user32 = ctypes.windll.user32
            user32.RegisterHotKey(None, HOTKEY_ID, mods, vk)
            self.filter = HotkeyFilter(self.triggered.emit)
            QtWidgets.QApplication.instance().installNativeEventFilter(self.filter)
            self.is_registered = True

    def stop(self):
        if self.is_registered:
            user32 = ctypes.windll.user32
            user32.UnregisterHotKey(None, HOTKEY_ID)
            if self.filter:
                QtWidgets.QApplication.instance().removeNativeEventFilter(self.filter)
            self.is_registered = False
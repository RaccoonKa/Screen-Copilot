import os
import ctypes
from ctypes import wintypes
import psutil
from config import TARGET_IDES

user32 = ctypes.windll.user32


def get_foreground_process_name() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    if pid.value == os.getpid():
        return "self"

    try:
        proc = psutil.Process(pid.value)
        return proc.name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def is_ide_focused() -> bool:
    proc_name = get_foreground_process_name()
    if proc_name == "self":
        return True
    target_set = {name.lower() for name in TARGET_IDES}
    return proc_name in target_set
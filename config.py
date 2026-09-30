import os

HOTKEY = "ctrl+alt+x"

TARGET_IDES = {
    "pycharm64.exe",
    "code.exe",
    "bds.exe",
    "rider64.exe",
    "devenv.exe"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models", "moondream2")

DEFAULT_PROMPT = (
    "Ты — ассистент разработчика. "
    "Внимательно изучи изображение с кодом или ошибкой. "
    "Кратко объясни причину проблемы и напиши готовое исправление."
)
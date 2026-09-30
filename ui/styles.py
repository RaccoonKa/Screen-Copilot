from enum import Enum
from PyQt6.QtGui import QColor


class SelectionMode(Enum):
    RECT = 0
    LASSO = 1


OVERLAY_BG = QColor(10, 12, 18, 160)
BORDER_COLOR_START = QColor(0, 242, 255)
BORDER_COLOR_MID = QColor(138, 43, 226)
BORDER_COLOR_END = QColor(187, 0, 255)
SELECTION_BORDER_WIDTH = 3
CORNER_RADIUS = 8

RESULT_CARD_STYLE = """
QTextBrowser {
    background: transparent;
    border: none;
    font-family: 'Consolas', 'Segoe UI', monospace;
    font-size: 13px;
    color: #E0E0E0;
}
QPushButton#CloseBtn {
    background: transparent;
    border: none;
    color: #888899;
    font-size: 13px;
    padding: 0px;
}
QPushButton#CloseBtn:hover {
    color: #FF5555;
}
QLineEdit {
    background-color: rgba(28, 31, 40, 220);
    border: 1px solid rgba(80, 90, 115, 160);
    border-radius: 8px;
    padding: 6px 12px;
    color: #ECEFF4;
    font-size: 13px;
    selection-background-color: #00F2FF;
}
QLineEdit:focus {
    border: 1px solid #00F2FF;
    background-color: rgba(32, 36, 48, 240);
}
QPushButton#SendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F2FF, stop:1 #7000FF);
    border: none;
    border-radius: 8px;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: bold;
    padding: 6px 12px;
}
QPushButton#SendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2BF6FF, stop:1 #8B2BFF);
}
QPushButton#SendBtn:disabled {
    background: rgba(60, 65, 80, 120);
    color: #666A7A;
}
QPushButton#TranslateBtn {
    background-color: rgba(45, 52, 70, 180);
    border: 1px solid rgba(0, 242, 255, 120);
    border-radius: 6px;
    color: #00F2FF;
    font-size: 11px;
    font-weight: bold;
    padding: 2px 10px;
}
QPushButton#TranslateBtn:hover {
    background-color: rgba(0, 242, 255, 40);
    border: 1px solid #00F2FF;
}
QPushButton#TranslateBtn:disabled {
    background-color: rgba(35, 40, 52, 120);
    border: 1px solid rgba(80, 90, 115, 80);
    color: #555A6B;
}
QPushButton#ActionBtn {
    background-color: rgba(35, 40, 55, 200);
    border: 1px solid rgba(80, 95, 125, 160);
    border-radius: 6px;
    color: #D8DEE9;
    font-size: 11px;
    padding: 4px 10px;
}
QPushButton#ActionBtn:hover {
    border: 1px solid #00F2FF;
    color: #00F2FF;
    background-color: rgba(0, 242, 255, 25);
}
QPushButton#ActionBtn:disabled {
    color: #555A6B;
    border-color: rgba(50, 55, 70, 120);
}
QPushButton#PrimaryActionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F2FF, stop:1 #7000FF);
    border: none;
    border-radius: 6px;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: bold;
    padding: 4px 12px;
}
QPushButton#PrimaryActionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2BF6FF, stop:1 #8B2BFF);
}
QPushButton#PrimaryActionBtn:disabled {
    background: rgba(50, 55, 70, 120);
    color: #555A6B;
}
"""
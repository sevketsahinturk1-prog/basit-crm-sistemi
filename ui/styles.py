"""
Uygulama geneli QSS stilleri — açık ve koyu tema.

Yuvarlatılmış kontroller ve yumuşak palet ile minimalist görünüm.
"""

from __future__ import annotations

from typing import Literal

ThemeName = Literal["light", "dark"]


def uygulama_stili(tema: ThemeName) -> str:
    """
    PyQt5 için tam stil sayfası döndürür.

    Args:
        tema: 'light' veya 'dark'.

    Returns:
        QApplication.setStyleSheet için QSS metni.
    """
    if tema == "dark":
        return _DARK_QSS
    return _LIGHT_QSS


# Ortak ölçüler
_RADIUS = "14px"
_BTN_PAD = "10px 20px"

_LIGHT_QSS = f"""
QMainWindow, QDialog {{
    background-color: #f4f6fb;
    color: #1a1d26;
}}
QWidget#Card {{
    background-color: #ffffff;
    border-radius: {_RADIUS};
    border: 1px solid #e2e6ef;
}}
QLabel#CardTitle {{
    color: #6b7280;
    font-size: 11px;
    letter-spacing: 0.5px;
}}
QLabel#CardValue {{
    color: #111827;
    font-size: 22px;
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid #e2e6ef;
    border-radius: {_RADIUS};
    background: #ffffff;
    top: -1px;
}}
QTabBar::tab {{
    background: #eef1f7;
    color: #4b5563;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    min-width: 88px;
}}
QTabBar::tab:selected {{
    background: #ffffff;
    color: #2563eb;
    font-weight: 600;
    border-bottom: 2px solid #2563eb;
}}
QPushButton {{
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: {_BTN_PAD};
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #1d4ed8;
}}
QPushButton:pressed {{
    background-color: #1e40af;
}}
QPushButton#Secondary {{
    background-color: #e5e7eb;
    color: #374151;
}}
QPushButton#Secondary:hover {{
    background-color: #d1d5db;
}}
QPushButton#Danger {{
    background-color: #ef4444;
}}
QPushButton#Danger:hover {{
    background-color: #dc2626;
}}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 8px 12px;
    background: #ffffff;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid #2563eb;
}}
QTableWidget {{
    gridline-color: #e5e7eb;
    background: #ffffff;
    alternate-background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}}
QHeaderView::section {{
    background: #f3f4f6;
    color: #374151;
    padding: 8px;
    border: none;
    font-weight: 600;
}}
QScrollBar:vertical {{
    width: 10px;
    background: #f3f4f6;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #c7cad1;
    min-height: 28px;
    border-radius: 5px;
}}
QGroupBox {{
    font-weight: 600;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
"""

_DARK_QSS = f"""
QMainWindow, QDialog {{
    background-color: #12141a;
    color: #e8eaef;
}}
QWidget#Card {{
    background-color: #1c1f28;
    border-radius: {_RADIUS};
    border: 1px solid #2a2f3d;
}}
QLabel#CardTitle {{
    color: #9ca3af;
    font-size: 11px;
    letter-spacing: 0.5px;
}}
QLabel#CardValue {{
    color: #f3f4f6;
    font-size: 22px;
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid #2a2f3d;
    border-radius: {_RADIUS};
    background: #1c1f28;
    top: -1px;
}}
QTabBar::tab {{
    background: #252936;
    color: #9ca3af;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    min-width: 88px;
}}
QTabBar::tab:selected {{
    background: #1c1f28;
    color: #60a5fa;
    font-weight: 600;
    border-bottom: 2px solid #60a5fa;
}}
QPushButton {{
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: {_BTN_PAD};
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #2563eb;
}}
QPushButton:pressed {{
    background-color: #1d4ed8;
}}
QPushButton#Secondary {{
    background-color: #374151;
    color: #e5e7eb;
}}
QPushButton#Secondary:hover {{
    background-color: #4b5563;
}}
QPushButton#Danger {{
    background-color: #f87171;
    color: #111827;
}}
QPushButton#Danger:hover {{
    background-color: #ef4444;
    color: #ffffff;
}}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 8px 12px;
    background: #111318;
    color: #e8eaef;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid #60a5fa;
}}
QTableWidget {{
    gridline-color: #2a2f3d;
    background: #1c1f28;
    alternate-background-color: #22262f;
    border: 1px solid #2a2f3d;
    border-radius: 12px;
    color: #e8eaef;
}}
QHeaderView::section {{
    background: #252936;
    color: #d1d5db;
    padding: 8px;
    border: none;
    font-weight: 600;
}}
QScrollBar:vertical {{
    width: 10px;
    background: #1c1f28;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #4b5563;
    min-height: 28px;
    border-radius: 5px;
}}
QGroupBox {{
    font-weight: 600;
    border: 1px solid #374151;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 8px;
    color: #e8eaef;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
"""

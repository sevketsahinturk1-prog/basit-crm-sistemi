"""
Sevket CRM giriş noktası.

Çalıştırma (proje kökünden):

    python -m crm.main

Doğrudan bu dosyayı çalıştırırken (ör. ``python crm/main.py``) proje kökü
``sys.path`` üzerine eklenir; böylece ``crm`` paketi bulunur.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ``python crm/main.py`` ile çalıştırıldığında paket kökünü bul
_root = Path(__file__).resolve().parent.parent
_root_str = str(_root)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from PyQt5.QtWidgets import QApplication, QDialog

from crm.db.database import Database
from crm.ui.login_dialog import LoginDialog
from crm.ui.main_window import MainWindow
from crm.ui.styles import uygulama_stili


def main() -> int:
    """Uygulamayı başlatır: veritabanı, giriş, ana pencere."""
    app = QApplication(sys.argv)
    app.setApplicationName("Sevket CRM")
    app.setStyle("Fusion")

    db = Database()
    db.init_schema()
    db.seed_if_empty()

    app.setStyleSheet(uygulama_stili("light"))

    giris = LoginDialog(db)
    if giris.exec_() != QDialog.Accepted:
        return 0

    pencere = MainWindow(db)
    pencere.show()
    kod = app.exec_()
    db.close()
    return int(kod)


if __name__ == "__main__":
    raise SystemExit(main())

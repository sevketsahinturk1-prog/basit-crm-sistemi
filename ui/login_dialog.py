"""Basit yönetici girişi — kimlik doğrulama sonrası ana pencereye geçiş."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from crm.db.auth import kullanici_dogrula
from crm.db.database import Database


class LoginDialog(QDialog):
    """
    Tek kullanıcılı basit giriş diyaloğu.

    Varsayılan (ilk kurulum): kullanıcı `admin`, şifre `admin123`.
    """

    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("Sevket CRM — Giriş")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._kur()

    def _kur(self) -> None:
        title = QLabel("Yönetici Paneli")
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignCenter)

        hint = QLabel("Devam etmek için oturum açın.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: palette(mid);")

        self._user = QLineEdit()
        self._user.setPlaceholderText("Kullanıcı adı")
        self._pass = QLineEdit()
        self._pass.setPlaceholderText("Şifre")
        self._pass.setEchoMode(QLineEdit.Password)
        # Enter'a basıldığında (özellikle şifre alanında) giriş denensin.
        self._user.returnPressed.connect(self._dene)
        self._pass.returnPressed.connect(self._dene)

        form = QFormLayout()
        form.addRow("Kullanıcı", self._user)
        form.addRow("Şifre", self._pass)

        btn_ok = QPushButton("Giriş Yap")
        btn_ok.clicked.connect(self._dene)
        btn_ok.setDefault(True)
        btn_cancel = QPushButton("Çıkış")
        btn_cancel.setObjectName("Secondary")
        btn_cancel.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addWidget(hint)
        root.addSpacing(12)
        root.addLayout(form)
        root.addSpacing(8)

        self._user.setText("admin")

    def _dene(self) -> None:
        u = self._user.text().strip()
        p = self._pass.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Eksik bilgi", "Kullanıcı adı ve şifre girin.")
            return
        try:
            ok = kullanici_dogrula(self._db, u, p)
        except Exception as e:
            # Konsol görünmüyorsa kullanıcı hatayı göremeyebilir; bu yüzden burada mesaj gösteriyoruz.
            QMessageBox.critical(self, "Hata", f"Kimlik doğrulama sırasında beklenmeyen hata: {e}")
            return

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Kullanıcı adı veya şifre hatalı.")

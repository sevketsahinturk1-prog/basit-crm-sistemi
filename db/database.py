"""
SQLite bağlantısı ve şema yönetimi.

Uygulama verileri kullanıcı dizininde `crm_data.sqlite` dosyasında saklanır.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    """Uygulama veritabanı dosyasının tam yolunu döndürür."""
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SevketCRM"
    base.mkdir(parents=True, exist_ok=True)
    return base / "crm_data.sqlite"


class Database:
    """
    Tekil SQLite bağlantısı; context manager ile güvenli kullanım.

    Attributes:
        path: Veritabanı dosya yolu.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or get_db_path()
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Bağlantıyı açar ve satır fabrikasını ayarlar."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        """Bağlantıyı kapatır."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> sqlite3.Connection:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        # Bağlantıyı dışarıda da kullanılabilsin diye burada kapatmıyoruz;
        # close() ile kapatılır.

    def init_schema(self) -> None:
        """Tabloları oluşturur; yoksa atlar."""
        conn = self.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kullanici (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
                sifre_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS musteri (
                musteri_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                telefon TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS satis (
                satis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun TEXT NOT NULL,
                kategori TEXT NOT NULL DEFAULT '',
                adet INTEGER NOT NULL DEFAULT 1,
                fiyat REAL NOT NULL,
                musteri_id INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                FOREIGN KEY (musteri_id) REFERENCES musteri(musteri_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS destek_talebi (
                talep_id INTEGER PRIMARY KEY AUTOINCREMENT,
                aciklama TEXT NOT NULL,
                musteri_id INTEGER NOT NULL,
                durum TEXT NOT NULL DEFAULT 'Açık',
                FOREIGN KEY (musteri_id) REFERENCES musteri(musteri_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_satis_tarih ON satis(tarih);
            CREATE INDEX IF NOT EXISTS idx_musteri_ad ON musteri(ad);
            """
        )
        conn.commit()
        self.migrate_satis_columns()

    def migrate_satis_columns(self) -> None:
        """Eski veritabanlarına kategori ve adet sütunlarını ekler."""
        conn = self.connect()
        names = {row["name"] for row in conn.execute("PRAGMA table_info(satis)")}
        if "kategori" not in names:
            conn.execute(
                "ALTER TABLE satis ADD COLUMN kategori TEXT NOT NULL DEFAULT ''"
            )
        if "adet" not in names:
            conn.execute(
                "ALTER TABLE satis ADD COLUMN adet INTEGER NOT NULL DEFAULT 1"
            )
        conn.commit()

    def seed_if_empty(self) -> None:
        """İlk kurulumda varsayılan admin ve örnek veri ekler."""
        conn = self.connect()
        cur = conn.execute("SELECT COUNT(*) AS c FROM kullanici")
        if cur.fetchone()["c"] > 0:
            return

        default_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        conn.execute(
            "INSERT INTO kullanici (kullanici_adi, sifre_hash) VALUES (?, ?)",
            ("admin", default_hash),
        )

        musteriler = [
            ("Ayşe Yılmaz", "0532 111 2233"),
            ("Mehmet Kaya", "0544 222 3344"),
            ("Zeynep Demir", "0555 333 4455"),
            ("Can Öztürk", "0533 444 5566"),
        ]
        conn.executemany(
            "INSERT INTO musteri (ad, telefon) VALUES (?, ?)", musteriler
        )

        cur = conn.execute("SELECT musteri_id, ad FROM musteri ORDER BY musteri_id")
        rows = list(cur.fetchall())
        if not rows:
            conn.commit()
            return

        today = datetime.now()
        ornek_satis = []
        for i, r in enumerate(rows):
            mid = r["musteri_id"]
            ornek_satis.extend(
                [
                    ("Lisans Paketi A", "Yazılım", 1, 12500.0 + i * 500, mid, (today - timedelta(days=14 - i)).isoformat(timespec="seconds")),
                    ("Danışmanlık 10s", "Hizmet", 10, 3500.0, mid, (today - timedelta(days=7 - i)).isoformat(timespec="seconds")),
                    ("Bakım Yıllık", "Abonelik", 1, 8900.0, mid, (today - timedelta(days=2)).isoformat(timespec="seconds")),
                ]
            )
        conn.executemany(
            """INSERT INTO satis (urun, kategori, adet, fiyat, musteri_id, tarih)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ornek_satis,
        )

        conn.execute(
            """INSERT INTO destek_talebi (aciklama, musteri_id, durum)
               VALUES (?, ?, 'Açık')""",
            ("Fatura PDF formatında gelmiyor.", rows[0]["musteri_id"]),
        )
        conn.execute(
            """INSERT INTO destek_talebi (aciklama, musteri_id, durum)
               VALUES (?, ?, 'Kapalı')""",
            ("Şifre sıfırlama talebi — çözüldü.", rows[1]["musteri_id"]),
        )
        conn.commit()

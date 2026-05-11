"""Dashboard ve özet istatistikler."""

from __future__ import annotations

from typing import Any, Dict

from crm.db.database import Database


def dashboard_ozet(db: Database) -> Dict[str, Any]:
    """
    Ana ekran kartları için özet sayıları döndürür.

    Returns:
        musteri_sayisi, satis_toplam, acik_destek keys.
    """
    conn = db.connect()
    m = conn.execute("SELECT COUNT(*) AS c FROM musteri").fetchone()["c"]
    s = conn.execute("SELECT COALESCE(SUM(fiyat * adet), 0) AS t FROM satis").fetchone()["t"]
    d = conn.execute(
        "SELECT COUNT(*) AS c FROM destek_talebi WHERE durum = ?",
        ("Açık",),
    ).fetchone()["c"]
    return {
        "musteri_sayisi": int(m),
        "satis_toplam": float(s),
        "acik_destek": int(d),
    }

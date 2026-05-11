"""Basit kullanıcı doğrulama (SHA-256 hash)."""

from __future__ import annotations

import hashlib

from crm.db.database import Database


def sifre_hash_olustur(duz_metin: str) -> str:
    """Düz metin şifreyi SHA-256 hex stringe çevirir."""
    return hashlib.sha256(duz_metin.encode("utf-8")).hexdigest()


def kullanici_dogrula(db: Database, kullanici_adi: str, sifre: str) -> bool:
    """
    Kullanıcı adı ve şifre doğruysa True döner.

    Args:
        db: Veritabanı örneği.
        kullanici_adi: Giriş adı.
        sifre: Düz metin şifre.

    Returns:
        Kimlik bilgileri eşleşiyorsa True.
    """
    conn = db.connect()
    row = conn.execute(
        "SELECT sifre_hash FROM kullanici WHERE kullanici_adi = ?",
        (kullanici_adi.strip(),),
    ).fetchone()
    if row is None:
        return False
    return row["sifre_hash"] == sifre_hash_olustur(sifre)

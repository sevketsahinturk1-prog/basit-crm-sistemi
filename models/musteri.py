"""Müşteri varlığı ve CRUD işlemleri."""

from __future__ import annotations

from typing import Any, List, Optional

from crm.db.database import Database


class Musteri:
    """
    Müşteri kaydı ve veritabanı işlemleri.

    Attributes:
        musteri_id: Birincil anahtar (yeni kayıtta None olabilir).
        ad: Müşteri adı soyadı.
        telefon: İletişim telefonu.
    """

    def __init__(
        self,
        db: Database,
        ad: str = "",
        telefon: str = "",
        musteri_id: Optional[int] = None,
    ) -> None:
        self._db = db
        self.musteri_id = musteri_id
        self.ad = ad
        self.telefon = telefon

    def musteri_ekle(self, ad: Optional[str] = None, telefon: Optional[str] = None) -> int:
        """
        Yeni müşteri ekler.

        Args:
            ad: İsim; None ise örnek öznitelik kullanılır.
            telefon: Telefon; None ise örnek öznitelik kullanılır.

        Returns:
            Oluşan musteri_id.
        """
        a = (ad if ad is not None else self.ad).strip()
        t = (telefon if telefon is not None else self.telefon).strip()
        conn = self._db.connect()
        cur = conn.execute(
            "INSERT INTO musteri (ad, telefon) VALUES (?, ?)",
            (a, t),
        )
        conn.commit()
        self.musteri_id = int(cur.lastrowid)
        self.ad, self.telefon = a, t
        return self.musteri_id

    def musteri_sil(self, musteri_id: Optional[int] = None) -> None:
        """Müşteriyi ve ilişkili satış/talepleri (CASCADE) siler."""
        mid = musteri_id if musteri_id is not None else self.musteri_id
        if mid is None:
            raise ValueError("musteri_id gerekli")
        conn = self._db.connect()
        conn.execute("DELETE FROM musteri WHERE musteri_id = ?", (mid,))
        conn.commit()

    def musteri_guncelle(
        self,
        musteri_id: Optional[int] = None,
        ad: Optional[str] = None,
        telefon: Optional[str] = None,
    ) -> None:
        """Müşteri bilgisini günceller."""
        mid = musteri_id if musteri_id is not None else self.musteri_id
        if mid is None:
            raise ValueError("musteri_id gerekli")
        a = ad if ad is not None else self.ad
        t = telefon if telefon is not None else self.telefon
        conn = self._db.connect()
        conn.execute(
            "UPDATE musteri SET ad = ?, telefon = ? WHERE musteri_id = ?",
            (a.strip(), t.strip(), mid),
        )
        conn.commit()
        if self.musteri_id == mid:
            self.ad, self.telefon = a.strip(), t.strip()

    def musteri_listele(self, arama: Optional[str] = None) -> List[dict[str, Any]]:
        """
        Müşterileri listeler; isteğe bağlı canlı arama (ad veya telefon).

        Args:
            arama: Alt string eşleşmesi (case-insensitive).

        Returns:
            Sözlük listesi (musteri_id, ad, telefon).
        """
        conn = self._db.connect()
        if arama and arama.strip():
            like = f"%{arama.strip()}%"
            cur = conn.execute(
                """SELECT musteri_id, ad, telefon FROM musteri
                   WHERE ad LIKE ? COLLATE NOCASE OR telefon LIKE ? COLLATE NOCASE
                   ORDER BY ad COLLATE NOCASE""",
                (like, like),
            )
        else:
            cur = conn.execute(
                "SELECT musteri_id, ad, telefon FROM musteri ORDER BY ad COLLATE NOCASE"
            )
        return [dict(r) for r in cur.fetchall()]

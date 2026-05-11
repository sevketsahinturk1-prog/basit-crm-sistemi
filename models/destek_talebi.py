"""Destek talebi yaşam döngüsü."""

from __future__ import annotations

from typing import Any, List, Optional

from crm.db.database import Database


class DestekTalebi:
    """
    Destek talebi.

    Attributes:
        talep_id: Birincil anahtar.
        aciklama: Talep metni.
        musteri_id: İlişkili müşteri.
        durum: 'Açık' veya 'Kapalı'.
    """

    DURUM_ACIK = "Açık"
    DURUM_KAPALI = "Kapalı"

    def __init__(
        self,
        db: Database,
        aciklama: str = "",
        musteri_id: Optional[int] = None,
        durum: str = DURUM_ACIK,
        talep_id: Optional[int] = None,
    ) -> None:
        self._db = db
        self.talep_id = talep_id
        self.aciklama = aciklama
        self.musteri_id = musteri_id
        self.durum = durum

    def talep_olustur(
        self,
        aciklama: Optional[str] = None,
        musteri_id: Optional[int] = None,
    ) -> int:
        """
        Yeni açık talep oluşturur.

        Returns:
            talep_id.
        """
        ac = (aciklama if aciklama is not None else self.aciklama).strip()
        mid = musteri_id if musteri_id is not None else self.musteri_id
        if mid is None:
            raise ValueError("musteri_id gerekli")
        conn = self._db.connect()
        cur = conn.execute(
            """INSERT INTO destek_talebi (aciklama, musteri_id, durum)
               VALUES (?, ?, ?)""",
            (ac, mid, self.DURUM_ACIK),
        )
        conn.commit()
        self.talep_id = int(cur.lastrowid)
        self.aciklama, self.musteri_id, self.durum = ac, mid, self.DURUM_ACIK
        return self.talep_id

    def talep_kapat(self, talep_id: Optional[int] = None) -> None:
        """Talebi Kapalı durumuna alır."""
        tid = talep_id if talep_id is not None else self.talep_id
        if tid is None:
            raise ValueError("talep_id gerekli")
        conn = self._db.connect()
        conn.execute(
            "UPDATE destek_talebi SET durum = ? WHERE talep_id = ?",
            (self.DURUM_KAPALI, tid),
        )
        conn.commit()
        if self.talep_id == tid:
            self.durum = self.DURUM_KAPALI

    def talep_listele(
        self,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        """
        Talepleri müşteri adı ile listeler.

        Args:
            durum: 'Açık', 'Kapalı' veya None (tümü).
            arama: Açıklama veya müşteri adında alt string araması.

        Returns:
            talep_id, aciklama, musteri_id, durum, musteri_ad.
        """
        conn = self._db.connect()
        sql = """
            SELECT d.talep_id, d.aciklama, d.musteri_id, d.durum, m.ad AS musteri_ad
            FROM destek_talebi d
            JOIN musteri m ON m.musteri_id = d.musteri_id
            WHERE 1=1
        """
        params: List[Any] = []
        if durum:
            sql += " AND d.durum = ?"
            params.append(durum)
        if arama and arama.strip():
            like = f"%{arama.strip()}%"
            sql += " AND (d.aciklama LIKE ? COLLATE NOCASE OR m.ad LIKE ? COLLATE NOCASE)"
            params.extend((like, like))
        sql += " ORDER BY d.talep_id DESC"
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

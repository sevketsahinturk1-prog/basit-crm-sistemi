"""Satış kayıtları ve listeleme (tek günlük satış tarihi filtresi ile)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, List, Optional

from crm.db.database import Database


class Satis:
    """
    Satış varlığı.

    Attributes:
        satis_id: Birincil anahtar.
        urun: Ürün veya hizmet adı.
        kategori: Ürün kategorisi.
        adet: Satılan adet.
        fiyat: Tutar (satır toplamı veya birim; burada kaydedilen tutar).
        musteri_id: İlişkili müşteri.
        tarih: ISO format tarih-saat.
    """

    def __init__(
        self,
        db: Database,
        urun: str = "",
        kategori: str = "",
        adet: int = 1,
        fiyat: float = 0.0,
        musteri_id: Optional[int] = None,
        tarih: Optional[datetime] = None,
        satis_id: Optional[int] = None,
    ) -> None:
        self._db = db
        self.satis_id = satis_id
        self.urun = urun
        self.kategori = kategori
        self.adet = int(adet)
        self.fiyat = float(fiyat)
        self.musteri_id = musteri_id
        self.tarih = tarih or datetime.now()

    def satis_ekle(
        self,
        urun: Optional[str] = None,
        fiyat: Optional[float] = None,
        musteri_id: Optional[int] = None,
        tarih: Optional[datetime] = None,
        kategori: Optional[str] = None,
        adet: Optional[int] = None,
    ) -> int:
        """
        Yeni satış ekler.

        Args:
            urun: Ürün adı.
            fiyat: Tutar.
            musteri_id: Müşteri FK.
            tarih: Satış anı; None ise örnek öznitelik.
            kategori: Ürün kategorisi; boş bırakılabilir.
            adet: Adet; None veya <1 ise 1 kabul edilir.

        Returns:
            satis_id.
        """
        u = (urun if urun is not None else self.urun).strip()
        kat = (kategori if kategori is not None else self.kategori).strip()
        ad = int(adet if adet is not None else self.adet)
        if ad < 1:
            ad = 1
        f = float(fiyat if fiyat is not None else self.fiyat)
        mid = musteri_id if musteri_id is not None else self.musteri_id
        if mid is None:
            raise ValueError("musteri_id gerekli")
        dt = tarih if tarih is not None else self.tarih
        ts = dt.isoformat(timespec="seconds") if isinstance(dt, datetime) else str(dt)
        conn = self._db.connect()
        cur = conn.execute(
            """INSERT INTO satis (urun, kategori, adet, fiyat, musteri_id, tarih)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (u, kat, ad, f, mid, ts),
        )
        conn.commit()
        self.satis_id = int(cur.lastrowid)
        self.urun, self.kategori, self.adet = u, kat, ad
        self.fiyat, self.musteri_id = f, mid
        self.tarih = dt if isinstance(dt, datetime) else datetime.fromisoformat(ts)
        return self.satis_id

    def satis_listele(
        self,
        satis_baslangic: Optional[datetime] = None,
        satis_bitis: Optional[datetime] = None,
        musteri_id: Optional[int] = None,
        arama: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        """
        Satışları müşteri adı ile birlikte listeler.

        Args:
            satis_baslangic: Verilirse bu tarihten sonra (takvim günü sınırlarında) olan satışlar.
            satis_bitis: Verilirse bu tarihten önce (takvim günü sınırlarında) olan satışlar.
            musteri_id: Sadece bu müşteri.
            arama: Ürün, kategori veya müşteri adında alt string araması.

        Returns:
            satis_id, urun, kategori, adet, fiyat, musteri_id, tarih, musteri_ad.
        """
        conn = self._db.connect()
        sql = """
            SELECT s.satis_id, s.urun, s.kategori, s.adet, s.fiyat, s.musteri_id,
                   s.tarih, m.ad AS musteri_ad
            FROM satis s
            JOIN musteri m ON m.musteri_id = s.musteri_id
            WHERE 1=1
        """
        params: List[Any] = []
        if satis_baslangic is not None:
            if isinstance(satis_baslangic, datetime):
                d = satis_baslangic.date()
            elif isinstance(satis_baslangic, date):
                d = satis_baslangic
            else:
                raise TypeError("satis_baslangic datetime veya date olmalıdır")
            bas = datetime.combine(d, time.min)
            sql += " AND s.tarih >= ?"
            params.append(bas.isoformat(timespec="seconds"))

        if satis_bitis is not None:
            if isinstance(satis_bitis, datetime):
                d = satis_bitis.date()
            elif isinstance(satis_bitis, date):
                d = satis_bitis
            else:
                raise TypeError("satis_bitis datetime veya date olmalıdır")
            bit = datetime.combine(d, time.max)
            sql += " AND s.tarih <= ?"
            params.append(bit.isoformat(timespec="seconds"))
        if musteri_id is not None:
            sql += " AND s.musteri_id = ?"
            params.append(musteri_id)
        if arama and arama.strip():
            like = f"%{arama.strip()}%"
            sql += """ AND (
                s.urun LIKE ? COLLATE NOCASE OR
                s.kategori LIKE ? COLLATE NOCASE OR
                m.ad LIKE ? COLLATE NOCASE
            )"""
            params.extend((like, like, like))
        sql += " ORDER BY s.tarih DESC"
        cur = conn.execute(sql, params)
        rows = []
        for r in cur.fetchall():
            dct = dict(r)
            if dct.get("kategori") is None:
                dct["kategori"] = ""
            if dct.get("adet") is None:
                dct["adet"] = 1

            # DB'de `fiyat` birim fiyat olarak saklanıyor; tabloda ve grafikte satır toplamı gösteriyoruz.
            try:
                dct["fiyat"] = float(dct.get("fiyat") or 0.0) * int(dct.get("adet") or 1)
            except Exception:
                # Güvenlik: veri bozulursa en azından sıfır gösterelim.
                dct["fiyat"] = 0.0
            rows.append(dct)
        return rows

    @staticmethod
    def toplam_ciro(
        db: Database,
        baslangic: Optional[datetime] = None,
        bitis: Optional[datetime] = None,
    ) -> float:
        """Verilen aralıkta toplam satış tutarı (dashboard için tümü: parametresiz)."""
        conn = db.connect()
        sql = "SELECT COALESCE(SUM(fiyat * adet), 0) AS t FROM satis WHERE 1=1"
        params: List[Any] = []
        if baslangic is not None:
            sql += " AND tarih >= ?"
            params.append(baslangic.isoformat(timespec="seconds"))
        if bitis is not None:
            sql += " AND tarih <= ?"
            params.append(bitis.isoformat(timespec="seconds"))
        row = conn.execute(sql, params).fetchone()
        return float(row["t"] if row else 0.0)

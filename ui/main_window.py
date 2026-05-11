"""Ana pencere: dashboard, sekmeler, arama, tema ve grafik."""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional, Tuple

from PyQt5.QtCore import QDate, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from crm.db.database import Database
from crm.models.destek_talebi import DestekTalebi
from crm.models.musteri import Musteri
from crm.models.satis import Satis
from crm.services.stats import dashboard_ozet
from crm.ui.chart_widget import SatisGrafikWidget
from crm.ui.styles import ThemeName, uygulama_stili


def _para_metni(tutar: float) -> str:
    """Tutarı okunaklı metne çevirir."""
    return f"{tutar:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")


class MainWindow(QMainWindow):
    """
    CRM ana arayüzü: özet kartlar, sekmeli modüller, canlı arama ve tema.

    Katmanlar: bu sınıf yalnızca UI ve kullanıcı etkileşimi; iş kuralları model
    sınıflarında, kalıcılık SQLite üzerinden `Database` ile yönetilir.
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db
        self._musteri = Musteri(db)
        self._satis = Satis(db)
        self._destek = DestekTalebi(db)
        self._tema: ThemeName = "light"

        self.setWindowTitle("Sevket CRM")
        self.setMinimumSize(1080, 700)
        self.resize(1280, 800)

        self._kart_musteri_val: Optional[QLabel] = None
        self._kart_satis_val: Optional[QLabel] = None
        self._kart_destek_val: Optional[QLabel] = None
        self._arama: Optional[QLineEdit] = None
        self._tabs: Optional[QTabWidget] = None
        self._tablo_musteri: Optional[QTableWidget] = None
        self._tablo_satis: Optional[QTableWidget] = None
        self._tablo_destek: Optional[QTableWidget] = None
        self._grafik: Optional[SatisGrafikWidget] = None
        self._satis_tarih: Optional[QDateEdit] = None
        self._liste_tarih_baslangic: Optional[QDateEdit] = None
        self._liste_tarih_bitis: Optional[QDateEdit] = None
        self._combo_musteri_satis: Optional[QComboBox] = None
        self._combo_musteri_destek: Optional[QComboBox] = None
        self._filtre_destek: Optional[QComboBox] = None
        self._btn_tema: Optional[QPushButton] = None

        self._m_ad = QLineEdit()
        self._m_tel = QLineEdit()
        self._s_kategori = QLineEdit()
        self._s_urun = QLineEdit()
        self._s_adet = QSpinBox()
        self._s_adet.setMinimum(1)
        self._s_adet.setMaximum(999_999)
        self._s_adet.setValue(1)
        self._s_fiyat = QDoubleSpinBox()
        self._s_fiyat.setMaximum(1e9)
        self._s_fiyat.setDecimals(2)
        self._s_fiyat.setPrefix("₺ ")
        self._d_aciklama = QTextEdit()
        self._d_aciklama.setMaximumHeight(90)

        self._timer_arama = QTimer(self)
        self._timer_arama.setSingleShot(True)
        self._timer_arama.setInterval(180)
        self._timer_arama.timeout.connect(self._arama_yenile)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(14)
        root.setContentsMargins(20, 18, 20, 18)

        root.addLayout(self._ust_bant())
        root.addWidget(self._dashboard_kartlari())
        root.addLayout(self._arama_satiri())
        root.addWidget(self._sekmeler(), stretch=1)
        self._sekme_degisti(0)

        self._uygula_tema()
        self._musteri_combolarini_doldur()
        self._varsayilan_tarihler()
        self.yenile_hepsi()

    def _ust_bant(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        baslik = QLabel("Sevket CRM")
        f = QFont()
        f.setPointSize(18)
        f.setBold(True)
        baslik.setFont(f)
        alt = QLabel("Müşteri · Satış · Destek")
        alt.setStyleSheet("color: palette(mid);")
        v = QVBoxLayout()
        v.addWidget(baslik)
        v.addWidget(alt)
        w = QWidget()
        w.setLayout(v)

        self._btn_tema = QPushButton("Koyu tema")
        self._btn_tema.setObjectName("Secondary")
        self._btn_tema.clicked.connect(self._tema_degistir)

        lay.addWidget(w)
        lay.addStretch()
        lay.addWidget(self._btn_tema)
        return lay

    def _dashboard_kartlari(self) -> QWidget:
        grid = QGridLayout()
        grid.setSpacing(12)

        def kart(baslik: str) -> Tuple[QWidget, QLabel]:
            w = QWidget()
            w.setObjectName("Card")
            lay = QVBoxLayout(w)
            lay.setContentsMargins(18, 16, 18, 16)
            t = QLabel(baslik.upper())
            t.setObjectName("CardTitle")
            v = QLabel("—")
            v.setObjectName("CardValue")
            lay.addWidget(t)
            lay.addWidget(v)
            return w, v

        w1, self._kart_musteri_val = kart("Toplam müşteri")
        w2, self._kart_satis_val = kart("Toplam satış")
        w3, self._kart_destek_val = kart("Açık destek talepleri")

        grid.addWidget(w1, 0, 0)
        grid.addWidget(w2, 0, 1)
        grid.addWidget(w3, 0, 2)
        for c in range(3):
            grid.setColumnStretch(c, 1)

        wrap = QWidget()
        wrap.setLayout(grid)
        return wrap

    def _arama_satiri(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        self._arama = QLineEdit()
        self._arama.setPlaceholderText("Canlı ara: sekme içeriğine göre filtreler")
        self._arama.textChanged.connect(self._arama_zamanla)
        yenile = QPushButton("Yenile")
        yenile.setObjectName("Secondary")
        yenile.clicked.connect(self.yenile_hepsi)
        lay.addWidget(QLabel("Ara:"))
        lay.addWidget(self._arama, stretch=1)
        lay.addWidget(yenile)
        return lay

    def _arama_zamanla(self) -> None:
        self._timer_arama.start()

    def _arama_yenile(self) -> None:
        idx = self._tabs.currentIndex() if self._tabs else 0
        if idx == 0:
            self._musteri_tablosu_doldur()
        elif idx == 1:
            self._satis_sekmesi_yenile()
        else:
            self._destek_tablosu_doldur()

    def _sekmeler(self) -> QTabWidget:
        self._tabs = QTabWidget()
        self._tabs.addTab(self._sekme_musteri(), "Müşteriler")
        self._tabs.addTab(self._sekme_satis(), "Satışlar")
        self._tabs.addTab(self._sekme_destek(), "Destek Talepleri")
        self._tabs.currentChanged.connect(self._sekme_degisti)
        return self._tabs

    def _sekme_degisti(self, index: int) -> None:
        if not self._arama:
            return
        if index == 0:
            self._arama.setPlaceholderText("İsim veya telefon ile canlı ara…")
        elif index == 1:
            self._arama.setPlaceholderText("Ürün veya müşteri adı ile ara…")
        else:
            self._arama.setPlaceholderText("Açıklama veya müşteri adı ile ara…")
        self._arama_yenile()

    def _sekme_musteri(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        form = QGroupBox("Yeni / düzenle")
        fg = QGridLayout(form)
        self._m_ad.setPlaceholderText("Ad Soyad")
        self._m_tel.setPlaceholderText("Telefon")
        fg.addWidget(QLabel("Ad"), 0, 0)
        fg.addWidget(self._m_ad, 0, 1)
        fg.addWidget(QLabel("Telefon"), 0, 2)
        fg.addWidget(self._m_tel, 0, 3)
        btn_ekle = QPushButton("Ekle")
        btn_ekle.clicked.connect(self._musteri_ekle_ui)
        btn_guncelle = QPushButton("Güncelle")
        btn_guncelle.setObjectName("Secondary")
        btn_guncelle.clicked.connect(self._musteri_guncelle_ui)
        btn_sil = QPushButton("Sil")
        btn_sil.setObjectName("Danger")
        btn_sil.clicked.connect(self._musteri_sil_ui)
        fg.addWidget(btn_ekle, 1, 1)
        fg.addWidget(btn_guncelle, 1, 2)
        fg.addWidget(btn_sil, 1, 3)

        self._tablo_musteri = QTableWidget(0, 3)
        self._tablo_musteri.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Telefon"])
        self._tablo_musteri.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tablo_musteri.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tablo_musteri.setAlternatingRowColors(True)
        self._tablo_musteri.itemSelectionChanged.connect(self._musteri_secimden_form)

        lay.addWidget(form)
        lay.addWidget(self._tablo_musteri, stretch=1)
        return w

    def _sekme_satis(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        filt = QGroupBox("Satış filtresi ve yeni kayıt")
        fl = QGridLayout(filt)

        self._liste_tarih_baslangic = QDateEdit(calendarPopup=True)
        self._liste_tarih_baslangic.setDisplayFormat("d.MM.yyyy")
        self._liste_tarih_baslangic.dateChanged.connect(lambda *_: self._satis_sekmesi_yenile())

        self._liste_tarih_bitis = QDateEdit(calendarPopup=True)
        self._liste_tarih_bitis.setDisplayFormat("d.MM.yyyy")
        self._liste_tarih_bitis.dateChanged.connect(lambda *_: self._satis_sekmesi_yenile())

        self._satis_tarih = QDateEdit(calendarPopup=True)
        self._satis_tarih.setDisplayFormat("d.MM.yyyy")

        fl.addWidget(QLabel("Liste başlangıç"), 0, 0)
        fl.addWidget(self._liste_tarih_baslangic, 0, 1)
        fl.addWidget(QLabel("Yeni satış tarihi"), 0, 2)
        fl.addWidget(self._satis_tarih, 0, 3)

        fl.addWidget(QLabel("Liste bitiş"), 1, 0)
        fl.addWidget(self._liste_tarih_bitis, 1, 1)
        fl.addWidget(QLabel("(Liste + grafik bu aralığa göre)"), 1, 2, 1, 2)

        self._combo_musteri_satis = QComboBox()
        fl.addWidget(QLabel("Müşteri"), 2, 0)
        fl.addWidget(self._combo_musteri_satis, 2, 1, 1, 3)

        self._s_kategori.setPlaceholderText("Örn. Yazılım, Donanım")
        fl.addWidget(QLabel("Kategori"), 3, 0)
        fl.addWidget(self._s_kategori, 3, 1)
        fl.addWidget(QLabel("Adet"), 3, 2)
        fl.addWidget(self._s_adet, 3, 3)

        self._s_urun.setPlaceholderText("Ürün / hizmet adı")
        fl.addWidget(QLabel("Ürün"), 4, 0)
        fl.addWidget(self._s_urun, 4, 1)
        fl.addWidget(QLabel("Fiyat"), 4, 2)
        fl.addWidget(self._s_fiyat, 4, 3)
        btn_s = QPushButton("Satış kaydet")
        btn_s.clicked.connect(self._satis_ekle_ui)
        fl.addWidget(btn_s, 5, 3)

        # Form splitter dışında: liste + grafik için tüm dikey alan kalır
        lay.addWidget(filt)

        self._tablo_satis = QTableWidget(0, 7)
        self._tablo_satis.setHorizontalHeaderLabels(
            ["ID", "Tarih", "Kategori", "Ürün", "Adet", "Müşteri", "Tutar"]
        )
        self._tablo_satis.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._tablo_satis.setAlternatingRowColors(True)
        self._tablo_satis.setMinimumHeight(240)
        self._tablo_satis.verticalHeader().setDefaultSectionSize(26)

        self._grafik = SatisGrafikWidget()

        liste_kutu = QGroupBox("Satış listesi")
        lk = QVBoxLayout(liste_kutu)
        lk.setContentsMargins(8, 10, 8, 8)
        lk.addWidget(self._tablo_satis)

        grafik_kutu = QGroupBox("Günlük satış grafiği")
        gk = QVBoxLayout(grafik_kutu)
        gk.setContentsMargins(8, 10, 8, 8)
        gk.addWidget(self._grafik)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(liste_kutu)
        split.addWidget(grafik_kutu)
        split.setStretchFactor(0, 58)
        split.setStretchFactor(1, 42)
        split.setHandleWidth(8)
        split.setChildrenCollapsible(False)
        # Başlangıç oranı: tablo geniş, grafik okunaklı minimum genişlikte
        split.setSizes([720, 480])

        lay.addWidget(split, stretch=1)
        return w

    def _sekme_destek(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        form = QGroupBox("Yeni talep")
        fg = QGridLayout(form)
        self._combo_musteri_destek = QComboBox()
        fg.addWidget(QLabel("Müşteri"), 0, 0)
        fg.addWidget(self._combo_musteri_destek, 0, 1, 1, 3)
        fg.addWidget(QLabel("Açıklama"), 1, 0)
        fg.addWidget(self._d_aciklama, 1, 1, 1, 3)
        btn_t = QPushButton("Talep oluştur")
        btn_t.clicked.connect(self._destek_olustur_ui)
        fg.addWidget(btn_t, 2, 3)

        ctrl = QHBoxLayout()
        self._filtre_destek = QComboBox()
        self._filtre_destek.addItems(["Tümü", "Açık", "Kapalı"])
        self._filtre_destek.currentIndexChanged.connect(self._destek_tablosu_doldur)
        ctrl.addWidget(QLabel("Durum:"))
        ctrl.addWidget(self._filtre_destek)
        ctrl.addStretch()
        btn_kapat = QPushButton("Seçili talebi kapat")
        btn_kapat.setObjectName("Secondary")
        btn_kapat.clicked.connect(self._destek_kapat_ui)
        ctrl.addWidget(btn_kapat)

        self._tablo_destek = QTableWidget(0, 4)
        self._tablo_destek.setHorizontalHeaderLabels(["ID", "Müşteri", "Açıklama", "Durum"])
        self._tablo_destek.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._tablo_destek.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tablo_destek.setAlternatingRowColors(True)

        lay.addWidget(form)
        lay.addLayout(ctrl)
        lay.addWidget(self._tablo_destek, stretch=1)
        return w

    def _varsayilan_tarihler(self) -> None:
        d = QDate.currentDate()
        if self._satis_tarih:
            self._satis_tarih.setDate(d)
        if self._liste_tarih_baslangic:
            self._liste_tarih_baslangic.setDate(d)
        if self._liste_tarih_bitis:
            self._liste_tarih_bitis.setDate(d)

    def _musteri_combolarini_doldur(self) -> None:
        rows = self._musteri.musteri_listele()
        for cb in (self._combo_musteri_satis, self._combo_musteri_destek):
            if cb is None:
                continue
            cb.clear()
            for r in rows:
                cb.addItem(r["ad"], r["musteri_id"])

    def _liste_tarih_araligi(self) -> Tuple[datetime, datetime]:
        """Liste başlangıç/bitişini gün başı/gün sonu sınırlarıyla datetime'e çevirir."""
        bas_d = self._liste_tarih_baslangic.date().toPyDate()
        bit_d = self._liste_tarih_bitis.date().toPyDate()
        bas = datetime.combine(bas_d, time.min)
        bit = datetime.combine(bit_d, time.max)
        return bas, bit

    def _arama_metni(self) -> str:
        return self._arama.text().strip() if self._arama else ""

    def _musteri_tablosu_doldur(self) -> None:
        t = self._tablo_musteri
        if t is None:
            return
        arama = self._arama_metni()
        rows = self._musteri.musteri_listele(arama if arama else None)
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["musteri_id"])))
            t.setItem(i, 1, QTableWidgetItem(r["ad"]))
            t.setItem(i, 2, QTableWidgetItem(r["telefon"]))

    def _satis_sekmesi_yenile(self) -> None:
        bas, bit = self._liste_tarih_araligi()
        arama = self._arama_metni() if self._tabs and self._tabs.currentIndex() == 1 else ""
        rows = self._satis.satis_listele(
            satis_baslangic=bas,
            satis_bitis=bit,
            arama=arama if arama else None,
        )
        t = self._tablo_satis
        if t is None:
            return
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["satis_id"])))
            t.setItem(i, 1, QTableWidgetItem(str(r["tarih"])[:19].replace("T", " ")))
            t.setItem(i, 2, QTableWidgetItem(str(r.get("kategori") or "")))
            t.setItem(i, 3, QTableWidgetItem(r["urun"]))
            t.setItem(i, 4, QTableWidgetItem(str(int(r.get("adet") or 1))))
            t.setItem(i, 5, QTableWidgetItem(r["musteri_ad"]))
            t.setItem(i, 6, QTableWidgetItem(_para_metni(float(r["fiyat"]))))
        if self._grafik:
            self._grafik.guncelle(rows, self._tema == "dark")

    def _destek_durum_filtre(self) -> Optional[str]:
        if not self._filtre_destek:
            return None
        txt = self._filtre_destek.currentText()
        if txt == "Tümü":
            return None
        return txt

    def _destek_tablosu_doldur(self) -> None:
        durum = self._destek_durum_filtre()
        arama = self._arama_metni() if self._tabs and self._tabs.currentIndex() == 2 else ""
        rows = self._destek.talep_listele(
            durum=durum,
            arama=arama if arama else None,
        )
        t = self._tablo_destek
        if t is None:
            return
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, QTableWidgetItem(str(r["talep_id"])))
            t.setItem(i, 1, QTableWidgetItem(r["musteri_ad"]))
            t.setItem(i, 2, QTableWidgetItem(r["aciklama"]))
            t.setItem(i, 3, QTableWidgetItem(r["durum"]))

    def _dashboard_guncelle(self) -> None:
        oz = dashboard_ozet(self._db)
        if self._kart_musteri_val:
            self._kart_musteri_val.setText(str(oz["musteri_sayisi"]))
        if self._kart_satis_val:
            self._kart_satis_val.setText(_para_metni(oz["satis_toplam"]))
        if self._kart_destek_val:
            self._kart_destek_val.setText(str(oz["acik_destek"]))

    def yenile_hepsi(self) -> None:
        """Tüm sekmeleri ve kartları veritabanından yeniler."""
        self._musteri_combolarini_doldur()
        self._dashboard_guncelle()
        self._musteri_tablosu_doldur()
        self._satis_sekmesi_yenile()
        self._destek_tablosu_doldur()

    def _secili_musteri_id_tablo(self) -> Optional[int]:
        if self._tablo_musteri is None:
            return None
        r = self._tablo_musteri.currentRow()
        if r < 0:
            return None
        it = self._tablo_musteri.item(r, 0)
        if not it:
            return None
        return int(it.text())

    def _musteri_secimden_form(self) -> None:
        mid = self._secili_musteri_id_tablo()
        if mid is None:
            return
        rows = self._musteri.musteri_listele()
        for x in rows:
            if x["musteri_id"] == mid:
                self._m_ad.setText(x["ad"])
                self._m_tel.setText(x["telefon"])
                break

    def _musteri_ekle_ui(self) -> None:
        ad, tel = self._m_ad.text().strip(), self._m_tel.text().strip()
        if not ad or not tel:
            QMessageBox.warning(self, "Eksik", "Ad ve telefon zorunludur.")
            return
        self._musteri.musteri_ekle(ad, tel)
        self._m_ad.clear()
        self._m_tel.clear()
        self.yenile_hepsi()

    def _musteri_guncelle_ui(self) -> None:
        mid = self._secili_musteri_id_tablo()
        if mid is None:
            QMessageBox.information(self, "Seçim", "Güncellemek için satır seçin.")
            return
        ad, tel = self._m_ad.text().strip(), self._m_tel.text().strip()
        if not ad or not tel:
            QMessageBox.warning(self, "Eksik", "Ad ve telefon zorunludur.")
            return
        self._musteri.musteri_guncelle(mid, ad, tel)
        self.yenile_hepsi()

    def _musteri_sil_ui(self) -> None:
        mid = self._secili_musteri_id_tablo()
        if mid is None:
            QMessageBox.information(self, "Seçim", "Silmek için satır seçin.")
            return
        rep = QMessageBox.question(
            self,
            "Onay",
            "Bu müşteri ve ilişkili satış/talepler silinecek. Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return
        self._musteri.musteri_sil(mid)
        self._m_ad.clear()
        self._m_tel.clear()
        self.yenile_hepsi()

    def _satis_ekle_ui(self) -> None:
        if self._combo_musteri_satis.currentIndex() < 0:
            QMessageBox.warning(self, "Müşteri", "Önce müşteri ekleyin.")
            return
        mid = int(self._combo_musteri_satis.currentData())
        urun = self._s_urun.text().strip()
        if not urun:
            QMessageBox.warning(self, "Eksik", "Ürün adı girin.")
            return
        kategori = self._s_kategori.text().strip()
        adet = int(self._s_adet.value())
        if adet < 1:
            QMessageBox.warning(self, "Adet", "Adet en az 1 olmalıdır.")
            return
        fiyat = float(self._s_fiyat.value())
        d = self._satis_tarih.date().toPyDate() if self._satis_tarih else datetime.now().date()
        satis_zamani = datetime.combine(d, time(12, 0, 0))
        self._satis.satis_ekle(
            urun=urun,
            fiyat=fiyat,
            musteri_id=mid,
            tarih=satis_zamani,
            kategori=kategori,
            adet=adet,
        )
        self._s_urun.clear()
        self._s_kategori.clear()
        self._s_adet.setValue(1)
        self._s_fiyat.setValue(0.0)
        self.yenile_hepsi()

    def _destek_olustur_ui(self) -> None:
        if self._combo_musteri_destek.currentIndex() < 0:
            QMessageBox.warning(self, "Müşteri", "Müşteri seçin.")
            return
        mid = int(self._combo_musteri_destek.currentData())
        ac = self._d_aciklama.toPlainText().strip()
        if not ac:
            QMessageBox.warning(self, "Eksik", "Açıklama girin.")
            return
        self._destek.talep_olustur(ac, mid)
        self._d_aciklama.clear()
        self.yenile_hepsi()

    def _secili_talep_id(self) -> Optional[int]:
        if self._tablo_destek is None:
            return None
        r = self._tablo_destek.currentRow()
        if r < 0:
            return None
        it = self._tablo_destek.item(r, 0)
        if not it:
            return None
        return int(it.text())

    def _destek_kapat_ui(self) -> None:
        tid = self._secili_talep_id()
        if tid is None:
            QMessageBox.information(self, "Seçim", "Kapatmak için talep seçin.")
            return
        self._destek.talep_kapat(tid)
        self.yenile_hepsi()

    def _tema_degistir(self) -> None:
        self._tema = "dark" if self._tema == "light" else "light"
        self._uygula_tema()
        self._satis_sekmesi_yenile()

    def _uygula_tema(self) -> None:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(uygulama_stili(self._tema))
        if self._btn_tema:
            self._btn_tema.setText("Açık tema" if self._tema == "dark" else "Koyu tema")

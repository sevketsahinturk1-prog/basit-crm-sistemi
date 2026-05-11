"""Matplotlib ile günlük satış grafiği (filtrelenmiş veri)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, List

import matplotlib

matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout


class SatisGrafikWidget(QWidget):
    """
    Seçilen satış kayıtlarından günlük toplam tutar çubuk grafiği çizer.

    Tema rengine göre eksen ve arka plan uyarlanır.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Yatay panelde daha geniş figür; pencere büyüdükçe canvas da büyür
        self._fig = Figure(figsize=(7, 4.2), dpi=96)
        # QPainter/Qt arayüzünde şeffaf arka plan bazı temalarda "kirli" görünebilir.
        self._fig.patch.set_alpha(1.0)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(QSize(340, 260))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._canvas)
        self._ax = self._fig.add_subplot(111)

    def guncelle(self, satis_satirlari: List[dict[str, Any]], koyu_tema: bool) -> None:
        """
        Grafiği verilen satış listesiyle yeniden çizer.

        Args:
            satis_satirlari: `tarih` ve `fiyat` anahtarları içeren sözlükler.
            koyu_tema: True ise koyu palet.
        """
        self._ax.clear()
        gun_toplam: dict[str, float] = defaultdict(float)
        for r in satis_satirlari:
            ts = str(r.get("tarih", ""))
            gun = ts[:10] if len(ts) >= 10 else ts
            gun_toplam[gun] += float(r.get("fiyat", 0.0))

        gunler = sorted(gun_toplam.keys())
        degerler = [gun_toplam[g] for g in gunler]

        if koyu_tema:
            self._fig.patch.set_facecolor("#12141a")
            self._ax.set_facecolor("#1c1f28")
            bar_color = "#60a5fa"
            text_color = "#e8eaef"
            grid_c = "#374151"
        else:
            self._fig.patch.set_facecolor("#f4f6fb")
            self._ax.set_facecolor("#ffffff")
            bar_color = "#2563eb"
            text_color = "#1a1d26"
            grid_c = "#e5e7eb"

        if not gunler:
            self._ax.text(
                0.5,
                0.5,
                "Bu aralıkta satış yok",
                ha="center",
                va="center",
                transform=self._ax.transAxes,
                color=text_color,
                fontsize=11,
            )
            self._ax.set_xticks([])
            self._ax.set_yticks([])
        else:
            x = range(len(gunler))
            self._ax.bar(x, degerler, color=bar_color, edgecolor="none", width=0.65)
            self._ax.set_xticks(list(x))
            self._ax.set_xticklabels(gunler, rotation=30, ha="right", fontsize=9, color=text_color)
            self._ax.set_ylabel("Tutar (₺)", color=text_color)
            self._ax.tick_params(axis="y", colors=text_color)
            self._ax.tick_params(axis="x", colors=text_color)
            self._ax.yaxis.get_major_formatter().set_scientific(False)
            self._ax.grid(axis="y", linestyle="--", alpha=0.35, color=grid_c)
            self._ax.set_axisbelow(True)

        self._ax.set_title("Günlük satış özeti", color=text_color, fontsize=12, pad=12)
        for spine in self._ax.spines.values():
            spine.set_color(grid_c)
        self._fig.tight_layout()
        self._canvas.draw()

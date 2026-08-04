"""Bina konfigürasyonu ve tüketim/üretim hesapları."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ── Bina tipi varsayılanları ─────────────────────────────────────
BINA_TIPLERI: dict[str, dict] = {
    "Müstakil Ev": dict(kat=1, daire_per_kat=1, aktif_daire=1, oda=4, cati_alani=60,
                        asansor=False, hvac=True, su_pompasi=False, ev_sarj=True,
                        kamera=True, gunes_isitici=True, jenerator=False),
    "Villa": dict(kat=2, daire_per_kat=1, aktif_daire=1, oda=5, cati_alani=100,
                  asansor=False, hvac=True, su_pompasi=True, ev_sarj=True,
                  kamera=True, gunes_isitici=True, jenerator=True),
    "Apartman": dict(kat=5, daire_per_kat=3, aktif_daire=12, oda=3, cati_alani=140,
                     asansor=True, hvac=False, su_pompasi=True, ev_sarj=True,
                     kamera=True, gunes_isitici=False, jenerator=True),
    "Ofis Binası": dict(kat=6, daire_per_kat=2, aktif_daire=10, oda=6, cati_alani=200,
                        asansor=True, hvac=True, su_pompasi=True, ev_sarj=True,
                        kamera=True, gunes_isitici=False, jenerator=True),
}

PANEL_ALAN_M2 = 1.7      # bir panelin kapladığı çatı alanı
PANEL_GUC_KW = 0.45      # panel başına kurulu güç (450 W)
JENERATOR_TL_KWH = 12.0  # dizel jeneratör birim maliyeti (TL/kWh)


@dataclass
class BinaConfig:
    bina_tipi: str = "Apartman"
    kat: int = 5
    daire_per_kat: int = 3
    aktif_daire: int = 12
    oda: int = 3
    cati_alani: float = 140.0
    asansor: bool = True
    hvac: bool = False
    su_pompasi: bool = True
    ev_sarj: bool = True
    kamera: bool = True
    gunes_isitici: bool = False
    jenerator: bool = True

    @classmethod
    def from_tip(cls, tip: str) -> "BinaConfig":
        return cls(bina_tipi=tip, **BINA_TIPLERI[tip])

    # ── Türetilmiş büyüklükler ───────────────────────────────────
    @property
    def toplam_daire(self) -> int:
        return self.kat * self.daire_per_kat

    @property
    def gunluk_tuketim_kwh(self) -> float:
        """Spesifikasyondaki formül."""
        t = self.aktif_daire * self.oda * 1.8
        t += 8.0 if self.asansor else 0.0
        t += self.kat * 3.0 if self.hvac else 0.0
        t += 2.0 if self.su_pompasi else 0.0
        t += 9.6 if self.ev_sarj else 0.0
        t += 0.6 if self.kamera else 0.0          # kameralar 7/24 düşük güç
        t -= self.aktif_daire * 0.5 if self.gunes_isitici else 0.0  # su ısıtma tasarrufu
        return max(t, 1.0)

    @property
    def panel_sayisi(self) -> int:
        return int(self.cati_alani / PANEL_ALAN_M2)

    @property
    def panel_kw(self) -> float:
        return round(self.panel_sayisi * PANEL_GUC_KW, 2)

    @property
    def batarya_kwh(self) -> float:
        return round(self.gunluk_tuketim_kwh * 0.4, 1)

    @property
    def batarya_guc_kw(self) -> float:
        """C/2 şarj-deşarj gücü."""
        return round(self.batarya_kwh / 2.0, 1)


# ── Saatlik profil şekilleri (24 değer, toplamı 1'e normalize) ──
def _norm(x: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=float), 0.0, None)
    return x / x.sum()

_H = np.arange(24)

# Konut temel yükü: sabah ve akşam tepe
_SHAPE_KONUT = _norm(0.45 + 0.55 * np.exp(-0.5 * ((_H - 8) / 2.2) ** 2)
                     + 1.15 * np.exp(-0.5 * ((_H - 20) / 2.8) ** 2))
# Asansör: gündüz yoğun, sabah/akşam tepe
_SHAPE_ASANSOR = _norm(0.15 + np.exp(-0.5 * ((_H - 8.5) / 1.8) ** 2)
                       + np.exp(-0.5 * ((_H - 18) / 2.2) ** 2))
# HVAC: öğle-akşam arası klima yükü
_SHAPE_HVAC = _norm(0.10 + np.exp(-0.5 * ((_H - 15) / 3.5) ** 2))
# Su pompası: sabah ve akşam kullanım tepeleri
_SHAPE_POMPA = _norm(0.20 + np.exp(-0.5 * ((_H - 7.5) / 1.5) ** 2)
                     + np.exp(-0.5 * ((_H - 19.5) / 2.0) ** 2))
# EV şarj: gece 22:00–06:00
_SHAPE_EV = _norm(np.where((_H >= 22) | (_H < 6), 1.0, 0.02))
# Kamera: sabit
_SHAPE_SABIT = _norm(np.ones(24))


def saatlik_talep_kw(cfg: BinaConfig) -> np.ndarray:
    """Bina bileşenlerinin toplam saatlik talebi (kW, 24 değer)."""
    konut = cfg.aktif_daire * cfg.oda * 1.8
    if cfg.gunes_isitici:
        konut -= cfg.aktif_daire * 0.5
    kwh = konut * _SHAPE_KONUT
    if cfg.asansor:
        kwh = kwh + 8.0 * _SHAPE_ASANSOR
    if cfg.hvac:
        kwh = kwh + cfg.kat * 3.0 * _SHAPE_HVAC
    if cfg.su_pompasi:
        kwh = kwh + 2.0 * _SHAPE_POMPA
    if cfg.ev_sarj:
        kwh = kwh + 9.6 * _SHAPE_EV
    if cfg.kamera:
        kwh = kwh + 0.6 * _SHAPE_SABIT
    return kwh  # 1 saatlik adımda kWh == kW


def saatlik_gunes_kw(cfg: BinaConfig, ay: int, shape: np.ndarray | None = None) -> np.ndarray:
    """Panel gücünden saatlik güneş üretimi (kW).

    shape verilirse (gerçek PVWatts profili, tepe=1) o kullanılır,
    verilmezse mevsime göre sentetik çan eğrisi üretilir.
    """
    if shape is None:
        # Mevsimsel gün uzunluğu ve yoğunluk
        yaz = 1.0 - 0.55 * np.cos((ay - 7) * 2 * np.pi / 12) ** 2
        merkez = 13.0
        genis = 3.0 + 0.8 * yaz
        shape = np.exp(-0.5 * ((_H - merkez) / genis) ** 2)
        shape = np.where((_H < 5) | (_H > 21), 0.0, shape)
        shape = shape * (0.55 + 0.45 * yaz)
    return cfg.panel_kw * 0.80 * shape  # 0.80: sistem kayıpları

"""24 saatlik bina simülasyonu.

Ajan, eğitildiği ev ölçeğinde (10 kWh batarya) karar verir; bina daha
büyükse problem doğrusal ölçeklendiği için tüm büyüklükler k katsayısıyla
ajan ölçeğine indirilir, sonuçlar gerçek ölçekte raporlanır.

Fizik (env ile uyumlu): verim %95, satış = alış × 0.60, min SoC %10,
öz-deşarj %0.05/saat.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .agent import EGITIM_BATARYA_KWH, build_obs
from .config import JENERATOR_TL_KWH

VERIM = 0.95
SATIS_ORANI = 0.60
MIN_SOC = 0.10
OZ_DESARJ = 0.0005

# Ay bazlı sıcaklık-verim çarpanı: lityum batarya soğukta verim kaybeder
# (Oca..Ara — kışın ~%12 kayıp, yazın tam verim)
SICAKLIK_VERIM = [0.88, 0.90, 0.94, 0.97, 1.00, 1.00, 1.00, 1.00, 0.98, 0.95, 0.91, 0.88]


def simulate_day(prices_tl_mwh: np.ndarray,
                 solar_kw: np.ndarray,
                 demand_kw: np.ndarray,
                 batt_kwh: float,
                 batt_power_kw: float,
                 agent,
                 dow: int = 0,
                 initial_soc: float = 0.5,
                 outage_hours: set[int] | None = None,
                 jenerator: bool = False,
                 ay: int | None = None) -> pd.DataFrame:
    outage_hours = outage_hours or set()
    # Mevsimsel batarya verimi (ay verilmezse standart %95)
    verim = VERIM * (SICAKLIK_VERIM[ay - 1] if ay else 1.0)
    p_kwh = np.asarray(prices_tl_mwh, dtype=float) / 1000.0  # TL/kWh
    tomorrow = p_kwh.copy()  # gün-öncesi: yarın için bugünkü seri en iyi tahmin

    # Ajan ölçeği
    k = max(batt_kwh / EGITIM_BATARYA_KWH, 1e-6)
    solar_a = solar_kw / k
    demand_a = demand_kw / k

    soc = float(initial_soc)
    rows = []
    for h in range(24):
        grid_up = h not in outage_hours
        obs = build_obs(soc, h, dow, p_kwh, tomorrow, solar_a, demand_a,
                        grid_up=grid_up, obs_dim=getattr(agent, "obs_dim", 106))
        a, defer = agent.act(obs)

        # Kesintide ve jeneratör yoksa: batarya önceliği → şarjı iptal et
        if not grid_up:
            acik = demand_kw[h] - solar_kw[h]
            a = min(a, 0.0) if acik > 0 else a

        # ── Batarya fiziği (gerçek ölçek) ──
        soc = max(0.0, soc - OZ_DESARJ)
        sarj_kwh = desarj_kwh = 0.0
        istek = a * batt_power_kw
        if istek > 0:
            bosluk = (1.0 - soc) * batt_kwh
            sarj_kwh = min(istek, bosluk / verim)
            soc = min(1.0, soc + sarj_kwh * verim / batt_kwh)
        elif istek < 0:
            mevcut = max(0.0, soc - MIN_SOC) * batt_kwh
            cekilen = min(-istek, mevcut)
            soc = max(0.0, soc - cekilen / batt_kwh)
            desarj_kwh = cekilen * verim

        net = demand_kw[h] - solar_kw[h] + sarj_kwh - desarj_kwh

        maliyet = gelir = jen_kwh = karsilanmayan = 0.0
        if grid_up:
            if net > 0:
                maliyet = net * p_kwh[h]
            else:
                gelir = -net * p_kwh[h] * SATIS_ORANI
        else:
            if net > 0:
                if jenerator:
                    jen_kwh = net
                    maliyet = net * JENERATOR_TL_KWH
                else:
                    karsilanmayan = net

        # Karşılaştırma: batarya+güneş olmasaydı
        taban = demand_kw[h] * p_kwh[h] if grid_up else 0.0

        if sarj_kwh > 0.05:
            karar = "şarj"
        elif desarj_kwh > 0.05:
            karar = "deşarj"
        else:
            karar = "bekle"

        rows.append(dict(
            saat=h, fiyat_tl_mwh=prices_tl_mwh[h], fiyat_tl_kwh=p_kwh[h],
            soc=soc, karar=karar, aksiyon=a,
            sarj_kwh=sarj_kwh, desarj_kwh=desarj_kwh,
            gunes_kw=solar_kw[h], talep_kw=demand_kw[h], net_kwh=net,
            maliyet_tl=maliyet, gelir_tl=gelir, taban_maliyet_tl=taban,
            jenerator_kwh=jen_kwh, karsilanmayan_kwh=karsilanmayan,
            kesinti=not grid_up, defer_sinyal=defer,
        ))

    df = pd.DataFrame(rows)
    df["net_maliyet_tl"] = df["maliyet_tl"] - df["gelir_tl"]
    df["tasarruf_tl"] = df["taban_maliyet_tl"] - df["net_maliyet_tl"]
    return df


def oneriler(df: pd.DataFrame, saat: int) -> list[str]:
    """Kullanıcıya doğal dilde öneriler üretir."""
    r = df.iloc[saat]
    out = []
    p = r["fiyat_tl_mwh"]
    ort = df["fiyat_tl_mwh"].mean()
    if r["karar"] == "şarj":
        out.append(f"⚡ Şu an şarj edin — fiyat düşük ({p:.0f} TL/MWh, ortalama {ort:.0f})")
    elif r["karar"] == "deşarj":
        out.append(f"🔋 Batarya %{r['soc']*100:.0f} — deşarj ile pahalı saatten kaçınılıyor ({p:.0f} TL/MWh)")
    else:
        out.append(f"⏸️ Beklemede — fiyat nötr bölgede ({p:.0f} TL/MWh)")

    # Ertelenebilir yük önerisi: ajan sinyali > 0 olan ilk gündüz saati, yoksa en ucuz saat
    sinyal = df[(df["defer_sinyal"] > 0) & (df["saat"].between(6, 21))]
    if not sinyal.empty:
        en_iyi = int(sinyal.iloc[0]["saat"])
    else:
        gunduz = df[df["saat"].between(6, 21)]
        en_iyi = int(gunduz.loc[gunduz["fiyat_tl_mwh"].idxmin(), "saat"])
    out.append(f"🌀 Çamaşır/bulaşık makinesini saat {en_iyi:02d}:00'te çalıştırın (günün en uygun saati)")

    if r["gunes_kw"] > 0.5:
        out.append(f"☀️ Güneş {r['gunes_kw']:.1f} kW üretiyor — yüksek tüketimli işleri şimdi yapın")
    if r["kesinti"]:
        out.append("🚨 Elektrik kesintisi! " + ("Jeneratör devrede." if r["jenerator_kwh"] > 0 or r["karsilanmayan_kwh"] == 0 else f"{r['karsilanmayan_kwh']:.1f} kWh karşılanamıyor!"))
    return out


def oneriler_kodlu(df: pd.DataFrame, saat: int) -> list[dict]:
    """Öneriler — dile bağımsız yapısal veri (kod + parametre).
    Frontend her kodu kendi i18n şablonuyla biçimlendirir."""
    r = df.iloc[saat]
    out: list[dict] = []
    p = float(r["fiyat_tl_mwh"])
    ort = float(df["fiyat_tl_mwh"].mean())
    if r["karar"] == "şarj":
        out.append({"code": "charge", "p": round(p), "ort": round(ort)})
    elif r["karar"] == "deşarj":
        out.append({"code": "discharge", "soc": round(float(r["soc"]) * 100), "p": round(p)})
    else:
        out.append({"code": "idle", "p": round(p)})

    sinyal = df[(df["defer_sinyal"] > 0) & (df["saat"].between(6, 21))]
    if not sinyal.empty:
        en_iyi = int(sinyal.iloc[0]["saat"])
    else:
        gunduz = df[df["saat"].between(6, 21)]
        en_iyi = int(gunduz.loc[gunduz["fiyat_tl_mwh"].idxmin(), "saat"])
    out.append({"code": "defer", "saat": f"{en_iyi:02d}"})

    if r["gunes_kw"] > 0.5:
        out.append({"code": "solar", "kw": round(float(r["gunes_kw"]), 1)})
    if r["kesinti"]:
        if r["jenerator_kwh"] > 0 or r["karsilanmayan_kwh"] == 0:
            out.append({"code": "outageGen"})
        else:
            out.append({"code": "outageUnmet", "kwh": round(float(r["karsilanmayan_kwh"]), 1)})
    return out

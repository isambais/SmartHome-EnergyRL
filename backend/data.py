"""Streamlit'siz veri katmanı — dashboard/core/data.py'nin API uyarlaması.

Öncelik: EPİAŞ API (kimlik verilirse) → CSV arşiv → sentetik.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

EPIAS_CAS = "https://giris.epias.com.tr/cas/v1/tickets"
EPIAS_MCP = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"


@lru_cache(maxsize=1)
def load_combined() -> pd.DataFrame:
    df = pd.read_csv(DATA / "epias_combined.csv", parse_dates=["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


@lru_cache(maxsize=1)
def load_aligned() -> pd.DataFrame:
    df = pd.read_csv(DATA / "processed" / "aligned_dataset.csv", parse_dates=["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


@lru_cache(maxsize=12)
def gunes_sekli(ay: int) -> np.ndarray:
    """Gerçek PVWatts profilinden ay bazlı tipik güneş şekli (tepe=1)."""
    df = load_aligned()
    sub = df[df["timestamp"].dt.month == ay]
    if sub.empty:
        return np.zeros(24)
    prof = (sub.groupby(sub["timestamp"].dt.hour)["solar_kw"].mean()
            .reindex(range(24), fill_value=0.0).to_numpy())
    m = prof.max()
    return prof / m if m > 0 else prof


def _csv_gun_fiyati(tarih: dt.date, gurultu: bool) -> np.ndarray | None:
    df = load_combined()
    gun = df[df["timestamp"].dt.date == tarih]
    if len(gun) == 24:
        return gun["price_tl_mwh"].to_numpy(dtype=float)

    adaylar = df[(df["timestamp"].dt.month == tarih.month)
                 & (df["timestamp"].dt.dayofweek == tarih.weekday())]
    if adaylar.empty:
        adaylar = df[df["timestamp"].dt.month == tarih.month]
    if adaylar.empty:
        return None
    son_gun = adaylar["timestamp"].dt.date.max()
    fiyat = df[df["timestamp"].dt.date == son_gun]["price_tl_mwh"].to_numpy(dtype=float)
    if len(fiyat) != 24:
        return None
    if gurultu:
        rng = np.random.default_rng(tarih.toordinal())
        fiyat = fiyat * (1.0 + rng.normal(0, 0.04, 24))
    return np.clip(fiyat, 0.0, None)


def _api_gun_fiyati(tarih: dt.date, kullanici: str, sifre: str) -> np.ndarray | None:
    try:
        # TGT al — Accept: text/plain olmadan EPİAŞ TGT'yi HTML olarak döndürür
        r = requests.post(
            EPIAS_CAS,
            data={"username": kullanici, "password": sifre},
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Accept": "text/plain"},
            timeout=15,
        )
        if r.status_code not in (200, 201):
            return None
        tgt = r.text.strip()
        gun = tarih.strftime("%Y-%m-%dT00:00:00+03:00")
        r2 = requests.post(
            EPIAS_MCP,
            json={"startDate": gun, "endDate": gun},
            headers={"TGT": tgt, "Content-Type": "application/json",
                     "Accept": "application/json"},
            timeout=20,
        )
        if r2.status_code != 200:
            return None
        items = r2.json().get("items", [])
        fiyat = [it.get("price") for it in items if it.get("price") is not None]
        if len(fiyat) >= 24:
            return np.asarray(fiyat[:24], dtype=float)
    except Exception:
        return None
    return None


def gun_fiyati(tarih: dt.date | None = None,
               kullanici: str = "", sifre: str = "") -> tuple[np.ndarray, str]:
    """24 saatlik PTF (TL/MWh) + kaynak etiketi. Asla başarısız olmaz."""
    tarih = tarih or dt.date.today()

    if kullanici and sifre:
        f = _api_gun_fiyati(tarih, kullanici, sifre)
        if f is not None:
            return f, "EPİAŞ API (canlı)"

    f = _csv_gun_fiyati(tarih, gurultu=True)
    if f is not None:
        df = load_combined()
        gercek = not df[df["timestamp"].dt.date == tarih].empty
        return f, ("EPİAŞ arşiv (CSV)" if gercek else "Sentetik (EPİAŞ desenli)")

    rng = np.random.default_rng(0)
    taban = 2400 + 900 * np.sin((np.arange(24) - 14) * np.pi / 12)
    return np.clip(taban + rng.normal(0, 80, 24), 500, None), "Sentetik (varsayılan)"

"""Curriculum Aşama 2 veri seti oluşturucu.

EPIAS fiyatı + PVWatts güneş üretimi + UK-DALE ev talebi verilerini
aynı saatlik takvimde birleştirir.

Çıktı: data/processed/aligned_dataset.csv
Kolonlar: timestamp, price_tl_mwh, solar_kw, demand_kw
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.data.solar_profile import SolarProfileGenerator  # noqa: E402
from src.data.demand_profile import DemandProfileGenerator  # noqa: E402

OUT_PATH = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"
EPIAS_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"


def build_solar(target_dates: pd.DatetimeIndex) -> np.ndarray:
    print("Güneş verisi çekiliyor (PVWatts DEMO_KEY)...")
    gen = SolarProfileGenerator(api_key="DEMO_KEY", lat=41.01, lon=28.98)
    profile = gen.fetch_hourly_profile()
    aligned = gen.align_to_dates(profile, target_dates)
    print(f"  Ort. {aligned['solar_kw'].mean():.3f} kW, maks. {aligned['solar_kw'].max():.2f} kW")
    return aligned["solar_kw"].values


def build_demand(target_dates: pd.DatetimeIndex) -> np.ndarray:
    print("Ev talebi işleniyor (UK-DALE channel_1.dat)...")
    gen = DemandProfileGenerator(raw_dir=str(_PROJECT_ROOT / "data" / "raw"))
    raw = gen.load_raw("channel_1.dat")
    print(f"  Ham veri: {len(raw):,} satır")
    hourly = gen.resample_hourly(raw)
    typical = gen.compute_typical_profile(hourly)
    aligned = gen.align_to_dates(typical, target_dates)
    print(f"  Ort. {aligned['demand_kw'].mean():.3f} kW, maks. {aligned['demand_kw'].max():.2f} kW")
    return aligned["demand_kw"].values


def main() -> None:
    print(f"EPIAS verisi yükleniyor: {EPIAS_PATH}")
    price_df = pd.read_csv(EPIAS_PATH, parse_dates=["timestamp"])
    target_dates = pd.DatetimeIndex(price_df["timestamp"])
    print(f"  {len(price_df)} saat, {price_df['price_tl_mwh'].mean():.1f} TL/MWh ort.")

    solar_kw = build_solar(target_dates)
    demand_kw = build_demand(target_dates)

    aligned = pd.DataFrame({
        "timestamp": price_df["timestamp"],
        "price_tl_mwh": price_df["price_tl_mwh"].values,
        "solar_kw": solar_kw,
        "demand_kw": demand_kw,
    })

    if aligned.isna().any().any():
        raise ValueError("Hizalanmış veri setinde NaN var!")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(OUT_PATH, index=False)
    print(f"\nKaydedildi: {OUT_PATH} ({len(aligned)} satır)")
    print(aligned.describe().round(3))


if __name__ == "__main__":
    main()
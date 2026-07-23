"""Gerçek veri yoksa kullanılacak sentetik EPIAS verisi üretici.

Üretilen veri gerçekçi desenler içerir:
  - Mevsimsel dalgalanma (kış/yaz yüksek)
  - Günlük iki zirve (sabah 09:00, akşam 19:00)
  - Hafta sonu ~%8 indirimi
  - Rastgele gürültü + nadir fiyat sıçramaları

Kullanım:
    python scripts/generate_epias_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
DAYS = 366
BASE_PRICE = 2200.0  # TL/MWh
OUT = Path(__file__).parent.parent / "data" / "epias_2024_synthetic.csv"


def generate(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hours = DAYS * 24
    timestamps = pd.date_range("2025-07-15", periods=hours, freq="h")

    day_of_year = np.arange(hours) / 24
    seasonal = 0.20 * np.cos(2 * np.pi * (day_of_year - 15) / 365)
    seasonal += 0.12 * np.cos(4 * np.pi * (day_of_year - 15) / 365)

    hour_of_day = np.array([t.hour for t in timestamps])
    daily = (
        0.18 * np.cos(2 * np.pi * (hour_of_day - 9) / 24)
        + 0.13 * np.cos(2 * np.pi * (hour_of_day - 19) / 24)
        - 0.08 * np.exp(-((hour_of_day - 3) ** 2) / 8)
    )

    is_weekend = np.array([t.weekday() >= 5 for t in timestamps], dtype=float)
    noise = 0.06 * rng.standard_normal(hours)
    spikes = (rng.random(hours) < (2 / (30 * 24))) * rng.uniform(0.3, 0.8, hours)

    price = BASE_PRICE * (1 + seasonal + daily - 0.08 * is_weekend + noise + spikes)
    price = np.clip(price, 300.0, 4500.0).round(2)

    return pd.DataFrame({"timestamp": timestamps, "price_tl_mwh": price})


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUT, index=False)
    print(f"Kaydedildi: {OUT}")
    print(f"Satır: {len(df)}, Ort: {df['price_tl_mwh'].mean():.1f} TL/MWh")


if __name__ == "__main__":
    main()
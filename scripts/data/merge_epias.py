"""EPİAŞ ham CSV dosyalarını birleştirip data/epias_combined.csv oluşturur.

Ham dosyalar data/ klasöründe olmalı: epias_2022.csv, epias_2023.csv, ...
EPİAŞ şeffaflık platformu formatı: noktalı virgül ayraç, virgül ondalık.

Kullanım:
    python scripts/data/merge_epias.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

import pandas as pd  # noqa: E402


def parse_epias_raw(filepath: Path) -> pd.DataFrame:
    """EPİAŞ ham CSV → timestamp + price_tl_mwh DataFrame."""
    df = pd.read_csv(filepath, sep=";")
    df = df[["Tarih", "Saat", "PTF (TL/MWh)"]].copy()
    df.columns = ["tarih", "saat", "price_tl_mwh"]
    # Nokta = binde ayraç, virgül = ondalık ayraç
    df["price_tl_mwh"] = (
        df["price_tl_mwh"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    df["timestamp"] = pd.to_datetime(
        df["tarih"] + " " + df["saat"], format="%d.%m.%Y %H:%M"
    )
    return df[["timestamp", "price_tl_mwh"]]


def main() -> None:
    data_dir = _ROOT / "data"
    frames: list[pd.DataFrame] = []

    # Ham yıllık dosyalar
    raw_files = sorted(data_dir.glob("epias_20*.csv"))
    for fpath in raw_files:
        df = parse_epias_raw(fpath)
        print(
            f"{fpath.name}: {len(df):>5} saat | "
            f"{df['timestamp'].min().date()} → {df['timestamp'].max().date()} | "
            f"{df['price_tl_mwh'].min():.0f}-{df['price_tl_mwh'].max():.0f} TL/MWh"
        )
        frames.append(df)

    # İşlenmiş aligned_dataset'ten fiyat sütununu da ekle (boşluk kapama)
    aligned = data_dir / "processed" / "aligned_dataset.csv"
    if aligned.exists():
        df_al = pd.read_csv(aligned, parse_dates=["timestamp"])[["timestamp", "price_tl_mwh"]]
        print(
            f"aligned_dataset: {len(df_al):>5} saat | "
            f"{df_al['timestamp'].min().date()} → {df_al['timestamp'].max().date()}"
        )
        frames.append(df_al)

    combined = (
        pd.concat(frames)
        .drop_duplicates(subset="timestamp")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    out = data_dir / "epias_combined.csv"
    combined.to_csv(out, index=False)

    print(f"\nToplam (tekrarsız): {len(combined):>6} saat")
    print(f"Tarih aralığı: {combined['timestamp'].min().date()} → {combined['timestamp'].max().date()}")
    print(f"Sıfır fiyat : {(combined['price_tl_mwh'] == 0).sum()} adet (sMAPE ile ele alınıyor)")
    print(f"Kaydedildi  : {out}")


if __name__ == "__main__":
    main()

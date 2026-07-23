"""Ham EPIAS PTF CSV'sini (Türkçe format) işleyerek data/epias_2024.csv üretir.

Kullanım:
    Orijinal dosyayı data/epias_raw.csv olarak kopyalayın, sonra:
    python scripts/prepare_epias_data.py
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "epias_raw.csv"
OUT = Path(__file__).parent.parent / "data" / "epias_2024.csv"


def parse_turkish_float(s: str) -> float:
    return float(str(s).strip().replace(".", "").replace(",", "."))


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(
            f"{RAW} bulunamadi.\n"
            "EPIAS ham verisini data/epias_raw.csv olarak kaydedin."
        )

    df = pd.read_csv(RAW, sep=";", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    df["timestamp"] = pd.to_datetime(
        df["Tarih"] + " " + df["Saat"], format="%d.%m.%Y %H:%M"
    )
    df["price_tl_mwh"] = df["PTF (TL/MWh)"].apply(parse_turkish_float)

    out = df[["timestamp", "price_tl_mwh"]].sort_values("timestamp").reset_index(drop=True)

    expected = (out["timestamp"].max() - out["timestamp"].min()).total_seconds() / 3600 + 1
    missing = int(expected - len(out))
    if missing > 0:
        print(f"UYARI: {missing} eksik saat — interpolasyon uygulanıyor")
        out = out.set_index("timestamp").resample("h").interpolate().reset_index()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Kaydedildi : {OUT}")
    print(f"Satır sayısı: {len(out)}")
    print(f"Tarih aralığı: {out['timestamp'].min()} → {out['timestamp'].max()}")
    print(f"Ort. fiyat : {out['price_tl_mwh'].mean():.1f} TL/MWh")


if __name__ == "__main__":
    main()
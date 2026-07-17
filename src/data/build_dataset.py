"""Üç veri kaynağını (EPİAŞ fiyatı, PVWatts güneş üretimi, UK-DALE ev talebi) aynı
saatlik takvimde hizalayıp RL ortamının doğrudan kullanabileceği birleşik bir veri
seti oluşturan modül.

implementation_plan.md Bölüm 8: "Bu üçünün saatlik zaman damgalarıyla hizalanması
(aynı takvime oturtulması) ön işlemenin en kritik adımıdır — bu adım aksarsa ortam
yanlış sinyal üretir."

Kullanım (data/raw altına gerekli ham dosyalar konduktan sonra):

    from src.data.epias_loader import EpiasLoader
    from src.data.solar_profile import SolarProfileGenerator
    from src.data.demand_profile import DemandProfileGenerator
    from src.data.build_dataset import build_aligned_dataset, save_processed_dataset

    price_df = EpiasLoader().load_csv("Piyasa_Takas_Fiyati-15072025-15072026.csv")

    solar_gen = SolarProfileGenerator(api_key="DEMO_KEY", lat=41.01, lon=28.98)
    solar_profile = solar_gen.fetch_hourly_profile()

    demand_gen = DemandProfileGenerator()
    demand_hourly = demand_gen.resample_hourly(demand_gen.load_raw("channel_1.dat"))
    demand_typical = demand_gen.compute_typical_profile(demand_hourly)

    aligned = build_aligned_dataset(price_df, solar_profile, demand_typical, solar_gen, demand_gen)
    save_processed_dataset(aligned)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.demand_profile import DemandProfileGenerator
from src.data.solar_profile import SolarProfileGenerator


def build_aligned_dataset(
    price_df: pd.DataFrame,
    solar_profile: pd.DataFrame,
    demand_typical_profile: pd.DataFrame,
    solar_generator: SolarProfileGenerator,
    demand_generator: DemandProfileGenerator,
    add_demand_noise: bool = True,
    demand_seed: int = 42,
) -> pd.DataFrame:
    """price_df (EpiasLoader çıktısı), solar_profile (SolarProfileGenerator.fetch_hourly_profile
    çıktısı) ve demand_typical_profile (DemandProfileGenerator.compute_typical_profile çıktısı)
    verilerini, price_df'in zaman damgalarına hizalayarak tek bir DataFrame'de birleştirir.

    Dönen kolonlar: timestamp, price_tl_mwh, solar_kw, demand_kw

    price_df'te tekrarlanan zaman damgası varsa (veri hatası) veya hizalama sonrası
    eksik (NaN) değer oluşursa ValueError fırlatır — implementation_plan.md'nin
    vurguladığı "hizalama aksarsa ortam yanlış sinyal üretir" riskine karşı erken uyarı.
    """
    if price_df["timestamp"].duplicated().any():
        raise ValueError(
            "price_df içinde tekrarlanan zaman damgaları var; hizalama güvenilir olmaz."
        )

    target_dates = pd.DatetimeIndex(price_df["timestamp"])

    solar_aligned = solar_generator.align_to_dates(solar_profile, target_dates)
    demand_aligned = demand_generator.align_to_dates(
        demand_typical_profile,
        target_dates,
        add_noise=add_demand_noise,
        seed=demand_seed,
    )

    merged = price_df.merge(solar_aligned, on="timestamp", how="left")
    merged = merged.merge(demand_aligned, on="timestamp", how="left")

    if len(merged) != len(price_df):
        raise ValueError(
            "Birleştirme sonrası satır sayısı değişti; hizalama beklenenden farklı çalıştı."
        )

    required_cols = ["price_tl_mwh", "solar_kw", "demand_kw"]
    if merged[required_cols].isna().any().any():
        raise ValueError(
            "Hizalanmış veri setinde eksik (NaN) değer var - hizalama kontrol edilmeli."
        )

    return merged[["timestamp", "price_tl_mwh", "solar_kw", "demand_kw"]]


def save_processed_dataset(
    df: pd.DataFrame, output_path: Path | str = "data/processed/aligned_dataset.csv"
) -> Path:
    """Birleşik veri setini data/processed/ altına CSV olarak kaydeder."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    from src.data.epias_loader import EpiasLoader

    price_df = EpiasLoader().load_csv("Piyasa_Takas_Fiyati-15072025-15072026.csv")

    solar_gen = SolarProfileGenerator(api_key="DEMO_KEY", lat=41.01, lon=28.98)
    solar_profile = solar_gen.fetch_hourly_profile()

    demand_gen = DemandProfileGenerator()
    demand_hourly = demand_gen.resample_hourly(demand_gen.load_raw("channel_1.dat"))
    demand_typical = demand_gen.compute_typical_profile(demand_hourly)

    aligned = build_aligned_dataset(
        price_df, solar_profile, demand_typical, solar_gen, demand_gen
    )
    path = save_processed_dataset(aligned)
    print(f"Kaydedildi: {path} ({len(aligned)} satır)")
    print(aligned.describe())

"""build_aligned_dataset() ve save_processed_dataset() için birim testleri.

Gerçek EPİAŞ/PVWatts/UK-DALE dosyalarına bağımlılık olmadan, küçük elle üretilmiş
DataFrame'lerle hizalama/birleştirme mantığı test edilir.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data.build_dataset import build_aligned_dataset, save_processed_dataset
from src.data.demand_profile import DemandProfileGenerator
from src.data.solar_profile import SolarProfileGenerator


@pytest.fixture
def price_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-07-13 00:00", periods=4, freq="h"),
            "price_tl_mwh": [1000.0, 1100.0, 1200.0, 1300.0],
        }
    )


@pytest.fixture
def solar_profile() -> pd.DataFrame:
    # SolarProfileGenerator.align_to_dates ay-gün-saat eşlemesi kullanıyor;
    # 2001 gibi soyut bir "tipik yıl" ile aynı ay-gün-saatleri kapsayalım.
    return pd.DataFrame(
        {
            "hour_of_year": range(4),
            "timestamp_tmy": pd.date_range("2001-07-13 00:00", periods=4, freq="h"),
            "solar_kw": [0.0, 0.0, 0.1, 0.3],
        }
    )


@pytest.fixture
def demand_typical_profile() -> pd.DataFrame:
    # 2026-07-13 bir Pazartesi'dir (weekday=0).
    return pd.DataFrame(
        {"mean_kw": [0.2, 0.2, 0.25, 0.3], "std_kw": [0.0, 0.0, 0.0, 0.0]},
        index=pd.MultiIndex.from_tuples(
            [(0, 0), (0, 1), (0, 2), (0, 3)], names=["weekday", "hour"]
        ),
    )


def test_build_aligned_dataset_merges_all_three_sources(
    price_df, solar_profile, demand_typical_profile
) -> None:
    solar_gen = SolarProfileGenerator()
    demand_gen = DemandProfileGenerator()

    merged = build_aligned_dataset(
        price_df,
        solar_profile,
        demand_typical_profile,
        solar_gen,
        demand_gen,
        add_demand_noise=False,
    )

    assert list(merged.columns) == ["timestamp", "price_tl_mwh", "solar_kw", "demand_kw"]
    assert len(merged) == 4
    assert merged.loc[2, "solar_kw"] == pytest.approx(0.1)
    assert merged.loc[3, "demand_kw"] == pytest.approx(0.3)
    assert not merged.isna().any().any()


def test_build_aligned_dataset_raises_on_duplicate_timestamps(
    solar_profile, demand_typical_profile
) -> None:
    dup_price_df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2026-07-13 00:00")] * 2,
            "price_tl_mwh": [1000.0, 1000.0],
        }
    )
    solar_gen = SolarProfileGenerator()
    demand_gen = DemandProfileGenerator()

    with pytest.raises(ValueError, match="tekrarlanan"):
        build_aligned_dataset(
            dup_price_df, solar_profile, demand_typical_profile, solar_gen, demand_gen
        )


def test_build_aligned_dataset_preserves_row_order(
    price_df, solar_profile, demand_typical_profile
) -> None:
    solar_gen = SolarProfileGenerator()
    demand_gen = DemandProfileGenerator()

    merged = build_aligned_dataset(
        price_df,
        solar_profile,
        demand_typical_profile,
        solar_gen,
        demand_gen,
        add_demand_noise=False,
    )

    pd.testing.assert_series_equal(
        merged["timestamp"], price_df["timestamp"], check_names=False
    )


def test_save_processed_dataset_writes_csv(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-07-13", periods=2, freq="h"),
            "price_tl_mwh": [1000.0, 1100.0],
            "solar_kw": [0.0, 0.1],
            "demand_kw": [0.2, 0.2],
        }
    )
    output_path = tmp_path / "data" / "processed" / "aligned_dataset.csv"

    result_path = save_processed_dataset(df, output_path)

    assert result_path.exists()
    reloaded = pd.read_csv(result_path)
    assert len(reloaded) == 2
    assert list(reloaded.columns) == ["timestamp", "price_tl_mwh", "solar_kw", "demand_kw"]

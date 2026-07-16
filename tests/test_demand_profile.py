"""DemandProfileGenerator için birim testleri.

Gerçek UK-DALE dosyası (channel_1.dat, ~330 MB) repoya girmiyor (.gitignore'da
data/raw/*), bu yüzden testler küçük, elle üretilmiş bir örnek .dat dosyasıyla
ve doğrudan oluşturulmuş pandas nesneleriyle çalışır.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data.demand_profile import DemandProfileGenerator


@pytest.fixture
def raw_dat_file(tmp_path: Path) -> Path:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    # 2024-01-01 00:00:00 UTC bir Pazartesi'dir. 6 saniyede bir, 1 saatlik
    # dilim için 5 örnek ölçüm (gerçek dosyada ~600 ölçüm/saat olur, test için
    # yeterli az sayıda satır kullanıyoruz).
    base_ts = 1704067200  # 2024-01-01 00:00:00 UTC
    lines = [f"{base_ts + i * 6} {200 + i * 2}" for i in range(5)]
    (raw / "channel_1.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return raw


def test_load_raw_parses_columns_and_timezone(raw_dat_file: Path) -> None:
    generator = DemandProfileGenerator(raw_dir=raw_dat_file)
    df = generator.load_raw("channel_1.dat")

    assert list(df.columns) == ["timestamp", "power_w"]
    assert len(df) == 5
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df.loc[0, "power_w"] == pytest.approx(200.0)


def test_resample_hourly_averages_power(raw_dat_file: Path) -> None:
    generator = DemandProfileGenerator(raw_dir=raw_dat_file)
    raw = generator.load_raw("channel_1.dat")
    hourly = generator.resample_hourly(raw)

    # 5 ölçüm: 200, 202, 204, 206, 208 -> ortalama 204 W -> 0.204 kW
    assert len(hourly) == 1
    assert hourly.iloc[0] == pytest.approx(0.204)


def test_compute_typical_profile_groups_by_weekday_and_hour() -> None:
    # İki farklı Pazartesi, aynı saat (10:00) için 100 kW ve 200 kW -> ortalama 150.
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2024-01-01 10:00", tz="Europe/London"),  # Pazartesi
            pd.Timestamp("2024-01-08 10:00", tz="Europe/London"),  # bir sonraki Pazartesi
        ]
    )
    hourly_kw = pd.Series([1.0, 2.0], index=index, name="demand_kw")

    generator = DemandProfileGenerator()
    profile = generator.compute_typical_profile(hourly_kw)

    assert profile.loc[(0, 10)] == pytest.approx(1.5)


def test_align_to_dates_maps_by_weekday_and_hour() -> None:
    profile = pd.Series(
        {(0, 8): 0.3, (0, 18): 0.6},  # Pazartesi 08:00 ve 18:00 için tipik değerler
        name="demand_kw",
    )
    generator = DemandProfileGenerator()

    # 2026-07-13 bir Pazartesi'dir.
    target_dates = pd.date_range("2026-07-13 08:00", periods=2, freq="10h")
    aligned = generator.align_to_dates(profile, target_dates)

    assert list(aligned.columns) == ["timestamp", "demand_kw"]
    assert aligned.loc[0, "demand_kw"] == pytest.approx(0.3)
    assert aligned.loc[1, "demand_kw"] == pytest.approx(0.6)


def test_align_to_dates_returns_zero_for_unknown_key() -> None:
    profile = pd.Series({(0, 8): 0.3}, name="demand_kw")
    generator = DemandProfileGenerator()

    target_dates = pd.date_range("2026-07-14 09:00", periods=1, freq="h")
    aligned = generator.align_to_dates(profile, target_dates)

    assert aligned.loc[0, "demand_kw"] == 0.0

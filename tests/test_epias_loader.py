"""EpiasLoader için birim testleri.

Gerçek EPİAŞ CSV dosyasına bağımlı olmamak için (o dosya .gitignore'da,
repoya girmiyor), küçük bir örnek CSV'yi test sırasında geçici olarak
oluşturup okuyoruz.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data.epias_loader import EpiasLoader

SAMPLE_CSV = (
    "Tarih;Saat;PTF (TL/MWh);PTF (USD/MWh);PTF (EUR/MWh)\n"
    "15.07.2026;00:00;3.325,00;70,88;62,03\n"
    "15.07.2026;01:00;2.717,20;57,92;50,69\n"
    "15.07.2026;02:00;1.001,00;21,34;18,67\n"
)


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "sample.csv").write_text(SAMPLE_CSV, encoding="utf-8")
    return raw


def test_load_csv_parses_turkish_number_format(raw_dir: Path) -> None:
    loader = EpiasLoader(raw_dir=raw_dir)
    df = loader.load_csv("sample.csv")

    assert list(df.columns) == ["timestamp", "price_tl_mwh"]
    assert len(df) == 3
    # '3.325,00' -> 3325.00 (binlik nokta silinir, ondalık virgül noktaya döner)
    assert df.loc[0, "price_tl_mwh"] == pytest.approx(3325.00)
    assert df.loc[2, "price_tl_mwh"] == pytest.approx(1001.00)


def test_load_csv_sorts_by_timestamp(raw_dir: Path) -> None:
    loader = EpiasLoader(raw_dir=raw_dir)
    df = loader.load_csv("sample.csv")

    assert df["timestamp"].is_monotonic_increasing


def test_load_csv_timestamp_is_datetime(raw_dir: Path) -> None:
    loader = EpiasLoader(raw_dir=raw_dir)
    df = loader.load_csv("sample.csv")

    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

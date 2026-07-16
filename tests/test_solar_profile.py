"""SolarProfileGenerator için birim testleri.

Gerçek PVWatts API'sine ağ bağımlılığı olmaması için requests.get() sahte (mock)
bir yanıtla değiştirilir — testler internet olmadan da hızlıca ve tekrarlanabilir
şekilde çalışır.
"""

import pandas as pd
import pytest

from src.data.solar_profile import SolarProfileGenerator


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def fake_pvwatts_payload():
    # 8760 saatlik dizi: ilk 24 saat gerçekçi bir gün eğrisi (gece 0, öğlen tepe),
    # geri kalanı basitçe sıfır dolgu (test amacı sadece format/hesap doğruluğu).
    day_curve = [0, 0, 0, 0, 0, 0, 100, 300, 500, 700, 800, 750,
                 700, 650, 600, 500, 400, 200, 50, 0, 0, 0, 0, 0]
    ac_hourly = day_curve + [0.0] * (8760 - 24)
    return {"errors": [], "warnings": [], "outputs": {"ac": ac_hourly}}


def test_fetch_hourly_profile_returns_8760_rows(monkeypatch, fake_pvwatts_payload):
    monkeypatch.setattr(
        "src.data.solar_profile.requests.get",
        lambda url, params, timeout: _FakeResponse(fake_pvwatts_payload),
    )

    generator = SolarProfileGenerator(api_key="DEMO_KEY", lat=41.0, lon=29.0)
    df = generator.fetch_hourly_profile()

    assert len(df) == 8760
    assert list(df.columns) == ["hour_of_year", "timestamp_tmy", "solar_kw"]


def test_fetch_hourly_profile_converts_watts_to_kw(monkeypatch, fake_pvwatts_payload):
    monkeypatch.setattr(
        "src.data.solar_profile.requests.get",
        lambda url, params, timeout: _FakeResponse(fake_pvwatts_payload),
    )

    generator = SolarProfileGenerator()
    df = generator.fetch_hourly_profile()

    # Saat 10 (indeks 10) -> 800 W -> 0.8 kW
    assert df.loc[10, "solar_kw"] == pytest.approx(0.8)
    # Gece saatleri (indeks 0) -> 0 kW
    assert df.loc[0, "solar_kw"] == pytest.approx(0.0)


def test_fetch_hourly_profile_raises_on_api_error(monkeypatch):
    monkeypatch.setattr(
        "src.data.solar_profile.requests.get",
        lambda url, params, timeout: _FakeResponse(
            {"errors": ["Invalid API key"], "outputs": {}}
        ),
    )

    generator = SolarProfileGenerator(api_key="bad_key")
    with pytest.raises(RuntimeError):
        generator.fetch_hourly_profile()


def test_align_to_dates_maps_month_day_hour(monkeypatch, fake_pvwatts_payload):
    monkeypatch.setattr(
        "src.data.solar_profile.requests.get",
        lambda url, params, timeout: _FakeResponse(fake_pvwatts_payload),
    )

    generator = SolarProfileGenerator()
    profile = generator.fetch_hourly_profile()

    target_dates = pd.date_range("2026-07-15 00:00", periods=24, freq="h")
    aligned = generator.align_to_dates(profile, target_dates)

    assert len(aligned) == 24
    assert list(aligned.columns) == ["timestamp", "solar_kw"]
    # 2026-07-15 saat 10:00 -> tipik yılın 01-01 saat 10 değeriyle eşleşmemeli,
    # ay-gün-saat eşlemesiyle kendi (07-15 10:00) değeriyle eşleşmeli.
    # fake veri sadece ilk 24 saati (01-01) dolduruyor, diğer günler 0 -> bu yüzden
    # burada sadece sütun/satır sayısı ve tip doğruluğunu kontrol ediyoruz.
    assert aligned["solar_kw"].dtype == float

"""PVWatts API (NLR/NREL) üzerinden güneş paneli saatlik üretim tahminini çeken modül.

Kaynak: https://developer.nlr.gov/docs/solar/pvwatts/v8/
Ücretsiz API key: https://developer.nlr.gov/signup/ (anında alınıyor). Test/prototipleme
için NREL'in herkese açık DEMO_KEY'i kullanılabilir (saatte 1000 istek limiti var),
ama gerçek kullanım için kendi API key'inizi almanız önerilir.

Not: PVWatts, belirli bir takvim yılına değil, seçilen konum için TMY (Typical
Meteorological Year — o bölgenin uzun dönemli ortalamasını temsil eden "tipik" bir yıl)
verisine dayanır. Bu yüzden API'den dönen 8760 saatlik seri belirli bir yılın (ör. 2026)
tarihlerine değil, soyut bir "1 Ocak - 31 Aralık" tipik yılına karşılık gelir.
`align_to_dates()` bu tipik yıl profilini gerçek hedef tarihlere (ay-gün-saat eşlemesiyle)
hizalamak için kullanılır — ör. EpiasLoader'dan gelen gerçek fiyat tarihleriyle eşleştirmek için.
"""

from __future__ import annotations

import pandas as pd
import requests


class SolarProfileGenerator:
    """PVWatts API'sinden saatlik güneş üretim (kW) profili çeken sınıf."""

    BASE_URL = "https://developer.nlr.gov/api/pvwatts/v8.json"

    def __init__(
        self,
        api_key: str = "DEMO_KEY",
        lat: float = 41.01,
        lon: float = 28.98,
        system_capacity: float = 4.0,
        module_type: int = 1,
        array_type: int = 1,
        tilt: float = 20.0,
        azimuth: float = 180.0,
        losses: float = 14.0,
    ) -> None:
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.system_capacity = system_capacity
        self.module_type = module_type
        self.array_type = array_type
        self.tilt = tilt
        self.azimuth = azimuth
        self.losses = losses

    def fetch_hourly_profile(self) -> pd.DataFrame:
        """PVWatts'tan tipik bir yıla ait saatlik AC üretim verisini (kW) çeker.

        Dönen DataFrame kolonları:
            - hour_of_year (int): 0-8759 arası saat indeksi
            - timestamp_tmy (datetime64): soyut "tipik yıl" zaman damgası
            - solar_kw (float): o saatteki AC güneş üretimi (kW)
        """
        params = {
            "api_key": self.api_key,
            "lat": self.lat,
            "lon": self.lon,
            "system_capacity": self.system_capacity,
            "module_type": self.module_type,
            "array_type": self.array_type,
            "tilt": self.tilt,
            "azimuth": self.azimuth,
            "losses": self.losses,
            "timeframe": "hourly",
            "dataset": "nsrdb",
        }
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            raise RuntimeError(f"PVWatts API hatası: {data['errors']}")

        ac_watts = data["outputs"]["ac"]
        hour_index = pd.date_range("2001-01-01", periods=len(ac_watts), freq="h")

        return pd.DataFrame(
            {
                "hour_of_year": range(len(ac_watts)),
                "timestamp_tmy": hour_index,
                "solar_kw": [w / 1000.0 for w in ac_watts],
            }
        )

    def align_to_dates(
        self, profile: pd.DataFrame, target_dates: pd.DatetimeIndex
    ) -> pd.DataFrame:
        """TMY tabanlı 8760 saatlik profili, hedef tarihlerin (ay-gün-saat) aynı
        saatine eşleyerek gerçek bir tarih aralığına (ör. EPİAŞ fiyat verisiyle
        aynı günlere) hizalar. Böylece ortam, farklı yıllara ait fiyat ve güneş
        verisini aynı takvimde birlikte kullanabilir.
        """
        lookup = profile.set_index(profile["timestamp_tmy"].dt.strftime("%m-%d %H:%M"))[
            "solar_kw"
        ]
        rows = []
        for ts in target_dates:
            key = ts.strftime("%m-%d %H:%M")
            solar_kw = float(lookup.loc[key]) if key in lookup.index else 0.0
            rows.append({"timestamp": ts, "solar_kw": solar_kw})
        return pd.DataFrame(rows)


if __name__ == "__main__":
    # Hızlı manuel doğrulama: DEMO_KEY ile İstanbul koordinatları için deneme.
    generator = SolarProfileGenerator(api_key="DEMO_KEY", lat=41.01, lon=28.98)
    yearly = generator.fetch_hourly_profile()
    print(yearly.head())
    print(f"Toplam yıllık üretim: {yearly['solar_kw'].sum():.1f} kWh")

"""UK-DALE veri setinden (gerçek ev elektrik tüketimi) saatlik ev talebi profili
üreten modül.

Kaynak: UK-DALE (UK Domestic Appliance-Level Electricity), Jack Kelly & William
Knottenbelt, Scientific Data 2015, DOI:10.1038/sdata.2015.7
İndirme: http://data.ukedc.rl.ac.uk/simplebrowse/edc/efficiency/residential/EnergyConsumption/Domestic/UK-DALE-2017/UK-DALE-FULL-disaggregated/ukdale.zip
Lisans: Creative Commons Attribution 4.0 International (CC BY 4.0)

Kullanılan dosya: house_1/channel_1.dat (evin "aggregate" / toplam güç kanalı).
Ham format: her satır "<unix_timestamp> <güç_watt>", 6 saniyede bir ölçüm.
house_1, 09/11/2012 - 26/04/2017 arası 4.3 yıllık kesintisiz kayıt içerir.

Bu modül ham 6 saniyelik ölçümü saatlik ortalamaya indirger, ardından çok yıllık
veriden haftanın günü + saat bazında bir "tipik hafta" profili (168 değerlik
lookup tablosu) çıkarır. Bu profil, EpiasLoader'dan gelen gerçek tarihlerle
(farklı takvim yılında olsa da) hizalanabilir — SolarProfileGenerator'daki
TMY hizalama mantığıyla aynı yaklaşım.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class DemandProfileGenerator:
    """UK-DALE house_1 "aggregate" kanalından tipik saatlik ev talebi (kW) profili
    çıkaran sınıf.
    """

    def __init__(self, raw_dir: Path | str = "data/raw") -> None:
        self.raw_dir = Path(raw_dir)

    def load_raw(self, filename: str = "channel_1.dat") -> pd.DataFrame:
        """UK-DALE'in ham .dat dosyasını okur.

        Dönen DataFrame kolonları:
            - timestamp (datetime64, Europe/London saat dilimi)
            - power_w (float): o andaki anlık toplam güç (Watt)
        """
        path = self.raw_dir / filename
        df = pd.read_csv(
            path,
            sep=" ",
            header=None,
            names=["unix_ts", "power_w"],
            dtype={"unix_ts": "int64", "power_w": "float32"},
        )
        df["timestamp"] = (
            pd.to_datetime(df["unix_ts"], unit="s", utc=True)
            .dt.tz_convert("Europe/London")
        )
        return df[["timestamp", "power_w"]]

    def resample_hourly(self, raw_df: pd.DataFrame) -> pd.Series:
        """6 saniyelik ham ölçümü saatlik ortalama güce (kW) indirger."""
        hourly_w = (
            raw_df.set_index("timestamp")["power_w"].resample("1h").mean().dropna()
        )
        return (hourly_w / 1000.0).rename("demand_kw")

    def compute_typical_profile(self, hourly_kw: pd.Series) -> pd.Series:
        """Çok yıllık saatlik seriden, haftanın günü + saat bazında ortalama
        alarak 168 (7 gün x 24 saat) değerlik bir "tipik hafta" profili çıkarır.

        Index: (weekday, hour) — weekday 0=Pazartesi ... 6=Pazar.
        """
        frame = hourly_kw.to_frame()
        frame["weekday"] = frame.index.weekday
        frame["hour"] = frame.index.hour
        return frame.groupby(["weekday", "hour"])["demand_kw"].mean()

    def align_to_dates(
        self, typical_profile: pd.Series, target_dates: pd.DatetimeIndex
    ) -> pd.DataFrame:
        """Tipik hafta profilini (haftanın günü + saat eşlemesiyle) hedef
        tarihlere hizalar — ör. EpiasLoader'dan gelen gerçek fiyat tarihleriyle
        aynı takvimde kullanılabilmesi için.
        """
        rows = []
        for ts in target_dates:
            key = (ts.weekday(), ts.hour)
            demand_kw = float(typical_profile.loc[key]) if key in typical_profile.index else 0.0
            rows.append({"timestamp": ts, "demand_kw": demand_kw})
        return pd.DataFrame(rows)


if __name__ == "__main__":
    # Hızlı manuel doğrulama: data/raw/channel_1.dat konmuşsa özet basar.
    generator = DemandProfileGenerator()
    raw = generator.load_raw("channel_1.dat")
    hourly = generator.resample_hourly(raw)
    profile = generator.compute_typical_profile(hourly)
    print(f"Saatlik veri noktası sayısı: {len(hourly)}")
    print(f"Ortalama günlük tüketim: {(hourly.groupby(hourly.index.date).sum()).mean():.2f} kWh")
    print("Pazartesi tipik profil (ilk 6 saat):")
    print(profile.loc[0].head(6))

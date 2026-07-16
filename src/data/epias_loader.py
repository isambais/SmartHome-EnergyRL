"""EPİAŞ Şeffaflık Platformu'ndan indirilen Piyasa Takas Fiyatı (PTF) CSV
dosyalarını okuyup ortamın beklediği saatlik fiyat serisine dönüştürür.

Veri kaynağı: https://seffaflik.epias.com.tr
(Hesap açmadan, ELEKTRİK > ELEKTRİK PİYASALARI > Piyasa Takas Fiyatı (PTF)
sayfasından CSV olarak indirilebiliyor.)

Beklenen ham dosya adı formatı: Piyasa_Takas_Fiyati-DDMMYYYY-DDMMYYYY.csv
Beklenen ham içerik formatı (noktalı virgülle ayrılmış, Türkçe sayı formatı):

    Tarih;Saat;PTF (TL/MWh);PTF (USD/MWh);PTF (EUR/MWh)
    15.07.2026;00:00;3.325,00;70,88;62,03
    15.07.2026;01:00;2.717,20;57,92;50,69
    ...
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class EpiasLoader:
    """EPİAŞ PTF CSV dosyalarını okuyup normalize eden yükleyici."""

    def __init__(self, raw_dir: Path | str = "data/raw") -> None:
        self.raw_dir = Path(raw_dir)

    def load_csv(self, filename: str) -> pd.DataFrame:
        """Tek bir EPİAŞ PTF CSV dosyasını okuyup normalize edilmiş bir
        DataFrame döndürür.

        Dönen DataFrame kolonları:
            - timestamp (datetime64): saatlik zaman damgası
            - price_tl_mwh (float): PTF, TL/MWh cinsinden
        """
        path = self.raw_dir / filename
        df = pd.read_csv(path, sep=";", encoding="utf-8")

        df["timestamp"] = pd.to_datetime(
            df["Tarih"] + " " + df["Saat"], format="%d.%m.%Y %H:%M"
        )
        df["price_tl_mwh"] = self._parse_turkish_number(df["PTF (TL/MWh)"])

        result = df[["timestamp", "price_tl_mwh"]].sort_values("timestamp")
        return result.reset_index(drop=True)

    @staticmethod
    def _parse_turkish_number(series: pd.Series) -> pd.Series:
        """'3.325,00' gibi Türkçe formatlı sayı string'lerini float'a çevirir.

        Binlik ayırıcı nokta önce silinir, ardından ondalık virgül noktaya
        çevrilir (ör. '3.325,00' -> '3325.00' -> 3325.0).
        """
        return (
            series.astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

    def load_range(self, filenames: list[str]) -> pd.DataFrame:
        """Birden fazla günlük CSV dosyasını birleştirip, zamana göre
        sıralanmış tek bir seri döndürür.

        Ortamın (SmartHomeEnergyEnv) birden fazla günü/haftayı bölüm olarak
        kullanabilmesi için tarih aralığını genişletmek üzere kullanılır.
        """
        frames = [self.load_csv(f) for f in filenames]
        combined = pd.concat(frames, ignore_index=True)
        return combined.sort_values("timestamp").reset_index(drop=True)


if __name__ == "__main__":
    # Hızlı manuel doğrulama: data/raw/ altına konan örnek dosyayı okuyup özet basar.
    loader = EpiasLoader()
    df = loader.load_csv("Piyasa_Takas_Fiyati-15072026-15072026.csv")
    print(df.head())
    print(f"Toplam satır: {len(df)}, ortalama fiyat: {df['price_tl_mwh'].mean():.2f} TL/MWh")

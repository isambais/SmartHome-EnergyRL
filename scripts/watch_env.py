"""Ortami gorsel olarak izlemek/test etmek icin projenin kalici yardimci scripti.

Bu bir demo degil, projenin resmi bir parcasi: her curriculum asamasindan
(Asama 1 - batarya arbitraji, Asama 2 - gunes+talep, Asama 3 - cihazlar)
sonra, ortamin gercekten dogru calistigini GOZLE dogrulamak icin kullanilir.
Ortam gelistikce (Gun 9, Gun 13) bu script de guncellenip ayni sekilde
calistirilmaya devam edecek.

Veri kaynagi: data/processed/aligned_dataset.csv varsa oradaki gercek EPIAS
fiyat verisinin ilk 24 saati kullanilir (build_dataset.py ile uretilir).
Dosya yoksa (henuz calistirilmadiysa), 15 Temmuz 2025'in gercek EPIAS
fiyatlarindan olusan gomulu bir yedek kullanilir - yine gercek veri, sadece
onceden kaydedilmis.

Calistirmak icin: pip install pygame
                   python watch_env.py

Kontroller (pencere acikken):
    YUKARI OK  = SARJ (bataryayi doldur)
    ASAGI OK   = DESARJ (bataryayi bosalt, sat)
    BOSLUK     = BEKLE (hicbir sey yapma)
    ESC        = cikis
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pygame

# scripts/ klasorunden calistirildiginda 'src' paketi otomatik bulunamaz;
# proje kok dizinini (bu dosyanin bir ust klasorunu) hem sys.path'e hem de
# calisma dizinine (os.chdir) ekleyerek hem import'lar hem de goreli veri
# yollari (data/processed/...) her zaman dogru calissin. Bu satirlar diger
# import'lardan sonra, src paketinin import'undan once gelmek zorunda.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

# Yedek: 15 Temmuz 2025 icin GERCEK EPIAS Piyasa Takas Fiyati (TL/MWh).
# data/processed/aligned_dataset.csv henuz uretilmediyse bu kullanilir.
FALLBACK_REAL_DAY_PRICES = np.array(
    [
        3230.00,
        3155.00,
        2910.11,
        2919.99,
        2783.64,
        2932.01,
        2843.00,
        1399.99,
        1599.98,
        1599.98,
        1401.00,
        1600.00,
        999.99,
        1599.97,
        1900.00,
        2340.00,
        2999.99,
        2919.99,
        2700.00,
        3360.00,
        3399.45,
        3399.45,
        3223.00,
        3064.00,
    ],
    dtype=np.float32,
)

PROCESSED_DATA_PATH = Path("data/processed/aligned_dataset.csv")


def load_day_prices() -> tuple[np.ndarray, str]:
    """Mumkunse gercek projeden uretilen veriyi, yoksa gomulu gercek yedegi kullanir."""
    if PROCESSED_DATA_PATH.exists():
        import pandas as pd

        df = pd.read_csv(PROCESSED_DATA_PATH)
        prices = df["price_tl_mwh"].values[:24].astype(np.float32)
        label = f"{PROCESSED_DATA_PATH} - {df['timestamp'].iloc[0]}"
        return prices, label
    return FALLBACK_REAL_DAY_PRICES, "gomulu yedek - 15 Temmuz 2025 EPIAS"


def main() -> None:
    prices, source_label = load_day_prices()
    env = SmartHomeEnergyEnv(prices, random_day=False, render_mode="human")
    obs, info = env.reset(seed=0)
    env.render()

    print("=" * 60)
    print(f"ORTAMI IZLE - veri kaynagi: {source_label}")
    print("YUKARI OK = SARJ | ASAGI OK = DESARJ | BOSLUK = BEKLE | ESC = CIKIS")
    print("=" * 60)

    total_reward = 0.0
    terminated = False

    while not terminated:
        action = None
        while action is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    env.close()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        env.close()
                        sys.exit(0)
                    elif event.key == pygame.K_UP:
                        action = np.array([1.0], dtype=np.float32)
                    elif event.key == pygame.K_DOWN:
                        action = np.array([-1.0], dtype=np.float32)
                    elif event.key == pygame.K_SPACE:
                        action = np.array([0.0], dtype=np.float32)
            env._clock.tick(30)

        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(
            f"Saat {info['hour']:>2}: fiyat={info['price_tl_kwh']:.2f} TL/kWh  "
            f"odul={reward:+.2f} TL  toplam={total_reward:+.2f} TL  SOC={obs[0]:.2f}"
        )

    print("=" * 60)
    print(f"GUN BITTI. Toplam kazancin: {total_reward:.2f} TL")
    print("(Karsilastirma: bataryayi hic kullanmasaydin kazancin 0.00 TL olurdu.)")
    print("Pencereyi kapatmak icin ESC'ye bas veya pencereyi kapat.")

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                waiting = False
        env._clock.tick(30)

    env.close()


if __name__ == "__main__":
    main()

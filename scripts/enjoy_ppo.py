"""Eğitilmiş PPO modelini pygame penceresiyle izleme scripti.

Eğitilmiş ajan her saatte kendi kararını veriyor — sen sadece izliyorsun.
watch_env.py'den farkı: klavye kontrolü yok, PPO karar veriyor.

Çalıştırmak için:
    python scripts/enjoy_ppo.py

Önce eğitim yapılmış olmalı:
    python scripts/train_ppo.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from stable_baselines3 import PPO  # noqa: E402
from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

PROCESSED_DATA_PATH = Path("data/processed/aligned_dataset.csv")

FALLBACK_PRICES = np.array(
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


def load_prices() -> np.ndarray:
    if PROCESSED_DATA_PATH.exists():
        import pandas as pd

        df = pd.read_csv(PROCESSED_DATA_PATH)
        return df["price_tl_mwh"].values.astype(np.float32)
    return FALLBACK_PRICES


def main() -> None:
    model_path = Path("models/ppo_smarthome_final.zip")
    if not model_path.exists():
        print("HATA: Model bulunamadı.")
        print("Önce 'python scripts/train_ppo.py' çalıştırın.")
        sys.exit(1)

    model = PPO.load(str(model_path))
    prices = load_prices()

    env = SmartHomeEnergyEnv(prices, random_day=False, render_mode="human")
    obs, info = env.reset(seed=0)
    env.render()

    print("=" * 55)
    print("  PPO AJANI IZLENIYOR")
    print("  ESC veya pencereyi kapat = cikis")
    print("=" * 55)

    total_reward = 0.0
    terminated = False

    while not terminated:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(
            f"Saat {info['hour']:>2}: fiyat={info['price_tl_kwh']:.2f} TL/kWh  "
            f"aksiyon={action[0]:+.2f}  odul={reward:+.2f} TL  "
            f"toplam={total_reward:+.2f} TL  SOC={obs[0]:.2f}"
        )
        time.sleep(0.5)

    print("=" * 55)
    print(f"GUN BITTI. PPO toplam kazanci: {total_reward:.2f} TL")
    print("Pencereyi kapatmak icin ESC.")

    import pygame

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

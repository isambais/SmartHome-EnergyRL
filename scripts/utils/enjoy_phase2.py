"""Eğitilmiş Aşama 2 PPO modelini pygame penceresiyle izleme scripti.

Güneş + ev talebi + batarya arbitrajı ile karar veren ajanı izler.
Hangi modeli izlemek istediğini --model parametresiyle seçebilirsin:
  ppo (varsayılan) | a2c | sac | td3

Çalıştırmak için:
    python scripts/utils/enjoy_phase2.py
    python scripts/utils/enjoy_phase2.py --model sac
    python scripts/utils/enjoy_phase2.py --model td3
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = Path("data/processed/aligned_dataset.csv")

MODEL_MAP = {
    "ppo": ("models/ppo_phase2_final.zip",         "models/ppo_phase2_vecnormalize.pkl",  "PPO"),
    "a2c": ("models/a2c_phase2_final.zip",         "models/a2c_phase2_vecnormalize.pkl",  "A2C"),
    "sac": ("models/sac_phase2_final.zip",         "models/sac_phase2_vecnormalize.pkl",  "SAC"),
    "td3": ("models/td3_phase2_final.zip",         "models/td3_phase2_vecnormalize.pkl",  "TD3"),
}


def load_data():
    df = pd.read_csv(DATA_PATH)
    return (
        df["price_tl_mwh"].values.astype(np.float32),
        df["solar_kw"].values.astype(np.float32),
        df["demand_kw"].values.astype(np.float32),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=list(MODEL_MAP), default="ppo",
                        help="Hangi modeli izleyeceğin: ppo | a2c | sac | td3")
    args = parser.parse_args()

    model_zip, vecnorm_pkl, algo_name = MODEL_MAP[args.model]
    model_path = Path(model_zip)
    stats_path = Path(vecnorm_pkl)

    if not model_path.exists():
        print(f"HATA: {model_path} bulunamadı.")
        print(f"Önce 'python scripts/train/{args.model}_phase2.py' çalıştırın.")
        sys.exit(1)

    price, solar, demand = load_data()

    def make_env():
        return SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh", random_day=False, render_mode="human",
        )

    # Algoritmaya göre model yükle
    if args.model == "ppo":
        from stable_baselines3 import PPO as Algo
    elif args.model == "a2c":
        from stable_baselines3 import A2C as Algo
    elif args.model == "sac":
        from stable_baselines3 import SAC as Algo
    else:
        from stable_baselines3 import TD3 as Algo

    model = Algo.load(str(model_path))

    venv = DummyVecEnv([make_env])
    if stats_path.exists():
        venv = VecNormalize.load(str(stats_path), venv)
        venv.training = False
        venv.norm_reward = False

    # Raw env (pygame render için)
    env = make_env()
    obs_raw, _ = env.reset(seed=0)
    env.render()

    print("=" * 60)
    print(f"  ASAMA 2 — {algo_name} AJANI IZLENIYOR")
    print(f"  Gunes + Talep + Batarya arbitraji")
    print("  ESC veya pencereyi kapat = cikis")
    print("=" * 60)

    total_reward = 0.0
    terminated = False

    while not terminated:
        obs_norm = venv.normalize_obs(obs_raw[np.newaxis])[0] if hasattr(venv, "normalize_obs") else obs_raw
        action, _ = model.predict(obs_norm, deterministic=True)
        obs_raw, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(
            f"Saat {info['hour']:>2}: fiyat={info['price_tl_kwh']:.2f} TL/kWh  "
            f"aksiyon={action[0]:+.2f}  odul={reward:+.2f} TL  "
            f"toplam={total_reward:+.2f} TL  SOC={obs_raw[0]:.2f}"
        )
        time.sleep(0.4)

    print("=" * 60)
    print(f"GUN BITTI. {algo_name} Asama2 toplam kazanci: {total_reward:.2f} TL")
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

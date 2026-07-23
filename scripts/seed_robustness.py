"""PPO'yu 5 farklı seed ile eğitip ortalama ± std raporlar.
'Model şansa mı bağlı?' sorusunu yanıtlar.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.evaluation import evaluate_policy  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"
SEEDS = [0, 1, 2, 3, 4]
TRAIN_STEPS = 50_000  # hız için kısa tutuldu


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    price_series = df["price_tl_mwh"]

    def make_env_fn():
        def _init():
            return SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")
        return _init

    results = []
    print(f"\nSeed robustlugu testi — {len(SEEDS)} seed, {TRAIN_STEPS:,} adim\n")
    print(f"  {'Seed':>5}  {'Ort Odul (TL)':>15}  {'Std':>8}")
    print(f"  {'-'*32}")

    for seed in SEEDS:
        train_env = make_vec_env(make_env_fn(), n_envs=2, seed=seed)
        eval_env = SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")

        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=3.25e-4,
            n_steps=256,
            batch_size=128,
            gamma=0.953,
            verbose=0,
            seed=seed,
        )
        model.learn(total_timesteps=TRAIN_STEPS)

        mean_r, std_r = evaluate_policy(
            model, eval_env, n_eval_episodes=20, deterministic=True
        )
        results.append(mean_r)
        print(f"  {seed:>5}  {mean_r:>+15.2f}  {std_r:>8.2f}")

    arr = np.array(results)
    print(f"  {'-'*32}")
    print(f"\n  Genel ortalama : {arr.mean():+.2f} TL")
    print(f"  Std (seedler arasi): {arr.std():.2f} TL")
    print(f"  Min / Max      : {arr.min():+.2f} / {arr.max():+.2f} TL")
    if arr.std() < 1.5:
        print("\n  SONUC: Model stabil — sonuclar seed'e bagimli degil.")
    else:
        print("\n  UYARI: Yuksek varyans — model seed'e duyarli.")


if __name__ == "__main__":
    main()
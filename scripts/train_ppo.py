from __future__ import annotations
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
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


def make_env(prices: np.ndarray, seed: int = 0):
    def _init():
        env = SmartHomeEnergyEnv(prices, random_day=True)
        return env

    return _init


def main() -> None:
    prices = load_prices()
    LOG_DIR = Path("logs/ppo_smarthome")
    MODEL_DIR = Path("models")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Eğitim ortamı (4 paralel)
    train_env = make_vec_env(make_env(prices), n_envs=4, seed=42)

    # Değerlendirme ortamı (tek)
    eval_env = SmartHomeEnergyEnv(prices, random_day=True)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "best_ppo"),
        log_path=str(LOG_DIR),
        eval_freq=2500,
        n_eval_episodes=10,
        deterministic=True,
        verbose=1,
    )

    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1,
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("=" * 55)
    print("  PPO Egitimi Basliyor")
    print(
        f"  Veri: {'gercek EPIAS' if PROCESSED_DATA_PATH.exists() else 'gomulu yedek'}"
    )
    print(f"  Log:  {LOG_DIR}")
    print(f"  Model kayit: {MODEL_DIR}")
    print("=" * 55)

    model.learn(
        total_timesteps=50_000,
        callback=eval_callback,
        progress_bar=True,
    )

    model.save(str(MODEL_DIR / "ppo_smarthome_final"))
    print("\nEgitim tamamlandi!")
    print(f"Final model: {MODEL_DIR}/ppo_smarthome_final.zip")
    print(f"TensorBoard: tensorboard --logdir {LOG_DIR}")


if __name__ == "__main__":
    main()

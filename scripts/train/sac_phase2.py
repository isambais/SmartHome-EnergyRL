"""Curriculum Aşama 2 — güneş + ev talebi ile SAC eğitimi."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3 import SAC  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

LOG_DIR = _PROJECT_ROOT / "logs" / "sac_phase2"
MODEL_DIR = _PROJECT_ROOT / "models"
DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    price = df["price_tl_mwh"].values.astype("float32")
    solar = df["solar_kw"].values.astype("float32")
    demand = df["demand_kw"].values.astype("float32")
    print(f"Veri: {len(df)} saat | güneş ort. {solar.mean():.3f} kW | talep ort. {demand.mean():.3f} kW")

    def make_env_fn():
        return SmartHomeEnergyEnv(
            price_data=price,
            solar_data=solar,
            demand_data=demand,
            price_unit="tl_per_mwh",
        )

    # ── Optuna Aşama 2 en iyi parametreler (Trial #23, 1.18 TL) ────
    LEARNING_RATE = 0.0008018536065930743
    BUFFER_SIZE   = 100_000
    BATCH_SIZE    = 128
    GAMMA         = 0.9981063075723566
    TAU           = 0.03186612494385683
    NET_ARCH_SIZE = 256

    # SAC off-policy: n_envs=1
    train_env = make_vec_env(make_env_fn, n_envs=1, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=GAMMA)

    eval_env = make_vec_env(make_env_fn, n_envs=1)
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "sac_phase2_best"),
        log_path=str(LOG_DIR),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )

    model = SAC(
        "MlpPolicy",
        train_env,
        learning_rate=LEARNING_RATE,
        buffer_size=BUFFER_SIZE,
        batch_size=BATCH_SIZE,
        gamma=GAMMA,
        tau=TAU,
        policy_kwargs=dict(net_arch=[NET_ARCH_SIZE, NET_ARCH_SIZE]),
        verbose=1,
        device="auto",
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("SAC Aşama 2 eğitimi başlıyor (300.000 adım)...")
    model.learn(total_timesteps=300_000, callback=eval_callback, progress_bar=True)
    model.save(str(MODEL_DIR / "sac_phase2_final"))
    train_env.save(str(MODEL_DIR / "sac_phase2_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'sac_phase2_final'}")


if __name__ == "__main__":
    main()

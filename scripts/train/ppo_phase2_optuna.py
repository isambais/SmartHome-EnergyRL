"""PPO Aşama 2 — Optuna en iyi parametreler (karşılaştırma için).

Optuna araması: phase2_ppo_optuna, 30 trial × 15k adım
En iyi trial: #0, değer: 1.56 TL
Parametreler: lr=2.37e-4, n_steps=128, batch=64, gamma=0.986,
              n_epochs=11, net_arch=512
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

LOG_DIR = _PROJECT_ROOT / "logs" / "ppo_phase2_optuna"
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

    # ── Optuna Aşama 2 en iyi parametreler (Trial #0, 1.56 TL) ─────
    LEARNING_RATE = 0.00023688639503640813
    N_STEPS       = 128
    BATCH_SIZE    = 64
    GAMMA         = 0.9857514384317185
    N_EPOCHS      = 11
    NET_ARCH_SIZE = 512

    train_env = make_vec_env(make_env_fn, n_envs=4, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=GAMMA)

    eval_vec = DummyVecEnv([make_env_fn])
    eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "ppo_phase2_optuna_best"),
        log_path=str(LOG_DIR),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )

    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=LEARNING_RATE,
        n_steps=N_STEPS,
        batch_size=BATCH_SIZE,
        n_epochs=N_EPOCHS,
        gamma=GAMMA,
        policy_kwargs=dict(net_arch=[NET_ARCH_SIZE, NET_ARCH_SIZE]),
        verbose=1,
        device="auto",
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("PPO Aşama 2 (OPTUNA) eğitimi başlıyor (300.000 adım)...")
    model.learn(total_timesteps=300_000, callback=eval_callback, progress_bar=True)
    model.save(str(MODEL_DIR / "ppo_phase2_optuna_final"))
    train_env.save(str(MODEL_DIR / "ppo_phase2_optuna_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'ppo_phase2_optuna_final'}")


if __name__ == "__main__":
    main()

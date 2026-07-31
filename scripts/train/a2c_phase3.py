"""Curriculum Aşama 3 — ertelenebilir yük ile A2C eğitimi.

Aşama 2'den farkları:
  - enable_deferrable=True  → aksiyon uzayı Box(2,), obs +2
  - Phase3MetricsCallback   → device_activation_rate TensorBoard'da izlenir
  - Hiperparametreler       → Aşama 2 Optuna değerleri başlangıç noktası

Eğitim sonrası model:
  models/a2c_phase3_final.zip
  models/a2c_phase3_vecnormalize.pkl
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3 import A2C  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402
from scripts.train.phase3_callback import Phase3MetricsCallback  # noqa: E402

LOG_DIR   = _PROJECT_ROOT / "logs" / "a2c_phase3"
MODEL_DIR = _PROJECT_ROOT / "models"
DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    price  = df["price_tl_mwh"].values.astype("float32")
    solar  = df["solar_kw"].values.astype("float32")
    demand = df["demand_kw"].values.astype("float32")
    print(f"Veri: {len(df)} saat | güneş ort. {solar.mean():.3f} kW | talep ort. {demand.mean():.3f} kW")

    def make_env_fn():
        return SmartHomeEnergyEnv(
            price_data=price,
            solar_data=solar,
            demand_data=demand,
            price_unit="tl_per_mwh",
            enable_deferrable=True,
            deferrable_load_power_kw=1.5,
            deferrable_load_hours=1.0,
            deferrable_window=(6, 22),
            deferrable_penalty_coef=2.0,
            max_activations_per_day=2,
        )

    # ── Hiperparametreler (Aşama 3 Optuna Trial #16, -8.38 TL) ──────
    LEARNING_RATE = 0.0002700374365646364
    N_STEPS       = 32
    GAMMA         = 0.9391728594279185
    ENT_COEF      = 0.033170321430599135
    NET_ARCH_SIZE = 512

    train_env = make_vec_env(make_env_fn, n_envs=4, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=GAMMA)

    eval_vec = DummyVecEnv([make_env_fn])
    eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "a2c_phase3_best"),
        log_path=str(LOG_DIR),
        eval_freq=5_000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )
    phase3_cb = Phase3MetricsCallback(verbose=0)

    model = A2C(
        "MlpPolicy",
        train_env,
        learning_rate=LEARNING_RATE,
        n_steps=N_STEPS,
        gamma=GAMMA,
        ent_coef=ENT_COEF,
        policy_kwargs=dict(net_arch=[NET_ARCH_SIZE, NET_ARCH_SIZE]),
        verbose=1,
        device="auto",
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("A2C Aşama 3 eğitimi başlıyor (300.000 adım)...")
    model.learn(
        total_timesteps=300_000,
        callback=[eval_callback, phase3_cb],
        progress_bar=True,
    )
    model.save(str(MODEL_DIR / "a2c_phase3_final"))
    train_env.save(str(MODEL_DIR / "a2c_phase3_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'a2c_phase3_final'}")


if __name__ == "__main__":
    main()

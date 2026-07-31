"""Curriculum Aşama 3 — ertelenebilir yük ile TD3 eğitimi.

TD3 deterministik politika + NormalActionNoise kullanır.
KRİTİK: Aşama 3'te aksiyon uzayı Box(2,) olduğundan action_noise dim=2 olmalı.
Aşama 2 scriptinden kopyalanıp n_actions otomatik alınırsa bu sorun yaşanmaz,
ama elle dim=1 yazılmışsa eğitim başta patlar — burada make_env ile alıyoruz.

Eğitim sonrası model:
  models/td3_phase3_final.zip
  models/td3_phase3_vecnormalize.pkl
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import TD3  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.noise import NormalActionNoise  # noqa: E402
from stable_baselines3.common.vec_env import VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402
from scripts.train.phase3_callback import Phase3MetricsCallback  # noqa: E402

LOG_DIR   = _PROJECT_ROOT / "logs" / "td3_phase3"
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

    # ── Hiperparametreler (Aşama 3 Optuna Trial #21, +0.46 TL) ──────
    LEARNING_RATE = 0.0005360438974044464
    BUFFER_SIZE   = 200_000
    BATCH_SIZE    = 256
    GAMMA         = 0.9907057855751791
    TAU           = 0.04365379435989359
    POLICY_DELAY  = 3
    NOISE_SIGMA   = 0.05375530290642189
    NET_ARCH_SIZE = 512

    # TD3 off-policy: n_envs=1
    train_env = make_vec_env(make_env_fn, n_envs=1, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=GAMMA)

    eval_env = make_vec_env(make_env_fn, n_envs=1)
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

    # KRİTİK: n_actions env'den alınıyor → Phase 3'te otomatik 2 olur
    n_actions = train_env.action_space.shape[0]  # 2
    action_noise = NormalActionNoise(
        mean=np.zeros(n_actions),
        sigma=NOISE_SIGMA * np.ones(n_actions),
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "td3_phase3_best"),
        log_path=str(LOG_DIR),
        eval_freq=5_000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )
    phase3_cb = Phase3MetricsCallback(verbose=0)

    model = TD3(
        "MlpPolicy",
        train_env,
        learning_rate=LEARNING_RATE,
        buffer_size=BUFFER_SIZE,
        batch_size=BATCH_SIZE,
        gamma=GAMMA,
        tau=TAU,
        action_noise=action_noise,
        policy_delay=POLICY_DELAY,
        target_policy_noise=0.2,
        target_noise_clip=0.5,
        policy_kwargs=dict(net_arch=[NET_ARCH_SIZE, NET_ARCH_SIZE]),
        verbose=1,
        device="auto",
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("TD3 Aşama 3 eğitimi başlıyor (500.000 adım)...")
    model.learn(
        total_timesteps=500_000,
        callback=[eval_callback, phase3_cb],
        progress_bar=True,
    )
    model.save(str(MODEL_DIR / "td3_phase3_final"))
    train_env.save(str(MODEL_DIR / "td3_phase3_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'td3_phase3_final'}")


if __name__ == "__main__":
    main()

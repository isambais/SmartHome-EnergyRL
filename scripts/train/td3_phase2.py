"""TD3 (Twin Delayed DDPG) — Curriculum Aşama 2.

SAC ile karşılaştırma için eklendi. Her ikisi de off-policy, sürekli aksiyon.
Temel fark:
  - TD3: deterministik politika + hedef gürültüsü + gecikmiş aktör güncellemesi
  - SAC: stokastik politika + entropi maksimizasyonu

Beklenti: SAC daha iyi exploration yapabilir, TD3 daha stabil öğrenebilir.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3 import TD3  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.noise import NormalActionNoise  # noqa: E402
from stable_baselines3.common.vec_env import VecNormalize  # noqa: E402
import numpy as np  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

LOG_DIR = _PROJECT_ROOT / "logs" / "td3_phase2"
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

    # ── Optuna Aşama 2 en iyi parametreler (Trial #22, 2.31 TL) ────
    LEARNING_RATE = 0.00028922914898910486
    BUFFER_SIZE   = 50_000
    BATCH_SIZE    = 256
    GAMMA         = 0.997657497320845
    TAU           = 0.011011220856353018
    POLICY_DELAY  = 1
    NOISE_SIGMA   = 0.22524286000415317
    NET_ARCH_SIZE = 512

    # TD3 off-policy: n_envs=1
    train_env = make_vec_env(make_env_fn, n_envs=1, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=GAMMA)

    eval_env = make_vec_env(make_env_fn, n_envs=1)
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

    n_actions = train_env.action_space.shape[0]
    action_noise = NormalActionNoise(
        mean=np.zeros(n_actions),
        sigma=NOISE_SIGMA * np.ones(n_actions),
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "td3_phase2_best"),
        log_path=str(LOG_DIR),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )

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

    print("TD3 Aşama 2 eğitimi başlıyor (300.000 adım)...")
    model.learn(total_timesteps=300_000, callback=eval_callback, progress_bar=True)
    model.save(str(MODEL_DIR / "td3_phase2_final"))
    train_env.save(str(MODEL_DIR / "td3_phase2_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'td3_phase2_final'}")


if __name__ == "__main__":
    main()

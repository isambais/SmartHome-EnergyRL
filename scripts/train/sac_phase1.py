"""SAC eğitimi — Phase 1, yeni gerçek dünya ortamıyla (56 boyut obs)."""

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

LOG_DIR = _PROJECT_ROOT / "logs" / "sac_smarthome"
MODEL_DIR = _PROJECT_ROOT / "models"
DATA_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    price_series = df["price_tl_mwh"].values.astype("float32")

    def make_env_fn():
        return SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")

    # SAC off-policy: n_envs=1
    train_env = make_vec_env(make_env_fn, n_envs=1, seed=42)
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=0.95)

    eval_env = make_vec_env(make_env_fn, n_envs=1)
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, training=False)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "sac_best"),
        log_path=str(LOG_DIR),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )

    model = SAC(
        "MlpPolicy",
        train_env,
        learning_rate=3e-4,
        buffer_size=200_000,
        batch_size=256,
        gamma=0.95,
        policy_kwargs=dict(net_arch=[256, 256]),
        verbose=1,
        device="cpu",  # torch 2.12.0+cpu — CUDA wheels mevcut değil
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("SAC Phase 1 eğitimi başlıyor (500.000 adım, CPU)...")
    print(f"Obs boyutu: {train_env.observation_space.shape[0]}  (beklenen: 56)")
    model.learn(total_timesteps=500_000, callback=eval_callback, progress_bar=True)
    model.save(str(MODEL_DIR / "sac_smarthome_final"))
    train_env.save(str(MODEL_DIR / "sac_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'sac_smarthome_final'}")


if __name__ == "__main__":
    main()

"""A2C eğitimi — gerçek EPIAS 2024 verisiyle, PPO ile karşılaştırma için."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import pandas as pd  # noqa: E402
from stable_baselines3 import A2C  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

LOG_DIR = _PROJECT_ROOT / "logs" / "a2c_smarthome"
MODEL_DIR = _PROJECT_ROOT / "models"
DATA_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    price_series = df["price_tl_mwh"].values.astype("float32")
    print(f"Veri yüklendi: {len(df)} saat, ort. {price_series.mean():.1f} TL/MWh")

    train_env = make_vec_env(
        lambda: SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh"),
        n_envs=4,
        seed=42,
    )
    train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=0.99)

    eval_vec = DummyVecEnv(
        [lambda: SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")]
    )
    eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODEL_DIR / "a2c_best"),
        log_path=str(LOG_DIR),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )

    model = A2C(
        "MlpPolicy",
        train_env,
        learning_rate=7e-4,
        n_steps=32,
        gamma=0.99,
        ent_coef=0.01,
        policy_kwargs=dict(net_arch=[256, 256]),
        verbose=1,
        tensorboard_log=str(LOG_DIR),
        seed=42,
    )

    print("A2C eğitimi başlıyor (500.000 adım)...")
    model.learn(total_timesteps=500_000, callback=eval_callback, progress_bar=True)
    model.save(str(MODEL_DIR / "a2c_smarthome_final"))
    train_env.save(str(MODEL_DIR / "a2c_vecnormalize.pkl"))
    print(f"Model kaydedildi: {MODEL_DIR / 'a2c_smarthome_final'}")


if __name__ == "__main__":
    main()
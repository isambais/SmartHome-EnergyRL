"""Optuna hiperparametre araması — Curriculum Aşama 2 (77 boyutlu gözlem).

Phase 1'in optimal parametreleri Phase 2 için optimal olmayabilir:
77 boyutlu gözlem uzayı, değişken verimlilik ve döngü cezası farklı
öğrenme hızı, gamma ve ağ boyutu gerektirebilir.

Kullanım:
    python scripts/optuna_phase2.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import optuna  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402
from stable_baselines3.common.callbacks import EvalCallback  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"
N_TRIALS = 30
TIMESTEPS_PER_TRIAL = 15_000


def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return (
        df["price_tl_mwh"].values.astype("float32"),
        df["solar_kw"].values.astype("float32"),
        df["demand_kw"].values.astype("float32"),
    )


def objective(trial: optuna.Trial) -> float:
    price, solar, demand = load_data()

    lr = trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True)
    n_steps = trial.suggest_categorical("n_steps", [128, 256, 512])
    batch_size = trial.suggest_categorical("batch_size", [64, 128, 256])
    gamma = trial.suggest_float("gamma", 0.90, 0.999)
    n_epochs = trial.suggest_int("n_epochs", 5, 15)
    net_arch_size = trial.suggest_categorical("net_arch_size", [128, 256, 512])

    # batch_size <= n_steps * n_envs
    if batch_size > n_steps * 4:
        return float("-inf")

    def make_env_fn():
        return SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )

    try:
        train_env = make_vec_env(make_env_fn, n_envs=4, seed=trial.number)
        train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=gamma)

        eval_vec = DummyVecEnv([make_env_fn])
        eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=lr,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            policy_kwargs=dict(net_arch=[net_arch_size, net_arch_size]),
            verbose=0,
            seed=trial.number,
        )
        model.learn(total_timesteps=TIMESTEPS_PER_TRIAL)

        # Manuel değerlendirme
        env_eval = SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh", random_day=True,
        )
        rewards = []
        for i in range(10):
            obs, _ = env_eval.reset(seed=i)
            done = False
            ep_r = 0.0
            while not done:
                obs_norm = eval_env.normalize_obs(obs[None])[0]
                action, _ = model.predict(obs_norm, deterministic=True)
                obs, r, done, _, _ = env_eval.step(action)
                ep_r += r
            rewards.append(ep_r)

        import numpy as np
        mean_r = float(np.mean(rewards))
        train_env.close()
        eval_env.close()
        return mean_r

    except Exception as e:
        print(f"Trial {trial.number} hata: {e}")
        return float("-inf")


def main() -> None:
    study = optuna.create_study(
        direction="maximize",
        study_name="phase2_ppo_optuna",
        storage=f"sqlite:///{_PROJECT_ROOT}/logs/optuna_phase2.db",
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print(f"\n{'='*50}")
    print(f"En iyi trial: #{study.best_trial.number}")
    print(f"En iyi değer: {study.best_value:.2f} TL")
    print("En iyi parametreler:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

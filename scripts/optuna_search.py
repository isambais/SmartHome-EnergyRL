"""Optuna ile PPO hiperparametre araması.
Her deneme 10.000 adım eğitip ortalama ödülü döndürür.
En iyi 20 denemeden kazanan set raporlanır.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
import optuna  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.evaluation import evaluate_policy  # noqa: E402
from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"
TRAIN_STEPS = 10_000
N_TRIALS = 20

df = pd.read_csv(DATA_PATH)
price_series = df["price_tl_mwh"]

def make_env_fn():
    def _init():
        return SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")
    return _init

def objective(trial: optuna.Trial) -> float:
    lr = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
    n_steps = trial.suggest_categorical("n_steps", [256, 512, 1024, 2048])
    batch_size = trial.suggest_categorical("batch_size", [32, 64, 128])
    gamma = trial.suggest_float("gamma", 0.95, 0.999)
    # batch_size n_steps'ten büyük olamaz
    if batch_size > n_steps:
        raise optuna.exceptions.TrialPruned()

    train_env = make_vec_env(make_env_fn(), n_envs=2, seed=42)
    eval_env = SmartHomeEnergyEnv(price_data=price_series, price_unit="tl_per_mwh")

    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=lr,
        n_steps=n_steps,
        batch_size=batch_size,
        gamma=gamma,
        verbose=0,
        seed=42,
    )
    model.learn(total_timesteps=TRAIN_STEPS)

    mean_reward, _ = evaluate_policy(
        model, eval_env, n_eval_episodes=10, deterministic=True
    )
    return float(mean_reward)


def main() -> None:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print(f"\nEn iyi deneme: #{study.best_trial.number}")
    print(f"En iyi ortalama odül: {study.best_value:.2f} TL")
    print("Hiperparametreler:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
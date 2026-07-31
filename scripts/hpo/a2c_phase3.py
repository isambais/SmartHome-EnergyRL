"""Optuna hiperparametre araması — A2C, Curriculum Aşama 3 (ertelenebilir yük) v2.

v2 değişiklikleri:
  - n_steps aralığı genişletildi: max 128 → max 512 (küçük n_steps Phase 3'ün
    uzun horizon'unu kapsamıyordu; v1'de Trial #16 n_steps=32 seçti, yetersiz)
  - gae_lambda eklendi (0.90-0.99)
  - vf_coef eklendi (0.25-0.75)
  - ent_coef üst sınırı 0.05 → 0.1 (daha fazla keşif)
  - Yeni study adı: phase3_a2c_optuna_v2

Kullanım:
    python scripts/hpo/a2c_phase3.py

Sonuçlar:
    logs/optuna_a2c_phase3_v2.db
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import numpy as np  # noqa: E402
import optuna  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import A2C  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"
N_TRIALS             = 30
TIMESTEPS_PER_TRIAL  = 15_000


def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return (
        df["price_tl_mwh"].values.astype("float32"),
        df["solar_kw"].values.astype("float32"),
        df["demand_kw"].values.astype("float32"),
    )


def make_phase3_env(price, solar, demand):
    return SmartHomeEnergyEnv(
        price_data=price,
        solar_data=solar,
        demand_data=demand,
        price_unit="tl_per_mwh",
        enable_deferrable=True,
        deferrable_penalty_coef=2.0,
        max_activations_per_day=2,
    )


def objective(trial: optuna.Trial) -> float:
    price, solar, demand = load_data()

    lr         = trial.suggest_float("learning_rate", 5e-5, 5e-4, log=True)
    n_steps    = trial.suggest_categorical("n_steps", [64, 128, 256, 512])
    gamma      = trial.suggest_float("gamma", 0.90, 0.999)
    ent_coef   = trial.suggest_float("ent_coef", 0.0, 0.1)
    gae_lambda = trial.suggest_float("gae_lambda", 0.90, 0.99)
    vf_coef    = trial.suggest_float("vf_coef", 0.25, 0.75)
    net_arch   = trial.suggest_categorical("net_arch_size", [256, 512])

    def make_env_fn():
        return make_phase3_env(price, solar, demand)

    try:
        train_env = make_vec_env(make_env_fn, n_envs=4, seed=trial.number)
        train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=gamma)

        eval_vec = DummyVecEnv([make_env_fn])
        eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

        model = A2C(
            "MlpPolicy",
            train_env,
            learning_rate=lr,
            n_steps=n_steps,
            gamma=gamma,
            ent_coef=ent_coef,
            gae_lambda=gae_lambda,
            vf_coef=vf_coef,
            policy_kwargs=dict(net_arch=[net_arch, net_arch]),
            verbose=0,
            seed=trial.number,
        )
        model.learn(total_timesteps=TIMESTEPS_PER_TRIAL)

        env_eval = make_phase3_env(price, solar, demand)
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

        train_env.close()
        eval_env.close()
        return float(np.mean(rewards))

    except Exception as e:
        print(f"Trial {trial.number} hata: {e}")
        return float("-inf")


def main() -> None:
    study = optuna.create_study(
        direction="maximize",
        study_name="phase3_a2c_optuna_v2",
        storage=f"sqlite:///{_PROJECT_ROOT}/logs/optuna_a2c_phase3_v2.db",
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print(f"\n{'='*50}")
    print(f"A2C Phase 3 v2 — En iyi trial: #{study.best_trial.number}")
    print(f"En iyi değer: {study.best_value:.2f} TL")
    print("En iyi parametreler:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

"""Optuna hiperparametre araması — TD3, Curriculum Aşama 3 (ertelenebilir yük).

KRİTİK: Aşama 3'te aksiyon uzayı Box(2,) — action_noise dim=2 olmalı.
        n_actions env'den otomatik alınıyor.

Kullanım:
    python scripts/hpo/td3_phase3.py

Sonuçlar:
    logs/optuna_td3_phase3.db
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
from stable_baselines3 import TD3  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402
from stable_baselines3.common.noise import NormalActionNoise  # noqa: E402
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

    lr           = trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True)
    buffer_size  = trial.suggest_categorical("buffer_size", [50_000, 100_000, 200_000])
    batch_size   = trial.suggest_categorical("batch_size", [128, 256, 512])
    gamma        = trial.suggest_float("gamma", 0.90, 0.999)
    tau          = trial.suggest_float("tau", 0.001, 0.05)
    policy_delay = trial.suggest_int("policy_delay", 1, 3)
    noise_sigma  = trial.suggest_float("noise_sigma", 0.05, 0.3)
    net_arch     = trial.suggest_categorical("net_arch_size", [128, 256, 512])

    def make_env_fn():
        return make_phase3_env(price, solar, demand)

    try:
        train_env = make_vec_env(make_env_fn, n_envs=1, seed=trial.number)
        train_env = VecNormalize(train_env, norm_obs=True, norm_reward=True, gamma=gamma)

        eval_vec = DummyVecEnv([make_env_fn])
        eval_env = VecNormalize(eval_vec, norm_obs=True, norm_reward=False, training=False)

        # KRİTİK: n_actions env'den alınıyor → Phase 3'te 2
        n_actions = train_env.action_space.shape[0]
        action_noise = NormalActionNoise(
            mean=np.zeros(n_actions),
            sigma=noise_sigma * np.ones(n_actions),
        )

        model = TD3(
            "MlpPolicy",
            train_env,
            learning_rate=lr,
            buffer_size=buffer_size,
            batch_size=batch_size,
            gamma=gamma,
            tau=tau,
            action_noise=action_noise,
            policy_delay=policy_delay,
            target_policy_noise=0.2,
            target_noise_clip=0.5,
            policy_kwargs=dict(net_arch=[net_arch, net_arch]),
            verbose=0,
            device="auto",
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
        study_name="phase3_td3_optuna",
        storage=f"sqlite:///{_PROJECT_ROOT}/logs/optuna_td3_phase3.db",
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print(f"\n{'='*50}")
    print(f"TD3 Phase 3 — En iyi trial: #{study.best_trial.number}")
    print(f"En iyi değer: {study.best_value:.2f} TL")
    print("En iyi parametreler:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

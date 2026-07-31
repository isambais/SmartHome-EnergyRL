"""Best model vs final model karşılaştırması — Phase 3."""
import sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from stable_baselines3 import PPO, A2C, SAC, TD3
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from src.env.energy_env import SmartHomeEnergyEnv

df = pd.read_csv("data/processed/aligned_dataset.csv")
price = df["price_tl_mwh"].values
solar = df["solar_kw"].values
demand = df["demand_kw"].values


def make_env():
    return SmartHomeEnergyEnv(
        price_data=price, solar_data=solar, demand_data=demand,
        price_unit="tl_per_mwh", enable_deferrable=True,
        deferrable_load_power_kw=1.5, deferrable_load_hours=1.0,
        deferrable_window=(6, 22), deferrable_penalty_coef=2.0,
        max_activations_per_day=2, random_day=True,
    )


def eval_model(algo_cls, model_path, stats_path, n_days=90, seed=42):
    model = algo_cls.load(model_path)
    dummy = DummyVecEnv([make_env])
    venv = VecNormalize.load(stats_path, dummy)
    venv.training = False
    venv.norm_reward = False
    rewards = []
    for i in range(n_days):
        env = make_env()
        obs, _ = env.reset(seed=seed + i)
        done = False
        ep_r = 0.0
        while not done:
            obs_n = venv.normalize_obs(obs[np.newaxis])[0]
            action, _ = model.predict(obs_n, deterministic=True)
            obs, r, done, _, _ = env.step(action)
            ep_r += r
        rewards.append(ep_r)
    return float(np.mean(rewards)), float(np.std(rewards))


configs = [
    ("PPO  final ", PPO, "models/ppo_phase3_final.zip",           "models/ppo_phase3_vecnormalize.pkl"),
    ("PPO  best  ", PPO, "models/ppo_phase3_best/best_model.zip", "models/ppo_phase3_vecnormalize.pkl"),
    ("A2C  final ", A2C, "models/a2c_phase3_final.zip",           "models/a2c_phase3_vecnormalize.pkl"),
    ("A2C  best  ", A2C, "models/a2c_phase3_best/best_model.zip", "models/a2c_phase3_vecnormalize.pkl"),
    ("TD3  final ", TD3, "models/td3_phase3_final.zip",           "models/td3_phase3_vecnormalize.pkl"),
    ("TD3  best  ", TD3, "models/td3_phase3_best/best_model.zip", "models/td3_phase3_vecnormalize.pkl"),
    ("SAC  final ", SAC, "models/sac_phase3_final.zip",           "models/sac_phase3_vecnormalize.pkl"),
    ("SAC  best  ", SAC, "models/sac_phase3_best/best_model.zip", "models/sac_phase3_vecnormalize.pkl"),
]

print(f"\n{'Politika':<16} {'Ort (TL)':>9} {'Std':>7}")
print("-" * 35)
for name, cls, mp, sp in configs:
    mean, std = eval_model(cls, mp, sp)
    marker = " ◄" if "best" in name and mean > 0 else ""
    print(f"{name:<16} {mean:>+9.2f} {std:>7.2f}{marker}")

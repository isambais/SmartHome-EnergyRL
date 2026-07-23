"""Politika değerlendirici — EPIAS 2024 gerçek verisiyle."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

Policy = Callable[[np.ndarray, SmartHomeEnergyEnv], np.ndarray]

DATA_PATH = Path("data/epias_2024.csv")

FALLBACK_PRICES = np.array(
    [3230,3155,2910,2919,2783,2932,2843,1399,1599,1599,
     1401,1600,999,1599,1900,2340,2999,2919,2700,3360,
     3399,3399,3223,3064], dtype=np.float32,
)


def load_prices() -> np.ndarray:
    if DATA_PATH.exists():
        import pandas as pd
        df = pd.read_csv(DATA_PATH)
        print(f"Veri: {DATA_PATH} ({len(df)} saat)")
        return df["price_tl_mwh"].values.astype(np.float32)
    print("UYARI: epias_2024.csv bulunamadi, fallback kullaniliyor.")
    return FALLBACK_PRICES


# --- Politikalar ---

def hold_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    return np.array([0.0], dtype=np.float32)


def random_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    return env.action_space.sample()


def threshold_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    prices = obs[1:]
    low = np.percentile(prices, 30)
    high = np.percentile(prices, 70)
    current_price = float(env._current_day_prices[env.t])
    if current_price <= low:
        return np.array([1.0], dtype=np.float32)
    elif current_price >= high:
        return np.array([-1.0], dtype=np.float32)
    return np.array([0.0], dtype=np.float32)


def make_ppo_policy() -> Policy:
    """PPO modelini VecNormalize ile yükle."""
    from stable_baselines3 import PPO as _PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/ppo_smarthome_final.zip")
    stats_path = Path("models/ppo_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _PPO.load(str(model_path))
    _venv = None
    if stats_path.exists():
        prices = load_prices()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(price_data=prices, price_unit="tl_per_mwh")])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_a2c_policy() -> Policy:
    """A2C modelini VecNormalize ile yükle."""
    from stable_baselines3 import A2C as _A2C
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/a2c_smarthome_final.zip")
    stats_path = Path("models/a2c_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _A2C.load(str(model_path))
    _venv = None
    if stats_path.exists():
        prices = load_prices()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(price_data=prices, price_unit="tl_per_mwh")])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy

def make_sac_policy() -> Policy:
    """SAC modelini VecNormalize ile yükle."""
    from stable_baselines3 import SAC as _SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/sac_smarthome_final.zip")
    stats_path = Path("models/sac_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _SAC.load(str(model_path))
    _venv = None
    if stats_path.exists():
        prices = load_prices()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(price_data=prices, price_unit="tl_per_mwh")])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy

# --- Değerlendirme ---

def evaluate(
    policy: Policy,
    prices: np.ndarray,
    n_days: int = 30,
    seed: int = 42,
) -> dict[str, float]:
    env = SmartHomeEnergyEnv(prices, random_day=True, price_unit="tl_per_mwh")
    rewards = []
    for i in range(n_days):
        obs, _ = env.reset(seed=seed + i)
        terminated = False
        episode_reward = 0.0
        while not terminated:
            action = policy(obs, env)
            obs, reward, terminated, _, _ = env.step(action)
            episode_reward += reward
        rewards.append(episode_reward)
    return {
        "mean": float(np.mean(rewards)),
        "std": float(np.std(rewards)),
        "min": float(np.min(rewards)),
        "max": float(np.max(rewards)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    prices = load_prices()
    n = args.days

    policies: list[tuple[str, Policy]] = [
        ("Bekle (hold)    ", hold_policy),
        ("Rastgele        ", random_policy),
        ("Esik (threshold)", threshold_policy),
        ("PPO             ", make_ppo_policy()),
        ("A2C             ", make_a2c_policy()),
        ("SAC             ", make_sac_policy()),
    ]

    print(f"\n{'='*58}")
    print(f"  Politika Karsilastirmasi — {n} gun (EPIAS 2026 verisi)")
    print(f"{'='*58}")
    print(f"  {'Politika':<22} {'Ort (TL)':>9} {'Std':>7} {'Min':>7} {'Maks':>7}")
    print(f"  {'-'*53}")

    for name, policy in policies:
        stats = evaluate(policy, prices, n_days=n)
        print(
            f"  {name:<22} {stats['mean']:>+9.2f} {stats['std']:>7.2f} "
            f"{stats['min']:>+7.2f} {stats['max']:>+7.2f}"
        )

    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
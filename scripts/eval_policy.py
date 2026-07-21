"""Herhangi bir politikayı SmartHomeEnergyEnv üzerinde çok sayıda gün boyunca
değerlendiren yardımcı script.

Kullanım:
    python scripts/eval_policy.py              # varsayılan: rastgele + eşik politikası
    python scripts/eval_policy.py --days 50    # 50 gün üzerinde değerlendir

Gün 8 kalibrasyon checkpoint'i ve ileriki karşılaştırmalar için altyapı sağlar.
"""

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

PROCESSED_DATA_PATH = Path("data/processed/aligned_dataset.csv")

FALLBACK_PRICES = np.array(
    [
        3230.00,
        3155.00,
        2910.11,
        2919.99,
        2783.64,
        2932.01,
        2843.00,
        1399.99,
        1599.98,
        1599.98,
        1401.00,
        1600.00,
        999.99,
        1599.97,
        1900.00,
        2340.00,
        2999.99,
        2919.99,
        2700.00,
        3360.00,
        3399.45,
        3399.45,
        3223.00,
        3064.00,
    ],
    dtype=np.float32,
)


def load_prices() -> np.ndarray:
    if PROCESSED_DATA_PATH.exists():
        import pandas as pd

        df = pd.read_csv(PROCESSED_DATA_PATH)
        return df["price_tl_mwh"].values.astype(np.float32)
    return FALLBACK_PRICES


# --- Politikalar ---


def random_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    """Tamamen rastgele aksiyon."""
    return env.action_space.sample()


def threshold_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    """Basit eşik politikası: ucuza şarj et, pahalıya deşarj et.

    Günün fiyatlarına bakarak alt %30 → şarj, üst %30 → deşarj.
    """
    prices = obs[1:]  # obs[0] = SOC, obs[1:] = fiyatlar
    low = np.percentile(prices, 30)
    high = np.percentile(prices, 70)
    current_price = float(env._current_day_prices[env.t])

    if current_price <= low:
        return np.array([1.0], dtype=np.float32)
    elif current_price >= high:
        return np.array([-1.0], dtype=np.float32)
    return np.array([0.0], dtype=np.float32)


def hold_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    """Hiçbir şey yapma (baseline alt sınırı)."""
    return np.array([0.0], dtype=np.float32)


# --- Değerlendirme ---


def evaluate(
    policy: Policy,
    prices: np.ndarray,
    n_days: int = 30,
    seed: int = 42,
) -> dict[str, float]:
    """Politikayı n_days gün boyunca çalıştır, istatistikleri döndür."""
    env = SmartHomeEnergyEnv(prices, random_day=True)
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
    parser = argparse.ArgumentParser(description="Politika değerlendirici")
    parser.add_argument(
        "--days", type=int, default=30, help="Değerlendirilecek gün sayısı"
    )
    args = parser.parse_args()

    prices = load_prices()
    n = args.days

    policies: list[tuple[str, Policy]] = [
        ("Bekle (hold)   ", hold_policy),
        ("Rastgele       ", random_policy),
        ("Eşik (threshold)", threshold_policy),
    ]

    print(f"\n{'='*55}")
    print(f"  Politika Karşılaştırması — {n} gün")
    print(f"{'='*55}")
    print(f"  {'Politika':<22} {'Ort (TL)':>9} {'Std':>7} {'Min':>7} {'Maks':>7}")
    print(f"  {'-'*50}")

    for name, policy in policies:
        stats = evaluate(policy, prices, n_days=n)
        print(
            f"  {name:<22} {stats['mean']:>+9.2f} {stats['std']:>7.2f} "
            f"{stats['min']:>+7.2f} {stats['max']:>+7.2f}"
        )

    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()

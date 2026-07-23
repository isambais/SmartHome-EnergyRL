"""5 → 6 politikayı karşılaştıran bar chart — PNG olarak kaydeder."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from stable_baselines3 import A2C, PPO, SAC  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH = _PROJECT_ROOT / "data" / "epias_2024.csv"
OUT_PATH = _PROJECT_ROOT / "docs" / "policy_comparison.png"
N_DAYS = 50
SEED = 42


def load_venv(stats_path: Path, prices: np.ndarray):
    if not stats_path.exists():
        return None
    dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(price_data=prices, price_unit="tl_per_mwh")])
    venv = VecNormalize.load(str(stats_path), dummy)
    venv.training = False
    venv.norm_reward = False
    return venv


def run_policy(policy_fn, prices, n_days=N_DAYS):
    env = SmartHomeEnergyEnv(prices, random_day=True, price_unit="tl_per_mwh")
    rewards = []
    for i in range(n_days):
        obs, _ = env.reset(seed=SEED + i)
        done = False
        ep_r = 0.0
        while not done:
            action = policy_fn(obs, env)
            obs, r, done, _, _ = env.step(action)
            ep_r += r
        rewards.append(ep_r)
    return np.array(rewards)


def main():
    df = pd.read_csv(DATA_PATH)
    prices = df["price_tl_mwh"].values.astype("float32")

    ppo_model = PPO.load(str(_PROJECT_ROOT / "models" / "ppo_smarthome_final"))
    ppo_venv = load_venv(_PROJECT_ROOT / "models" / "ppo_vecnormalize.pkl", prices)

    a2c_model = A2C.load(str(_PROJECT_ROOT / "models" / "a2c_smarthome_final"))
    a2c_venv = load_venv(_PROJECT_ROOT / "models" / "a2c_vecnormalize.pkl", prices)

    sac_model = SAC.load(str(_PROJECT_ROOT / "models" / "sac_smarthome_final"))
    sac_venv = load_venv(_PROJECT_ROOT / "models" / "sac_vecnormalize.pkl", prices)

    def norm(venv, obs):
        return venv.normalize_obs(obs[np.newaxis])[0] if venv else obs

    policies = {
        "Bekle":    lambda obs, env: np.array([0.0], dtype="float32"),
        "Rastgele": lambda obs, env: env.action_space.sample(),
        "Eşik":     lambda obs, env: _threshold(obs, env),
        "PPO":      lambda obs, env: ppo_model.predict(norm(ppo_venv, obs), deterministic=True)[0],
        "A2C":      lambda obs, env: a2c_model.predict(norm(a2c_venv, obs), deterministic=True)[0],
        "SAC":      lambda obs, env: sac_model.predict(norm(sac_venv, obs), deterministic=True)[0],
    }

    color_map = {
        "Bekle":    "#6c757d",
        "Rastgele": "#dc3545",
        "Eşik":     "#fd7e14",
        "PPO":      "#0d6efd",
        "A2C":      "#198754",
        "SAC":      "#9b59b6",
    }

    means, stds, colors = [], [], []
    for name, fn in policies.items():
        r = run_policy(fn, prices)
        means.append(r.mean())
        stds.append(r.std())
        colors.append(color_map[name])
        print(f"{name:10s}: {r.mean():+.2f} ± {r.std():.2f} TL")

    # --- Grafik ---
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(policies))
    bars = ax.bar(x, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="white", linewidth=0.8, width=0.55)

    for i, (bar, m) in enumerate(zip(bars, means)):
        ypos = m + stds[i] + 0.4 if m >= 0 else m - stds[i] - 1.2
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                f"{m:+.1f} TL", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(list(policies.keys()), fontsize=12)
    ax.set_ylabel("Ortalama Günlük Ödül (TL)", fontsize=11)
    ax.set_title(f"Politika Karşılaştırması — {N_DAYS} Gün (EPIAS Gerçek Verisi)",
                 fontsize=13, fontweight="bold", pad=14)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(min(means) - max(stds) - 4, max(means) + max(stds) + 6)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"\nGrafik kaydedildi: {OUT_PATH}")


def _threshold(obs, env):
    prices = obs[1:]
    low = np.percentile(prices, 30)
    high = np.percentile(prices, 70)
    cur = float(env._current_day_prices[env.t])
    if cur <= low:
        return np.array([1.0], dtype="float32")
    elif cur >= high:
        return np.array([-1.0], dtype="float32")
    return np.array([0.0], dtype="float32")


if __name__ == "__main__":
    main()
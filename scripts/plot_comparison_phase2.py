"""Curriculum Aşama 2 — tüm algoritmaları karşılaştıran bar chart.

Politikalar: Bekle, Rastgele, Eşik, PPO, A2C, SAC, TD3 (Phase 2 modelleri)
Çıktı: docs/policy_comparison_phase2.png
"""

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
from stable_baselines3 import A2C, PPO, SAC, TD3  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize  # noqa: E402

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

DATA_PATH  = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"
OUT_PATH   = _PROJECT_ROOT / "docs" / "policy_comparison_phase2.png"
OUT_PATH2  = _PROJECT_ROOT / "docs" / "policy_comparison_phase1_vs_phase2.png"
N_DAYS = 50
SEED   = 42


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return (
        df["price_tl_mwh"].values.astype("float32"),
        df["solar_kw"].values.astype("float32"),
        df["demand_kw"].values.astype("float32"),
    )


def load_venv(stats_path: Path, price, solar=None, demand=None):
    if not stats_path.exists():
        return None
    if solar is not None:
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
    else:
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, price_unit="tl_per_mwh",
        )])
    venv = VecNormalize.load(str(stats_path), dummy)
    venv.training = False
    venv.norm_reward = False
    return venv


def run_episode(policy_fn, env):
    rewards = []
    for i in range(N_DAYS):
        obs, _ = env.reset(seed=SEED + i)
        done, ep_r = False, 0.0
        while not done:
            action = policy_fn(obs, env)
            obs, r, done, _, _ = env.step(action)
            ep_r += r
        rewards.append(ep_r)
    return np.array(rewards)


def threshold_phase2(obs, env):
    prices = obs[8:32]
    low, high = np.percentile(prices, 30), np.percentile(prices, 70)
    cur = float(env._current_day_prices[env.t])
    if cur <= low:
        return np.array([1.0], dtype="float32")
    elif cur >= high:
        return np.array([-1.0], dtype="float32")
    return np.array([0.0], dtype="float32")


def make_policy(model, venv):
    def _fn(obs, env):
        obs_n = venv.normalize_obs(obs[np.newaxis])[0] if venv else obs
        return model.predict(obs_n, deterministic=True)[0]
    return _fn


# ── Ana fonksiyon ─────────────────────────────────────────────────────────────

def main():
    price, solar, demand = load_data()

    # Phase 2 ortamı
    def make_env():
        return SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh", random_day=True,
        )

    env = make_env()

    # Model yükleme
    models_dir = _PROJECT_ROOT / "models"

    ppo_m   = PPO.load(str(models_dir / "ppo_phase2_final"))
    ppo_v   = load_venv(models_dir / "ppo_phase2_vecnormalize.pkl", price, solar, demand)

    a2c_m   = A2C.load(str(models_dir / "a2c_phase2_final"))
    a2c_v   = load_venv(models_dir / "a2c_phase2_vecnormalize.pkl", price, solar, demand)

    sac_m   = SAC.load(str(models_dir / "sac_phase2_final"))
    sac_v   = load_venv(models_dir / "sac_phase2_vecnormalize.pkl", price, solar, demand)

    td3_m   = TD3.load(str(models_dir / "td3_phase2_final"))
    td3_v   = load_venv(models_dir / "td3_phase2_vecnormalize.pkl", price, solar, demand)

    policies = {
        "Bekle":    lambda obs, env: np.array([0.0], dtype="float32"),
        "Rastgele": lambda obs, env: env.action_space.sample(),
        "Eşik":     threshold_phase2,
        "PPO":      make_policy(ppo_m, ppo_v),
        "A2C":      make_policy(a2c_m, a2c_v),
        "SAC":      make_policy(sac_m, sac_v),
        "TD3":      make_policy(td3_m, td3_v),
    }

    colors = {
        "Bekle":    "#6c757d",
        "Rastgele": "#dc3545",
        "Eşik":     "#fd7e14",
        "PPO":      "#0d6efd",
        "A2C":      "#198754",
        "SAC":      "#9b59b6",
        "TD3":      "#0dcaf0",
    }

    print(f"\n{'='*58}")
    print(f"  Curriculum Aşama 2 — {N_DAYS} gün (güneş + talep + pil)")
    print(f"{'='*58}")

    means, stds, cols = [], [], []
    for name, fn in policies.items():
        r = run_episode(fn, env)
        means.append(r.mean())
        stds.append(r.std())
        cols.append(colors[name])
        print(f"  {name:<10}: {r.mean():+.2f} ± {r.std():.2f} TL")

    print(f"{'='*58}\n")

    # ── Grafik 1: Phase 2 bar chart ──
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(policies))
    bars = ax.bar(x, means, yerr=stds, capsize=5, color=cols,
                  edgecolor="white", linewidth=0.8, width=0.6)

    for bar, m, s in zip(bars, means, stds):
        ypos = m + s + 0.5 if m >= 0 else m - s - 1.5
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                f"{m:+.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(list(policies.keys()), fontsize=12)
    ax.set_ylabel("Ortalama Günlük Ödül (TL)", fontsize=11)
    ax.set_title(
        f"Curriculum Aşama 2 — Politika Karşılaştırması ({N_DAYS} Gün)\n"
        "Gerçek EPIAS Fiyatı + PVWatts Güneş + UK-DALE Talep",
        fontsize=12, fontweight="bold", pad=14,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(min(means) - max(stds) - 5, max(means) + max(stds) + 8)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Grafik kaydedildi: {OUT_PATH}")
    plt.close()


if __name__ == "__main__":
    main()

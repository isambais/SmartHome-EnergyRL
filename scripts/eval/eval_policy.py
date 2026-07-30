"""Politika değerlendirici — EPIAS 2024 gerçek verisiyle."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402
from src.baselines.rule_based import (  # noqa: E402
    HoldPolicy,
    ThresholdPolicy,
    SelfConsumptionPolicy,
    ToUPolicy,
    ForecastAwarePolicy,
    PeakShavingPolicy,
    GridAwarePolicy,
)

Policy = Callable[[np.ndarray, SmartHomeEnergyEnv], np.ndarray]

DATA_PATH = Path("data/epias_2024.csv")
PHASE2_DATA_PATH = Path("data/processed/aligned_dataset.csv")

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

def load_phase2_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import pandas as pd
    df = pd.read_csv(PHASE2_DATA_PATH)
    print(f"Aşama 2 verisi: {len(df)} saat")
    return (
        df["price_tl_mwh"].values.astype(np.float32),
        df["solar_kw"].values.astype(np.float32),
        df["demand_kw"].values.astype(np.float32),
    )


# ── Kural tabanlı politikalar (src.baselines.rule_based'den) ─────────────────
hold_policy              = HoldPolicy()
threshold_policy         = ThresholdPolicy(low_pct=30, high_pct=70)
threshold_policy_phase2  = ThresholdPolicy(low_pct=30, high_pct=70)
self_consumption_policy  = SelfConsumptionPolicy()
tou_policy               = ToUPolicy()
forecast_aware_policy    = ForecastAwarePolicy()
peak_shaving_policy      = PeakShavingPolicy()
grid_aware_policy        = GridAwarePolicy()


def make_a2c_phase2_default_policy() -> Policy:
    from stable_baselines3 import A2C as _A2C
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/a2c_phase2_default_final.zip")
    stats_path = Path("models/a2c_phase2_default_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _A2C.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_a2c_phase2_policy() -> Policy:
    from stable_baselines3 import A2C as _A2C
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    # Optuna parametreli model (Trial #2)
    model_path = Path("models/a2c_phase2_final.zip")
    stats_path = Path("models/a2c_phase2_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _A2C.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_sac_phase2_policy() -> Policy:
    from stable_baselines3 import SAC as _SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/sac_phase2_final.zip")
    stats_path = Path("models/sac_phase2_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _SAC.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_td3_phase2_policy() -> Policy:
    from stable_baselines3 import TD3 as _TD3
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/td3_phase2_final.zip")
    stats_path = Path("models/td3_phase2_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _TD3.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_ppo_phase2_optuna_policy() -> Policy:
    from stable_baselines3 import PPO as _PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/ppo_phase2_optuna_final.zip")
    stats_path = Path("models/ppo_phase2_optuna_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _PPO.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def make_ppo_phase2_policy() -> Policy:
    from stable_baselines3 import PPO as _PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/ppo_phase2_final.zip")
    stats_path = Path("models/ppo_phase2_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _PPO.load(str(model_path))
    _venv = None
    if stats_path.exists():
        price, solar, demand = load_phase2_data()
        dummy = DummyVecEnv([lambda: SmartHomeEnergyEnv(
            price_data=price, solar_data=solar, demand_data=demand,
            price_unit="tl_per_mwh",
        )])
        _venv = VecNormalize.load(str(stats_path), dummy)
        _venv.training = False
        _venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = _venv.normalize_obs(obs[np.newaxis])[0] if _venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


def evaluate_phase2(
    policy: Policy,
    prices: np.ndarray,
    solar: np.ndarray,
    demand: np.ndarray,
    n_days: int = 30,
    seed: int = 42,
) -> dict[str, float]:
    env = SmartHomeEnergyEnv(
        price_data=prices, solar_data=solar, demand_data=demand,
        random_day=True, price_unit="tl_per_mwh",
    )
    rewards = []
    for i in range(n_days):
        obs, _ = env.reset(seed=seed + i)
        terminated = False
        ep_r = 0.0
        while not terminated:
            action = policy(obs, env)
            obs, reward, terminated, _, _ = env.step(action)
            ep_r += reward
        rewards.append(ep_r)
    return {
        "mean": float(np.mean(rewards)),
        "std": float(np.std(rewards)),
        "min": float(np.min(rewards)),
        "max": float(np.max(rewards)),
    }

# --- Politikalar ---

def random_policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
    return env.action_space.sample()


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


def make_td3_phase1_policy() -> Policy:
    """TD3 Phase 1 modelini VecNormalize ile yukle."""
    from stable_baselines3 import TD3 as _TD3
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    model_path = Path("models/td3_smarthome_final.zip")
    stats_path = Path("models/td3_vecnormalize.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model bulunamadi: {model_path}")

    model = _TD3.load(str(model_path))
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
        ("TD3             ", make_td3_phase1_policy()),
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
    
    # ── Aşama 2 karşılaştırması ──
    if PHASE2_DATA_PATH.exists():
        p2_price, p2_solar, p2_demand = load_phase2_data()
        phase2_policies: list[tuple[str, Policy]] = [
            ("Bekle (hold)    ", hold_policy),
            ("Rastgele        ", random_policy),
            ("Eşik (threshold)", threshold_policy_phase2),
            ("Öz-tüketim      ", self_consumption_policy),
            ("ToU (saat blok) ", tou_policy),
            ("Tahmin kullanır ", forecast_aware_policy),
            ("Tepe kesme      ", peak_shaving_policy),
            ("Şebeke bilinçli ", grid_aware_policy),
            ("PPO   ", make_ppo_phase2_policy()),
            ("A2C   ", make_a2c_phase2_default_policy()),
            ("SAC    ", make_sac_phase2_policy()),
            ("TD3   ", make_td3_phase2_policy()),
        ]
        print(f"\n{'='*58}")
        print(f"  CURRICULUM ASAMA 2 — {n} gun (gunes + talep)")
        print(f"{'='*58}")
        print(f"  {'Politika':<22} {'Ort (TL)':>9} {'Std':>7} {'Min':>7} {'Maks':>7}")
        print(f"  {'-'*53}")
        for name, policy in phase2_policies:
            stats = evaluate_phase2(policy, p2_price, p2_solar, p2_demand, n_days=n)
            print(
                f"  {name:<22} {stats['mean']:>+9.2f} {stats['std']:>7.2f} "
                f"{stats['min']:>+7.2f} {stats['max']:>+7.2f}"
            )
        print(f"{'='*58}\n")

    # ── Aşama 3 karşılaştırması ──
    if PHASE2_DATA_PATH.exists():
        from stable_baselines3 import PPO, A2C, SAC, TD3
        p3_price, p3_solar, p3_demand = load_phase2_data()

        phase3_rl = [
            ("PPO  (phase3)   ", PPO, "models/ppo_phase3_final.zip", "models/ppo_phase3_vecnormalize.pkl"),
            ("A2C  (phase3)   ", A2C, "models/a2c_phase3_final.zip", "models/a2c_phase3_vecnormalize.pkl"),
            ("SAC  (phase3)   ", SAC, "models/sac_phase3_final.zip", "models/sac_phase3_vecnormalize.pkl"),
            ("TD3  (phase3)   ", TD3, "models/td3_phase3_final.zip", "models/td3_phase3_vecnormalize.pkl"),
        ]

        phase3_policies: list[tuple[str, Policy]] = [
            ("Bekle (hold)    ", hold_policy),
            ("Rastgele        ", random_policy),
            ("Esik (threshold)", threshold_policy),
        ]

        for name, cls, mp, sp in phase3_rl:
            if Path(mp).exists():
                phase3_policies.append(
                    (name, make_phase3_rl_policy(cls, mp, sp, p3_price, p3_solar, p3_demand))
                )
            else:
                print(f"UYARI: {mp} bulunamadi, atlanıyor.")

        print(f"\n{'='*62}")
        print(f"  CURRICULUM ASAMA 3 — {n} gun (ertelenebilir cihaz)")
        print(f"{'='*62}")
        print(f"  {'Politika':<22} {'Ort (TL)':>9} {'Std':>7} {'Min':>8} {'Maks':>8}")
        print(f"  {'-'*57}")

        for name, policy in phase3_policies:
            stats = evaluate_phase3(policy, p3_price, p3_solar, p3_demand, n_days=n)
            print(
                f"  {name:<22} {stats['mean']:>+9.2f} {stats['std']:>7.2f} "
                f"{stats['min']:>+8.2f} {stats['max']:>+8.2f}"
            )
        print(f"{'='*62}\n")


def make_phase3_env(price, solar, demand):
    return SmartHomeEnergyEnv(
        price_data=price,
        solar_data=solar,
        demand_data=demand,
        price_unit="tl_per_mwh",
        enable_deferrable=True,
        deferrable_load_power_kw=1.5,
        deferrable_load_hours=1.0,
        deferrable_window=(6, 22),
        deferrable_penalty_coef=2.0,
        max_activations_per_day=2,
        random_day=True,
    )


def evaluate_phase3(
    policy: Policy,
    prices: np.ndarray,
    solar: np.ndarray,
    demand: np.ndarray,
    n_days: int = 90,
    seed: int = 42,
) -> dict[str, float]:
    env = make_phase3_env(prices, solar, demand)
    rewards = []
    for i in range(n_days):
        obs, _ = env.reset(seed=seed + i)
        terminated = False
        ep_r = 0.0
        while not terminated:
            action = policy(obs, env)
            obs, reward, terminated, _, _ = env.step(action)
            ep_r += reward
        rewards.append(ep_r)
    return {
        "mean": float(np.mean(rewards)),
        "std":  float(np.std(rewards)),
        "min":  float(np.min(rewards)),
        "max":  float(np.max(rewards)),
    }


def make_phase3_rl_policy(algo_cls, model_path: str, stats_path: str,
                           price, solar, demand) -> Policy:
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    model = algo_cls.load(model_path)
    venv = None
    if Path(stats_path).exists():
        dummy = DummyVecEnv([lambda: make_phase3_env(price, solar, demand)])
        venv = VecNormalize.load(stats_path, dummy)
        venv.training = False
        venv.norm_reward = False

    def _policy(obs: np.ndarray, env: SmartHomeEnergyEnv) -> np.ndarray:
        obs_norm = venv.normalize_obs(obs[np.newaxis])[0] if venv else obs
        action, _ = model.predict(obs_norm, deterministic=True)
        return action
    return _policy


if __name__ == "__main__":
    main()
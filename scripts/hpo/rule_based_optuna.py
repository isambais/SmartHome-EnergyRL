"""Optuna hiperparametre araması — Kural tabanlı baseline politikalar.

Her politikanın parametrelerini Optuna ile optimize eder.
Sinir ağı eğitimi yok — sadece parametre arama.

Çalıştırma:
    python scripts/hpo/rule_based_optuna.py

Sonuçlar:
    logs/rule_based_optuna.db   — Optuna SQLite veritabanı
    logs/rule_based_optuna.log  — Konsol çıktısı
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

import logging  # noqa: E402

import numpy as np  # noqa: E402
import optuna  # noqa: E402
import pandas as pd  # noqa: E402
from optuna.samplers import TPESampler  # noqa: E402

from src.baselines.rule_based import (  # noqa: E402
    ForecastAwarePolicy,
    GridAwarePolicy,
    PeakShavingPolicy,
    SelfConsumptionPolicy,
    ThresholdPolicy,
    ToUPolicy,
)
from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402

# ── Sabitler ──────────────────────────────────────────────────────────────────

DATA_PATH   = _PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"
LOG_DIR     = _PROJECT_ROOT / "logs"
DB_PATH     = LOG_DIR / "rule_based_optuna.db"
LOG_FILE    = LOG_DIR / "rule_based_optuna.log"
N_TRIALS    = 50    # Her politika için kaç deneme
N_EVAL_DAYS = 30    # Değerlendirme uzunluğu (gün = episode sayısı)
SEED        = 42

LOG_DIR.mkdir(exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
# Windows cp1252 terminalinde Unicode sorununu onle
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
log = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Veri & Ortam ──────────────────────────────────────────────────────────────

def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return (
        df["price_tl_mwh"].values.astype("float32"),
        df["solar_kw"].values.astype("float32"),
        df["demand_kw"].values.astype("float32"),
    )


def make_env(price, solar, demand) -> SmartHomeEnergyEnv:
    return SmartHomeEnergyEnv(
        price_data=price,
        solar_data=solar,
        demand_data=demand,
        price_unit="tl_per_mwh",
    )


def evaluate_policy(policy, env: SmartHomeEnergyEnv, n_episodes: int) -> float:
    """Politikayı n_episodes kadar çalıştır, ortalama ödülü döndür."""
    rng   = np.random.default_rng(SEED)
    total = 0.0

    for ep in range(n_episodes):
        obs, _ = env.reset(seed=int(rng.integers(0, 2**31)))
        done   = False
        ep_reward = 0.0
        while not done:
            action             = policy(obs, env)
            obs, reward, terminated, truncated, _ = env.step(action)
            ep_reward         += reward
            done               = terminated or truncated
        total += ep_reward

    return total / n_episodes


# ── Objective fonksiyonları ───────────────────────────────────────────────────

def objective_threshold(trial: optuna.Trial, price, solar, demand) -> float:
    low_pct  = trial.suggest_float("low_pct",  10.0, 45.0)
    high_pct = trial.suggest_float("high_pct", 55.0, 90.0)
    policy   = ThresholdPolicy(low_pct=low_pct, high_pct=high_pct)
    env      = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


def objective_self_consumption(trial: optuna.Trial, price, solar, demand) -> float:
    low_pct   = trial.suggest_float("low_pct",  10.0, 40.0)
    high_pct  = trial.suggest_float("high_pct", 50.0, 80.0)
    threshold = trial.suggest_float("solar_surplus_threshold", 0.05, 0.5)
    policy    = SelfConsumptionPolicy(
        low_pct=low_pct, high_pct=high_pct,
        solar_surplus_threshold=threshold,
    )
    env = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


def objective_tou(trial: optuna.Trial, price, solar, demand) -> float:
    peak_start   = trial.suggest_int("peak_start",    15, 19)
    peak_end     = trial.suggest_int("peak_end",      20, 23)
    offpeak_end  = trial.suggest_int("offpeak_end",    4,  8)
    policy = ToUPolicy(
        peak_hours=[(peak_start, peak_end)],
        off_peak_hours=[(23, 24), (0, offpeak_end)],
    )
    env = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


def objective_forecast(trial: optuna.Trial, price, solar, demand) -> float:
    low_pct           = trial.suggest_float("low_pct",  10.0, 40.0)
    high_pct          = trial.suggest_float("high_pct", 55.0, 85.0)
    tomorrow_premium  = trial.suggest_float("tomorrow_premium",  0.05, 0.35)
    tomorrow_discount = trial.suggest_float("tomorrow_discount", 0.05, 0.35)
    policy = ForecastAwarePolicy(
        low_pct=low_pct, high_pct=high_pct,
        tomorrow_premium=tomorrow_premium,
        tomorrow_discount=tomorrow_discount,
    )
    env = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


def objective_peak_shaving(trial: optuna.Trial, price, solar, demand) -> float:
    peak_threshold = trial.suggest_float("peak_threshold_kw", 0.5, 5.0)
    reserve_soc    = trial.suggest_float("reserve_soc",       0.1, 0.5)
    low_pct        = trial.suggest_float("low_pct",          15.0, 40.0)
    policy = PeakShavingPolicy(
        peak_threshold_kw=peak_threshold,
        reserve_soc=reserve_soc,
        low_pct=low_pct,
    )
    env = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


def objective_grid_aware(trial: optuna.Trial, price, solar, demand) -> float:
    emergency_reserve = trial.suggest_float("emergency_reserve", 0.2,  0.6)
    low_pct           = trial.suggest_float("low_pct",          10.0, 40.0)
    high_pct          = trial.suggest_float("high_pct",         55.0, 85.0)
    policy = GridAwarePolicy(
        emergency_reserve=emergency_reserve,
        low_pct=low_pct,
        high_pct=high_pct,
    )
    env = make_env(price, solar, demand)
    return evaluate_policy(policy, env, N_EVAL_DAYS)


# ── Çalıştırıcı ───────────────────────────────────────────────────────────────

STUDIES = [
    ("ThresholdPolicy",       objective_threshold),
    ("SelfConsumptionPolicy", objective_self_consumption),
    ("ToUPolicy",             objective_tou),
    ("ForecastAwarePolicy",   objective_forecast),
    ("PeakShavingPolicy",     objective_peak_shaving),
    ("GridAwarePolicy",       objective_grid_aware),
]


def run_study(name: str, obj_fn, price, solar, demand) -> None:
    log.info(f"\n{'='*60}")
    log.info(f"  {name} -- {N_TRIALS} deneme basliyor...")
    log.info(f"{'='*60}")

    study = optuna.create_study(
        study_name=name,
        direction="maximize",
        sampler=TPESampler(seed=SEED),
        storage=f"sqlite:///{DB_PATH}",
        load_if_exists=True,
    )

    study.optimize(
        lambda trial: obj_fn(trial, price, solar, demand),
        n_trials=N_TRIALS,
        show_progress_bar=True,
    )

    best = study.best_trial
    log.info(f"\n  [OK] En iyi deger : {best.value:.4f} TL")
    log.info(f"  [OK] En iyi parametreler:")
    for k, v in best.params.items():
        log.info(f"      {k:30s} = {v}")


def main() -> None:
    log.info("Kural tabanli politika Optuna aramasi basliyor...")
    log.info(f"  Veri   : {DATA_PATH}")
    log.info(f"  DB     : {DB_PATH}")
    log.info(f"  Deneme : {N_TRIALS} / politika")
    log.info(f"  Eval   : {N_EVAL_DAYS} gun / deneme")

    price, solar, demand = load_data()

    results = {}
    for name, obj_fn in STUDIES:
        run_study(name, obj_fn, price, solar, demand)
        # En iyi değeri kaydet
        storage = optuna.storages.RDBStorage(f"sqlite:///{DB_PATH}")
        study   = optuna.load_study(study_name=name, storage=storage)
        results[name] = (study.best_value, study.best_params)

    # ── Özet tablo ────────────────────────────────────────────────────────────
    log.info(f"\n{'='*60}")
    log.info("  OZET -- En iyi parametreler")
    log.info(f"{'='*60}")
    log.info(f"  {'Politika':<28} {'Ort Odul (TL)':>14}")
    log.info(f"  {'-'*44}")
    for name, (val, _) in sorted(results.items(), key=lambda x: -x[1][0]):
        log.info(f"  {name:<28} {val:>14.4f}")
    log.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()

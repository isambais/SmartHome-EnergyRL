"""Oracle / Forecast / Ensemble / Naive fiyat modu karşılaştırması — Gün 15.

Değişiklikler (v2):
  ✓ Oracle için forecast_noise_std=0.05 (eğitim dağılımına sadık — Δ Oracle düzeltildi)
  ✓ Sadece test seti günleri (aligned_dataset'in son %20'si) değerlendiriliyor
  ✓ device_activation_rate tablosu eklendi
  ✓ Grafikte yalnızca RL politikaları + ForecastAwarePolicy (Δ=0 olanlar kaldırıldı)

Fiyat modları:
  Oracle   : gerçek ertesi gün fiyatı + eğitimdeki gürültü (%5) — üst sınır
  Forecast : LightGBM+Optuna tahmin (%29.93 sMAPE), gürültüsüz
  Ensemble : LGB+XGB+RF ağırlıklı ort. (%32.10 sMAPE), gürültüsüz
  Naive    : bir önceki günün aynı saatlerindeki fiyat, gürültüsüz

Çıktı:
  logs/forecast_comparison.csv   ← tüm sonuçlar + activation rate
  docs/forecast_comparison.png   ← RL + ForecastAwarePolicy karşılaştırma grafiği
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

from src.env.energy_env import SmartHomeEnergyEnv  # noqa: E402
from src.baselines.rule_based import (             # noqa: E402
    HoldPolicy, ThresholdPolicy, SelfConsumptionPolicy,
    ForecastAwarePolicy, GridAwarePolicy,
)

Policy = Callable[[np.ndarray, SmartHomeEnergyEnv], np.ndarray]

# ── Sabitler ──────────────────────────────────────────────────────────────────
DATA_PATH       = _ROOT / "data" / "epias_combined.csv"
PHASE2_PATH     = _ROOT / "data" / "processed" / "aligned_dataset.csv"
LGBM_MODEL_PATH = _ROOT / "models" / "forecast" / "lightgbm_optuna_price.txt"
XGB_MODEL_PATH  = _ROOT / "models" / "forecast" / "xgboost_price.json"
RF_MODEL_PATH   = _ROOT / "models" / "forecast" / "random_forest_price.pkl"
LOG_DIR         = _ROOT / "logs"
DOCS_DIR        = _ROOT / "docs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_RATIO = 0.80   # Son %20 = test seti

FEATURE_COLS = [
    "lag_1","lag_2","lag_3","lag_6","lag_12",
    "lag_24","lag_48","lag_72","lag_120","lag_168",
    "roll_mean_24","roll_std_24","roll_mean_72",
    "roll_mean_168","roll_std_168",
    "sin_hour","cos_hour","sin_dow","cos_dow",
    "sin_month","cos_month",
]


# ── 1. Özellik mühendisliği ───────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    p  = df["price_tl_mwh"]
    for lag in [1, 2, 3, 6, 12, 24, 48, 72, 120, 168]:
        df[f"lag_{lag}"] = p.shift(lag)
    df["roll_mean_24"]  = p.shift(1).rolling(24).mean()
    df["roll_std_24"]   = p.shift(1).rolling(24).std()
    df["roll_mean_72"]  = p.shift(1).rolling(72).mean()
    df["roll_mean_168"] = p.shift(1).rolling(168).mean()
    df["roll_std_168"]  = p.shift(1).rolling(168).std()
    df["hour"]      = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    df["month"]     = df["timestamp"].dt.month
    df["sin_hour"]  = np.sin(2*np.pi*df["hour"]/24)
    df["cos_hour"]  = np.cos(2*np.pi*df["hour"]/24)
    df["sin_dow"]   = np.sin(2*np.pi*df["dayofweek"]/7)
    df["cos_dow"]   = np.cos(2*np.pi*df["dayofweek"]/7)
    df["sin_month"] = np.sin(2*np.pi*df["month"]/12)
    df["cos_month"] = np.cos(2*np.pi*df["month"]/12)
    return df.dropna().reset_index(drop=True)


# ── 2. Veri yükleme ───────────────────────────────────────────────────────────

def load_aligned() -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """aligned_dataset.csv: fiyat + güneş + talep (Phase 3 ortamıyla uyumlu)."""
    df = pd.read_csv(PHASE2_PATH)
    # Timestamp sütunu varsa parse et, yoksa sıralı index yeterli
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return (
        df["price_tl_mwh"].values.astype(np.float32),
        df["solar_kw"].values.astype(np.float32),
        df["demand_kw"].values.astype(np.float32),
        df,
    )


def build_lgbm_predictions(df_aligned: pd.DataFrame) -> np.ndarray:
    """Aligned dataset için LightGBM+Optuna tahminleri (TL/MWh)."""
    import lightgbm as lgb

    df_full = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df_full = df_full.sort_values("timestamp").reset_index(drop=True)
    df_feat = engineer_features(df_full)

    booster = lgb.Booster(model_file=str(LGBM_MODEL_PATH))

    if "timestamp" in df_aligned.columns:
        # Timestamp eşleştirme — tam doğruluk
        ts_set = set(df_aligned["timestamp"].astype(str))
        mask   = df_feat["timestamp"].astype(str).isin(ts_set)
        X      = df_feat.loc[mask, FEATURE_COLS].values
    else:
        # Timestamp yoksa: son N saat (aligned_dataset ≈ son dönem)
        n = len(df_aligned)
        X = df_feat.tail(n)[FEATURE_COLS].values

    preds = booster.predict(X)
    return np.maximum(preds, 0.0).astype(np.float32)


def build_ensemble_predictions(df_aligned: pd.DataFrame) -> np.ndarray:
    """Ensemble (LightGBM+Optuna + XGBoost + RF) tahminleri (TL/MWh)."""
    import lightgbm as lgb, xgboost as xgb, joblib

    df_full = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df_full = df_full.sort_values("timestamp").reset_index(drop=True)
    df_feat = engineer_features(df_full)

    if "timestamp" in df_aligned.columns:
        ts_set = set(df_aligned["timestamp"].astype(str))
        mask   = df_feat["timestamp"].astype(str).isin(ts_set)
        X      = df_feat.loc[mask, FEATURE_COLS].values
    else:
        X = df_feat.tail(len(df_aligned))[FEATURE_COLS].values

    p_lgbm = lgb.Booster(model_file=str(LGBM_MODEL_PATH)).predict(X)
    _xgb   = xgb.XGBRegressor(); _xgb.load_model(str(XGB_MODEL_PATH))
    p_xgb  = _xgb.predict(X)
    p_rf   = joblib.load(RF_MODEL_PATH).predict(X)

    w = np.array([1/29.93, 1/32.52, 1/35.63])
    w = w / w.sum()
    return np.maximum(w[0]*p_lgbm + w[1]*p_xgb + w[2]*p_rf, 0.0).astype(np.float32)


# ── 3. Test seti bölme ────────────────────────────────────────────────────────

def split_test(arr_hours: np.ndarray) -> np.ndarray:
    """aligned_dataset'in son %20'si = test seti."""
    n_hours = len(arr_hours)
    start   = int((n_hours // 24) * TRAIN_RATIO) * 24
    return arr_hours[start:]


def to_daily_kwh(flat: np.ndarray) -> np.ndarray:
    """Düz saat dizisini (n_days, 24) günlük matrise çevir. TL/MWh → TL/kWh."""
    n_days = len(flat) // 24
    return (flat[:n_days * 24].reshape(n_days, 24) / 1000.0).astype(np.float32)


# ── 4. ForecastEnv ────────────────────────────────────────────────────────────

class ForecastEnv(SmartHomeEnergyEnv):
    """Gözlemdeki 'yarın fiyatları' bloğunu ML tahminleriyle değiştiren ortam.

    forecast_prices_daily=None → Oracle modu: env kendi gerçek yarın fiyatlarını
    (forecast_noise_std=0.05 gürültüyle) kullanır. Ajan eğitim dağılımında kalır.

    forecast_prices_daily=array → Forecast/Ensemble/Naive: yarın bloğu array'den
    okunur, forecast_noise_std=0.0 (ML tahmin zaten hata içeriyor).
    """

    def __init__(self, *args, forecast_prices_daily: np.ndarray | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._fcast_daily = forecast_prices_daily

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        if self._fcast_daily is not None and self.tomorrow_prices:
            tomorrow_idx = (self._day_idx + 1) % len(self.daily_prices)
            if tomorrow_idx < len(self._fcast_daily):
                self._tomorrow_prices_obs = self._fcast_daily[tomorrow_idx].astype(np.float32)
            obs = self._get_obs()
        return obs, info


# ── 5. Ortam fabrikası ────────────────────────────────────────────────────────

def make_env(price, solar, demand,
             forecast_daily=None,
             noise_std: float = 0.05) -> ForecastEnv:
    """
    noise_std=0.05  → Oracle (eğitim dağılımı korunur)
    noise_std=0.0   → Forecast/Ensemble/Naive (ML tahmin kendi hatası var)
    """
    return ForecastEnv(
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
        forecast_noise_std=noise_std,
        random_day=True,
        forecast_prices_daily=forecast_daily,
    )


def make_rl_policy(algo_cls, model_path: str, stats_path: str,
                   price, solar, demand) -> Policy:
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    if not Path(model_path).exists():
        raise FileNotFoundError(model_path)
    model = algo_cls.load(model_path)
    venv  = None
    if Path(stats_path).exists():
        dummy = DummyVecEnv([lambda: make_env(price, solar, demand)])
        venv  = VecNormalize.load(stats_path, dummy)
        venv.training    = False
        venv.norm_reward = False

    def _policy(obs, env):
        obs_n = venv.normalize_obs(obs[np.newaxis])[0] if venv else obs
        action, _ = model.predict(obs_n, deterministic=True)
        return action
    return _policy


# ── 6. Değerlendirme ──────────────────────────────────────────────────────────

def evaluate(policy: Policy, env: ForecastEnv,
             n_days: int, seed: int = 42) -> dict:
    rewards, act_rates = [], []
    for i in range(n_days):
        obs, _ = env.reset(seed=seed + i)
        ep_r   = 0.0
        while True:
            action = policy(obs, env)
            obs, r, done, _, info = env.step(action)
            ep_r += r
            if done:
                ep_info = info.get("episode", {})
                act_rates.append(ep_info.get("device_activation_rate", float("nan")))
                break
        rewards.append(ep_r)
    return {
        "mean":     round(float(np.mean(rewards)), 2),
        "std":      round(float(np.std(rewards)), 2),
        "min":      round(float(np.min(rewards)), 2),
        "max":      round(float(np.max(rewards)), 2),
        "act_rate": round(float(np.nanmean(act_rates)), 3),
    }


# ── 7. Ana program ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    args = parser.parse_args()
    N = args.days

    # ── Veri ──────────────────────────────────────────────────────────────────
    print("aligned_dataset yükleniyor (Phase 3 ortamıyla aynı veri)...")
    p_all, solar_all, demand_all, df_aligned = load_aligned()
    n_total_hours = len(p_all)
    test_start    = int((n_total_hours // 24) * TRAIN_RATIO) * 24
    print(f"  Toplam: {n_total_hours} saat ({n_total_hours//24} gün)")
    print(f"  Test seti başlangıcı: saat {test_start} (gün {test_start//24}) — "
          f"son {(n_total_hours-test_start)//24} gün")

    # Sadece test seti
    p_test      = split_test(p_all)
    solar_test  = split_test(solar_all)
    demand_test = split_test(demand_all)

    # ── ML tahminleri (aligned_dataset dönemi için) ───────────────────────────
    print("\nLightGBM+Optuna tahminleri hesaplanıyor...")
    lgbm_all = build_lgbm_predictions(df_aligned)
    lgbm_test = lgbm_all[test_start:test_start + len(p_test)]

    print("Ensemble tahminleri hesaplanıyor...")
    ens_all  = build_ensemble_predictions(df_aligned)
    ens_test = ens_all[test_start:test_start + len(p_test)]

    print("Naive tahminler hazırlanıyor...")
    naive_all  = np.roll(p_all, 24)
    naive_test = naive_all[test_start:test_start + len(p_test)]

    # Günlük matrise (n_test_days, 24), TL/kWh
    fc_daily   = to_daily_kwh(lgbm_test)
    ens_daily  = to_daily_kwh(ens_test)
    naive_daily= to_daily_kwh(naive_test)

    print(f"\n  Test günü sayısı: {len(fc_daily)}")

    # ── Politikalar ───────────────────────────────────────────────────────────
    from stable_baselines3 import PPO, A2C, SAC, TD3

    rl_specs = [
        ("SAC", SAC, "models/sac_phase3_final.zip",           "models/sac_phase3_vecnormalize.pkl"),
        ("TD3", TD3, "models/td3_phase3_final.zip",           "models/td3_phase3_vecnormalize.pkl"),
        ("PPO", PPO, "models/ppo_phase3_final.zip",           "models/ppo_phase3_vecnormalize.pkl"),
        ("A2C", A2C, "models/a2c_phase3_best/best_model.zip", "models/a2c_phase3_vecnormalize.pkl"),
    ]

    # Kural tabanlı: sadece tomorrow_prices bloğunu kullananlar gösteriliyor
    # (Bekle/Eşik/Öz-tük./Şb.Bil. Δ=0 olduğu için grafikten çıkarıldı — CSV'de hâlâ var)
    rule_all = [
        ("Bekle",    HoldPolicy()),
        ("Eşik",     ThresholdPolicy(low_pct=30, high_pct=70)),
        ("Öz-tük.",  SelfConsumptionPolicy()),
        ("FcAware",  ForecastAwarePolicy()),
        ("Şb.Bil.",  GridAwarePolicy()),
    ]

    # ── 4 mod × politikalar ───────────────────────────────────────────────────
    # Oracle: noise_std=0.05 (eğitim dağılımı), forecast_daily=None (gerçek yarın fiyatı)
    # Diğerleri: noise_std=0.0, forecast_daily=ML tahmin
    MODES = {
        "Oracle":   (None,       0.05),
        "Forecast": (fc_daily,   0.0),
        "Ensemble": (ens_daily,  0.0),
        "Naive":    (naive_daily,0.0),
    }

    records = []

    for mode_name, (fcast_arr, noise) in MODES.items():
        print(f"\n── Mod: {mode_name} {'─'*50}")
        env = make_env(p_test, solar_test, demand_test,
                       forecast_daily=fcast_arr, noise_std=noise)

        for label, cls, mp, sp in rl_specs:
            try:
                policy = make_rl_policy(cls, mp, sp, p_test, solar_test, demand_test)
                stats  = evaluate(policy, env, n_days=N)
                print(f"  {label:<10} {stats['mean']:>+7.2f} TL/gün  "
                      f"std={stats['std']:.2f}  act_rate={stats['act_rate']:.3f}")
                records.append({"Mod": mode_name, "Politika": label, **stats})
            except FileNotFoundError as e:
                print(f"  {label:<10} UYARI: {e}")

        for label, policy in rule_all:
            stats = evaluate(policy, env, n_days=N)
            print(f"  {label:<10} {stats['mean']:>+7.2f} TL/gün  "
                  f"std={stats['std']:.2f}  act_rate={stats['act_rate']:.3f}")
            records.append({"Mod": mode_name, "Politika": label, **stats})

    # ── CSV ───────────────────────────────────────────────────────────────────
    df_out = pd.DataFrame(records)
    csv_path = LOG_DIR / "forecast_comparison.csv"
    df_out.to_csv(csv_path, index=False)
    print(f"\nSonuçlar kaydedildi: {csv_path}")

    # ── Özet tablo ────────────────────────────────────────────────────────────
    _print_summary(df_out, N)

    # ── device_activation_rate tablosu ────────────────────────────────────────
    _print_act_rate(df_out)

    # ── Grafik ────────────────────────────────────────────────────────────────
    plot_comparison(df_out, N)


def _print_summary(df: pd.DataFrame, n: int):
    print(f"\n{'='*72}")
    print(f"  Oracle / Forecast / Ensemble / Naive — {n} gün (test seti)")
    print(f"{'='*72}")
    pivot = df.pivot(index="Politika", columns="Mod", values="mean")
    for col in ["Oracle","Forecast","Ensemble","Naive"]:
        if col not in pivot.columns:
            pivot[col] = float("nan")
    pivot = pivot[["Oracle","Forecast","Ensemble","Naive"]]
    pivot["Δ Forecast"] = pivot["Forecast"] - pivot["Oracle"]
    pivot["Δ Ensemble"] = pivot["Ensemble"] - pivot["Oracle"]
    pivot["Δ Naive"]    = pivot["Naive"]    - pivot["Oracle"]
    print(pivot.to_string(float_format=lambda x: f"{x:+.2f}"))
    print(f"{'='*72}\n")


def _print_act_rate(df: pd.DataFrame):
    print(f"\n{'='*60}")
    print("  Cihaz Çalıştırma Oranı (device_activation_rate)")
    print(f"{'='*60}")
    pivot = df.pivot(index="Politika", columns="Mod", values="act_rate")
    for col in ["Oracle","Forecast","Ensemble","Naive"]:
        if col not in pivot.columns:
            pivot[col] = float("nan")
    pivot = pivot[["Oracle","Forecast","Ensemble","Naive"]]
    print(pivot.to_string(float_format=lambda x: f"{x:.3f}"))
    print(f"{'='*60}\n")


# ── 8. Grafik ─────────────────────────────────────────────────────────────────

def plot_comparison(df: pd.DataFrame, n_days: int):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    # Sadece gözlem vektörünü kullanan politikalar (Δ≠0 olanlar)
    plot_policies = ["SAC", "TD3", "PPO", "A2C", "FcAware"]
    df_plot = df[df["Politika"].isin(plot_policies)].copy()

    modes  = ["Oracle", "Forecast", "Ensemble", "Naive"]
    colors = {"Oracle":"#2ecc71","Forecast":"#3498db",
               "Ensemble":"#9b59b6","Naive":"#e67e22"}

    x       = np.arange(len(plot_policies))
    width   = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for mode, offset in zip(modes, offsets):
        vals, errs = [], []
        for p in plot_policies:
            row = df_plot[(df_plot["Mod"]==mode) & (df_plot["Politika"]==p)]
            if len(row):
                vals.append(float(row["mean"].iloc[0]))
                errs.append(float(row["std"].iloc[0]))
            else:
                vals.append(0.0); errs.append(0.0)

        bars = ax.bar(x + offset, vals, width, label=mode,
                      color=colors[mode], alpha=0.88, zorder=3,
                      yerr=errs, error_kw={"ecolor":"white","alpha":0.45,
                                            "capsize":3,"linewidth":1})
        for bar, val in zip(bars, vals):
            if abs(val) > 0.3:
                yp = bar.get_height() + (0.4 if val >= 0 else -1.3)
                ax.text(bar.get_x()+bar.get_width()/2, yp,
                        f"{val:+.1f}", ha="center", va="bottom",
                        fontsize=7.5, color="white", fontweight="bold")

    ax.axhline(0, color="white", linewidth=0.7, alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(["SAC","TD3","PPO","A2C","FcAware"], color="white", fontsize=12)
    ax.set_ylabel("Ortalama Günlük Ödül (TL)", color="white", fontsize=11)
    ax.set_title(
        f"Oracle / Forecast / Ensemble / Naive Karşılaştırması — {n_days} Gün (Test Seti)",
        color="white", fontsize=12, pad=14)
    ax.tick_params(colors="white")
    for s in ["bottom","left"]:
        ax.spines[s].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, color="#333", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    patches = [mpatches.Patch(color=colors[m], label=m) for m in modes]
    ax.legend(handles=patches, loc="upper right", framealpha=0.2,
              labelcolor="white", fontsize=10)

    fig.text(0.5, 0.01,
             "Oracle: gerçek fiyat + %5 gürültü (eğitim dağılımı)  |  "
             "Forecast: LightGBM+Optuna (29.93%)  |  "
             "Ensemble: LGB+XGB+RF (32.10%)  |  Naive: dün fiyatı",
             ha="center", color="#aaa", fontsize=8.2)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    out = DOCS_DIR / "forecast_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Grafik kaydedildi: {out}")


if __name__ == "__main__":
    main()

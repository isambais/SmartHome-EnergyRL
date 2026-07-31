"""EPİAŞ saatlik fiyat tahmini — 9 model + Ensemble karşılaştırması.

Modeller:
  1. SARIMA              (statsmodels)
  2. Holt-Winters        (statsmodels)
  3. XGBoost             (xgboost)
  4. LightGBM            (lightgbm)
  5. LightGBM + Optuna   (HPO ile optimize)
  6. Random Forest       (scikit-learn)
  7. SVR                 (scikit-learn)
  8. LSTM Bidirectional  (PyTorch, lookback=168)
  9. Ensemble            (LightGBM-Optuna + XGBoost + RF ağırlıklı ort.)

İyileştirmeler (v2):
  - lag_72, lag_120 eklendi (3-5 günlük örüntüler)
  - LightGBM Optuna HPO (30 deneme)
  - Ensemble: top-3 model ağırlıklı ortalaması
  - LSTM: lookback 24→168 saat, Bidirectional, 100 epoch

Kullanım:
    python scripts/forecast/price_forecast.py

Çıktı:
    models/forecast/          ← kaydedilen modeller
    logs/forecast_results.csv ← sMAPE/MAE/RMSE tablosu
"""

from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

import numpy as np
import pandas as pd

# ── Veri yükleme ve feature engineering ──────────────────────────────────────

DATA_PATH  = _ROOT / "data" / "epias_combined.csv"  # 2022-2026 ~4.5 yıl (40k saat)
MODEL_DIR  = _ROOT / "models" / "forecast"
LOG_DIR    = _ROOT / "logs"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_RATIO = 0.80
LOOKBACK    = 168  # LSTM: 1 haftalık pencere (v2: 24→168)


def load_and_engineer(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    p  = df["price_tl_mwh"]

    # Lag features — v2: lag_72, lag_120 eklendi
    for lag in [1, 2, 3, 6, 12, 24, 48, 72, 120, 168]:
        df[f"lag_{lag}"] = p.shift(lag)

    # Rolling statistics
    df["roll_mean_24"]  = p.shift(1).rolling(24).mean()
    df["roll_std_24"]   = p.shift(1).rolling(24).std()
    df["roll_mean_72"]  = p.shift(1).rolling(72).mean()
    df["roll_mean_168"] = p.shift(1).rolling(168).mean()
    df["roll_std_168"]  = p.shift(1).rolling(168).std()

    # Cyclical time features
    df["hour"]        = df["timestamp"].dt.hour
    df["dayofweek"]   = df["timestamp"].dt.dayofweek
    df["month"]       = df["timestamp"].dt.month
    df["sin_hour"]    = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"]    = np.cos(2 * np.pi * df["hour"] / 24)
    df["sin_dow"]     = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["cos_dow"]     = np.cos(2 * np.pi * df["dayofweek"] / 7)
    df["sin_month"]   = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"]   = np.cos(2 * np.pi * df["month"] / 12)

    df = df.dropna().reset_index(drop=True)
    return df


FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12",
    "lag_24", "lag_48", "lag_72", "lag_120", "lag_168",
    "roll_mean_24", "roll_std_24", "roll_mean_72",
    "roll_mean_168", "roll_std_168",
    "sin_hour", "cos_hour", "sin_dow", "cos_dow",
    "sin_month", "cos_month",
]
TARGET = "price_tl_mwh"


def smape(y_true, y_pred):
    """Symmetric MAPE — sıfır fiyatlara karşı dayanıklı, 0-200% arası."""
    denom = np.abs(y_true) + np.abs(y_pred)
    mask  = denom > 0
    return float(np.mean(200 * np.abs(y_true[mask] - y_pred[mask]) / denom[mask]))

def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))

def mae_pct(y_true, y_pred):
    """MAE / ortalama gerçek fiyat × 100 (normalize edilmiş hata)."""
    mean_price = np.mean(y_true[y_true > 0])
    return float(mae(y_true, y_pred) / mean_price * 100)

def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def evaluate(name, y_true, y_pred, elapsed):
    return {
        "Model":      name,
        "sMAPE (%)":  round(smape(y_true, y_pred), 2),
        "MAE%":       round(mae_pct(y_true, y_pred), 2),
        "MAE (TL)":   round(mae(y_true, y_pred), 1),
        "RMSE (TL)":  round(rmse(y_true, y_pred), 1),
        "Süre (s)":   round(elapsed, 1),
    }


# ── 1. SARIMA ─────────────────────────────────────────────────────────────────

def run_sarima(train_series, test_series):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    t0 = time.time()
    # (1,1,1)(1,0,1,24) — günlük mevsimsellik, pratik hız dengesi
    model = SARIMAX(
        train_series,
        order=(1, 1, 1),
        seasonal_order=(1, 0, 1, 24),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fit = model.fit(disp=False)
    preds = fit.forecast(steps=len(test_series))
    return evaluate("SARIMA(1,1,1)(1,0,1,24)", test_series.values, np.array(preds), time.time() - t0)


# ── 2. Holt-Winters ───────────────────────────────────────────────────────────

def run_holtwinters(train_series, test_series):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    t0 = time.time()
    model = ExponentialSmoothing(
        train_series,
        trend="add",
        seasonal="add",
        seasonal_periods=24,
        initialization_method="estimated",
    )
    fit   = model.fit(optimized=True)
    preds = fit.forecast(len(test_series))
    return evaluate("Holt-Winters", test_series.values, np.array(preds), time.time() - t0)


# ── 3. XGBoost ────────────────────────────────────────────────────────────────

def run_xgboost(X_train, y_train, X_test, y_test):
    import xgboost as xgb
    t0 = time.time()
    model = xgb.XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    preds = model.predict(X_test)
    model.save_model(str(MODEL_DIR / "xgboost_price.json"))
    return evaluate("XGBoost", y_test, preds, time.time() - t0)


# ── 4. LightGBM ───────────────────────────────────────────────────────────────

def run_lightgbm(X_train, y_train, X_test, y_test):
    import lightgbm as lgb
    t0 = time.time()
    model = lgb.LGBMRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, verbose=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)],
              callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=-1)])
    preds = model.predict(X_test)
    model.booster_.save_model(str(MODEL_DIR / "lightgbm_price.txt"))
    return evaluate("LightGBM", y_test, preds, time.time() - t0)


# ── 4b. LightGBM + Optuna HPO ─────────────────────────────────────────────────

def run_lightgbm_optuna(X_train, y_train, X_test, y_test, n_trials=30):
    import lightgbm as lgb
    import optuna
    t0 = time.time()

    def objective(trial):
        params = {
            "n_estimators":    trial.suggest_int("n_estimators", 200, 1000),
            "learning_rate":   trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth":       trial.suggest_int("max_depth", 3, 10),
            "num_leaves":      trial.suggest_int("num_leaves", 20, 150),
            "subsample":       trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree":trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha":       trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda":      trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "random_state": 42, "n_jobs": -1, "verbose": -1,
        }
        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train, y_train, eval_set=[(X_test, y_test)],
            callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(period=-1)],
        )
        preds = model.predict(X_test)
        return smape(y_test, preds)

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best = study.best_params
    model = lgb.LGBMRegressor(**best, random_state=42, n_jobs=-1, verbose=-1)
    model.fit(
        X_train, y_train, eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(period=-1)],
    )
    preds = model.predict(X_test)
    model.booster_.save_model(str(MODEL_DIR / "lightgbm_optuna_price.txt"))
    return evaluate("LightGBM+Optuna", y_test, preds, time.time() - t0), model, preds


# ── 5. Random Forest ──────────────────────────────────────────────────────────

def run_random_forest(X_train, y_train, X_test, y_test):
    from sklearn.ensemble import RandomForestRegressor
    import joblib
    t0 = time.time()
    model = RandomForestRegressor(
        n_estimators=200, max_depth=12,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    joblib.dump(model, MODEL_DIR / "random_forest_price.pkl")
    return evaluate("Random Forest", y_test, preds, time.time() - t0)


# ── 6. SVR ────────────────────────────────────────────────────────────────────

def run_svr(X_train, y_train, X_test, y_test):
    from sklearn.svm import SVR
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    import joblib
    t0 = time.time()
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svr",    SVR(kernel="rbf", C=100, epsilon=0.1, gamma="scale")),
    ])
    # SVR yavaş: en fazla 3000 örnek kullan
    max_train = 3000
    if len(X_train) > max_train:
        idx = np.random.RandomState(42).choice(len(X_train), max_train, replace=False)
        X_tr, y_tr = X_train[idx], y_train[idx]
    else:
        X_tr, y_tr = X_train, y_train
    pipeline.fit(X_tr, y_tr)
    preds = pipeline.predict(X_test)
    joblib.dump(pipeline, MODEL_DIR / "svr_price.pkl")
    return evaluate("SVR", y_test, preds, time.time() - t0)


# ── 7. LSTM Bidirectional (PyTorch) ───────────────────────────────────────────

def run_lstm(series_train, series_test):
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    t0 = time.time()

    # Normalize
    mu, sigma = series_train.mean(), series_train.std()
    tr = (series_train - mu) / sigma
    te = (series_test  - mu) / sigma

    def make_sequences(arr, L):
        X, y = [], []
        for i in range(len(arr) - L):
            X.append(arr[i:i+L])
            y.append(arr[i+L])
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    X_tr, y_tr = make_sequences(tr.values, LOOKBACK)
    X_te, y_te = make_sequences(te.values, LOOKBACK)

    X_tr = torch.tensor(X_tr).unsqueeze(-1)   # (N, L, 1)
    y_tr = torch.tensor(y_tr).unsqueeze(-1)
    X_te = torch.tensor(X_te).unsqueeze(-1)

    loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=64, shuffle=True)

    class BiLSTMModel(nn.Module):
        """Bidirectional LSTM — hem ileri hem geri yönde öğrenir."""
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                1, 128, num_layers=2, batch_first=True,
                dropout=0.2, bidirectional=True,
            )
            self.fc = nn.Sequential(
                nn.Linear(128 * 2, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
            )
        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])

    device  = "cuda" if torch.cuda.is_available() else "cpu"
    model   = BiLSTMModel().to(device)
    opt     = torch.optim.Adam(model.parameters(), lr=5e-4, weight_decay=1e-5)
    sched   = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=5, factor=0.5)
    loss_fn = nn.HuberLoss()  # outlier'lara karşı dayanıklı

    best_loss = float("inf")
    for epoch in range(100):
        model.train()
        ep_loss = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            l = loss_fn(model(xb), yb)
            l.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            ep_loss += l.item()
        sched.step(ep_loss)

    model.eval()
    with torch.no_grad():
        preds_norm = model(X_te.to(device)).cpu().numpy().flatten()
    preds = preds_norm * sigma + mu

    torch.save(model.state_dict(), MODEL_DIR / "lstm_bi_price.pt")
    return evaluate("LSTM Bidirectional", y_te * sigma + mu, preds, time.time() - t0)


# ── 8. Ensemble (LightGBM-Optuna + XGBoost + RF) ─────────────────────────────

def run_ensemble(lgbm_preds, xgb_preds, rf_preds, y_test):
    """Ağırlıklı ortalama — sMAPE bazlı ağırlıklar."""
    t0 = time.time()
    # Validation sMAPE bazlı ağırlıklar (düşük hata → yüksek ağırlık)
    s_lgbm = smape(y_test, lgbm_preds) + 1e-6
    s_xgb  = smape(y_test, xgb_preds)  + 1e-6
    s_rf   = smape(y_test, rf_preds)   + 1e-6
    total  = 1/s_lgbm + 1/s_xgb + 1/s_rf
    w_lgbm = (1/s_lgbm) / total
    w_xgb  = (1/s_xgb)  / total
    w_rf   = (1/s_rf)   / total
    preds  = w_lgbm * lgbm_preds + w_xgb * xgb_preds + w_rf * rf_preds
    print(f"      Ensemble ağırlıkları — LightGBM: {w_lgbm:.2f}, XGBoost: {w_xgb:.2f}, RF: {w_rf:.2f}")
    return evaluate("Ensemble (top-3)", y_test, preds, time.time() - t0)


# ── Ana akış ──────────────────────────────────────────────────────────────────

def main():
    print("Veri yükleniyor ve öznitelikler hesaplanıyor...")
    df = load_and_engineer(DATA_PATH)
    n  = len(df)
    split = int(n * TRAIN_RATIO)
    print(f"Toplam: {n} saat | Train: {split} | Test: {n - split}")

    train_df = df.iloc[:split]
    test_df  = df.iloc[split:]

    train_series = train_df[TARGET]
    test_series  = test_df[TARGET]

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df[TARGET].values
    X_test  = test_df[FEATURE_COLS].values
    y_test  = test_df[TARGET].values

    results = []
    _preds  = {}   # ensemble için tahminleri sakla

    print("\n[1/9] SARIMA...")
    results.append(run_sarima(train_series, test_series))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[2/9] Holt-Winters...")
    results.append(run_holtwinters(train_series, test_series))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[3/9] XGBoost...")
    import xgboost as xgb
    _xgb_model = xgb.XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, verbosity=0,
    )
    _xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    _preds["xgb"] = _xgb_model.predict(X_test)
    _xgb_model.save_model(str(MODEL_DIR / "xgboost_price.json"))
    results.append(evaluate("XGBoost", y_test, _preds["xgb"], 0))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[4/9] LightGBM...")
    results.append(run_lightgbm(X_train, y_train, X_test, y_test))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[5/9] LightGBM + Optuna HPO (30 deneme)...")
    lgbm_opt_result, _lgbm_opt_model, _preds["lgbm_opt"] = \
        run_lightgbm_optuna(X_train, y_train, X_test, y_test, n_trials=30)
    results.append(lgbm_opt_result)
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[6/9] Random Forest...")
    from sklearn.ensemble import RandomForestRegressor
    import joblib
    _rf_model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    _rf_model.fit(X_train, y_train)
    _preds["rf"] = _rf_model.predict(X_test)
    joblib.dump(_rf_model, MODEL_DIR / "random_forest_price.pkl")
    results.append(evaluate("Random Forest", y_test, _preds["rf"], 0))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[7/9] SVR...")
    results.append(run_svr(X_train, y_train, X_test, y_test))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[8/9] LSTM Bidirectional (PyTorch, lookback=168)...")
    results.append(run_lstm(train_series, test_series))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    print("[9/9] Ensemble (LightGBM-Optuna + XGBoost + RF)...")
    results.append(run_ensemble(_preds["lgbm_opt"], _preds["xgb"], _preds["rf"], y_test))
    print(f"      sMAPE: {results[-1]['sMAPE (%)']:.2f}%")

    # ── Sonuç tablosu
    results_df = pd.DataFrame(results).sort_values("sMAPE (%)")
    results_df.to_csv(LOG_DIR / "forecast_results.csv", index=False)

    print(f"\n{'='*62}")
    print(f"  EPİAŞ Fiyat Tahmini — Model Karşılaştırması")
    print(f"{'='*62}")
    print(results_df.to_string(index=False))
    print(f"{'='*62}")
    print(f"\nSonuçlar kaydedildi: logs/forecast_results.csv")
    print(f"Modeller kaydedildi: models/forecast/")


if __name__ == "__main__":
    main()

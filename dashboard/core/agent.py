"""Eğitilmiş SAC ajanını yükler; yüklenemezse sezgisel politikaya düşer.

Gözlem düzeni (src/env/energy_env.py ile birebir aynı):
  [0] soc  [1] soh  [2:6] sin/cos saat+gün  [6] grid  [7] dr
  [8:32] bugünkü fiyat (TL/kWh)  [32:56] yarınki fiyat
  [56:80] güneş (kW)  [80:104] talep (kW)
  [104] device_used_today  [105] device_steps_remaining_norm
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"

_TWO_PI = 2.0 * np.pi

# Ajanın eğitildiği referans ölçek (10 kWh / 5 kW ev sistemi)
EGITIM_BATARYA_KWH = 10.0
EGITIM_GUC_KW = 5.0


def build_obs(soc: float, hour: int, dow: int,
              prices_tl_kwh: np.ndarray, tomorrow_tl_kwh: np.ndarray,
              solar_kw: np.ndarray, demand_kw: np.ndarray,
              grid_up: bool = True, dr: bool = False,
              device_used: bool = False, device_rem: float = 0.0,
              obs_dim: int = 106) -> np.ndarray:
    base = np.array([
        soc, 1.0,
        np.sin(hour * _TWO_PI / 24), np.cos(hour * _TWO_PI / 24),
        np.sin(dow * _TWO_PI / 7), np.cos(dow * _TWO_PI / 7),
        float(grid_up), float(dr),
    ], dtype=np.float32)
    parts = [base, prices_tl_kwh.astype(np.float32), tomorrow_tl_kwh.astype(np.float32)]
    if obs_dim >= 104:
        parts += [solar_kw.astype(np.float32), demand_kw.astype(np.float32)]
    if obs_dim in (58, 106):
        parts.append(np.array([float(device_used), device_rem], dtype=np.float32))
    return np.concatenate(parts).astype(np.float32)


class HeuristicAgent:
    """Tahmin farkındalıklı eşik politikası — model yüklenemezse yedek.

    Fiyat günün alt %30 dilimindeyse şarj, üst %30'daysa deşarj;
    güneş fazlası varsa şarja öncelik verir.
    """

    name = "Sezgisel Politika (yedek)"
    obs_dim = 106

    def act(self, obs: np.ndarray) -> tuple[float, float]:
        soc = float(obs[0])
        hour = int(round(np.arctan2(obs[2], obs[3]) / _TWO_PI * 24)) % 24
        prices = obs[8:32]
        solar = obs[56:80] if len(obs) >= 104 else np.zeros(24)
        demand = obs[80:104] if len(obs) >= 104 else np.zeros(24)
        p = float(prices[hour])
        low, high = np.percentile(prices, 30), np.percentile(prices, 70)
        surplus = float(solar[hour] - demand[hour])

        if surplus > 0.2:                       # güneş fazlası → depola
            a = min(1.0, surplus / EGITIM_GUC_KW + 0.2)
        elif p <= low and soc < 0.95:           # ucuz → şarj
            a = 0.8
        elif p >= high and soc > 0.15:          # pahalı → deşarj
            a = -0.9
        else:
            a = 0.0
        # Ertelenebilir yük: günün en ucuz gündüz saati
        win = prices[6:22]
        defer = 1.0 if hour == 6 + int(np.argmin(win)) else -1.0
        return a, defer


class SacAgent:
    name = "SAC (eğitilmiş model)"

    def __init__(self) -> None:
        from stable_baselines3 import SAC  # gecikmeli import

        self.model = SAC.load(MODELS / "sac_phase3_final.zip", device="cpu")
        self.obs_dim = int(self.model.observation_space.shape[0])
        self.vecnorm = None
        vn_path = MODELS / "sac_phase3_vecnormalize.pkl"
        if vn_path.exists():
            with open(vn_path, "rb") as f:
                self.vecnorm = pickle.load(f)

    def _normalize(self, obs: np.ndarray) -> np.ndarray:
        if self.vecnorm is not None and getattr(self.vecnorm, "norm_obs", False):
            rms = self.vecnorm.obs_rms
            clip = getattr(self.vecnorm, "clip_obs", 10.0)
            eps = getattr(self.vecnorm, "epsilon", 1e-8)
            return np.clip((obs - rms.mean) / np.sqrt(rms.var + eps), -clip, clip).astype(np.float32)
        return obs

    def act(self, obs: np.ndarray) -> tuple[float, float]:
        action, _ = self.model.predict(self._normalize(obs), deterministic=True)
        a = float(np.clip(action[0], -1, 1))
        defer = float(action[1]) if len(action) > 1 else -1.0
        return a, defer


def load_algo(algo: str):
    """Uzman modu için herhangi bir algoritmayı yükle (SAC/TD3/PPO/A2C)."""
    import stable_baselines3 as sb3

    cls = getattr(sb3, algo.upper())
    model = cls.load(MODELS / f"{algo.lower()}_phase3_final.zip", device="cpu")
    ag = SacAgent.__new__(SacAgent)
    ag.model = model
    ag.obs_dim = int(model.observation_space.shape[0])
    ag.vecnorm = None
    vn = MODELS / f"{algo.lower()}_phase3_vecnormalize.pkl"
    if vn.exists():
        with open(vn, "rb") as f:
            ag.vecnorm = pickle.load(f)
    ag.name = f"{algo.upper()} (eğitilmiş model)"
    return ag


def get_agent():
    """(ajan, durum_mesajı) döndürür — asla exception fırlatmaz."""
    try:
        return SacAgent(), "SAC ajanı yüklendi ✓"
    except Exception as e:  # torch/sb3 yok veya model bozuk
        return HeuristicAgent(), f"Model yüklenemedi, sezgisel politika aktif ({type(e).__name__})"

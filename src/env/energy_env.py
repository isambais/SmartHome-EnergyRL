"""SmartHomeEnergyEnv — Gerçek Dünya Kapsamlı Ev Enerji Yönetimi RL Ortamı.

Curriculum yapısı:
  Aşama 1 (solar_data=None): Saf batarya arbitrajı
  Aşama 2 (solar_data verildiğinde): Güneş + talep + batarya entegrasyonu

Gerçek dünya özellikleri:
  ─ Asimetrik fiyat       : Satış fiyatı = alış × sell_ratio (varsayılan 0.60)
  ─ SoH bozunumu          : Her episode [0.70,1.00] arasında rastgele SoH başlar
  ─ Öz-deşarj             : Saat başı küçük enerji kaybı (varsayılan %0.05)
  ─ Min SoC rezervi       : Kullanıcı tanımlı acil şarj alt sınırı (varsayılan %10)
  ─ Değişken verimlilik   : C-rate + SoC bağımlı (yavaş şarj → daha verimli)
  ─ Döngü cezası          : Her kWh döngü başına küçük ceza
  ─ Şebeke ihracat limiti : Sözleşme sınırı (varsayılan sınırsız)
  ─ Şebeke kesintisi      : Saat başı düşük olasılıkla ada moduna geçiş
  ─ Talep yanıtı          : Şebeke sinyal anında tüketimi azaltmak bonus getirir
  ─ Stokastik güneş/talep : Episode başında çarpımsal gürültü (bulutluluk vb.)
  ─ Yarınki fiyat tahmini : 48 saatlik gözlem penceresi (gün-öncesi pazar)
  ─ Zaman özellikleri     : sin/cos(saat, haftanın günü) → döngüsel kodlama

Gözlem boyutları (tüm özellikler açık):
  Aşama 1 : 8 + 24 + 24 = 56
  Aşama 2 : 8 + 24 + 24 + 24 + 24 = 104

  Detay (8 temel):
    [0]   soc              : Şarj durumu [0,1]
    [1]   soh              : Pil sağlığı [0.5,1.0]
    [2]   sin_hour         : Döngüsel saat kodlaması
    [3]   cos_hour
    [4]   sin_dow          : Döngüsel haftanın günü
    [5]   cos_dow
    [6]   grid_available   : 1=normal, 0=kesinti
    [7]   dr_signal        : 1=talep yanıtı eventi, 0=normal
    [8:32]  bugünkü fiyatlar (24 saat)
    [32:56] yarınki fiyat tahmini (24 saat, gürültülü)
    [56:80] güneş profili  (Aşama 2)
    [80:104] talep profili (Aşama 2)
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces

ObsType = np.ndarray
ActType = np.ndarray | list[float]
StepResult = tuple[ObsType, float, bool, bool, dict[str, Any]]
ResetResult = tuple[ObsType, dict[str, Any]]

_TWO_PI = 2.0 * np.pi


def split_into_daily_episodes(
    hourly_data: np.ndarray, hours_per_episode: int = 24
) -> np.ndarray:
    n_complete = len(hourly_data) // hours_per_episode
    trimmed = hourly_data[: n_complete * hours_per_episode]
    return trimmed.reshape(n_complete, hours_per_episode)


class SmartHomeEnergyEnv(gym.Env):

    metadata = {"render_modes": ["human"], "render_fps": 2}

    def __init__(
        self,
        price_data: pd.Series | np.ndarray,
        solar_data: np.ndarray | None = None,
        demand_data: np.ndarray | None = None,
        hours_per_episode: int = 24,

        # ── Fiyatlandırma ──────────────────────────────────────────
        sell_ratio: float = 0.60,          # satış fiyatı = alış × sell_ratio
        price_unit: str = "tl_per_mwh",

        # ── Pil ────────────────────────────────────────────────────
        battery_capacity_kwh: float = 10.0,
        max_power_kw: float = 5.0,
        variable_efficiency: bool = True,
        charge_eff_max: float = 0.98,      # yavaş şarjda maksimum verimlilik
        charge_eff_min: float = 0.88,      # tam hızda minimum verimlilik
        round_trip_efficiency: float = 0.90,  # variable_efficiency=False için
        soh_range: tuple[float, float] = (0.70, 1.00),  # episode başı SoH aralığı
        soh_fixed: float | None = None,    # None → rastgele, float → sabit
        soh_degradation_per_kwh: float = 5e-6,  # kWh başı SoH kaybı
        self_discharge_per_hour: float = 0.0005,  # saatlik fraksiyon kaybı
        min_soc_reserve: float = 0.10,     # acil şarj rezervi (deşarj alt sınırı)
        cycle_penalty_coef: float = 0.005, # TL / kWh döngü

        # ── Şebeke ─────────────────────────────────────────────────
        max_grid_export_kw: float | None = None,   # None = sınırsız
        grid_outage_prob: float = 0.002,   # saat başı kesinti olasılığı (%0.2)
        outage_unmet_penalty: float = 2.0,  # karşılanamayan talep için fiyat çarpanı

        # ── Talep Yanıtı ───────────────────────────────────────────
        dr_signal_prob: float = 0.05,      # saat başı DR sinyal olasılığı
        dr_reward_coef: float = 0.30,      # DR sırasında net ihracat başına TL bonus

        # ── Belirsizlik ────────────────────────────────────────────
        stochastic_solar: bool = True,
        stochastic_demand: bool = True,
        solar_noise_std: float = 0.10,     # çarpımsal gürültü std
        demand_noise_std: float = 0.15,

        # ── Gözlem ─────────────────────────────────────────────────
        time_features: bool = True,
        tomorrow_prices: bool = True,      # 48 saatlik gözlem penceresi
        forecast_noise_std: float = 0.05,  # yarınki fiyat tahmin hatası

        # ── Diğer ──────────────────────────────────────────────────
        initial_soc: float = 0.5,
        random_day: bool = True,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(f"render_mode '{render_mode}' desteklenmiyor.")
        self.render_mode = render_mode

        # Render state
        self._window = self._clock = self._font = self._font_small = None
        self._last_action = 0.0
        self._last_reward = 0.0
        self._last_eff = 1.0
        self._episode_total_reward = 0.0
        self._episode_total_cost = 0.0
        self._episode_total_revenue = 0.0

        # ── Fiyat verisi ───────────────────────────────────────────
        prices = np.asarray(price_data, dtype=np.float32)
        if price_unit == "tl_per_mwh":
            prices = prices / 1000.0
        elif price_unit != "tl_per_kwh":
            raise ValueError("price_unit 'tl_per_mwh' veya 'tl_per_kwh' olmalı.")

        self.daily_prices = split_into_daily_episodes(prices, hours_per_episode)
        n_days = len(self.daily_prices)
        if n_days == 0:
            raise ValueError("price_data yeterli veri içermiyor.")

        # ── Güneş ve talep verisi (Aşama 2) ───────────────────────
        self._phase2 = solar_data is not None and demand_data is not None
        if self._phase2:
            solar = np.asarray(solar_data, dtype=np.float32)
            demand = np.asarray(demand_data, dtype=np.float32)
            self.daily_solar = split_into_daily_episodes(solar, hours_per_episode)
            self.daily_demand = split_into_daily_episodes(demand, hours_per_episode)
            min_days = min(n_days, len(self.daily_solar), len(self.daily_demand))
            self.daily_prices = self.daily_prices[:min_days]
            self.daily_solar = self.daily_solar[:min_days]
            self.daily_demand = self.daily_demand[:min_days]
        else:
            _z = np.zeros((n_days, hours_per_episode), dtype=np.float32)
            self.daily_solar = _z
            self.daily_demand = _z.copy()

        # ── Parametreler ───────────────────────────────────────────
        self.hours_per_episode = hours_per_episode
        self.sell_ratio = float(sell_ratio)
        self.battery_capacity_kwh = float(battery_capacity_kwh)
        self.max_power_kw = float(max_power_kw)
        self.variable_efficiency = variable_efficiency
        self.charge_eff_max = float(charge_eff_max)
        self.charge_eff_min = float(charge_eff_min)
        _fixed = float(np.sqrt(round_trip_efficiency))
        self._fixed_charge_eff = _fixed
        self._fixed_discharge_eff = _fixed
        self.soh_range = soh_range
        self.soh_fixed = soh_fixed
        self.soh_degradation_per_kwh = float(soh_degradation_per_kwh)
        self.self_discharge_per_hour = float(self_discharge_per_hour)
        self.min_soc_reserve = float(min_soc_reserve)
        self.cycle_penalty_coef = float(cycle_penalty_coef)
        self.max_grid_export_kw = max_grid_export_kw
        self.grid_outage_prob = float(grid_outage_prob)
        self.outage_unmet_penalty = float(outage_unmet_penalty)
        self.dr_signal_prob = float(dr_signal_prob)
        self.dr_reward_coef = float(dr_reward_coef)
        self.stochastic_solar = stochastic_solar
        self.stochastic_demand = stochastic_demand
        self.solar_noise_std = float(solar_noise_std)
        self.demand_noise_std = float(demand_noise_std)
        self.time_features = time_features
        self.tomorrow_prices = tomorrow_prices
        self.forecast_noise_std = float(forecast_noise_std)
        self.initial_soc = float(initial_soc)
        self.random_day = random_day

        # ── Gözlem uzayı ───────────────────────────────────────────
        # 8 temel + bugün (24) + yarın (24 opsiyonel) + [solar+talep] (48 opsiyonel)
        _n_base = 8  # soc, soh, sin_h, cos_h, sin_dow, cos_dow, grid, dr
        _n_prices = hours_per_episode * (2 if tomorrow_prices else 1)
        _n_phase2 = hours_per_episode * 2 if self._phase2 else 0
        _obs_dim = _n_base + _n_prices + _n_phase2

        price_low = float(self.daily_prices.min())
        price_high = float(self.daily_prices.max())

        if self._phase2:
            solar_high = float(self.daily_solar.max()) + 0.1
            demand_high = float(self.daily_demand.max()) + 0.1
            p2_low = np.array([0.0] * hours_per_episode + [0.0] * hours_per_episode, dtype=np.float32)
            p2_high = np.array([solar_high] * hours_per_episode + [demand_high] * hours_per_episode, dtype=np.float32)
        else:
            p2_low = np.array([], dtype=np.float32)
            p2_high = np.array([], dtype=np.float32)

        price_arr_low = np.full(hours_per_episode, price_low, dtype=np.float32)
        price_arr_high = np.full(hours_per_episode, price_high, dtype=np.float32)

        if tomorrow_prices:
            prices_low = np.concatenate([price_arr_low, price_arr_low])
            prices_high = np.concatenate([price_arr_high, price_arr_high])
        else:
            prices_low = price_arr_low
            prices_high = price_arr_high

        low = np.concatenate([
            [0.0, 0.5, -1.0, -1.0, -1.0, -1.0, 0.0, 0.0],  # 8 temel
            prices_low,
            p2_low,
        ]).astype(np.float32)

        high = np.concatenate([
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # 8 temel
            prices_high,
            p2_high,
        ]).astype(np.float32)

        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

        # ── Durum değişkenleri ─────────────────────────────────────
        self.soc: float = self.initial_soc
        self.soh: float = 1.0
        self.t: int = 0
        self._day_idx: int = 0
        self._current_day_prices: np.ndarray = self.daily_prices[0]
        self._tomorrow_prices_obs: np.ndarray = self.daily_prices[0]
        self._current_day_solar: np.ndarray = self.daily_solar[0]
        self._current_day_demand: np.ndarray = self.daily_demand[0]
        self._grid_available: np.ndarray = np.ones(hours_per_episode, dtype=np.float32)
        self._dr_signals: np.ndarray = np.zeros(hours_per_episode, dtype=np.float32)

    # ── Verimlilik ────────────────────────────────────────────────

    def _compute_efficiency(self, action: float) -> tuple[float, float]:
        """C-rate ve SoC'a bağlı şarj/deşarj verimliliği."""
        if not self.variable_efficiency:
            return self._fixed_charge_eff, self._fixed_discharge_eff

        c_rate = abs(action)
        eff_range = self.charge_eff_max - self.charge_eff_min
        base_eff = self.charge_eff_max - eff_range * c_rate

        if action > 0.0:
            # Şarj: dolu bataryada verimlilik düşer
            soc_penalty = max(0.0, (self.soc - 0.85) / 0.15) * 0.05
            charge_eff = max(base_eff - soc_penalty, self.charge_eff_min)
            discharge_eff = self.charge_eff_max
        elif action < 0.0:
            # Deşarj: boş bataryada verimlilik düşer
            soc_penalty = max(0.0, (0.15 - self.soc) / 0.15) * 0.05
            discharge_eff = max(base_eff - soc_penalty, self.charge_eff_min)
            charge_eff = self.charge_eff_max
        else:
            charge_eff = discharge_eff = self.charge_eff_max

        return charge_eff, discharge_eff

    # ── Gözlem ───────────────────────────────────────────────────

    def _get_obs(self) -> np.ndarray:
        hour = self.t % self.hours_per_episode
        dow = self._day_idx % 7

        base = np.array([
            self.soc,
            self.soh,
            float(np.sin(hour * _TWO_PI / 24)),
            float(np.cos(hour * _TWO_PI / 24)),
            float(np.sin(dow * _TWO_PI / 7)),
            float(np.cos(dow * _TWO_PI / 7)),
            float(self._grid_available[hour]),
            float(self._dr_signals[hour]),
        ], dtype=np.float32)

        parts = [base, self._current_day_prices]

        if self.tomorrow_prices:
            parts.append(self._tomorrow_prices_obs)

        if self._phase2:
            parts.append(self._current_day_solar)
            parts.append(self._current_day_demand)

        return np.concatenate(parts).astype(np.float32)

    # ── Reset ────────────────────────────────────────────────────

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> ResetResult:
        super().reset(seed=seed)

        # Gün seçimi
        if self.random_day:
            self._day_idx = int(self.np_random.integers(0, len(self.daily_prices)))
        else:
            self._day_idx = (self._day_idx + 1) % len(self.daily_prices)

        self._current_day_prices = self.daily_prices[self._day_idx].copy()
        self._current_day_solar = self.daily_solar[self._day_idx].copy()
        self._current_day_demand = self.daily_demand[self._day_idx].copy()

        # Yarınki fiyat tahmini (gürültülü)
        tomorrow_idx = (self._day_idx + 1) % len(self.daily_prices)
        true_tomorrow = self.daily_prices[tomorrow_idx]
        if self.tomorrow_prices:
            noise = self.np_random.normal(0, self.forecast_noise_std, size=self.hours_per_episode).astype(np.float32)
            self._tomorrow_prices_obs = np.maximum(true_tomorrow * (1.0 + noise), 0.0)
        else:
            self._tomorrow_prices_obs = true_tomorrow.copy()

        # Stokastik güneş ve talep (bulutluluk, misafir etkisi vb.)
        if self._phase2 and self.stochastic_solar:
            scale = float(self.np_random.normal(1.0, self.solar_noise_std))
            self._current_day_solar = np.maximum(self._current_day_solar * scale, 0.0)

        if self._phase2 and self.stochastic_demand:
            scale = float(self.np_random.normal(1.0, self.demand_noise_std))
            self._current_day_demand = np.maximum(self._current_day_demand * scale, 0.1)

        # Pil durumu: SoH rastgele veya sabit
        if self.soh_fixed is not None:
            self.soh = float(self.soh_fixed)
        else:
            self.soh = float(self.np_random.uniform(self.soh_range[0], self.soh_range[1]))

        self.soc = self.initial_soc
        self.t = 0
        self._last_eff = self.charge_eff_max
        self._episode_total_reward = 0.0
        self._episode_total_cost = 0.0
        self._episode_total_revenue = 0.0

        # Günlük şebeke ve DR sinyalleri (episode başında üret)
        self._grid_available = (
            self.np_random.random(self.hours_per_episode) > self.grid_outage_prob
        ).astype(np.float32)

        self._dr_signals = (
            self.np_random.random(self.hours_per_episode) < self.dr_signal_prob
        ).astype(np.float32)

        return self._get_obs(), {"day_idx": self._day_idx, "soh": self.soh}

    # ── Step ────────────────────────────────────────────────────

    def step(self, action: ActType) -> StepResult:
        action = np.asarray(action, dtype=np.float32).reshape(-1)
        a = float(np.clip(action[0], -1.0, 1.0))

        price_buy_t = float(self._current_day_prices[self.t])
        price_sell_t = price_buy_t * self.sell_ratio
        solar_t = float(self._current_day_solar[self.t])
        demand_t = float(self._current_day_demand[self.t])
        grid_up = bool(self._grid_available[self.t])
        dr_on = bool(self._dr_signals[self.t])

        # ── Öz-deşarj ─────────────────────────────────────────
        self.soc = max(0.0, self.soc - self.self_discharge_per_hour)

        # ── Verimlilik ─────────────────────────────────────────
        charge_eff, discharge_eff = self._compute_efficiency(a)
        self._last_eff = (charge_eff + discharge_eff) / 2.0

        # ── Pil hareketi ───────────────────────────────────────
        requested_kwh = a * self.max_power_kw
        eff_capacity = self.battery_capacity_kwh * self.soh   # SoH'a göre gerçek kapasite
        battery_charge_kwh = 0.0
        battery_discharge_kwh = 0.0

        if requested_kwh > 0.0:  # Şarj
            headroom = (1.0 - self.soc) * eff_capacity
            max_charge = headroom / charge_eff if charge_eff > 0 else 0.0
            battery_charge_kwh = min(requested_kwh, max_charge)
            soc_delta = (battery_charge_kwh * charge_eff) / eff_capacity
            self.soc = float(np.clip(self.soc + soc_delta, 0.0, 1.0))

        elif requested_kwh < 0.0:  # Deşarj
            requested_dis = -requested_kwh
            # min_soc_reserve'in altına inemez
            available = max(0.0, self.soc - self.min_soc_reserve) * eff_capacity
            applied = min(requested_dis, available)
            soc_delta = applied / eff_capacity
            self.soc = float(np.clip(self.soc - soc_delta, 0.0, 1.0))
            battery_discharge_kwh = applied * discharge_eff

        # ── SoH bozunumu ───────────────────────────────────────
        energy_cycled = battery_charge_kwh + battery_discharge_kwh
        self.soh = max(0.50, self.soh - self.soh_degradation_per_kwh * energy_cycled)

        # ── Net şebeke ─────────────────────────────────────────
        # pozitif = satın alma, negatif = satış
        net_grid_kwh = demand_t - solar_t + battery_charge_kwh - battery_discharge_kwh

        # ── Şebeke kesintisi ───────────────────────────────────
        cost = revenue = 0.0
        unmet_penalty = 0.0

        if not grid_up:
            # Ada modu: şebekeden alınamaz, satılamaz
            if net_grid_kwh > 0.0:
                # Karşılanamayan talep: ceza
                unmet_penalty = net_grid_kwh * price_buy_t * self.outage_unmet_penalty
            # net < 0 → fazla enerji, kesintide satılamaz (israf)
        else:
            if net_grid_kwh > 0.0:
                # Alım
                cost = net_grid_kwh * price_buy_t
            else:
                # Satım — ihracat limiti var mı?
                export_kwh = -net_grid_kwh
                if self.max_grid_export_kw is not None:
                    export_kwh = min(export_kwh, self.max_grid_export_kw)
                revenue = export_kwh * price_sell_t

        # ── Talep yanıtı bonusu ────────────────────────────────
        dr_bonus = 0.0
        if dr_on and grid_up and net_grid_kwh <= 0.0:
            dr_bonus = (-net_grid_kwh) * self.dr_reward_coef

        # ── Döngü cezası ───────────────────────────────────────
        cycle_penalty = self.cycle_penalty_coef * energy_cycled

        # ── Ödül ───────────────────────────────────────────────
        reward = revenue - cost - unmet_penalty - cycle_penalty + dr_bonus

        self._last_action = a
        self._last_reward = reward
        self._episode_total_reward += reward
        self._episode_total_cost += cost
        self._episode_total_revenue += revenue

        self.t += 1
        terminated = self.t >= self.hours_per_episode

        info = {
            "day_idx": self._day_idx,
            "hour": self.t - 1,
            "price_buy_tl_kwh": price_buy_t,
            "price_sell_tl_kwh": price_sell_t,
            "solar_kw": solar_t,
            "demand_kw": demand_t,
            "net_grid_kwh": net_grid_kwh,
            "cost_tl": cost,
            "revenue_tl": revenue,
            "unmet_penalty_tl": unmet_penalty,
            "cycle_penalty_tl": cycle_penalty,
            "dr_bonus_tl": dr_bonus,
            "charge_eff": charge_eff,
            "discharge_eff": discharge_eff,
            "soh": self.soh,
            "grid_available": grid_up,
            "dr_signal": dr_on,
        }
        if terminated:
            info["episode"] = {
                "total_reward": self._episode_total_reward,
                "total_cost": self._episode_total_cost,
                "total_revenue": self._episode_total_revenue,
            }

        if self.render_mode == "human":
            self.render()

        return self._get_obs(), reward, terminated, False, info

    # ── Render ──────────────────────────────────────────────────

    def render(self) -> None:
        if self.render_mode != "human":
            return None
        import pygame

        W, H = 800, 460
        if self._window is None:
            pygame.init()
            pygame.display.set_caption("SmartHomeEnergyEnv")
            self._window = pygame.display.set_mode((W, H))
            self._clock = pygame.time.Clock()
            self._font = pygame.font.SysFont("arial", 21)
            self._font_small = pygame.font.SysFont("arial", 15)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close(); return

        BG = (24, 26, 30); WHITE = (235, 235, 235); GRAY = (90, 95, 100)
        GREEN = (60, 180, 100); RED = (200, 70, 70); AMBER = (230, 170, 40)
        BLUE = (70, 140, 220); PURPLE = (150, 100, 220)

        s = self._window
        s.fill(BG)

        # Batarya
        bx, by, bw, bh = 40, 60, 130, 240
        pygame.draw.rect(s, GRAY, (bx, by, bw, bh), width=3, border_radius=6)
        pygame.draw.rect(s, GRAY, (bx + 40, by - 14, 50, 14), border_radius=3)
        fh = int(bh * self.soc)
        sc = RED if self.soc < 0.2 else (AMBER if self.soc < 0.6 else GREEN)
        if fh > 8:
            pygame.draw.rect(s, sc, (bx+4, by+(bh-fh)+4, bw-8, fh-8), border_radius=4)
        s.blit(self._font.render(f"SoC: %{int(self.soc*100)}", True, WHITE), (bx, by+bh+10))
        s.blit(self._font_small.render(f"SoH: %{int(self.soh*100)}", True, AMBER), (bx, by+bh+32))
        s.blit(self._font_small.render(f"Verim: %{int(self._last_eff*100)}", True, GRAY), (bx, by+bh+50))

        # Grid/DR göstergeleri
        g_color = GREEN if self._grid_available[min(self.t, self.hours_per_episode-1)] else RED
        s.blit(self._font_small.render(
            "ŞEBEKE: " + ("✓" if self._grid_available[min(self.t, self.hours_per_episode-1)] else "KESİNTİ"),
            True, g_color), (bx, by+bh+70))
        if self._dr_signals[min(self.t, self.hours_per_episode-1)]:
            s.blit(self._font_small.render("⚡ DR SİNYALİ", True, PURPLE), (bx, by+bh+88))

        # Aksiyon oku
        ax, ay = bx+bw+60, by+bh//2
        if self._last_action > 0.02:
            pygame.draw.polygon(s, GREEN, [(ax, ay+28),(ax+36,ay+28),(ax+18,ay-18)])
            s.blit(self._font.render("ŞARJ", True, GREEN), (ax-5, ay+42))
        elif self._last_action < -0.02:
            pygame.draw.polygon(s, RED, [(ax, ay-28),(ax+36,ay-28),(ax+18,ay+18)])
            s.blit(self._font.render("DEŞARJ", True, RED), (ax-10, ay+42))
        else:
            pygame.draw.circle(s, GRAY, (ax+18, ay), 13, width=3)
            s.blit(self._font.render("BEKLE", True, GRAY), (ax-5, ay+42))

        # Fiyat grafiği
        cx, cy, cw, ch = 410, 40, 340, 200
        prices = self._current_day_prices
        pm, px_ = float(prices.min()), float(prices.max())
        pr = (px_ - pm) or 1.0
        bw2 = cw / len(prices)
        cur = min(self.t, len(prices)-1)
        for i, p in enumerate(prices):
            bh2 = int(((p - pm) / pr) * ch)
            col = AMBER if i == cur else BLUE
            pygame.draw.rect(s, col, (cx+i*bw2, cy+(ch-bh2), max(bw2-1,1), bh2))

        s.blit(self._font_small.render("Bugünkü fiyat (TL/kWh) — turuncu=şu an", True, WHITE), (cx, cy+ch+6))

        # Bilgi satırları
        lines = [
            f"Saat: {cur:02d}:00",
            f"Alış: {price_buy_t:.3f} / Satış: {float(price_buy_t*self.sell_ratio):.3f} TL/kWh" if hasattr(self, '_last_action') else "",
            f"Son ödül: {self._last_reward:+.2f} TL",
        ]
        if self._phase2:
            lines.append(f"Güneş: {float(self._current_day_solar[cur]):.2f} kW  Talep: {float(self._current_day_demand[cur]):.2f} kW")

        # price_buy_t için mevcut adım fiyatını düzelt
        price_buy_t = float(self._current_day_prices[cur])
        lines[1] = f"Alış: {price_buy_t:.3f} / Satış: {price_buy_t*self.sell_ratio:.3f} TL/kWh"

        for i, ln in enumerate(lines):
            if ln:
                s.blit(self._font.render(ln, True, WHITE), (cx, cy+ch+30+i*26))

        pygame.display.flip()
        self._clock.tick(self.metadata["render_fps"])

    def close(self) -> None:
        if self._window is not None:
            import pygame
            pygame.display.quit(); pygame.quit()
            self._window = None

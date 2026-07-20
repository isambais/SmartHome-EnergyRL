"""Curriculum Aşama 1 için minimal SmartHomeEnergyEnv: saf batarya arbitrajı.

implementation_plan.md Bölüm 6 (RL Problem Formülasyonu) ve Bölüm 15 (Gün 5)
kapsamında:
    - Gözlem: batarya SOC'si (0-1) + 24 saatlik elektrik fiyatı (oracle, TL/kWh).
      Güneş üretimi, ev talebi ve ertelenebilir cihazlar bu aşamada yok.
    - Aksiyon: battery_action ∈ [-1, 1] (tek boyutlu, sürekli). Pozitif değer
      şarj, negatif değer deşarj demektir.
    - Batarya fizik modeli: basit doğrusal şarj/deşarj verimliliği (round-trip
      efficiency), SOC 0-1 sınırları asla aşılmaz.
    - Ödül: reward = -(saatlik şebeke maliyeti) + (deşarjdan gelen gelir) —
      Bölüm 9'daki genel ödül formunun, bu aşamada ev talebi/güneş olmadığı
      için sadeleşmiş hâli.

Beklenti (Bölüm 6): ajanın gece ucuzken şarj edip akşam pahalıyken deşarj
etmeyi (arbitraj) öğrenmesi.
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


def split_into_daily_episodes(
    hourly_prices: np.ndarray, hours_per_episode: int = 24
) -> np.ndarray:
    """Saatlik fiyat dizisini (N,) sabit uzunluklu bölüm (episode) bloklarına ayırır.

    N, hours_per_episode'a tam bölünmüyorsa sondaki eksik blok atılır.
    Dönen dizi şekli: (n_episodes, hours_per_episode).
    """
    n_complete = len(hourly_prices) // hours_per_episode
    trimmed = hourly_prices[: n_complete * hours_per_episode]
    return trimmed.reshape(n_complete, hours_per_episode)


class SmartHomeEnergyEnv(gym.Env):
    """Curriculum Aşama 1: sadece batarya SOC'si ve 24 saatlik (oracle) fiyat
    gözlemlenen, tek boyutlu sürekli battery_action aksiyonuna sahip ortam.
    """

    metadata = {"render_modes": ["human"], "render_fps": 2}

    def __init__(
        self,
        price_data: pd.Series | np.ndarray,
        hours_per_episode: int = 24,
        battery_capacity_kwh: float = 10.0,
        max_power_kw: float = 5.0,
        round_trip_efficiency: float = 0.9,
        initial_soc: float = 0.5,
        random_day: bool = True,
        price_unit: str = "tl_per_mwh",
        render_mode: str | None = None,
    ) -> None:
        super().__init__()

        if render_mode is not None and render_mode not in self.metadata["render_modes"]:
            raise ValueError(
                f"render_mode '{render_mode}' desteklenmiyor. Seçenekler: {self.metadata['render_modes']}"
            )
        self.render_mode = render_mode
        self._window = None
        self._clock = None
        self._font = None
        self._font_small = None
        self._last_action = 0.0
        self._last_reward = 0.0

        if not 0.0 < round_trip_efficiency <= 1.0:
            raise ValueError("round_trip_efficiency (0, 1] aralığında olmalı.")
        if not 0.0 <= initial_soc <= 1.0:
            raise ValueError("initial_soc [0, 1] aralığında olmalı.")

        prices = np.asarray(price_data, dtype=np.float32)
        if price_unit == "tl_per_mwh":
            prices = (
                prices / 1000.0
            )  # TL/MWh -> TL/kWh, ödül ölçeği daha okunur olsun diye
        elif price_unit != "tl_per_kwh":
            raise ValueError("price_unit 'tl_per_mwh' veya 'tl_per_kwh' olmalı.")

        self.daily_prices = split_into_daily_episodes(prices, hours_per_episode)
        if len(self.daily_prices) == 0:
            raise ValueError(
                f"price_data en az {hours_per_episode} saatlik tam bir bölüm içermiyor."
            )

        self.hours_per_episode = hours_per_episode
        self.battery_capacity_kwh = battery_capacity_kwh
        self.max_power_kw = max_power_kw
        # Simetrik verimlilik bölüşümü: charge_eff * discharge_eff = round_trip_efficiency
        self.charge_efficiency = float(np.sqrt(round_trip_efficiency))
        self.discharge_efficiency = float(np.sqrt(round_trip_efficiency))
        self.initial_soc = initial_soc
        self.random_day = random_day

        price_low = float(self.daily_prices.min())
        price_high = float(self.daily_prices.max())
        # Gözlem: [soc, price_0, price_1, ..., price_{hours_per_episode-1}]
        low = np.array([0.0] + [price_low] * hours_per_episode, dtype=np.float32)
        high = np.array([1.0] + [price_high] * hours_per_episode, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

        self.soc: float = self.initial_soc
        self.t: int = 0
        self._day_idx: int = 0
        self._current_day_prices: np.ndarray = self.daily_prices[0]

    def _get_obs(self) -> np.ndarray:
        return np.concatenate(([self.soc], self._current_day_prices)).astype(np.float32)

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> ResetResult:
        super().reset(seed=seed)

        if self.random_day:
            self._day_idx = int(self.np_random.integers(0, len(self.daily_prices)))
        else:
            self._day_idx = (self._day_idx + 1) % len(self.daily_prices)

        self._current_day_prices = self.daily_prices[self._day_idx]
        self.soc = self.initial_soc
        self.t = 0

        observation = self._get_obs()
        info = {"day_idx": self._day_idx}
        return observation, info

    def step(self, action: ActType) -> StepResult:
        action = np.asarray(action, dtype=np.float32).reshape(-1)
        a = float(np.clip(action[0], -1.0, 1.0))

        price_t = float(self._current_day_prices[self.t])
        requested_energy_kwh = a * self.max_power_kw

        cost = 0.0
        revenue = 0.0
        applied_energy_kwh = 0.0

        if requested_energy_kwh > 0.0:
            # Şarj: batarya doluluk payı kadar (charge_efficiency ile) şarj edilebilir.
            headroom_kwh = (1.0 - self.soc) * self.battery_capacity_kwh
            max_grid_draw = (
                headroom_kwh / self.charge_efficiency
                if self.charge_efficiency > 0
                else 0.0
            )
            applied_energy_kwh = min(requested_energy_kwh, max_grid_draw)
            soc_delta = (
                applied_energy_kwh * self.charge_efficiency
            ) / self.battery_capacity_kwh
            self.soc = float(np.clip(self.soc + soc_delta, 0.0, 1.0))
            cost = price_t * applied_energy_kwh
        elif requested_energy_kwh < 0.0:
            # Deşarj: bataryada mevcut enerji kadar deşarj edilebilir.
            requested_discharge = -requested_energy_kwh
            available_kwh = self.soc * self.battery_capacity_kwh
            applied_energy_kwh = min(requested_discharge, available_kwh)
            soc_delta = applied_energy_kwh / self.battery_capacity_kwh
            self.soc = float(np.clip(self.soc - soc_delta, 0.0, 1.0))
            delivered_kwh = applied_energy_kwh * self.discharge_efficiency
            revenue = price_t * delivered_kwh

        reward = revenue - cost
        self._last_action = a
        self._last_reward = reward

        self.t += 1
        terminated = self.t >= self.hours_per_episode
        truncated = False

        if terminated:
            # Bölüm bittiğinde bir sonraki step() çağrısı reset gerektirir;
            # yine de indeks taşmasını önlemek için gözlemi son geçerli saate göre üretiyoruz.
            observation = self._get_obs()
        else:
            observation = self._get_obs()

        info = {
            "day_idx": self._day_idx,
            "hour": self.t - 1,
            "price_tl_kwh": price_t,
            "cost_tl": cost,
            "revenue_tl": revenue,
        }

        if self.render_mode == "human":
            self.render()

        return observation, reward, terminated, truncated, info

    def render(self) -> None:
        """render_mode='human' ise pygame ile canlı bir pencerede ortamın o anki
        durumunu (saat, fiyat, batarya SOC'si, son aksiyon/ödül) çizer.
        """
        if self.render_mode != "human":
            return None

        import pygame

        window_w, window_h = 760, 420

        if self._window is None:
            pygame.init()
            pygame.display.set_caption("SmartHomeEnergyEnv - Curriculum Asama 1")
            self._window = pygame.display.set_mode((window_w, window_h))
            self._clock = pygame.time.Clock()
            self._font = pygame.font.SysFont("arial", 22)
            self._font_small = pygame.font.SysFont("arial", 16)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return None

        BG = (24, 26, 30)
        WHITE = (235, 235, 235)
        GRAY = (90, 95, 100)
        GREEN = (60, 180, 100)
        RED = (200, 70, 70)
        AMBER = (230, 170, 40)
        BLUE = (70, 140, 220)

        surface = self._window
        surface.fill(BG)

        # --- Batarya kutusu (soldan) ---
        batt_x, batt_y, batt_w, batt_h = 60, 60, 140, 260
        pygame.draw.rect(
            surface, GRAY, (batt_x, batt_y, batt_w, batt_h), width=3, border_radius=6
        )
        pygame.draw.rect(
            surface, GRAY, (batt_x + 45, batt_y - 16, 50, 16), border_radius=3
        )

        fill_h = int(batt_h * self.soc)
        soc_color = RED if self.soc < 0.2 else (AMBER if self.soc < 0.6 else GREEN)
        pygame.draw.rect(
            surface,
            soc_color,
            (
                batt_x + 4,
                batt_y + (batt_h - fill_h) + 4,
                batt_w - 8,
                fill_h - 8 if fill_h > 8 else 0,
            ),
            border_radius=4,
        )

        soc_label = self._font.render(f"SOC: %{int(self.soc * 100)}", True, WHITE)
        surface.blit(soc_label, (batt_x, batt_y + batt_h + 14))

        # --- Aksiyon oku ---
        arrow_x = batt_x + batt_w + 70
        arrow_y = batt_y + batt_h // 2
        if self._last_action > 0.02:
            pygame.draw.polygon(
                surface,
                GREEN,
                [
                    (arrow_x, arrow_y + 30),
                    (arrow_x + 40, arrow_y + 30),
                    (arrow_x + 20, arrow_y - 20),
                ],
            )
            action_text = "SARJ"
            action_color = GREEN
        elif self._last_action < -0.02:
            pygame.draw.polygon(
                surface,
                RED,
                [
                    (arrow_x, arrow_y - 30),
                    (arrow_x + 40, arrow_y - 30),
                    (arrow_x + 20, arrow_y + 20),
                ],
            )
            action_text = "DESARJ"
            action_color = RED
        else:
            pygame.draw.circle(surface, GRAY, (arrow_x + 20, arrow_y), 14, width=3)
            action_text = "BEKLE"
            action_color = GRAY
        action_label = self._font.render(action_text, True, action_color)
        surface.blit(action_label, (arrow_x - 10, arrow_y + 45))

        # --- Sağda: 24 saatlik fiyat çubukları, o anki saat vurgulu ---
        chart_x, chart_y, chart_w, chart_h = 400, 40, 320, 200
        prices = self._current_day_prices
        p_min, p_max = float(prices.min()), float(prices.max())
        p_range = (p_max - p_min) or 1.0
        bar_w = chart_w / len(prices)
        current_hour = min(self.t, len(prices) - 1)

        for i, price in enumerate(prices):
            bar_h = int(((price - p_min) / p_range) * chart_h)
            bar_color = BLUE if i != current_hour else AMBER
            pygame.draw.rect(
                surface,
                bar_color,
                (
                    chart_x + i * bar_w,
                    chart_y + (chart_h - bar_h),
                    max(bar_w - 1, 1),
                    bar_h,
                ),
            )
        axis_label = self._font_small.render(
            "Gunun fiyat egrisi (TL/kWh) - turuncu = su an", True, WHITE
        )
        surface.blit(axis_label, (chart_x, chart_y + chart_h + 8))

        # --- Üst bilgi paneli ---
        info_lines = [
            f"Saat: {current_hour:02d}:00",
            f"Fiyat: {float(prices[current_hour]):.2f} TL/kWh",
            f"Son odul: {self._last_reward:+.2f} TL",
        ]
        for idx, line in enumerate(info_lines):
            label = self._font.render(line, True, WHITE)
            surface.blit(label, (400, chart_y + chart_h + 40 + idx * 28))

        pygame.display.flip()
        self._clock.tick(self.metadata["render_fps"])
        return None

    def close(self) -> None:
        if self._window is not None:
            import pygame

            pygame.display.quit()
            pygame.quit()
            self._window = None

"""Birim testleri — src/baselines/rule_based.py

Her politikanın:
  - Doğru aksiyon döndürdüğü (şarj/deşarj/bekle)
  - action_space uyumlu shape ve dtype ürettiği
  - Sınır koşullarında (SOC=0, SOC=1, kesinti) beklenen davranışı sergilediği
test edilir.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.baselines.rule_based import (
    ForecastAwarePolicy,
    GridAwarePolicy,
    HoldPolicy,
    PeakShavingPolicy,
    SelfConsumptionPolicy,
    ThresholdPolicy,
    ToUPolicy,
)

# ── Yardımcı sabitler & fabrika fonksiyonları ─────────────────────────────────

N_OBS = 104  # Aşama 2 gözlem boyutu

# Saatlik fiyatlar: gece ucuz (indeks 0-6), sabah orta, akşam pahalı
CHEAP_PRICES  = np.full(24, 1000.0, dtype=np.float32)  # her saat ucuz
MEDIUM_PRICES = np.full(24, 2500.0, dtype=np.float32)  # her saat orta
EXPENSIVE_PRICES = np.full(24, 4000.0, dtype=np.float32)  # her saat pahalı

# Yarınki tahmin fiyatları
TOMORROW_EXPENSIVE = np.full(24, 6000.0, dtype=np.float32)  # yarın çok pahalı
TOMORROW_CHEAP     = np.full(24,  500.0, dtype=np.float32)  # yarın çok ucuz


def make_obs(
    soc: float = 0.5,
    grid: int = 1,
    dr: int = 0,
    today_prices: np.ndarray | None = None,
    tomorrow_prices: np.ndarray | None = None,
    solar_kw: float = 0.0,
    demand_kw: float = 1.0,
) -> np.ndarray:
    """Test gözlemi oluştur."""
    obs = np.zeros(N_OBS, dtype=np.float32)
    obs[0] = soc
    obs[6] = grid
    obs[7] = dr
    obs[8:32]  = today_prices    if today_prices    is not None else MEDIUM_PRICES
    obs[32:56] = tomorrow_prices if tomorrow_prices is not None else MEDIUM_PRICES
    obs[56:80] = solar_kw    # güneş profili (tüm saatler aynı değer)
    obs[80:104]= demand_kw   # talep profili (tüm saatler aynı değer)
    return obs


class DummyEnv:
    """Minimum env arayüzü — sadece baseline politikaların ihtiyacı olan alanlar."""

    def __init__(self, t: int = 12, prices: np.ndarray | None = None) -> None:
        self.t = t
        self._current_day_prices = (
            prices if prices is not None else MEDIUM_PRICES
        )

    @property
    def action_space(self):
        import gymnasium as gym
        return gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)


def assert_action(action: np.ndarray, expected: float, tol: float = 1e-5) -> None:
    assert action.shape == (1,), f"Beklenen shape (1,), alınan {action.shape}"
    assert action.dtype == np.float32, f"dtype float32 olmalı, alınan {action.dtype}"
    assert abs(float(action[0]) - expected) < tol, (
        f"Beklenen aksiyon {expected}, alınan {float(action[0]):.4f}"
    )


# ── HoldPolicy ────────────────────────────────────────────────────────────────

class TestHoldPolicy:
    def setup_method(self):
        self.policy = HoldPolicy()
        self.env = DummyEnv()

    def test_always_zero(self):
        for soc in [0.0, 0.5, 1.0]:
            obs = make_obs(soc=soc)
            assert_action(self.policy(obs, self.env), 0.0)

    def test_shape_dtype(self):
        obs = make_obs()
        action = self.policy(obs, self.env)
        assert action.shape == (1,)
        assert action.dtype == np.float32

    def test_repr(self):
        assert "HoldPolicy" in repr(self.policy)


# ── ThresholdPolicy ───────────────────────────────────────────────────────────

class TestThresholdPolicy:
    def setup_method(self):
        self.policy = ThresholdPolicy(low_pct=30, high_pct=70)

    def test_charge_when_cheap(self):
        """Ucuz saatte şarj et."""
        obs = make_obs(today_prices=MEDIUM_PRICES)
        env = DummyEnv(t=0, prices=CHEAP_PRICES)   # fiyat 1000 — P30 altında
        obs[8:32] = MEDIUM_PRICES
        # Mevcut fiyat çok ucuz → şarj
        env2 = DummyEnv(t=0, prices=np.array([500.0] * 24, dtype=np.float32))
        obs2 = make_obs(today_prices=np.array([500.0] * 24, dtype=np.float32))
        assert_action(self.policy(obs2, env2), 1.0)

    def test_discharge_when_expensive(self):
        """Pahalı saatte deşarj et."""
        prices = np.array([500.0] * 20 + [5000.0] * 4, dtype=np.float32)
        obs = make_obs(today_prices=prices)
        env = DummyEnv(t=22, prices=prices)
        assert_action(self.policy(obs, env), -1.0)

    def test_hold_when_medium(self):
        """Orta fiyatta bekle."""
        # Yarısı ucuz, yarısı pahalı, ortası orta
        prices = np.concatenate([
            np.full(8, 500.0),
            np.full(8, 2500.0),
            np.full(8, 5000.0),
        ]).astype(np.float32)
        obs = make_obs(today_prices=prices)
        env = DummyEnv(t=12, prices=prices)  # t=12 → fiyat 2500 (P30-P70 arası)
        assert_action(self.policy(obs, env), 0.0)

    def test_custom_percentiles(self):
        policy = ThresholdPolicy(low_pct=10, high_pct=90)
        assert "P10" in repr(policy)
        assert "P90" in repr(policy)


# ── SelfConsumptionPolicy ─────────────────────────────────────────────────────

class TestSelfConsumptionPolicy:
    def setup_method(self):
        self.policy = SelfConsumptionPolicy()

    def test_charge_on_solar_surplus(self):
        """Güneş fazlası varsa şarj et."""
        obs = make_obs(solar_kw=3.0, demand_kw=1.0)  # fazla 2 kW
        env = DummyEnv(t=10)
        assert_action(self.policy(obs, env), 1.0)

    def test_discharge_when_expensive_and_has_charge(self):
        """Pahalı saatte ve batarya doluysa deşarj et."""
        prices = np.array([500.0] * 20 + [5000.0] * 4, dtype=np.float32)
        obs = make_obs(soc=0.8, today_prices=prices, solar_kw=0.0, demand_kw=1.5)
        env = DummyEnv(t=22, prices=prices)
        assert_action(self.policy(obs, env), -1.0)

    def test_hold_when_no_solar_medium_price(self):
        """Güneş yok, orta fiyat → bekle.

        SelfConsumptionPolicy yüksek eşiği için P60 kullanır. P60'ın
        mevcut fiyattan kesinlikle yüksek, P30'un kesinlikle düşük olması
        için asimetrik bir dağılım gereklidir.

        Dağılım: 2×500 + 5×1000 + 5×2000 + 12×4000 (toplam=24)
          numpy P30 (i=6.9) → 1000 + 0.9×(2000-1000) = 1900
          numpy P60 (i=13.8) → 4000
        t=9 → prices[9]=2000 > 1900 (şarj yok), 2000 < 4000 (deşarj yok) → bekle
        """
        prices = np.array(
            [500.0] * 2 + [1000.0] * 5 + [2000.0] * 5 + [4000.0] * 12,
            dtype=np.float32,
        )
        obs = make_obs(soc=0.5, today_prices=prices, solar_kw=0.0, demand_kw=1.0)
        env = DummyEnv(t=9, prices=prices)   # prices[9] = 2000
        assert_action(self.policy(obs, env), 0.0)


# ── ToUPolicy ─────────────────────────────────────────────────────────────────

class TestToUPolicy:
    def setup_method(self):
        self.policy = ToUPolicy(
            peak_hours=[(17, 22)],
            off_peak_hours=[(23, 24), (0, 7)],
        )
        self.obs = make_obs()

    def test_discharge_during_peak(self):
        """Pik saatinde (17-22) deşarj et."""
        for hour in [17, 18, 19, 20, 21]:
            env = DummyEnv(t=hour)
            assert_action(self.policy(self.obs, env), -1.0)

    def test_charge_during_off_peak(self):
        """Gece saatinde (23-06) şarj et."""
        for hour in [0, 1, 2, 3, 4, 5, 6, 23]:
            env = DummyEnv(t=hour)
            assert_action(self.policy(self.obs, env), 1.0)

    def test_hold_during_day(self):
        """Gündüz saatinde (07-16) bekle."""
        for hour in [7, 10, 14, 16]:
            env = DummyEnv(t=hour)
            assert_action(self.policy(self.obs, env), 0.0)

    def test_repr(self):
        assert "ToUPolicy" in repr(self.policy)


# ── ForecastAwarePolicy ───────────────────────────────────────────────────────

class TestForecastAwarePolicy:
    def setup_method(self):
        self.policy = ForecastAwarePolicy(
            tomorrow_premium=0.15,
            tomorrow_discount=0.15,
        )

    def test_agressive_charge_when_tomorrow_expensive(self):
        """Yarın çok pahalıysa ve fiyat orta düzeydeyse şarj et."""
        today = np.full(24, 2000.0, dtype=np.float32)
        tomorrow = np.full(24, 5000.0, dtype=np.float32)  # %150 daha pahalı
        obs = make_obs(soc=0.3, today_prices=today, tomorrow_prices=tomorrow)
        env = DummyEnv(t=6, prices=today)  # sabah, fiyat orta
        action = self.policy(obs, env)
        # Yarın çok pahalı + şu an orta fiyat → şarj beklenir
        assert float(action[0]) >= 0.0, "Yarın pahalıyken şarj ya da bekle beklenir"

    def test_hold_when_tomorrow_cheap(self):
        """Yarın çok ucuzsa bugün şarj etme."""
        today = np.full(24, 2000.0, dtype=np.float32)
        tomorrow = np.full(24, 500.0, dtype=np.float32)   # %75 daha ucuz
        obs = make_obs(soc=0.5, today_prices=today, tomorrow_prices=tomorrow)
        env = DummyEnv(t=10, prices=today)  # gündüz, orta fiyat
        action = self.policy(obs, env)
        # Yarın ucuz → bugün şarj etme (0 ya da deşarj)
        assert float(action[0]) <= 0.0, "Yarın ucuzken şarj edilmemeli"


# ── PeakShavingPolicy ─────────────────────────────────────────────────────────

class TestPeakShavingPolicy:
    def setup_method(self):
        self.policy = PeakShavingPolicy(peak_threshold_kw=2.0, reserve_soc=0.30)

    def test_discharge_when_peak_exceeded(self):
        """Net şebeke çekişi eşik üzerindeyse deşarj et."""
        obs = make_obs(soc=0.8, solar_kw=0.5, demand_kw=5.0)  # net=4.5 kW > 2.0
        env = DummyEnv(t=14)
        assert_action(self.policy(obs, env), -1.0)

    def test_no_discharge_when_battery_low(self):
        """Batarya rezervin altındaysa deşarj etme."""
        obs = make_obs(soc=0.10, solar_kw=0.0, demand_kw=5.0)  # SOC < reserve
        env = DummyEnv(t=14)
        # SOC rezerv altında → deşarj olmamalı
        action = self.policy(obs, env)
        assert float(action[0]) >= 0.0

    def test_no_discharge_when_solar_covers_demand(self):
        """Güneş talebi karşılıyorsa tepe yok, deşarj gerekmez."""
        obs = make_obs(soc=0.8, solar_kw=6.0, demand_kw=3.0)  # net=0 kW
        env = DummyEnv(t=12)
        action = self.policy(obs, env)
        assert float(action[0]) >= 0.0  # şarj ya da bekle


# ── GridAwarePolicy ───────────────────────────────────────────────────────────

class TestGridAwarePolicy:
    def setup_method(self):
        self.policy = GridAwarePolicy(emergency_reserve=0.40)

    def test_low_discharge_during_outage_with_enough_soc(self):
        """Kesinti + SOC rezerv üstünde → düşük güçte deşarj."""
        obs = make_obs(soc=0.8, grid=0, dr=0)
        env = DummyEnv(t=12)
        action = self.policy(obs, env)
        assert float(action[0]) < 0.0, "Kesintide SOC yeterliyse deşarj etmeli"

    def test_hold_during_outage_low_soc(self):
        """Kesinti + SOC rezerv altında → rezervi koru."""
        obs = make_obs(soc=0.20, grid=0, dr=0)
        env = DummyEnv(t=12)
        assert_action(self.policy(obs, env), 0.0)

    def test_discharge_on_dr_signal(self):
        """DR sinyali + yeterli SOC → deşarj et."""
        obs = make_obs(soc=0.8, grid=1, dr=1)
        env = DummyEnv(t=18)
        assert_action(self.policy(obs, env), -1.0)

    def test_hold_on_dr_signal_empty_battery(self):
        """DR sinyali ama batarya boş → bekle."""
        obs = make_obs(soc=0.05, grid=1, dr=1)
        env = DummyEnv(t=18)
        assert_action(self.policy(obs, env), 0.0)

    def test_normal_mode_follows_threshold(self):
        """Normal modda threshold kuralını izle."""
        obs = make_obs(soc=0.5, grid=1, dr=0,
                       today_prices=CHEAP_PRICES)
        env = DummyEnv(t=5, prices=CHEAP_PRICES)
        assert_action(self.policy(obs, env), 1.0)   # ucuz → şarj


# ── Aşama 3: Faz 3 Deferrable Aksiyon Testleri ──────────────────────────────

N_OBS_PHASE3 = 106  # 104 (Aşama 2) + 2 (device_used_today + steps_remaining)


class DummyEnvPhase3(DummyEnv):
    """enable_deferrable=True olan minimum env."""

    def __init__(self, t: int = 10, prices: np.ndarray | None = None) -> None:
        super().__init__(t=t, prices=prices)
        self.enable_deferrable = True

    @property
    def action_space(self):
        import gymnasium as gym
        return gym.spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)


def make_obs_phase3(**kwargs) -> np.ndarray:
    """Aşama 3 gözlemi oluştur (104 + 2 = 106 boyutlu)."""
    base = make_obs(**kwargs)
    deferrable = np.zeros(2, dtype=np.float32)  # [device_used_today, steps_remaining_norm]
    return np.concatenate([base, deferrable])


class TestPhase3DeferrableActions:
    """Tüm politikaların Faz 3 (enable_deferrable=True) ortamda (2,) aksiyon döndürdüğünü doğrula."""

    def setup_method(self):
        self.env = DummyEnvPhase3(t=10)
        self.obs = make_obs_phase3()
        self.obs_cheap = make_obs_phase3(today_prices=CHEAP_PRICES)
        self.obs_window = make_obs_phase3()  # saat 10 → pencere içi (6-22)

    def _assert_phase3_action(self, action: np.ndarray) -> None:
        assert action.shape == (2,), f"Faz 3'te shape (2,) beklenir, alınan {action.shape}"
        assert action.dtype == np.float32
        assert -1.0 <= float(action[0]) <= 1.0, "Batarya aksiyonu [-1,1] aralığında olmalı"
        assert -1.0 <= float(action[1]) <= 1.0, "Deferrable sinyal [-1,1] aralığında olmalı"

    def test_hold_policy_returns_2d(self):
        action = HoldPolicy()(self.obs, self.env)
        self._assert_phase3_action(action)
        assert float(action[0]) == pytest.approx(0.0)   # batarya: bekle
        assert float(action[1]) < 0.0                   # cihaz: çalıştırma

    def test_threshold_policy_returns_2d(self):
        action = ThresholdPolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_threshold_activates_on_cheap_price(self):
        """ThresholdPolicy ucuz fiyatta cihaz sinyali > 0 vermeli."""
        env_cheap = DummyEnvPhase3(t=5, prices=np.array([500.0] * 24, dtype=np.float32))
        obs_cheap = make_obs_phase3(today_prices=np.array([500.0] * 24, dtype=np.float32))
        action = ThresholdPolicy()(obs_cheap, env_cheap)
        self._assert_phase3_action(action)
        assert float(action[1]) > 0.0, "Ucuz fiyatta deferrable sinyali pozitif olmalı"

    def test_self_consumption_policy_returns_2d(self):
        action = SelfConsumptionPolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_self_consumption_activates_on_solar_surplus(self):
        """SelfConsumptionPolicy güneş fazlasında cihaz sinyali > 0 vermeli."""
        obs = make_obs_phase3(solar_kw=5.0, demand_kw=1.0)  # 4 kW fazla
        action = SelfConsumptionPolicy(solar_surplus_threshold=0.1)(obs, self.env)
        self._assert_phase3_action(action)
        assert float(action[1]) > 0.0, "Güneş fazlasında deferrable sinyali pozitif olmalı"

    def test_tou_policy_returns_2d(self):
        action = ToUPolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_tou_no_deferrable_during_peak(self):
        """ToUPolicy pik saatinde cihaz sinyali < 0 vermeli."""
        env_peak = DummyEnvPhase3(t=18)  # saat 18 → pik
        action = ToUPolicy(peak_hours=[(17, 22)])(self.obs, env_peak)
        self._assert_phase3_action(action)
        assert float(action[1]) < 0.0, "Pik saatinde deferrable sinyali negatif olmalı"

    def test_forecast_aware_policy_returns_2d(self):
        action = ForecastAwarePolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_peak_shaving_policy_returns_2d(self):
        action = PeakShavingPolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_peak_shaving_no_deferrable_during_peak_demand(self):
        """PeakShavingPolicy yüksek talep saatinde cihaz sinyali < 0 vermeli."""
        obs = make_obs_phase3(solar_kw=0.0, demand_kw=5.0)  # net=5kW > eşik(2kW)
        action = PeakShavingPolicy(peak_threshold_kw=2.0)(obs, self.env)
        self._assert_phase3_action(action)
        assert float(action[1]) < 0.0, "Yüksek net çekişte deferrable sinyali negatif olmalı"

    def test_grid_aware_policy_returns_2d(self):
        action = GridAwarePolicy()(self.obs, self.env)
        self._assert_phase3_action(action)

    def test_grid_aware_no_deferrable_during_outage(self):
        """GridAwarePolicy kesintide cihaz sinyali < 0 vermeli."""
        obs = make_obs_phase3(grid=0, dr=0)
        action = GridAwarePolicy()(obs, self.env)
        self._assert_phase3_action(action)
        assert float(action[1]) < 0.0, "Kesintide deferrable sinyali negatif olmalı"

    def test_grid_aware_no_deferrable_during_dr(self):
        """GridAwarePolicy DR eventinde cihaz sinyali < 0 vermeli."""
        obs = make_obs_phase3(grid=1, dr=1)
        action = GridAwarePolicy()(obs, self.env)
        self._assert_phase3_action(action)
        assert float(action[1]) < 0.0, "DR eventinde deferrable sinyali negatif olmalı"

    def test_phase1_env_still_returns_1d(self):
        """enable_deferrable=False ortamda tüm politikalar hâlâ (1,) döndürmeli."""
        env_p1 = DummyEnv(t=10)  # enable_deferrable yok
        obs_p1 = make_obs()
        for PolicyClass in [HoldPolicy, ThresholdPolicy, SelfConsumptionPolicy,
                            ToUPolicy, ForecastAwarePolicy, PeakShavingPolicy, GridAwarePolicy]:
            action = PolicyClass()(obs_p1, env_p1)
            assert action.shape == (1,), f"{PolicyClass.__name__} Faz 1'de (1,) döndürmeli"

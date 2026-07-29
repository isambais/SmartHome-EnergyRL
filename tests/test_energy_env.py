"""SmartHomeEnergyEnv için birim testleri.

implementation_plan.md Bölüm 13 (Test Stratejisi) kapsamında:
    - step()'in batarya SOC sınırlarını (0-1) asla aşmadığının doğrulanması
    - ödülün beklenen aralıkta olduğunun doğrulanması
    - Gymnasium check_env() yardımcı fonksiyonundan hatasız geçişin doğrulanması
"""

from __future__ import annotations

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from src.env.energy_env import SmartHomeEnergyEnv, split_into_daily_episodes


@pytest.fixture
def sample_prices() -> np.ndarray:
    # 3 gün x 24 saat = 72 saatlik, TL/MWh cinsinden basit bir örnek fiyat serisi.
    rng = np.random.default_rng(42)
    return rng.uniform(500.0, 4000.0, size=72).astype(np.float32)


def test_split_into_daily_episodes_shapes_correctly(sample_prices) -> None:
    daily = split_into_daily_episodes(sample_prices, hours_per_episode=24)
    assert daily.shape == (3, 24)


def test_split_into_daily_episodes_drops_incomplete_tail() -> None:
    prices = np.arange(50, dtype=np.float32)  # 50 saat -> 2 tam gün + 2 saat artık
    daily = split_into_daily_episodes(prices, hours_per_episode=24)
    assert daily.shape == (2, 24)


def test_reset_returns_valid_observation(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False)
    obs, info = env.reset(seed=0)

    assert obs.shape == (56,)
    assert obs[0] == pytest.approx(0.5)  # initial_soc varsayılanı
    assert env.observation_space.contains(obs)
    assert "day_idx" in info


def test_step_respects_soc_bounds(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=True)
    env.reset(seed=0)
    rng = np.random.default_rng(1)

    for _ in range(200):
        action = rng.uniform(-1.0, 1.0, size=(1,)).astype(np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        soc = obs[0]
        assert 0.0 <= soc <= 1.0
        assert np.isfinite(reward)
        if terminated:
            env.reset()


def test_full_charge_action_costs_money_and_increases_soc(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False, initial_soc=0.0)
    env.reset(seed=0)

    obs, reward, terminated, truncated, info = env.step(
        np.array([1.0], dtype=np.float32)
    )

    assert obs[0] > 0.0  # SOC arttı
    assert reward < 0.0  # şarj için ödeme yapıldı, ödül negatif
    assert info["cost_tl"] > 0.0
    assert info["revenue_tl"] == 0.0


def test_full_discharge_action_earns_money_and_decreases_soc(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False, initial_soc=1.0)
    env.reset(seed=0)

    obs, reward, terminated, truncated, info = env.step(
        np.array([-1.0], dtype=np.float32)
    )

    assert obs[0] < 1.0  # SOC azaldı
    assert reward > 0.0  # deşarjdan gelir elde edildi, ödül pozitif
    assert info["revenue_tl"] > 0.0
    assert info["cost_tl"] == 0.0


def test_discharge_when_empty_is_a_no_op(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False, initial_soc=0.0)
    env.reset(seed=0)

    obs, reward, terminated, truncated, info = env.step(
        np.array([-1.0], dtype=np.float32)
    )

    assert obs[0] == pytest.approx(0.0)
    assert reward == pytest.approx(0.0)


def test_episode_terminates_after_hours_per_episode(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, hours_per_episode=24, random_day=False)
    env.reset(seed=0)

    terminated = False
    steps = 0
    while not terminated:
        _, _, terminated, _, _ = env.step(np.array([0.0], dtype=np.float32))
        steps += 1

    assert steps == 24


def test_reset_is_reproducible_with_same_seed(sample_prices) -> None:
    env_a = SmartHomeEnergyEnv(sample_prices, random_day=True)
    env_b = SmartHomeEnergyEnv(sample_prices, random_day=True)

    obs_a, info_a = env_a.reset(seed=7)
    obs_b, info_b = env_b.reset(seed=7)

    np.testing.assert_array_equal(obs_a, obs_b)
    assert info_a["day_idx"] == info_b["day_idx"]


def test_gymnasium_check_env_passes(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=True)
    check_env(env.unwrapped, skip_render_check=True)


def test_wait_action_gives_zero_reward(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False)
    env.reset(seed=0)

    obs, reward, terminated, truncated, info = env.step(
        np.array([0.0], dtype=np.float32)
    )

    assert reward == pytest.approx(0.0)
    assert info["cost_tl"] == pytest.approx(0.0)
    assert info["revenue_tl"] == pytest.approx(0.0)


def test_charge_then_discharge_has_net_loss(sample_prices) -> None:
    env = SmartHomeEnergyEnv(sample_prices, random_day=False, initial_soc=0.0)
    env.reset(seed=0)

    # Aynı fiyatta şarj et
    _, charge_reward, _, _, _ = env.step(np.array([1.0], dtype=np.float32))
    # Aynı fiyatta deşarj et
    _, discharge_reward, _, _, _ = env.step(np.array([-1.0], dtype=np.float32))

    net = charge_reward + discharge_reward
    assert net < 0.0  # verimlilik kaybı nedeniyle net kayıp olmalı


def test_higher_price_gives_higher_discharge_reward(sample_prices) -> None:
    prices_low = np.full(24, 1000.0, dtype=np.float32)
    prices_high = np.full(24, 3000.0, dtype=np.float32)

    env_low = SmartHomeEnergyEnv(
        prices_low, random_day=False, initial_soc=1.0, price_unit="tl_per_mwh"
    )
    env_high = SmartHomeEnergyEnv(
        prices_high, random_day=False, initial_soc=1.0, price_unit="tl_per_mwh"
    )

    env_high.reset(seed=0)
    env_low.reset(seed=0)

    _, reward_low, _, _, _ = env_low.step(np.array([-1.0], dtype=np.float32))
    _, reward_high, _, _, _ = env_high.step(np.array([-1.0], dtype=np.float32))

    assert reward_high > reward_low


def test_episode_info_contains_totals(sample_prices) -> None:
    env = SmartHomeEnergyEnv(
        sample_prices,
        random_day=False,
    )
    env.reset(seed=0)

    terminated = False
    info = {}
    while not terminated:
        _, _, terminated, _, info = env.step(np.array([0.0], dtype=np.float32))

    assert "episode" in info
    assert "total_reward" in info["episode"]
    assert "total_cost" in info["episode"]
    assert "total_revenue" in info["episode"]


# ── Gün 13: Aşama 3 — Ertelenebilir Yük Testleri ─────────────────────────────


@pytest.fixture
def phase3_env(sample_prices) -> SmartHomeEnergyEnv:
    """enable_deferrable=True ile Phase 3 ortamı."""
    return SmartHomeEnergyEnv(
        sample_prices,
        random_day=False,
        enable_deferrable=True,
        deferrable_load_power_kw=1.5,
        deferrable_load_hours=1.0,
        deferrable_window=(6, 22),
        deferrable_penalty_coef=5.0,
    )


def test_phase3_action_space_is_two_dimensional(phase3_env) -> None:
    """Aşama 3'te aksiyon uzayı (2,) boyutunda olmalı."""
    assert phase3_env.action_space.shape == (2,)


def test_phase3_obs_space_is_two_larger(sample_prices) -> None:
    """enable_deferrable=True gözlem boyutunu 2 artırmalı (device_used_today + steps_remaining)."""
    env_base = SmartHomeEnergyEnv(sample_prices, random_day=False)
    env_p3 = SmartHomeEnergyEnv(sample_prices, random_day=False, enable_deferrable=True)

    obs_base, _ = env_base.reset(seed=0)
    obs_p3, _ = env_p3.reset(seed=0)

    assert obs_p3.shape[0] == obs_base.shape[0] + 2


def test_phase3_device_used_flag_starts_zero(phase3_env) -> None:
    """Episode başında device_used_today flag'i (obs[-2]) 0 olmalı."""
    obs, _ = phase3_env.reset(seed=0)
    assert obs[-2] == pytest.approx(0.0)   # device_used_today
    assert obs[-1] == pytest.approx(0.0)   # device_steps_remaining_norm


def test_phase3_activation_sets_device_flag(phase3_env) -> None:
    """Cihaz çalıştırıldığında (action[1] > 0, saat penceresi içi) flag 1 olmalı."""
    phase3_env.reset(seed=0)
    # t=0, hour=0 → pencere dışı (deferrable_window=(6,22))
    # t=6'ya kadar ilerle
    for _ in range(6):
        phase3_env.step(np.array([0.0, -1.0], dtype=np.float32))  # çalıştırma

    # t=6, saat 6 → pencere içi, cihazı çalıştır
    obs, _, _, _, info = phase3_env.step(np.array([0.0, 1.0], dtype=np.float32))

    assert obs[-2] == pytest.approx(1.0)  # device_used_today flag set
    assert obs[-1] == pytest.approx(0.0)  # 1-saatlik cihaz bu adımda bitti → remaining=0
    assert info["deferrable_action"] == 1
    assert info["deferrable_load_kw"] == pytest.approx(1.5)


def test_phase3_activation_increases_demand(phase3_env) -> None:
    """Cihaz çalıştırıldığında net şebeke tüketimi artmalı."""
    phase3_env.reset(seed=0)
    for _ in range(6):
        phase3_env.step(np.array([0.0, -1.0], dtype=np.float32))

    # Cihaz kapalıyken
    _, _, _, _, info_off = phase3_env.step(np.array([0.0, -1.0], dtype=np.float32))
    phase3_env.reset(seed=0)
    for _ in range(6):
        phase3_env.step(np.array([0.0, -1.0], dtype=np.float32))

    # Cihaz açıkken
    _, _, _, _, info_on = phase3_env.step(np.array([0.0, 1.0], dtype=np.float32))

    # Cihaz açıkken daha fazla şebekeden alım olmalı
    assert info_on["net_grid_kwh"] > info_off["net_grid_kwh"]


def test_phase3_penalty_applied_when_device_never_used(phase3_env) -> None:
    """Gün boyunca cihaz hiç çalıştırılmazsa episode sonunda ceza uygulanmalı."""
    phase3_env.reset(seed=0)

    terminated = False
    info = {}
    total_deferrable_penalty = 0.0
    while not terminated:
        _, _, terminated, _, info = phase3_env.step(
            np.array([0.0, -1.0], dtype=np.float32)  # hiç çalıştırma
        )
        total_deferrable_penalty += info.get("deferrable_penalty_tl", 0.0)

    assert total_deferrable_penalty == pytest.approx(5.0)
    assert info["episode"]["device_activation_count"] == 0
    assert info["episode"]["device_activation_rate"] == pytest.approx(0.0)


def test_phase3_no_penalty_when_device_used(phase3_env) -> None:
    """Cihaz en az bir kez çalıştırıldığında episode sonu cezası sıfır olmalı."""
    phase3_env.reset(seed=0)

    terminated = False
    info = {}
    device_activated = False
    total_deferrable_penalty = 0.0
    t = 0
    while not terminated:
        if t == 6 and not device_activated:
            action = np.array([0.0, 1.0], dtype=np.float32)  # çalıştır
            device_activated = True
        else:
            action = np.array([0.0, -1.0], dtype=np.float32)
        _, _, terminated, _, info = phase3_env.step(action)
        total_deferrable_penalty += info.get("deferrable_penalty_tl", 0.0)
        t += 1

    assert total_deferrable_penalty == pytest.approx(0.0)
    assert info["episode"]["device_activation_count"] >= 1
    assert info["episode"]["device_activation_rate"] > 0.0


def test_phase3_outside_window_action_ignored(phase3_env) -> None:
    """Pencere dışındaki saatlerde (0-5) action[1]=1 cihazı çalıştırmamalı."""
    phase3_env.reset(seed=0)

    # Saat 0-5 arasında cihazı çalıştırmayı dene (pencere dışı)
    for _ in range(5):
        _, _, _, _, info = phase3_env.step(np.array([0.0, 1.0], dtype=np.float32))
        assert info["deferrable_action"] == 0
        assert info["deferrable_load_kw"] == pytest.approx(0.0)


def test_phase3_gymnasium_check_env_passes(sample_prices) -> None:
    """Aşama 3 ortamı Gymnasium check_env'den hatasız geçmeli."""
    env = SmartHomeEnergyEnv(
        sample_prices,
        random_day=True,
        enable_deferrable=True,
    )
    check_env(env.unwrapped, skip_render_check=True)


def test_phase3_episode_info_has_activation_rate(phase3_env) -> None:
    """Episode info'da device_activation_rate metrikleri bulunmalı."""
    phase3_env.reset(seed=0)

    terminated = False
    info = {}
    while not terminated:
        _, _, terminated, _, info = phase3_env.step(
            np.array([0.0, -1.0], dtype=np.float32)
        )

    assert "device_activation_count" in info["episode"]
    assert "device_activation_rate" in info["episode"]
    assert 0.0 <= info["episode"]["device_activation_rate"] <= 1.0


def test_phase3_device_runs_multiple_steps(sample_prices) -> None:
    """2 saatlik cihaz, tek aktivasyonla iki ardışık adımda yük uygular."""
    env = SmartHomeEnergyEnv(
        sample_prices, random_day=False, enable_deferrable=True,
        deferrable_load_power_kw=1.5, deferrable_load_hours=2.0,
        deferrable_window=(6, 22),
    )
    env.reset(seed=0)
    # Saat 8'e kadar ilerle (pencere içi)
    for _ in range(8):
        env.step(np.array([0.0, -1.0], dtype=np.float32))

    # Aktivasyon
    obs_act, _, _, _, info_act = env.step(np.array([0.0, 1.0], dtype=np.float32))
    assert info_act["deferrable_action"] == 1
    assert info_act["deferrable_load_kw"] == pytest.approx(1.5)
    # 2 adımlık cihaz: bu adımda 1 adım bitti, 1 kaldı → remaining_norm = 0.5
    assert obs_act[-1] == pytest.approx(0.5)

    # Sonraki adım — cihaz hâlâ çalışmalı (action[1]=-1 olsa bile)
    obs_cont, _, _, _, info_cont = env.step(np.array([0.0, -1.0], dtype=np.float32))
    assert info_cont["deferrable_action"] == 0       # yeni aktivasyon yok
    assert info_cont["deferrable_load_kw"] == pytest.approx(1.5)  # yük devam ediyor
    assert obs_cont[-1] == pytest.approx(0.0)        # bitti

    # Bir sonraki adımda cihaz durmuş olmalı
    _, _, _, _, info_stop = env.step(np.array([0.0, -1.0], dtype=np.float32))
    assert info_stop["deferrable_load_kw"] == pytest.approx(0.0)


def test_phase3_device_steps_remaining_normalized(sample_prices) -> None:
    """device_steps_remaining_norm obs[-1] doğru normalize edilmeli."""
    env = SmartHomeEnergyEnv(
        sample_prices, random_day=False, enable_deferrable=True,
        deferrable_load_hours=2.0, deferrable_window=(0, 24),
    )
    env.reset(seed=0)

    # Saat 0'da aktivasyon (pencere=(0,24) → her saat geçerli)
    obs, _, _, _, _ = env.step(np.array([0.0, 1.0], dtype=np.float32))
    # 2 adımlık cihaz, bu adımda 1 bitti, 1 kaldı → 1/2 = 0.5
    assert obs[-1] == pytest.approx(0.5)


def test_phase3_device_cannot_be_reactivated_while_running(sample_prices) -> None:
    """Cihaz çalışırken tekrar aktivasyon sinyali görmezden gelinmeli."""
    env = SmartHomeEnergyEnv(
        sample_prices, random_day=False, enable_deferrable=True,
        deferrable_load_hours=3.0, deferrable_window=(0, 24),
        max_activations_per_day=5,
    )
    env.reset(seed=0)

    # İlk aktivasyon
    _, _, _, _, info1 = env.step(np.array([0.0, 1.0], dtype=np.float32))
    assert info1["deferrable_action"] == 1

    # Çalışıyor — tekrar aktivasyon denemesi, yeni aktivasyon OLMAMALI
    _, _, _, _, info2 = env.step(np.array([0.0, 1.0], dtype=np.float32))
    assert info2["deferrable_action"] == 0      # yeni aktivasyon yok
    assert info2["deferrable_load_kw"] == pytest.approx(1.5)  # ama yük devam ediyor

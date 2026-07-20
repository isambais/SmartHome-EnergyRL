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

    assert obs.shape == (25,)
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
